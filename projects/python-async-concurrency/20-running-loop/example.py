import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 取得正在运行本协程的循环，不创建新循环。
    same_loop = asyncio.get_running_loop()  # 同一线程、同一次运行，取得同一个对象。
    print("same loop", loop is same_loop)


if __name__ == "__main__":
    asyncio.run(exercise())  # 建立并运行循环；协程结束后完成收尾并关闭它。
    try:
        asyncio.get_running_loop()  # run 已返回，当前线程没有正在运行的循环。
    except RuntimeError:
        print("outside run: no running loop")
