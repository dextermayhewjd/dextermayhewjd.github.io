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
    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(generate(10, fail=True))
            group.create_task(generate(11, fail=True))
        print("group finished")
    except* ValueError as errors:
        print("caught", type(errors).__name__)
        for error in errors.exceptions:
            print("error", error)


if __name__ == "__main__":
    asyncio.run(main())
