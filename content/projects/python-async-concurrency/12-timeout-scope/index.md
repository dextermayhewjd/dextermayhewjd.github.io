---
title: "15 · asyncio.timeout：给一段异步代码共享时间预算"
description: "用同一个超时作用域管理多个 await，分清共享预算、当前任务取消和块外异常处理。"
weight: 150
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 已经会算剩余时间，多个 await 怎样共用一份预算？

1. **前面已经会了：** 第 13 课用 `wait_for` 限制一次等待；第 14 课用固定截止读数减去当前读数，算出下一次等待还能用多少时间。
2. **现在要管理一段连续工作：** 里面有多个 `await`，希望它们合计使用同一份预算，不在每一步重新获得完整时限。
3. **先看旧办法：** 每次都写 `wait_for(..., timeout=0.3)`，得到的是每次各有 `0.3` 秒。沿用第 14 课，在每一步计算 `remaining` 再传给 `wait_for`，也能共享预算，但需要调用方持续组织这些计算。

这一课把预算管理放在一个明确的代码块上：**进入这段工作、执行多个等待、退出时处理超时。** 新增的接口是 `asyncio.timeout`，写法是 `async with asyncio.timeout(...)`。先确认第 04 课的 [with / async with：进入、执行与退出](../04-with-async-with/#async-with-basics) 已经理解；这次只看这套结构如何用于超时作用域。

## 2. asyncio.timeout：用一份预算包住两次等待

仍然使用 `generate` 和 `asyncio.sleep` 模拟工作。两次调用依次等待 `0.2` 秒，但整个代码块只有 `0.3` 秒预算。

先预测：第二次调用开始时，会重新得到完整的 `0.3` 秒吗？`finished 20`、`cleanup 20` 和 `both finished`，哪些能出现？

```python
import asyncio


async def generate(rollout_id, seconds):
    print("start", rollout_id)
    try:
        await asyncio.sleep(seconds)
        print("finished", rollout_id)
        return rollout_id
    finally:
        print("cleanup", rollout_id)


async def exercise():
    try:
        async with asyncio.timeout(0.3):
            await generate(10, 0.2)
            await generate(20, 0.2)
            print("both finished")
    except TimeoutError:
        print("shared budget expired")

    print("outside timeout block")


if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载 example.py](example.py) · 运行：`python3 -W error example.py`。本课使用 Python 3.12；`asyncio.timeout` 从 Python 3.11 开始提供。

本机 Python 3.12.3 的一次实际输出：

```text
start 10
finished 10
cleanup 10
start 20
cleanup 20
shared budget expired
outside timeout block
```

这里用等待时长制造“第一步能完成、第二步会耗尽总预算”的条件，不靠日志小数判断调度。系统负载会影响实际经过时间；后文的 `0.2`、`0.1` 是帮助理解预算的近似值。

<span id="shared-timeout"></span>

## 3. async with + timeout：进入一次，多个 await 共用截止边界

### 3.1 执行到 async with 时建立什么？

```python
async with asyncio.timeout(0.3):
```

`asyncio.timeout(0.3)` 返回一个异步上下文管理器。这里可以先把它理解为**负责进入和退出超时作用域的对象**，不必先展开协议方法。

在本例这行表达式中，调用 `timeout(0.3)` 时确定相对当前时刻的截止读数，随后 `async with` 进入作用域、安排超时处理。后面的等待共用这个截止边界。它不是每执行一行，就重新计算“从现在开始还有 `0.3` 秒”。

### 3.2 两次 await 仍然依次执行

1. `await generate(10, 0.2)` 先进入第一份工作。它正常返回前执行 `finally`，所以先看到 `finished 10`，再看到 `cleanup 10`。
2. 第一份工作返回后，才调用并等待 `generate(20, 0.2)`。此时第一步已经消耗了约 `0.2` 秒，总预算只剩约 `0.1` 秒。
3. 第二份工作等待时，共享预算到期，等待被取消中断。本次运行中它没有到达 `finished 20`，但仍会执行已经进入的 `finally`。

**`async with` 不会让块里的两行 `await` 自动并发。** 本例没有调用 `create_task`，两次 `generate` 都是在运行 `exercise` 的同一个 Task 中依次执行。

<span id="timeout-exit"></span>

## 4. TimeoutError：为什么在 async with 外捕获？

### 4.1 先处理取消，再退出超时作用域

沿主例子的超时路径看：

1. `timeout` 到期，向**当前正在运行这段代码的 Task** 发出取消请求。
2. 第二次 `generate` 正在 `await asyncio.sleep(...)`，因此在等待处接收到 `CancelledError`，跳过后面的 `finished 20`。
3. `generate` 的 `finally` 先执行，输出 `cleanup 20`，随后取消继续向外传播；`both finished` 也因此被跳过。
4. 退出 `async with` 时，超时上下文管理器把**这次自身超时引起的取消**转换为 `TimeoutError`。
5. 块外的 `except TimeoutError` 处理它，之后仍可执行 `outside timeout block`。

不是任意来源的取消都会被转换成超时。也不要在内部吞掉 `CancelledError`，否则会破坏这里依赖的取消传播。

### 4.2 try 包住整个 async with

主例子的结构是：

```python
try:
    async with asyncio.timeout(0.3):
        await generate(10, 0.2)
        await generate(20, 0.2)
except TimeoutError:
    print("shared budget expired")
```

外面的 `try` 覆盖了进入、执行和退出这整个作用域。由 `timeout` 自身产生的 `TimeoutError` 在退出时才形成，所以要在 `async with` 外捕获，不能把捕获它的 `try/except` 全部塞进块内。

内部调用也可能自己抛出其他异常，甚至业务自己的 `TimeoutError`；那是异常的另一个来源。本课的 `generate` 只等待并返回，输出中的超时来自这个预算作用域。

<span id="individual-budgets"></span>

## 5. wait_for 与 timeout：每次各有时限，还是整段共享时限？

保持 `generate` 函数和两次 `0.2` 秒等待不变，只把主例子的共享预算块替换成：

```python
await asyncio.wait_for(generate(10, 0.2), timeout=0.3)
await asyncio.wait_for(generate(20, 0.2), timeout=0.3)
print("both finished")
```

[下载完整对照 individual.py](individual.py)。本机运行时，两次工作都完成了：

```text
start 10
finished 10
cleanup 10
start 20
finished 20
cleanup 20
both finished
outside timeout block
```

| 写法 | 给谁分配预算 | 第二步开始时 |
| --- | --- | --- |
| 两次独立 `wait_for(..., timeout=0.3)` | 每次等待各有 `0.3` 秒 | 得到新的一份 `0.3` 秒 |
| 一个 `async with timeout(0.3)` 包住两次等待 | 整个作用域共用 `0.3` 秒 | 继续使用第一步之后的剩余预算 |

这不是说 `wait_for` 无法限制整个过程：第 14 课的手动 `remaining` 方案可以；把两步组织到一个协程中，再对整个协程使用一次 `wait_for`，也可以。`timeout` 让调用方直接用代码块表达共享边界。

### 5.1 timeout 也不承诺在截止瞬间强制结束

本例的 `finally` 只是打印。如果清理还包含等待，实际退出作用域的时间可能超过设定预算，这一点延续第 10–12 课。

超时依赖事件循环取得执行机会和任务响应取消，不能抢占一段占住线程的同步代码。它取消的是当前 Task，也不会按代码缩进自动找出并回收所有单独创建的后台 Task。本例使用直接 `await`，先把同一个 Task 中的取消路径看清楚。

## 6. 带走三条结论，再做自查

1. **`asyncio.timeout` 为一个作用域建立共享预算。** 多个 `await` 不会各自重置时限，也不会因为放进 `async with` 就自动并发。
2. **超时先取消当前 Task，再沿等待传播并执行清理。** 主例子的 `cleanup 20` 先于块外的超时报告。
3. **由这个作用域产生的 `TimeoutError` 在块外捕获。** `try` 包住整个 `async with`，处理后可以继续执行外部代码。

试着回答：

1. 为什么主例子没有 `finished 20`，却有 `cleanup 20`？
2. 把 `0.3` 改成足够长的预算，例如 `1` 秒，正常情况下会多出哪两行？
3. 两次独立 `wait_for(..., timeout=0.3)` 是否等于整个过程最多使用 `0.3` 秒？
4. 为什么捕获这个预算超时的 `except TimeoutError` 要写在 `async with` 外？

<details>
<summary>查看自查解释</summary>

1. 第二次等待被取消打断，正常路径上的打印被跳过，已经进入的 `finally` 仍然执行。
2. 会看到 `finished 20` 和 `both finished`，不再出现 `shared budget expired`。清理和块外打印仍会执行。
3. 不等于。每次各有自己的时限；共享总预算需要明确组织。
4. `timeout` 自身把取消转换为 `TimeoutError` 的动作发生在退出作用域时，块外的捕获才能接住它。

</details>

下一单元新增的问题是：**如果取消了等待者，但某份内部工作需要继续，怎样保留它，又由谁负责等完？** 见[第 16 单元：asyncio.shield](../13-shield/)。

{{< python-async-slime title="按需阅读：Slime 应用与本节源码位置" >}}

## generate：让准备、执行和评估共享外层预算

主例子是独立标准库实验，沿用 `generate` 这个名字来观察等待。下面才是固定 Slime 快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的原代码，位于 `examples/coding_agent_rl/`，不是核心包高频调用的证明。

这里进入真实 `generate` 的执行阶段：此前已经准备样本信息并打开 adapter session；接下来需要准备工作区、运行 agent、收集结果并评估。本节只看这些等待怎样共用外层 `rollout_guard_sec`，不展开 sandbox、agent 或评估器的实现。

{{< source-reference id="source-1" >}}

`prepare_workspace`、agent 的 `run`、`git_diff` 和 `run_evaluation` 都在同一个外层超时作用域内。内层 sandbox 的作用域结束后，评估仍然使用这份外层预算；块的缩进决定这里的管理范围。

## except / finally：退出超时块以后报告并收尾

下段位于同一函数的末尾，中间正常路径省略，仅通过两个连续源码摘录分开展示：

{{< source-reference id="source-2" >}}

这里的 `except asyncio.TimeoutError` 位于超时块外；在本课的 Python 3.12 中，它是内置 `TimeoutError` 的别名。最外层 `finally` 继续清理 session，所以外层预算到期也不表示整个函数已在那一刻返回。实际业务有自己的结果和清理规则，不能把标准库实验的打印当成项目的完整行为。

{{< python-async-coverage lesson="12-timeout-scope" >}}

## 版本与语义核对

按 [Python 3.12 的 asyncio.timeout 文档](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.timeout)和本机 CPython 3.12.3 的实现核对：超时作用于当前 Task，由上下文管理器在退出时转换自身超时引起的取消。实验未吞掉取消，也没有另建需要独立收尾的后台任务。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：14 · time.monotonic / time.perf_counter：计量经过时间与预算](../11-time-budget/) · [下一节：16 · asyncio.shield：区分取消等待者与内部工作](../13-shield/) · [完整学习路线](../learning-route/)
