from asyncio import get_event_loop

from AsyncDB import AsyncDB

M = 10000
FILE = 'Test.db'


async def write():
    db = AsyncDB(FILE)
    for i in range(M):
        db[i] = i
        print('set', i)


async def read():
    db = AsyncDB(FILE)
    for i in range(M):
        value = await db[i]
        print('get', value)


def main():
    loop = get_event_loop()
    loop.run_until_complete(write())
    # loop.run_until_complete(read())


if __name__ == '__main__':
    main()
