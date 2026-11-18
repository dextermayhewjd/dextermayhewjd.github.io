import asyncio


async def exercise():
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    print("pending done", future.done())  # 尚未完成，返回 False。
    try:
        future.result()  # 只读取，不等待；尚未完成时抛 InvalidStateError。
    except asyncio.InvalidStateError:
        print("pending result InvalidStateError")

    future.set_exception(ValueError("read failed"))  # 记录失败并完成 Future；此处不抛该错误。
    print("failed done", future.done())  # 失败也算完成，因此是 True。
    print("stored error", future.exception())  # 读取已保存的异常对象。
    try:
        await future  # 等待失败的 Future，在这里收到保存的 ValueError。
    except ValueError as error:
        print("await raised", error)

    try:
        future.set_result([0, 1, 2])  # 已失败完成，不能再覆盖成成功。
    except asyncio.InvalidStateError:
        print("second completion InvalidStateError")


if __name__ == "__main__":
    asyncio.run(exercise())
