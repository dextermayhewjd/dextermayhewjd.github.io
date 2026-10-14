import asyncio


async def generate(rollout_id, seconds):
    await asyncio.sleep(seconds)
    return rollout_id


async def exercise():
    task_10 = asyncio.create_task(generate(10, 2))
    task_11 = asyncio.create_task(generate(11, 1))
    tasks = [task_10, task_11]

    # wait 返回 (done, pending)，两者都是 set，元素是 Task 对象。
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
    )
    print("done", len(done))
    print("pending", len(pending))

    for task in done:  # 返回时已完成的 Task 集合
        # 本例中任务已正常完成：直接取结果，再打印，不会重新执行任务。
        print("completed", await task)

    for task in pending:  # 返回时尚未完成的 Task 集合
        # 任务早已安排好，仍由事件循环管理，不是到这里才启动。
        # 若仍未完成，exercise 在 await 处挂起，等到任务完成后再打印。
        # 若此时已经完成，就直接取得结果。
        print("remaining", await task)


if __name__ == "__main__":
    asyncio.run(exercise())
