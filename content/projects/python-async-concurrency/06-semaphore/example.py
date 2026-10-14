import asyncio


async def generate(rollout_id, semaphore, fail=False):
    print("waiting", rollout_id)
    async with semaphore:
        print("entered", rollout_id)
        try:
            await asyncio.sleep(0.1)
            if fail:
                raise ValueError(f"generation {rollout_id} failed")
            print("finished", rollout_id)
            return rollout_id
        finally:
            print("cleanup", rollout_id)


async def exercise():
    semaphore = asyncio.Semaphore(2)
    tasks = []
    for rollout_id in range(10, 15):
        tasks.append(asyncio.create_task(generate(rollout_id, semaphore)))
    print("tasks scheduled", len(tasks))
    print("results", await asyncio.gather(*tasks))


if __name__ == "__main__":
    asyncio.run(exercise())
