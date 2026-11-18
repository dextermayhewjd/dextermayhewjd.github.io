import asyncio

from example import generate


async def exercise():
    semaphore = asyncio.Semaphore(1)
    try:
        await generate(10, semaphore, fail=True)
    except ValueError as error:
        print("error", error)
    print("result", await generate(11, semaphore))


if __name__ == "__main__":
    asyncio.run(exercise())
