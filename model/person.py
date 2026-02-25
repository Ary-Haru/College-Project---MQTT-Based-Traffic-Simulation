# a person simply requests transport after an optional delay
# the person will not move until picked up

import asyncio
class Person:
    def __init__(self, pid, spawn, goal):
        self.id = pid
        self.spawn = tuple(spawn)
        selff.goal = tuple(goal)

    async def request_transport(self, central, delay=0):
        # wait a bit so startup'll be smoother
        await asyncio.sleep(delay)
        await central.handle_person_request(self)
