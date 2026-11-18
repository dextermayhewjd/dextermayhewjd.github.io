import asyncio
import time


def get_samples(num_samples):
    time.sleep(0.01)
    return list(range(num_samples))


async def exercise():
    print("before await")
    samples = await asyncio.to_thread(get_samples, 3)
    print("samples", samples)
    print("after await")


if __name__ == "__main__":
    asyncio.run(exercise())
