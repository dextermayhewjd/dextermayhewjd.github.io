import asyncio


def report(label, finished):
    print(label)  # 只有循环真正调用 report，才会打印这份标签。
    if label == "later":
        finished.set_result(None)  # 标记延迟回调已经执行，允许主协程结束。


async def exercise():
    loop = asyncio.get_running_loop()
    finished = loop.create_future()  # 只用来等最后一个回调执行完。

    loop.call_later(0.1, report, "later", finished)  # 现在登记，约 0.1 秒后才到期。
    loop.call_soon(report, "soon", finished)  # 后登记，但直接进入就绪队列。
    print("both registered")  # 登记立即返回，两份回调此时都还没有执行。
    await finished  # 当前协程挂起，让循环执行回调并等待延迟回调完成。
    print("finished")


if __name__ == "__main__":
    asyncio.run(exercise())
