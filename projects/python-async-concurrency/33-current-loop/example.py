import asyncio


async def exercise():
    print("inside coroutine")
    # 取出当前正在运行这个协程的事件循环。
    loop = asyncio.get_running_loop()
    # 再取一次，仍然是当前这一个循环，不会新建循环。
    same_loop = asyncio.get_running_loop()
    print("same loop", loop is same_loop)  # True：两个变量指向同一个对象。


if __name__ == "__main__":
    print("before run")
    asyncio.run(exercise())  # 沿用第 01 课的入口，运行协程并等它结束。
    print("after run")
