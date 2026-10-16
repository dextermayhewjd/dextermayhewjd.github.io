---
title: "33.2 · run_in_executor / await：提交到指定线程池并等待结果"
description: "把第 26 课的 await 等待和第 31 课的自选线程池接起来。"
weight: 332
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 26 课](../26-to-thread/)已经用 await 等线程工作；[31.1](../31-threadpool-submit/)已经会创建自己的线程池；[33.1](../33-current-loop/)取得了当前事件循环。
>
> **本节新增的问题：** 使用自己选定的线程池时，怎样让协程也能用 await 等待结果？

<span id="executor-await"></span>
<span id="1-get_running_loop--run_in_executor把指定线程池接到协程等待"></span>
<span id="11-to_thread--threadpoolexecutor先接回第-2631-课"></span>
<span id="12-协程--线程沿用第-26-课的两个执行位置"></span>
<span id="13-reader--loop分别管理线程和调度协程"></span>

## 1. run_in_executor：把已学的两个部分接起来

还是调用 `get_samples(3)`，取得 `[0, 1, 2]`。第 26 课的 `to_thread` 使用默认线程池；现在要用第 31 课那样自己创建的线程池。

先把本例名称对回旧知识：

<div class="async-api-reference">

| 名称 | 本例负责什么 |
| --- | --- |
| `reader` | 线程池对象，角色与第 31 课的 `executor` 相同；名字由我们选择 |
| `get_samples` | 普通同步函数，在工作线程中生成列表 |
| `get_samples_async` | 在主线程运行的协程函数，负责提交工作、等待和接回结果 |
| `loop` | 33.1 已经取得的当前事件循环 |

</div>

**同步函数做实际取数，协程函数负责提交与等待。** 脚本直接运行 `get_samples_async`，先用这一条调用链看清交接。

<span id="2-run_in_executor--await提交一次再等这一次的结果"></span>

## 2. run_in_executor / await：提交一次，接回一次结果

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples):
    # 工作线程：提交后被 reader 安排执行，不必等主协程执行 await。
    return list(range(num_samples))


async def get_samples_async(reader, num_samples):
    # 主协程 1：取得当前事件循环；这一步还没有提交 get_samples。
    loop = asyncio.get_running_loop()
    # 主协程 2：现在提交 get_samples(num_samples)；工作线程就可以开始执行。
    future = loop.run_in_executor(reader, get_samples, num_samples)
    print("work submitted")  # 主协程 3：提交已返回；不表示取数刚开始或已经结束。
    # 主协程 4：等这次结果；Future 未就绪时挂起，就绪时取得列表。
    samples = await future
    print("samples", samples)  # 主协程 5：已取得 get_samples 返回的列表。
    return samples


if __name__ == "__main__":
    # reader 是本例的线程池变量名，对应第 31 课的 executor。
    with ThreadPoolExecutor(max_workers=1) as reader:
        # 主线程运行这一个协程；reader 中的工作线程运行同步取数函数。
        asyncio.run(get_samples_async(reader, 3))
    print("pool closed")
```

</div>

实际输出：

```text
work submitted
samples [0, 1, 2]
pool closed
```

`reader` 由 `with ThreadPoolExecutor(...)` 创建。它在本例使用一个工作线程；协程仍在主线程里运行。

**代码中的 1–5 只标记主协程的执行顺序。** `get_samples` 在工作线程运行，它与这几个步骤如何交错，接下来单独说明。

<span id="3-get_running_loop提交await分别在哪一步发生"></span>

## 3. run_in_executor / await：把核心三行分开读

### 3.1. get_running_loop：先取得当前循环

```python
loop = asyncio.get_running_loop()  # 取得 33.1 认识的同一个事件循环。
```

沿用上一节的动作，不会新建事件循环或线程池。

### 3.2. run_in_executor：现在提交，拿到结果对象

```python
future = loop.run_in_executor(reader, get_samples, num_samples)  # 提交给 reader，返回 asyncio Future。
```

三个参数分别回答：交给哪个池、执行哪个函数、传入什么参数。这里只传函数名，不先写 `get_samples(...)` 执行函数，这一点延续第 26、27、31 课。

提交发生在这个调用内部。工作线程被安排执行后，就会进入 `get_samples(num_samples)`；它甚至可能在这一行返回 Future 之前就开始运行。主协程得到 `future` 后，继续打印 `work submitted`。

**这里交出去的是同步函数，由另一个线程执行；启动它不依赖当前协程先执行 await。**

### 3.3. await：等待这次工作的结果

```python
samples = await future  # 结果未完成时挂起当前协程；取得列表后才继续。
```

`future` 代表尚待取得的结果，`samples` 才是 `[0, 1, 2]`。await 等的是刚才提交的同一次调用，不会重新调用函数。

工作线程执行 `get_samples`；主线程中的协程在 await 处等待。结果就绪后，协程取得列表，继续打印 `samples`。

### 3.4. run_in_executor / await：get_samples 到底什么时候运行？

下面画出**一种可能的交错顺序**：左边是主线程中的协程与事件循环，右边是 reader 的工作线程。L 对应上面主例子的行号。

```text
# STEP | MAIN: get_samples_async / loop   | WORKER: get_samples
# T01  | L12 get_running_loop()           |
# T02  | L14 submit to reader             |
# T03  |                                  | L5 enter get_samples(...)
# T04  | L14 receive Future               |
# T05  | L15 print("work submitted")      |
# T06  | L17 await future [pause]         |
# T07  |                                  | L7 return list(range(num_samples))
# T08  | loop delivers result to Future   |
# T09  | L17 await future [resume]        |
# T10  | L18 print("samples", samples)    |
```

图里 **T03 已经进入 get_samples，而 T06 才执行 await**。取数由 T02 的提交触发，await 负责等待结果；在 T06 挂起的是主协程，工作线程仍可继续运行。T08 是事件循环转交线程结果的步骤，由标准库完成。

**T03 的位置不是固定的。** 工作线程也可能在主协程打印 `work submitted` 之后才进入函数，或者早在主协程执行 await 之前就返回了结果。Future 如果已经就绪，await 会直接取得结果，不经过图里的挂起和恢复。

无论怎样交错，都必须先提交工作，工作线程才能运行本次 `get_samples`；主协程必须先取得结果，才能打印 `samples [...]`。

主例子的 `get_samples` 没有打印日志，所以实际输出没有直接显示它进入和返回的时刻。`work submitted` 只能证明提交已返回，不能据此判断取数进度；`samples [...]` 才能证明主协程已经取得结果。

自查：如果在 `get_samples` 开头加一句 `print("worker started")`，它与 `work submitted` 哪一句先出现？

<details><summary>查看解释</summary>

两种顺序都可能。工作线程可能在提交返回前就进入函数，也可能在主协程打印之后才进入；不能依靠某一次输出，把其中一种顺序当成保证。它一定先于主协程打印 `samples [...]`，因为必须先运行函数并返回，才能取得它的结果。

</details>

<span id="14-future--samples继续分开等待对象和最终结果"></span>

## 4. Future / await：和第 31 课真正差在哪里？

两节都有“提交工作 → 等结果”，主要区别在返回的结果对象：

<div class="async-api-reference">

| 提交入口 | 得到什么，怎样等 |
| --- | --- |
| 第 31 课 `reader.submit(...)` | `concurrent.futures.Future`；用 `result()` 等待时，未完成会阻塞调用线程 |
| 本节 `loop.run_in_executor(reader, ...)` | `asyncio.Future`；用 await 等待时，未完成可以挂起当前协程，让事件循环继续工作 |

</div>

**是同一类“交给线程池执行”的需求，接回结果的方式适配了协程。** 结果已经就绪时，await 不一定挂起，这一点与第 03 课相同。

<span id="4-await自己在等为什么其他协程还能运行"></span>

主例子只有一个协程，同步函数也很短。下一节单独用通知实验观察：当前协程等待时，其他协程怎样继续运行。

<span id="5-run_in_executor带走三条结论"></span>

## 5. run_in_executor / await：带走三条结论

1. `reader` 是自己创建的线程池，`loop` 是当前事件循环；两者继续承担前面学过的职责。
2. `run_in_executor` 调用时提交同步函数，返回可 await 的 asyncio Future。
3. `await future` 取得同一次调用的结果；结果未完成时，挂起的是当前协程。

自查：`get_samples` 在哪个线程执行？`get_samples_async` 在哪个线程执行？`future` 本身是列表吗？

<details><summary>查看解释</summary>

同步函数在 reader 的工作线程执行；协程在主线程执行。Future 是结果对象，await 后拿到的 samples 才是列表。

</details>

同步函数抛错时，异常在 await 处传回。取消等待者不会强行停止已经开始的同步函数，延续第 26 课的边界。

<span id="6-get_running_loop--run_in_executor本课接口速查"></span>

## 6. run_in_executor：本节接口速查

<div class="async-api-reference">

| 调用或动作 | 作用 |
| --- | --- |
| `loop.run_in_executor(reader, func, *args)` | 向指定执行器提交函数与参数，返回 asyncio Future |
| `await future` | 等待并取得结果；函数失败时传回异常 |

</div>

传入 `None` 作为第一个参数时，会使用循环的默认执行器；本节先看显式传入 reader 的用法。已经通过 `submit()` 拿到执行器 Future 时，如何改为 await，留给[第 34 课](../34-wrap-future/)。

{{< python-async-slime title="按需阅读：原始源码与教学裁剪" >}}

沿用 Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `get_samples`、`get_samples_async` 名称。正文把 `self._reader` 改为显式传入的 reader，把真实队列/文件读取缩成生成列表，并把原来的一行拆成取得循环、提交和等待三步。

{{< source-reference id="source-1" >}}

标准库依据：[Python 3.12：loop.run_in_executor](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.run_in_executor)。例子在 Python 3.12.3 运行，最低 Python 3.11。

{{< python-async-coverage lesson="33-run-in-executor" >}}

{{< /python-async-slime >}}

---

[上一节：33.1 · get_running_loop](../33-current-loop/) · [下一节：33.3 · await / Event](../33-await-handoff/) · [重点续学路线](../learning-route/#priority-reading)
