import asyncio
from contextvars import ContextVar


current_id = ContextVar("current_id", default=None)  # 创建一个对象，未设置时读取 None。


async def generate(number):
    current_id.set(number)  # 设置这份任务上下文中的值。
    await asyncio.sleep(0)  # 交还执行机会，其他任务也可以设置自己的值。
    return current_id.get()  # 恢复后读取本任务的值，不会读成另一任务的编号。


async def exercise():
    results = await asyncio.gather(generate(10), generate(11))  # 安排两份任务并收集结果。
    print(results)
    print(current_id.get())  # 本任务没有设置过，仍然读取默认值 None。


if __name__ == "__main__":
    asyncio.run(exercise())
