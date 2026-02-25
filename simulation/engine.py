
# schedules coroutine based tasks and runs them concurrently 
# this is simplen register a set of coroutine functions (or callables),
# the engine creates tasks and waits until an external event (e.g. STOP.wait(

import asyncio
from typing import Callable, List, Coroutine

class Engine:
    def __init__(self, tick: float = 0.2, logger=None):
        self.tick = tick
        self._task_callables: List[Callable[[], Coroutine]] = []
        self.logger = logger

    def add_task(self, coro_func):
        
        # add a task to the engine.

        # accepts:
        # - an async function object (no args), e.g. async def f(): ...
        #- a zero-arg callable returning a coroutine (lambda: f(...))
        self._task_callables.append(coro_func)

    async def start(self, run_until=None):
        # Create asyncio tasks from the registered callables
        running_tasks = []
        for fn in self._task_callables:
            try:
                if asyncio.iscoroutinefunction(fn):
                    running_tasks.append(asyncio.create_task(fn()))
                else:
                    maybe_coro = fn()
                    if asyncio.iscoroutine(maybe_coro):
                        running_tasks.append(asyncio.create_task(maybe_coro))
            except Exception as e:
                print("Engine: failed to schedule a task:", e)

        # If there's no run_until we just gather forever (not used here)
        if run_until is None:
            await asyncio.gather(*running_tasks)
            return

        # Wait for the external event (e.g. STOP.wait())
        await run_until()

        # Cancel tasks for a clean shutdown
        for t in running_tasks:
            t.cancel()
        # Give tasks a moment to clean up
            await asyncio.sleep(0.1)

