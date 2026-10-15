import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 取得当前循环，继续使用同一个时钟。
    deadline = loop.time()  # 故意给零秒预算：截止位置就是现在。
    await asyncio.sleep(0)  # 让出一次执行机会；不会自动产生超时异常。
    remaining = deadline - loop.time()  # 现在已经到达或越过截止位置。
    print("budget expired", remaining <= 0)
    print("coroutine still running")  # 说明读时钟、算预算本身不会取消协程。
    if remaining <= 0:
        print("skip new work")  # 调用方根据预算作决定，不再开始下一份工作。
        return


if __name__ == "__main__":
    asyncio.run(exercise())  # 运行这个独立的零预算实验。
