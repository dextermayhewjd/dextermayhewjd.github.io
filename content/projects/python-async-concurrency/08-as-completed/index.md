---
title: "12 · asyncio.as_completed：按完成顺序取结果"
description: "沿用两份已安排的任务，用 as_completed 逐份等待并处理结果，分清等待入口、返回值与剩余任务的责任。"
weight: 120
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. 取得一轮完成情况以后，怎样连续收取结果？

1. **前面已经会了：** 第 07、08 单元用 `wait` 取得完成情况，再读取 Task 的结果或异常；刚才的整组失败处理也明确了剩余任务的责任。
2. **现在多了一个要求：** 谁先完成，就先处理谁的结果；处理以后继续等下一份，直到这批结果收完。
3. **先看原来的办法：** `gather` 在全部正常完成后给出结果列表，列表按传入顺序排列。反复对剩余任务调用 `wait(..., return_when=asyncio.FIRST_COMPLETED)`，可以先处理每轮已完成的一批，再更新 `pending`；如果该轮有多份完成，`done` 是无序集合，不提供它们的先后次序。每轮的结果读取和剩余集合更新也需要自己组织。

这次只新增 **`asyncio.as_completed`**，让它提供逐份取得完成结果的等待入口。任务仍沿用第 03 单元的 `create_task` 提前安排；变化发生在结果收取阶段。

本课采用 **Python 3.12 的普通 `for` 加 `await`** 写法。后续单元再学习异步迭代，不把新版的 `async for` 写法作为这里的前置。

## 2. 沿用同一组任务，先预测谁的结果先被打印

`generate` 的行为没有变化：等待指定秒数，再返回编号。仍然先创建任务 10，再创建任务 11，输入列表也仍然是 `[task_10, task_11]`。

预测：任务 10 等 2 秒，任务 11 等 1 秒。下面会打印 `10 → 11`，还是 `11 → 10`？

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
        # completed 是等待下一份完成结果的协程对象，不是原来的 Task。
        result = await completed
        print("result", result)


if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载 example.py](example.py) · 运行：`python3 -W error example.py`。

本机 Python 3.12.3 的运行输出为：

```text
result 11
result 10
```

本次运行中，11 先完成，所以先取得 `11`。两份任务几乎同时完成时，不依赖它们有固定的先后次序；这里也不通过精确耗时证明调度规则。

<span id="as-completed-results"></span>

## 3. 沿执行过程看：for 取得入口，await 取得结果

1. **先安排两份任务。** 两次 `create_task` 已经把工作安排给事件循环。`tasks` 是保存两个 Task 的列表，顺序是 10、11；后面的循环不会重新启动它们。
2. **进入 `for`，取得第一个 `completed`。** 在本课写法中，`as_completed(tasks)` 返回一个迭代器，供普通 `for` 逐次取得协程对象。这个对象用于等待下一份完成结果；取得它本身不等于某个原始 Task 已经完成。
3. **执行第一次 `await completed`。** 如果还没有可取得的完成结果，调用方在这里挂起，事件循环可以推进两份任务。本次运行中，11 先返回，等待入口取得它的返回值，`result` 成为整数 `11`，随后打印。
4. **下一轮继续等待。** `for` 取得新的等待入口；第二次 `await completed` 取得另一份结果。本次运行中它来自任务 10，打印 `result 10`。10 的工作一直由事件循环推进，不会在这次 `await` 时重新开始等完整的 2 秒。
5. **收完这批结果，循环结束。** 主例子中两个任务都正常完成，两个等待入口都已被等待。`exercise` 随后结束。

如果某份结果在到达 `await completed` 之前就已可取得，这次等待可以直接返回，不需要再挂起。

这里逐个 `await` 的是**收取结果的入口**。两份工作在循环之前已经安排，所以逐份取值不会把工作改成“做完 10 才开始 11”。

| 名称 | 在本例中是什么 | 能怎样使用 |
| --- | --- | --- |
| `tasks` | 保存原始 Task 的列表 | 传给 `as_completed`，保留这批任务的引用 |
| `task_10`、`task_11` | 两个已安排的 Task | 使用前课的等待、状态检查与读取方法 |
| `completed` | 本轮取得的包装协程对象 | 用 `await completed` 等待并取得下一份完成结果 |
| `result` | 工作函数返回的整数 | 本例逐份打印；也可以在这里处理业务结果 |

**变量名叫 `completed`，不代表它是原来的 Task，也不代表它已经执行完。** 不要对它调用前课的 `.done()` 或 `.result()`。本课也没有一次返回一个结果数组：每次 `await completed` 取得一份结果。

## 4. 什么时候选择这种写法？

选择取决于你要怎样收取结果：

| 当前要求 | 可以选择的写法 | 调用方接下来处理什么 |
| --- | --- | --- |
| 全部正常完成后，一次收齐结果 | `await asyncio.gather(*tasks)` | 按传入顺序排列的结果列表 |
| 先拿到一轮完成与未完成的任务 | `await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)` | `done`、`pending` 两个 Task 集合 |
| 每完成一份，就收取并处理一份 | `for completed in asyncio.as_completed(tasks)`，循环内 `await completed` | 逐份取得的结果或传播的异常 |

例如，几份独立请求已经同时安排，谁先返回就先更新进度或保存它的结果，可以用本课模式。无需等待较慢的任务完成后，才处理已经完成的那份。

这个循环的输入是已经确定的 `tasks`，它不提供动态加入新任务的接口；持续补充任务的场景，需要调用方另外组织。

## 5. 有任务失败，或提前退出循环时呢？

### 5.1 预期的任务异常，在 await 处处理

第 08 单元已经看到：任务失败时，读取它的结果会抛出保存的异常。本课同样会在 **`await completed`** 处传播对应任务的异常。

如果沿用第 08 单元带 `fail` 参数的 `generate`，让 11 抛出 `ValueError`，而要求是“记录这份失败，继续收取其他任务”，可以将收取部分写成：

```python
for completed in asyncio.as_completed(tasks):
    try:
        result = await completed
    except ValueError as error:
        print("error", error)
    else:
        print("result", result)
```

`else` 属于普通 `try/except`：只有 `try` 没有抛异常时才执行，因此失败那一轮不会把不存在的新结果当成成功打印。

[下载完整失败实验 failure.py](failure.py)。它保留 10 等 2 秒、11 等 1 秒，只将 11 改为 `fail=True`，并采用上面的异常处理。运行输出为：

```text
error generation 11 failed
result 10
```

捕获并记录 11 的失败后，循环继续取得 10 的结果。这里只处理明确预期的 `ValueError`；是否继续收取取决于需求，不需要为了继续而忽略所有异常。

### 5.2 停止收取，不会自动停止剩余 Task

如果循环里执行 `break`，或者异常没有被处理而离开循环，**`as_completed` 不会因此自动取消其余任务**。只要事件循环仍在运行，已安排的任务仍可能继续推进；保存它们的 `tasks` 也还在。

如果希望剩余工作完成，调用方仍要继续等待并读取相应结果；如果希望停止剩余工作，就需要请求取消并等待收尾。后者已在第 09 单元讲过。本课的主例子选择完整收取，失败实验则处理预期异常后继续收取。

还要区分脚本结束：如果提前退出后连 `exercise` 也结束了，`asyncio.run` 的收尾会请求取消尚未完成的 Task。这是运行入口的收尾行为，不能据此认为 `as_completed` 在离开循环时取消了它们。

## 6. 带走三条结论，再做自查

重点是知道什么时候用这种模式，能分清对象和退出边界；不需要背每次打印的顺序。

1. **想逐份处理先完成的结果，可以用 `as_completed`。** 任务先安排，循环中逐份等待；它收取完成结果，不按输入列表的排列位置取值。
2. **在本课的普通 `for` 写法中，`completed` 是包装协程，`await completed` 才取得结果或传播任务异常。** 它不是原来的 Task，不能直接套用 `.result()`、`.done()`。
3. **收取方式与剩余任务的处理责任要一起考虑。** 可以在等待处处理预期异常后继续收取；提前退出循环时，调用方仍要决定怎样等待或停止剩余工作。

试着回答：

1. 把输入列表改为 `[task_11, task_10]`，会让 `as_completed` 改为按列表位置取结果吗？
2. 循环里的 `completed` 是原始 Task、最终整数，还是等待入口？用哪行代码取得整数？
3. 逐个执行 `await completed`，会让任务 10、11 改为依次开始吗？
4. 记录 11 的预期异常后仍想要 10 的结果，应继续循环，还是直接退出？如果直接退出，10 会被这个 API 自动取消吗？

<details>
<summary>查看自查解释</summary>

1. 不会。它按完成推进结果收取，不按列表的位置取值。本次实验中仍是 11 先返回；几乎同时完成的情况不依赖固定先后。
2. 是等待入口，在这里具体为包装协程对象；`result = await completed` 取得工作返回的整数。
3. 不会。两份任务在进入循环前已经由 `create_task` 安排；循环逐份收取它们的结果。
4. 可以在 `await completed` 周围捕获预期异常，然后继续循环。直接退出不会让 `as_completed` 自动取消 10，剩余工作的等待与收尾仍需要调用方负责。

</details>

到这里已经分别学会整组等待、失败收尾和按完成顺序收取结果。下一单元新增的问题是：**如果不愿一直等待，怎样为这次等待设置时限？** 继续阅读[13 · asyncio.wait_for：限制一次等待的时长](../10-wait-for/)。

{{< python-async-slime title="按需阅读：Slime 应用与本节源码位置" >}}

## 源码中的逐份收取发生在哪里

主例子与失败实验是独立标准库实验。下面保留旧课已核对的 Slime 快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，与三库 API 统计的新快照分开记录。

这里跟随评测函数 `eval_rollout_single_dataset` 的**结果收集阶段**：此前已经准备好 `tasks`，现在需要每完成一份就保存结果、更新进度。源码用 `for coro in asyncio.as_completed(tasks)` 取得等待入口，再用 `sample = await coro` 得到业务数据；它与主例子的 `completed → result` 是同一个关系。

本节只读这段交接：输入是任务集合，输出/副作用是向 `data` 加入样本并更新 `pbar`。首次样本日志、样本列表展开属于评测业务；读完返回评测函数的汇总流程，不在这里新增业务 API。

{{< source-reference id="source-1" >}}

{{< python-async-coverage lesson="08-as-completed" >}}

## 版本与语义核对

以 [Python 3.12 的 asyncio.as_completed 文档](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.as_completed)与本机 Python 3.12.3 `asyncio.tasks.as_completed` 实现核对：普通迭代得到协程对象，在等待处取得下一份完成结果或传播异常。本课不引入 `timeout` 参数。

《Fluent Python, 2nd Edition》21.3 的完成顺序描述也已对照本地中英镜像：英文短语 “in the order they are completed”（`en/ch21.md` 第 161 行），官方中文为“按照传入的协程完成的顺序”（`zh/ch21.md` 第 124 行）；对齐节锚点是 `an-asyncio-example-probing-domains`。这里只引用完成顺序，包装协程与实际等待行为按上述 Python 版本文档和实现说明。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：11.2 · ExceptionGroup / except*：读取任务组的错误](../11-exception-groups/) · [下一节：13 · asyncio.wait_for：限制一次等待的时长](../10-wait-for/) · [完整学习路线](../learning-route/)
