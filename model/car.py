# car is an async actor, it holds a route, moves one cell per loop
# towards the next waypoint, publishes its position via comm,
# accepts commands from central (via comm) and logs state to the logger

# the movement is grid based, speed is modeled as a modifier for how
# long the car sleeps between "steeps", the smooth slowdown is simplified
# as the new speed is set directly, there are no physics involved

import asyncio

class Car:
    def __init__(self, car_id: int, x: int, y: int, max_speed: float, comm, logger):
        self.id = car_id
        self.x = int(x)
        self.y = int(y)
        self.max_speed = float(max_speed)
        self.speed = 0.0
        self.route = []
        self.comm = comm
        self.logger = logger
        self.lock = asyncio.Lock()
        self.parked = True
        self.command_queue = asyncio.Queue()
        # local comm will call attach_cmd_listener to send command callbacks to us
        if hasattr(self.comm, "attach_cmd_listener"):
            self.comm.attach_cmd_listener(self._receive_cmd)

    async def _receive_cmd(self, car_id, cmd):
        # only accept commands for this car
        if car_id != self.id:
            return
        await self.command_queue.put(cmd)

    async def _handle_commands(self):
        # process queued commands
        while not self.command_queue.empty():
            cmd = await self.command_queue.get()
            if not isinstance(cmd, dict):
                continue
            c = cmd.get("cmd")
            if c == "set_speed":
                val = float(cmd.get("value", 0.0))
                await self.set_speed(val)
            elif c == "set_route":
                route = cmd.get("route", [])
                cleaned = [(int(x), int(y)) for x,y in route]
                await self.set_route(cleaned)
            # ignore unknown commands

    async def run(self):
        try:
            while True:
                async with self.lock:
                    await self._handle_commands()
                    if self.route:
                        nx, ny = self.route[0]
                        dx = nx - self.x
                        dy = ny - self.y
                        step_x = 0 if dx == 0 else (1 if dx>0 else -1)
                        step_y = 0 if dy == 0 else (1 if dy>0 else -1)
                        self.x += step_x
                        self.y += step_y
                        # if we reached the waypoint, pop it
                        if (self.x, self.y) == (nx, ny):
                            self.route.pop(0)
                            if not self.route:
                                self.parked = True
                                await self.set_speed(0.0)
                        else:
                            if self.speed == 0.0:
                                await self.set_speed(self.max_speed)
                    # publish current position
                    await self.comm.publish_position(self.id, (self.x, self.y), speed=self.speed)
                    # log current state
                    await self.logger.record("car", self.id, {"x": self.x, "y": self.y, "speed": self.speed})
                sleep_time = 0.25 / (self.speed if self.speed > 0 else 1.0)
                await asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            return

    async def set_route(self, route):
        async with self.lock:
            self.route = list(route)
            self.parked = False
            await self.set_speed(self.max_speed)  # start moving

    async def set_speed(self, new_speed: float):
        async with self.lock:
            self.speed = max(0.0, min(self.max_speed, float(new_speed)))

    async def current_pos(self):
        async with self.lock:
            return (self.x, self.y)               
