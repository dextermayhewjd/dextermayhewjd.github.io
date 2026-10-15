import asyncio
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples):
    # 线程池中的工作线程执行这个同步函数，返回样本列表。
    return list(range(num_samples))


async def get_samples_async(reader, num_samples):
    # 取得当前协程正在使用的事件循环；不创建新的循环。
    loop = asyncio.get_running_loop()
    # 现在就提交 get_samples(num_samples)，返回可 await 的 asyncio Future。
    future = loop.run_in_executor(reader, get_samples, num_samples)
    print("work submitted")
    # 结果未就绪时挂起当前协程；工作线程返回后，取得同一次调用的结果。
    return await future


async def exercise(reader):
    print("before submit")
    # 沿当前协程的调用链等待，不会额外创建一个 Task。
    samples = await get_samples_async(reader, 3)
    print("samples", samples)


if __name__ == "__main__":
    # 在事件循环外管理自选线程池；离开 with 时等待并关闭池。
    with ThreadPoolExecutor(max_workers=1) as reader:
        # 在主线程运行事件循环，把同一个 reader 交给协程使用。
        asyncio.run(exercise(reader))
    print("pool closed")
