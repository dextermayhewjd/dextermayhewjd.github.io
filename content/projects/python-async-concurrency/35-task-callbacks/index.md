---
title: "35.3 · Task.add_done_callback：任务完成后安排回调"
description: "一个 Task、一个普通函数，分清登记回调与执行回调。"
weight: 353
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 03 课](../03-tasks/)用 create_task 安排协程；[第 08 课](../07-task-results/)读取 Task 的结果；[20.4–20.5](../20-await-future/)区分执行任务、保存结果与等待交付。[35.2](../35-future-completion/)另有结果交付的源码回顾，可按需阅读。
>
> **本节新增的需求：** Task 结束时，希望自动调用一个函数来处理结果，不用每次都手动在 await 后面调用它。
>
> **本节的解决方式：** 用 task.add_done_callback(on_done) 登记一个任务结束后的 post hook。Task 完成后，事件循环调用 on_done(task)。

## 1. add_done_callback：登记任务结束后的 post hook

**可以把它理解为任务结束后的 post hook：提前登记，Task 结束后再执行。**

这里 post 表示“在任务结束之后”，hook 表示预先登记的处理函数。这个 hook 就是本节的回调 on_done；事件循环负责在 Task 完成后调用它。正常返回、抛出异常或被取消，都可能使任务结束。

本节沿用已经学过的 Task：generate 返回 7，Task 保存 7。然后回调读取这个结果。

## 2. add_done_callback / result：只看一个短例子

主例子是独立的标准库实验，只演示成功完成。

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio


async def generate():
    return 7  # Task 完成时，保存这个返回值。


def on_done(done_task):
    print("callback", done_task.result())  # 收到已完成的 Task，读取它的结果 7。


async def exercise():
    task = asyncio.create_task(generate())  # 安排 generate 运行。
    task.add_done_callback(on_done)  # 登记 post hook；任务结束后调用 on_done(task)。
    print("registered", task.done())  # False：此时只完成登记，任务还没运行。
    await task  # 等 generate 结束；回调由事件循环调用，不是这一行手动调用。


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

实际输出：

```text
registered False
callback 7
```

按三个阶段读：

1. **登记。** 第 13 行安排 Task，第 14 行登记 on_done。默认调度下，exercise 还没有让出执行权，所以先打印 False；on_done 还没有被调用。
2. **任务完成。** 第 16 行 await 让 exercise 等待。事件循环运行 generate，它返回 7，Task 保存结果并变成已完成。
3. **执行回调。** 事件循环调用 on_done(task)，把原来的 Task 作为参数传进去。第 9 行 result() 取得 7，于是打印 callback 7。

**done_task 就是前面的 task，不是数值 7，也不是新创建的 Task。** 数值需要通过 done_task.result() 读取。

## 3. on_done：传函数，不是提前调用它

<span id="task-done-callback"></span>

第 14 行传入的是 **on_done 这个函数**，不写 on_done()。后者会立刻调用函数，而且这里还缺少 done_task 参数。

add_done_callback 是普通方法，返回 None，不需要 await。它登记的函数会收到一个参数：完成的 Task。这里的回调用普通 def；直接传 async def，循环不会自动 await 它返回的协程。

回调在同一个事件循环线程里执行，不会另开线程。它适合简短的结果处理、日志或从任务集合中移除已结束的任务。

**登记回调和等待任务各做一件事：** add_done_callback 决定“结束后做什么”；本例的 await task 等任务结束，让 exercise 不要提前离开。任务完成才触发回调，并不要求必须写这一处 await。

如果登记时 Task 已经完成，回调仍会被安排执行；它不会直接在 add_done_callback 这一行同步运行。

## 4. result：完成回调也要区分成功、失败与取消

回调在 Task 结束时运行，结束不一定成功。下面复用第 08、09 课的规则，不再增加一份失败实验。

<div class="async-api-reference">

| Task 的结束情况 | 回调里的 result() | 处理方式 |
| --- | --- | --- |
| 成功返回 | 得到返回值 | 使用结果 |
| 抛出异常 | 再抛出该异常 | 用 try/except 处理，或用 exception() 读取异常对象 |
| 被取消 | 抛 CancelledError | 单独处理取消；exception() 也会抛 CancelledError |

</div>

主例子确定成功，所以直接 result()。真实回调如果同时接收这些状态，就需要处理对应分支；登记回调不会自动把失败变成成功。

## 5. add_done_callback：带走三条结论

1. add_done_callback 登记任务结束后的 post hook，再由事件循环安排执行。
2. 回调收到的是那个 Task，要用 result() 等方法读取它的结果或异常。
3. 回调负责结束后的处理，await 负责等待；二者职责不同。

自查：为什么登记时打印 False，回调里却能直接读取 7？

<details><summary>查看解释</summary>

登记时任务还没运行，on_done 也没有执行。generate 返回 7 后，Task 已经完成，循环才调用 on_done，因此回调能读取完成后的结果。

</details>

下一单元进入事件循环本身：除了 asyncio.run，怎样明确创建、运行和关闭一个循环？

{{< python-async-slime title="按需阅读：源码对照与适用范围" >}}

Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 fully-async 路径为每个生成 Task 登记完成回调：

{{< source-reference id="source-1" >}}

这里 _make_done_cb(gid) 返回一个回调函数，add_done_callback 再登记这个返回的函数。它没有在这一行提前处理任务结果。

{{< source-reference id="source-2" >}}

真正的回调 _cb 接收 done_task，读取结果，并分别处理取消与失败。这与主例子的 on_done 是同一种机制。主例子只打印成功结果，没有复现 Slime 的回调工厂、样本筛选、重新入队和输出队列；这些业务留到源码阅读。

{{< python-async-coverage lesson="35-task-callbacks" >}}

依据：[Python 3.12：Task.add_done_callback](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.Task.add_done_callback)、[Future 回调规则](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.Future.add_done_callback)。主例子在 Python 3.12.3 默认调度方式下运行，适用本教程 Python 3.11 及以上版本。

{{< /python-async-slime >}}

---

[上一节：35.2 · 创建 Future 并写入结果](../35-future-completion/) · [下一节：36.1 · 手动管理事件循环](../36-manual-event-loop/) · [当前补课顺序](../learning-route/#priority-reading)
