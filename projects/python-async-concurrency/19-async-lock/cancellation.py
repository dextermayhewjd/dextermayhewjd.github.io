import asyncio


async def hold(lock):
    async with lock:
        print("holder acquired")
        try:
            await asyncio.sleep(3600)
        finally:
            print("holder cleanup")


async def exercise():
    lock = asyncio.Lock()
    task = asyncio.create_task(hold(lock))
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("holder cancelled")
    async with lock:
        print("lock acquired again")


if __name__ == "__main__":
    asyncio.run(exercise())
