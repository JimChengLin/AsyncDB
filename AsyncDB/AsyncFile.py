from asyncio import get_event_loop
from collections import deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from os.path import getsize

loop = get_event_loop()


class FastIO:
    def __init__(self, filename: str):
        self.cursor = 0
        self.file = open(filename, 'rb+', buffering=0)

    def seek(self, offset: int):
        if offset != self.cursor:
            self.file.seek(offset)

    def read(self, offset: int, length: int):
        self.seek(offset)
        self.cursor = offset + length
        return self.file.read(length)

    def write(self, offset: int, data: bytes):
        self.seek(offset)
        self.cursor = offset + len(data)
        self.file.write(data)
        self.file.flush()

    def exec(self, offset: int, action: Callable):
        self.seek(offset)
        result = action(self.file)
        self.file.flush()
        self.cursor = self.file.tell()
        return result


class AsyncFile:
    def __init__(self, filename: str, io_num=4):
        self.size = getsize(filename)
        self.executor = ThreadPoolExecutor(io_num)
        self.io_que = deque((FastIO(filename) for _ in range(io_num + 1)), io_num + 1)

    async def read(self, offset: int, length: int):
        def async_call():
            io = self.io_que.popleft()
            result = io.read(offset, length)
            self.io_que.append(io)
            return result

        return await loop.run_in_executor(self.executor, async_call)

    async def write(self, offset: int, data: bytes):
        assert self.size >= offset + len(data)

        def async_call():
            io = self.io_que.popleft()
            io.write(offset, data)
            self.io_que.append(io)

        await loop.run_in_executor(self.executor, async_call)

    async def exec(self, offset: int, action: Callable):
        def async_call():
            io = self.io_que.popleft()
            result = io.exec(offset, action)
            self.io_que.append(io)
            return result

        return await loop.run_in_executor(self.executor, async_call)

    def close(self):
        for io in self.io_que:
            io.file.close()
