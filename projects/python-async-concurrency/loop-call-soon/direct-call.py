import asyncio


def report():
    print("report runs")  # 只有真正执行函数体，才会打印这一行。


async def exercise():
    loop = asyncio.get_running_loop()  # 取得当前循环，沿用 20.2 的用法。

    print("direct: before")
    report()  # 直接调用：现在执行 report，再继续下一行。
    print("direct: after")

    print("scheduled: before")
    loop.call_soon(report)  # 只登记 report，让循环稍后调用；这里不执行 report。
    print("scheduled: after")  # 当前协程继续运行，这一行先于已登记的 report。
    await asyncio.sleep(0)  # 让出执行机会，循环可以执行已登记的 report。
    print("scheduled: resumed")  # 当前协程恢复后继续。


if __name__ == "__main__":
    asyncio.run(exercise())
