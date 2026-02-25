# this class will run a background listener that forwards incoming messages to attached listeners
# will provide publish_position/command so it can send messages

import asyncio
import json
from asyncio_mqtt import Client, MqttError

class MqttComm:
    def __init__(self, cfg):
        self.host = cfg.get("host", "localhost")
        self.port = cfg.get("port", 1883)
        self.topic_base = cfg.get("topic_base", "sim/")
        self._listeners = []
        self._cmd_listeners = []
        self._client = Client(self.host, self.port)
        # start listener task
        self._task = asyncio.create_task(self._listener_loop())

    def attach_listener(self, func):
        self._listeners.append(func)

    def attach_cmd_listener(self, func):
        self._cmd_listeners.append(func)

    async def _listener_loop(self):
        # listens for messages on topic_base#
        try:
            async with self._client as client:
                await client.subscribe(f"{self.topic_base}#")
                async with client.unfiltered_messages() as messages:
                    async for msg in messages:
                        try:
                            payload = json.loads(msg.payload.decode())
                        except Exception:
                            continue
                        # expect payload like {"car":id, "pos":[x,y], "speed":v}
                        car = payload.get("car")
                        pos = payload.get("pos")
                        speed = payload.get("speed")
                        for f in self._listeners:
                            # schedule listener calls to avoid blocking mqtt loop
                            asyncio.create_task(f(car, pos, speed))
        except MqttError as e:
            print("MQTT listener stopped due to error:", e)

    async def publish_position(self, car_id, pos, speed=0.0):
        topic = f"{self.topic_base}cars/{car_id}/pos"
        payload = json.dumps({"car": car_id, "pos": pos, "speed": speed})
        try:
            async with self._client as client:
                await client.publish(topic, payload)
        except Exception:
            pass

    async def publish_command(self, car_id, cmd):
        topic = f"{self.topic_base}cars/{car_id}/cmd"
        payload = json.dumps({"cmd": cmd})
        try:
            async with self._client as client:
                await client.publish(topic, payload)
        except Exception:
            pass                      
