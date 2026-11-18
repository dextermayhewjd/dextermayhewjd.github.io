import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 沿用 20.2，取得当前循环。
    future = loop.create_future()  # 创建一份尚未完成的结果对象；没有启动工作。
    print("future created")
    samples = [0, 1, 2]
    future.set_result(samples)  # 保存这份列表，并把 future 标为成功完成。
    print("result stored")
    received = await future  # 已经完成，直接取得保存的列表。
    print("received", received)
    print("same value", received is samples)  # 取得保存的对象，没有复制列表。
    print("again", await future)  # 再等同一个 Future，仍取得同一份结果。


if __name__ == "__main__":
    asyncio.run(exercise())
