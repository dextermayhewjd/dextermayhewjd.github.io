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
        result = await asyncio.wait_for(task, timeout=1)
        print("result", result)
    except TimeoutError:
        print("timeout")


if __name__ == "__main__":
    asyncio.run(exercise())
