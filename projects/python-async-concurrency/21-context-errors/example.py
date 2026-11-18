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
    try:
        async with boot_agent_sandbox("demo-image", "case-error") as sandbox:
            print("inside", sandbox["open"])
            raise ValueError("work failed")
    except ValueError as error:
        print("error", error)
    print("outside", sandbox["open"])


if __name__ == "__main__":
    asyncio.run(exercise())
