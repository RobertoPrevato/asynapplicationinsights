from asyncio import Queue, QueueEmpty
from abc import ABC, abstractmethod
from typing import List


class TelemetryChannel(ABC):

    def __init__(self):
        self._queue = Queue()
        self._max_length = 500

    def get(self):
        try:
            return self._queue.get_nowait()
        except QueueEmpty:
            return None

    async def put(self, item):
        if not item:
            return
        await self._queue.put(item)
        if self.should_flush():
            await self.flush()

    def should_flush(self) -> bool:
        return self._max_length <= self._queue.qsize()

    async def flush(self):
        data = []
        while True:
            item = self.get()
            if not item:
                break
            data.append(item)

        await self.send(data)

    @abstractmethod
    async def send(self, data: List):
        pass

    @abstractmethod
    async def dispose(self):
        pass
