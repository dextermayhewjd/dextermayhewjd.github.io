import asyncio


async def exercise():
    release = asyncio.Event()
    release.set()
    release.set()
    print("first wait", await release.wait())
    print("second wait", await release.wait())

    release.clear()
    task = asyncio.create_task(release.wait())
    await asyncio.sleep(0)
    print("waiting after clear", not task.done())
    release.set()
    print("after next set", await task)


if __name__ == "__main__":
    asyncio.run(exercise())
