import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def boot_agent_sandbox():
    print("enter")
    try:
        yield "sandbox"
    finally:
        print("exit")

async def chunks():
    for value in ("A", "B"):
        await asyncio.sleep(0)
        yield value

async def exercise():
    async with boot_agent_sandbox() as sandbox:
        print(sandbox)
        async for chunk in chunks():
            print(chunk)

if __name__ == "__main__":
    asyncio.run(exercise())
