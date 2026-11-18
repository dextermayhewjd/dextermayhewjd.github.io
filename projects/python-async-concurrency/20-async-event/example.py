import asyncio


async def exercise():
    release = asyncio.Event()
    group = ["sample"]

    async def fetch(count):
        print("fetch waiting")
        allowed = await release.wait()
        print("fetch resumed", allowed)
        return [group]

    task = asyncio.create_task(fetch(1))
    await asyncio.sleep(0)
    print("main set")
    release.set()
    print("main after set")
    print("received", await task)


if __name__ == "__main__":
    asyncio.run(exercise())
