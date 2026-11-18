import asyncio
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples):
    print("get_samples called")  # 只有工作线程实际执行函数时，才打印这一行。
    return list(range(num_samples))


async def get_samples_async(executor_future):
    # 已经提交过的工作：只包装它的 Future，不重新执行 get_samples。
    future = asyncio.wrap_future(executor_future)
    # 结果未就绪时挂起当前协程；就绪后取得同一次工作的列表。
    samples = await future
    print("samples", samples)
    return samples


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=1) as reader:
        # 沿用第 31 课：在这里提交一次，得到 concurrent.futures.Future。
        executor_future = reader.submit(get_samples, 3)
        # 把已经拿到的 Future 传入协程，由协程接回结果。
        asyncio.run(get_samples_async(executor_future))
    print("pool closed")
