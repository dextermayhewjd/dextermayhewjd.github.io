import asyncio


async def ensure_async_iterator(iterable):
    for item in iterable:
        print("source preparing", item)
        await asyncio.sleep(0)
        print("source yield", item)
        yield item
        print("source resumed", item)
    print("source exhausted")


async def exercise():
    stream = ensure_async_iterator([10, 11])
    print("stream created")
    async for item in stream:
        print("body received", item)
        await asyncio.sleep(0)
        print("body finished", item)
    print("loop finished")


if __name__ == "__main__":
    asyncio.run(exercise())
