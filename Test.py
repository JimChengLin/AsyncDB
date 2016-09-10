from asyncio import get_event_loop, sleep, ensure_future
from os import remove
from os.path import isfile
from random import randint

from AsyncDB import AsyncDB

T = 10000
M = 10000
FILE = 'Test.db'


async def acid_t():
    if isfile(FILE):
        remove(FILE)

    std = {}
    db = AsyncDB(FILE)

    async def compare(key, expect_value):
        db_value = await db[key]
        assert db_value == expect_value

    for _ in range(T):
        # 增改
        if randint(0, 1):
            rand_key = randint(0, M)
            rand_value = randint(0, M)
            print('set', rand_key)
            std[rand_key] = rand_value
            db[rand_key] = rand_value

        # 删
        if randint(0, 1):
            rand_key = randint(0, M)
            print('pop', rand_key)
            if rand_key in std:
                del std[rand_key]
            db.pop(rand_key)

        # 读
        if randint(0, 1):
            rand_key = randint(0, M)
            expect_value = std.get(rand_key)
            ensure_future(compare(rand_key, expect_value))
            await sleep(0)

    # 遍历
    std_items = list(std.items())
    for key, value in std_items:
        db_value = await db[key]
        assert db_value == value

    items = await db.items()
    for key, value in items:
        assert value == std[key]
    assert len(items) == len(std_items)
    print('iter OK')

    # 参数
    std_items.sort()
    max_i = len(std_items)
    i_from = randint(0, max_i - 1)
    i_to = randint(i_from + 1, max_i)
    sub_items = std_items[i_from:i_to]

    items = await db.items(item_from=sub_items[0][0], item_to=sub_items[-1][0])
    assert items == sub_items
    items = await db.items(item_from=sub_items[0][0], item_to=sub_items[-1][0], reverse=True)
    assert items == sorted(sub_items, reverse=True)
    max_len = randint(1, M)
    items = await db.items(item_from=sub_items[0][0], item_to=sub_items[-1][0], max_len=max_len)
    assert len(items) == min(max_len, len(sub_items))
    print('params OK')
    await db.close()

    db = AsyncDB(FILE)
    for key, value in std_items:
        db_value = await db[key]
        assert db_value == value
    await db.close()
    print('ACID OK')


def main():
    loop = get_event_loop()
    for _ in range(1000):
        loop.run_until_complete(acid_t())
        remove(FILE)


if __name__ == '__main__':
    main()
