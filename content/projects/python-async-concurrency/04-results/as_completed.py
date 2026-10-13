import asyncio


async def generate(rollout_id, seconds):
    await asyncio.sleep(seconds)
    return rollout_id


async def exercise():
    task_10 = asyncio.create_task(generate(10, 2))
    task_11 = asyncio.create_task(generate(11, 1))
    tasks = [task_10, task_11]

    for completed in asyncio.as_completed(tasks):
        result = await completed
        print("result", result)


if __name__ == "__main__":
    asyncio.run(exercise())
