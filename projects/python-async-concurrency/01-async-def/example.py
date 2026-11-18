import asyncio

async def generate(rollout_id):
    print("run", rollout_id)
    return rollout_id

def main():
    coro = generate(10)
    print("created")
    result = asyncio.run(coro)
    print("result", result)

if __name__ == "__main__":
    main()
