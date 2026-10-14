import asyncio

from example import _next, _produce


async def exercise():
    outputs = asyncio.Queue(maxsize=1)
    async with asyncio.TaskGroup() as group:
        consumer = group.create_task(_next(outputs))
        group.create_task(_produce(outputs))
    print("received", consumer.result())


if __name__ == "__main__":
    asyncio.run(exercise())
