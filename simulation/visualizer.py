# lightweight ASCII visualizer that drawsthe map into the terminal, it is simple
# think of it as webcam: not pretty, but useful

import asyncio
import os

class Visualizer:
    def __init__(self, game_map, cars, persons, enabled=True, refresh_every=1.0):
        self.map = game_map
        self.cars = cars
        self.persons  = persons
        self.enabled = enabled
        self.refresh_every = refresh_every

    async def run(self):
        if not self.enabled:
            return
        try:
            while True:
                self._render()
                await asyncio.sleep(self.refresh_every)
        except asyncio.CancelledError:
            return

    def _render(self):
        # clear the terminal nicely
        os.system("cls" if os.name== "nt" else "clear")
        w, h = self.map.w, self.map.h
        # initialize empty grid with dots
        grid = [["." for _ in range(w)] for _ in range(h)]

        # mark blocked cells
        for bx, by in self.map.blocked:
            if 0 <= bx < w and 0 <= by < h:
                grid[by][bx] = "#"

        # mark persons (spawn = P, goal = D)
        for p in self.persons:
            sx, sy = p.spawn
            gx, gy = p.goal
            if 0 <= sx < w and 0 <= sy < h:
                grid[sy][sx] = "P"
            if 0 <= gx < w and 0 <= gy < h:
                grid[gy][gx] = "D"

        # mark cars (digit or letter), last car written wins in case of colliding
        # display

        for c in self.cars:
            try:
                x, y = c.x, c.y
                if 0 <= x < w and 0 <= y < h:
                    marker = str(c.id % 10)
                    grid[y][x] = marker
            except Exception:
                pass

        # print header and the grid
        print("=== Traffic Simulator - ASCII view ===")
        for row in grid:
            print("".join(row))
        print("znLegend: .empty, # blocked, P spawn, D dest, digits are cars")
