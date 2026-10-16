---
title: "33.3 · await / Event：等待线程时，让其他协程继续"
description: "从 33.2 的线程池取样本出发，观察等待结果时另一份协程怎样继续运行。"
weight: 333
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [33.2](../33-run-in-executor/)中，`get_samples_async` 已经能把 `get_samples` 交给 reader 线程池，再用 `await future` 取得样本。这里保留这些名称和职责。
>
> **本节新增的需求：** 取样本还没完成时，另一份协程也要继续工作，例如处理消息。
>
> **本节的解决方式：** 用 `await future` 等结果，让当前协程在结果未就绪时挂起，并通过 Event 通知实验验证另一份协程能够继续运行。

<span id="executor-handoff"></span>

## 1. await / Event：把两种等待分开

上一节的取样本流程已经能正常完成。本节继续用它，只增加一份通过[第 03 课的 create_task](../03-tasks/)安排的协程，观察它能否在取样本尚未结束时运行。它由同一个 loop 调度；reader 线程池仍只负责执行同步函数 `get_samples`。

**为什么例子又加了 Event？** 生成 `[0, 1, 2]` 太快，难以稳定观察等待过程。因此借用[第 29 课的 Event](../29-thread-event/)，先不让 `get_samples` 返回，再让新增的 `allow_read` 协程发通知放行。能收到这份通知，就说明另一份协程在等待期间获得了运行机会。

**Event 是为这次观察加的实验工具；正常向线程池提交工作不要求配一个 Event。** 本节没有新增 API，只把已学过的提交、等待和协程调度接起来。代码先看两条线：`get_samples_async` 等结果，`allow_read` 发通知。

<div class="async-api-reference">

| 谁在等待 | 等什么，怎样才能继续 |
| --- | --- |
| 工作线程中的 `get_samples` | `release.wait()` 等通知标志被设置；收到通知后返回列表 |
| 主线程中的 `get_samples_async` | `await future` 等那次调用的结果；拿到列表后继续 |

</div>

`release` 是双方共用的通知对象，本例通过参数显式传递。它只用于让这次等待看得见，使用线程池并不要求先创建 Event。

## 2. create_task / await：运行同一份交接实验

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples, release):
    # 工作线程等 release 的通知；标志未设置时，阻塞的是这个工作线程。
    release.wait()
    return list(range(num_samples))


async def allow_read(release):
    print("other coroutine ran")
    # 设置 Event 的通知标志，放行工作线程；这一步不会直接写入 Future。
    release.set()


async def get_samples_async(reader, num_samples):
    release = threading.Event()  # 只创建这一个通知对象，初始标志为 False。
    loop = asyncio.get_running_loop()  # 取得正在运行 get_samples_async 的事件循环。
    # 立即提交工作；release 尚未设置，因此此时不可能取得结果。
    future = loop.run_in_executor(reader, get_samples, num_samples, release)
    # 安排另一份协程；它要等当前协程让出执行机会后才能运行。
    notifier = asyncio.create_task(allow_read(release))
    try:
        print("before await")
        samples = await future  # 结果未就绪，当前协程在这里挂起。
        print("samples", samples)
        await notifier  # 本例中它已完成，直接通过；接回这份 Task 的完成或异常。
    finally:
        release.set()  # 即使读取过程意外退出，也放行工作线程，避免池无法收尾。


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=1) as reader:
        asyncio.run(get_samples_async(reader, 3))  # 主线程运行协程，reader 的线程执行同步函数。
    print("pool closed")
```

</div>

实际输出：

```text
before await
other coroutine ran
samples [0, 1, 2]
pool closed
```

第一行由 get_samples_async 打印；第二行由 allow_read 打印；第三行由恢复执行的 get_samples_async 打印。

## 3. await：沿泳道看暂停、通知与恢复

CALLER 是 `get_samples_async`，NOTIFIER 是 `allow_read`；前两列都在主线程中，右列是同一进程里的工作线程。下面是一种允许的次序，L 对应主例子的行号。

```text
# STEP | CALLER (main)             | NOTIFIER (main)         | WORKER (reader)
# T01  | L19 Event [unset]         |                         |
# T02  | L22 submit work           |                         |
# T03  |                           |                         | L8 wait() [blocked]
# T04  | L24 create_task(...)      |                         |
# T05  | L26 print("before await") |                         |
# T06  | L27 await future [pause]  |                         |
# T07  |                           | L13 print("...ran")     |
# T08  |                           | L15 release.set()       |
# T09  |                           | allow_read ends [done]  |
# T10  |                           |                         | L8 wait() returns
# T11  |                           |                         | L9 return samples
# T12  | L27 await future [resume] |                         |
# T13  | L28 print("samples", ...) |                         |
# T14  | L29 await notifier [done] |                         |
```

T06 只挂起等待结果的 `get_samples_async`，事件循环可以运行已经安排好的通知协程。**T08 改变的是 Event 的通知标志，不是 Future 的结果。** 工作线程收到通知后继续，直到 T11 返回列表，再由事件循环把结果传给 Future，T12 才能接着往下执行。

本例只有一个 `release` 对象，等待它的是工作线程；Event 自己没有“正在等待”的执行过程。`await future` 等待的是函数的结果，不是 Event 标志。

**池里只有一个工作线程也够用：allow_read 是在主线程的事件循环中运行的协程，不占用 reader 的工作线程。**

工作线程实际开始的时刻不固定。如果 L15 先发生，工作线程后来到达 L8 时会直接通过；Event 的通知标志会保留，输出仍然相同。

### 3.1. await notifier：本例中直接通过，确认通知任务已经结束

`notifier` 是运行 `allow_read` 的 Task。`allow_read` 在 `release.set()` 后没有其他 await，会直接执行到函数末尾；因此当前协程拿到 samples 时，notifier 已经完成。

所以 T14 的 `await notifier` 不会再次发通知，也不会重新取样本；本例正常运行时删掉这一行，四行输出仍然相同。保留它是为了明确等待这份 Task 结束，并接收其可能抛出的异常；若通知协程以后增加了别的工作，这里也会等它全部结束。

## 4. await / result：为什么这次等待能让另一份协程运行？

如果改用第 31 课的 `reader.submit(...).result()` 同步等待，主线程会被阻塞；在这个实验中，负责发通知的 allow_read 就没有机会运行，双方也就无法完成交接。

本例用 await 等待未完成结果，暂停的是 get_samples_async，而不是整个事件循环。末尾的 finally 复用第 09 课的清理结构：即使读取过程意外退出，也要放行工作线程，让它能收尾。这里的 `release.set()` 仍操作同一个 Event；正常路径上标志已经为 True，再次设置不会重新运行取样本函数。

## 5. await / Event：带走两条结论

1. Event 控制工作线程什么时候继续；await Future 控制 get_samples_async 什么时候取得结果，是两处不同的等待。
2. 协程等待未完成结果时可以挂起，事件循环能推进其他就绪协程；收到结果后，从 await 后面继续。

自查：`release.set()` 发生后，get_samples_async 就立刻拿到列表了吗？

<details><summary>查看解释</summary>

还需要工作线程继续执行并返回列表，再由事件循环让等待结果的 get_samples_async 恢复。发通知、函数返回、协程恢复是不同的步骤。

</details>

---

[上一节：33.2 · run_in_executor / await](../33-run-in-executor/) · [下一节：33.4 · loop.time](../33-loop-time/) · [重点续学路线](../learning-route/#priority-reading)
