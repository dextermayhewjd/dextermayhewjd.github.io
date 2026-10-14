---
title: "17 · asyncio.Semaphore：限制同时进入的工作"
description: "从创建 Semaphore 对象、传给任务，到 async with 管理进入与退出，再展开同一对象的 acquire 和 release 方法，理解许可怎样限制并发。"
weight: 170
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. asyncio.Semaphore：任务都已安排，怎样限制同时进入的数量？

前面已经会用 `create_task` 安排工作，用 `gather` 收集结果，也知道出错、取消和超时后要处理收尾。现在多一个要求：**可以提前安排 5 份工作，但某段请求代码最多只允许 2 份工作同时进入。**

只把 5 个 Task 交给 `gather`，它会等待并收集结果，并没有设置“同时最多进入 2 份”的规则。逐份直接 `await` 可以把数量压到 1，但也没有表达“最多允许 2 份”的要求。

本课使用 Semaphore 管理许可。按这条顺序读：**先创建共享对象 → 把它交给任务 → 在任务内部用它管理进入和退出 → 最后展开取得、归还许可的方法。**

## 2. Semaphore / create_task：先创建共享对象，再把它交给任务

先分清主程序中的两步：

1. **`semaphore = asyncio.Semaphore(2)` 创建对象。** `Semaphore` 是类型名，变量 `semaphore` 保存这次创建的对象；这个对象初始有 2 个可用许可。
2. **`asyncio.create_task(generate(10, semaphore))` 安排任务，并把这个对象交给它。** 和之前一样，`generate(...)` 先产生协程对象，`create_task` 安排它运行。新增的参数只是让 `generate` 内部也能使用这个 Semaphore 对象。

后面的任务 11–14 也传入同一个 `semaphore`，因此它们共享一份许可数量。这里不是每创建一个 Task 就另建一个 Semaphore。

**做到这一步，还没有取得许可。** 把对象传给函数，不会自动限制这个函数；任务运行后，还需要在函数内部实际使用它。

<span id="semaphore-permits"></span>

## 3. async with semaphore：在任务内部取得许可、退出时归还

`generate` 收到对象以后，在需要限制的代码外面写 `async with semaphore:`。

沿用第 04 课学过的进入、执行、退出结构，这个 Semaphore 对象为它提供的规则是：

1. **进入前取得一个许可。** 有许可才进入块内，没有就等待；等待时可以让其他任务运行。
2. **进入后执行块内代码。** 即使在块内 `await`，只要还没有退出，就仍然持有许可。
3. **退出时归还许可。** 其他等待者随后有机会取得许可、进入自己的代码块。

这就是主程序创建的对象和函数内部 `async with` 的连接：**传进来的同一个 `semaphore`，在这里被用来管理进入与退出。** 取得、归还具体对应的方法，等看完运行过程后再展开。

### 3.1 create_task / async with：把外部安排和内部限流放在同一份例子里

沿用前面的 `generate`、异步等待和 `finally` 清理打印。先看 `exercise` 创建并传入对象，再看 `generate` 如何使用收到的对象。这是独立标准库实验，用短暂等待代替真实请求；Slime 的原始用法放在文末。

先预测：5 个任务都会出现 `waiting` 吗？任务 12 会在什么时候打印 `entered`？

```python
import asyncio


async def generate(rollout_id, semaphore, fail=False):
    print("waiting", rollout_id)
    async with semaphore:
        print("entered", rollout_id)
        try:
            await asyncio.sleep(0.1)
            if fail:
                raise ValueError(f"generation {rollout_id} failed")
            print("finished", rollout_id)
            return rollout_id
        finally:
            print("cleanup", rollout_id)


async def exercise():
    semaphore = asyncio.Semaphore(2)
    tasks = []
    for rollout_id in range(10, 15):
        tasks.append(asyncio.create_task(generate(rollout_id, semaphore)))
    print("tasks scheduled", len(tasks))
    print("results", await asyncio.gather(*tasks))


if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载 example.py](example.py) · 运行：`python3 -W error example.py`。本课使用 Python 3.12。

循环只是把编号 10–14 的工作逐一创建成 Task，并存进 `tasks`；`gather(*tasks)` 等待这些已创建的任务。`fail=False` 沿用前面失败实验的开关，主例子全部正常完成，后面的补充实验才打开它。

### 3.2 Semaphore(2)：观察 5 个任务怎样分批进入

本机 CPython 3.12.3 默认调度下的一次实际输出：

```text
tasks scheduled 5
waiting 10
entered 10
waiting 11
entered 11
waiting 12
waiting 13
waiting 14
finished 10
cleanup 10
finished 11
cleanup 11
entered 12
entered 13
finished 12
cleanup 12
finished 13
cleanup 13
entered 14
finished 14
cleanup 14
results [10, 11, 12, 13, 14]
```

### 3.3 async with semaphore：沿这次输出走一遍

沿这次输出看执行顺序：

1. **先创建 5 个 Task。** `tasks scheduled 5` 表示工作已经安排；`Semaphore(2)` 没有把 Task 数量变成 2。这里没有在创建循环中 `await`，随后等待 `gather` 时，其他任务得到运行机会。
2. **任务 10、11 各取得一个许可，进入代码块。** `entered` 写在 `async with semaphore` 内部，只有成功取得许可之后才会打印。它们在 `await asyncio.sleep(...)` 处挂起时，仍然持有许可。
3. **任务 12–14 已经开始运行，但暂时进不去。** 它们打印了块外的 `waiting`，随后在 `async with` 的进入阶段等待可用许可；等待期间可以让事件循环运行其他任务。
4. **任务 10、11 先清理，再离开受限代码块。** 正常返回前，先执行函数里写出的 `finally`，打印 `cleanup`；然后 `async with semaphore` 的退出过程归还许可。剩余任务才有机会取得许可并进入。
5. **全部工作结束后，gather 收齐结果。** 最后仍然得到 5 个结果，顺序与传入的 Task 顺序一致。

**这里限制的是“已经进入、还没退出代码块”的任务数，包括块内正在 `await` 的任务。** 不是要求这 2 个任务同时执行 Python 指令，也不是限制整个程序只能存在 2 个 Task。

这次输出中，任务 12 的 `entered` 出现在前面任务的 `cleanup` 之后。具体打印如何交错不作为调度保证；应检查的规则是：在正常配对取得、归还许可的前提下，受限区域里最多有 2 份工作。

<span id="semaphore-acquire-release"></span>

## 4. async with 与 acquire / release：两种等价的许可管理写法

现在已经看到 `async with semaphore` 会取得、归还许可。**它与手动写出的 `await semaphore.acquire()`、`try/finally`、`semaphore.release()`，是两种等价的许可管理写法。** 下面把完整的取得与归还过程放在一起对照。

只保留块内的一次等待，看许可管理这一层。两段都是协程内部的代码片段：

```python
async with semaphore:
    await asyncio.sleep(0.1)
```

等价的手动写法是：

```python
await semaphore.acquire()  # 进入前：取得一个许可，没有就等待
try:
    await asyncio.sleep(0.1)
finally:
    semaphore.release()  # 退出时：归还许可
```

**这两段解决同一个问题，选一种即可。** 单独的 `await semaphore.acquire()` 只负责取得许可，不会自动完成退出时的归还；等价关系包含后面的 `try/finally` 和 `release()`。主例子已经用了 `async with semaphore`，无需再额外添加一次 `acquire()` 和 `release()`。完整例子里其他块内语句，也仍然放在对应的 `try` 内。

| 操作 | 在这里做什么 | 返回与等待 |
| --- | --- | --- |
| `await semaphore.acquire()` | 取得一个许可；有许可时可立即取得，没有时等待 | 成功取得后返回 `True` |
| `semaphore.release()` | 归还一个许可，让等待者有机会继续 | 普通方法，不写 `await`；返回 `None` |

`acquire()` 前面写 `await`，因为没有许可时可能需要等待；`release()` 只是归还许可，不需要等待。

**取得许可在这个 `try` 之前。** 只有取得成功后才进入块内工作，退出时才负责归还；不要还没取得许可就随意 `release()`。普通 Semaphore 允许多次额外释放，因此本课的“最多 2 个”依赖正确配对，`async with` 能减少漏还或多还的机会。

### 4.1 Semaphore / TaskGroup：同样写 async with，具体职责由对象决定

第 05 课已经用过 `async with asyncio.TaskGroup()`。两者都使用进入和退出的语法，但放进去的对象不同，承担的职责也不同：

| 写法 | 进入与退出的具体职责 |
| --- | --- |
| `async with asyncio.TaskGroup() as group` | 管理登记在组内的 Task；退出时等待它们结束，必要时取消并收尾 |
| `async with semaphore` | 进入前取得许可，退出时归还许可；不会替你创建或等待一组 Task |

主例子里，`Semaphore` 管进入数量，`gather` 等全部结果，函数里的 `finally` 打印清理过程。三者各自承担一件事。

<span id="semaphore-cleanup"></span>

## 5. finally 与 Semaphore：出错、取消之后，许可还会归还吗？

### 5.1 ValueError：出错退出，下一份工作仍能取得许可

[下载 failure.py](failure.py)，和 `example.py` 放在同一目录后运行。它直接导入上面的 `generate`，把许可数改为 1：先运行会失败的任务 10，处理错误后，再运行任务 11。

```text
waiting 10
entered 10
cleanup 10
error generation 10 failed
waiting 11
entered 11
finished 11
cleanup 11
result 11
```

任务 10 已经取得唯一的许可。它抛出 `ValueError` 后，先执行自己的 `finally`，再由 `async with semaphore` 的退出过程归还许可，异常随后向外传播。外层处理错误后，任务 11 仍能进入，说明许可没有因错误而遗失。

### 5.2 Task.cancel：处理取消并退出，也会归还已取得的许可

[下载 cancellation.py](cancellation.py)，同样与 `example.py` 放在一起。它先安排任务 10，用已学的 `await asyncio.sleep(0)` 给任务进入并等待的机会，再调用 `cancel()` 并 `await` 收尾，最后运行任务 11。

```text
waiting 10
entered 10
cleanup 10
cancelled 10
waiting 11
entered 11
finished 11
cleanup 11
result 11
```

这次顺序是：

1. 任务 10 已取得许可，在块内的 `await` 处收到 `CancelledError`。
2. 本例没有在 `generate` 里捕获取消，跳过后面的正常工作，执行已进入的 `finally`。
3. 离开 `async with semaphore`，归还许可，再继续向外传播取消。
4. 调用方等到取消收尾后，任务 11 可以取得同一个许可。

因此，许可不是调用 `cancel()` 的瞬间归还的，而是在任务处理取消、退出受限代码块时归还。

如果任务还在等待许可就被取消，它尚未进入块内工作，也不会执行块内这个 `finally`。此时不能自己额外释放一个没有取得的许可。

<span id="semaphore-limits"></span>

## 6. Semaphore：带走三条结论，再做自查

1. **限制的是一段区域的同时进入数量。** 5 个 Task 可以全部创建，其中最多 2 个持有这个共享 Semaphore 的许可；块内 `await` 不会自动归还许可。
2. **创建、传入对象之后，还要在函数内部使用它。** `async with semaphore` 配对取得与归还，展开就是 `await acquire()` 与 `finally` 中的 `release()`，无需两种写法叠加。正常返回、出错或处理取消而退出时，都会归还已经取得的许可。
3. **范围和对象都要一致。** 需要受同一个上限约束的工作共用同一个 Semaphore，并放进它的代码块。块外工作不受这个上限约束；每个任务各建一个 Semaphore，也无法形成共同的上限。

试着回答：

1. 把 `Semaphore(2)` 改成 `Semaphore(1)`，Task 总数和结果数量分别是多少？同时进入的最大数量是多少？
2. 为什么任务 12 已经打印 `waiting`，却还没有打印 `entered`？
3. 主例子中的任务在 `sleep` 时是否占用许可？打印 `cleanup` 的 `finally` 和归还许可的操作，是同一件事吗？
4. 一份工作出错或被取消后，下一份为什么仍能进入？若取消发生在取得许可之前，又有什么不同？
5. 如果只把 `semaphore` 传给 `generate`，但函数里既不用 `async with`，也不调用取得许可的方法，还会自动限制进入数量吗？

<details>
<summary>查看自查解释</summary>

1. Task 和结果仍各有 5 份，同时进入的最大数量变为 1。可以沿 `entered` 计入、`cleanup` 计出，记录本例区域内的最大数量；它应与正确配对使用的许可上限一致。
2. `waiting` 在块外；它已运行到这里，但取得许可的过程还没有结束。
3. 仍占用许可。函数里的 `finally` 执行本例清理；随后退出 `async with`，由 Semaphore 的退出过程归还许可。
4. 已进入的工作退出时归还许可。尚未取得许可就取消，则未进入工作区域，无需调用方额外归还。
5. 不会。传递对象只让函数能够使用它；实际取得许可的动作，才会在没有许可时让任务等待。

</details>

下一课增加的问题是：**一边产生数据、一边消费数据，处理不过来时，数据怎样等待交接？** 见[18 · asyncio.Queue：让生产者与消费者交接数据](../07-queues/)。

{{< python-async-slime title="按需阅读：Slime 应用与本节源码位置" >}}

## GenerateState 与 generate_and_rm：找到共享许可和受限区域

主例子是独立标准库实验，不是 Slime 函数的裁剪实现。下面保留固定 Slime 快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的原始代码；本次已核对本地保存的连续源码和文件哈希。

1. **先找共享对象。** `GenerateState.__init__` 创建 `self.semaphore`。初始许可数由传入的 `concurrency` 或配置计算，后续工作使用同一个状态对象中的 Semaphore。

{{< source-reference id="source-1" >}}

2. **再找实际范围。** 进入 `generate_and_rm` 的生成阶段，输入是本次样本与生成参数。它先通过 `async with state.semaphore` 取得许可，再等待启动节奏、检查状态并等待生成调用。区块内的等待也占用许可；退出后才归还，随后继续处理样本并返回调用方。

{{< source-reference id="source-2" >}}

这里不只实际生成调用处于受限区域，前面的 `generation_pacer.wait()` 也在里面。区块之后的样本处理不再受这一段 Semaphore 限制。阅读真实代码时，要同时找到共享对象和代码块边界，才能说清“究竟限制了什么”。本课不展开节奏控制器和框架业务。

{{< python-async-coverage lesson="06-semaphore" >}}

语义核对：[Python 3.12 Semaphore、acquire 与 release](https://docs.python.org/3.12/library/asyncio-sync.html#semaphore)。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：16 · asyncio.shield：区分取消等待者与内部工作](../13-shield/) · [下一节：18 · asyncio.Queue：让生产者与消费者交接数据](../07-queues/) · [完整学习路线](../learning-route/)
