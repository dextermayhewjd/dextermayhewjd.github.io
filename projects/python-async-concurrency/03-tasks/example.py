import asyncio
import time

async def generate(rollout_id, seconds, started_at):
    print(f"[{time.perf_counter() - started_at:.3f}s] generate {rollout_id}: sleep {seconds}s")
    await asyncio.sleep(seconds)
    print(f"[{time.perf_counter() - started_at:.3f}s] generate {rollout_id}: resumed")
    return rollout_id

async def main():
    started_at = time.perf_counter()
    task_10 = asyncio.create_task(generate(10, 2, started_at))
    task_11 = asyncio.create_task(generate(11, 1, started_at))
    print(f"[{time.perf_counter() - started_at:.3f}s] main: tasks scheduled")
    result_10 = await task_10
    print(f"[{time.perf_counter() - started_at:.3f}s] main: received {result_10}")
    result_11 = await task_11
    print(f"[{time.perf_counter() - started_at:.3f}s] main: received {result_11}")
    print("results", [result_10, result_11])

if __name__ == "__main__":
    asyncio.run(main())
