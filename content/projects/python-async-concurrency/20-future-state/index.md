---
title: "20.5 · Future 的状态与异常：分清等待、读取和完成"
description: "观察尚未完成、成功与失败，连接 Task 与 Future，同时明确一次完成的边界。"
weight: 205
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [20.3–20.4](../20-future-result/)用 `set_result` 完成 Future，通过 `await` 取得值；[第 08 课](../07-task-results/)区分 Task 的状态、结果与异常。
>
> **本课新增的问题：** 结果提供者报告失败时怎么办？怎样判断 Future 是否完成，区分等待、读取与写入完成结果？

## 1. 状态读取：先回接 Task 中见过的规则

本节比较未完成、成功和失败，并把第 09 课学过的取消状态并列回顾。

| 状态 | `future.done()` | `future.result()` | `future.exception()` | `await future` |
| --- | --- | --- | --- | --- |
| 尚未完成 | `False` | 抛 `InvalidStateError` | 抛 `InvalidStateError` | 等待完成 |
| 成功完成 | `True` | 返回值 | `None` | 返回值 |
| 失败完成 | `True` | 抛保存的异常 | 返回异常对象 | 抛保存的异常 |
| 已取消 | `True` | 抛 `CancelledError` | 抛 `CancelledError` | 抛 `CancelledError` |

这些状态下，读取规则与第 08–09 课的 Task 相同：`result()` 和 `exception()` 都不会等待；要等结果，用 `await`。

## 2. set_exception：完成一次失败，再观察读取

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

```python
import asyncio


async def exercise():
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    print("pending done", future.done())  # 尚未完成，返回 False。
    try:
        future.result()  # 只读取，不等待；尚未完成时抛 InvalidStateError。
    except asyncio.InvalidStateError:
        print("pending result InvalidStateError")

    future.set_exception(ValueError("read failed"))  # 记录失败并完成 Future；此处不抛该错误。
    print("failed done", future.done())  # 失败也算完成，因此是 True。
    print("stored error", future.exception())  # 读取已保存的异常对象。
    try:
        await future  # 等待失败的 Future，在这里收到保存的 ValueError。
    except ValueError as error:
        print("await raised", error)

    try:
        future.set_result([0, 1, 2])  # 已失败完成，不能再覆盖成成功。
    except asyncio.InvalidStateError:
        print("second completion InvalidStateError")


if __name__ == "__main__":
    asyncio.run(exercise())
```

实际输出：

```text
pending done False
pending result InvalidStateError
failed done True
stored error read failed
await raised read failed
second completion InvalidStateError
```

## 3. 两种错误，发生在不同的位置

1. **未完成就读取：** 第一处 `InvalidStateError` 是调用者读取太早；这时 Future 仍未完成。
2. **记录操作失败：** `set_exception` 保存 `ValueError` 并完成 Future，调用这行本身不抛出这个 ValueError。
3. **等待失败的结果：** `await future` 在等待方抛出保存的 ValueError；`result()` 读取失败结果时也会抛出它。
4. **重复完成：** 最后一处 `InvalidStateError` 是试图改写已经完成的 Future，原失败结果不会被覆盖。

读取结果不会重新执行提供者，也不会把 Future 重置。已经完成或取消的 Future 都不能再用 `set_result` / `set_exception` 完成一次。

## 4. Task 与 Future：共同的结果接口，不同的完成责任

`asyncio.Task` 继承 `asyncio.Future` 的许多状态与结果接口。这解释了为什么前面学过的 `done/result/exception` 又出现了。

| 对象 | 谁负责使它完成 |
| --- | --- |
| `loop.create_future()` 得到的 Future | 结果提供者显式交付值或异常；取消也是一种结束状态 |
| `asyncio.create_task(coro)` 得到的 Task | Task 驱动协程执行，依据协程的返回、异常或最终取消而结束 |

不能对 Task 使用 `set_result` / `set_exception` 来改写它的执行结果。给一份协程安排执行用 Task；需要连接外部结果提供者和等待者时，可以使用 Future。创建普通 Future 不会自动驱动一份协程。

本章讨论的是 **asyncio Future**。[第 31 课](../31-threadpool-submit/)会介绍线程池的 `concurrent.futures.Future`：它是另一种类，`.result()` 可以阻塞线程，不能直接 `await`。不要因为名称相同就照搬等待方法。

## 5. 带走三条结论

1. `done()` 只回答是否结束；失败也是结束。
2. `await` 可以等待，`result/exception` 只读取；`set_result/set_exception` 负责完成一次交付。
3. Task 还负责驱动协程；普通 Future 由结果提供者完成，本身不执行工作。

自查：`future.exception()` 返回异常对象，与 `await future` 抛出异常有什么区别？前者让调用方主动检查，后者把失败传到等待位置；它们读取的是同一次失败。

本节为独立标准库实验，按 Python 3.12.3 验证，最低 Python 3.11。依据：[Future 状态与结果](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.Future)、[Task](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.Task)。

---

[上一节：20.4 · 等待 Future](../20-await-future/) · [下一课：21.1 · 资源三阶段](../21-resource-lifecycle/) · [学习路线](../learning-route/)
