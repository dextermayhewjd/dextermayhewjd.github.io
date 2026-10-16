import asyncio
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples):
    # 工作线程：提交后被 reader 安排执行，不必等主协程执行 await。
    return list(range(num_samples))


async def get_samples_async(reader, num_samples):
    # 主协程 1：取得当前事件循环；这一步还没有提交 get_samples。
    loop = asyncio.get_running_loop()
    # 主协程 2：现在提交 get_samples(num_samples)；工作线程就可以开始执行。
    future = loop.run_in_executor(reader, get_samples, num_samples)
    print("work submitted")  # 主协程 3：提交已返回；不表示取数刚开始或已经结束。
    # 主协程 4：等这次结果；Future 未就绪时挂起，就绪时取得列表。
    samples = await future
    print("samples", samples)  # 主协程 5：已取得 get_samples 返回的列表。
    return samples


if __name__ == "__main__":
    # reader 是本例的线程池变量名，对应第 31 课的 executor。
    with ThreadPoolExecutor(max_workers=1) as reader:
        # 主线程运行这一个协程；reader 中的工作线程运行同步取数函数。
        asyncio.run(get_samples_async(reader, 3))
    print("pool closed")
