import asyncio


async def generate(rollout_id, seconds):
    await asyncio.sleep(seconds)
    return rollout_id


async def exercise():
    task_10 = asyncio.create_task(generate(10, 2))
    task_11 = asyncio.create_task(generate(11, 1))
    tasks = [task_10, task_11]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    print("done", sorted(task.result() for task in done))
    print("pending", len(pending))
    print("remaining", await asyncio.gather(*pending))


if __name__ == "__main__":
    asyncio.run(exercise())
