---
title: "04 · TaskGroup：离开代码块前，等任务结束"
description: "沿用两个 Task 的例子，只增加一个关系：由 TaskGroup 等待组内任务结束。"
weight: 40
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 已经会等任务结束，为什么还需要任务组？

1. **上一节已经会了：** 先用 `create_task` 安排多份工作，再分别 `await`，可以等它们全部结束。
2. **现在多了一个要求：** 这些任务属于同一组工作。希望给这组工作一个明确的结束位置：继续下一步之前，由这里统一等组内任务结束。
3. **沿用原来的办法：** 可以做到，但保存哪些 Task、等待哪些 Task，仍要由调用方自己组织。能不能让这一段代码在退出时，负责等完交给它的任务？

**第 03 课已经解决了并发执行；本课只增加“一组任务在哪里统一等完”的管理方式。** 先看全部任务正常结束的情况。

## 2. 新增 TaskGroup 和它的代码块

**TaskGroup 让一个代码块负责一组任务：正常离开这个代码块前，等组内任务全部结束。**

下面用 `async with asyncio.TaskGroup() as group:` 建立并进入任务组，`group` 是指向这个组的变量名；缩进部分就是它的代码块。

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

## 3. 沿三个位置理解等待发生在哪里

1. **进入代码块**：创建并进入 TaskGroup，把它绑定到 `group`。
2. **执行代码块内的语句**：两次 `group.create_task` 安排任务；`main` 接着打印 `inside group`，没有在每次创建后等结果。
3. **正常退出代码块**：即使 `main` 已走到缩进代码的最后一行，组内任务也可能还在运行。TaskGroup 在退出时等待，等两份工作都结束，才允许 `main` 打印外面的 `group finished`。

`async with` 的进入和退出可以执行异步操作；本例中需要记住的就是**退出时等待组内任务**。代码块内的语句仍按顺序执行。

与第 03 课对照，现在可以看清两处变化：

| 做的事 | 第 03 课的方式 | 本课的方式 |
| --- | --- | --- |
| 安排任务 | `asyncio.create_task` 返回 Task，由调用方记录 | `group.create_task` 安排 Task，并把它登记到组内 |
| 正常结束前等待 | 调用方执行自己安排的各个 `await` | TaskGroup 在退出代码块时统一等待组内任务 |

## 4. 读完只带走这三条

1. **`group.create_task` 安排任务，并把任务交给这个 TaskGroup 管理。** 它仍然返回 Task；本例暂时不用保存这个返回值。
2. **组内语句仍按顺序执行；创建任务时，不等待这份任务完成。**
3. **正常退出代码块前，TaskGroup 会等所有组内任务结束。** 之后才继续执行代码块外的下一行。

试着回答：

1. `inside group` 已打印，两份任务一定结束了吗？
2. 把任务 10 的等待改成 3 秒，`group finished` 能在它结束前打印吗？

这里展示全部任务成功的路径。遇到未处理的普通异常时，TaskGroup 会取消其余任务、等待收尾，再向外报告异常；这部分随[取消与超时](../05-cancellation/)继续学习。

接下来可以单独学习 [gather 怎样收集整组返回值](../05-gather/#gather-results)。它已经独立为第 05 课。

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

语义核对：[Python 3.12 Task groups](https://docs.python.org/3.12/library/asyncio-task.html#task-groups)、[async with](https://docs.python.org/3.12/reference/compound_stmts.html#the-async-with-statement)。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：03 · create_task](../03-tasks/) · [下一节：05 · gather：等待一组任务，收集一组结果](../05-gather/) · [gather 结果收集入口](../05-gather/#gather-results)
