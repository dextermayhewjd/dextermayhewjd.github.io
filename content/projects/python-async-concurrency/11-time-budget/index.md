---
title: "14 · time.monotonic / time.perf_counter：计量经过时间与预算"
description: "为上一课的等待与清理测量实际耗时，再从同一个截止读数计算剩余预算，分清观察与调度。"
weight: 140
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 已经知道清理可能超时，怎样测量实际经过的时间？

1. **上一课已经会了：** 用 `wait_for` 限制一次等待；时限到达后，还要给任务处理取消和清理的机会。
2. **现在多了一个要求：** 实际等了多久？如果前面已经用掉一部分时间，下一步还剩多少预算？
3. **先看原来的办法：** `timeout=0.1` 表达设定的时限，不能直接当作实际耗时；只看打印先后，也得不到两次事件之间相隔多久。

这次新增两个读时钟的接口：**`time.perf_counter()`** 用来测量短时间间隔，**`time.monotonic()`** 用来计算经过时间和截止预算。它们返回以秒为单位的浮点数；本课用“同一时钟的两次读数相减”建立理解。

## 2. 沿用慢清理实验，只增加前后两次读数

保留第 13 课的等待时限 `0.1` 秒，以及 `finally` 中的 `0.2` 秒清理等待。任务安排好之后、开始 `wait_for` 之前记录一次，调用方收到超时后再记录一次。

先预测：`elapsed` 测到的只有 `0.1` 秒吗？清理等待会不会包含在里面？

```python
import asyncio
import time


async def generate(rollout_id, seconds):
    try:
        await asyncio.sleep(seconds)
        return rollout_id
    finally:
        print("cleanup start", rollout_id)
        await asyncio.sleep(0.2)
        print("cleanup finished", rollout_id)


async def exercise():
    task = asyncio.create_task(generate(10, 60))
    started = time.perf_counter()

    try:
        await asyncio.wait_for(task, timeout=0.1)
    except TimeoutError:
        elapsed = time.perf_counter() - started
        print(f"[{elapsed:.3f}s] timeout")


if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载 example.py](example.py) · 运行：`python3 -W error example.py`。本课使用 Python 3.12。

本机 Python 3.12.3 的一次运行输出如下，最后的具体数值会随运行环境变化：

```text
cleanup start 10
cleanup finished 10
[0.301s] timeout
```

这里测量的是**从开始这次等待，到调用方收到超时为止的时间**，包括任务等待、取消处理与清理。它不代表整个脚本的运行时间，也不只是 CPU 正在执行 Python 代码的时间。

<span id="elapsed-time"></span>

## 3. perf_counter：看前后差值，不把读数当日期

### 3.1 沿执行位置理解两次读数

1. `create_task` 安排任务；本例没有改变第 13 课的任务执行方式。
2. `started = time.perf_counter()` 记录等待之前的读数。这个调用本身没有 `await`，不会为了计时而把任务启动一遍。
3. `await wait_for(...)` 等待任务；超时后仍要等待本例的清理完成。
4. 进入 `except` 后再次读取同一个时钟，再减去 `started`，得到被这两个位置包围的时间间隔。

```python
elapsed = time.perf_counter() - started
```

`perf_counter()` 用高分辨率时钟测量时间间隔，计入睡眠和异步等待期间经过的时间。单独一个读数没有可供解释的日期起点；我们要比较的是差值。

### 3.2 数值怎样理解？

如果两次读数分别为 `100.0` 和 `100.3`，差值就是 `0.3` 秒。这里的 `100.0` 不是“程序从启动到现在运行了 100 秒”，也不是现实世界的某个时刻。

前面第 03、05、06 课日志中的 `[0.123s]`，也是 `time.perf_counter() - started_at` 得到的相对时间。代码中的 `:.3f` 表示保留三位小数；显示三位小数不代表测量精度恰好为一毫秒。

两次读数必须使用同一个时钟。不要用 `perf_counter()` 的结果减去 `monotonic()` 的结果，即使某个 Python 实现恰好让它们使用同一底层时钟。

<span id="remaining-budget"></span>

## 4. monotonic：从同一个截止读数扣掉已经过去的时间

### 4.1 先确定预算结束的位置

`time.monotonic()` 返回单调时钟的读数，不受系统时钟校准的影响，也不能当作日期使用。连续读数可以相等，但不会倒退。

如果从现在开始给整个过程 5 秒预算，先计算一次：

```python
deadline = time.monotonic() + 5
```

`deadline` 是同一时钟上的截止读数。假设当前读数为 `100`，就得到 `105`。

后续需要检查时，再计算：

```python
remaining = deadline - time.monotonic()
```

| 检查时的读数 | 剩余预算 | 含义 |
| --- | --- | --- |
| `102` | `3` 秒 | 还可以继续使用这一份预算 |
| `105` | `0` 秒 | 已经到达截止位置 |
| `106` | `-1` 秒 | 已经超过预算 |

**截止读数只确定一次，后续从它扣掉已经过去的时间。** 如果每一步都重新计算“现在加 5 秒”，就给每一步重置了预算。

### 4.2 把剩余预算交给已学的等待方式

[下载 budget.py](budget.py)。这个补充实验先给一份 `0.1` 秒预算，再用一次 `sleep(0.02)` 模拟准备工作；后续等待只使用剩余时间：

```python
remaining = deadline - time.monotonic()

try:
    if remaining <= 0:
        raise TimeoutError("budget expired")
    task = asyncio.create_task(generate(10, 60))
    await asyncio.wait_for(task, timeout=remaining)
except TimeoutError:
    print("budget expired")
```

本例的输出为：

```text
budget expired
```

1. 如果准备工作之后已经没有预算，直接报告超时，不再创建新任务。
2. 如果还有预算，把当时算出的 `remaining` 交给 `wait_for`，而不是再给一次完整的 `0.1` 秒。
3. 等待超时后，仍按第 13 课的规则处理取消与收尾。这个最小工作函数不持有需要额外清理的资源，所以没有专门增加 `finally`。

读时钟、检查和开始等待之间仍有执行间隔，任务清理也可能需要时间。这种预算计算不等于保证整个过程在某个瞬间强制结束；下一课再用 `asyncio.timeout` 管理一段代码共享的预算。

<span id="timing-is-observation"></span>

## 5. 时钟读数不会驱动任务，也不能单凭小数判断调度

| 本课接口 | 常见用途 | 读数本身不会做什么 |
| --- | --- | --- |
| `time.perf_counter()` | 记录两个位置之间的实际耗时 | 不会让出执行机会，也不会等待任务结束 |
| `time.monotonic()` | 计算截止读数与剩余预算 | 不会在预算用完时自动取消任务 |

这是本课采用的常见分工，不表示 `monotonic()` 不能用于测量时间间隔。无论使用哪个，都要让一组计算采用同一个时钟。

预算超时后采取什么行动，由调用方的判断以及 `wait_for` 等机制负责；时钟只提供读数。两条日志显示的时间很接近，也不能由此断言两段 Python 代码在同时执行。

要判断任务执行的先后，仍要结合 `create_task` 的安排位置、实际的 `await` 和输出事件。不要用“恰好相差一毫秒”来代替对控制流程的理解。

## 6. 带走三条结论，再做自查

1. **用同一时钟的前后差值测量经过时间。** 本例的 `elapsed` 包含超时后的清理，不把设定时限当成测量结果。
2. **用固定截止读数减去当前读数，得到剩余预算。** 检查 `remaining` 是否耗尽，再决定是否开始下一次等待。
3. **计时只是观察，不能替代等待和取消。** 读时钟不会调度任务；时间戳也不能单独证明并发执行顺序。

试着回答：

1. 主例子在清理完成后才计算差值，为什么结果可能超过 `0.1` 秒？
2. 单独打印 `time.perf_counter()` 得到 `100.0`，能否说程序已经运行了 100 秒？
3. `remaining` 变成负数时，任务会因为这次减法自动停止吗？
4. 能否用一次 `perf_counter()` 减去一次 `monotonic()` 来测量耗时？

<details>
<summary>查看自查解释</summary>

1. 两次读数包围了等待、取消处理与清理，实际耗时不止设定的等待时限。
2. 不能。它的日期起点没有这个含义；需要与同一时钟的另一次读数相减。
3. 不会。负数表示预算已耗尽，是否报告错误或取消工作，需要调用方采取行动。
4. 不应这样写。使用同一时钟的两次读数，避免依赖具体实现恰好共享底层时钟。

</details>

下一单元新增的问题是：**多个 `await` 怎样共享一段时间预算，而不用每一步都手动组织剩余时间？** 见[第 15 单元：asyncio.timeout](../12-timeout-scope/)。

{{< python-async-slime title="按需阅读：Slime 应用与本节源码位置" >}}

## 在关闭流程中保留同一个截止读数

主例子和预算实验是独立标准库实验。源码继续使用教程已核对的 Slime 快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。

这里进入 `DistributedRollout.close` 的等待阶段：此前已向 worker 发出关闭请求，持有待等待的 `refs`。本节只看它怎样为这些等待共享一份预算：

{{< source-reference id="source-1" >}}

1. `deadline` 在循环外用 `time.monotonic() + 300` 计算一次。
2. 每次等待前，再从同一个 `deadline` 减去当前读数。
3. `max(0, ...)` 把交给等待接口的负值截为零；具体零时限行为由该接口决定。

这里的 `ray.get` 是项目的等待接口，不是 `asyncio.wait_for`。本节只对应原生时钟计算，Ray 的调用与退出处理留在原项目阅读语境中。

<section id="source-usage-locations">
<h2>源码位置与扫描口径</h2>
<p>旧版 Slime 扫描清单没有将这两个时钟接口列入已识别的 API，所以自动位置统计为零；这不表示源码没有使用它们。上面的摘录是按固定文件内容与行号人工核对的实际用法。</p>
<p><a href="/python-async-concurrency/source_snapshot/slime/rollout/fully_async_distributed.py.txt">查看完整固定快照</a>：<code>DistributedRollout.close</code> 的 L583、L586 对应截止读数与剩余预算。</p>
</section>

## 版本与语义核对

时钟语义按 [Python 3.12 perf_counter](https://docs.python.org/3.12/library/time.html#time.perf_counter) 与 [monotonic](https://docs.python.org/3.12/library/time.html#time.monotonic) 文档核对；实验运行环境为 Python 3.12.3。这里没有把不同 Python 版本与平台的底层时钟实现当作必须记忆的知识。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：13 · asyncio.wait_for：限制一次等待的时长](../10-wait-for/) · [下一节：15 · asyncio.timeout：给一段异步代码共享时间预算](../12-timeout-scope/) · [完整学习路线](../learning-route/)
