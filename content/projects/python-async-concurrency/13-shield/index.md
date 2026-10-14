---
title: "16 · asyncio.shield：区分取消等待者与内部工作"
description: "外层等待超时，内部 Task 仍可继续；保留引用，继续负责等待完成并读取结果或错误。"
weight: 160
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 外层已经不等了，内部工作是否也要停止？

1. **前面已经会了：** 第 09 课知道取消需要传播和收尾，第 13 课限制一次等待，第 15 课让代码块共用预算。外层 Task 被取消时，如果正在直接 `await task`，取消通常也会传给这个被等待的 Task。
2. **现在要分开两件事：** 本次等待可以因超时结束，但某份已经安排的内部工作仍需要完成，并有人接着读取结果。
3. **先看原来的办法：** 单独 `create_task` 只把工作安排到另一份 Task 中；随后直接 `await task`，仍然建立了会传递取消的等待关系。仅仅创建独立 Task，并没有隔开这一层取消。

本课新增 **`asyncio.shield`**：在这一次等待中阻断外层取消向内部工作的传播。外层仍会收到取消；内部继续以后，也仍须有人持有并收尾。

主例子承接第 15 课，用 `timeout` 制造一次外层取消。我们保留同样的 `generate`、睡眠和清理打印，先把两份 Task 的身份看清楚。

这里的 `async with` 仍然用于第 15 课的超时作用域；新增的 `shield` 用在里面的 `await` 上。需要复习进入和退出结构时，返回第 04 课的 [with / async with 前置说明](../04-with-async-with/#async-with-basics)。

## 2. shield(task)：外层先超时，内部随后完成

内部工作等待 `0.2` 秒，这次外层等待的预算只有 `0.05` 秒。先预测：`waiter timed out`、`finished 10`、`cleanup 10` 和 `result 10`，本次运行会怎样排列？

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
    task = asyncio.create_task(generate(10, 0.2))
    try:
        async with asyncio.timeout(0.05):
            await asyncio.shield(task)
    except TimeoutError:
        print("waiter timed out")

    # 保留 task 引用，并在这次预算作用域之外负责等完、读取结果。
    print("result", await task)


if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载 example.py](example.py) · 运行：`python3 -W error example.py`。本课使用 Python 3.12。

本机 Python 3.12.3 的一次实际输出：

```text
start 10
waiter timed out
finished 10
cleanup 10
result 10
```

这次外层先报告等待超时，内部随后正常完成并清理，最后读到结果。这里用较短的外层预算触发取消，不把具体小数当作调度保证；系统负载会影响事件的实际时间。

<span id="shield-cancellation"></span>

## 3. asyncio.shield：隔开哪一层取消？

### 3.1 先辨认等待者与内部 Task

| 对象或写法 | 在主例子中的身份 |
| --- | --- |
| 运行 `exercise` 的 Task | 外层等待者；`timeout` 到期时取消它 |
| `task` | `create_task` 返回的内部 Task，运行 `generate` |
| `asyncio.shield(task)` | 提供这次等待的可等待对象，隔开向内部 Task 传递的取消 |

`shield(task)` 使用已有的内部 Task，不是再执行一份 `generate`。本课显式创建并保存 `task`，避免把内部工作的身份藏在一行调用里。

### 3.2 沿超时路径走一遍

1. 外层进入 `timeout(0.05)`，通过 `await shield(task)` 等待内部工作。
2. 预算到期，`timeout` 取消外层 Task；这一层 `await` 仍然接收到 `CancelledError`。
3. `shield` 阻止这次取消顺带取消内部 `task`。本次等待被打断，但内部工作仍可继续推进。
4. 退出超时作用域时，第 15 课的 `timeout` 把自身超时引起的取消转换成 `TimeoutError`，块外打印 `waiter timed out`。
5. 外层随后在作用域外 `await task`。内部正常返回前执行 `finally`，外层取得 `10` 并打印结果。

**`shield` 没有消除外层取消，也不负责把取消变成超时异常。** 本例的转换来自 `timeout`。如果其他代码直接取消外层等待者，`await shield(task)` 仍会抛出 `CancelledError`，需要按取消路径处理。

### 3.3 去掉 shield，会观察到什么？

保持内部函数、Task 创建方式和预算不变，把作用域里的等待换成：

```python
await task
```

[下载对照 unshielded.py](unshielded.py)。末尾继续等待时，专门捕获取消来辨认内部 Task 的结束状态；本机输出：

```text
start 10
cleanup 10
waiter timed out
inner task cancelled
```

这次外层取消通过直接等待传给了内部 Task：它跳过 `finished 10`，先执行清理，再结束为取消。随后再次 `await task` 得到的仍是这个取消结果，不会把它重新运行一遍。

| 本次等待方式 | 外层预算到期 | 内部工作在这次实验中的结果 |
| --- | --- | --- |
| `await task` | 取消传给直接等待的内部 Task | 清理后结束为取消 |
| `await shield(task)` | 外层等待被取消，向内部的传播被隔开 | 随后正常完成，读到结果 |

<span id="shield-ownership"></span>

## 4. await task：工作继续以后，谁负责等完和读取结果？

### 4.1 保留引用，等待不是重新启动

主例子从创建时就保留 `task`，在处理超时后继续等待它。这同时解决两个责任：**持有内部工作，读取它最终的结果或异常。** 不只调用一行 `shield` 就丢下它。

内部 Task 能继续，是因为这次外层取消没有传给它，事件循环仍能给它执行机会。**不是直到最后一行 `await task`，它才被重新启动。** 即使内部已经完成，这个 `await` 也只是取得现成结果。

最后一行位于 `timeout` 作用域之外，已经不受刚才那份 `0.05` 秒预算约束。所以外层报告这次等待超时，不等于整个 `exercise` 已经返回。

本例由同一个 `exercise` 完成后续收尾。实际代码若把责任交给其他管理者，也要明确谁持有 Task、谁等待结束、谁读取错误。`shield` 本身不建立这样的管理者。

### 4.2 内部失败时也要读到错误

`shield` 只改变取消传播，不把内部工作变成一定成功的工作。

[下载补充 failure.py](failure.py)：保留同样的外层预算，把内部正常返回改成等待后抛出已学的 `ValueError`，末尾等待时处理这个错误。实际输出：

```text
start 10
waiter timed out
cleanup 10
error generation 10 failed
```

外层超时和内部失败是两件事。本例的内部错误在后续 `await task` 时读到；如果内部在原来的等待结束前就失败，`await shield(task)` 也会传播它自己的异常。

<span id="shield-limits"></span>

## 5. Task.cancel 与 shield：保护的是这次传播，不是全部生命周期

1. **其他代码仍能直接取消内部 Task。** `task.cancel()` 不需要经过这层 `shield`；内部被取消时，等待它的 `shield` 也会体现为 `CancelledError`。
2. **换回直接等待，就恢复了直接等待的取消关系。** 主例子最后的 `await task` 没有 `shield`；如果此时又发生一次外层取消，它仍可能传给内部 Task。本例只制造一次预算取消，不把它当成处理反复取消的完整实现。
3. **事件循环收尾也有自己的取消。** 如果删去后续等待，马上让 `exercise` 返回，`asyncio.run` 关闭时会取消尚未完成的 Task；`shield` 不保证内部工作能在脚本结束之后继续。

因此，使用场景是：**确实需要把结束本次等待与结束内部工作分开，同时安排后续收尾责任。** 普通超时若本来就希望停止内部工作，前面已学的直接等待与取消路径即可表达这个要求。

## 6. 带走三条结论，再做自查

1. **`shield` 隔开这一次向内部工作的取消传播。** 外层仍会收到取消；本例由 `timeout` 在块外表现为超时。
2. **内部工作继续，不等于收尾责任消失。** 保留 Task 引用，等到完成，再读取结果或处理错误；`await` 不会重启它。
3. **保护有明确边界。** 直接取消内部 Task、后续新的直接等待和事件循环关闭，都不是一次 `shield` 能全部隔开的事情。

试着回答：

1. 主例子的 `TimeoutError` 是 `shield` 产生的吗？
2. 内部 Task 为什么在外层超时以后还可以继续？
3. 最后一行 `await task` 是重新运行 `generate`，还是等待并读取同一份工作的结果？
4. 内部最终抛出 `ValueError` 时，谁会读到它？

<details>
<summary>查看自查解释</summary>

1. 不是。`shield` 让外层等待仍接收取消，`timeout` 在退出时把自身超时引起的取消转换为 `TimeoutError`。
2. 这次外层取消没有通过 `shield` 传给内部 Task，事件循环仍能推进它。
3. 是等待并读取同一个 Task 的结果，可能需要继续等待，也可能立即取得已完成结果。
4. 本例由 `exercise` 后续等待读取；若错误发生在原来的等待结束前，原来的 `await shield(task)` 也会传播内部错误。

</details>

至此，等待时限、共享预算和取消传播边界已经串起来。下一单元学习：**任务都已安排后，怎样限制同时进入某段工作的数量？** 见[17 · asyncio.Semaphore：限制同时进入的工作](../06-semaphore/)。

{{< python-async-slime title="按需阅读：Slime 应用与本节源码位置" >}}

## run_rollout_io：取消等待者以后，继续负责已接受的工作

上面的 `generate` 是独立标准库实验，不是项目函数的裁剪实现。下面才是固定 Slime 快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 中的原代码。

这里进入 `run_rollout_io` 的提交与等待阶段：调用方交来 `function` 及其输入；函数取得容量许可后，把工作安排到 `pending`，再等待它。当前单元只看取消发生后的等待和责任保留；许可与线程提交将在后续单元展开。

{{< source-reference id="source-1" >}}

1. `pending` 在创建时被保存，正常路径通过 `shield(pending)` 等待它。
2. 外层收到取消后，函数没有立刻丢下已经接受的工作，而是继续持有输入和容量，等待 `pending` 收尾。
3. 后续等待仍使用 `shield`，循环处理再次出现的外层取消。它比主例子只处理一次超时、多承担了反复取消下的等待责任。
4. `pending.result()` 读取工作结果，也可能抛出工作的实际错误。正常完成时，末尾 `raise` 再传播先前的取消。

这里短暂处理 `CancelledError` 是为了完成明确的收尾责任，之后仍传播取消或实际工作错误；不能把它理解为“任何取消都应该忽略”。主例子也没有演示线程能否强行终止，这属于后面的线程单元。

{{< python-async-coverage lesson="13-shield" >}}

## 版本与语义核对

按 [Python 3.12 的 asyncio.shield 文档](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.shield)及本机 CPython 3.12.3 实现核对：外层仍可取消，内部仍可被其他方式取消，Task 引用和后续结果处理需要由调用方负责。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：15 · asyncio.timeout：给一段异步代码共享时间预算](../12-timeout-scope/) · [下一节：17 · asyncio.Semaphore：限制同时进入的工作](../06-semaphore/) · [完整学习路线](../learning-route/)
