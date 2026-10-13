import asyncio

async def generate(rollout_id, semaphore, state):
    async with semaphore:
        state["active"] += 1
        state["peak"] = max(state["peak"], state["active"])
        try:
            await asyncio.sleep(0)
            return rollout_id
        finally:
            state["active"] -= 1

async def exercise():
    semaphore = asyncio.Semaphore(2)
    state = {"active": 0, "peak": 0}
    results = await asyncio.gather(*(generate(i, semaphore, state) for i in range(5)))
    print("results", results)
    print("peak", state["peak"])

if __name__ == "__main__":
    asyncio.run(exercise())
