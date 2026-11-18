import asyncio


async def generate(rollout_id, fail=False):
    print("start", rollout_id)
    try:
        if fail:
            raise ValueError(f"generation {rollout_id} failed")
        await asyncio.sleep(0.1)
        print("finished", rollout_id)
        return rollout_id
    finally:
        print("cleanup", rollout_id)


async def main():
    task_10 = asyncio.create_task(generate(10))
    task_11 = asyncio.create_task(generate(11, fail=True))
    results = await asyncio.gather(task_10, task_11, return_exceptions=True)
    print("results", results)
    for result in results:
        if isinstance(result, BaseException):
            print("error", type(result).__name__, result)
        else:
            print("result", result)


if __name__ == "__main__":
    asyncio.run(main())
