---
title: "20.3 · create_future / set_result：保存一次完成的结果"
description: "从 Event 的通知进入 Future：把一次完成状态与结果值放在同一个对象里。"
weight: 203
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [20.1](../20-async-event/)的 Event 保存一个布尔标志；等待者得到的 `True` 只表示允许继续。[20.2](../20-running-loop/)已经取得当前事件循环对象。
>
> **本课新增的问题：** 这次等待的是一份操作的最终结果，希望等待完成时直接取得样本列表。怎样把完成状态和结果值放在一起？

## 1. 从通知到结果：为什么增加 Future

**要做的事：等到样本准备好，再取得样本列表。**

用 **Event + 一个共享变量** 就能做到。以等待方先等住的一次交接为例：

1. **等待方等通知：** `await release.wait()`，暂时停在这里。
2. **提供方保存结果：** 把样本列表存进共享变量。
3. **提供方发通知：** `release.set()`，让等待方可以继续。
4. **等待方取结果：** 恢复后，从共享变量读取样本列表。

如果操作失败，还要另存异常，并通知等待方来读取。

**Future 把完成状态、结果或异常放在同一个对象中。** 等待方直接通过它取得结果。

Future 本身不执行取样函数，创建它不会自动产生结果。结果既可以在等待前保存好，也可以稍后交付。

先用已经得到的列表观察“保存 → 取得”，下一节再加入等待。

## 2. create_future / set_result：先保存，再取得

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

```python
import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 沿用 20.2，取得当前循环。
    future = loop.create_future()  # 创建一份尚未完成的结果对象；没有启动工作。
    print("future created")
    samples = [0, 1, 2]
    future.set_result(samples)  # 保存这份列表，并把 future 标为成功完成。
    print("result stored")
    received = await future  # 已经完成，直接取得保存的列表。
    print("received", received)
    print("same value", received is samples)  # 取得保存的对象，没有复制列表。
    print("again", await future)  # 再等同一个 Future，仍取得同一份结果。


if __name__ == "__main__":
    asyncio.run(exercise())
```

实际输出：

```text
future created
result stored
received [0, 1, 2]
same value True
again [0, 1, 2]
```

## 3. 三个对象，各自是什么

| 名字 | 对象与作用 |
| --- | --- |
| `loop` | 正在运行的事件循环，创建属于它的 asyncio Future |
| `future` | 保存这一次完成状态与结果的 `asyncio.Future` |
| `samples`、`received` | 同一份样本列表；它是结果值 |

1. `loop.create_future()` 返回一个尚未完成的 Future。
2. `future.set_result(samples)` 保存列表，同时将它标为成功完成。
3. `await future` 取得列表。此时结果已经就绪，不需要挂起任务。
4. 再次 `await future` 仍读取同一份结果，不会重新取样，也不消耗结果。

一个 Future 只完成一次。它不像 Queue 那样交接一串数据，也没有 Event 的 `clear()` 重置过程；下一次独立操作使用另一份 Future。对已完成对象再次写入会报错，20.5 再观察这个边界。

## 4. 带走三条结论

1. 创建 Future 是创建一个等待结果的对象，不是安排一份工作。
2. `set_result(value)` 保存成功值并完成它；`await future` 取得该值。
3. Future 可以在等待前完成，也可以被重复等待；重复等待不重新执行工作。

自查：如果删掉 `set_result(samples)`，谁负责让这个 Future 完成？本例没有其他提供者，所以它将一直未完成；下一节会明确安排提供者。

本节为独立标准库实验，按 Python 3.12.3 验证，最低 Python 3.11。依据：[Future](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.Future)、[create_future](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.create_future)。

---

[上一节：20.2 · 当前事件循环](../20-running-loop/) · [下一节：20.4 · 等待 Future](../20-await-future/) · [学习路线](../learning-route/)
