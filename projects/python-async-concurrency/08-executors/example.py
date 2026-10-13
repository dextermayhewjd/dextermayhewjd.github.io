import asyncio
from concurrent.futures import ThreadPoolExecutor

def get_samples(num_samples):
    return list(range(num_samples))

async def get_samples_async(reader, num_samples):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(reader, get_samples, num_samples)

async def exercise(reader):
    print("to_thread", await asyncio.to_thread(get_samples, 3))
    print("reader", await get_samples_async(reader, 3))

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=1) as reader:
        asyncio.run(exercise(reader))
