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
            await asyncio.shield(task)
    except TimeoutError:
        print("waiter timed out")

    # 保留 task 引用，并在这次预算作用域之外负责等完、读取结果。
    print("result", await task)


if __name__ == "__main__":
    asyncio.run(exercise())
