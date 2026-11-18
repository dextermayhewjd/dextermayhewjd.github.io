import asyncio


async def exercise():
    future = asyncio.gather(asyncio.sleep(0, result=7))  # 沿用 gather，得到 asyncio Future；结果为 [7]。
    print("before", future.done())  # False：内部任务还没有完成。
    try:
        future.result()  # 只读取，不等待；此时会抛 InvalidStateError。
    except asyncio.InvalidStateError:
        print("not ready")
    await future  # 等内部任务完成，再继续下面的读取。
    print("after", future.done())  # True：已经完成。
    print("result", future.result())  # [7]：直接读取已有结果。
    print("exception", future.exception())  # None：成功完成，没有异常。


if __name__ == "__main__":
    asyncio.run(exercise())
