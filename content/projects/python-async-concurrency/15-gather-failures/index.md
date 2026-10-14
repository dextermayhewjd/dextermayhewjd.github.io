---
title: "10.1 · asyncio.gather：收集报错，任务仍可继续"
description: "先分清任务运行和结果收集：默认 gather 报错，不会因此取消其他已创建的 Task。"
weight: 100
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. asyncio.gather：先用一句话理解本课

**某个任务失败时，默认 gather 会让这次整组取结果提前报错，但不会因此取消其他已经创建的 Task；它们仍可继续执行。**

先把前面学过的两件事分开：

| 代码 | 在本例中做什么 |
| --- | --- |
| `create_task(...)` | 创建并安排 Task，让这份工作可以运行 |
| `gather(...)` | 等待这些 Task，收集它们的结果 |

第 06 单元里两份任务都成功，所以能拿到完整结果列表。现在只增加一个情况：**任务 11 失败时，任务 10 还在运行。** 本课要看清：这次结果收集会怎样结束，任务 10 又会怎样继续。

<span id="gather-failure"></span>

## 2. 默认 gather：收集报错后，任务 10 继续完成

沿用 `generate` 和任务 10、11。参数 `fail=True` 让任务 11 在开头抛出 `ValueError`；任务 10 正常等待后返回编号。`cleanup` 只是 `finally` 中的收尾日志，不表示任务一定成功。

```python
import asyncio


async def generate(rollout_id, fail=False):
    print("start", rollout_id)
    try:
        if fail:
            raise ValueError(f"generation {rollout_id} failed")
        await asyncio.sleep(0.1)
        print("finished", rollout_id)
        return rollout_id
    finally:
        print("cleanup", rollout_id)


async def main():
    task_10 = asyncio.create_task(generate(10))
    task_11 = asyncio.create_task(generate(11, fail=True))
    try:
        results = await asyncio.gather(task_10, task_11)
        print("results", results)
    except ValueError as error:
        print("gather error", error)

    print("remaining done", task_10.done())
    result = await task_10
    print("remaining result", result)


if __name__ == "__main__":
    asyncio.run(main())
```

[下载 example.py](example.py) · 运行：`python3 example.py`。本机 CPython 3.12.3 默认调度下的实际输出：

```text
start 10
start 11
cleanup 11
gather error generation 11 failed
remaining done False
finished 10
cleanup 10
remaining result 10
```

## 3. await gather 与 await task：分别在哪里等、拿到什么？

只跟着 `main` 看三个位置：

1. **`await gather(...)`：尝试收齐结果。** 任务 11 失败，异常传到这里；这次没有取得完整列表，`results = ...` 没有完成赋值，下一行打印也被跳过。
2. **`except ValueError`：处理这次收集的错误。** `main` 打印 `gather error`。此时任务 10 没被取消，`task_10.done()` 为 `False`。
3. **`await task_10`：继续等待原来的任务 10。** 它正常完成后，这次等待取得返回值 `10`。这没有重新创建或重新运行任务。

所以输出里可以先有 `gather error`，后有 `finished 10`：**报错结束的是这次整组收集，任务 10 的工作仍在继续。** 实际程序中，其他任务也可能已经完成；gather 报错本身不决定它们的完成状态。

<span id="gather-cleanup"></span>

这里由 `main` 保留任务 10，并负责最后等完。如果捕获错误后直接让 `main` 返回，`asyncio.run` 会在关闭时取消尚未结束的 Task。因此，“gather 不取消其他任务”不代表可以让程序退出后，它们还一直运行。

如果不再需要剩余结果，回看[第 09 单元的 cancel 与 await](../09-task-cancellation/)即可；[取消剩余任务的补充实验](cancel_remaining.py)也保留供复习，这里先不增加一条处理分支。

## 4. asyncio.gather：带走三条结论

1. **创建任务与收集结果是两件事。** 本例先用 `create_task` 安排工作，再用 gather 收集结果。
2. **默认 gather 因子任务错误而报错，不会因此取消其他 Task。** 这次拿不到完整列表，其他任务仍可继续运行。
3. **继续运行的任务仍要有人等完并读取结果。** `await task_10` 等的是原来的工作，不会重新启动它。

自查：为什么 `gather error` 后还能出现 `finished 10`？最后的 `await task_10` 是启动任务，还是等待并读取已有任务的结果？

<span id="gather-return-exceptions"></span>

下一节只增加一个要求：**有一份失败，也希望一次收齐每份任务的成功或失败情况。** 进入 [10.2 · return_exceptions=True：收齐结果与异常](../15-gather-exceptions/)。[原收集异常示例下载](collect_exceptions.py)仍保留。

{{< python-async-slime title="按需阅读：Slime 应用与本节源码位置" >}}

## _produce：gather 报错以后，谁负责剩余任务？

主例子是独立标准库实验。下面才是 Slime 固定快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的原代码。

进入 `_GenerationActor._produce` 的结束部分：前面已经创建任务并保存在 `tasks` 中，这里先用默认 gather 等待。正常返回或异常离开 `try` 时，都要执行后面的 `finally`。

<span id="source-source-2"></span>

{{< source-reference id="source-1" >}}

取消剩余任务是调用方在 `finally` 中明确执行的动作，不是默认 gather 自动做的。最后一行用下一节的收集方式等它们收尾；读完 10.2 再回看即可。

<section id="source-usage-locations">

## 本节对应的源码位置

[fully_async_distributed.py:338–342](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_distributed.py#L338-L342)：`_GenerationActor._produce` 在退出时主动取消并等待任务。

</section>

语义核对：[Python 3.12 asyncio.gather](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.gather)、[asyncio.run 的退出](https://docs.python.org/3.12/library/asyncio-runner.html#asyncio.run)。全部调用位置仍见[第 06 单元的源码索引](../05-gather/#source-usage-locations)。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：09 · Task.cancel：请求取消并等待收尾](../09-task-cancellation/) · [下一节：10.2 · return_exceptions=True：收齐结果与异常](../15-gather-exceptions/) · [完整学习路线](../learning-route/)
