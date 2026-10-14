---
title: "06 · wait 与 as_completed：先处理已经完成的工作"
description: "先用已知的任务和 sleep 理解 wait，再学习按完成顺序取得结果。"
weight: 60
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 这次只给已知的两份任务换一种等待方式

上一节已经会用 `gather` 等待整组任务正常完成并取得结果。现在增加一个需求：有任务完成时，先取得完成情况，继续管理尚未结束的任务。本节沿用已知的 Task 和 sleep，先集中看一行新的 `asyncio.wait()`。

先准备一个你已经认识的协程：

```python
async def generate(rollout_id, seconds):
    await asyncio.sleep(seconds)
    return rollout_id
```

它等待指定秒数，然后返回自己的编号。

```python
task_10 = asyncio.create_task(generate(10, 2))
task_11 = asyncio.create_task(generate(11, 1))
tasks = [task_10, task_11]
```

现在安排了两份任务：10 等 2 秒，11 等 1 秒。`tasks` 只是保存这两个 Task 的普通列表。

<span id="wait-results"></span>

## 第一步：只看 wait 这一行

```python
done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
```

可以读成：**“等这组任务，只要有任务完成，就把此刻的完成情况交给我。”**

<span id="wait-execution-order"></span>

### 这里的 await 到底在执行谁？

**`asyncio.wait()` 本身也是一个协程函数。** 因此，`await` 后面既可以是我们写的 `generate(...)`，也可以是库提供的 `asyncio.wait(...)`。

这一行直接进入的是 **wait 自己的等待逻辑**：观察 `tasks` 中已经安排好的任务，直到指定条件满足，再返回 `done` 和 `pending`。

把本例从头连起来看：

```text
exercise() 正在执行
    ↓
create_task 把 10、11 安排好，调用方继续往下走
    ↓
await asyncio.wait(...) 进入 wait 的逻辑
    ↓
任务还没完成，wait 需要等待，当前调用方挂起
    ↓
事件循环获得执行机会，运行已经排队的 10、11
    ↓
有任务完成，满足 FIRST_COMPLETED
    ↓
wait 返回 done、pending，调用方继续下一行
```

本例使用默认调度方式，创建完两个 Task 后没有先在别处让出执行机会，所以它们在这里得到运行机会。

**不要记成“只要出现 await，就自动启动所有协程”。** 先看 `await` 后面等待的是谁，再看它是否需要挂起。`create_task` 已经负责安排 10、11；这一行负责等待它们达到条件。如果任务此前已经开始，wait 就观察现有任务，而不是重新启动它们。


| 这一小段 | 在说什么 |
| --- | --- |
| `tasks` | 要观察的那两份任务 |
| `FIRST_COMPLETED` | 返回条件：至少有一份任务完成 |
| `await asyncio.wait(...)` | 当前调用方等待这个条件满足；两份任务仍可以推进 |
| `done, pending` | 把返回的两组 Task 接到两个普通变量中 |

`done` 和 `pending` 只是这里取的变量名，不是需要再调用的功能。

按本例通常的执行顺序，约 1 秒后 11 已经返回，10 还在等待。因此这次返回时：

```text
done     里面是 task_11：已经完成
pending  里面是 task_10：尚未完成
```

**wait 返回，不代表 10 被停止了。** 当前调用方只是先拿到了这次完成情况。

## 第二步：完成的 Task 和它返回的值不同

`done` 里面放的是 Task 对象，不是数字 11。Task 保存着那份协程最终返回的值。

确认任务已经完成后，可以这样拿出返回值：

```python
print(task_11.result())  # 得到 generate 中 return 的 11
```

这里的 `.result()` 是取出已有结果，不会重新执行 `generate(11, 1)`。本节先看正常返回的情况；任务出错时，取结果也可能抛出错误。

## 第三步：还没完成的任务怎么办

10 还在 `pending` 里。这里用整组收集工具 `gather` 等它完成；写法见[第 05 课的 gather 讲解](../05-gather/#gather-results)：

```python
await asyncio.gather(*pending)
```

这样，先拿到了 11 的结果，随后又等到了 10，没有把剩下的工作遗留在后台。

<span id="gather-remaining-time"></span>

### wait 返回以后，sleep 的时间还在走吗？

**在走。挂起的是协程代码，不是已经开始的 sleep 等待时间。**

本例里，10、11 在同一个事件循环线程中先后获得执行机会，很快都进入了各自的 sleep。可以把它们看成几乎同时开始等待，但不是两个函数体在两个线程中同时执行。

约 1 秒后，11 完成，`wait` 返回。调用方接着运行两行 `print`。此时 10 通常还挂起在自己的 `sleep(2)` 上：它后面的 `return` 没有在后台继续执行，但等待的时间仍随真实时间流逝。

这里是同一线程中的调用方协程恢复了，不是切换到另一个“主线程”。如果两行同步 `print` 占用这条线程，事件循环里的其他协程也不能趁这段时间执行 Python 代码。

### gather 还需要等多久？

以两个任务进入 sleep 的时刻近似作为 0 秒，忽略启动差距和调度开销：

| 时刻 | 发生什么 |
| --- | --- |
| 0 秒 | 10 开始等 2 秒；11 开始等 1 秒 |
| 1 秒 | 11 完成，`wait` 返回，调用方开始执行两行 `print` |
| 1.5 秒 | 假设两行 `print` 共耗时 0.5 秒，现在执行 `await asyncio.gather(*pending)` |
| 2 秒 | 10 的等待到期；它获得执行机会、继续到 `return`，gather 随后拿到结果 |

因此，**gather 等的是这份任务剩余的等待与执行时间，不是重新开始等完整的 2 秒。**

| wait 返回后，两行 print 的总耗时 | 到 gather 时，10 通常还要等多久 |
| --- | --- |
| 近似 0 秒 | 约 1 秒 |
| 0.5 秒 | 约 0.5 秒 |
| 已超过 1 秒 | sleep 的等待条件已满足，但仍需调度 10 继续运行到返回 |

还要分清“计时到期”和“代码已经继续执行”：如果事件循环的线程正被同步代码占用，10 即使已经等够 2 秒，也得等线程重新处理事件循环，才能执行后面的代码。

`await gather(*pending)` 在本例中让调用方继续等待，给剩余任务恢复的机会；它不重启任务，也不重设 sleep。这里 `pending` 只有 10，所以最终收取的是 `[10]`。


<details>
<summary>展开完整的 wait 实验</summary>

```python
import asyncio


async def generate(rollout_id, seconds):
    await asyncio.sleep(seconds)
    return rollout_id


async def exercise():
    task_10 = asyncio.create_task(generate(10, 2))
    task_11 = asyncio.create_task(generate(11, 1))
    tasks = [task_10, task_11]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    print("done", sorted(task.result() for task in done))
    print("pending", len(pending))
    print("remaining", await asyncio.gather(*pending))


if __name__ == "__main__":
    asyncio.run(exercise())
```

</details>

[下载并运行 example.py](example.py)。这是独立的标准库语言实验，不连接模型或其他外部服务。

一次运行的输出为：

```text
done [11]
pending 1
remaining [10]
```

`FIRST_COMPLETED` 的意思是“至少一份完成”，不保证返回时恰好只有一份完成。如果调用方恢复得较晚，两份任务也可能都已完成，此时 `done` 包含两份，`pending` 为空。

如果省略 `return_when=...`，`asyncio.wait(tasks)` 默认等整组任务完成。先记住当前这个“有任务完成就返回”的版本即可。

## 先在这里检查理解

如果 10 还在睡眠，11 已经返回：

- `done` 里应该是谁？
- `pending` 里应该是谁？
- `wait` 返回后，10 会被自动停止吗？

<details><summary>查看解释</summary>

`done` 里是 11 的 Task，`pending` 里是 10 的 Task。10 没有被停止，只是尚未完成。`wait` 返回的是任务状态的两组集合，返回值需要从任务中取得。

</details>

---

<span id="as-completed-results"></span>

## 理解 wait 后，再看 as_completed

现在换一个需求：**谁先完成，就先处理谁的结果，然后继续等下一份。**

独立运行下面这组实验，重新创建同样的两份任务。收取结果时换成：

```python
for completed in asyncio.as_completed(tasks):
    result = await completed
    print("result", result)
```

这里先把 `completed` 理解成“取得下一份完成结果的等待入口”，不是已经拿到的结果值。

1. 第一次 `await completed` 等到最快完成的那份，得到 11。
2. 下一次循环再次等待，得到随后完成的 10。
3. 两份结果都取完，循环结束。

```text
result 11
result 10
```

这个循环按完成先后拿结果，不要求按 `tasks` 列表的顺序。循环中的 `await` 仍然是在等待，其他已安排的任务可以继续推进。

<details>
<summary>展开完整的 as_completed 实验</summary>

```python
import asyncio


async def generate(rollout_id, seconds):
    await asyncio.sleep(seconds)
    return rollout_id


async def exercise():
    task_10 = asyncio.create_task(generate(10, 2))
    task_11 = asyncio.create_task(generate(11, 1))
    tasks = [task_10, task_11]

    for completed in asyncio.as_completed(tasks):
        result = await completed
        print("result", result)


if __name__ == "__main__":
    asyncio.run(exercise())
```

</details>

[下载并运行 as_completed.py](as_completed.py)。本专题使用 Python 3.12 的普通 `for` 写法，每次通过 `await completed` 获取结果。

## 两者的区别，最后再放到一起

| 入口 | 交给调用方什么 |
| --- | --- |
| `wait(..., FIRST_COMPLETED)` | 此刻已完成和未完成的两组任务；后续怎样处理由调用方决定 |
| `as_completed(tasks)` | 逐个等待完成结果的入口，方便循环处理每一份结果 |

语义核对：[wait / as_completed](https://docs.python.org/3.12/library/asyncio-task.html#waiting-primitives)。

{{< python-async-slime >}}

## 回到 Slime 的两种消费者

理解前面的独立实验后，再展开源码。rollout 循环用 `wait` 拿到完成集合，继续管理 `state.pendings`；评测分支用 `as_completed` 逐个处理结果。

<details>
<summary>展开 Slime 源码：generate_rollout_async</summary>

{{< source-reference id="source-1" >}}

</details>

<details>
<summary>展开 Slime 源码：eval_rollout_single_dataset</summary>

{{< source-reference id="source-2" >}}

</details>

{{< python-async-coverage lesson="04-results" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../05-gather/) · [下一节：07 · 取消与超时：请求停止以后，还要等待收尾](../05-cancellation/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
