---
title: "07 · 取消与超时：请求停止以后，还要等待收尾"
description: "理解 cancel、CancelledError、finally 和任务级超时。"
weight: 70
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="task-cancellation"></span>

## cancel() 之后，任务就消失了吗

取消是一个请求。任务获得执行机会时，会在相应位置收到 `CancelledError`；清理逻辑仍需要运行。等待任务退出，才能知道收尾走完。

```python
import asyncio

async def generate(rollout_id):
    try:
        await asyncio.sleep(60)
        return rollout_id
    finally:
        print("cleanup", rollout_id)

async def exercise():
    task = asyncio.create_task(generate(10))
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled")
    try:
        async with asyncio.timeout(0.01):
            await asyncio.sleep(60)
    except TimeoutError:
        print("timeout")

if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
cleanup 10
cancelled
timeout
```

示例先让任务进入等待，再请求取消。`finally` 中的 `cleanup` 先出现，等待者随后捕获取消。第二段的 `asyncio.timeout` 为一个代码块设定超时，在块外捕获 `TimeoutError`。本实验要求 Python 3.11 及以上。

<span id="timeouts-and-shield"></span>

## 三种“等到时间”的区别

| 写法 | 到时发生什么 |
| --- | --- |
| `wait(tasks, timeout=t)` | 返回 done/pending，pending 不会自动取消 |
| `wait_for(awaitable, timeout=t)` | 通常取消等待对象，并等待取消处理；实际耗时可超过 t |
| `async with asyncio.timeout(t)` | 用当前任务的取消机制限制一个代码块，在作用域外表现为 TimeoutError |

清理后一般继续传播 `CancelledError`。把它吞掉并返回正常结果，会让上层误判任务成功。`shield` 保护等待对象免受这一层取消传播，但外层等待者仍然可以被取消；它不是“全程不可能取消”。

### shield 保护谁，取消后谁来收尾

把 `await pending` 换成 `await asyncio.shield(pending)`，改变的是这一层等待的取消传播：调用方被取消时，仍会收到 `CancelledError`，但这次取消不会通过 shield 顺带取消里面的 pending。pending 仍可能被其他代码直接取消，所以这不代表它永远不会停止。


| 阶段 | 调用方 | pending |
| --- | --- | --- |
| 正常等待 | 在 `await shield(pending)` 处挂起 | 可以继续推进 |
| 调用方收到取消 | 进入 `except CancelledError` | 不被这一层取消顺带取消 |
| 收尾 | 继续等待并检查结果 | 完成或报告自己的错误 |
| 返回上层 | 传播取消或实际工作错误 | 不留下无人负责的已接受工作 |


`asyncio.TimeoutError` 在 Python 3.11 以后是内置 `TimeoutError` 的别名，源码两种拼法表达同一异常类型；本教程使用 Python 3.11 及以上。`wait(timeout=...)`、`wait_for(...)` 和 `timeout(...)` 的差别仍要看上表，不能只看异常名字。

<details><summary>复述检查</summary>

`cancel()` 发出请求；`await task` 或清理用的 `gather` 等待请求被处理。超时预算还可能包含清理时间，不是强行停止线程或外部进程的按钮。

</details>

语义核对：[任务取消](https://docs.python.org/3.12/library/asyncio-task.html#task-cancellation)、[超时](https://docs.python.org/3.12/library/asyncio-task.html#timeouts)。

{{< python-async-slime >}}

## Slime 为什么取消之后还 gather

`_GenerationActor._next()` 同时等待取数任务和生产者。无论结果、异常或取消从哪里返回，`finally` 都取消不再需要的取数任务，再等待它收尾，避免它以后取走不属于本次请求的数据。

<details>
<summary>展开 Slime 源码：_GenerationActor._next</summary>

{{< source-reference id="source-1" >}}

</details>

<details>
<summary>展开 Slime 源码：generate</summary>

{{< source-reference id="source-2" >}}

</details>

Slime 的 `run_rollout_io()` 保留 pending 的引用。调用方取消之后，它继续等已经接受的工作完成，再取结果、释放许可，最后重新抛出取消。这里取消的是“我在等待”，不是“已接受的工作已经安全回收”。线程里究竟做什么，第 10 节再展开。

<details>
<summary>展开 Slime 源码：取消之后继续等待已接受的工作</summary>

{{< source-reference id="source-3" >}}

</details>

{{< python-async-coverage lesson="05-cancellation" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../04-results/) · [下一节：08 · Semaphore：限制同时进入的工作数量](../06-semaphore/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
