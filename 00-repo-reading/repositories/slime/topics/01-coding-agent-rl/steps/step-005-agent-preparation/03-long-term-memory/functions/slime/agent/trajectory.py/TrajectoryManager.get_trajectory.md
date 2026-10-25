# TrajectoryManager.get_trajectory

- 源码定位：[slime/agent/trajectory.py:405–442](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L405-L442)，由助手核对。
- 首次接触：Step 3，2026-10-21；从 `finish_session` 的调用处进入。
- 最近认识更新：2026-10-24，用户表示对象前置大概理解，希望继续读本函数并先审阅讲解顺序；此前已大致理解外层交接，具体拼接、分段和 mask 算法仍未逐段展开。

<a id="trajectory-object-entry"></a>

对象回查：[TrajectoryManager](../../../../classes/slime/agent/trajectory.py/TrajectoryManager.md) · [MessageNode](../../../../classes/slime/agent/trajectory.py/MessageNode.md#tree-example)。这里的 `self` 是 manager；本方法同步执行，调用处没有 `await`。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`finish_session` 已收尾并取好长度上限，现在导出已有轨迹。
2. **具体内容**：按 sid 取树，将叶子路径交给组装函数，汇总样本、赋奖励并移除本会话记录。
3. **建议构建的心智模型**：

   > 已有消息树 → 按路径组装样本 → 赋奖励 → 移除会话登记并返回列表。

4. **调用代码**（[finish_session:333–339](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L333-L339)）：

   ```python
   samples = self.manager.get_trajectory(
       sid,
       base_sample=base_sample,
       reward=reward,
       extra_metadata=extra_metadata,
       max_sample_tokens=max_sample_tokens,
   )
   ```

## 本场景的输入与输出

沿用原卡片的单轮、无分叉教学场景。以下先看交接，完整 token 和字段值在后面的数值例子中保留。

| 观察什么 | 本例的内容 |
| --- | --- |
| 会话与已有状态 | `sid="sid-demo"`，manager 已保存下图及该 sid 的轮次计数 |
| 导出参数 | `base_sample` 提供基础字段；`reward=1.0`；另有 `extra_metadata` 和 `max_sample_tokens=4096` |
| 返回值 | `[s]`：一个已赋奖励的 Sample；响应文本仍待父函数解码 |
| 状态变化 | 移除该 sid 的树和轮次计数，其他会话保留 |

```text
self._trees["sid-demo"]
└─ root
   └─ user_node
      └─ assistant_node  (turn)
```

`user_node` 保存用户消息；`assistant_node` 还带本轮生成记录。下面三段始终使用这棵树。

<a id="get-trajectory-mainline"></a>

### 1. 用 sid 取树（422–424）

```python
root = self._trees.get(sid)
if root is None:
    return []
```

- 本例取得图中的 `root`，后续从它遍历整棵树。
- 找不到该 sid 时直接返回 `[]`；已有树来自 manager 的记录。

<a id="trajectory-path-iteration"></a>

### 2. 取得路径，汇总样本（426–435）

```python
samples: list[Sample] = []
for routing_leaf in root.leaves():
    if routing_leaf.is_root:
        continue
    chain = routing_leaf.path_from_root()
    samples.extend(
        self._chain_to_samples(
            chain, base_sample=base_sample, extra_metadata=extra_metadata, max_sample_tokens=max_sample_tokens
        )
    )
```

- **找终点**：本例 `root.leaves()` 只给出 `assistant_node`。若只剩占位根，则被 `is_root` 跳过。
- **得到路径**：`path_from_root()` 返回 `[user_node, assistant_node]`，其中是节点，不含占位根。
- **交给组装函数**：`_chain_to_samples(...)` 把该路径交成样本；沿用本例结果 `[s]`，此时奖励尚为 `0.0`。
- **汇入总列表**：`extend` 把样本对象放入 `samples`；本例得到 `[s]`，没有把节点或 token 数组直接拼入结果列表。

| 需要时进入 | 返回后继续什么 |
| --- | --- |
| [节点的叶子与路径方法](../../../../classes/slime/agent/trajectory.py/MessageNode.md#tree-example) | 得到 `chain`，继续 `431` 的样本组装与汇总 |
| [_chain_to_samples 源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L577-L600) | 接回样本列表，随后到 `437` 赋奖励；内部算法后续再读 |

一般情况下，不同路径可以共享节点，一条路径也可能产生零个或多个样本；本例只用一条路径看清交接。

### 3. 赋奖励、移除记录并返回（437–442）

```python
for s in samples:
    s.reward = reward

self._trees.pop(sid, None)
self._turn_count.pop(sid, None)
return samples
```

- 本例 `s.reward` 从 `0.0` 变为 `1.0`；若有多个样本，每个都得到传入的完整奖励。
- 移除的是当前 `sid` 对应的整棵树登记及计数，不是单独移除一个叶子；已返回的样本数据仍然保留。
- 返回 `samples`。接下来由 [finish_session:340–345](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L340-L345)解码响应区，补 `s.response`。

<details>
<summary>完整数值例子：输入、token 与 Sample 字段（历史验证）</summary>

下面保留 2026-10-21 的最小教学构造，字段值属于历史示例；本轮只对照当前源码解释主流程，没有重新运行完整导出。新版另带权重版本、统计、追踪和可选 replay 字段，此处仍按基本字段节选阅读。

沿用 [finish_session 卡片](../adapters/common.py/BaseAdapter.finish_session.md) 的单轮教学构造。这里把观察终点停在 `get_trajectory` 返回，尚未执行父函数的文本解码；没有分叉或长度截断。

**输入**：

```python
sid = "sid-demo"
base_sample = Sample(index=7, group_index=0, prompt="修复加法函数。", session_id=sid)
reward = 1.0
extra_metadata = {"grading_solved": True, "instance_id": "demo-1"}
max_sample_tokens = 4096
```

此前 `record_turn` 已在 `self._trees[sid]` 中留下这棵树。图中的节点是 `MessageNode` 对象，消息与生成记录保存在节点上：

```text
root（占位根，不是一条消息）
└─ user_node：user，content="修复加法函数。"，turn=None
   └─ assistant_node：assistant，content="已修复。"，turn=下方记录
```

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

token ID 来自本地 tokenizer 对构造文本的编码；logprob 和奖励为构造输入。初始 `self._turn_count[sid] = 1`。

**输出**：返回 `[s]`，其中唯一的 `Sample` 字段如下（节选，省略默认字段）：

```python
s.index = 7
s.group_index = 0
s.rollout_id = 7
s.prompt = "修复加法函数。"
s.tokens = prompt_ids + [96221, 103833, 1710, 248046]
s.response_length = 4
s.loss_mask = [1, 1, 1, 1]
s.rollout_log_probs = [-0.1, -0.2, -0.3, -0.4]
s.reward = 1.0
s.response = ""  # 返回父函数后才由 tokenizer 解码补上
s.status = Sample.Status.COMPLETED
s.metadata = {
    "grading_solved": True, "instance_id": "demo-1",
    "truncated": False, "use_tool": False, "ill_formed": False,
}
```

正常导出后，manager 的 `_trees` 和 `_turn_count` 都不再保留这个 `sid`；再次导出同一会话返回 `[]`。这里的移除不影响已经返回的样本数据。

</details>

<details>
<summary>分叉、共享历史与压缩：后续对照</summary>

- **不同叶子仍会共享历史**：例如两条路径为 `A → B → C → D` 与 `A → B → E → F`，终点 `D/F` 不同，共同节点 `A/B` 仍出现在两条 chain 中。因此，遍历叶子本身不会消除共享前缀。
- **组装层怎样处理共享生成**：假设 `B` 是共同的生成回复，组装层用节点上的 `response_trained` 标记避免再次给它分配训练信号；后续路径仍保留它作为上下文，对应 `loss_mask=0`。这里不是按文本相同删除整条轨迹，标记也不表示已经执行训练。两条分支的图和 mask 对照见[中间分叉的例子](../../../../../../step-004-trajectory-to-samples/references/trajectory-compaction.md#shared-prefix-export)。

### 旧上下文被压缩后再请求

- 这里先把“压缩”理解为：CLI 用摘要替换旧对话，再发起下一轮请求。manager 接到的是这轮实际使用的消息和 `TurnRecord`；压缩请求不等于清空整个会话的旧记录。
- **记录时**，`record_turn` 根据消息是否匹配决定怎样接入树；**导出时**，`_chain_to_samples` 及其内部组装函数根据已记录的 token 判断能否合成一个样本。`get_trajectory` 仍只负责取路径、汇总、赋奖励和移除。
- 本轮构造的例子中，旧 user 消息被新的摘要消息替换，形成两条路径：`旧 prompt → 旧输出`、`摘要 prompt → 新输出`，最终返回两个样本，各自保留对应的 token 与输出 logprob，各自获得完整 `reward`。
- 这不是“压缩必定产生两个样本”的规则：具体数量还取决于消息分支、token 对齐及改写处理。具体数组、正常续接的对照和边界见[压缩后的轨迹例子](../../../../../../step-004-trajectory-to-samples/references/trajectory-compaction.md)。本卡继续保留导出函数这一层的模型。

</details>

## 我的直接表述（原话）

2026-10-24，对当前卡片的反馈与重排要求（节选）：

> 那么再继续看一下这里的这个trajectorymanager的get trajectory吧
> 目前是已经了解了
>
> 但是这里的get trajectory是否也应该考虑一下按照skill中的重构一下?
> 整体的内容其实是比较高质量的
> 但是顺序和内容的复杂度是否可以更好
> 先给我一个方案吧

完整表述见[本轮反馈](../../../../../../step-004-trajectory-to-samples/04-flow.md#get-trajectory-reorder-feedback)。随后按该方案重排；此前阅读记录完整保留在下方。

<details>
<summary>此前复述与澄清</summary>

> 好的 那么我们看一下这里的get trajectory吧

后续追问：

> 这个做成卡片了吗？
> 以及这里的get trajectory我怎么感觉细节会非常多呢？
> 特别是如果遇到压缩了之后 这里的trajectory到底是怎么算呢？

接着追问共享路径与移除范围：

> 那么这里pop out的只是一个叶子吗？
> 还是说整个一条轨迹都会被pop out呢？
> 我不是特别理解如果一条轨迹非常长
> 但是中间有了分支？
> 这里的get trajectory是怎么处理的呢？
> 我比较想要知道

随后初步复述当前阅读层次：

> 好的我简单复述一下把 当前是把manager当中的轨迹树统计了之后考虑了一下这里到底每一次如何从这里的routing tree里面拿到轨迹对吗？
> 但是这里没有讲述的细节在与到底是如何做到多份轨迹的
> 也没有到底是怎么分配mask或者怎么凭借的部分
> 单纯就是 如何从manager当中取得轨迹
> 轨迹大概是从什么样的地方取出的
> 但是当前还没有讲述到底怎么做轨迹叠加这种对吗？

助手核对：用户已初步区分取得轨迹的外层职责与待深入的组装算法。这里更准确地说是遍历和导出；多个叶子对应多条消息路径的来源已讲过，路径内部怎样拆成样本、拼接 token 与分配 mask 尚未逐段展开。实际调用已经委托子函数完成组装，最终返回 `Sample` 列表，并非只返回原始路径；这一澄清尚未收到后续反馈。

<a id="trajectory-leaves-and-shared-prefix"></a>

2026-10-22，回到本函数后再次复述，并追问去重与阅读深度：

> 好的那么现在我们需要继续读的是否就是这里的这里的manager.get_trajectory了呢？
> 这里我该了解的是这里的_trees.get(sid)获得的是一个关于message node的tree
> 然后获得这里对应leafs
> 然后拿到对应的轨迹
> 然后在这个for loop里面找到所有的chain
> 然后这里的chain_to_samples会考虑到这里直接除去重复的轨迹吗？
> 还是说因为这里给出的内容是leafs
> 所以不会出现这种问题呢？
> 反正最后是生成了一个从这样子的chain 转换到samples的形式
>
> 置于内部的实现细节当前是否暂时不考虑呢？
> 这是目前我对于这里的理解

助手核对：这次已明确表达从消息路径到样本的交接。`_trees.get(sid)` 具体取得的是占位根节点，每轮循环由一个叶子取得一条完整 chain；不同 chain 仍可共享节点。组装层避免重复分配共享生成节点的训练信号，保留其上下文，不是删除重复文本或整条轨迹。建议本轮停在这些接口结果，加上本函数的赋奖励与移除职责；具体拼接、分段和 mask 算法留作后续问题。这些新澄清当时尚待用户反馈。

同日，用户在上述澄清后给出整体反馈（节选）：

> 好的 我觉得 我大致理解了 这里和finish session的全部内容了

据此记录为整体内容已大致理解，继续保留尚未逐段展开的算法；完整问题与任务总结见[本次收拢](../../../../../../step-004-trajectory-to-samples/04-flow.md#sample-export-flow-closure)。

</details>

## 尚不清楚

- `_chain_to_samples` 如何利用节点中的 `TurnRecord` 组装样本，以及如何得到 `response_length`、mask 与 logprob。
- 已区分消息路径与训练样本；实际何时把一条路径拆成多个样本、如何拼接和重新对齐 token，仍需在组装算法中深入。
- 已补充旧 user 历史被摘要替换的两轮例子；真实 CLI 压缩请求的消息形状尚未采集，不能据此断定实际任务的分支或样本数量。共享生成节点避免重复分配训练信号、短回复改写与 token 对齐的完整实现仍未逐段带读。
- 导出中途失败时怎样处理已经更新的内部状态；本轮只走正常返回与缺失会话的入口分支。

<details>
<summary>来源、验证与完整例子</summary>

- 当前主流程依据 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；生成记录见 [TurnRecord:41–54](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L41-L54)，基本输出字段对照 [_SampleBuilder.to_sample:311–359](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L311-L359)。下列运行及分叉、压缩样例保留原版本的历史证据，本轮没有重新验证其全部内部细节。
- 2026-10-21 局部执行：沿用父卡的源码提取与本地 tokenizer 环境，重新用构造数据调用真实 `record_turn`，直接执行 `get_trajectory`。确认一片叶子、`chain` 角色为 `user → assistant`、一个样本的 token/mask/logprob/奖励及空 `response`，并验证会话移除、重复调用与未知 `sid` 都返回空列表。
- 为观察本层与子函数的交接，只在 `_chain_to_samples` 外包一层记录返回值的观察函数，实际组装仍执行原方法；观察到子函数返回时 `reward=0.0`，本函数返回时 `reward=1.0`，两处 `response` 均为空。没有运行真实模型、HTTP、沙箱或训练，也没有验证多轮及分叉算法。
- 后续压缩追问的局部执行：用实际 `Sample` 类和轨迹实现、构造消息与整数 ID，对照正常续接、摘要替换旧 user 消息、早期 token 前缀变化、最近回复区域重新对齐四种输入，核对叶子数、样本数、token、mask、logprob 与奖励。结果及其适用条件保存在[补充例子](../../../../../../step-004-trajectory-to-samples/references/trajectory-compaction.md)；没有运行真实 CLI 压缩或训练。此项补充验证不改变上一轮单轮实验的范围。
- 后续分叉追问的局部执行：构造共享 `A → B` 后分成 `C → D` 与 `E → F` 的消息树，确认两条完整路径、两份样本及共享回复在后份样本的零 mask；每条路径组装后，会话和两个叶子都仍存在。全部导出后目标 `sid` 的树与计数移除，另一个会话保留，重复导出为空。未运行真实模型或训练。
- 样例来源与 tokenizer 版本见 [finish_session 的完整输入输出与验证](../adapters/common.py/BaseAdapter.finish_session.md)。本页和父卡为同一教学场景、两个观察终点；数据中的回复、logprob 与评分不作为真实任务结果。
- 形成过程：[Step 3 · 进入 get_trajectory](../../../../../../step-004-trajectory-to-samples/04-flow.md#get-trajectory-reading)。此前写入树的认识见[继承的 record_turn](TrajectoryManager.record_turn.md)。
- 后续问题：[Step 3 · 压缩后的轨迹与卡片边界](../../../../../../step-004-trajectory-to-samples/04-flow.md#trajectory-after-compaction)。
- 分叉与移除范围：[Step 3 · 先遍历整棵树，再移除会话](../../../../../../step-004-trajectory-to-samples/04-flow.md#whole-session-export)。
- 个人复述与澄清：[Step 3 · 取得路径与组装样本](../../../../../../step-004-trajectory-to-samples/04-flow.md#trajectory-first-restatement)。
- 2026-10-22 复述与去重疑问：[Step 3 · 不同叶子与共享训练信号](../../../../../../step-004-trajectory-to-samples/04-flow.md#trajectory-leaves-and-shared-prefix)。本轮静态复核 `MessageNode:46–108`、`get_trajectory:307–344`、`_split_chain_into_builders:456–477` 与 `_chain_to_samples:479–502`，沿用此前分叉实例，没有新增执行实验。
- 2026-10-24 按“整体交接 → 单轮例子 → 三段源码 → 复杂对照”重排；[重排前完整卡片](../../../../../../step-004-trajectory-to-samples/references/get-trajectory-before-mainline-layout.md)保留原文，[本轮方案与确认](../../../../../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#get-trajectory-card-reorder-applied)保存调整依据。重排不改变源码、历史实验或认识日期。
- 本轮局部验证：执行原始 MessageNode 与 get_trajectory，组装层使用返回单个样本的替身，核对路径传递、赋奖励、仅移除目标 sid、重复调用和空根场景。此验证只覆盖外层交接，不验证 token 拼接、真实样本组装或模型运行。

</details>
