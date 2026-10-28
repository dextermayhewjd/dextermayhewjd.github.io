# AsyncRolloutWorker._make_done_cb

- 源码定位：[fully_async_rollout.py:246–275](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L246-L275)，由助手核对，固定版本 `18868a79`。
- 首次接触：Step 012 作为注册调用定位；2026-10-26 在 Step 013 确认独立阅读。
- 最近认识更新：2026-10-26，用户已表达“完成的 Task 作为 done_task，取 result 后放入 output_queue”，并指出队列属于 worker、存在 prepare_retry_group 分支；队列创建位置与分支触发条件由助手核对补充。返回函数的细节尚未复述。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_loop 刚为一组输入创建 Task，需要安排它结束时怎样交付结果。Task 结束后，生成结果仍需送入 output_queue，才能由上层取组；本函数为这次任务准备对应的完成处理函数。
2. **具体内容**：外层接收 gid 与 input_group，准备重试背景并返回内层函数 _cb。任务结束后，事件循环调用这个 _cb；本轮正常路径读取结果，再把 (gid, result) 放进同一个 worker 的 output_queue。
3. **建议构建的心智模型**：

   > 给每组生成任务配一份“完成后的交付办法”，按两次函数调用理解：
   >
   > ```text
   > 创建并返回回调：_loop 调用 _make_done_cb
   >   → 准备 retry_group → 返回 _cb → 调用方登记到 Task
   >
   > 任务结束后执行回调：事件循环调用 _cb(done_task)
   >   → 读取 result
   >   ├─ 有 ABORTED / PENDING → 整理重试组，交回 data_buffer
   >   └─ 未命中上述状态      → 将 (gid, result) 放入 output_queue
   > ```
   >
   > _make_done_cb 返回函数；_cb 的结果交付通过队列或输入源完成，返回值是 None。

4. **调用代码**（_loop:222）：

   ```python
   task.add_done_callback(self._make_done_cb(gid, group))
   ```

## 本场景的输入与输出

**教学构造，静态推导**：gid=7，input_group 有两个输入 Sample；组级生成正常返回 result_group。用对象名表示样本，不展开已有 Sample 字段。结果可能包含生成器返回的分段列表，本方法正常入队时保留其结构，不负责压平。

| 阶段/对象 | 输入 | 返回值或副作用 |
| --- | --- | --- |
| 创建并返回回调：_make_done_cb | self、gid=7、input_group | 返回一个 _cb 函数；此时尚未因这个任务写入结果队列 |
| 任务结束后执行回调：_cb | asyncio 传入已结束的 done_task，其正常返回值为 result_group | output_queue 新增 (7, result_group)；_cb 返回 None |

gid 来自 _loop 的局部计数，不是 Sample.index。input_group 在实际外层函数中用于准备重试背景；它不是稍后从 done_task 取出的结果。

<a id="compact-skeleton"></a>

### 整体小骨架：创建并返回回调 → 任务结束后执行回调

这是 _make_done_cb 自身的完整处理骨架，供先连起整体流程。教学剪枝：省略类型注解、Task 取消/异常、返回类型检查，以及重试提交的异常包装；保留重试输入、两个业务去向和 return _cb。具体复制与 helper 内部暂时留白。

```python
def _make_done_cb(self, gid, input_group):
    # 创建阶段：准备重试输入
    retry_group = [sample if isinstance(sample, list) else copy.deepcopy(sample) for sample in input_group]

    def _cb(done_task):
        # 执行阶段（Task 已结束）：取结果；异常与类型检查暂时折叠
        result = done_task.result()

        if any(s.status in (Sample.Status.ABORTED, Sample.Status.PENDING) for s in iter_samples(result)):
            self.data_buffer.add_samples([prepare_retry_group(retry_group, result)])
            return

        self.output_queue.put((gid, result))

    # 创建阶段：交出函数，供调用方登记
    return _cb
```

- **创建并返回回调**：准备 retry_group，定义 _cb，最后 return _cb；调用方用 task.add_done_callback(...) 登记这个函数。
- **任务结束后执行回调**：_cb 接到 done_task，读取 result；有 ABORTED/PENDING 时交回 data_buffer 后返回，否则写入 output_queue。

两阶段对应两次函数调用：_loop 先调用 _make_done_cb，事件循环在 Task 结束后调用 _cb。return _cb 属于第一阶段，内层函数体属于第二阶段；两者之间没有固定的等待时长。下面的①与②沿用这两个阶段。[骨架形成过程](../../../../../04-flow.md#step013-parent-skeleton-correction) · [阶段名称澄清](../../../../../04-flow.md#step013-explicit-callback-phases)。

<a id="phase-1"></a>

### ① 创建并返回回调：_make_done_cb

本段看外层返回什么、调用方怎样登记它；[初次观察过程](../../../../../04-flow.md#step013-return-callback-reading)。

以下保留外层真实结构，仅用省略号折叠内层函数体。retry_group 的复制先知道用途，不展开机制。

```python
def _make_done_cb(self, gid: int, input_group: list[Sample]):
    retry_group = [sample if isinstance(sample, list) else copy.deepcopy(sample) for sample in input_group]  # [1a]

    def _cb(done_task: asyncio.Task) -> None:
        ...

    return _cb  # [1b]
```

- **[1a]** 为可能的重试保留输入背景；正常结果的交付先不使用这一分支。
- **[1b]** 交出 _cb 函数本身，没有写成 _cb(...)，因此这里没有调用内层函数。

把调用处等价拆开阅读（新增 callback 仅是教学变量，原代码是一行）：

```python
callback = self._make_done_cb(gid, group)
task.add_done_callback(callback)
```

第一次调用准备函数，第二次调用登记函数。_cb 后续由事件循环调用；即使 Task 在登记时已经结束，回调也通过调度执行，不是这行代码直接调用 _cb。

<a id="phase-2"></a>

### ② 任务结束后执行回调：_cb

教学裁剪：仅保留内层正常路径，省略异常、类型检查与 ABORTED/PENDING 分支。前提是组级生成成功返回 list，成员没有待处理或中止状态。

```python
def _cb(done_task: asyncio.Task) -> None:
    result = done_task.result()                 # [2a]
    self.output_queue.put((gid, result))        # [2b]
```

- **[2a]** done_task 是 asyncio 传入的原 Task；这里读它已经产生的返回值，不再启动生成，也不需要再 await。失败状态如何读取留给之后的分支。
- **[2b]** 以 (gid, result) 为一个队列元素交出整组结果；稍后由 [get_completed_groups](AsyncRolloutWorker.get_completed_groups.md) 领取。

_loop 从 active_tasks 移除完成 Task 与这里保存业务结果是两件事。回调不直接调用消费方法，也不在这里重新评分。

**output_queue 的来路**：它在 AsyncRolloutWorker.__init__:102 中创建，是当前 worker 持有的 queue.Queue；当前 _cb 通过 self 使用这个已有对象。[类卡中的最小来源](../../../../classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md#output-queue-origin)。

<a id="retry-branch-boundary"></a>

**按当前追问补充：正常结果与重试结果的去向。** 以下是实际分支的节选，省略重试提交的异常包装；先只看条件与去向，不展开 prepare_retry_group 内部。

```python
if any(s.status in (Sample.Status.ABORTED, Sample.Status.PENDING) for s in iter_samples(result)):
    self.data_buffer.add_samples([prepare_retry_group(retry_group, result)])
    return

self.output_queue.put((gid, result))
```

- 返回的 Sample 中有 ABORTED/PENDING：prepare_retry_group 整理可重试的组，add_samples 把它交回输入源，return 结束本次回调。
- 返回的 Sample 没有这两种状态：走原来的正常路径，结果进入 output_queue。
- 判断对象是返回的 Sample 状态；Task 已经返回结果也可能走重试分支。重试 helper 的输入输出在此定位；异常、取消与保存输入的复制细节继续留白。


<a id="prepare-retry-group-skeleton"></a>

<details>
<summary>prepare_retry_group 的按需参考</summary>

当前只把它作为“整理重试组并返回”的调用。此前误展开的[局部实现与例子](../../../../../references/prepare-retry-group-before-target-correction-2026-10-26.md)保留在参考中；用户要求的小骨架是本卡上方的 _make_done_cb 整体流程。

</details>

## 我的直接表述（原话）

用户已指定本步阅读这两个方法；范围确认原话见[Step 013 的形成过程](../../../../../../step-013-completed-group-handoff/04-flow.md#step013-start)。随后明确追问用途：

> 这一个make done cb是用来干嘛的 我很想要知道

随后对用途的直接理解：

> 我可以简单理解为
> 这里是通过在task中加一个done callback 
> 这样子能够确保这个任务完成了之后会有人把他们作为结果消费掉
> 是我对于这一部分的理解

[用途解释过程](../../../../../04-flow.md#step013-callback-purpose)和[本轮边界校准](../../../../../04-flow.md#step013-handoff-versus-consumption)保留上下文。用户已说清登记回调与完成后处理的联系；“确保消费掉”是原话，正常结果入队与之后实际消费的区别由助手补充，尚待用户确认。

用户随后进一步表达正常路径、队列归属和分支观察：

> 好的 我差不多理解了
> 首先这里的内容是asyncio的 task 作为done task
> 然后通过获得这样子done task的result
> 放进这里的output queue 里面
>
> 然后这里的outputqueue也是和之前说的一样 
> 是一个外来的数据结构对吗？
> 也就是在asyncrolloutworker中的outputqueue
> 不在当前的这个make done cb内部
>
> 然后这里其实是有一个分支的
> 就是这里prepare retry group是我的理解

[本轮核对](../../../../../04-flow.md#step013-queue-origin-and-retry)将用户已表达的关系与助手补充的创建位置、分支条件分开保存。

用户在阶段表述统一后给出总体反馈，并要求接续下一函数：

> 好的 我差不多理解了
> 那么考虑一下下一个部分吧
> 这里处理了make done cb之后我们应该看哪一个函数呢？

这是对本函数的总体理解反馈；下方具体未知保留。[下一处入口](../../../../../04-flow.md#step013-next-get-completed-groups)。

## 尚不清楚

- 用户已说明正常结果从 done_task.result() 进入队列；get_completed_groups 怎样领取结果尚未实际展开。
- 尚待反馈：返回 _cb、登记 _cb 与执行 _cb 三个时刻的区别。
- 已定位重试触发条件和两条去向；用户要求的小骨架属于 _make_done_cb，现已补在本卡开头。prepare_retry_group 的内部规则仅保留按需参考，retry_group 的保存方式、分段会话与异常/取消处理仍未展开。
- _cb 如何继续使用外层的 self/gid 有[按需语言参考](../../../../../references/python-callback-notes.md)，不作为当前主线的前置章节。

<details>
<summary>来源、验证与完整例子</summary>

- 注册：_loop:214–223；外层与回调：246–275；消费：get_completed_groups:147–161。
- [完整源码摘录](../../../../../references/source-excerpts.md)保留所有被折叠分支。
- [固定版本证据](../../../../../references/source-evidence.json)；本例为静态数据交接推导，未运行真实 worker、模型或队列服务。
- [原始 Step 013 过程](../../../../../../step-013-completed-group-handoff/04-flow.md#step013-start)。语言层依据来自本机标准库参考实现及《Fluent Python》第 2 版，见按需参考。

</details>
