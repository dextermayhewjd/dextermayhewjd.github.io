import asyncio
import time


async def generate(rollout_id):
    print("start", rollout_id)
    await asyncio.sleep(0)
    print("end", rollout_id)
    return rollout_id


async def generate_blocking(rollout_id):
    print("start", rollout_id)
    time.sleep(0.01)
    print("end", rollout_id)
    return rollout_id


async def no_other_task():
    await generate(10)
    await generate(11)


async def another_task_is_ready():
    task_11 = asyncio.create_task(generate(11))
    await generate(10)
    await task_11


async def blocking_sleep():
    task_11 = asyncio.create_task(generate_blocking(11))
    await generate_blocking(10)
    await task_11


if __name__ == "__main__":
    for label, example in (
        ("A: no other task", no_other_task),
        ("B: another task is ready", another_task_is_ready),
        ("C: blocking sleep", blocking_sleep),
    ):
        print(label)
        asyncio.run(example())
