import asyncio

async def generate(rollout_id):
    try:
        await asyncio.sleep(60)
        return rollout_id
    finally:
        print("cleanup", rollout_id)

async def exercise():
    task = asyncio.create_task(generate(10))
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled")
    try:
        async with asyncio.timeout(0.01):
            await asyncio.sleep(60)
    except TimeoutError:
        print("timeout")

if __name__ == "__main__":
    asyncio.run(exercise())
