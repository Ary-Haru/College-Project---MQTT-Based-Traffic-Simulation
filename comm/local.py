# ts a small in process message bus, everything is async aware and uses await
# it will support attach_listener for position updates, publish_position, attach_cmd_listener
# so it will allow external code such as car to receive commands and publish_command to send commands

import asyncio
class LocalBus:
    def __init__(self):
        self._pos_listeners = []
        selff._cmd_listeners = []

    def attach_listener(self, func):
        # func should be async function expecting
        self._pos_listeners.append(func)

    async def publish_position(self, car_id, pos, speed=0.0):
        # call all listeners
        for f in list(self._pos_listeners):
            try:
                await f(car_id, pos, speed)
            except Exception as e:
                print("LocalBus listener error:", e)

    def attach_cmd_listener(self, func):
        self._cmd_listeners.append(func)

    async def publish_command(self, car_id, cmd):
        for f in list(self._cmd_listeners):
            try:
                await f(car_id, cmd)
            except Exception as e:
                print("LocalBus cmd listener error:", e)
