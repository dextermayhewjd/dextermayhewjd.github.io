import asyncio

from example import generate


async def exercise():
    semaphore = asyncio.Semaphore(1)
    task = asyncio.create_task(generate(10, semaphore))
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled", 10)
    print("result", await generate(11, semaphore))


if __name__ == "__main__":
    asyncio.run(exercise())
