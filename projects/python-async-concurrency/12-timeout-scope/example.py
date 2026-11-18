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
        async with asyncio.timeout(0.3):
            await generate(10, 0.2)
            await generate(20, 0.2)
            print("both finished")
    except TimeoutError:
        print("shared budget expired")

    print("outside timeout block")


if __name__ == "__main__":
    asyncio.run(exercise())
