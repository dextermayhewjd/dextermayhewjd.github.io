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
    try:
        results = await asyncio.gather(task_10, task_11)
        print("results", results)
    except ValueError as error:
        print("gather error", error)

    print("remaining done", task_10.done())
    result = await task_10
    print("remaining result", result)


if __name__ == "__main__":
    asyncio.run(main())
