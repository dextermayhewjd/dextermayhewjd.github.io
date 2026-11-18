import asyncio


async def generate(rollout_id, seconds):
    print("start", rollout_id)
    try:
        await asyncio.sleep(seconds)
        print("finished", rollout_id)
        return rollout_id
    finally:
        print("cleanup", rollout_id)


async def exercise():
    try:
        await asyncio.wait_for(generate(10, 0.2), timeout=0.3)
        await asyncio.wait_for(generate(20, 0.2), timeout=0.3)
        print("both finished")
    except TimeoutError:
        print("individual wait expired")

    print("outside timeout block")


if __name__ == "__main__":
    asyncio.run(exercise())
