import asyncio

async def generate(rollout_id):
    await asyncio.sleep(0)
    return rollout_id

async def exercise():
    tasks = [asyncio.create_task(generate(i)) for i in (10, 11)]
    print("scheduled", len(tasks))
    results = await asyncio.gather(*tasks)
    print("results", results)

if __name__ == "__main__":
    asyncio.run(exercise())
