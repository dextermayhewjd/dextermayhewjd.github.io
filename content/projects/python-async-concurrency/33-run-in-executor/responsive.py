import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples, release):
    # 只有工作线程等通知；收到通知后才生成并返回列表。
    release.wait()
    return list(range(num_samples))


async def allow_read(release):
    print("other coroutine ran")
    # 另一份协程发出通知，让工作线程可以继续。
    release.set()


async def exercise(reader):
    release = threading.Event()  # 创建一次通知，显式传给双方共用。
    loop = asyncio.get_running_loop()  # 取得正在运行 exercise 的事件循环。
    # 立即提交工作；release 尚未设置，因此此时不可能取得结果。
    future = loop.run_in_executor(reader, get_samples, 3, release)
    # 安排另一份协程；它要等当前协程让出执行机会后才能运行。
    notifier = asyncio.create_task(allow_read(release))
    try:
        print("before await")
        samples = await future  # 结果未就绪，当前协程在这里挂起。
        print("samples", samples)
        await notifier  # 确认通知协程结束；本例中它已经完成。
    finally:
        release.set()  # 即使读取过程意外退出，也放行工作线程，避免池无法收尾。


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=1) as reader:
        asyncio.run(exercise(reader))  # 主线程运行协程，reader 的线程执行同步函数。
    print("pool closed")
