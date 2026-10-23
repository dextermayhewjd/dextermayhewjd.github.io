# BaseAdapter.finish_session

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../step-008-harness-communication/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/adapters/common.py:245–276](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L245-L276)，由助手核对。
- 首次接触：Step 3，2026-10-21 首次展开；此前仅在整体骨架中定位。
- 最近认识更新：2026-10-22，用户表示已大致理解本函数与 `get_trajectory` 的整体内容，准备收拢任务链路；具体的 token 拼接、分段和 mask 算法仍未逐段展开。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：Coding Agent 已结束，`generate` 已拿到评测奖励。在 `evaluation=False` 路径中，调用本函数把该会话已有的生成轨迹交成训练样本。

2. **具体内容**：先关闭会话入口并处理未结束的请求，取出会话的长度配置；把 `sid`、`base_sample`、`reward`、额外 metadata 与长度上限交给 `manager.get_trajectory`。拿到样本列表后，逐个解码样本尾部，补上 `response` 再返回。具体的 token、mask 与 logprob 组装由 manager 完成。

3. **建议构建的心智模型**：

   > `finish_session` 是一次会话的样本导出入口：收尾 → 委托 manager 把已有轨迹与奖励组织成样本 → 补上样本文本。
   >
   > `sid` 用来找到轨迹，`base_sample` 提供任务基础字段，`reward` 给出这次任务的评分。返回值是 `Sample` 列表；同一会话的记录在导出时被消费。

4. **调用代码**（[generate.py:237–245](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L237-L245)）：

   ```python
   samples = await state.adapter.finish_session(
       session_id,
       base_sample=base_sample,
       reward=float(reward),
       extra_metadata={
           "grading_solved": float(reward) == 1.0,
           "instance_id": instance_id,
       },
   )
   ```

## 本场景的输入与输出

教学构造：同一会话只有一轮“修复加法函数。”，已记录假设回复“已修复。”，评测奖励取 `1.0`。沿用前序的 Anthropic Adapter 场景，执行的是共同继承的本方法。本例没有在途请求、分叉或长度截断；它用于观察导出数据，不代表真实修复成功的任务。

**输入**：显式参数如下。`wait_timeout` 使用默认的 `5.0` 秒；它传给会话收尾，不是模型生成的超时参数。

```python
sid = "sid-demo"
base_sample = Sample(index=7, group_index=0, prompt="修复加法函数。", session_id=sid)
reward = 1.0
extra_metadata = {"grading_solved": True, "instance_id": "demo-1"}
```

还需要 `self` 中已经存在的状态：`self.store[sid].max_context_tokens = 4096`；`self.manager` 已通过 `record_turn` 保存本例的消息与下面这份生成记录。**轨迹不是从 `base_sample` 中取出的。**

```python
prompt_ids = [248045, 846, 198, 103833, 135998, 103733, 1710,
              248046, 198, 248045, 74455, 198, 248068, 198]
turn = TurnRecord(
    prompt_ids=prompt_ids,
    output_ids=[96221, 103833, 1710, 248046],
    output_log_probs=[-0.1, -0.2, -0.3, -0.4],
    finish_reason="stop",
    ill_formed=False,
)
```

token ID 来自本地 tokenizer 对构造文本的实际编码；logprob 是构造值。完整的消息输入与复核边界见折叠来源。

**输出**：返回 `[s]`，下面按字段展示唯一的 `Sample`（节选，省略默认字段）。

```python
s.index = 7
s.group_index = 0
s.rollout_id = 7
s.prompt = "修复加法函数。"
s.tokens = prompt_ids + [96221, 103833, 1710, 248046]  # 共 18 个 token
s.response_length = 4
s.loss_mask = [1, 1, 1, 1]
s.rollout_log_probs = [-0.1, -0.2, -0.3, -0.4]
s.reward = 1.0
s.response = "已修复。<|im_end|>"
s.status = Sample.Status.COMPLETED
s.metadata = {
    "grading_solved": True, "instance_id": "demo-1",
    "truncated": False, "use_tool": False, "ill_formed": False,
}
```

- `tokens` 包括初始 prompt 和后面的 response 区；本例的 `loss_mask`、`rollout_log_probs` 对齐后面 4 个 token。每个导出样本获得传入的完整 `reward`。
- 输出是新建的样本；`base_sample` 没有被原地填满，也不是所有字段都原样复制。例如本路径输出的 `s.session_id` 仍为默认 `None`；样本身份字段和 metadata 的具体组装由 manager 负责。
- 导出后，该 `sid` 的会话配置与 manager 轨迹被移除，`sid` 保留在关闭集合中；本例再次调用返回 `[]`。外层 `generate` 会处理空结果，并在非空样本上另补 `agent_exit_code`。

### 函数内部怎样完成这次导出

下面按真实顺序分三段。子函数先保留当前交接需要的合同，尚未独立展开的内部实现不写成已经读懂。

<a id="session-close-and-config"></a>

#### 1. 会话标识 → 收尾后的长度配置（261–263）

```python
await self.shutdown_session(sid, wait_timeout=wait_timeout)
session = self.store.pop(sid, None)
max_sample_tokens = int(getattr(session, "max_context_tokens", 0) or 0) if session is not None else 0
```

- **`sid` → 收尾**：`shutdown_session` 标记关闭并处理已登记的请求 Task；本例没有在途请求，可直接返回。等待、超时取消与跨循环交接已展开到[独立函数卡片](BaseAdapter.shutdown_session.md)，那里的有任务示例用于补看本例未经过的分支。
- **为什么在导出前做**：进行中的 `_run_turn` 可能还会调用 `record_turn` 写入轨迹。先处理这些请求，再进入下面的配置移除和轨迹导出，才能在正常收尾路径中完成交接。`shutdown_session` 自身不移除 `store` 中的配置或 manager 中的轨迹树。
- **`store` → `session`**：`self.store.pop(sid, None)` 移除 `sid` 对应的字典条目，同时把原来的 `Session` 对象返回给局部变量 `session`。这个对象含 `sampling_defaults` 与 `max_context_tokens`，没有逐轮轨迹；对象仍可经 `session` 读取，移除登记不等于立刻销毁对象。若条目不存在，则得到 `None`。
- **`session` → `max_sample_tokens`**：本例得到 `4096`，用于下一段限制导出样本的 token 总长度。缺少会话或未配置时传 `0`，表示不在此处施加该长度上限。

这里与后续的轨迹移除是两件事：

| 操作 | 操作之后，本例的数据在哪里 |
| --- | --- |
| 本段 `self.store.pop(sid, None)` | 配置对象由 `session` 接住；轨迹树仍在 `self.manager` 中 |
| 后续 `get_trajectory` 内的 `_trees.pop(sid, None)` | 已导出的数据由 `samples` 接住；manager 移除该会话整棵树的登记 |

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [shutdown_session：关闭入口、等待并处理在途请求](BaseAdapter.shutdown_session.md) | 返回本段读取 `session` 与长度上限，再进入轨迹导出；该调用返回 `None`，不返回轨迹 |

#### 2. 已有轨迹与任务结果 → Sample 列表（264–270）

```python
samples = self.manager.get_trajectory(
    sid,
    base_sample=base_sample,
    reward=reward,
    extra_metadata=extra_metadata,
    max_sample_tokens=max_sample_tokens,
)
```

- **找到已有记录**：`sid` 定位 manager 中的会话树；此前的 `record_turn` 已经提供消息与生成事实。
- **合入任务信息**：`base_sample` 提供基础字段，`reward` 是评测分数，`extra_metadata` 携带评分和任务标识。
- **接住 `samples`**：manager 负责组织 token、mask、logprob 等字段并消费轨迹。本例得到一个样本，此时 `response` 还等下一段填入；实际会话可能导出零个、一个或多个样本。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [get_trajectory：路径遍历与样本导出](../../trajectory.py/TrajectoryManager.get_trajectory.md) | 接住 `samples`，使用各自的 `tokens` 与 `response_length` 补文本 |

#### 3. 样本尾部 token → 文本 response 并返回（271–276）

```python
for s in samples:
    rlen = int(s.response_length or 0)
    s.response = (
        self.tokenizer.decode(s.tokens[-rlen:], skip_special_tokens=False) if rlen and s.tokens else ""
    )
return samples
```

- **确定解码范围**：本例 `rlen=4`，因此只取 `tokens` 最后 4 个编号，不把开头 14 个 prompt token 一起解码。
- **补上字符串**：得到 `"已修复。<|im_end|>"`，其中结束标记因 `skip_special_tokens=False` 被保留。没有可解码的 response 区时填空字符串。
- **交回同一列表**：这段只补 `response`；token、mask、logprob 和奖励已经由上一段得到。
- **保留多轮边界**：多轮样本的 response 区可能还包含工具结果等上下文，不能一概当成“最后一条助手回复”；哪些位置用于训练由 `loss_mask` 区分，具体组装留给 manager 的阅读。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [此前的 tok.decode](../../../../src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) | 复用编号到字符串的职责；本次输入是样本尾部，结果写入 `s.response` |

## 我的直接表述（原话）

用户在建议以本函数开始 Step 3 后确认：

> 好的 我觉得确实比较适合写一下这里的内容了？
> 看一下这一块吧

这是当时对本步范围与记录工作的确认；当时尚无对 `finish_session` 输入输出或内部机制的直接复述。

后续指出阅读前置缺口：

> 不对啊 这里不是需要考虑这里的shutdown session先吗 怎么直接快进到这里的get trajectory了呢？
> 以及不需要先知道store pop吗？

本轮据此回到第一段，区分请求收尾、取出会话配置与后续轨迹导出；这一要求不代表已掌握 `shutdown_session` 内部实现。

2026-10-22，在回补收尾并再次阅读 `get_trajectory` 后，用户给出整体反馈（节选）：

> 好的 我觉得 我大致理解了 这里和finish session的全部内容了

这表明用户对两层函数的整体内容已有大致理解；不据此补写尚未表达的逐字段复述，也不将未展开的组装算法标为掌握。完整问题与任务总结依据见[本次收拢](../../../../../../../step-004-trajectory-to-samples/04-flow.md#sample-export-flow-closure)。

## 尚不清楚

- `get_trajectory` 的外层职责已经阅读；多轮记录怎样在其内部组装函数中拼接、分段并确定 mask，仍未逐段展开。此前分叉例子的结果不等于完整算法已经读过。
- `base_sample` 中哪些字段被带入，manager 又补哪些字段；本卡给出最小结果，完整组装待展开。
- `shutdown_session` 已有初步个人复述，任务登记与取消顺序的校正见[该函数卡片](BaseAdapter.shutdown_session.md)；真实请求取消时的远端生成与轨迹保留边界仍待核对。
- 样本交回后，训练端怎样消费 reward、mask 与 logprob；不把本轮导出解释成已经完成训练。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。调用与导出见页首链接；会话配置见 [Session:33–42](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L33-L42)，输出字段依据见 [Sample:107–167](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/types.py#L107-L167) 和 [_SampleBuilder.to_sample:234–261](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L234-L261)。后者仅为字段核对，不表示本轮已独立讲解。
- 2026-10-21 局部执行：从本地源码用 AST 原样提取 `Sample`、`Session`、`shutdown_session`、`finish_session`，执行真实 `trajectory.py` 实现；用已配置字段的本地对象承载方法，未启动 Adapter HTTP 服务。输入没有在途请求；验证一个样本的全部展示字段、原 `base_sample` 未被填充、会话移除及再次导出为 `[]`。
- 示例消息为 `[{"role": "user", "content": "修复加法函数。"}]`；本地 tokenizer 用 `tools=[]`、`tokenize=True`、`add_generation_prompt=True` 编码 prompt，用 `encode("已修复。", add_special_tokens=False)` 后追加 EOS 构造输出。`record_turn` 的 `response_message` 为 `{"role": "assistant", "content": "已修复。"}`。
- tokenizer 为本地 `Qwen/Qwen3.6-35B-A3B`，revision `995ad96eacd98c81ed38be0c5b274b04031597b0`，类为 `Qwen2TokenizerFast`；配置来源与环境见[已有 decode 记录](../../../../src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md)。本次使用离线模式；没有模型权重推理，`reward` 与 logprob 均为构造输入，没有运行 HTTP、沙箱或训练。
- 形成过程：[Step 3 的首轮观察与证据](../../../../../../../step-004-trajectory-to-samples/04-flow.md#finish-session-first-reading)；此前轨迹写入的认识见[继承的 record_turn](../../../../../../../step-008-harness-communication/03-long-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md)。
- 后续带读：[沿本函数三段代码区分配置、轨迹与样本](../../../../../../../step-004-trajectory-to-samples/04-flow.md#finish-session-walkthrough)。本轮继续解释已有卡片，未据此更新个人认识时间。
- 前置回补：[先理解 shutdown_session 与 store.pop](../../../../../../../step-004-trajectory-to-samples/04-flow.md#return-to-session-shutdown)。本轮静态核对 [closed 检查与在途登记:328–338](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L328-L338)、[记录轨迹与请求结束:384–393](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L384-L393)，未新增有在途请求的运行实验。
- 随后的[独立 shutdown_session 阅读](../../../../../../../step-004-trajectory-to-samples/04-flow.md#shutdown-session-reading)新增四组本地 Task 核对，包括跨线程循环的正常结束与超时取消；其验证范围见子卡，未重写本卡原有的无在途请求示例。

</details>
