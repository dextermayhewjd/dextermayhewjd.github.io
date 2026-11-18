import asyncio


async def generate(rollout_id, seconds):
    print("start", rollout_id)
    try:
        await asyncio.sleep(seconds)
        raise ValueError(f"generation {rollout_id} failed")
    finally:
        print("cleanup", rollout_id)


async def exercise():
    task = asyncio.create_task(generate(10, 0.2))
    try:
        async with asyncio.timeout(0.05):
            await asyncio.shield(task)
    except TimeoutError:
        print("waiter timed out")

    try:
        print("result", await task)
    except ValueError as error:
        print("error", error)


if __name__ == "__main__":
    asyncio.run(exercise())
