import asyncio


async def generate(rollout_id, seconds, fail=False):
    await asyncio.sleep(seconds)
    if fail:
        raise ValueError(f"generation {rollout_id} failed")
    return rollout_id


async def exercise():
    task = asyncio.create_task(generate(10, 0))

    # 默认调度下，这里还没有让出执行机会，task 尚未完成。
    print("pending done", task.done())
    try:
        task.result()
    except asyncio.InvalidStateError:
        print("pending result InvalidStateError")
    try:
        task.exception()
    except asyncio.InvalidStateError:
        print("pending exception InvalidStateError")

    # await 先等任务正常完成；下面的方法只读取已经保存的状态与结果。
    await task
    print("success done", task.done())
    print("success result", task.result())
    print("success exception", task.exception())

    # wait 只等待完成情况；失败异常随后由读取方法显式取出。
    failed_task = asyncio.create_task(generate(11, 0, fail=True))
    await asyncio.wait([failed_task], return_when=asyncio.FIRST_COMPLETED)
    print("failed done", failed_task.done())
    print("failed exception", failed_task.exception())
    try:
        failed_task.result()
    except ValueError as error:
        print("failed result ValueError:", error)


if __name__ == "__main__":
    asyncio.run(exercise())
