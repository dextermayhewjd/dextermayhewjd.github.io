import asyncio


async def generate(rollout_id, seconds):
    try:
        print("generate", rollout_id, "started")
        await asyncio.sleep(seconds)
        return rollout_id
    finally:
        print("cleanup", rollout_id)


async def exercise():
    task = asyncio.create_task(generate(10, 60))

    # 本例先让任务进入 try 中的等待，再发出取消请求。
    await asyncio.sleep(0)
    requested = task.cancel()
    print("cancel requested", requested)
    print("done immediately", task.done())

    # cancel() 发出请求；await 等它处理取消并执行 finally。
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled")

    print("done after await", task.done())


if __name__ == "__main__":
    asyncio.run(exercise())
