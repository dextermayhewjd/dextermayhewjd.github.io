import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 沿用 33.1，取得当前事件循环。
    started = loop.time()  # 读取循环的单调时钟，单位为秒；不是日期时间。
    deadline = started + 1.0  # 只计算一次：从起点开始，共用一秒预算。
    print(f"[{started:.3f}s] start")
    print(f"[{deadline:.3f}s] deadline")

    await asyncio.sleep(0.02)  # 模拟前一步等待；实际经过时间由运行环境决定。

    now = loop.time()  # 等待后，再读同一个时钟。
    remaining = deadline - now  # 从原截止读数扣除当前读数，不重新给一秒。
    print(f"[{now:.3f}s] now")
    print(f"[{remaining:.3f}s] remaining")


if __name__ == "__main__":
    asyncio.run(exercise())  # 建立并运行事件循环，让 exercise 能读取 loop。
