import asyncio


async def generate(rollout_id):
    print("start", rollout_id)
    await asyncio.sleep(0)
    print("end", rollout_id)
    return rollout_id


async def with_assignment():
    first = await generate(10)
    second = await generate(11)


async def without_assignment():
    await generate(10)
    await generate(11)


if __name__ == "__main__":
    print("A: with assignment")
    asyncio.run(with_assignment())
    print("B: without assignment")
    asyncio.run(without_assignment())
