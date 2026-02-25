# central keeps track of car positions, assigns jobs to cars and calculates
# routes using CityMap, and enforces safe distances by gently adjusting car speeds

# uses euclidean distance to decide closeness, slowdown is proportional to how
# near two cars are (linear mapping), central subscribes comm messages to
# receive positions

import asyncio
import math

class Central:
    def __init__(self, game_map, comm, logger, safe_distance=1.0):
        self.map = game_map
        self.comm = comm
        self.logger = logger
        self.cars = {}
        self.positions = {}
        self.speeds = {}
        self.safe_distance = float(safe_distance)
        self.lock = asyncio.Lock()
        # subscribe to comm events
        self.comm.attach_listener(self.on_position_msg)

    def register_car(self, car):
        self.cars[car.id] = car
        self.positions[car.id] = (car.x, car.y)
        self.speeds[car.id] = car.speed

    async def on_position_msg(self, car_id, pos, speed=None):
        # called by comm layer whenever a car publishes its position
        async with self.lock:
            self.positions[car_id] = tuple(pos)
            if speed is not None:
                self.speeds[car_id] = float(speed)
            await self.logger.record("central_pos", car_id, {"x": pos[0], "y": pos[1], "speed": speed})
            await self._enforce_safe_distance(car_id)

    async def _enforce_safe_distance(self, changed_car_id):
        # find nearest neighbor and, if too close, slow down proportionally
        pos = self.positions.get(changed_car_id)
        if pos is None:
            return
        nearest = None
        nearest_dist = float("inf")
        for other_id, other_pos in self.positions.items():
            if other_id == changed_car_id:
                continue
            dist = math.hypot(pos[0] - other_pos[0], pos[1] - other_pos[1])
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = other_id
        if nearest is None:
            return
        if nearest_dist < self.safe_distance:
            # compute a slowdown factor between 0.2 and 1.0
            factor = max(0.0, min(1.0, nearest_dist / self.safe_distance))
            new_speed = (0.2 + 0.8 * factor) * self.cars[changed_car_id].max_speed
            await self.cars[changed_car_id].set_speed(new_speed)
            await self.logger.record("central_action", changed_car_id, {"action":"slowdown","to":new_speed,"near":nearest,"dist":nearest_dist})
            # also publish a command for external listeners (MQTT or other)
            await self.comm.publish_command(changed_car_id, {"cmd":"set_speed","value":new_speed})
        else:
            # restore speed if car is moving and below max
            car = self.cars.get(changed_car_id)
            if car and not car.parked and self.speeds.get(changed_car_id, 0) < car.max_speed:
                await car.set_speed(car.max_speed)
                await self.logger.record("central_action", changed_car_id, {"action":"restore_speed","to":car.max_speed})

    async def assign_car_to_person(self, person):
        # choose nearest parked car and assign pickup + dropoff route using A*
        async with self.lock:
            free = [c for c in self.cars.values() if c.parked]
            if not free:
                await self.logger.record("central_assign", "none", {"msg":"no_free_car","person":person.id})
                return None
            # nearest by Euclidean distance
            best = min(free, key=lambda c: math.hypot(c.x - person.spawn[0], c.y - person.spawn[1]))
            pickup = self.map.route((best.x, best.y), person.spawn) or []
            drop = self.map.route(person.spawn, person.goal) or []
            route = pickup + drop
            await best.set_route(route)
            await best.set_speed(best.max_speed)
            await self.logger.record("central_assign", best.id, {"person":person.id, "pickup_len":len(pickup), "drop_len":len(drop)})
            await self.comm.publish_command(best.id, {"cmd":"set_route","route":route})
            return best

    async def handle_person_request(self, person):
        # public API: called by Person when they request transport
        await self.logger.record("person_request", person.id, {"spawn": person.spawn, "goal": person.goal})
        return await self.assign_car_to_person(person)

    async def run(self):
        # periodic maintenance: assign random roaming routes to parked cars so the city is alive.
        try:
            while True:
                async with self.lock:
                    for car in list(self.cars.values()):
                        if car.parked:
                            start = await car.current_pos()
                            target = self.map.random_point()
                            path = self.map.route(start, target)
                            if path:
                                await car.set_route(path)
                                await car.set_speed(car.max_speed)
                                await self.logger.record("central_assign", car.id, {"target": target, "path_len": len(path)})
                                await self.comm.publish_command(car.id, {"cmd":"set_route","route":path})
                await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            return
