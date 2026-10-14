---
title: "13 · asyncio.wait_for：限制一次等待的时长"
description: "承接主动取消，为一次等待增加时限，分清任务内部的取消、调用方的超时和清理完成的顺序。"
weight: 130
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 已经会取消，怎样限制这次最多等待多久？

1. **前面已经会了：** 第 09 单元用 `task.cancel()` 请求取消，再 `await task` 等待清理；上一单元学会按完成顺序等待结果。
2. **现在多了一个要求：** 希望任务正常返回，但不愿一直等；如果这次等待超过指定时长，就请求取消，并向调用方报告超时。
3. **先看原来的办法：** 单独 `await task` 没有时限。沿用取消方法也可以自己组织计时与收尾，但这次希望让一个接口统一负责这段过程。

本课新增 **`asyncio.wait_for`**：为一次等待设置时限。同时学习内置异常 **`TimeoutError`** 的捕获和构造，用它向调用方报告超时。

## 2. 沿用 generate，只改变等待方式

仍然让任务 10 等待 60 秒，并保留第 09 课的 `finally`。为集中观察超时，这里省略取消实验中的开始与状态打印；调用方这次不主动写 `cancel()`，改为用 `wait_for` 设置 1 秒的等待时限。

先预测：调用方会收到 `CancelledError` 还是 `TimeoutError`？是先打印 `cleanup`，还是先打印 `timeout`？

```python
import asyncio


async def generate(rollout_id, seconds):
    try:
        await asyncio.sleep(seconds)
        return rollout_id
    finally:
        print("cleanup", rollout_id)


async def exercise():
    task = asyncio.create_task(generate(10, 60))

    try:
        result = await asyncio.wait_for(task, timeout=1)
        print("result", result)
    except TimeoutError:
        print("timeout")


if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载 example.py](example.py) · 运行：`python3 -W error example.py`。本课使用 Python 3.12。

本机 Python 3.12.3 的运行输出为：

```text
cleanup 10
timeout
```

这次任务没有正常返回编号 10，所以不会执行 `print("result", result)`。`finally` 中的清理先执行，调用方随后观察到超时。

<span id="wait-for"></span>

## 3. wait_for 等什么，返回什么？

### 3.1 参数和返回值

```python
result = await asyncio.wait_for(task, timeout=1)
```

| 部分 | 本例中的含义 |
| --- | --- |
| `task` | 已经创建的 Task，保存任务 10 的执行与结果 |
| `timeout=1` | 这次等待使用的时限，单位为秒 |
| `await asyncio.wait_for(...)` | 驱动这次带时限的等待；正常完成时取得原任务的返回值 |
| `result` | 任务正常返回的值，不是新的 Task，也不是完成集合 |

`wait_for` 接受可等待对象；本课显式传入 Task，保持任务身份清楚。`timeout` 可以是整数或小数，`None` 表示不设置超时。

时限从这次 `wait_for` 开始执行时计算，不是从 `create_task` 那一行追溯计算。若任务在调用之前已经运行了一段时间，这次设置的仍是当前等待的时限，也不会重启原任务。

如果把主例子的 `generate(10, 60)` 改成 `generate(10, 0)`，任务就会正常完成，输出变为：

```text
cleanup 10
result 10
```

正常返回同样会经过 `finally`；`wait_for` 此时返回 `10`，不会凭空制造超时异常。

### 3.2 超时时，沿着任务和调用方各看一遍

1. **开始等待。** `exercise` 等待已创建的任务 10，任务进入自己的 `sleep`。
2. **达到等待时限。** 任务尚未完成，`wait_for` 请求取消这份任务。
3. **任务处理取消。** `generate` 在等待处收到 `CancelledError`，离开 `try`，先执行 `finally`，打印 `cleanup 10`。
4. **调用方向外报告超时。** 本例的任务正常传播取消异常；`wait_for` 等待它结束后，在调用方表现为 `TimeoutError`，被 `except TimeoutError` 接住。

这里要认清两个位置：**工作函数处理的是取消，调用方这次处理的是等待超时。** `wait_for` 把第 09 课的取消与收尾过程接到了等待时限之后，不需要在超时处理分支里再重复取消这份任务。

这条路径沿用第 09 课的前提：工作函数不吞掉取消异常。若工作函数把取消吞掉并正常返回，`wait_for` 也可能返回那个值；取消仍然需要任务配合。

<span id="timeout-cleanup"></span>

## 4. timeout 是等待时限，不是清理结束的硬截止

主例子的清理只有一次打印，很快就结束。如果清理本身还需要等待，会怎样？

只把 `finally` 改成下面这样，并将实验的等待时限改为 `0.1` 秒：

```python
finally:
    print("cleanup start", rollout_id)
    await asyncio.sleep(0.2)
    print("cleanup finished", rollout_id)
```

[下载完整 slow_cleanup.py](slow_cleanup.py)。运行输出为：

```text
cleanup start 10
cleanup finished 10
timeout
```

1. 等待时限到达以后，开始取消和清理。
2. `finally` 中还有一次异步等待，`wait_for` 继续等待这段清理。
3. 任务结束后，调用方才收到本例的超时异常。因此 `cleanup finished` 仍在 `timeout` 之前。

**实际调用耗时可能超过 `timeout`。** 时限触发取消请求，不会强行跳过任务的清理；事件循环若被同步代码占用，超时处理本身也可能延后。这里用输出顺序验证收尾关系，经过时间怎样度量留到第 14 单元。

本例只有一次取消，且清理没有失败。如果清理自身抛出其他异常，该异常可能传播到等待者，不能认为所有退出路径都会变成 `TimeoutError`。

<span id="timeout-error"></span>

## 5. TimeoutError：加上能看懂的失败说明

主例子只打印 `timeout`，已经能处理这次超时。若当前函数还需要把失败交给上层判断，可以构造一个带业务说明的异常，再抛出去：

```python
try:
    return await asyncio.wait_for(task, timeout=0.1)
except TimeoutError as error:
    raise TimeoutError("任务 10 未在等待时限内完成") from error
```

1. `except TimeoutError as error` 接住等待处观察到的超时异常。
2. `TimeoutError("任务 10 未在等待时限内完成")` 创建一个新的异常对象，保存这段说明；这是内置的 `TimeoutError`，不需要从 `asyncio` 导入。
3. `raise` 把它交给调用方；`from error` 保留原异常作为原因，便于回查。这些操作补充失败信息，不会重新运行任务或再次开始计时。

[下载完整 timeout_message.py](timeout_message.py)。脚本入口接住带说明的异常并打印，输出为：

```text
cleanup 10
timeout: 任务 10 未在等待时限内完成
```

这与只在当前函数里 `print` 一句提示不同：`raise` 让上层仍然能够按失败处理。是否就地处理或继续抛出，取决于当前函数承担的职责，不要求每处都重新包装一次。

如果工作函数自己也可能抛出 `TimeoutError`，同一个 `except` 也能接住它，需结合调用边界解释来源。本例的 `generate` 不主动抛这种异常，所以可以清楚观察 `wait_for` 的超时路径。

## 6. 带走三条结论，再做自查

1. **`wait_for` 为一次等待增加时限。** 正常完成时，得到原任务的返回值；本课先显式创建 Task，再把它传进去。
2. **超时路径包含取消和收尾。** 在任务正常响应取消的前提下，任务内部收到 `CancelledError`，调用方等待结束后收到 `TimeoutError`。
3. **时限到达不等于清理立即结束。** 实际耗时可能超过 `timeout`；报告失败时，可以用 `TimeoutError("说明")` 加上业务信息，而不是把超时当成成功结果。

试着回答：

1. 把任务改成及时返回 `10`，`await wait_for(...)` 得到的是 Task 还是整数？
2. 时限到达后，任务正在 `finally` 中清理，调用方能否认为一切已经结束？
3. 在本课的超时路径中，`generate` 内部和调用方分别面对什么异常？
4. 如果只打印超时提示然后正常返回，和 `raise TimeoutError("说明")` 交给上层，有什么不同？

<details>
<summary>查看自查解释</summary>

1. 得到整数 `10`，也就是原任务的返回值。`wait_for` 不会把正常结果换成 Task 对象。
2. 不能。仍需等待任务处理取消和清理；`timeout` 不是整个收尾过程的硬截止。
3. 工作函数从等待处收到 `CancelledError`；本例正常传播取消后，调用方从 `wait_for` 收到 `TimeoutError`。
4. 打印只是输出信息，正常返回仍表现为返回值；抛出异常则让上层明确观察并处理失败。

</details>

下一单元再解决：**怎样度量经过时间和剩余预算，避免把时间戳误当成调度顺序？** 继续阅读[14 · time.monotonic / time.perf_counter：计量经过时间与预算](../11-time-budget/)。

{{< python-async-slime title="按需阅读：Slime 应用与本节源码位置" >}}

## 从服务器控制请求看两处用法

主例子和两个补充实验均为独立标准库实验。源码继续使用已核对的 Slime 快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，与三库统计的新快照分开记录。

这里跟随 `abort_server_until_idle` 的一次服务器状态检查，进入 `_get_server_load`：输入是服务地址 `url` 和单次请求时限 `request_timeout`；它等待 HTTP 取数，正常完成时向调用方返回负载信息。阅读重点是等待外层的时限，不展开 HTTP 客户端实现。

{{< source-reference id="source-1" >}}

源码把可等待的 HTTP 操作直接传给 `wait_for`；主例子先显式创建 Task，是为了继续沿用前课的任务身份与取消关系。HTTP 函数自己的 `timeout` 参数属于客户端接口，需要另查该客户端的语义，不能仅因数值相同就当成同一个接口。

回到调用方 `abort_server_until_idle`，当整体预算耗尽时，它构造并抛出带服务地址及最近状态的 `TimeoutError`。这段代码展示的是给异常添加说明，并不是 `wait_for` 内部抛错的源码。

{{< source-reference id="source-2" >}}

其中的循环、时钟与剩余预算先作为阅读背景；本课只看 `raise TimeoutError(...)` 的输入和失败输出，计时机制在下一单元展开。

{{< python-async-coverage lesson="10-wait-for" >}}

## 版本与语义核对

接口行为按 [Python 3.12 asyncio.wait_for](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.wait_for)、[内置 TimeoutError](https://docs.python.org/3.12/library/exceptions.html#TimeoutError)与本机 Python 3.12.3 的 `asyncio.tasks.wait_for` 实现核对。Python 3.11 起，此接口使用内置 `TimeoutError`。

本地《Fluent Python, 2nd Edition》英文全文中未检索到 `wait_for` 或 `asyncio.wait_for` 的对应讨论；本课不借用书中其他等待接口推断它的超时行为，以上述版本的文档、实现和运行实验为依据。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：12 · asyncio.as_completed：按完成顺序取结果](../08-as-completed/) · [下一节：14 · time.monotonic / time.perf_counter：计量经过时间与预算](../11-time-budget/) · [完整学习路线](../learning-route/)
