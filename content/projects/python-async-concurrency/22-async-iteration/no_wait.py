import asyncio


async def ensure_async_iterator(iterable):
    for item in iterable:
        yield item


async def other_work():
    print("other task")


async def exercise():
    task = asyncio.create_task(other_work())
    async for item in ensure_async_iterator([10, 11]):
        print("item", item)
    print("loop finished")
    await task


if __name__ == "__main__":
    asyncio.run(exercise())
