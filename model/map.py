# citymap implements a grid with blocked cells and an A* pathfinder
# A* returns the shortest path (list of corords excluding the start)

import heapq
import random
from typing import Tuple, List, Set

Coord = Tuple[int, int]

class CityMap:
    def __init__(self, cfg):
        self.w = cfg.get("width", 20)
        self.h = cfg.get("height", 20)
        blocked = cfg.get("blocked", [])
        # store blocked as set of tuples for fast lookup
        self.blocked: Set[Coord] = set((int(x), int(y)) for x,y in blocked)

    def valid(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h and (x, y) not in self.blocked

    def neighbors(self, x: int, y: int):
        # 4-connected grid (no diagonals)
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if self.valid(nx, ny):
                yield (nx, ny)

    def heuristic(self, a: Coord, b: Coord) -> float:
        # Euclidean heuristic (admissible here)
        return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5

    def astar(self, start: Coord, goal: Coord) -> List[Coord]:
        if start == goal:
            return []
        start = tuple(start)
        goal = tuple(goal)
        open_set = []
        heapq.heappush(open_set, (self.heuristic(start, goal), 0, start))
        came = {}
        gscore = {start: 0}
        while open_set:
            _, cost, current = heapq.heappop(open_set)
            if current == goal:
                break
            for nb in self.neighbors(*current):
                tentative_g = gscore[current] + 1
                if tentative_g < gscore.get(nb, float("inf")):
                    came[nb] = current
                    gscore[nb] = tentative_g
                    f = tentative_g + self.heuristic(nb, goal)
                    heapq.heappush(open_set, (f, tentative_g, nb))
        if goal not in came:
            return []
        # reconstruct path
        path = []
        cur = goal
        while cur != start:
            path.append(cur)
            cur = came[cur]
        path.reverse()
        return path

    def route(self, start: Coord, goal: Coord) -> List[Coord]:
        # wrapper to keep naming consistent across the project
        return self.astar(start, goal)

    def random_point(self) -> Coord:
        # try random picks first, fallback to scan
        for _ in range(500):
            x = random.randint(0, self.w-1)
            y = random.randint(0, self.h-1)
            if self.valid(x, y):
                return (x, y)
        for yy in range(self.h):
            for xx in range(self.w):
                if self.valid(xx, yy):
                    return (xx, yy)
        return (0,0)
