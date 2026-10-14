---
title: "08 · done、result、exception：读取 Task 的状态与结果"
description: "承接 wait，区分判断是否结束、读取返回值和读取异常；三个方法都不会等待任务完成。"
weight: 80
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 拿到了 Task，怎样查看它现在的情况？

1. **上一课已经会了：** `wait` 返回 `done`、`pending` 两组 Task，再用 `await task` 等待并取得结果。
2. **现在多了一个要求：** 拿到某一个 Task 后，先查看它结束没有；已经结束时，再读取返回值或失败异常。
3. **先看原来的办法：** `await task` 可以等待任务。如果任务尚未完成，调用方会挂起；它解决的是“等到结果”，而这次希望先进行一次不等待的检查。

这次只增加三个方法：`task.done()`、`task.result()`、`task.exception()`。它们都立即检查或读取当前状态，不会替调用方等到任务完成。

特别注意两个相似的名字：上一课的 **`done` 是变量，装着一组 Task**；这里的 **`task.done()` 是方法，返回一个布尔值**。

## 2. 用同一个实验观察三种情况

沿用 `generate` 的等待和返回编号行为，增加 `fail=False` 参数：默认正常返回；传入 `fail=True` 时，在等待后抛出 `ValueError`，用来观察失败的 Task。

先预测三个问题：任务尚未完成时能否直接读结果？正常结束后有没有异常？失败也算“已经结束”吗？

```python
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
```

[下载 example.py](example.py) · 运行：`python3 -W error example.py`。本例使用 Python 3.12 的默认任务调度，不设置提前执行任务的工厂。

本机 Python 3.12.3 的运行输出为：

```text
pending done False
pending result InvalidStateError
pending exception InvalidStateError
success done True
success result 10
success exception None
failed done True
failed exception generation 11 failed
failed result ValueError: generation 11 failed
```

这里的 `try/except` 只用于捕获正在观察的异常，让实验继续走到下一步。它不会重试、重新启动任务，也不会把失败改成成功。

<span id="task-results"></span>
<span id="task-done"></span>

## 3. 尚未完成：检查返回 False，直接读取会报错

`create_task` 先安排任务。在本例的默认调度下，紧接着执行的几次读取都没有挂起调用方，任务 10 还没有得到执行机会。

1. **`task.done()` 返回 `False`。** 它只回答“这个 Task 结束了吗”，不会等待。
2. **`task.result()` 抛出 `asyncio.InvalidStateError`。** 此时还没有可读取的最终结果，它也不会自动等待结果出现。
3. **`task.exception()` 同样抛出 `asyncio.InvalidStateError`。** 尚未结束时，不能把它读成“没有异常”；工作随后仍可能成功或失败。

所以，`False` 是状态检查的结果；`InvalidStateError` 表示这次读取的时机不对。它与工作本身失败是两件事：实验捕获这次读取错误后，任务 10 仍然可以正常完成。

`generate(10, 0)` 中的 `0` 是 `sleep` 的参数，不代表调用 `create_task` 时协程已经执行完。下面的 `await task` 才让本例的调用方等到它正常结束。

<span id="task-result"></span>

## 4. 正常完成：读到返回值，异常为 None

```python
await task
print("success done", task.done())
print("success result", task.result())
print("success exception", task.exception())
```

1. `await task` 等待任务 10 正常返回；这里没有保存 `await` 取得的值，Task 仍保留自己的最终结果。
2. `task.done()` 此时返回 `True`。
3. `task.result()` 读取 `generate` 返回的 `10`。读取已有结果不会重新执行 `generate`。
4. `task.exception()` 返回 `None`，表示这个任务正常结束，没有保存失败异常。

本例先用已学的 `await` 建立“已经完成”的条件，再观察三个方法。实际拿到一个已经完成的 Task 时，可以直接调用这些读取方法。

<span id="task-exception"></span>

## 5. 失败完成：结束为 True，但没有成功结果

任务 11 传入了 `fail=True`，在 `generate` 中抛出 `ValueError`。这里沿用上一课的 `wait` 等到它结束：

```python
await asyncio.wait([failed_task], return_when=asyncio.FIRST_COMPLETED)
```

`wait` 返回完成情况，不会替我们读取任务的结果。这让实验可以接着分别观察：

1. **`failed_task.done()` 返回 `True`。** 任务已经因异常结束，所以“结束”不等于“成功”。
2. **`failed_task.exception()` 返回保存的 `ValueError` 对象。** 打印它时显示 `generation 11 failed`；这不表示方法返回了一个字符串，也不表示这一行重新抛出了 `ValueError`。
3. **`failed_task.result()` 重新抛出同一个失败异常。** 后面的 `except ValueError` 接住它，实验才可以正常结束。

本课观察的是未完成、正常完成和失败完成。取消也属于任务结束的一种情况；取消状态和相应的读取边界见[第 09 单元](../09-task-cancellation/#cancelled-task-results)，`done()` 不能单独作为成功判断。

## 6. 带走三条结论，再做自查

本课重点是知道这三个方法有什么用、什么时候用，以及遇到失败怎样处理。能在例子中选择正确的等待与读取方式即可，不需要背每一行打印输出。

1. **通常用 `await task` 等待并取得结果。** 任务失败时，异常会在等待处传播；在这里处理你预期的异常。
2. **已经确认任务结束时，可以用 `result()` 读取结果。** 例如上一课 `wait` 返回的 `done` 集合。但结束的任务仍可能失败，读取时也需要处理预期的异常。
3. **需要主动检查时，再用 `done()` 和 `exception()`。** `done()` 查看是否结束；任务已经结束后，`exception()` 可以读取失败异常，正常完成则得到 `None`。

必须记住两条边界：

1. **`done()` 为 `True` 只表示结束，不能据此判断成功。** 本课的正常完成和失败完成都得到 `True`；取消情况在第 09 单元加入。
2. **`result()`、`exception()` 不会等待。** 任务尚未完成时调用，会抛 `InvalidStateError`；要等它完成，使用 `await task`。

下面的表供回查，重点是能说明这些行为会影响哪一种处理方式：

| 本课观察的情况 | `task.done()` | `task.result()` | `task.exception()` |
| --- | --- | --- | --- |
| 尚未完成 | `False` | 抛 `InvalidStateError` | 抛 `InvalidStateError` |
| 正常返回 `10` | `True` | 得到 `10` | 得到 `None` |
| 因 `ValueError` 结束 | `True` | 重新抛出 `ValueError` | 得到该 `ValueError` 对象 |

试着回答：

1. 拿到一个尚未完成的 Task，希望等它结束后取得值，应该选哪种写法？
2. 从 `wait` 的 `done` 集合取出 Task，再调用 `result()`，还需要考虑任务失败吗？
3. 一个 Task 的 `done()` 为 `True`，可以立刻断言它成功了吗？
4. 需要主动查看任务的失败原因时，可以用哪个方法？调用前要确认什么？

<details>
<summary>查看自查解释</summary>

1. 用 `await task` 等待并取得值，在等待处处理预期的异常。直接 `result()` 不会等任务完成。
2. 需要。`done` 集合只表明任务已经结束；任务失败时，`result()` 会重新抛出失败异常。
3. 不可以。异常结束也会得到 `True`；取消的情况将在第 09 单元继续说明。
4. 可以用 `task.exception()`，先确认任务已经结束。正常完成时得到 `None`，失败时得到异常对象；未完成时调用会抛 `InvalidStateError`。

</details>

下一单元新增的问题是：已经不再需要一份工作时，怎样请求它停止，并确认清理结束？继续阅读[第 09 单元：Task.cancel](../09-task-cancellation/)。

{{< python-async-slime title="按需阅读：Slime 应用与本节源码位置" >}}

## 源码中的检查与读取怎样接起来

主例子是独立标准库实验。下面的摘录沿用教程固定的 Slime 快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f`；它与三库统计所用的新快照分开记录。

1. `generate_rollout_async` 已经用 `wait` 取得完成集合，再调用 `task.result()` 读取样本组。这里的 `task` 是任务对象，`group` 才是它返回的业务数据。
2. `AsyncRolloutWorker._loop` 先通过 `t.done()` 找到已结束的任务，再通过 `t.result()` 读取结果或观察失败；`except` 说明作者没有把 `done()` 当作“必定成功”。业务回调和重新提交规则按后续源码阅读需要展开。

{{< source-reference id="source-1" >}}

{{< source-reference id="source-2" >}}

{{< python-async-coverage lesson="07-task-results" >}}

语义核对：[Python 3.12 Task.done](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.Task.done) · [Task.result](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.Task.result) · [Task.exception](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.Task.exception)。

实现核对使用本机 Python 3.12.3 的 `asyncio`；Task 的这些读取接口来自 Future。这里讨论的是 `asyncio` 对象，线程池 Future 的阻塞式读取会在后面的线程模块单独学习。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：07 · wait：先取得任务的完成情况](../04-results/) · [下一节：09 · Task.cancel：请求取消并等待收尾](../09-task-cancellation/) · [完整学习路线](../learning-route/)
