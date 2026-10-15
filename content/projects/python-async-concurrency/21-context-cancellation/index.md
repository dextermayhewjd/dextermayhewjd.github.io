---
title: "21.6 · Task.cancel：使用区被取消后怎样关闭"
description: "第 21 单元拆分学习的第 6 步：Task.cancel：使用区被取消后怎样关闭。"
weight: 216
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 09 课](../09-task-cancellation/#task-cancellation)用 `cancel()` 请求取消，再用 `await task` 等待收尾；[第 20 课](../20-async-event/#event-notification)用 `Event.set()` 发出通知、`Event.wait()` 等待通知；[21.5](../21-context-errors/)观察了资源退出时的关闭。
>
> **本课新增的问题：** 先确认任务拿到了资源，再取消它；调用方怎样确认资源的异步关闭也已经完成？

## 1. Task.cancel：在使用沙箱的等待中请求取消

21.5 已经观察了使用区报错后的关闭。现在只增加一个条件：**任务已拿到沙箱，正在等待时，另一个任务请求取消它。**

本例继续复用 21.4 的 boot_agent_sandbox，并用 Event 确认 work 已经进入使用区；收到这个通知后，调用方才请求取消。随后观察 `await task` 怎样等到资源退出。

## 2. Task.cancel / finally：先确认进入，再取消并等待

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
import asyncio
from contextlib import asynccontextmanager


@asynccontextmanager
async def boot_agent_sandbox(image, instance_id):
    print("boot", image, instance_id)
    await asyncio.sleep(0)
    sb = {"open": True}
    try:
        yield sb
    finally:
        print("closing", instance_id)
        await asyncio.sleep(0)
        sb["open"] = False
        print("closed", instance_id)


async def exercise():
    entered = asyncio.Event()

    async def work():
        async with boot_agent_sandbox("demo-image", "case-cancel") as sandbox:
            print("inside", sandbox["open"])
            entered.set()
            await asyncio.sleep(3600)
            print("work resumed")

    task = asyncio.create_task(work())
    await entered.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled after cleanup")


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

实际输出：

```text
boot demo-image case-cancel
inside True
closing case-cancel
closed case-cancel
cancelled after cleanup
```

## 3. await task：等的是使用任务及其退出清理

从上往下看执行顺序，`L` 对应上方代码行号；等待和交接位置已标在图中。

<div class="async-context-lanes" id="async-context-cancel-swimlanes">

```text
# L = example.py 行号；从上往下读，每行只在一列执行。
# MAIN 与 WORK 是两个 Task；resource 是 WORK 内的 boot_agent_sandbox。
# WAIT = 等待；RESUME = 恢复；YIELD = 交出资源；END = 任务结束。
# +------+-------------------------------+-----------------------------------+-----------------------------+
# | STEP | MAIN (exercise)               | WORK (work / resource)            | OUTPUT                      |
# +------+-------------------------------+-----------------------------------+-----------------------------+
# | T01  | L29 create; L30 WAIT(entered) |                                   |                             |
# | T02  |                               | work L23 ENTER -> T03             |                             |
# | T03  |                               | resource L7 print; L8 WAIT(loop)  | boot demo-image case-cancel |
# | T04  |                               | resource L8 RESUME; L9-10 prepare |                             |
# | T05  |                               | resource L11 YIELD -> T06         |                             |
# | T06  |                               | work L23-25 use; set entered      | inside True                 |
# | T07  |                               | work L26 WAIT(sleep)              |                             |
# | T08  | L30 RESUME; L31 cancel        |                                   |                             |
# | T09  | L32-33 WAIT(task)             |                                   |                             |
# | T10  |                               | work L26 CancelledError           |                             |
# | T11  |                               | work L23 EXIT -> T12              |                             |
# | T12  |                               | resource L11 error; L13 print     | closing case-cancel         |
# | T13  |                               | resource L14 WAIT(loop)           |                             |
# | T14  |                               | resource L14 RESUME; L15-16 close | closed case-cancel          |
# | T15  |                               | work L23 cancelled; END           |                             |
# | T16  | L33 raises; L34-35 except     |                                   | cancelled after cleanup     |
# +------+-------------------------------+-----------------------------------+-----------------------------+
# T01: MAIN 在 L30 等进入通知；T06 发通知，MAIN 到 T08 才恢复。
# T06-T07: set 只发通知；WORK 继续到 L26 等待，随后才轮到 MAIN。
# T08-T10: 本次先请求取消，MAIN 在 L33 让出执行，WORK 随后处理取消。
# T12: L11 收到同一个 CancelledError，进入 finally；T13 等关闭。
# T09-T16: MAIN 一直等 WORK；资源关闭、WORK 结束后，才确认取消。
```

</div>

[下载注释泳道图 execution-flow.py](execution-flow.py)。

entered 保证取消发生在已经取得沙箱之后；长 sleep 只是给使用区安排一个可取消的等待，本例不真的等满 3600 秒。

因此，task.cancel() 是取消请求；exercise 后面的 await task 还会等待 work 的退出。**work 的退出包括这一次 finally 中的异步关闭。**

这里验证一次取消的路径。清理代码自身报错或再次被取消，仍需另行处理；finally 提供清理机会，不能代替正确的关闭实现。

## 4. Task.cancel / finally：本节只带走两件事

1. 已进入的使用区收到取消时，本例会恢复 finally，先完成关闭。
2. 等待被取消的 task，也在等待它的资源退出；本例 closed 先于取消确认。

自查：为什么不能把 task.cancel() 返回理解成“沙箱已经关闭”？

<details><summary>查看解释</summary>

cancel 只是请求取消。work 还要处理取消、进入 finally，并等待关闭。调用方通过 await task 等它走完这条路径。

</details>

第 21 单元到这里结束。接下来第 22 课只增加一个新关系：同一个异步生成器怎样逐项产出多个值。

---

[上一节：21.5 · finally：使用区报错后怎样关闭](../21-context-errors/) · [下一节：22 · async for / 异步生成器](../22-async-iteration/) · [返回学习路线](../learning-route/)
