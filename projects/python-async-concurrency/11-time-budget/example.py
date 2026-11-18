import asyncio
import time


async def generate(rollout_id, seconds):
    try:
        await asyncio.sleep(seconds)
        return rollout_id
    finally:
        print("cleanup start", rollout_id)
        await asyncio.sleep(0.2)
        print("cleanup finished", rollout_id)


async def exercise():
    task = asyncio.create_task(generate(10, 60))
    started = time.perf_counter()

    try:
        await asyncio.wait_for(task, timeout=0.1)
    except TimeoutError:
        elapsed = time.perf_counter() - started
        print(f"[{elapsed:.3f}s] timeout")


if __name__ == "__main__":
    asyncio.run(exercise())
