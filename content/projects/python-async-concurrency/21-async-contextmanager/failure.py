import asyncio

from example import boot_agent_sandbox


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
