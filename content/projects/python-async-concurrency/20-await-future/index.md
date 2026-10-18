---
title: "20.4 · await Future：等待别处交付结果"
description: "分清等待者、结果提供者和 Future，沿 set_result 到任务恢复的过程阅读。"
weight: 204
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [20.3](../20-future-result/)先完成 Future，再取值；[第 03 课](../03-tasks/)用 `create_task()` 另行安排工作。
>
> **本课新增的问题：** 开始等待时结果还没到，怎样让一份任务等结果，另一份任务负责提供它？

## 1. 保留同一份结果对象，只改变谁完成它

上一节在 `exercise` 中直接 `set_result`。这次把这一步移到 `provide_samples`，用已学过的 `create_task` 安排它。

两份任务共用同一个 `future`：提供者写入，等待者读取。这个例子用于观察交接，不是推荐将一个简单的协程返回值都改写为 Future；如果工作本来就是一份可直接等待的协程，通常直接 `await` 它即可。

## 2. await：结果未到时让当前任务挂起

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

```python
import asyncio


async def provide_samples(future):
    print("provider running")
    future.set_result([0, 1, 2])  # 提供者完成结果，让等待者可以恢复。
    print("provider after set")  # set_result 不会在此处直接执行等待者。


async def exercise():
    loop = asyncio.get_running_loop()
    future = loop.create_future()  # 结果尚未到；创建对象本身没有启动提供者。
    provider = asyncio.create_task(provide_samples(future))  # 另行安排提供结果的工作。
    print("before await")
    samples = await future  # 默认调度下，提供者尚未运行；本任务在这里等住。
    print("received", samples)
    await provider  # 确认我们创建的提供者任务已结束。


if __name__ == "__main__":
    asyncio.run(exercise())
```

Python 3.12.3 默认任务调度下的实际输出：

```text
before await
provider running
provider after set
received [0, 1, 2]
```

## 3. 沿交接顺序分清三个角色

| 角色 | 本例中是谁 | 负责什么 |
| --- | --- | --- |
| 等待者 | 执行 `exercise` 的 Task | `await future`，等待并取得结果 |
| 提供者 | 执行 `provide_samples` 的 Task | 产生列表，调用 `set_result` |
| 结果对象 | `future` | 保存状态和结果，连接两边 |

1. 主任务创建未完成的 Future，并安排提供者任务。
2. `await future` 发现结果尚未就绪，主任务挂起，事件循环可以运行提供者。
3. 提供者调用 `set_result`，Future 完成，主任务可以恢复；提供者仍先执行自己的下一行。
4. 循环随后恢复主任务，`await future` 返回列表，赋给 `samples`。

这与 Event 的“通知不等于立即执行等待者”相连。但 Future 交付的是这次操作的结果，等待者直接取得列表，不必另查共享变量。

## 4. Future 与 Task：职责已经可以分开

`provider` 是 Task，它负责驱动一份协程执行。`future` 只表示这次结果的交付；它不知道取样函数如何运行。

本例特意没有使用提供者的 `return` 作为结果通道。提供者通过 `set_result` 交付列表；末尾 `await provider` 只是确认提供者任务结束。以后结果也可能由已有库的完成回调交付，不一定来自另一份协程。

如果提供者退出前始终没有完成 Future，等待就不会自行结束。提供者失败也不会自动把异常写进另一个 Future；需要明确的失败交付或收尾安排，下一节先学习 `set_exception()`。

自查：只执行 `loop.create_future()`，不安排提供者，列表会自动产生吗？不会。删除提供者的 `set_result` 后，等待者也不会因为提供者返回了就取得结果。

本节为独立标准库实验，最低 Python 3.11；未设置提前执行 Task 的工厂。依据：[Future 的等待语义](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.Future)。

---

[上一节：20.3 · 保存结果](../20-future-result/) · [下一节：20.5 · 状态与异常](../20-future-state/) · [学习路线](../learning-route/)
