import asyncio
import time


async def generate(rollout_id, seconds, started_at):
    print(f"[{time.perf_counter() - started_at:.3f}s] generate {rollout_id}: sleep {seconds}s")
    await asyncio.sleep(seconds)
    print(f"[{time.perf_counter() - started_at:.3f}s] generate {rollout_id}: resumed")
    return rollout_id


async def main():
    started_at = time.perf_counter()
    async with asyncio.TaskGroup() as group:
        group.create_task(generate(10, 2, started_at))
        group.create_task(generate(11, 1, started_at))
        await asyncio.sleep(0)
        print(f"[{time.perf_counter() - started_at:.3f}s] main: inside group")
    print(f"[{time.perf_counter() - started_at:.3f}s] main: group finished")


if __name__ == "__main__":
    asyncio.run(main())
