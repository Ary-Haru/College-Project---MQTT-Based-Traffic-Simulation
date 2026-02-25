# async friendly logger. It collects events in memory (per entity) and writes them
# to JSON and CSV files when flush() is called. Uses aiofiles to avoid blocking

import asyncio
import json
import time
from collections import defaultdict
import aiofiles

class SimulationLogger:
    def __init__(self, json_path="history.json", csv_path="history.csv"):
        self.json_path = json_path
        self.csv_path = csv_path
        self._history = defaultdict(list)
        self._lock = asyncio.Lock()

    async def record(self, entity_type, entity_id, state: dict):
        
        # record a snapshot for an entity, keep it small and simple

        entry = {"t": time.time(), "type": entity_type, "id": entity_id}
        entry.update(state)
        async with self._lock:
            self._history[entity_id].append(entry)

    async def flush(self):
        # write JSON and CSV. CSV is a naive flatten but workable for analysis.
        # this function is async and uses aiofiles so it won't block the event loop.
        
        async with self._lock:
            # write JSON
            async with aiofiles.open(self.json_path, "w") as f:
                await f.write(json.dumps(self._history, indent=2, default=str))

            # prepare CSV rows (flatten)
            rows = []
            for lst in self._history.values():
                rows.extend(lst)
            if not rows:
                return

            keys = sorted({k for r in rows for k in r.keys()})
            header = ",".join(keys) + "\n"
            async with aiofiles.open(self.csv_path, "w") as f:
                await f.write(header)
                for r in rows:
                    line = ",".join(str(r.get(k, "")) for k in keys) + "\n"
                    await f.write(line)

