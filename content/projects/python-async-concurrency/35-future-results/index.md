---
title: "35.1 · Future.done() / result() / exception()：读取 asyncio Future 的结果"
description: "一个最小例子，区分检查、等待和读取。"
weight: 351
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 06 课](../05-gather/)用 gather 收集结果；[第 08 课](../07-task-results/)读过 Task 的完成状态；[第 34 课](../34-wrap-future/)已经区分执行器 Future 与 asyncio Future。
>
> **本节新增的需求：** 手里已经有一个 asyncio Future，怎样判断它完成了没有，再读取结果？
>
> **本节的解决方式：** done() 检查，await 等待，result() 和 exception() 读取。

## 1. asyncio Future：先分清三个动作

<div class="async-api-reference">

| 动作 | 作用 |
| --- | --- |
| future.done() | 检查是否已经完成，不等待 |
| await future | 等它完成，取得结果；失败时抛出异常 |
| future.result() / exception() | 读取已有结果或异常，不等待 |

</div>

**本节只记住一个区别：读取，不等于等待。** asyncio Future 尚未完成时，result() 和 exception() 会立即抛出 InvalidStateError。

第 31 课的线程池 Future 不同：它的 result() 默认会阻塞等待。本节讨论的是 asyncio Future。

## 2. done / await / result：只看一个最小例子

这里沿用已经学过的 gather 取得 Future。内部任务运行到 sleep(0) 时让出一次执行机会，结束时返回 7；gather 将这一项收成列表 [7]。暂时不展开 Future 的手动创建。

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio


async def exercise():
    future = asyncio.gather(asyncio.sleep(0, result=7))  # 沿用 gather，得到 asyncio Future；结果为 [7]。
    print("before", future.done())  # False：内部任务还没有完成。
    try:
        future.result()  # 只读取，不等待；此时会抛 InvalidStateError。
    except asyncio.InvalidStateError:
        print("not ready")
    await future  # 等内部任务完成，再继续下面的读取。
    print("after", future.done())  # True：已经完成。
    print("result", future.result())  # [7]：直接读取已有结果。
    print("exception", future.exception())  # None：成功完成，没有异常。


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

实际输出：

```text
before False
not ready
after True
result [7]
exception None
```

按三个阶段读即可：

1. **await 之前：** 内部任务还没完成，done() 是 False，直接 result() 报错。
2. **执行 await：** 等内部任务完成；尚未就绪时，当前协程挂起。
3. **await 之后：** 本例成功完成，done() 是 True，result() 返回 [7]，exception() 返回 None。

这里按默认的 asyncio 调度方式运行。第 5 行安排内部任务后，当前协程到第 11 行 await 才让出执行权，因此前面的检查能看到未完成状态。result() 不会再次执行任务，最后读取的是同一次工作的结果。

## 3. result / exception：其他完成状态怎样读取？

<span id="asyncio-future-results"></span>

下面回接第 08、09 课的状态区别，不再增加一套失败实验。

<div class="async-api-reference">

| Future 的情况 | done() | result() | exception() |
| --- | --- | --- | --- |
| 尚未完成 | False | 抛 InvalidStateError | 抛 InvalidStateError |
| 成功完成 | True | 返回结果 | 返回 None |
| 失败完成 | True | 抛保存的异常 | 返回异常对象 |
| 已取消 | True | 抛 CancelledError | 抛 CancelledError |

</div>

**done() 为 True 只表示结束，不保证成功。** 失败时，result() 抛出异常，exception() 返回异常对象；这是两种不同的读取方式。

## 4. asyncio Future：带走三条结论

1. done() 只检查；await 负责等待。
2. result()、exception() 不等待，未完成时会报错。
3. 完成后可以直接读取，但要区分成功、失败和取消。

自查：主例子为什么先打印 not ready，后面却能打印 [7]？

<details><summary>查看解释</summary>

第一次 result() 发生在完成之前，它不会等待。后面的 await 等到完成后，再次 result() 就能读取已有的 [7]。

</details>

下一小节再说明：不借助 gather 或线程池，怎样手动创建一个 Future，由另一处提供结果？

{{< python-async-slime title="按需阅读：源码对照与适用范围" >}}

主例子是独立标准库实验。Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 AsyncPacer 也先检查 Future 是否已经完成：

{{< source-reference id="source-1" >}}

本节只看 done() 的检查作用。set_result 和分批调度随后再讲。

{{< python-async-coverage lesson="35-future-results" >}}

依据：[Python 3.12：asyncio Future](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.Future)、[gather](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.gather)。主例子在 Python 3.12.3 默认调度方式下运行，适用本教程 Python 3.11 及以上版本。

{{< /python-async-slime >}}

---

[前置回顾：34 · wrap_future](../34-wrap-future/) · [下一节：35.2 · 创建并完成 Future](../35-future-completion/) · [当前补课顺序](../learning-route/#priority-reading)
