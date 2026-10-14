---
title: "03 · create_task：先安排工作，再等待结果"
description: "对比直接 await 与提前创建 Task，只增加一种安排协程的方式。"
weight: 30
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 先带上前两课的最小结论

| 已经学过的内容 | 现在需要记住什么 |
| --- | --- |
| 第 01 课：`async def` 与调用 | 定义得到协程函数；调用它只创建协程对象，函数体还不执行。 |
| 第 01 课：普通 `main()` 与 `asyncio.run()` | 脚本入口调用普通 `main()`，里面用 `run` 运行一份协程。 |
| 第 02 课：`async def main()` 与 `await` | 脚本用 `asyncio.run(main())` 进入主协程；主协程用 `await` 执行并等待内部的协程。 |
| 第 02 课：返回值与继续执行 | 内部协程返回后，`await` 取得返回值，调用方才继续下一行。 |

1. **上一节已经会了：** 用 `await` 等待一份协程，取得结果后再继续下一行。
2. **现在多了一个要求：** 两份工作互不依赖，希望一份等待时，另一份也能开始并推进。

    <div class="async-task-comparison" id="direct-await-limitation">
      <section class="async-task-comparison__panel" aria-labelledby="direct-await-current">
        <h3 id="direct-await-current">当前：第一份返回后，才调用第二份</h3>
        <p>第一行直接 <code>await</code> 的协程还没返回，第二行就还没有执行。</p>
        <p><strong>在这个例子中，第一份挂起等待时，第二份协程尚未创建。</strong></p>
      </section>
      <section class="async-task-comparison__panel" aria-labelledby="direct-await-wanted">
        <h3 id="direct-await-wanted">希望：先安排两份工作，再分别等待结果</h3>
        <p>先把两份协程都交给事件循环安排。</p>
        <p><strong>当前任务真正挂起时，事件循环可以推进另一份已经就绪的任务。</strong> 两份等待因此有机会重叠。</p>
      </section>
    </div>

    **要改变的是工作何时被安排，而不是取消 `await` 的等待。** 提前安排任务不代表它们立即同时执行，也不能把上面的限制概括成“`await` 会阻塞所有任务”。

3. **先尝试原来的办法：** 连续写两行直接 `await`，能满足这个要求吗？先观察它们的执行顺序。

## 2. 先看直接 await 的先后关系

为了看清谁先等待、谁先恢复，给两份工作设置不同的等待时长：**10 等 2 秒，11 等 1 秒**。两种调用方式都使用下面的 `generate`：

```python
import asyncio
import time

async def generate(rollout_id, seconds, started_at):
    print(f"[{time.perf_counter() - started_at:.3f}s] generate {rollout_id}: sleep {seconds}s")
    await asyncio.sleep(seconds)
    print(f"[{time.perf_counter() - started_at:.3f}s] generate {rollout_id}: resumed")
    return rollout_id
```

`await asyncio.sleep(seconds)` 暂停当前任务，时间到后才具备继续运行的条件；它不会阻塞整个事件循环。`started_at` 是两份工作共用的计时起点，`time.perf_counter()` 只用来打印“从起点经过了几秒”。日志中的 `sleep 2s` 是请求的等待时长，前面的 `[0.000s]` 是实际经过时间。

先沿用已经会写的直接等待：

```python
async def main():
    started_at = time.perf_counter()
    result_10 = await generate(10, 2, started_at)
    print(f"[{time.perf_counter() - started_at:.3f}s] main: received {result_10}")
    result_11 = await generate(11, 1, started_at)
    print(f"[{time.perf_counter() - started_at:.3f}s] main: received {result_11}")
    print("results", [result_10, result_11])
```

[下载完整 sequential.py](sequential.py) · 运行结果：

```text
[0.000s] generate 10: sleep 2s
[2.002s] generate 10: resumed
[2.002s] main: received 10
[2.002s] generate 11: sleep 1s
[3.002s] generate 11: resumed
[3.002s] main: received 11
results [10, 11]
```

1. **0 秒左右**：10 开始等待 2 秒；`main` 仍在等 10 返回。
2. **2 秒左右**：10 恢复并返回，`main` 才开始调用 11，让它等待 1 秒。
3. **3 秒左右**：11 恢复并返回，两份结果都收到。

这个写法可以取得两份结果，但**第二份工作必须等第一份返回后才会开始**。它还没有满足“一份等待时，另一份也能推进”的新要求。接下来，把“安排工作”和“等待结果”分开。

<span id="task-creation"></span>

## 3. 新增 create_task：先安排，再等待

先看一行：

```python
task_10 = asyncio.create_task(generate(10, 2, started_at))
```

1. **创建协程对象**：`generate(10, 2, started_at)` 仍然只创建对象。
2. **安排执行**：`create_task(...)` 将这份协程包装为 Task，安排给当前运行的事件循环。
3. **取得任务对象**：返回的 `task_10` 用来代表这份任务，不是最终的数字 10。调用方可以继续下一行，不必在这里等它完成。

因此，可以先创建两份 Task，再用已经认识的 `await` 收取结果：

```python
import asyncio
import time

async def generate(rollout_id, seconds, started_at):
    print(f"[{time.perf_counter() - started_at:.3f}s] generate {rollout_id}: sleep {seconds}s")
    await asyncio.sleep(seconds)
    print(f"[{time.perf_counter() - started_at:.3f}s] generate {rollout_id}: resumed")
    return rollout_id

async def main():
    started_at = time.perf_counter()
    task_10 = asyncio.create_task(generate(10, 2, started_at))
    task_11 = asyncio.create_task(generate(11, 1, started_at))
    print(f"[{time.perf_counter() - started_at:.3f}s] main: tasks scheduled")
    result_10 = await task_10
    print(f"[{time.perf_counter() - started_at:.3f}s] main: received {result_10}")
    result_11 = await task_11
    print(f"[{time.perf_counter() - started_at:.3f}s] main: received {result_11}")
    print("results", [result_10, result_11])

if __name__ == "__main__":
    asyncio.run(main())
```

[下载并运行 example.py](example.py)。本例使用 Python 3.12 的默认任务调度。下面是一次实测输出，时间戳每次运行可能略有不同：

```text
[0.000s] main: tasks scheduled
[0.000s] generate 10: sleep 2s
[0.000s] generate 11: sleep 1s
[1.000s] generate 11: resumed
[2.001s] generate 10: resumed
[2.001s] main: received 10
[2.001s] main: received 11
results [10, 11]
```

与上一组相比，**10 先开始睡眠，11 随后开始，却先恢复并完成**。两份等待重叠，所以本次约 2 秒就收齐结果；两行 `await` 仍然先后执行，收到结果的顺序仍是 10、11。时间戳用于观察本次过程，不是精确调度保证。

## 4. 用事件循环解释等待与结果读取

1. **create_task 已经安排任务，不必等各自的 await 才启动。**
   - 本例默认调度下，两次 `create_task` 返回后，`main` 先打印 `tasks scheduled`。
   - 10、11 都已经交给同一个事件循环，有机会被调度。它们没有被放进一个隐藏的 `TaskGroup`。

2. **等待尚未完成的任务时，当前协程让出执行机会。**
   - `main` 执行 `await task_10`，10 尚未完成，于是 `main` 挂起。
   - 事件循环可以逐个推进其他**已经就绪**的任务，不是把所有 Task 同时运行起来。
   - 10 开始等 2 秒后挂起，11 才获得机会开始等 1 秒。仍在等计时到期的任务不能继续往下执行。
   - 这是协作式让出，不是其他任务强行抢占。并非每个 `await` 都会让出：如果等待的 Task 已完成，就能直接取得结果。

3. **每个协程内部仍按自己的代码顺序执行，协程之间可以交错。**
   - `main` 的顺序是先 `await task_10`，再 `await task_11`。
   - 10、11 各自也是先打印 sleep、等待，再打印 resumed。
   - 等待时间可以重叠，但同一线程中的 Python 代码仍然轮流执行；整个程序的执行顺序会在这些协程之间交错。

4. **任务完成，与调用方读取结果，是两个时刻。**
   - 约 1 秒：11 恢复并返回，结果已经保存在 `task_11` 中；`main` 仍在等 10。
   - 约 2 秒：10 完成，`main` 先从 `await task_10` 取得 10。
   - 随后执行 `await task_11`，直接取得已经保存的 11，不会重新运行它，也不会让它再睡 1 秒。

> **create_task 决定哪些工作提前进入调度；await 决定当前协程在哪里等待、何时接着往下走。**

## 5. 读完带走这六条知识

1. **连续直接 await 两份协程，后一行要等前一行返回才执行。**
2. **create_task 安排协程并返回 Task，不等待它执行完成。**
3. **提前安排的其他 Task，可以在当前任务挂起时推进。**
4. **await Task 等待并取得已有任务的结果，不会重新执行它。**
5. **Task 的完成顺序，可以与调用方读取结果的顺序不同。**
6. **create_task 让我们先安排多份工作，再分别等待结果；一份任务挂起期间，其他已经安排且就绪的任务可以继续执行。**

试着回答：

1. 日志里 11 已经在约 1 秒时恢复，为什么 `main` 到约 2 秒才打印 `received 11`？
2. 随后的 `await task_11` 会不会让它重新睡眠？为什么？

接下来的结果收集方式可以单独学习；先确认能分清“安排工作”和“等待结果”。

<span id="gather-results"></span>

整组结果收集已独立为[第 06 课：gather](../05-gather/#gather-results)。先读[第 04 单元的 with / async with](../04-with-async-with/)，再用第 05 课的任务组观察退出时的等待，最后继续收集结果。

<details>
<summary>可选实验：任务安排好了，为什么仍可能不交错？</summary>

已经理解本章主线后，可以用下面的实验检查：任务是否提前安排，以及运行中的代码是否让出执行机会。三种情况共用下面的生成函数；完整实验文件还包含同步等待的版本。

```python
import asyncio
import time

async def generate(rollout_id):
    print("start", rollout_id)
    await asyncio.sleep(0)
    print("end", rollout_id)
    return rollout_id
```

**对比 A：让出了，但没有另一份任务可运行**

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

**对比 B：同样让出，但 11 已经提前排队**

`generate()` 一行不改，只改调用处：

```python
async def another_task_is_ready():
    task_11 = asyncio.create_task(generate(11))
    await generate(10)
    await task_11
```

运行这组实验时，`asyncio.run(...)` 已经启动了 `another_task_is_ready()`。**当前正在执行的协程就是这个调用方；它要沿着函数体一行一行往下走。**

**为什么先安排了 11，却先执行 10？**

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

**对比 C：任务排好了，但同步 sleep 不让出**

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

**特别记住：阻塞线程与挂起协程是两回事**

> **`time.sleep()` 阻塞运行事件循环的线程；`await asyncio.sleep()` 挂起当前任务，把执行机会交还给事件循环。**

即使同样等待 1 秒，两种写法也有这个区别：

| 写法 | 当前等待期间发生什么 | 同一事件循环中的其他已就绪任务 |
| --- | --- | --- |
| `time.sleep(1)` | 线程被阻塞，不能继续推进事件循环 | 无法趁这段等待运行 |
| `await asyncio.sleep(1)` | 当前任务挂起，等待计时条件满足后恢复 | 可以获得执行机会 |

这里的**挂起是暂停，之后还能继续；不是退出协程或执行完函数**。对比 C 中的 11 虽然已排队，但 10 的同步休眠阻塞了事件循环线程，所以 11 不能在这段时间开始。

也不是只有 `asyncio.sleep()` 才能让出：等待网络数据、异步队列等尚未完成的异步操作时，也可能挂起当前任务。本节使用 sleep，是为了把区别看清楚。

还要保留 `await`：单独调用 `asyncio.sleep(1)` 只创建协程对象，不会产生上述等待与让出效果。

**把三种情况放在一起**

| 情况 | 11 是否已安排成另一任务 | 10 内部是否让出 | 10 返回前，11 是否开始 |
| --- | --- | --- | --- |
| A：顺序 await | 没有 | `await asyncio.sleep(0)` 让出 | 没有 |
| B：先创建 Task | 有 | `await asyncio.sleep(0)` 让出 | 有 |
| C：同步 sleep | 有 | `time.sleep()` 阻塞线程 | 没有 |

[下载完整 comparison.py，一次运行三种情况](comparison.py)。它是独立的 Python 语言实验，不是 Slime 原始源码；不连接外部服务。上面的三组输出已用 Python 3.12 默认事件循环实际核对。

</details>

语义核对：[创建 Task](https://docs.python.org/3.12/library/asyncio-task.html#creating-tasks)、[等待对象](https://docs.python.org/3.12/library/asyncio-task.html#awaitables)。

{{< python-async-slime >}}

## 回到 Slime：同样的两步，处理一组样本

在 `generate_and_rm_group` 中，调用方交进来一组样本，函数需要取得这些样本处理后的整组结果。

| 刚学过的动作 | Slime 中对应的写法与作用 |
| --- | --- |
| 安排每一份工作，保留 Task | 循环中把 `generate_and_rm(...)` 交给 `asyncio.create_task(...)`，再用 `tasks.append(...)` 保存返回的 Task。 |
| 等待整组，取得结果 | `group = await asyncio.gather(*tasks)` 把各任务返回的结果收集为列表，赋给 `group`，供后续组级处理使用。 |

先看清这个交接即可：**输入样本组 → 为每个样本安排任务 → 等待并取得结果组 → 继续后面的处理。** `generate_and_rm` 内部怎样生成和评分，不在本节展开。

<details>
<summary>展开 Slime 源码：generate_and_rm_group</summary>

{{< source-reference id="source-1" >}}

</details>

{{< python-async-coverage lesson="03-tasks" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：02 · await：等待结果，不等于自动并发](../02-await/) · [下一节：04 · with / async with：进入、执行与退出](../04-with-async-with/) · [完整学习路线](../learning-route/)
