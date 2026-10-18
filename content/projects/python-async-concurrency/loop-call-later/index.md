---
title: "call_later：定时登记与 Slime 分批放行"
linkTitle: "补充：call_later"
learningSupplement: true
description: "比较立即排队和登记定时调用，再看 Slime 的 AsyncPacer 如何分批完成 Future。"
weight: 510
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> [前置教学：call_soon](../loop-call-soon/)已经区分普通回调、协程和 Handle；[20.3–20.4](../20-future-result/)解释了 Future 的完成与等待。
>
> **本节新增的问题：** 同一个普通函数，希望它尽快执行或延迟执行，怎样登记？延迟到期是否意味着立刻打断其他代码？

**两者都是现在登记。`call_soon` 把回调放入就绪队列；`call_later` 登记一个定时调用，到期后由循环处理。** 当前代码不会因登记而暂停。

## 1. 先登记延迟回调，再登记尽快执行的回调

本例用 0.1 秒缩短等待时间；换成 2 秒，机制相同。两次都调用同一个 `report`，只改变登记方式。

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

```python
import asyncio


def report(label, finished):
    print(label)  # 只有循环真正调用 report，才会打印这份标签。
    if label == "later":
        finished.set_result(None)  # 标记延迟回调已经执行，允许主协程结束。


async def exercise():
    loop = asyncio.get_running_loop()
    finished = loop.create_future()  # 只用来等最后一个回调执行完。

    loop.call_later(0.1, report, "later", finished)  # 现在登记，约 0.1 秒后才到期。
    loop.call_soon(report, "soon", finished)  # 后登记，但直接进入就绪队列。
    print("both registered")  # 登记立即返回，两份回调此时都还没有执行。
    await finished  # 当前协程挂起，让循环执行回调并等待延迟回调完成。
    print("finished")


if __name__ == "__main__":
    asyncio.run(exercise())
```

Python 3.12.3 下的实际输出：

```text
both registered
soon
later
finished
```

1. `call_later` 先登记到期时间，不是等 0.1 秒以后才开始登记。
2. `call_soon` 随后把另一份回调放进就绪队列。它不是插队，但不必等前面那份定时调用到期。
3. `await finished` 交还执行机会；循环先调用 `report("soon", ...)`。
4. 延迟回调到期后，循环调用 `report("later", ...)`，并完成 Future，主协程才结束。

`finished` 只是本例等待延迟回调完成的明确条件；不是 `call_later` 返回的对象。`call_later` 立即返回的是 `TimerHandle`，和 Handle 一样可以在执行前取消登记。

## 2. 到期是可以执行，不是保证准点执行

在 CPython 中，`call_later` 立即把记录放进定时队列；循环检查到期记录，将它们转入就绪队列，再逐个执行。定时器精度还受时钟分辨率影响，不应把它当作精确定时器。

如果循环线程被一段同步代码阻塞，即使设置的时间已经到，也要等循环重新获得执行机会。它不会在第 2 秒强行打断正在运行的函数。

| 比较点 | call_soon | call_later |
| --- | --- | --- |
| 什么时候登记 | 现在 | 现在 |
| 登记在哪里 | 就绪队列 | 定时调用队列 |
| 什么时候执行 | 循环处理到这份就绪回调时 | 到期后，循环处理到这份回调时 |
| 返回什么 | Handle | TimerHandle |
| 回调执行前能否取消 | 可以 | 可以 |

## 3. Slime 确实用到了：一批最多放行 64 个等待者

Slime 的 `AsyncPacer` 使用这两个接口分批完成 Future：

1. 请求进入 `wait()`，创建并保存一份 Future；第一位等待者用 `call_soon(self._release)` 登记释放动作。
2. `_release()` 每批最多完成 64 份 Future，让对应等待者可以继续。
3. 如果还有等待者，用 `call_later(0.001, self._release)` 登记下一批，让循环有机会处理其他回调和 I/O。

它控制的是分批放行的节奏，不是“最多允许 64 个业务任务同时运行”；也没有等待上一批业务任务结束。

[下载可运行的 Slime 裁剪例子 slime-pacer.py](slime-pacer.py)，运行 `python3 -W error slime-pacer.py`。例子安排 65 个等待者，实际输出为：

```text
schedule call_soon
release 64
schedule call_later
release 1
finished 65
```

这里保留真实的 `AsyncPacer` 类、`wait` / `_release` 方法、`pending` / `scheduled` 字段、每批 64 个和 0.001 秒延迟。只增加三处 print 观察与标准库测试入口，不需要启动 Slime、模型或训练。

<details><summary>按需阅读：原始源码与版本依据</summary>

源码已核对本地 Slime 的 Git blob，固定为 `22a89f96835969a47055a659c588f46151f8b07a`。原文件：[slime/utils/async_utils.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/async_utils.py#L8)。下面是未经添加观察输出的原类：

```python
class AsyncPacer:
    """Reduce asyncio scheduling pressure by resuming waiting tasks in batches.

    At high concurrency, waking many tasks at once floods the loop's ready
    queue with callbacks, delaying socket I/O and timers. Release at most 64
    waiters per tick, with a 1 ms delay between batches, to spread that work
    across loop iterations. This paces task starts without limiting in-flight
    concurrency or waiting for previously released tasks to finish.

    Use each instance within a single event loop.
    """

    def __init__(self):
        self.pending = deque()
        self.scheduled = False

    async def wait(self):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending.append(future)
        if not self.scheduled:
            self.scheduled = True
            loop.call_soon(self._release)
        await future

    def _release(self):
        for _ in range(min(64, len(self.pending))):
            future = self.pending.popleft()
            if not future.done():
                future.set_result(None)
        if self.pending:
            # Let socket callbacks and timers run before waking more tasks.
            asyncio.get_running_loop().call_later(0.001, self._release)
        else:
            self.scheduled = False
```

Python 依据：[call_soon](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.call_soon)、[call_later](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.call_later)。例子按 Python 3.12.3 验证，最低 Python 3.11。

</details>

## 4. 自查

1. 延迟回调先登记，为什么本例仍然先打印 soon？
2. 0.001 秒到了，但循环还在执行别的函数，能保证下一批此时已经放行吗？
3. 输出 release 64，是否说明第一批 64 个业务任务都已经做完？

[关系摘要：call_soon 与 call_later](../comparisons/call-soon-vs-call-later/) · [前置教学：call_soon](../loop-call-soon/) · [当前学习记录](../learning-route/#reading-status)

{{< resource-aliases path="projects/python-async-concurrency/comparisons/call-soon-vs-call-later" >}}
