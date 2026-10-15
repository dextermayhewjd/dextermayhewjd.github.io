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
    entered = asyncio.Event()

    async def work():
        async with boot_agent_sandbox("demo-image", "case-cancel") as sandbox:
            print("inside", sandbox["open"])
            entered.set()
            await asyncio.sleep(3600)
            print("work resumed")

    task = asyncio.create_task(work())
    await entered.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled after cleanup")


if __name__ == "__main__":
    asyncio.run(exercise())
