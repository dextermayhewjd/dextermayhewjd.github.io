---
title: "36.1 · new_event_loop / set_event_loop / run_until_complete / close：手动运行并关闭事件循环"
description: "一个协程，分清创建循环、关联线程、运行与关闭。"
weight: 361
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 01–02 课](../02-await/)用 asyncio.run() 运行协程；[33.1](../33-current-loop/)用 get_running_loop() 取得正在运行的循环；[第 09 课](../09-task-cancellation/)用 finally 做收尾。
>
> **本节新增的需求：** 源码自己保存一个 loop，并分别决定什么时候运行、什么时候关闭。怎样读清这几步？
>
> **本节的解决方式：** 把循环的创建、线程关联、运行和关闭拆开，先用一个协程走完一次。

## 1. new_event_loop / set_event_loop：创建和关联，都不等于运行

以前的 asyncio.run() 会管理循环的创建、运行与关闭。现在把这些步骤展开，看清每个接口负责什么。

<div class="async-api-reference">

| 操作 | 具体做什么 |
| --- | --- |
| asyncio.new_event_loop() | 创建一个循环对象，返回 loop |
| asyncio.set_event_loop(loop) | 将这个 loop 关联到当前线程，返回 None |
| loop.run_until_complete(协程对象) | 运行循环，直到这份工作完成，再返回结果或抛出异常 |
| loop.close() | 在循环停止运行后关闭它，释放资源，返回 None |

</div>

**前两步只是准备。调用 run_until_complete，循环才开始推进协程。** 这些操作都在当前线程里进行，不会自动创建工作线程。

## 2. run_until_complete：运行一个协程，再回到调用处

本例是独立的标准库实验。沿用返回 7 的 generate，只增加循环的四个步骤。

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio


async def generate():
    print("generate start")
    await asyncio.sleep(0)  # 暂停一次，再由正在运行的循环继续推进。
    return 7


if __name__ == "__main__":
    loop = asyncio.new_event_loop()  # 创建循环对象，此时还没有开始运行。
    asyncio.set_event_loop(loop)  # 把它关联到当前线程，也不会开始运行。
    try:
        print("before run")
        value = loop.run_until_complete(generate())  # 运行循环，等协程完成并取得 7。
        print("result", value)
    finally:
        asyncio.set_event_loop(None)  # 解除当前线程与循环的关联。
        loop.close()  # 循环已经停止运行，关闭它并释放资源。
        print("closed")
```

</div>

实际输出：

```text
before run
generate start
result 7
closed
```

按四步读：

1. **创建与关联。** 第 11–12 行准备 loop。此时 generate 还没有运行，所以先打印 before run。
2. **开始运行。** 第 15 行调用 generate() 得到协程对象，再交给 run_until_complete。这个方法在内部把协程安排为 Task，启动循环，才进入 generate 的函数体。
3. **完成并返回。** generate 在 sleep(0) 处暂停一次，由循环继续推进，最后返回 7。run_until_complete 结束这次运行，把 7 交给 value，再打印 result 7。
4. **收尾。** finally 中的 set_event_loop(None) 解除线程关联，close() 关闭循环，最后打印 closed。

**run_until_complete 返回之前，调用它的这条执行路线会一直等。** 运行期间，循环内部仍能在 await 处调度就绪任务；它不是把协程交给另一个线程运行。

本例从脚本的同步入口运行。已经在同一线程的运行中循环里时，应继续用 await，不要嵌套调用 run_until_complete。

## 3. close：停止运行以后，才关闭资源

<span id="manual-event-loop"></span>

run_until_complete 返回，表示这次循环运行已经停止，**不表示 loop 已关闭**。在调用 close 之前，可以再用它运行另一份工作；关闭以后就不能再使用。

set_event_loop(None) 和 close() 也做不同的事：前者解除线程关联，后者释放循环资源。只解除关联，不会替你关闭循环。

本例只有 generate 这一个任务，所以它完成后就可以收尾。**run_until_complete 只等待传入的那份工作，close 不会替你等完其他任务或执行它们的 finally。** 真实代码如果额外创建了任务，仍要先按前面的课程等待或取消并收尾。

这个例子用来认识循环生命周期。它没有用到线程池或异步生成器，不是 asyncio.run 完整清理过程的替代实现；普通脚本仍可以继续使用 asyncio.run。

## 4. run_forever / stop：读 Slime 时再认出这两个名字

Slime 有些循环需要持续接收工作，不会在一份协程完成后就停止。这时会看到：

<div class="async-api-reference">

| 操作 | 什么情况下返回 |
| --- | --- |
| loop.run_until_complete(工作) | 这份工作完成时，返回结果或抛出异常 |
| loop.run_forever() | 持续运行，直到请求停止；不以某一份任务完成为退出条件 |
| loop.stop() | 请求循环停止；运行中的本轮回调处理后退出循环运行 |

</div>

stop() 不等于 close()，也不等于取消全部任务。这里只先认清作用；下一节再看怎样从另一个线程把工作交给正在运行的循环。

## 5. 事件循环：带走三条结论

1. new_event_loop 创建循环，set_event_loop 关联线程；它们都不启动运行。
2. run_until_complete 驱动传入的工作，等它完成，再把结果交回调用处。
3. 循环停止运行以后才能 close；其他任务的收尾仍需明确安排。

自查：只执行 new_event_loop 和 set_event_loop，没有调用任何运行方法，协程会自动开始吗？run_until_complete 返回以后，loop 就已经关闭了吗？

<details><summary>查看解释</summary>

都不会。创建和关联不负责推进协程；run_until_complete 返回也只结束这次运行，关闭由后面的 close 完成。

</details>

{{< python-async-slime title="按需阅读：Slime 中的创建、运行与持续服务" >}}

以下来自 Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。本例只用一个协程认识原生接口，没有复现 HTTP 服务或后台线程。

{{< source-reference id="source-1" >}}

这里先创建 loop，再在线程的入口中关联并 run_forever。先只辨认循环的三个动作；线程间怎样交接协程，留到 36.2。

{{< source-reference id="source-2" >}}

这里两次 run_until_complete 分别等完服务准备和监听启动，再在后续代码中 run_forever 持续服务。一次运行结束，loop 仍可以用于下一次运行。主例子额外用 finally 展示关闭，不能把它当成这两个源码片段已经实现的清理行为。

{{< python-async-coverage lesson="36-manual-event-loop" >}}

依据：[Python 3.12：事件循环的运行、停止和关闭](https://docs.python.org/3.12/library/asyncio-eventloop.html#running-and-stopping-the-loop)、[设置当前线程的事件循环](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.set_event_loop)。主例子在 Python 3.12.3 下运行，适用本教程 Python 3.11 及以上版本。

{{< /python-async-slime >}}

---

[上一节：35.3 · Task 完成回调](../35-task-callbacks/) · [下一节：36.2 · 跨线程提交协程](../36-threadsafe-submit/) · [当前补课顺序](../learning-route/#priority-reading)
