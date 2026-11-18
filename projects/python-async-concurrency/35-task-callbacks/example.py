import asyncio


async def generate():
    return 7  # Task 完成时，保存这个返回值。


def on_done(done_task):
    print("callback", done_task.result())  # 收到已完成的 Task，读取它的结果 7。


async def exercise():
    task = asyncio.create_task(generate())  # 安排 generate 运行。
    task.add_done_callback(on_done)  # 登记 post hook；任务结束后调用 on_done(task)。
    print("registered", task.done())  # False：此时只完成登记，任务还没运行。
    await task  # 等 generate 结束；回调由事件循环调用，不是这一行手动调用。


if __name__ == "__main__":
    asyncio.run(exercise())
