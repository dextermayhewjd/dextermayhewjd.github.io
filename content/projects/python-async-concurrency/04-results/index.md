---
title: "07 · wait：先取得任务的完成情况"
description: "承接 gather，用 wait 取得 done/pending，再用已学的 await 读取结果并等完剩余任务。"
weight: 70
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 一份任务已经完成，能先继续往下做吗？

1. **上一课已经会了：** 用 `create_task` 安排两份工作，再用 `gather` 等待整组正常完成，得到结果列表。
2. **现在多了一个要求：** 两份工作用时不同。希望有任务完成时，就先取得完成情况，处理这部分结果，之后再等剩余工作。
3. **先看原来的办法：** 如果仍写 `results = await asyncio.gather(task_10, task_11)`，即使 11 已完成，只要 10 还没完成，就还拿不到完整的 `results`。

因此，这次需要一个不同的等待条件：**先等到至少一份任务完成，再把任务分成“已完成”和“未完成”两组交回来。**

本页按[41 单元学习路线](../learning-route/#curriculum-stage-results)编排，只新增 `asyncio.wait`。拿到 Task 之后，继续用已学过的 `await` 取值；Task 的结果方法在规划第 08 单元展开，按完成顺序连续取结果在规划第 12 单元展开。后续请按学习路线继续；侧边栏将已整理的单元与旧版参考材料分开显示。

<span id="wait-results"></span>

## 2. 沿用两份工作，只换等待方式

仍然是编号 10 和 11：10 等待 2 秒，11 等待 1 秒，然后各自返回编号。这里去掉上一课显示时间戳的辅助代码，保留相同的等待与返回行为。

先预测：`wait` 返回时，哪一份更可能已经完成？哪一份还需要继续等待？

```python
import asyncio


async def generate(rollout_id, seconds):
    await asyncio.sleep(seconds)
    return rollout_id


async def exercise():
    task_10 = asyncio.create_task(generate(10, 2))
    task_11 = asyncio.create_task(generate(11, 1))
    tasks = [task_10, task_11]

    # wait 返回 (done, pending)，两者都是 set，元素是 Task 对象。
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
    )
    print("done", len(done))
    print("pending", len(pending))

    for task in done:  # 返回时已完成的 Task 集合
        # 本例中任务已正常完成：直接取结果，再打印，不会重新执行任务。
        print("completed", await task)

    for task in pending:  # 返回时尚未完成的 Task 集合
        # 任务早已安排好，仍由事件循环管理，不是到这里才启动。
        # 若仍未完成，exercise 在 await 处挂起，等到任务完成后再打印。
        # 若此时已经完成，就直接取得结果。
        print("remaining", await task)


if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载 example.py](example.py) · 运行：`python3 example.py`。这是独立的标准库实验，使用 Python 3.12 的默认任务调度。

本机 Python 3.12.3 的一次运行输出为：

```text
done 1
pending 1
completed 11
remaining 10
```

`done 1` 和 `pending 1` 是两组任务的数量；`completed 11` 和 `remaining 10` 才是从任务中取得的返回值。短一些的等待有助于观察这次实验，不能把一次运行的先后当成所有调度条件下的保证。

<span id="wait-execution-order"></span>

## 3. 这一行等待的是谁，交回的又是什么？

```python
done, pending = await asyncio.wait(
    tasks,
    return_when=asyncio.FIRST_COMPLETED,
)
```

| 这一部分 | 在本例中表示什么 |
| --- | --- |
| `tasks` | 已由 `create_task` 安排好的两个 Task |
| `return_when=asyncio.FIRST_COMPLETED` | 等待条件：至少一份任务完成 |
| `await asyncio.wait(...)` | 等待这次完成情况的返回 |
| `done, pending` | 接住返回的两组集合：已完成的 Task、尚未完成的 Task |

`wait` 返回二元组 `(done, pending)`，其中 `done` 和 `pending` 各是一个 **集合（set）**，不是数组或列表。集合里装的是原来的 **Task 对象**；`generate` 返回的数字要通过 `await task` 取得。

沿本次运行往下看：

1. **安排任务。** 两次 `create_task` 已安排 10 和 11。`tasks` 只是把这两个对象保存到普通列表里。
2. **等待条件满足。** `asyncio.wait` 本身也是协程函数，`await` 进入它的等待逻辑。任务尚未完成时，调用方挂起，事件循环有机会推进已经安排的任务。本例创建 Task 后没有先在别处挂起，它们在这里获得运行机会；已经开始的任务也不会被 `wait` 重新启动。
3. **接回完成情况。** 本次运行中，11 先正常返回，10 仍在等待。`wait` 返回时，`done` 含 `task_11`，`pending` 含 `task_10`，调用方继续执行后面的 `print`。
4. **读取已经完成的任务。** 第一个 `for` 取出 `done` 中的 Task。`await task` 取得已保存的返回值 `11`，不会再执行一次 `generate`。
5. **等完剩余任务。** 第二个 `for` 取出 `pending` 中的 Task。`await task` 等到它完成，取得 `10`。这次等待延续原任务，不会重置它已经开始的 `sleep`。

两个 `for` 循环依次取值，不会使已经安排好的任务改为逐个启动。安排工作的是前面的 `create_task`。

## 4. wait 返回以后，还要负责什么？

1. **未完成的任务仍需要有人等待。** `wait` 返回完成情况，不会顺手停止 `pending` 中的任务。本例用第二个 `for` 等完它们，之后 `exercise` 才返回。
2. **FIRST_COMPLETED 表示至少一份完成。** 如果调用方恢复时两份都已完成，`done` 可以包含两份，`pending` 为空；后面的第二个 `for` 就没有任务可取。
3. **两组集合记录的是返回时的分类。** 拿到 `pending` 后，其中的任务仍可能继续推进。集合也不承诺任务顺序，所以不能把 `for task in done` 当作按完成先后排序。

这一页用两份正常返回的任务建立关系。失败与取消时怎样读取结果、怎样收尾，会在后续单元中增加。

## 5. 带走三条结论，再做自查

1. **create_task 安排任务；wait 等待指定的完成条件。** 本例等到至少一份任务完成就返回。`wait` 返回这件事本身，不会停止 `pending` 中的任务。
2. **done 和 pending 都是装着 Task 对象的集合（set），不是返回值数组。** 它们记录返回时哪些任务已完成、哪些尚未完成；`await task` 才取得任务的返回值。
3. **await task 是让调用方等待，不是让任务保持运行的开关。** `task10` 早已被安排好；只要事件循环继续运行、它的等待条件满足并获得调度，就可以继续推进，不要求调用方直接 `await task10`。

   **为什么本例最后还要等待 pending？** 如果 `task10` 仍未完成，`await task` 会让调用方 `exercise()` 暂停，等它完成后取得结果，再继续打印。若删掉这个等待，让 `exercise()` 直接返回，`asyncio.run()` 就会进入收尾，取消仍未完成的任务。因此，本例保留最后的等待，是为了先等 `task10` 正常完成，再结束 `exercise()`。

试着回答：

1. 假设 `wait` 返回时 11 已完成、10 尚未完成，两组集合各放谁？数字 `11` 又是在哪一步取到的？
2. 把两份工作的等待时间对调，会改变哪个 Task 更可能先完成？需要换掉 `wait` 的返回条件吗？
3. 如果 `wait` 返回时两份都已完成，第二个 `for` 会做什么？
4. 如果删掉等待 `pending` 的循环，让 `exercise()` 直接返回，`asyncio.run()` 会怎样处理仍未完成的 `task10`？

<details>
<summary>查看自查解释</summary>

1. `done` 放 `task_11`，`pending` 放 `task_10`；第一个循环中的 `await task` 取得数字 `11`。
2. 对调等待时间后，10 更可能先完成。条件仍是“至少一份完成”，不需要修改。
3. `pending` 为空，第二个循环不执行；第一个循环读取两份结果，集合不保证遍历顺序。
4. `asyncio.run()` 会进入收尾，取消仍未完成的任务。`task10` 不是因为缺少一次直接 `await` 就自动停止，而是因为本例的入口函数已经结束。保留最后的等待，才能让入口函数先等完它。

</details>

下一单元将直接观察 Task 的状态与结果：怎样判断已经完成，怎样读取返回值或异常。继续阅读[第 08 单元：done、result、exception：读取 Task 的状态与结果](../07-task-results/)。

{{< python-async-slime title="按需阅读：后续单元、补充实验与源码位置" >}}

## 后续单元 07：Task 保存的结果怎样读取？

[第 08 单元已经独立整理：done、result、exception：读取 Task 的状态与结果](../07-task-results/)。

旧版页面用下面这一行读取已经正常完成的任务：

```python
print(task_11.result())  # 得到 generate 中 return 的 11
```

`.result()` 读取 Task 保存的结果，不会重新执行 `generate`。但它与 `await task` 的等待行为不同：任务尚未完成、失败或被取消时，读取结果需要区分处理。第 08 单元将先讲未完成、成功与失败，取消状态在第 09 单元加入。本课主例子先沿用已学的 `await`。

<span id="gather-remaining-time"></span>

## 补充：先等到一份完成，剩余的等待会重新计时吗？

不会。10、11 很快先后进入各自的 `sleep`，可以近似看作同时开始等待；它们仍在同一个事件循环线程中执行。

约 1 秒后，11 完成，调用方拿到 `done/pending` 并执行同步的 `print`。此时 10 通常还挂起在原来的 `sleep(2)` 上：它后面的 `return` 没有继续执行，但已经开始的等待时间仍在流逝。

若把主例子中等待 `pending` 的循环换成上一课学过的整组收集，也可以等完这些已有任务：

```python
remaining = await asyncio.gather(*pending)
```

以两份任务进入 `sleep` 的时刻近似作为 0 秒，忽略启动差距和调度开销：

| 时刻 | 发生什么 |
| --- | --- |
| 0 秒 | 10 开始等 2 秒；11 开始等 1 秒 |
| 1 秒 | 11 完成，`wait` 返回，调用方开始执行同步代码 |
| 1.5 秒 | 假设同步代码共耗时 0.5 秒，现在开始等待 `pending` |
| 2 秒 | 10 的等待到期；它获得执行机会后继续到 `return`，等待者取得结果 |

因此，后面的 `await task` 或 `await gather(*pending)` 等的是剩余工作，不会重新开始完整的 2 秒。这里 `pending` 只有 10，整组收集最终得到 `[10]`。

还要分清“等待时间到期”和“代码继续执行”：同步代码占用事件循环线程时，其他协程不能同时在这条线程上执行 Python 代码。即使 10 已经等够时间，也要等事件循环有机会调度它，才能执行后面的 `return`。

<span id="as-completed-results"></span>

## 后续单元 08：按完成顺序连续取得结果

旧版页面把 `as_completed` 和 `wait` 放在同一课。这里保留原来的材料与下载，正式阅读顺序是先完成第 08 单元的 Task 状态与结果，再进入[第 12 单元：asyncio.as_completed：按完成顺序取结果](../08-as-completed/)。

新增的问题是：**谁先完成，就先处理谁的结果，然后继续等下一份。**

```python
for completed in asyncio.as_completed(tasks):
    result = await completed
    print("result", result)
```

这里的 `completed` 是取得下一份完成结果的等待入口。第一次 `await completed` 在本次实验中取得 11，下一次取得 10；不是按 `tasks` 列表顺序收取。

下面是保留的完整实验，独立运行时会重新创建同样的两份任务：

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

[下载 as_completed.py](as_completed.py)。一次运行的输出为：

```text
result 11
result 10
```

这里使用 Python 3.12 的普通 `for` 写法，每次通过 `await completed` 取得结果。

| 入口 | 交给调用方什么 |
| --- | --- |
| `wait(..., FIRST_COMPLETED)` | 已完成和未完成的两组任务，后续怎样处理由调用方安排 |
| `as_completed(tasks)` | 逐个等待完成结果的入口，方便循环处理每一份结果 |

## 回到 Slime：先接回完成集合，再继续处理样本

下面保留教程绑定的 Slime 固定快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，与三库 API 统计所使用的新快照分开记录。

`generate_rollout_async` 已经把生成任务放入 `state.pendings`，然后用 `wait(..., FIRST_COMPLETED)` 接回完成集合，并把尚未完成的集合保存回 `state.pendings`。拿到的 Task 随后才被读取为样本组 `group`。本课先对照前两步，`.result()` 的完整边界在后续单元展开。

<details>
<summary>展开 Slime 源码：generate_rollout_async</summary>

{{< source-reference id="source-1" >}}

</details>

评测分支 `eval_rollout_single_dataset` 用 `as_completed` 连续收取已完成结果，对应第 12 单元。

<details>
<summary>展开 Slime 源码：eval_rollout_single_dataset</summary>

{{< source-reference id="source-2" >}}

</details>

{{< python-async-coverage lesson="04-results" >}}

语义核对：[Python 3.12：wait](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.wait) · [as_completed](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.as_completed)。`wait` 省略 `return_when` 时默认等整组完成；本课主例子明确指定 `FIRST_COMPLETED`。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：06 · gather：等待一组任务，收集一组结果](../05-gather/) · [下一节：08 · done、result、exception：读取 Task 的状态与结果](../07-task-results/) · [完整学习路线](../learning-route/)
