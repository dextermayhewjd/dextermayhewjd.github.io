import asyncio


async def increment(name, state, lock):
    print(name, "waiting")
    await lock.acquire()
    try:
        current = state["count"]
        print(name, "read", current)
        await asyncio.sleep(0)
        state["count"] = current + 1
        print(name, "wrote", state["count"])
    finally:
        lock.release()
    print(name, "released")


async def exercise():
    state = {"count": 0}
    lock = asyncio.Lock()
    async with asyncio.TaskGroup() as group:
        group.create_task(increment("A", state, lock))
        group.create_task(increment("B", state, lock))
    print("total", state["count"])


if __name__ == "__main__":
    asyncio.run(exercise())
