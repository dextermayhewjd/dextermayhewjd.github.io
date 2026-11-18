import asyncio

from example import ensure_async_iterator


async def exercise():
    stream = ensure_async_iterator([10, 11])
    print("stream created")
    try:
        await stream
    except TypeError:
        print("await stream: TypeError")
    try:
        for item in stream:
            print(item)
    except TypeError:
        print("for item in stream: TypeError")


if __name__ == "__main__":
    asyncio.run(exercise())
