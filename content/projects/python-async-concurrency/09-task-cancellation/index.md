---
title: "09 · Task.cancel：请求取消并等待收尾"
description: "沿用已创建的 Task，区分取消请求、协程处理取消、finally 清理和 await 确认结束。"
weight: 90
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 不再需要任务结果时，怎样让它结束？

1. **上一课已经会了：** 读取 Task 的完成状态、结果和异常。但知道任务还没完成，不等于已经让它停止。
2. **现在多了一个要求：** 调用方已经不需要其中一份工作，希望它停止继续等待，执行必要的清理，然后确认它已经结束。
3. **先看原来的办法：** `await task` 可以等它结束，但单独等待不会主动发出停止请求。直接不再等待，也不代表任务已停止或清理已完成。

这次增加 **`task.cancel()`**，并把它与已经学过的 `await task` 接起来：**先请求取消，再等待取消得到处理。**

同时解释两项配套内容：任务通过 `asyncio.CancelledError` 观察取消；工作函数用 `try/finally` 放置退出前的清理。超时会在第 13 单元加入，本课只主动取消一个已创建的 Task。

## 2. 一份最小实验：先请求取消，再确认清理完成

仍然使用 `generate(rollout_id, seconds)`。这次只保留任务 10，让它进入较长的等待；增加 `finally`，用打印 `cleanup` 表示执行了一次清理动作。

先预测：`cancel()` 返回后，`task.done()` 会立即变成 `True` 吗？`cleanup` 和调用方的 `cancelled`，谁先打印？

```python
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
```

[下载 example.py](example.py) · 运行：`python3 -W error example.py`。本例使用 Python 3.12 的默认任务调度。

本机 Python 3.12.3 的运行输出为：

```text
generate 10 started
cancel requested True
done immediately False
cleanup 10
cancelled
done after await True
```

`60` 用来表示一份尚未结束的等待；这次取消会打断它，不需要等满 60 秒。实验看的是请求、清理和确认结束的先后关系，不用精确耗时证明调度。

<span id="task-cancellation"></span>

## 3. 沿执行过程分清三个位置

### 3.1 工作函数：先进入 try，暂停在 await

`create_task` 先安排任务。随后 `exercise` 执行 `await asyncio.sleep(0)`，主动让出执行机会；在本例中，任务 10 得以开始执行，打印 `started`，再暂停在 `await asyncio.sleep(60)`。

这里的 `sleep(0)` 没有等完任务 10，只是让本例的任务先进入等待。它也不是复杂任务中“所有初始化都已完成”的通用确认方式。

所以，执行到本例的 `task.cancel()` 时，`generate` 已经开始，并暂停在自己的 `await asyncio.sleep(60)`。但不能推广成“写过一个 `await`，就一定进入了 `generate`”：有的等待对象已经完成，`await` 未必让出执行机会；后面的 `await task` 也可能只是在观察一个开始前就被取消的任务。本例先打印 `started`，再打印 `cancel requested`，才是进入顺序的直接证据。

这一步有实际作用：**先进入了 `try`，后面离开这段代码时才会执行它对应的 `finally`。** 如果任务刚创建、函数体还没开始就被取消，不能指望这个尚未进入的 `finally` 已经承担了清理责任。

### 3.2 调用方：cancel 发出请求，不等待清理

```python
requested = task.cancel()
print("cancel requested", requested)
print("done immediately", task.done())
```

1. `task.cancel()` 的接收者是任务 10。它请求该 Task 取消，不是取消当前正在执行的 `exercise`。
2. 方法立即返回一个布尔值。本例得到 `True`，表示接受了这次请求；**它不证明任务已经退出，也不保证工作函数一定会让取消传播到底。** 对已经结束的 Task 调用会返回 `False`。
3. 这几行之间没有新的等待。在本例中，任务 10 还没获得执行机会处理取消，因此 `done immediately` 仍然是 `False`。

取消通过协程后续执行时收到的 `asyncio.CancelledError` 表现出来。本例的工作函数暂停在 `sleep` 的等待处，因此它会从这里收到取消异常，离开正常执行路径；后面的 `return rollout_id` 不会执行。

### 3.3 再 await：任务先清理，等待者再观察取消

```python
try:
    await task
except asyncio.CancelledError:
    print("cancelled")
```

1. `exercise` 开始等待任务 10 结束；此时事件循环可以让任务 10 继续执行并处理取消。
2. 任务 10 因取消离开已经进入的 `try`，先执行 `finally`，打印 `cleanup 10`。
3. 工作函数没有吞掉取消异常，`CancelledError` 继续向外传播，Task 以取消状态结束。
4. 等待者的 `await task` 因而抛出 `CancelledError`，被本例的 `except` 接住，才打印 `cancelled`。后面的 `task.done()` 此时为 `True`。

这里的再次 `await` **不会重启 `generate`**。它等待的是同一个 Task 对取消请求的处理及退出结果。

任务获得执行机会后就可以处理取消，并非必须先有人 `await` 它。这里写 `await`，是让调用方等到处理完成并观察结果；不是把它当作取消开始生效的开关。

<span id="cancel-cleanup-responsibility"></span>

## 4. try/finally 管清理，try/except 管异常处理

### 4.1 没有 try/finally，协程也可以被取消

**`cancel()` 生效不要求被取消的协程必须写 `try/finally`。** 回看第 12 节原来的工作函数：

```python
async def generate(rollout_id, seconds):
    await asyncio.sleep(seconds)
    return rollout_id
```

它在等待时收到 `CancelledError`，如果没有捕获这个异常，异常就会向外传播，协程随之退出。本课增加 `finally`，是为了展示退出前的清理责任，不是为了让取消具备作用。

### 4.2 长耗时请求更需要检查谁负责清理

耗时较长的请求或生成任务，可能还没完成，调用方就已经不需要结果了。这时要同时回答两个问题：**怎样请求任务停止，以及退出前还有什么需要归还或恢复？**

是否需要 `finally`，主要看清理责任，而不是只看等待时间有多长：

| 这份工作持有什么 | 需要考虑的处理 |
| --- | --- |
| 只是等待结果，没有由本层负责释放的资源或恢复的状态 | 不必为了能够取消而专门添加 `finally`；让取消异常继续传播即可 |
| 已经取得连接、并发许可或临时资源 | 退出时要归还或释放，包括正常完成、失败和取消 |
| 已经把某份工作登记为“进行中” | 提前退出时也要按实际结束情况更新或恢复状态，不能只在成功返回后更新 |

因此，长请求里经常看到 `try/finally`，是因为它们往往同时承担资源和状态的管理责任。若清理已由上下文管理器负责，则沿用那套管理方式；关键是确认清理由谁负责，并把实际等待放在相应的保护范围内。

也不要只把清理写在 `await` 后面的正常路径上：一旦等待处抛出取消异常，后面的普通语句可能不会执行。本例用 `finally`，就是为了让已经进入的工作区域在退出时仍经过清理。

### 4.3 本例的两处 try 各自负责什么

主例子中有两处 `try`，它们承担不同责任：

| 所在位置 | 写法 | 本例中的责任 |
| --- | --- | --- |
| 工作函数 `generate` | `try/finally` | 离开已经进入的工作区域时执行清理 |
| 调用方 `exercise` | `try/except asyncio.CancelledError` | 等待自己取消的任务，处理预期的取消结果 |

`finally` 不只在取消时运行：正常返回、普通异常退出时也会经过它。因此真正的资源清理应放在这里；本例的 `print` 只是让清理时机可见，并没有关闭任何实际资源。

**执行 `finally` 不等于捕获并消除异常。** 主例子的 `generate` 没有写 `except CancelledError`，所以清理之后，原来的取消异常会继续传播，不需要额外再写一次 `raise`。

如果工作函数确实需要捕获取消，例如先记录一条信息，通常应在处理后用单独的 `raise` 继续抛出：

```python
except asyncio.CancelledError:
    print("正在处理取消")
    raise
```

这是需要时放进工作函数的异常分支，不必添加到主例子里。若捕获后直接正常返回，任务可能表现为正常完成，调用方就无法按原来的取消结果处理它。

本例调用方主动取消自己创建的任务，随后在等待它的边界捕获预期取消。若当前协程本身收到上层的取消请求，也应在必要清理后继续传播，不能把两种处理责任混在一起。

<span id="cancelled-task-results"></span>

## 5. 补上第 08 节的取消状态，再记住处理边界

第 08 节已经知道 `done()` 为 `True` 不等于成功。本例又增加一种已经结束的情况：工作函数让 `CancelledError` 传播出去，Task 以取消状态结束。

| 对这个已取消的 Task 进行操作 | 行为 |
| --- | --- |
| `task.done()` | 返回 `True` |
| `await task` | 抛出 `asyncio.CancelledError` |
| `task.result()` | 抛出 `asyncio.CancelledError` |
| `task.exception()` | 也抛出 `asyncio.CancelledError`，不是返回异常对象 |

最后一行与普通失败不同：普通失败时，`exception()` 返回保存的异常对象；Task 以取消状态结束时，这个方法本身会抛取消异常。

日常处理可以先记住这几个边界：

1. **不再需要一份工作时，保留 Task 引用，请求取消后继续等待收尾。** 本课的基本写法就是 `task.cancel()`，随后 `await task`，处理预期的取消结果。
2. **`CancelledError` 要显式识别。** 在本课的 Python 3.12 中，它继承自 `BaseException`，一般的 `except Exception` 接不住它。清理通常放在 `finally`，不要为了捕获取消就笼统吞掉所有异常。
3. **取消需要协程获得执行机会。** 它不是强制中断正在执行的任意 Python 语句；如果一段同步代码长时间占用事件循环，取消处理也会被推迟。

本例只有一次取消，且清理动作本身正常完成。不要把它扩展理解成“发出取消后，任何清理一定能完成”；如果清理自身抛出其他异常，等待者也需要按实际异常处理。

## 6. 带走三条结论，再做自查

本课重点是会把请求、清理和确认结束接起来，不需要背每一行打印输出。

1. **`cancel()` 发出请求；返回 `True` 不代表任务已经退出。** 本例请求后立即读取的 `done()` 仍为 `False`。
2. **有清理责任时，用 `finally` 等资源管理方式处理退出，并让取消继续传播。** 没有 `finally` 的协程同样可以被取消；本例先打印 `cleanup`，不会正常返回编号 10。
3. **调用方继续 `await task`，等待并观察结束结果。** 本例在等待处收到取消异常，随后检查 `done()` 为 `True`。

试着回答：

1. `cancel()` 返回 `True` 后，能否立刻断言任务已经清理完毕？
2. 为什么本例要先 `await asyncio.sleep(0)`，而不是刚创建任务就立刻取消？
3. 没有 `try/finally` 的协程就不能被取消吗？添加 `finally` 会消除取消异常吗？
4. Task 已经以取消状态结束，`done()` 为 `True`，能否把 `exception()` 当作不会抛异常的读取？
5. 一次请求耗时很长，判断需不需要清理保护时，应先找什么？

<details>
<summary>查看自查解释</summary>

1. 不能。它是取消请求被接受的结果；还要让任务处理请求，并继续等待退出结果。
2. 让本例任务先进入 `try` 中的等待，以便观察它离开时执行 `finally`。尚未开始的函数体不能保证执行其中的清理。
3. 仍然可以被取消。`finally` 用来执行清理；它正常执行完以后，原来的异常继续向外传播，捕获和消除异常是另一回事。
4. 不能。Task 以取消状态结束时，`result()` 和 `exception()` 都会抛出 `CancelledError`。
5. 先找本层持有的资源、需要恢复的状态，以及谁负责清理。耗时长会增加中途不再需要结果的机会，但仅凭“耗时长”不能判断必须手写 `finally`。

</details>

下一节把问题扩展到一组任务：**某一份失败，gather 报错，其他任务是否会自动停止？** 继续阅读[10.1 · gather 的失败处理](../15-gather-failures/)。

{{< python-async-slime title="按需阅读：Slime 应用与本节源码位置" >}}

## 从一次取数回到清理责任

主例子是独立标准库实验。下面继续使用教程已核对的 Slime 快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，与三库 API 统计采用的新快照分开记录。

这里进入 `_GenerationActor._next()`，跟随**一次取数请求**：它先创建 `take`，等待队列取数与生产者的完成情况，再决定向调用方返回什么。读本段是为了看清一个交接：离开这次请求前，谁负责处理仍可能挂起的取数任务？

1. 输入是这次创建的 `take` 和已有的 `self.producer`；任务结果读取沿用第 06、07 单元。
2. 离开 `try` 时进入 `finally`，先调用 `take.cancel()`，再等待它收尾。若 `take` 已经结束，取消请求不会重新启动或再次执行它。
3. 这样处理以后，这次请求不会留下一个无人负责、以后可能取走数据的挂起取数任务。读完返回 `_next()` 的返回路径；队列机制在后续协调模块展开。

{{< source-reference id="source-1" >}}

源码使用 `gather(..., return_exceptions=True)` 等待清理。这是批量收尾中的一种结果处理方式，参数细节在第 10 单元回访 `gather` 时展开；本课先用单个 `await task` 与显式 `except CancelledError` 建立同一条“取消后还要等待”的关系。

{{< python-async-coverage lesson="09-task-cancellation" >}}

## 版本与语义核对

取消请求与清理行为按 [Python 3.12 Task.cancel](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.Task.cancel)、[任务取消](https://docs.python.org/3.12/library/asyncio-task.html#task-cancellation)及本机 Python 3.12.3 `asyncio.tasks` 实现核对。取消后的读取规则见 [Task.result](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.Task.result)和 [Task.exception](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.Task.exception)；异常继承关系见 [CancelledError](https://docs.python.org/3.12/library/asyncio-exceptions.html#asyncio.CancelledError)。

《Fluent Python, 2nd Edition》19.4.3 也讨论了取消怎样进入协程：英文短语“raises a `CancelledError` exception”（本地 `en/ch19.md` 第 335 行），中文为“抛出 `CancelledError` 异常”（`zh/ch19.md` 第 323 行）；对齐节锚点是 `spinner-with-coroutines`。本书基于 Python 3.10；本课按 Python 3.12 区分发出请求与随后处理请求，不能把这段描述理解为调用 `cancel()` 时清理已经完成。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：08 · done、result、exception：读取 Task 的状态与结果](../07-task-results/) · [下一节：10.1 · asyncio.gather：收集报错，任务仍可继续](../15-gather-failures/) · [完整学习路线](../learning-route/)
