import asyncio


async def wait_for_start(name, ready):
    print(name, "waiting")
    await ready.wait()
    print(name, "continued")


async def exercise():
    ready = asyncio.Event()
    async with asyncio.TaskGroup() as group:
        group.create_task(wait_for_start("A", ready))
        group.create_task(wait_for_start("B", ready))
        await asyncio.sleep(0)
        ready.set()
        print("main after set")
    print("all finished")


if __name__ == "__main__":
    asyncio.run(exercise())
