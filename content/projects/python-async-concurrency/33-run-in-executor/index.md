---
title: "33.1 · get_running_loop / run_in_executor：从协程使用指定线程池"
description: "已经会提交线程池工作，怎样用 await 等待结果，并让其他协程继续运行？"
weight: 331
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 26 课](../26-to-thread/)用 `to_thread()` 把同步函数交给线程；[31.1](../31-threadpool-submit/)用自己创建的线程池提交工作，再用 `result()` 等结果。
>
> **本课新增的问题：** 已经选定线程池，在协程里怎样提交工作，用 `await` 等结果，同时让事件循环还能处理其他协程？补充实验会复用[第 29 课的 Event](../29-thread-event/)。

<span id="executor-await"></span>

## 1. get_running_loop / run_in_executor：把指定线程池接到协程等待

第 31 课的 `future.result()` 能取结果，但如果还没完成，会阻塞调用它的线程。现在调用方变成协程：希望等待期间，主线程上的事件循环还能安排其他协程。

本课仍然让 `get_samples(3)` 生成 `[0, 1, 2]`，只改变提交和等待的入口。先分清对象：

<div class="async-api-reference">

| 名字 | 负责什么 |
| --- | --- |
| `reader` | 自己创建的线程池，工作线程在这里执行同步函数 |
| `loop` | 当前正在运行的事件循环，调度主线程中的协程 |
| `future` | 这次提交返回的 **asyncio Future**，可以用 `await` 等它 |
| `samples` | 等到结果后拿到的样本列表 |

</div>

`loop` 不是新线程，也不是线程池。`asyncio.run()` 已经在主线程建立并运行了事件循环，`get_running_loop()` 只是取得它。

`run_in_executor(reader, get_samples, 3)` 的意思是：**请当前事件循环把 `get_samples(3)` 交给 reader，并给我一个可以异步等待的结果对象。**

## 2. run_in_executor + await：提交一次，再等这一次的结果

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples):
    # 线程池中的工作线程执行这个同步函数，返回样本列表。
    return list(range(num_samples))


async def get_samples_async(reader, num_samples):
    # 取得当前协程正在使用的事件循环；不创建新的循环。
    loop = asyncio.get_running_loop()
    # 现在就提交 get_samples(num_samples)，返回可 await 的 asyncio Future。
    future = loop.run_in_executor(reader, get_samples, num_samples)
    print("work submitted")
    # 结果未就绪时挂起当前协程；工作线程返回后，取得同一次调用的结果。
    return await future


async def exercise(reader):
    print("before submit")
    # 沿当前协程的调用链等待，不会额外创建一个 Task。
    samples = await get_samples_async(reader, 3)
    print("samples", samples)


if __name__ == "__main__":
    # 在事件循环外管理自选线程池；离开 with 时等待并关闭池。
    with ThreadPoolExecutor(max_workers=1) as reader:
        # 在主线程运行事件循环，把同一个 reader 交给协程使用。
        asyncio.run(exercise(reader))
    print("pool closed")
```

</div>

实际输出：

```text
before submit
work submitted
samples [0, 1, 2]
pool closed
```

这份教学裁剪保留 Slime 的 `get_samples`、`get_samples_async` 名称与样本返回关系；将类中的 `self._reader` 改为显式传入的 `reader`，将真实队列/文件读取缩成生成列表，并拆开原来的一行表达式，便于观察提交与等待。末尾保留原始源码。

## 3. get_running_loop、提交、await：分别在哪一步发生？

下面沿主线程的调用顺序看。工作线程从提交后就可能开始，不必等主线程执行到 await。

1. 主线程创建线程池，`asyncio.run(exercise(reader))` 开始运行协程。
2. `exercise` 直接 await `get_samples_async`，沿当前 Task 的调用链进入函数，不会自动新增一份 Task。
3. `get_running_loop()` 返回当前循环；`run_in_executor(...)` **调用时就提交工作**，随后打印 `work submitted`。
4. 工作线程执行 `get_samples(3)`；`await future` 取得同一次调用的结果，不会再提交一次。
5. 结果尚未就绪时，当前协程挂起，事件循环可以处理其他工作。结果已经就绪时，这次 await 不一定挂起。
6. 协程取得列表并打印结果；`asyncio.run()` 返回后，外层 `with` 等待并关闭自选线程池，再打印 `pool closed`。

主例子的函数非常短，也没有安排其他协程；仅凭这四行输出不能证明发生过任务切换。下面再单独观察等待期间的行为。

`to_thread(get_samples, 3)` 使用默认线程池；这里显式指定 `reader`。如果传入 `None`，`run_in_executor(None, ...)` 也会使用循环的默认执行器。本课先使用自己选定的线程池，不展开其他差异。

## 4. await：自己在等，为什么其他协程还能运行？

这是一个独立实验：[下载 responsive.py](responsive.py)。只为观察等待，让工作线程先等一个 Event；另一份协程负责发通知。

**release 是一个通知对象，显式传给双方共用。** 工作线程调用 `wait()`；通知协程调用 `set()`。Event 只用于控制本次实验，不是调用 `run_in_executor` 必须准备的对象。

<div class="async-coordination-code">

```python
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples, release):
    # 只有工作线程等通知；收到通知后才生成并返回列表。
    release.wait()
    return list(range(num_samples))


async def allow_read(release):
    print("other coroutine ran")
    # 另一份协程发出通知，让工作线程可以继续。
    release.set()


async def exercise(reader):
    release = threading.Event()  # 创建一次通知，显式传给双方共用。
    loop = asyncio.get_running_loop()  # 取得正在运行 exercise 的事件循环。
    # 立即提交工作；release 尚未设置，因此此时不可能取得结果。
    future = loop.run_in_executor(reader, get_samples, 3, release)
    # 安排另一份协程；它要等当前协程让出执行机会后才能运行。
    notifier = asyncio.create_task(allow_read(release))
    try:
        print("before await")
        samples = await future  # 结果未就绪，当前协程在这里挂起。
        print("samples", samples)
        await notifier  # 确认通知协程结束；本例中它已经完成。
    finally:
        release.set()  # 即使读取过程意外退出，也放行工作线程，避免池无法收尾。


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=1) as reader:
        asyncio.run(exercise(reader))  # 主线程运行协程，reader 的线程执行同步函数。
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

下面是一种允许的执行次序，L 对应上面代码的行号；工作线程实际开始的时刻不固定。左列是主线程中的协程，右列是 reader 的工作线程，每行只画一侧的动作：

```text
# STEP | MAIN (event loop)                      | WORKER (reader)
# T01  | L22 run_in_executor(...)               |
# T02  |                                        | L8 release.wait()
# T03  | L24 create_task(allow_read(...))       |
# T04  | L26 print("before await")              |
# T05  | L27 await future [pause]               |
# T06  | L13 print("other coroutine ran")       |
# T07  | L15 release.set(); allow_read returns  |
# T08  |                                        | L8 wait() returns
# T09  |                                        | L9 return samples
# T10  | L27 await future [resume]              |
# T11  | L28 print("samples", samples)          |
```

关键在 T05–T07：**exercise 等结果时，allow_read 仍能在同一个事件循环中执行。** `allow_read` 发出通知后，工作线程才能返回，随后 exercise 才拿到结果。

如果工作线程直到通知发出后才开始，它的 `wait()` 会直接通过；输出仍然相同。这是 Event 保留通知状态的作用。

如果改成第 31 课的 `reader.submit(...).result()` 来同步等待，事件循环线程会被占住，负责发通知的协程就没有机会运行。这里通过 `await` 等待的是 `run_in_executor` 返回的 asyncio Future。

## 5. run_in_executor：带走三条结论

1. `get_running_loop()` 取得当前循环；没有正在运行的循环时会报 `RuntimeError`。本课把它放在协程里调用。
2. `run_in_executor` 调用时提交同步函数，返回可 await 的 asyncio Future；`await` 负责等结果。
3. 等未完成结果时挂起的是当前协程。工作线程继续工作，事件循环也可以运行其他协程。

如果同步函数抛出异常，异常会在等待结果的 `await` 处传回，可以用已经学过的 `try/except` 处理。取消等待者也不等于强行停止已经运行的同步函数，延续第 26 课的边界。

自查：`future` 和 `samples` 分别是什么？补充实验只有一个工作线程，为什么 `allow_read` 仍能运行？

<details><summary>查看解释</summary>

`future` 是等待这次调用的 asyncio Future；`samples` 才是返回的列表。`allow_read` 在主线程的事件循环中运行，不需要占用 reader 的工作线程。

</details>

## 6. get_running_loop / run_in_executor：本课接口速查

<div class="async-api-reference">

| 调用或动作 | 用途与结果 |
| --- | --- |
| `asyncio.get_running_loop()` | 取得当前线程正在运行的事件循环；本课在协程内调用 |
| `loop.run_in_executor(reader, func, *args)` | 立即向指定执行器提交同步函数调用，返回 asyncio Future |
| `await future` | 返回函数结果或传回异常；结果未就绪时允许当前协程挂起 |

</div>

本课的 Future 可以 await；31.1 中 `executor.submit()` 返回的是 `concurrent.futures.Future`，不能直接套用这种等待写法。[第 34 课](../learning-route/#curriculum-stage-bridges)再讲已经拿到后一种 Future 时怎样接入协程。

{{< python-async-slime title="按需阅读：原始源码与标准库依据" >}}

Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 中，`QueueReader.get_samples_async` 使用已有的 `_reader`，把同步读取交给线程池。下面是原始方法；正文的最小实验没有真实队列和文件读写。

{{< source-reference id="source-1" >}}

API 语义核对：[Python 3.12：取得当前循环](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.get_running_loop)、[使用执行器](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.run_in_executor)。例子已在 Python 3.12.3 运行，使用 Python 3.11 及以上版本。

{{< python-async-coverage lesson="33-run-in-executor" >}}

{{< /python-async-slime >}}

---

[上一节：31.2 · ThreadPoolExecutor.map](../31-threadpool-map/) · [下一节：33.2 · loop.time](../33-loop-time/) · [重点续学路线](../learning-route/#priority-reading)
