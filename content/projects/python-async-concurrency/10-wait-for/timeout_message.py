import asyncio


async def generate(rollout_id, seconds):
    try:
        await asyncio.sleep(seconds)
        return rollout_id
    finally:
        print("cleanup", rollout_id)


async def exercise():
    task = asyncio.create_task(generate(10, 60))

    try:
        return await asyncio.wait_for(task, timeout=0.1)
    except TimeoutError as error:
        raise TimeoutError("任务 10 未在等待时限内完成") from error


if __name__ == "__main__":
    try:
        asyncio.run(exercise())
    except TimeoutError as error:
        print("timeout:", error)
