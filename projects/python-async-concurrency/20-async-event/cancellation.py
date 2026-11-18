import asyncio


async def wait_for_start(name, ready):
    print(name, "waiting")
    try:
        await ready.wait()
        print(name, "continued")
    finally:
        print(name, "cleanup")


async def exercise():
    ready = asyncio.Event()
    first = asyncio.create_task(wait_for_start("A", ready))
    second = asyncio.create_task(wait_for_start("B", ready))
    await asyncio.sleep(0)

    first.cancel()
    try:
        await first
    except asyncio.CancelledError:
        print("A cancelled")
    print("B still waiting", not second.done())
    ready.set()
    await second


if __name__ == "__main__":
    asyncio.run(exercise())
