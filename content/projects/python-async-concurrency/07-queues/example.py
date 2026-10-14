import asyncio


async def _produce(outputs):
    for value in (10, 11):
        print("put request", value)
        await outputs.put(value)
        print("put done", value)
    await outputs.put(None)
    print("producer finished")


async def _next(outputs):
    values = []
    while True:
        print("get request")
        value = await outputs.get()
        if value is None:
            print("consumer finished")
            return values
        print("get", value)
        await asyncio.sleep(0.1)
        print("processed", value)
        values.append(value)


async def exercise():
    outputs = asyncio.Queue(maxsize=1)
    consumer = asyncio.create_task(_next(outputs))
    producer = asyncio.create_task(_produce(outputs))
    _, values = await asyncio.gather(producer, consumer)
    print("received", values)


if __name__ == "__main__":
    asyncio.run(exercise())
