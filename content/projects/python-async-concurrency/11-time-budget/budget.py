import asyncio
import time


async def generate(rollout_id, seconds):
    await asyncio.sleep(seconds)
    return rollout_id


async def exercise():
    budget = 0.1
    deadline = time.monotonic() + budget

    # 模拟前面的准备工作，它也消耗同一份预算。
    await asyncio.sleep(0.02)
    remaining = deadline - time.monotonic()

    try:
        if remaining <= 0:
            raise TimeoutError("budget expired")
        task = asyncio.create_task(generate(10, 60))
        await asyncio.wait_for(task, timeout=remaining)
    except TimeoutError:
        print("budget expired")


if __name__ == "__main__":
    asyncio.run(exercise())
