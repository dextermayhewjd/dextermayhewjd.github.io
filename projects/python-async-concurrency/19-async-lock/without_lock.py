import asyncio


async def increment(name, state):
    current = state["count"]
    print(name, "read", current)
    await asyncio.sleep(0)
    state["count"] = current + 1
    print(name, "wrote", state["count"])


async def exercise():
    state = {"count": 0}
    async with asyncio.TaskGroup() as group:
        group.create_task(increment("A", state))
        group.create_task(increment("B", state))
    print("total", state["count"])


if __name__ == "__main__":
    asyncio.run(exercise())
