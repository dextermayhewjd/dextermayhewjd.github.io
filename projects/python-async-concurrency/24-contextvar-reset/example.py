import asyncio
from contextvars import ContextVar


current_id = ContextVar("current_id", default=None)


async def exercise():
    current_id.set(10)  # 模拟这份任务原本已经有一个值。
    print("before", current_id.get())

    token = current_id.set(20)  # 改成临时值，同时取得这一次修改的恢复凭据。
    try:
        print("temporary", current_id.get())  # 当前上下文现在读到 20。
    finally:
        current_id.reset(token)  # 还原这次修改前的绑定，恢复为 10。

    print("restored", current_id.get())


if __name__ == "__main__":
    asyncio.run(exercise())
