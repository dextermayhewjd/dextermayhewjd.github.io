---
title: "35.2 · loop.create_future / Future.set_result / set_exception：创建 Future 并写入结果"
description: "只看一个 Future：创建、写入 7，再读出 7。"
weight: 352
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [35.1](../35-future-results/)已经学习用 done() 检查、用 result() 或 await 取结果；[33.1](../33-current-loop/)已经取得当前事件循环。
>
> **本节新增的需求：** 前面读到的结果，是怎样写进 Future 的？
>
> **本节的解决方式：** 用 create_future() 创建尚未完成的 Future，再用 set_result(7) 写入结果。整节先沿着同一个对象往下看。

## 1. Future：先只看创建、写入和读取

**本节只增加“自己创建 Future，并给它一个结果”这件事。**

创建时，Future 尚未完成；调用 set_result(7) 后，它保存结果 7，并变成已完成。这里没有把函数或任务放进去，写入的就是数值 7。

## 2. create_future / set_result：用一个顺序例子看清楚

这是独立的标准库实验，所有操作从上往下执行。asyncio.run 和 exercise 只是沿用已学的协程运行入口。

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 沿用 33.1：取出当前事件循环。
    future = loop.create_future()  # 创建尚未完成的 Future，此时没有结果。
    print("created", future.done())  # False：还没有写入结果。
    future.set_result(7)  # 写入结果 7，同时把这个 Future 标记为完成。
    print("completed", future.done())  # True：现在已经完成。
    print("result", future.result())  # 读取已经写入的 7。
    print("await", await future)  # 已经完成，直接得到 7；这次不会挂起。


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

实际输出：

```text
created False
completed True
result 7
await 7
```

按三个动作读：

1. **创建：** create_future() 返回一个新的 Future，done() 是 False。
2. **写入：** set_result(7) 操作刚才那个 Future，把结果设为 7，done() 变成 True。
3. **读取：** result() 和 await future 都取得已有的 7，不会重新执行工作。

**本例在 await 之前已经写入结果，所以这一次 await 不会挂起。** 如果 Future 尚未完成，await 才需要等其他代码完成它；await 自己不会产生结果。先把“结果写在哪里”看清，再学习另一处代码怎样来写。

## 3. set_exception：把完成结果换成失败

<span id="future-completion"></span>

成功与失败是两种完成方式，选一种即可：

<div class="async-api-reference">

| 写入操作 | Future 保存什么 | 后续 await / result() 会怎样 |
| --- | --- | --- |
| future.set_result(7)：标记成功完成 | 数值 7 | 得到 7 |
| future.set_exception(ValueError("failed"))：标记失败完成 | 这个异常 | 抛出这个 ValueError |

</div>

两个方法都不需要 await。set_exception 保存异常，等待或读取结果时才会抛出；35.1 的 exception() 则用于取出异常对象。

**同一个 Future 只能完成一次。** 成功、失败或取消后，再调用 set_result 或 set_exception 都会抛 InvalidStateError，不能用它反复覆盖结果。

## 4. Future：带走三条结论

1. create_future() 创建一个尚未完成的结果对象，不会启动工作。
2. set_result(value) 写入成功值；set_exception(error) 写入失败异常。
3. 写入后 Future 已经完成；await 可以直接取得结果，不是每次都会挂起。

自查：在这个例子里，如果把 set_result(7) 移到 await future 后面，程序能走到写入那一行吗？

<details><summary>查看解释</summary>

不能。当前协程先等住了，后面的写入没有机会执行；本例又没有其他代码来完成这个 Future。真正需要“先等、后写”的场景，必须另外安排能执行写入的代码。

</details>

后面再把这个对象接回任务和回调：Future 保存结果，执行代码负责在合适的时候完成它。

{{< python-async-slime title="按需阅读：源码对照与适用范围" >}}

主例子用顺序操作帮助辨认对象，不是 Slime 业务函数的裁剪版，也没有演示等待中的协程恢复。Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 则把创建、等待与写入放在不同位置：

{{< source-reference id="source-1" >}}

现在只认出 wait 中的 create_future 和 await future；队列与回调调度随后再串联。

{{< source-reference id="source-2" >}}

_release 取出之前保存的同一个 Future，确认尚未完成，再用 set_result(None) 完成它。这里的结果是 None，表示等待者可以继续；没有把 Task 填进 Future。

{{< python-async-coverage lesson="35-future-completion" >}}

依据：[Python 3.12：创建 Future](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.create_future)、[写入结果与异常](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.Future.set_result)。主例子在 Python 3.12.3 下运行，适用本教程 Python 3.11 及以上版本。

{{< /python-async-slime >}}

---

[上一节：35.1 · 读取 Future 的结果](../35-future-results/) · [下一节：35.3 · 完成回调](../35-task-callbacks/) · [当前补课顺序](../learning-route/#priority-reading)
