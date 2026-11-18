import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 沿用 33.1：取出当前事件循环。
    future = loop.create_future()  # 创建尚未完成的 Future，此时没有结果。
    print("created", future.done())  # False：还没有写入结果。
    future.set_result(7)  # 写入结果 7，同时把这个 Future 标记为完成。
    print("completed", future.done())  # True：现在已经完成。
    print("result", future.result())  # 读取已经写入的 7。
    print("await", await future)  # 已经完成，直接得到 7；这次不会挂起。


if __name__ == "__main__":
    asyncio.run(exercise())
