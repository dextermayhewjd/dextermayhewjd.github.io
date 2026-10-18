import asyncio


async def provide_samples(future):
    print("provider running")
    future.set_result([0, 1, 2])  # 提供者完成结果，让等待者可以恢复。
    print("provider after set")  # set_result 不会在此处直接执行等待者。


async def exercise():
    loop = asyncio.get_running_loop()
    future = loop.create_future()  # 结果尚未到；创建对象本身没有启动提供者。
    provider = asyncio.create_task(provide_samples(future))  # 另行安排提供结果的工作。
    print("before await")
    samples = await future  # 默认调度下，提供者尚未运行；本任务在这里等住。
    print("received", samples)
    await provider  # 确认我们创建的提供者任务已结束。


if __name__ == "__main__":
    asyncio.run(exercise())
