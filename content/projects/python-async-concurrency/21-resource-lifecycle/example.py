import asyncio


async def exercise():
    image, instance_id = "demo-image", "case-1"
    print("boot", image, instance_id)
    await asyncio.sleep(0)
    sandbox = {"open": True}
    try:
        print("inside", sandbox["open"])
        await asyncio.sleep(0)
    finally:
        print("closing", instance_id)
        await asyncio.sleep(0)
        sandbox["open"] = False
        print("closed", instance_id)
    print("outside", sandbox["open"])


if __name__ == "__main__":
    asyncio.run(exercise())
