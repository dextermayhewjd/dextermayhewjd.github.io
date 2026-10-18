---
title: "35.1 · Future.done() / result() / exception()：复习结果读取与取消"
description: "复习 asyncio Future 的检查、等待与读取，补齐取消状态并对照 AsyncPacer。"
weight: 351
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> [20.5](../20-future-state/)已经正式讲过 Future 的状态与读取；[第 34 课](../34-wrap-future/)把线程池结果接回协程。
>
> **本节是复习与应用：** 用已学的 gather 返回值检验这些规则，并保留源码中的完成检查入口。需要重新建立基础时，回看 [20.3–20.5](../20-future-result/)；已经理解时，可以读完状态表后继续完成回调。

## 1. Future.done / result / exception：复习四种状态

<span id="asyncio-future-results"></span>

| Future 的情况 | done() | result() | exception() | await future |
| --- | --- | --- | --- | --- |
| 尚未完成 | False | 抛 InvalidStateError | 抛 InvalidStateError | 等待完成 |
| 成功完成 | True | 返回结果 | 返回 None | 返回结果 |
| 失败完成 | True | 抛保存的异常 | 返回异常对象 | 抛保存的异常 |
| 已取消 | True | 抛 CancelledError | 抛 CancelledError | 抛 CancelledError |

`done()` 为 True 只表示结束；`result()`、`exception()` 不等待。第 31 课的执行器 Future 不同：它的 `result()` 可以阻塞调用线程。

## 2. gather：把已学规则用于另一个 Future

这次不手动创建 Future，沿用第 06 课的 gather 取得它。任务返回 7，gather 的结果是列表 `[7]`；只改变 Future 的来源，读取规则不变。

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

默认调度下，当前协程到 `await future` 才让出执行机会，所以先观察到未完成，再等到结果。后面的 `result()` 读取同一次工作的结果，不会重新执行任务。

自查：把第一次 `result()` 改为 `exception()`，为什么仍然报 `InvalidStateError`？因为它们都只读取已有的完成结果，不负责等待。

{{< python-async-slime title="按需阅读：源码对照与适用范围" >}}

主例子是独立标准库实验。Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 AsyncPacer 也先检查 Future 是否已经完成：

{{< source-reference id="source-1" >}}

这里复习 done() 的检查作用；set_result 复用第 20 单元，分批调度沿源码主线继续展开。

{{< python-async-coverage lesson="35-future-results" >}}

依据：[Python 3.12：asyncio Future](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.Future)、[gather](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.gather)。主例子在 Python 3.12.3 默认调度方式下运行，适用本教程 Python 3.11 及以上版本。

{{< /python-async-slime >}}


---

[回顾基础：20.5 · 状态与异常](../20-future-state/) · [下一节：35.2 · 复习结果交付](../35-future-completion/) · [学习路线](../learning-route/)
