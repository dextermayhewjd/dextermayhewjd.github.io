---
title: "09 · Queue：把生产速度和消费速度接起来"
description: "用有界队列理解等待、背压与结束信号。"
weight: 90
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="async-queue"></span>

## 限制执行中工作，还不够

如果生产者不断生成结果，消费者暂时不读取，结果放在哪里？有界队列把“已经生产、尚未消费”的数量也限制住。

```python
import asyncio

async def _produce(outputs):
    for value in (10, 11):
        await outputs.put(value)
    await outputs.put(None)

async def _next(outputs):
    values = []
    while True:
        value = await outputs.get()
        if value is None:
            return values
        values.append(value)

async def exercise():
    outputs = asyncio.Queue(maxsize=1)
    _, values = await asyncio.gather(_produce(outputs), _next(outputs))
    print("received", values)

if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
received [10, 11]
```

这里 `None` 是实验约定的结束信号，不是 Queue 的内置协议。队列满时 `await put()` 等待；队列空时 `await get()` 等待。生产和消费因此通过同一条队列配合。

<span id="thread-queue"></span>

## 与 threading 队列区分

`asyncio.Queue` 为同一事件循环中的任务设计，不保证 OS 线程之间的安全访问。跨线程数据交接常用标准库 `queue.Queue`；它的阻塞等待也需要考虑运行位置。

如果使用 `queue.join()`，消费者必须为取出的工作调用相应的 `task_done()`；本实验使用结束信号和 `gather` 等待退出，未采用 join 协议。

| 同步队列的写法 | 本次调用的行为 |
| --- | --- |
| `put(value)` | 入队；有界队列满时会阻塞调用线程 |
| `get()` | 取走一项；空队列时会阻塞调用线程 |
| `get_nowait()` | 立刻尝试取走；没有数据时抛 `queue.Empty` |
| `qsize()` / `empty()` | 查看这一刻的状态；其他线程下一刻可能改变队列 |

不能先看 `empty()`，就保证随后 `get()` 一定不阻塞。要表达“没有就算了”，应直接尝试 `get_nowait()` 并处理 `queue.Empty`。`qsize()` 适合观察积压，不是预留结果的操作。


对于本节的异步队列，`empty()` 同样只是状态观察；需要等待下一份结果时用 `await get()`。同步 Queue、异步 Queue、进程 Queue 的等待位置不同，进程版本在第 20 节继续讲。

语义核对：[同步 queue.Queue](https://docs.python.org/3.12/library/queue.html#queue.Queue)。

<details><summary>复述检查</summary>

Semaphore 限制的是进入某段工作的许可，Queue 的 maxsize 限制的是已排队元素。二者可以同时存在，分别约束不同阶段。

</details>

语义核对：[asyncio Queue](https://docs.python.org/3.12/library/asyncio-queue.html)。

{{< python-async-slime >}}

## Slime 的结果队列

`_GenerationActor._start()` 建立 `Queue(maxsize=1)`，生产者在 `_produce()` 中把结果放进去，消费者通过 `_next()` 取走。跟踪 `self.outputs`，就能把这三个方法连起来。

<details>
<summary>展开 Slime 源码：_GenerationActor._start</summary>

{{< source-reference id="source-1" >}}

</details>

<details>
<summary>展开 Slime 源码：_GenerationActor._produce</summary>

{{< source-reference id="source-2" >}}

</details>

容量 1 表示最多 1 份结果**已经入队**。生产者本身还可能持有正在等待入队的结果，所以它不是整个系统的内存总量上限。

### Slime 怎样取走“现在已经完成”的结果

`AsyncRolloutWorker.get_completed_groups()` 使用同步 `queue.Queue`。它调用 `get_nowait()`：有结果就立刻取走，没有就抛出 `queue.Empty`，于是这一轮停止收集。它没有等待未来才会出现的结果。

<details>
<summary>展开 Slime 源码：同步队列的非阻塞收集</summary>

{{< source-reference id="source-3" >}}

</details>

{{< python-async-coverage lesson="07-queues" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../06-semaphore/) · [下一节：10 · 线程池：把阻塞工作移出事件循环](../08-executors/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
