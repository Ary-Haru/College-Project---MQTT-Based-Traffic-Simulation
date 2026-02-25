
# this is a simple script, everything important lives in the modules
# below. if something breaks, check which file made the noise.

import asyncio
import json
import signal
import sys
from simulation.engine import Engine
from simulation.logger import SimulationLogger
from simulation.visualizer import Visualizer
from model.map import CityMap
from model.central import Central
from model.car import Car
from model.person import Person
from comm.local import LocalBus
from comm.mqtt_async import MqttComm

# used to signal shutdown from SIGINT/SIGTERM
stop=asyncio.Event()

def _on_signal():
    # called on crtl-c, sets stop to let engine shutdown cleanly
    STOP.set()

async def build_and_run():
    # load configuration, igf this fails we stop here, better to know fast
    try:
        with open("config.json", "r") as f:
            cfg = json.load(f)
    except Exception as e:
        print("failed to load config.json:", e)
        sys.exit(1)

    # create map (grid + blocked cells)
    game_map = CityMap(cfg["map"])

    # logger will collect event history and flush to JSON/CSV at the end
    loggr = SimulationLogger(cfg.get("log_path", "history.json"), cfg.get("log_csv", "history.csv"))

    if cfg.get("comm_mode", "local") == "mqtt":
        comm = MqttComm(cfg["mqtt"])
    else:
        comm = LocalBus()

    # central controller will assign routes and enforce safe distance
    central = Central(game_map, comm, logger, safe_distance=cfg.get("safe_distance", 1.0))

    # create and register cars
    cars = []
    for c in cfg.get("cars", []):
        car = Car(car_id=c["id"], x=c["pos"][0], y=c["pos"][1], max_speed=c.get("max_speed", 1.0), comm=comm, logger=logger)
        cars.append(car)
        central.register_car(car)

        # create persons
        persons = []
        for p in cfg.get("persons", []):
            person = Person(pid=p["id"], spawn=tuple(p["soawn"]), goal=tuple(p["goal"]))
            persons.append(person)

        # engine manages tasks
        engine = Engine(tick=cfg.get("tick", 0.2), logger=logger)

        #visualizer (optional) prints grid every few seconds
        vis_cfg = cfg.get("visualizer", {})
        visualizer = Visualizer(game_map, cars, persons, enabled=vis_cfg.get("enabled", True), refresh_every=vis_cfg.get("refresh_every", 1.0))

        # register tasks
        enfine.add_task(central.run)
        for car in cars:
            engine.add_task(car.run)
        enfine.add_task(visualizer.run)

        # stagger person requests a bit so theyll all not scream at once

    for i, person in enumerate(persons):
        engine.add_task(lambda p=person, d=i: p.request_transport(central, delay=1 +d*0.8))

        # hook for shutdown
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, _on_signal)
        loop.add_signal_handler(signal.SIGTERM, _on_signal)

        print("starting simulation. press ctrl-c to stop")
        await engine.start(run_until=STOP.wait)

        print("simulation stopped, flushing logs...")
        await logger.flush()
        print("logs flushed, exiting")

    if __name__ == "__main__":
        asyncio.run(build_and_run())
 
