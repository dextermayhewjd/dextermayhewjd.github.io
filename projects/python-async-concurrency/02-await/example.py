import asyncio

async def generate(rollout_id):
    print("start", rollout_id)
    await asyncio.sleep(0)
    print("end", rollout_id)
    return rollout_id

async def exercise():
    first = await generate(10)
    second = await generate(11)
    print("results", [first, second])

if __name__ == "__main__":
    asyncio.run(exercise())
