import asyncio

async def _produce(outputs):
    for value in (10, 11):
        await outputs.put(value)
    await outputs.put(None)

async def _next(outputs):
    values = []
    while True:
        value = await outputs.get()
        if value is None:
            return values
        values.append(value)

async def exercise():
    outputs = asyncio.Queue(maxsize=1)
    _, values = await asyncio.gather(_produce(outputs), _next(outputs))
    print("received", values)

if __name__ == "__main__":
    asyncio.run(exercise())
