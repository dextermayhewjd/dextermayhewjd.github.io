---
title: "05 · TaskGroup：离开代码块前，等任务结束"
description: "承接 with / async with 的进入与退出，用 TaskGroup 等待组内任务结束。"
weight: 50
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 已经会等任务结束，为什么还需要任务组？

1. **第 03 课已经会了：** 先用 `create_task` 安排多份工作，再分别 `await`，可以等它们全部结束。
2. **现在多了一个要求：** 这些任务属于同一组工作。希望给这组工作一个明确的结束位置：继续下一步之前，由这里统一等组内任务结束。
3. **沿用原来的办法：** 可以做到，但保存哪些 Task、等待哪些 Task，仍要由调用方自己组织。能不能让这一段代码在退出时，负责等完交给它的任务？

**第 03 课已经解决了并发执行；本课只增加“一组任务在哪里统一等完”的管理方式。** 先看全部任务正常结束的情况。

<span id="async-with-basics"></span>

先确认已经理解上一单元的 [with / async with：进入、执行与退出](../04-with-async-with/#async-with-basics)。下面使用 TaskGroup 验证一次具体的退出操作。

<span id="2-新增-taskgroup-和它的代码块"></span>

<span id="3-taskgroup正常退出代码块前等组内任务结束"></span>

## 2. TaskGroup：正常退出代码块前，等组内任务结束

**TaskGroup 让一个代码块负责一组任务：正常离开这个代码块前，等组内任务全部结束。**

下面用 `async with asyncio.TaskGroup() as group:` 建立并进入任务组。`group` 接收进入动作的返回值；对 TaskGroup 来说，返回的就是这个任务组本身。缩进部分就是它的代码块。

沿用第 03 课的 `generate`，只替换 `main` 中安排和等待任务的部分：

<div class="taskgroup-code-comparison" id="taskgroup-code-comparison">
<div class="taskgroup-code-comparison__current">
<p class="taskgroup-code-comparison__title">本课：TaskGroup 统一等待</p>

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
    async with asyncio.TaskGroup() as group:
        group.create_task(generate(10, 2, started_at))
        group.create_task(generate(11, 1, started_at))
        print(f"[{time.perf_counter() - started_at:.3f}s] main: inside group")
    print(f"[{time.perf_counter() - started_at:.3f}s] main: group finished")


if __name__ == "__main__":
    asyncio.run(main())
```

</div>

<details class="taskgroup-code-comparison__previous" id="previous-task-example">
<summary>展开对比代码：第 03 课的 create_task 与逐个 await</summary>

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

这是第 03 课的完整原例。`generate` 保持不变，对比时只看 `main` 怎样安排任务、在哪里等待。

[下载第 03 课完整 example.py](../03-tasks/example.py)。

旧写法在两行 `await task_10`、`await task_11` 处等待；本课的新写法由 TaskGroup 在退出 `async with` 时统一等待组内任务。

</details>
</div>

[下载 example.py](example.py) · 运行：`python3 example.py`。TaskGroup 需要 Python 3.11 及以上；本例沿用 Python 3.12 的默认任务调度。

忽略开头可变的时间戳后，一次运行的输出为：

```text
main: inside group
generate 10: sleep 2s
generate 11: sleep 1s
generate 11: resumed
generate 10: resumed
main: group finished
```

<span id="4-沿三个位置理解等待发生在哪里"></span>

## 3. 沿三个位置理解等待发生在哪里

1. **进入代码块**：创建并进入 TaskGroup，把它绑定到 `group`。
2. **执行代码块内的语句**：两次 `group.create_task` 安排任务；`main` 接着打印 `inside group`，没有在每次创建后等结果。
3. **正常退出代码块**：即使 `main` 已走到缩进代码的最后一行，组内任务也可能还在运行。TaskGroup 在退出时等待，等两份工作都结束，才允许 `main` 打印外面的 `group finished`。

`async with` 的进入和退出可以执行异步操作；本例中需要记住的就是**退出时等待组内任务**。代码块内的语句仍按顺序执行。

<span id="31-create_task-已经安排任务为什么先打印-inside-group"></span>

### 3.1 TaskGroup.create_task：已经安排任务，为什么先打印 inside group？

在本课使用的默认调度下，沿主例子看四步：

1. 两次 `group.create_task(...)` 已经创建并安排了任务 10、11，但不会在这里等待它们执行完。
2. `main` 接下来没有挂起，继续打印 `main: inside group`。此时只是组内主线语句执行到了这里，不代表任务 10、11 已经结束。
3. `main` 走到缩进末尾，开始执行 TaskGroup 的退出操作。退出需要等组内任务，所以 `main` 在这里挂起，事件循环才有机会推进已经安排好的任务。
4. 任务 10、11 都结束后，退出操作完成，`main` 才能打印块外的 `main: group finished`。

因此，**这份主例子确实是先打印 `inside group`，再看到两份 `generate` 开始执行。但原因是 `main` 在退出时才首次挂起，不是 TaskGroup 规定任务必须等到退出时才能开始。**

### 3.2 TaskGroup 退出等待：main 挂起时，其他任务怎样继续？

这里的 **“`main` 挂起”是指：正在执行 `main()` 的任务暂时停在等待的位置，保留当前的执行进度和变量，让事件循环有机会运行其他已经安排的任务。**

在主例子中，这个等待位置就在 TaskGroup 的退出过程中。虽然你没有在缩进末尾再写一行 `await`，TaskGroup 的退出操作仍会进行异步等待。

沿着主例子的输出，可以把这段过程拆开看：

| 发生了什么 | `main` 此时在做什么 |
| --- | --- |
| 打印 `main: inside group` | 还在执行代码块内的语句 |
| 准备退出 TaskGroup，组内任务还没结束 | 挂起在退出等待处，暂时不能执行块外的打印 |
| 任务 10、11 开始执行，分别等待 2 秒和 1 秒 | 继续等待组内任务全部结束 |
| 任务 11 先结束，任务 10 还没结束 | 仍不能结束这次退出等待 |
| 任务 10 也结束，组内任务全部结束 | 随后恢复执行，完成退出，再打印 `main: group finished` |

因此，挂起的是执行 `main()` 的这个任务，**整个程序没有停止**。任务 10、11 仍然可以获得执行机会；它们执行到各自的 `await asyncio.sleep(...)` 时，也会暂停等待，到时间后再继续。

`main` 恢复时会接着完成刚才的退出过程，不会从函数第一行重新运行，也不会重新创建任务 10、11。这里的等待只是等工作结束，并不会替任务执行工作，也不会把没有完成的任务直接变成已完成。

### 3.3 async with 与 TaskGroup：谁规定了退出时要等任务？

你可以把当前例子的规则记成：**正常退出 `async with asyncio.TaskGroup()` 时，只要组内还有任务没结束，TaskGroup 就会异步等待；这时执行 `main()` 的任务会挂起。**

但这两个部分各自负责的事情需要分清：

| 写法 | 在这里负责什么 |
| --- | --- |
| `async with` | 安排进入、执行代码块和退出；允许进入与退出过程进行异步等待 |
| `asyncio.TaskGroup()` | 提供具体的进入与退出行为；正常退出时，等待登记到这个组里的全部任务结束 |

上一单元的 `with open(...) as file:` 在退出时关闭文件；本课的 TaskGroup 在退出时等待组内任务。**退出时具体做什么，由被使用的对象决定。** `async with` 本身不会自动寻找程序里所有没完成的任务。

由此可以判断两种情况：

1. **退出时组内还有任务没完成：** TaskGroup 继续等待，`main` 暂停在退出处，直到组内任务全部结束。
2. **退出时组内任务已经全部完成：** 不需要再等待这些任务，`main` 可以完成退出并继续向下执行。写了 `async with`，并不意味着退出时一定会发生一次挂起。

这里的“组内任务”指通过这个 `group.create_task(...)` 登记的任务。仅仅在缩进代码块里使用普通的 `asyncio.create_task(...)`，不会自动把它加入这个 TaskGroup。

以上仍只讨论全部任务正常结束的路径；发生异常或取消时的处理放到后续单元。

<span id="32-组内先挂起一次任务就可以在退出前推进"></span>

### 3.4 asyncio.sleep(0)：组内先挂起一次，任务就可以在退出前推进

保持主例子的两份任务不变，只在组内打印之前插入一行已经学过的等待：

```python
group.create_task(generate(10, 2, started_at))
group.create_task(generate(11, 1, started_at))
await asyncio.sleep(0)
print(f"[{time.perf_counter() - started_at:.3f}s] main: inside group")
```

`sleep(0)` 让当前任务挂起一次，给其他已经安排的任务执行机会。[下载完整对照 start_before_exit.py](start_before_exit.py)。忽略时间戳后，本机实际输出：

```text
generate 10: sleep 2s
generate 11: sleep 1s
main: inside group
generate 11: resumed
generate 10: resumed
main: group finished
```

这次两份 `generate` 在组内打印之前就已经开始，作用域仍未退出。之后走到退出位置时，TaskGroup 继续等待尚未完成的工作。

**创建时安排任务，挂起时让其他任务推进，退出时确保组内任务都结束。** 不要把这三个位置合并成“退出时才开始运行任务”。

与第 03 课对照，现在可以看清两处变化：

| 做的事 | 第 03 课的方式 | 本课的方式 |
| --- | --- | --- |
| 安排任务 | `asyncio.create_task` 返回 Task，由调用方记录 | `group.create_task` 安排 Task，并把它登记到组内 |
| 正常结束前等待 | 调用方执行自己安排的各个 `await` | TaskGroup 在退出代码块时统一等待组内任务 |

<span id="5-读完只带走这三条"></span>

## 4. 读完只带走这三条

1. **`group.create_task` 安排任务，并把任务交给这个 TaskGroup 管理。** 它仍然返回 Task；本例暂时不用保存这个返回值。
2. **组内语句仍按顺序执行；创建任务时，不等待这份任务完成。** 已安排的任务可以在组内的挂起点推进，不必等到退出时才开始。
3. **正常退出代码块前，TaskGroup 会等所有组内任务结束。** 还有任务未完成时，执行 `main()` 的任务会挂起等待，其他任务仍能继续；全部完成后，`main` 才继续执行块外的下一行。这是 TaskGroup 的退出行为，不是所有 `async with` 都会等待任务。

试着回答：

1. `inside group` 已打印，两份任务一定结束了吗？
2. 把任务 10 的等待改成 3 秒，`group finished` 能在它结束前打印吗？
3. 在组内打印之前加入 `await asyncio.sleep(0)`，两份任务能否在退出作用域之前开始执行？
4. 退出时任务 11 已结束、任务 10 还没结束，`main` 能继续打印 `group finished` 吗？此时任务 10 还能继续执行吗？

这里展示全部任务成功的路径。遇到未处理的普通异常时，TaskGroup 会取消其余任务、等待收尾，再向外报告异常；这部分在[TaskGroup 的失败处理](../11-taskgroup-failures/)中继续学习。

接下来可以单独学习 [gather 怎样收集整组返回值](../05-gather/#gather-results)。它已经独立为第 06 课。

{{< python-async-slime title="按需阅读：AReaL 应用与本节源码位置" >}}

## AReaL 为什么把评分任务放进一组

AReaL 的推理服务需要为多份 session 并发评分，并在释放这些 session 前等评分结束。下面保留实际的 TaskGroup 作用域：先用 `scoring.create_task` 安排评分，退出组后才读取结果。

本节只对应这个“离开作用域前等任务结束”的关系。评分业务、结果检查和 session 的完整释放路径属于后续源码阅读。

{{< source-reference id="source-1" >}}

<section id="source-usage-locations">

## 本节对应的源码位置

本轮固定版本的核心包中，AReaL 有一处 `TaskGroup` 构造和一处 `TaskGroup.create_task` 调用，都在上述代码块；Slime 和 verl 未命中这两种调用。将它放在这里是为了补全任务作用域的理解，仍需与三库共同高频的 `gather` 区分。

| API | AReaL 固定版本位置 |
| --- | --- |
| `asyncio.TaskGroup()` | [app.py:1011](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/v2/inference_service/data_proxy/app.py#L1011) |
| `scoring.create_task(...)` | [app.py:1013](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/v2/inference_service/data_proxy/app.py#L1013) |

</section>

语义核对：[Python 3.12 Task groups](https://docs.python.org/3.12/library/asyncio-task.html#task-groups)、[sleep 与 sleep(0)](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.sleep)、[async with](https://docs.python.org/3.12/reference/compound_stmts.html#the-async-with-statement)。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：04 · with / async with：进入、执行与退出](../04-with-async-with/) · [下一节：06 · gather：等待一组任务，收集一组结果](../05-gather/) · [完整学习路线](../learning-route/)
