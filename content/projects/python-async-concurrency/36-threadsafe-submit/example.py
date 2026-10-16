import asyncio


async def generate():
    print("loop: generate")  # 在主线程的事件循环中执行。
    return 7


def submit(loop):
    # 在工作线程创建协程对象，再交给主线程的循环运行。
    future = asyncio.run_coroutine_threadsafe(generate(), loop)
    value = future.result()  # 未完成时，当前工作线程在这里等待结果。
    print("worker: received", value)
    return value


async def exercise():
    loop = asyncio.get_running_loop()  # 取得主线程已经运行的循环。
    print("main: wait worker")
    value = await asyncio.to_thread(submit, loop)  # exercise 等待；循环仍能运行 generate。
    print("main: received", value)


if __name__ == "__main__":
    asyncio.run(exercise())
