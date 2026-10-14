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
        await asyncio.gather(task_10, task_11)
    except ValueError as error:
        print("gather error", error)
        task_10.cancel()
        try:
            await task_10
        except asyncio.CancelledError:
            print("remaining cancelled")


if __name__ == "__main__":
    asyncio.run(main())
