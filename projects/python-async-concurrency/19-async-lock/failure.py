import asyncio


async def update(lock):
    async with lock:
        print("update acquired")
        raise ValueError("update failed")


async def exercise():
    lock = asyncio.Lock()
    try:
        await update(lock)
    except ValueError as error:
        print("error", error)
    async with lock:
        print("lock acquired again")


if __name__ == "__main__":
    asyncio.run(exercise())
