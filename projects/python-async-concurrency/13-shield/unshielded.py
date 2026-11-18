import asyncio


async def generate(rollout_id, seconds):
    print("start", rollout_id)
    try:
        await asyncio.sleep(seconds)
        print("finished", rollout_id)
        return rollout_id
    finally:
        print("cleanup", rollout_id)


async def exercise():
    task = asyncio.create_task(generate(10, 0.2))
    try:
        async with asyncio.timeout(0.05):
            await task
    except TimeoutError:
        print("waiter timed out")

    try:
        print("result", await task)
    except asyncio.CancelledError:
        print("inner task cancelled")


if __name__ == "__main__":
    asyncio.run(exercise())
