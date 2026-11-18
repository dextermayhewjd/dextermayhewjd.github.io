import asyncio


async def generate(rollout_id, seconds, fail=False):
    await asyncio.sleep(seconds)
    if fail:
        raise ValueError(f"generation {rollout_id} failed")
    return rollout_id


async def exercise():
    task_10 = asyncio.create_task(generate(10, 2))
    task_11 = asyncio.create_task(generate(11, 1, fail=True))
    tasks = [task_10, task_11]

    for completed in asyncio.as_completed(tasks):
        try:
            result = await completed
        except ValueError as error:
            print("error", error)
        else:
            print("result", result)


if __name__ == "__main__":
    asyncio.run(exercise())
