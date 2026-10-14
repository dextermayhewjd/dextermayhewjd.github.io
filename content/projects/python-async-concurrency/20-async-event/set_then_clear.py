import asyncio


async def exercise():
    release = asyncio.Event()
    first = asyncio.create_task(release.wait())
    await asyncio.sleep(0)

    release.set()
    release.clear()
    print("already awakened", await first)

    second = asyncio.create_task(release.wait())
    await asyncio.sleep(0)
    print("new waiter blocked", not second.done())
    release.set()
    print("new waiter released", await second)


if __name__ == "__main__":
    asyncio.run(exercise())
