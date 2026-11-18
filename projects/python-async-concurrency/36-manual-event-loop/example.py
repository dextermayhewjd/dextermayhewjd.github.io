import asyncio


async def generate():
    print("generate start")
    await asyncio.sleep(0)  # 暂停一次，再由正在运行的循环继续推进。
    return 7


if __name__ == "__main__":
    loop = asyncio.new_event_loop()  # 创建循环对象，此时还没有开始运行。
    asyncio.set_event_loop(loop)  # 把它关联到当前线程，也不会开始运行。
    try:
        print("before run")
        value = loop.run_until_complete(generate())  # 运行循环，等协程完成并取得 7。
        print("result", value)
    finally:
        asyncio.set_event_loop(None)  # 解除当前线程与循环的关联。
        loop.close()  # 循环已经停止运行，关闭它并释放资源。
        print("closed")
