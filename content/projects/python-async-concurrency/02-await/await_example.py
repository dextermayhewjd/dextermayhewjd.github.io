import asyncio

async def generate(rollout_id):
    print("run", rollout_id)
    return rollout_id

async def main():
    coro = generate(10)
    print("created")
    result = await coro
    print("result", result)

if __name__ == "__main__":
    asyncio.run(main())
