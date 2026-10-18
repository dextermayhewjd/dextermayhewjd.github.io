---
title: "34 · asyncio.wrap_future：等待已有的执行器 Future"
description: "工作已经通过 submit 提交，怎样让协程等待它，而不重新提交一次？"
weight: 340
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [31.1](../31-threadpool-submit/)用 `reader.submit(...)` 提交工作，拿到执行器 Future；[33.2](../33-run-in-executor/)用 `run_in_executor(...)` 提交工作，并用 `await` 等待它返回的 asyncio Future。
>
> **本节新增的需求：** 工作已经由别处通过 `submit()` 提交，现在协程需要取得这次工作的结果，同时让事件循环能够继续调度其他协程。
>
> **本节的解决方式：** 用 `asyncio.wrap_future(...)` 把已有的执行器 Future 接成可 await 的 asyncio Future，再等待同一次工作的结果。

<span id="wrap-future"></span>

## 1. Future：先分清提交之后拿到的对象

仍然使用 `get_samples(3)` 取得样本列表。区别在于：**本节开始等待之前，工作就已经提交了。**

下面这两种对象都叫 Future，等待方式却不同：

<div class="async-api-reference">

| 从哪里得到 | 怎样取得结果 |
| --- | --- |
| `reader.submit(...)` 返回的 `concurrent.futures.Future` | 第 31 课用 `result()` 等待；未完成时会阻塞调用线程，不能直接 await |
| `loop.run_in_executor(...)` 返回的 `asyncio.Future` | 第 33 课用 await；未完成时挂起当前协程，让事件循环继续工作 |

</div>

如果直接写 `await executor_future`，会得到 TypeError，因为这里的执行器 Future 不支持 await。`wrap_future` 解决的就是这个接入问题。

本节只学习这两类对象怎样交接。读取状态、手动写入结果与注册回调仍按后续小节分别学习。

## 2. asyncio.wrap_future / await：接回已经提交的工作

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

本例继续保留 `get_samples`、`get_samples_async` 和 `reader`。提交动作放在入口，因此 `get_samples_async` 现在接收的是**已有的 executor_future**，不再接收线程池与取样本参数。

<div class="async-coordination-code">

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples):
    print("get_samples called")  # 只有工作线程实际执行函数时，才打印这一行。
    return list(range(num_samples))


async def get_samples_async(executor_future):
    # 已经提交过的工作：只包装它的 Future，不重新执行 get_samples。
    future = asyncio.wrap_future(executor_future)
    # 结果未就绪时挂起当前协程；就绪后取得同一次工作的列表。
    samples = await future
    print("samples", samples)
    return samples


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=1) as reader:
        # 沿用第 31 课：在这里提交一次，得到 concurrent.futures.Future。
        executor_future = reader.submit(get_samples, 3)
        # 把已经拿到的 Future 传入协程，由协程接回结果。
        asyncio.run(get_samples_async(executor_future))
    print("pool closed")
```

</div>

实际输出：

```text
get_samples called
samples [0, 1, 2]
pool closed
```

`get_samples called` 只出现一次：提交、包装和等待并没有让函数执行三次。

## 3. submit / wrap_future / await：三个动作，对应同一次工作

1. **submit 提交工作。** 工作线程从这次提交后就可以开始执行 `get_samples`，返回的 `executor_future` 代表这次工作的结果。
2. **wrap_future 接上协程等待。** 它接收 `executor_future`，返回另一个可 await 的 `future`；原来的 Future 仍然存在，没有被原地改成另一种类型。
3. **await 取得结果。** 工作完成后，结果传到 asyncio Future，等待者取得列表；如果结果尚未就绪，当前协程先挂起。

对象关系可以这样读：

```text
# reader.submit(get_samples, 3)    # 只在这里提交一次
#              |
#              v
#       executor_future           # concurrent.futures.Future
#              |
#    asyncio.wrap_future(...)
#              |
#              v
#           future                # asyncio.Future
#              |
#         await future
#              |
#              v
#           samples               # [0, 1, 2]
```

两个 Future 关联的是**同一次工作**。函数可能在进入协程之前就已完成，也可能仍在运行；两种情况都可以包装。已经结束的工作不会因为被包装而重跑。

本例在正在运行的协程中调用 `wrap_future`，它使用当前事件循环。包装本身不创建线程池，也不安排第二份 `get_samples`。

## 4. run_in_executor / wrap_future：根据是否已经提交来选择

<div class="async-api-reference">

| 现在手上有什么 | 对应操作 |
| --- | --- |
| 函数和参数，还没有提交工作 | 沿用 33.2：`loop.run_in_executor(reader, get_samples, 3)` 提交并返回 asyncio Future |
| 已经通过 submit 拿到执行器 Future | 本节：`asyncio.wrap_future(executor_future)` 接回已有工作 |

</div>

如果先 `submit(get_samples, 3)`，又调用一次 `run_in_executor(reader, get_samples, 3)`，那是提交了两次调用，不能用第二次调用来代替对第一次结果的等待。

## 5. asyncio.wrap_future：带走三条结论

1. 执行器 Future 与 asyncio Future 是两类对象，前者不能直接 await。
2. `wrap_future` 接回已经提交的工作，不重新提交或执行函数。
3. 两个 Future 关联同一次结果；协程通过 await 取得值，函数失败时也会在 await 处收到异常。

自查：工作在包装前已经完成，还能调用 `wrap_future` 吗？主例子中的 `get_samples` 一共执行几次？

<details><summary>查看解释</summary>

可以，包装也能接回已经完成的结果。主例子只在 submit 处提交一次，因此函数执行一次；包装和 await 都不会重新执行它。

</details>

## 6. asyncio.wrap_future：本节接口速查

<div class="async-api-reference">

| 调用或动作 | 作用 |
| --- | --- |
| `asyncio.wrap_future(executor_future)` | 把执行器 Future 接为当前循环中的 asyncio Future |
| `await future` | 结果未就绪时挂起当前协程，结果就绪后取得值或收到异常 |

</div>

{{< python-async-slime title="按需阅读：源码对照与适用范围" >}}

主例子是沿用第 31、33 课名称的独立标准库实验，没有复现 Slime 的业务流程。

Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 中，下面的 `next` 方法也先取得一个执行器 Future，再用 wrap_future 等待它。本段的 Future 来自跨线程协程提交，这部分留到第 36 课；现在只看“已有 Future → 包装 → await”这条关系。

{{< source-reference id="source-1" >}}

{{< python-async-coverage lesson="34-wrap-future" >}}

标准库依据：[Python 3.12：asyncio.wrap_future](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.wrap_future)。主例子在 Python 3.12.3 运行，使用 Python 3.11 及以上版本。

{{< /python-async-slime >}}

---

[复习结果读取：35.1 · asyncio Future](../35-future-results/)

[上一节：33.4 · loop.time](../33-loop-time/) · [下一重点：25 · inspect：辨认函数与可等待对象](../25-inspect-awaitable/) · [重点续学路线](../learning-route/#priority-reading)
