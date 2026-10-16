---
title: "33.4 · loop.time：用事件循环时钟计算剩余预算"
description: "取得当前事件循环后，怎样用同一套时钟读数建立截止位置并计算剩余时间？"
weight: 334
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 14 课](../11-time-budget/#remaining-budget)已经用固定截止读数计算剩余预算；[33.1](../33-current-loop/)学会取得正在运行的 `loop`。
>
> **本节新增的需求：** 在使用当前事件循环的代码中，继续计算一段工作的总时间预算，以及后续步骤还剩多少时间。
>
> **本节的解决方式：** 用 `loop.time()` 读取时间，起点加预算得到固定的 `deadline`，再用 `deadline` 减去当前读数得到 `remaining`。

第 14 课的方法已经能计算时间预算；本节只补充怎样从 `loop` 取得时钟读数，继续沿用“截止读数 − 当前读数 = 剩余预算”的计算关系。

<span id="loop-time-budget"></span>

## 1. loop.time：读循环的时钟，不是读日期

`loop.time()` 返回当前事件循环的**单调时钟读数，单位是秒，类型是 float**。单调表示后一次读数不会比前一次更小，但两次也可能相同。

它不是日期或 Unix 时间戳。单独看到 `100.0` 没有“几点钟”的含义；同一个时钟上两次读数的差才表示经过多久。

计算方式沿用第 14 课，只是这次统一从 `loop` 取时间：

<div class="async-api-reference">

| 计算 | 含义 |
| --- | --- |
| `deadline = loop.time() + 1.0` | 只确定一次：从现在开始，一秒后截止 |
| `remaining = deadline - loop.time()` | 再次检查时，还剩多少秒 |

</div>

**加预算确定截止读数，减当前读数得到剩余时间。** 不要把 `deadline` 本身当作“还剩多少秒”。

## 2. loop.time：沿一次等待计算剩余时间

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 沿用 33.1，取得当前事件循环。
    started = loop.time()  # 读取循环的单调时钟，单位为秒；不是日期时间。
    deadline = started + 1.0  # 只计算一次：从起点开始，共用一秒预算。
    print(f"[{started:.3f}s] start")
    print(f"[{deadline:.3f}s] deadline")

    await asyncio.sleep(0.02)  # 模拟前一步等待；实际经过时间由运行环境决定。

    now = loop.time()  # 等待后，再读同一个时钟。
    remaining = deadline - now  # 从原截止读数扣除当前读数，不重新给一秒。
    print(f"[{now:.3f}s] now")
    print(f"[{remaining:.3f}s] remaining")


if __name__ == "__main__":
    asyncio.run(exercise())  # 建立并运行事件循环，让 exercise 能读取 loop。
```

</div>

Python 3.12.3 的一次实际输出：

```text
[633209.846s] start
[633210.846s] deadline
[633209.866s] now
[0.980s] remaining
```

前三行方括号是时钟上的读数，最后一行是相减得到的时长，单位都为秒。读数与实际经过时间每次运行会变化；这里只显示三位小数，并不代表时钟精度恰好为一毫秒。

## 3. deadline / remaining：截止位置保持不变，剩余预算逐渐减少

沿输出看：

1. 起点约为 `633209.846`，给一秒预算，截止读数就是 `633210.846`。
2. 一次等待后，当前读数约为 `633209.866`。
3. 原截止读数减去当前读数，得到剩余约 `0.980` 秒。

如果后面还有第二步、第三步，仍然使用同一个 `deadline`。每一步重新写 `loop.time() + 1.0`，相当于不断重新给一秒，不再是共享总预算。

`remaining > 0` 表示还有时间，等于零表示到达截止位置，小于零表示已经超过截止位置。操作系统调度会影响实际等待时长，不能保证 `sleep(0.02)` 恰好只花 `0.02` 秒。

同一套预算从头到尾使用同一个循环的 `loop.time()`。不要把 `time.time()`、`time.perf_counter()` 的读数混进来相减；即使本机某些时钟的底层实现相同，也不能由此推广到其他事件循环。

## 4. loop.time：读到预算耗尽，不会自动停止任务

这是另一个独立实验：[下载 expired.py](expired.py)。为了稳定看到预算耗尽，故意把截止位置设为当前读数，即零秒预算。

<div class="async-coordination-code">

```python
import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 取得当前循环，继续使用同一个时钟。
    deadline = loop.time()  # 故意给零秒预算：截止位置就是现在。
    await asyncio.sleep(0)  # 让出一次执行机会；不会自动产生超时异常。
    remaining = deadline - loop.time()  # 现在已经到达或越过截止位置。
    print("budget expired", remaining <= 0)
    print("coroutine still running")  # 说明读时钟、算预算本身不会取消协程。
    if remaining <= 0:
        print("skip new work")  # 调用方根据预算作决定，不再开始下一份工作。
        return


if __name__ == "__main__":
    asyncio.run(exercise())  # 运行这个独立的零预算实验。
```

</div>

实际输出：

```text
budget expired True
coroutine still running
skip new work
```

第二行尤其关键：**时间已经用完，协程仍能继续。** `loop.time()` 只读时间，不发取消请求，也不抛超时异常；本例由 `if` 决定不再开始下一份工作。

如果要限制后面的等待，可以复用第 14 课：先检查 `remaining <= 0`，还有预算才把它传给 `asyncio.wait_for(..., timeout=remaining)`。如果要让一段代码共享超时控制，复用[第 15 课的 `asyncio.timeout`](../12-timeout-scope/)。本节只补齐时间从哪里来，不再展开那些取消过程。

## 5. loop.time：带走三条结论

1. `loop.time()` 返回循环的单调时钟读数，单位为秒；不是日期时间。
2. 一份总预算只确定一次截止读数，再用同一个时钟计算剩余时间。
3. 读时钟、算预算本身不会暂停或取消任务，必须由调用方决定后续行为。

自查：读数从 `100` 变为 `103`，最初给五秒，`deadline` 和 `remaining` 分别是多少？如果当前读数已经是 `106`，任务会自动停止吗？

<details><summary>查看解释</summary>

`deadline = 105`，`remaining = 2`。读数为 `106` 时剩余为 `-1`；预算耗尽，但不会仅因这次相减而自动停止任务。

</details>

## 6. loop.time：本课接口速查

<div class="async-api-reference">

| 调用或计算 | 返回什么，改变什么 |
| --- | --- |
| `loop.time()` | 返回 float 秒数；只读时钟，不等待、不改变任务状态 |
| `deadline - loop.time()` | 计算剩余秒数；负数说明已经超时 |

</div>

<details><summary>按需阅读：标准库依据</summary>

依据 [Python 3.12：loop.time](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.time)。例子已在 Python 3.12.3 运行，使用 Python 3.11 及以上版本。

CPython 3.12.3 的默认 `BaseEventLoop.time()` 调用 `time.monotonic()`。这是当前实现的依据；写代码时仍遵守“同一预算使用同一个时钟”的接口约定。

</details>

---

[上一节：33.3 · await / Event](../33-await-handoff/) · [下一重点：34 · asyncio.wrap_future](../34-wrap-future/) · [重点续学路线](../learning-route/#priority-reading)
