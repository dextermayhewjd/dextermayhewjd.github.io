---
title: "03 · Task 与 gather：把多份工作安排起来"
description: "看清创建任务、保留引用和等待整组结果三个动作。"
weight: 30
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="task-creation"></span>

## 从两次顺序等待，改成两份任务

上一节第一份工作结束后才创建第二份。这次先创建两个 Task，再等待它们。

```python
import asyncio

async def generate(rollout_id):
    await asyncio.sleep(0)
    return rollout_id

async def exercise():
    tasks = [asyncio.create_task(generate(i)) for i in (10, 11)]
    print("scheduled", len(tasks))
    results = await asyncio.gather(*tasks)
    print("results", results)

if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
scheduled 2
results [10, 11]
```

这里的关键不是多写了一个 `await`，而是 `create_task()` 已把两个协程安排给事件循环。程序保留 `tasks` 引用，最后由 `gather(*tasks)` 等待整组结果。

`gather` 的返回列表按传入顺序排列。即使编号 11 先完成，列表里的第一个结果仍对应传入的编号 10。

## 用三种情况观察任务是否交错

学过 `create_task` 之后，再把第 2 节的等待放回多任务环境。三种情况共用下面的生成函数；完整实验文件还包含同步等待的版本。

```python
import asyncio
import time

async def generate(rollout_id):
    print("start", rollout_id)
    await asyncio.sleep(0)
    print("end", rollout_id)
    return rollout_id
```

### 对比 A：让出了，但没有另一份任务可运行

仍然使用上面的 `generate()`，把调用处写成：

```python
async def no_other_task():
    await generate(10)
    await generate(11)
```

结果仍然是：

```text
A: no other task
start 10
end 10
start 11
end 11
```

这里已经去掉 `first =` 和 `second =`，顺序没有变，所以**赋值符号不决定等待顺序**。

`generate(10)` 走到 `await asyncio.sleep(0)` 时，当前任务确实让出了一次。但 `generate(11)` 所在的第二行还没执行，它还没有被创建、安排。事件循环没有另一份用户任务可运行，就会在当前任务可以继续时恢复它。

当前只有一条执行链：

```text
exercise / no_other_task 这个任务
  └─ await generate(10)
       └─ await asyncio.sleep(0)  ← 整个当前任务让出
  └─ 第一份返回后，才到 await generate(11)
```

注意：**没有其他任务，不代表没有挂起。** 本例 `sleep(0)` 让出后可以很快恢复；如果是 `sleep(1)`，即使没有别的任务，也要等计时条件满足才能继续。

<span id="comparison-b"></span>

### 对比 B：同样让出，但 11 已经提前排队

`generate()` 一行不改，只改调用处：

```python
async def another_task_is_ready():
    task_11 = asyncio.create_task(generate(11))
    await generate(10)
    await task_11
```

运行这组实验时，`asyncio.run(...)` 已经启动了 `another_task_is_ready()`。**当前正在执行的协程就是这个调用方；它要沿着函数体一行一行往下走。**

#### 为什么先安排了 11，却先执行 10？

看清第一行和第二行做的是不同的事：

| 当前走到哪一行 | 这一步做了什么 | 当前由谁继续执行 |
| --- | --- | --- |
| `task_11 = asyncio.create_task(generate(11))` | 创建 11 的任务，并把它安排给事件循环；本例默认调度下没有在这一行交出执行机会 | 调用方继续往下走 |
| `await generate(10)` | 沿当前执行链直接进入这份新协程，执行到它返回或内部需要暂停为止 | 进入 10，先打印 `start 10` |
| 10 内部的 `await asyncio.sleep(0)` | 当前执行链暂停一次，把执行机会交回事件循环 | 已排队的 11 可以开始 |

**11 先排队，10 却先被当前调用方直接进入。因此“先排队”不代表会抢在当前调用方的下一行之前执行。**

这里的两处 `await` 也要分开看：外层 `await generate(10)` 先进入 10 的函数体；内部执行到 `await asyncio.sleep(0)`，才出现本例的这次让出。不是每看见一个 `await`，就立即换成另一个任务。

在本实验的默认事件循环中，输出为：

```text
B: another task is ready
start 10
start 11
end 10
end 11
```

将输出接回执行过程：

1. 10 被直接进入，先打印 `start 10`。
2. 10 执行到内部的 `await asyncio.sleep(0)`，让出执行机会，11 开始并打印 `start 11`。
3. 11 也执行到内部的 `await asyncio.sleep(0)` 并让出，原来的执行链恢复，10 打印 `end 10` 并返回。
4. 调用方这时才走到 `await task_11`，等待 11 完成；11 恢复后打印 `end 11`。

所以，**`await task_11` 在这里负责等待结果，不是到这一行才启动 11。** 11 已经在 10 暂停期间开始执行。产生这次让出效果的是 `await asyncio.sleep(0)`，不是单独调用 `asyncio.sleep()`。

### 对比 C：任务排好了，但同步 sleep 不让出

把生成函数换成下面这一版。它仍由 `async def` 定义，但内部使用同步的 `time.sleep()`：

```python
async def generate_blocking(rollout_id):
    print("start", rollout_id)
    time.sleep(0.01)
    print("end", rollout_id)
    return rollout_id
```

调用处仍然提前安排 11：

```python
async def blocking_sleep():
    task_11 = asyncio.create_task(generate_blocking(11))
    await generate_blocking(10)
    await task_11
```

输出又变成：

```text
C: blocking sleep
start 10
end 10
start 11
end 11
```

这次 11 已经排队，但 10 中的 `time.sleep()` 阻塞了事件循环所在的线程，没有把执行机会交还给循环。直到 10 返回，调用方等待 `task_11` 时，11 才开始。

<span id="sleep-key-point"></span>

#### 特别记住：阻塞线程与挂起协程是两回事

> **`time.sleep()` 阻塞运行事件循环的线程；`await asyncio.sleep()` 挂起当前任务，把执行机会交还给事件循环。**

即使同样等待 1 秒，两种写法也有这个区别：

| 写法 | 当前等待期间发生什么 | 同一事件循环中的其他已就绪任务 |
| --- | --- | --- |
| `time.sleep(1)` | 线程被阻塞，不能继续推进事件循环 | 无法趁这段等待运行 |
| `await asyncio.sleep(1)` | 当前任务挂起，等待计时条件满足后恢复 | 可以获得执行机会 |

这里的**挂起是暂停，之后还能继续；不是退出协程或执行完函数**。对比 C 中的 11 虽然已排队，但 10 的同步休眠阻塞了事件循环线程，所以 11 不能在这段时间开始。

也不是只有 `asyncio.sleep()` 才能让出：等待网络数据、异步队列等尚未完成的异步操作时，也可能挂起当前任务。本节使用 sleep，是为了把区别看清楚。

还要保留 `await`：单独调用 `asyncio.sleep(1)` 只创建协程对象，不会产生上述等待与让出效果。

### 把三种情况放在一起

| 情况 | 11 是否已安排成另一任务 | 10 内部是否让出 | 10 返回前，11 是否开始 |
| --- | --- | --- | --- |
| A：顺序 await | 没有 | `await asyncio.sleep(0)` 让出 | 没有 |
| B：先创建 Task | 有 | `await asyncio.sleep(0)` 让出 | 有 |
| C：同步 sleep | 有 | `time.sleep()` 阻塞线程 | 没有 |

[下载完整 comparison.py，一次运行三种情况](comparison.py)。它是独立的 Python 语言实验，不是 Slime 原始源码；不连接外部服务。上面的三组输出已用 Python 3.12 默认事件循环实际核对。


## Slime 怎样组织一组样本

在 `generate_and_rm_group` 中，输入是同一组样本；循环为每个样本安排 `generate_and_rm(...)`；`gather` 收齐后把整组结果交还调用方。读取时先看组的输入与输出，不必马上进入生成器的业务细节。

<details>
<summary>展开 Slime 源码：generate_and_rm_group</summary>

{{< source-reference id="source-1" >}}

</details>

<span id="gather-results"></span>

## 一个重要的失败边界

默认的 `gather` 会把子任务异常传播给等待者，但不能据此推断其他子任务都已经被取消。`return_exceptions=True` 则把异常作为列表元素返回，需要调用者检查。

第 5 节会单独讲怎样取消并收尾。这里先保留“安排任务的人也应考虑怎样收回任务”的问题。

<details><summary>复述检查</summary>

`tasks` 保存的是 Task，不是最终样本。`gather` 被等待之后才拿到整组结果。直接 `await generate(...)` 是等待一份工作，先创建多个 Task 才让它们都有机会推进。

</details>

语义核对：[创建 Task](https://docs.python.org/3.12/library/asyncio-task.html#creating-tasks)、[gather](https://docs.python.org/3.12/library/asyncio-task.html#running-tasks-concurrently)。

{{< python-async-coverage lesson="03-tasks" >}}

---

[专题首页](../) · [上一节](../02-await/) · [下一节：04 · wait 与 as_completed：先处理已经完成的工作](../04-results/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
