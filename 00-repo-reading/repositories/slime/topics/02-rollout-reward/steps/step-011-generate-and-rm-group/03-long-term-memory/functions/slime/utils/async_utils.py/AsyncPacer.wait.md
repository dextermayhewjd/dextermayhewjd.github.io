# AsyncPacer.wait

- Step 011 继承：来自 [Step 010 · 02-short-term-memory](../../../../../../step-010-generate-and-rm/02-short-term-memory/functions/slime/utils/async_utils.py/AsyncPacer.wait.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- 源码定位：[slime/utils/async_utils.py:24–31](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/async_utils.py#L24-L31)，辅助回调 `_release` 在 33–42 行。
- 首次接触：Step 010，2026-10-25 讨论分批启动；2026-10-26 先建空白文件，本轮按用户指定展开。
- 最近认识更新：2026-10-26，用户已表达先创建 Future 的初步理解，并询问入队时机、loop 控制数量与样本如何集中。入队、共享队列及批次范围的解释仍待反馈。

调用位置：[generate_and_rm](../../rollout/sglang_rollout.py/generate_and_rm.md#generation-admission) 已取得 semaphore 名额 → **本方法** → 返回父函数 `333` 行的中止检查。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据当前调用、固定源码及局部实验整理，作为理解参考。

1. **使用场合**：当前生成任务已经取得一个并发名额，但大量任务同时往下执行会带来集中调度压力，因此先经过共享 pacer 分批放行。

2. **具体内容**：取得当前事件循环，为这次调用创建 Future 并加入等待队列；若尚未安排放行，就登记 `_release` 回调；当前任务等待自己的 Future。回调每次取出至多 64 个队列项，将其中未完成的 Future 设为完成，有剩余则稍后继续。

3. **建议构建的心智模型**：

   > 每个调用者先留下一个“等我放行”的 Future；pacer 按批次完成这些 Future，让对应任务继续。它控制继续执行的节奏，不等待上一批生成结束，也不归还 semaphore 名额。

4. **调用代码**：

   ```python
   await state.semaphore.acquire()       # 当前任务已取得名额
   try:
       await state.generation_pacer.wait()
       if state.aborted:                # wait 返回后继续到这里
           sample.status = Sample.Status.ABORTED
           return sample
       ...  # DP 上下文、生成调用与等待
   finally:
       state.semaphore.release()
   ```

## 本场景的输入与输出

**输入**：隐式 `self` 是 `state.generation_pacer`，由 `GenerateState.__init__:98` 创建的 `AsyncPacer()`。没有显式参数，不接收 Sample。当前任务已取得 semaphore 名额，等待期间仍持有它。

| pacer 字段 | 保存什么 |
| --- | --- |
| `pending` | `deque`，每项是一次 wait 调用创建的 Future；不是 Sample 或 Task 列表 |
| `scheduled` | 是否已经安排了放行回调链；初始为 False，不是手动暂停开关 |

**输出**：正常返回 `None`；本函数没有显式 return。原来的生成任务继续执行 `state.aborted` 检查，Sample 在本方法里不改变。中间产生的 Future 用于等待通知，并不作为返回对象交给父函数。

### 1. 登记当前调用，并等待通知（24–31）

下面是完整的 wait 方法：

```python
async def wait(self):
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    self.pending.append(future)
    if not self.scheduled:
        self.scheduled = True
        loop.call_soon(self._release)
    await future
```

- 每次调用创建自己的 Future，加入同一个 pacer 的队尾。
- 当前没有放行安排时，设置 `scheduled = True`，用 `call_soon` 请事件循环稍后调用 `_release`。这里没有同步执行 `_release()`，也没有创建新的生成 Task。
- 后续调用看到 `scheduled` 已为 True，只登记自己的 Future，不重复启动回调链。
- `await future` 等到这份 Future 完成；挂起的是当前生成任务，事件循环仍可执行回调和其他任务。

### 2. 回调完成 Future，使等待者能够继续（33–42）

`_release` 由事件循环调用，不是 wait 用普通函数调用直接进入。这里按本方法的必要辅助说明，暂不单独建卡。

```python
def _release(self):
    for _ in range(min(64, len(self.pending))):
        future = self.pending.popleft()
        if not future.done():
            future.set_result(None)
    if self.pending:
        asyncio.get_running_loop().call_later(0.001, self._release)
    else:
        self.scheduled = False
```

- 一次回调最多取出 64 个队列项；正常未取消的场景下，对应至多 64 个等待者被放行。
- `future.set_result(None)` 将 Future 设为完成，等待它的任务随后有机会恢复。它不直接执行这份任务后面的生成代码。
- 队列仍有等待项时，设置约 1 毫秒延迟的下一次回调；实际执行时刻取决于事件循环调度，不保证精确间隔。
- 队列清空时，`scheduled` 恢复 False，后续新调用可以再次启动回调链。

**`AsyncPacer._release` 完成等待凭据；`Semaphore.release` 归还并发名额。它们操作的对象不同。**

### 3. 回到原来的生成任务

```text
当前任务：wait → 建 Future、入队 → await Future ───────→ 返回 None → aborted 检查
事件循环：                  call_soon → _release → set_result(None)
```

生成任务恢复后仍持有先前取得的 semaphore 名额。后续批次不检查上一批是否已生成完；因此“每批 64 个”不是“最多同时生成 64 个”。并发数量上限仍由外层 semaphore 控制。

### 入队时机、共享队列与批次大小

`create_future()`、`pending.append(future)` 与安排回调的代码之间没有 await。当前任务运行到 wait 后，先连续创建 Future、立即入队，再走到 `await future` 交还控制；不会先等事件循环检查 pending、批准入队。这里的 pending 是 AsyncPacer 自己的 deque，不是事件循环的内部队列。

多个调用者能在一起排队，是因为同一进程内的生成任务通常取得同一个 GenerateState，并使用其中同一个 generation_pacer。调用者陆续执行 wait，就把各自的 Future 加到同一队列。样本本身仍由各自的生成任务持有。

上游已有一组输入 group；当前所选的新 Sample 路径由 `generate_and_rm_group:417–427` 为各个样本创建 Task，最后用 gather 等待结果：

```python
# 教学裁剪：省略已完成列表、采样参数与其他准备
for idx, sample in enumerate(group):
    tasks[idx] = asyncio.create_task(generate_and_rm(...))
results = await asyncio.gather(*tasks.values())
```

这一处只补来源关系，不展开上游调度。group 是调用方已传来的样本集合；pacer 的一批是当时已在 pending 中的一部分 Future，两者不必一一对应，也不保证同组任务一起开始。

| 数量问题 | 谁决定 |
| --- | --- |
| 同时有多少任务占用生成名额 | semaphore 初始化的容量，等待 pacer 时也占名额 |
| 一次回调取出多少等待项 | `min(64, len(self.pending))`，不等队列凑满 64 |
| 输入组里有多少 Sample | 上游传入的 group；不是 loop 临时把样本合成组 |

例如回调执行时只有 3 个正常等待项，就处理这 3 个；有 100 个，则这次最多处理 64 个，其余安排后续回调。它让任务分批有机会继续，不承诺任务在同一物理时刻执行，也不把多个样本合成一次模型请求。

### 局部运行证据

2026-10-26，从固定本地源码原样提取 AsyncPacer 类，在 Python 3.12.3 中运行 130 个 wait 调用；仅在子类回调外记录每批队列减少量，不改原实现。每个任务离开 pacer 后等待同一个尚未打开的 Event，以观察前批任务未完成时后批能否继续。

```text
Release batches: [64, 64, 2]
wait() returned None: 130 tasks
Tasks still awaiting downstream gate: 130
Pending: 0 ; scheduled: False
```

这是本地控制流程实验，不含真实生成、网络、SGLang 或沙箱；130 是实验设置，不是当前 Slime 并发配置。它验证正常批次与后续任务仍在运行的关系，不是性能测试或实际延迟保证。

## 我的直接表述（原话）

此前提问：

> 然后这里的state generation pacer wait 是什么呢?

本轮指定：

> 好的那么现在看一下这里的generation pacer wait的部分吧

此前的 Future、回调与放行解释由助手提供。随后用户给出以下初步理解与疑问：

> 好的 我简单理解是这里的在一开始会创建一个future
> 然后这里如果在这个loop能够轮换到这里的pending的部分才考虑到底是否需要把这个futrue加入进去？
> 但是问题变成了 这个loop到底控制多少个以及如何让这些sample集中到一起
> 一轮一起跑呢？

“先创建 Future”是用户已表达的关系；其余关于立即入队、共享队列和批次边界的校准由助手补充，尚待反馈。

## 尚不清楚

- 已初步表达创建 Future；立即入队与事件循环调度的区别、多个任务如何共享 pending 尚待反馈。
- `scheduled` 的作用与“等待上一批结束”的区别尚待反馈。
- 取消后队列项的处理、真实事件循环延迟及实际吞吐影响未展开。

<details>
<summary>来源、版本与书面依据</summary>

- 上游来源回查：[generate_and_rm_group:417–427](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L417-L427)；[GenerateState 缓存实例](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/misc.py#L62-L76)。
- 固定源码：Slime `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，[类与完整方法](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/async_utils.py#L8-L42)、[对象创建](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L95-L98)、[父函数调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L329-L351)。
- Python 官方文档：[call_soon](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.call_soon)、[call_later](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.call_later)、[Future.set_result](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.Future.set_result)。在线文档随维护版更新，本地实验使用 Python 3.12.3。
- 形成过程：[Step 010 · 展开 pacer.wait](../../../../../../step-010-generate-and-rm/04-flow.md#generation-pacer-wait-reading)。

### 书上怎么说

await 的操作对象需要可等待。[依据 A] 书中同节将 asyncio.Future 列为可等待对象的例子。

### 我的判断（本书未覆盖）

本例用独立 Future 连接“调用者等待”与“回调放行”，每批最多取 64 项、下一批使用 0.001 秒延迟。这些是 Slime 源码的设计，不是书中规定的参数。

### 依据 A

- 《Fluent Python》第 2 版，第 21 章，New Concept: Awaitable；锚点 `new-concept-awaitable`。
- 英文 `corpus/en/ch21.md:203–228`；中文 `corpus/zh/ch21.md:166–187`，21.4 新概念：可异步调用对象。
- 原文：“The `for` keyword works with iterables. The `await` keyword works with awaitables.”
- 对照：“`for` 关键字处理可迭代对象，`await` 关键字处理可异步调用对象。”
- 版本：书籍基于 Python 3.10，本地实验为 Python 3.12.3。

</details>
