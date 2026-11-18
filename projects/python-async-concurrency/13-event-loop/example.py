import asyncio

async def wait():
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    loop.call_soon(future.set_result, 7)
    return await future

async def exercise():
    print("value", await wait())

if __name__ == "__main__":
    asyncio.run(exercise())
