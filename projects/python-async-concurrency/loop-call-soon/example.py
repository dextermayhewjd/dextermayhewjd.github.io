import asyncio


def report():
    print("callback: start")
    print("callback: end")  # 普通回调：本次调用在这里连续执行到结束。
    return 7  # 这个返回值不会成为 Handle 中可等待的结果。


async def report_async():
    print("task: start")
    await asyncio.sleep(0)  # 暂停这份 Task，让循环执行其他已经就绪的工作。
    print("task: end")  # 循环随后恢复这份 Task，继续执行函数体。
    return 7  # Task 保存这个结果，等待它的调用方可以取得。


async def exercise():
    loop = asyncio.get_running_loop()  # 两份工作交给当前同一个循环。
    task = asyncio.create_task(report_async())  # 先安排协程，返回可等待的 Task。
    handle = loop.call_soon(report)  # 再登记普通函数，返回登记句柄 Handle。
    print("main: both scheduled")  # 默认调度下，两份工作都还没开始。
    result = await task  # 当前协程等 Task 结束，循环可以运行刚才安排的工作。
    print("main: task result", result)  # 得到 report_async 返回的 7。


if __name__ == "__main__":
    asyncio.run(exercise())
