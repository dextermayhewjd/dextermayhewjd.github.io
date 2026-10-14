---
title: "06 · gather：等待一组任务，收集一组结果"
description: "沿用已创建的两个 Task，理解 gather 的结果列表与传入顺序。"
weight: 60
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 一组任务结束后，怎样一次拿到结果？

1. **前面已经会了：** 第 03 课用 `create_task` 安排工作，再分别 `await` 取得结果；第 05 课用 TaskGroup 管理一组任务的结束。
2. **现在多了一个要求：** 已经安排了多份工作，希望一次等到它们完成，得到一个包含各份返回值的列表。
3. **沿用原来的办法：** 分别 `await`，再把结果放进列表，也能做到。能不能把“等这一组”和“收这一组结果”写在一起？

<details>
<summary>展开对照：第 03 课怎样逐个取得结果</summary>

两份 Task 已经创建好，原来这样取结果：

```python
result_10 = await task_10
result_11 = await task_11
results = [result_10, result_11]
```

两份任务仍可以并发推进。这里比较的是收集结果的写法，不是让它们重新开始运行。

[查看第 03 课完整代码](../03-tasks/example.py)。

</details>

<span id="gather-results"></span>

## 2. 新增 gather：等待已有任务，返回结果列表

把上面三行合成一行：

```python
results = await asyncio.gather(task_10, task_11)
```

沿用同一个 `generate`：10 等待 2 秒，11 等待 1 秒。只改变取得结果的部分。

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
    results = await asyncio.gather(task_10, task_11)
    print("results", results)


if __name__ == "__main__":
    asyncio.run(main())
```

[下载 example.py](example.py) · 运行：`python3 example.py`。本例沿用 Python 3.12 的默认任务调度。

忽略开头可变的时间戳后，一次运行的输出为：

```text
main: tasks scheduled
generate 10: sleep 2s
generate 11: sleep 1s
generate 11: resumed
generate 10: resumed
results [10, 11]
```

## 3. 先完成的任务，结果一定排在前面吗？

**不一定。任务的完成顺序与结果列表的顺序，是两件事。**

| 要观察的顺序 | 本例中发生什么 |
| --- | --- |
| 任务完成顺序 | 11 等得更短，先完成；10 随后完成 |
| 传给 gather 的顺序 | `task_10` 在前，`task_11` 在后 |
| 返回列表的顺序 | `[10, 11]`，与传入顺序对应 |

沿调用过程看：

1. 两份 Task 已由 `create_task` 安排好；`gather` 接收它们，不会重新执行它们。
2. `await` 等待这次整组收集。即使 11 已完成，只要 10 还没有正常返回，本例就还拿不到完整结果列表。
3. 两份任务都正常返回后，`gather` 按传入顺序组成列表，交给 `results`；调用方再打印它。

如果换成 `await asyncio.gather(task_11, task_10)`，同样两份任务的结果列表会变成 `[11, 10]`。

## 4. 读完只带走这三条

1. **gather 可以一起等待多个已经创建的 Task，不会重启它们。**
2. **全部正常完成后，await gather 得到各任务返回值组成的列表。**
3. **列表按传入顺序排列，任务的完成顺序可以不同。**

试着回答：

1. 11 已经结束、10 还在等待时，为什么还不能打印完整的 `results`？
2. 交换传给 `gather` 的两个 Task，变化的是结果顺序，还是任务被重新执行了？

<details>
<summary>补充：任务放在列表中时，怎样使用 *tasks</summary>

把已创建的 Task 放进普通列表：

```python
tasks = [task_10, task_11]
results = await asyncio.gather(*tasks)
```

`*tasks` 是 Python 的参数展开，把列表中的元素分别传入，等价于 `gather(task_10, task_11)`。`tasks` 保存任务对象，`results` 保存返回值。

下面保留原来的无计时简短例子。这里的 `generate` 只接收编号，列表推导式逐个创建 Task，再收集整组结果：

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

[下载 gather_example.py](gather_example.py)。输出为：

```text
scheduled 2
results [10, 11]
```

`scheduled 2` 表示已安排两份任务，不表示它们已经完成。

</details>

<details>
<summary>补充：gather 也可以直接接收协程对象</summary>

在本课的 `main` 内，也可以这样写：

```python
results = await asyncio.gather(
    generate(10, 2, started_at),
    generate(11, 1, started_at),
)
```

`gather` 会把传入的协程安排成 Task。先分别学习 `create_task` 和 `gather`，是为了看清安排工作与收集结果；不是每次使用 `gather` 都必须手动创建 Task。

</details>

<details>
<summary>后续选读：有任务失败时，gather 怎样返回？</summary>

“等到整组完成并得到结果列表”在前文限定为所有任务都正常返回。默认情况下，`gather` 将首先收到的异常传播给等待者，但不会因此自动取消其他任务。`return_exceptions=True` 则将异常作为列表元素返回，由调用方检查。

因此，不能把它当作 TaskGroup 的完整生命周期管理替代品。取消与收尾可从[第 09 单元](../09-task-cancellation/)继续学习；失败后的任务继续见 [10.1](../15-gather-failures/)，收齐结果与异常见 [10.2](../15-gather-exceptions/)。

</details>

{{< python-async-slime title="按需阅读：三库应用与本节源码位置" >}}

## 三个框架为什么都需要整组结果

以下是三仓库统计固定版本中的核心包调用位置数，区别于实际运行次数：

| 框架 | 一处代表性用法 | gather 调用位置数 |
| --- | --- | ---: |
| Slime | [收集同组样本为 group](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L414) | 13 |
| AReaL | [收集各服务启动结果为 server_infos](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/infra/controller/rollout_controller.py#L489) | 100 |
| verl | [收集各样本 agent loop 的 outputs](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/agent_loop/agent_loop.py#L671) | 57 |

下方逐行摘录继续沿用教程的 Slime 固定快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。`generate_and_rm_group` 先为组内样本创建 Task，再通过 `group = await asyncio.gather(*tasks)` 接回组内结果，继续执行需要整组数据的评分。

{{< source-reference id="source-1" >}}

{{< python-async-coverage lesson="05-gather" >}}

语义核对：[Python 3.12 Running tasks concurrently](https://docs.python.org/3.12/library/asyncio-task.html#running-tasks-concurrently)。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：05 · TaskGroup：离开代码块前，等任务结束](../04-taskgroup/) · [下一节：07 · wait：先取得任务的完成情况](../04-results/) · [完整学习路线](../learning-route/)
