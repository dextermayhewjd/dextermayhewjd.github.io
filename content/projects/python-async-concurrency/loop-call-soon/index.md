---
title: "call_soon：登记回调、Handle 与执行"
linkTitle: "补充：call_soon"
learningSupplement: true
url: "/projects/python-async-concurrency/loop-call-soon/"
description: "比较普通回调与协程，观察执行、暂停和结果返回，再用 Handle 取消一次修改状态的回调。"
weight: 500
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> [第 03 课](../03-tasks/)用 `create_task` 安排协程，[20.2](../20-running-loop/)取得当前循环。现在把 `call_soon` 放到同一个例子里比较。
>
> **本节的问题：** 都是交给 loop 安排，登记一个普通函数与安排一份协程，到底有什么不同？

**`call_soon` 登记一次普通函数调用；`create_task` 安排协程的执行，并用 Task 保存它的完成结果。** 两者使用同一个事件循环，本例都不创建新线程。

<span id="call-soon-vs-task"></span>

## 1. 先把两种写法并排看

| 比较点 | `loop.call_soon(report)` | `asyncio.create_task(report_async())` |
| --- | --- | --- |
| 交给循环的是什么 | 普通函数 `report`，没有提前调用 | `report_async()` 创建的协程对象 |
| 本例怎样执行 | 调用普通函数，连续打印 start、end，然后返回 | 开始执行，在 await 处暂停，随后恢复并返回 |
| 调用方拿到什么 | 登记句柄 `Handle`，不是函数返回的 7 | `Task`，可以通过 `await task` 取得返回的 7 |

下面两份工作都打印 start、end，都返回 7。协程中只多一处已学过的 `await asyncio.sleep(0)`，用来显示暂停和恢复。

## 2. 一个能直接看到差别的例子

先安排 Task，再登记普通回调。观察：Task 开始以后，普通回调能否在它结束前执行？

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

```python
import asyncio


def report():
    print("callback: start")
    print("callback: end")  # 普通回调：本次调用在这里连续执行到结束。
    return 7  # 这个返回值不会成为 Handle 中可等待的结果。


async def report_async():
    print("task: start")
    await asyncio.sleep(0)  # 暂停这份 Task，让循环执行其他已经就绪的工作。
    print("task: end")  # 循环随后恢复这份 Task，继续执行函数体。
    return 7  # Task 保存这个结果，等待它的调用方可以取得。


async def exercise():
    loop = asyncio.get_running_loop()  # 两份工作交给当前同一个循环。
    task = asyncio.create_task(report_async())  # 先安排协程，返回可等待的 Task。
    handle = loop.call_soon(report)  # 再登记普通函数，返回登记句柄 Handle。
    print("main: both scheduled")  # 默认调度下，两份工作都还没开始。
    result = await task  # 当前协程等 Task 结束，循环可以运行刚才安排的工作。
    print("main: task result", result)  # 得到 report_async 返回的 7。


if __name__ == "__main__":
    asyncio.run(exercise())
```

Python 3.12.3 默认调度下的实际输出：

```text
main: both scheduled
task: start
callback: start
callback: end
task: end
main: task result 7
```

## 3. 沿输出看执行、暂停与恢复

| 顺序 | 当前执行什么 | 这一步说明什么 |
| --- | --- | --- |
| 1 | `exercise` 打印 `main: both scheduled` | 安排完成以后，当前代码仍先继续运行 |
| 2 | `report_async` 打印 `task: start`，在 await 处暂停 | Task 已开始，但还没有结束 |
| 3 | `report` 连续打印 `callback: start` 和 `callback: end` | loop 执行了登记的普通函数，本次调用连续完成 |
| 4 | `report_async` 恢复，打印 `task: end` 并返回 7 | Task 的同一次执行跨过了暂停与恢复 |
| 5 | `exercise` 恢复，打印 `main: task result 7` | `await task` 取得协程的最终结果 |

关键是中间四行：

```text
task: start
    callback: start
    callback: end
task: end
```

普通回调出现在 Task 的开始与结束之间，因为 Task 在 await 处交还了执行机会。这里没有两个线程同时打印。

## 4. 两个函数都返回 7，为什么最后只取到了 Task 的 7？

- `report` 返回的 7 被忽略。这里保留这个返回值，是为了和协程返回 7 作对比；`call_soon` 不会把它保存进 `handle`。
- `report_async` 的返回值由 `task` 保存；调用方通过 `await task` 取得这个 7。

因此本例写 `result = await task`。`handle` 不是可等待对象，不能照搬成 `await handle`。

`create_task` 安排的协程也可以没有 await；本例特意加一处等待，让“可以暂停再恢复”出现在输出中。两种机制的区别还包括接收的对象与结果接口，不能只看函数有没有真的暂停。

<span id="call-soon-handle"></span>

## 5. Handle 能做什么：取消尚未执行的登记

分清两个返回时刻：

1. 当前协程调用 `loop.call_soon(report)`，立刻拿到 `Handle`。这时 `report` 还没有执行。
2. 稍后循环执行 `report()`，它返回 7；这个返回值不会变成 Handle 的结果。

**Handle 管理的是“这一次登记”，可以在回调执行前取消它。** 它不提供 Task 那样的 `await` 和结果读取。

| 操作 | 含义 |
| --- | --- |
| `handle.cancel()` | 取消这份尚未执行的回调登记 |
| `handle.cancelled()` | 检查这份 Handle 是否被取消 |

下面把回调的实际动作改为“向列表添加一项”。它不打印，也不返回业务结果；外面的代码通过列表变化观察动作是否发生。

[下载 cancel.py](cancel.py)，运行 `python3 -W error cancel.py`。

```python
import asyncio


def record(events, name):
    events.append(name)  # 真正的动作是修改列表；这个回调不依靠返回值交付结果。


async def exercise():
    loop = asyncio.get_running_loop()
    events = []

    handle = loop.call_soon(record, events, "cancelled")  # 登记一次 record(events, "cancelled")。
    handle.cancel()  # 回调尚未执行，取消这一份登记。
    loop.call_soon(record, events, "kept")  # 另一次登记不取消，稍后会修改列表。

    print("before", events)  # 尚未交还执行机会，两次回调都没有运行。
    await asyncio.sleep(0)  # 循环跳过被取消的回调，执行保留的那一个。
    print("after", events)
    print("cancelled", handle.cancelled())  # True 表示这份 Handle 已被取消。


if __name__ == "__main__":
    asyncio.run(exercise())
```

Python 3.12.3 下的实际输出：

```text
before []
after ['kept']
cancelled True
```

`cancelled` 那一项没有被添加，`kept` 那一项被添加了。取消只针对拿到这份 Handle 的登记，不会取消所有回调。

`cancelled()` 不是“工作是否已经完成”的检查。若回调已经执行并修改了列表，之后再调用 `cancel()` 也不会撤销那次修改。

<span id="call-soon-actions"></span>

## 6. call_soon 的用途：安排动作，不限于日志和打印

**`call_soon` 的职责是安排一次普通函数调用；至于调用后做什么，由这个函数决定。** 前面用 print，是为了直接看到执行顺序。

| 普通回调可以做的动作 | 产生的效果 |
| --- | --- |
| 打印、记录日志 | 输出一条消息 |
| 像 `record` 一样修改列表或更新状态 | 改变已有对象，供其他代码读取 |
| `event.set()` | 发出通知，让等待者可以继续 |
| `future.set_result(value)` | 完成已有的 Future，让等待者取得结果 |
| Slime 中的 `AsyncPacer._release()` | 处理一批等待者，完成对应 Future |

因此，它可以安排真正影响程序状态的动作。回调不依靠 return 交付结果时，常常自然返回 `None`；需要交付结果，也可以明确写入已有对象或完成 Future，而不是从 Handle 取值。

日常日志可以直接调用 `logger.info(...)`，不必都经过 `call_soon`。只有希望由事件循环稍后安排这次调用时，才需要这一层登记。

回调仍在事件循环的线程里运行，适合短小的同步动作。把耗时阻塞函数交给 `call_soon`，不会让它自动进入后台线程；它仍可能阻塞循环。

## 7. 对回你刚才的理解

`call_soon` 登记的 `report`，就是之后真正被调用的函数。它不是给 `report_async` 加的“执行前钩子”：输出里 Task 已经开始了，`report` 才运行。

记住对应关系即可：

```python
loop.call_soon(report)                    # 传普通函数，登记一次调用。
task = asyncio.create_task(report_async())  # 传协程对象，安排其执行。
result = await task                       # 取得协程的完成结果。
```

自查：如果删除 `report_async` 中的 `await asyncio.sleep(0)`，为什么 Task 的 start 和 end 会连续打印？它是否仍然是 Task？

<details><summary>查看解释</summary>

没有等待点，这个函数体就能在本次执行中直接返回，因此 start、end 连续打印。它仍由 `create_task` 安排为 Task，返回值仍可以通过 `await task` 取得。

</details>

<details><summary>回顾：直接调用与 call_soon 的原例子</summary>

原来的例子保存在 [direct-call.py](direct-call.py)，运行 `python3 -W error direct-call.py`。

它只比较同一个普通函数的 `report()` 与 `loop.call_soon(report)`：直接调用立即执行；登记调用时，当前协程先打印 `scheduled: after`，交还执行机会后循环才调用 `report`。

</details>

<details><summary>按需阅读：标准库依据与后续用途</summary>

依据：[Python 3.12：loop.call_soon](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.call_soon)、[Handle](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.Handle)、[create_task](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.create_task)。本例按 Python 3.12.3 的默认调度验证，最低 Python 3.11。

普通回调由当前循环线程执行，阻塞调用也会阻塞这个循环。协程同样需要在等待点交还执行机会；`create_task` 本身不会把它移到工作线程。

Slime 的 `AsyncPacer` 用 `call_soon` 登记后续释放动作；可回到[源码中的分批完成 Future](../13-event-loop/#pacer-callbacks)辨认这种普通回调。

</details>

---

[关系摘要：create_task 与 call_soon](../comparisons/call-soon-vs-create-task/) · [当前学习记录](../learning-route/#reading-status) · [36.2：尚未读懂，暂时跳过](../36-threadsafe-submit/) · [Python 异步与并发](../)
