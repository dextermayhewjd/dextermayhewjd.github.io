import asyncio
from contextlib import asynccontextmanager


@asynccontextmanager
async def boot_agent_sandbox(image, instance_id):
    print("boot", image, instance_id)
    await asyncio.sleep(0)
    sb = {"open": True}
    try:
        yield sb
    finally:
        print("closing", instance_id)
        await asyncio.sleep(0)
        sb["open"] = False
        print("closed", instance_id)


async def exercise():
    manager = boot_agent_sandbox("demo-image", "case-1")
    print("manager created")
    async with manager as sandbox:
        print("inside", sandbox["open"])
        await asyncio.sleep(0)
    print("outside", sandbox["open"])


if __name__ == "__main__":
    asyncio.run(exercise())
