import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples, release):
    # 工作线程等 release 的通知；标志未设置时，阻塞的是这个工作线程。
    release.wait()
    return list(range(num_samples))


async def allow_read(release):
    print("other coroutine ran")
    # 设置 Event 的通知标志，放行工作线程；这一步不会直接写入 Future。
    release.set()


async def get_samples_async(reader, num_samples):
    release = threading.Event()  # 只创建这一个通知对象，初始标志为 False。
    loop = asyncio.get_running_loop()  # 取得正在运行 get_samples_async 的事件循环。
    # 立即提交工作；release 尚未设置，因此此时不可能取得结果。
    future = loop.run_in_executor(reader, get_samples, num_samples, release)
    # 安排另一份协程；它要等当前协程让出执行机会后才能运行。
    notifier = asyncio.create_task(allow_read(release))
    try:
        print("before await")
        samples = await future  # 结果未就绪，当前协程在这里挂起。
        print("samples", samples)
        await notifier  # 本例中它已完成，直接通过；接回这份 Task 的完成或异常。
    finally:
        release.set()  # 即使读取过程意外退出，也放行工作线程，避免池无法收尾。


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=1) as reader:
        asyncio.run(get_samples_async(reader, 3))  # 主线程运行协程，reader 的线程执行同步函数。
    print("pool closed")
