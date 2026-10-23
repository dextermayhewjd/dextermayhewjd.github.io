# TrajectoryManager.get_trajectory

- 源码定位：[slime/agent/trajectory.py:307–344](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L307-L344)，由助手核对。
- 首次接触：Step 3，2026-10-21；从 `finish_session` 的调用处进入。
- 最近认识更新：2026-10-22，用户进一步复述树、叶子、chain 到 samples 的关系；澄清共享上下文与重复训练信号后，表示已大致理解本函数与 `finish_session` 的整体内容。具体拼接、分段和 mask 算法仍未逐段展开。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`finish_session` 已完成会话收尾、取得长度上限，现在需要把 manager 中已记录的会话轨迹导出为样本。调用返回后，`finish_session` 继续补样本的文本 `response`。

2. **具体内容**：按 `sid` 找到消息树，逐个取得叶子对应的消息路径；将每条路径交给 `_chain_to_samples`，汇总它返回的样本。随后给每个样本赋传入的 `reward`，移除该会话在 manager 中的树和轮次计数，再返回列表。

3. **建议构建的心智模型**：

   > `get_trajectory` 把一棵会话消息树，按路径交给样本组装函数，再把结果汇总为 `Sample` 列表。
   >
   > 路径怎样转成 token、mask 和 logprob 由 `_chain_to_samples` 继续处理；本层负责遍历路径、汇总、赋奖励和导出后的移除。
   >
   > 所有路径处理完成后，才移除这个 `sid` 对应的整棵树的登记，返回汇总的样本列表。

4. **调用代码**（[finish_session，common.py:264–270](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L264-L270)）：

   ```python
   samples = self.manager.get_trajectory(
       sid,
       base_sample=base_sample,
       reward=reward,
       extra_metadata=extra_metadata,
       max_sample_tokens=max_sample_tokens,
   )
   ```

   进入本函数后，`self` 是这个 `TrajectoryManager` 对象。它是同步方法，调用处没有 `await`。

## 本场景的输入与输出

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

### 函数内部怎样完成这次导出

#### 1. 会话标识 → 对应消息树（324–326）

```python
root = self._trees.get(sid)
if root is None:
    return []
```

- **`sid` → `root`**：本例找到上面的占位根，从它可以访问整棵树。
- **没有对应树**：直接返回空列表。这里读取的是 manager 已存的轨迹；`base_sample` 不用于重建一棵缺失的树。

#### 2. 消息树 → 消息路径 → 汇总样本（328–337）

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

- **`root.leaves()` → 路径终点**：依次取得没有子节点的叶子。本例只有 `assistant_node`；若树只有占位根，`is_root` 会把它跳过。
- **叶子 → `chain`**：`path_from_root()` 返回按消息顺序排列的节点列表，本例为 `[user_node, assistant_node]`，不包含占位根。分叉时，每个叶子都取得从根开始的完整消息路径，共同的前半段会出现在多条路径中；这里不删除叶子或共享节点。此时得到的是消息路径，还没有变成 token 数组。
- **`chain` → 本路径的样本列表**：交给 `_chain_to_samples` 处理。它读取路径上的生成记录并组织样本字段；本例返回一个样本，其中 `reward` 此时还是 `0.0`，`response` 还是空字符串。
- **合入 `samples`**：把本路径返回的各个样本并入总列表。这里的 `extend` 汇总的是样本对象，不把不同分支的 token 首尾拼成一条序列。一般情况下，一条路径可能产出零个、一个或多个样本，不能按节点数或叶子数直接断定样本数；本例最终只有一个。
- **不同叶子仍会共享历史**：例如两条路径为 `A → B → C → D` 与 `A → B → E → F`，终点 `D/F` 不同，共同节点 `A/B` 仍出现在两条 chain 中。因此，遍历叶子本身不会消除共享前缀。
- **组装层怎样处理共享生成**：假设 `B` 是共同的生成回复，组装层用节点上的 `response_trained` 标记避免再次给它分配训练信号；后续路径仍保留它作为上下文，对应 `loss_mask=0`。这里不是按文本相同删除整条轨迹，标记也不表示已经执行训练。两条分支的图和 mask 对照见[中间分叉的例子](../../../../../references/trajectory-compaction.md#shared-prefix-export)。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [MessageNode.leaves:103–108](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L103-L108) 与 [path_from_root:93–101](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L93-L101)，本轮保留路径接口 | 取得一个按消息顺序排列的 `chain`，交给样本组装 |
| [_chain_to_samples:479–502](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L479-L502)，需要深入组装时的入口；本轮保留输入输出与共享节点处理的结果 | 接住这条路径返回的样本列表，合入 `samples` 后赋奖励 |

#### 3. 样本列表 → 赋奖励、移除记录并返回（339–344）

```python
for s in samples:
    s.reward = reward

self._trees.pop(sid, None)
self._turn_count.pop(sid, None)
return samples
```

- **赋奖励**：本例把样本的 `reward` 从 `0.0` 设为 `1.0`。若导出了多个样本，每个都得到传入的完整奖励；奖励在遍历和组装之后赋值，不控制本层选择哪条路径。
- **移除本会话记录**：正常走到这里时，所有叶子的路径都已处理。`self._trees.pop(sid, None)` 删除的是 `sid → 根节点` 这一整项登记，覆盖这个会话的全部分支；不是逐个弹出叶子或仅删一条路径，其他 `sid` 不受影响。`pop` 返回的根对象在这里没有被接收，函数最后返回的是 `samples`。轮次计数也随之移除，再次导出同一会话将返回空列表。
- **返回 `finish_session`**：交回 `samples`，父函数随后用各样本的 `tokens` 与 `response_length` 补 `s.response`；本函数尚未做文本解码。

### 补充场景：旧上下文被压缩后再请求

- 这里先把“压缩”理解为：CLI 用摘要替换旧对话，再发起下一轮请求。manager 接到的是这轮实际使用的消息和 `TurnRecord`；压缩请求不等于清空整个会话的旧记录。
- **记录时**，`record_turn` 根据消息是否匹配决定怎样接入树；**导出时**，`_chain_to_samples` 及其内部组装函数根据已记录的 token 判断能否合成一个样本。`get_trajectory` 仍只负责取路径、汇总、赋奖励和移除。
- 本轮构造的例子中，旧 user 消息被新的摘要消息替换，形成两条路径：`旧 prompt → 旧输出`、`摘要 prompt → 新输出`，最终返回两个样本，各自保留对应的 token 与输出 logprob，各自获得完整 `reward`。
- 这不是“压缩必定产生两个样本”的规则：具体数量还取决于消息分支、token 对齐及改写处理。具体数组、正常续接的对照和边界见[压缩后的轨迹例子](../../../../../references/trajectory-compaction.md)。本卡继续保留导出函数这一层的模型。

## 我的直接表述（原话）

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

## 尚不清楚

- `_chain_to_samples` 如何利用节点中的 `TurnRecord` 组装样本，以及如何得到 `response_length`、mask 与 logprob。
- 已区分消息路径与训练样本；实际何时把一条路径拆成多个样本、如何拼接和重新对齐 token，仍需在组装算法中深入。
- 已补充旧 user 历史被摘要替换的两轮例子；真实 CLI 压缩请求的消息形状尚未采集，不能据此断定实际任务的分支或样本数量。共享生成节点避免重复分配训练信号、短回复改写与 token 对齐的完整实现仍未逐段带读。
- 导出中途失败时怎样处理已经更新的内部状态；本轮只走正常返回与缺失会话的入口分支。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。本函数、路径接口与直接被调用者见上方链接；生成记录定义见 [TurnRecord:28–38](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L28-L38)，样本构造字段见 [_SampleBuilder.to_sample:234–261](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L234-L261)。后者用于核对输出，不表示本轮已逐项展开其实现。
- 2026-10-21 局部执行：沿用父卡的源码提取与本地 tokenizer 环境，重新用构造数据调用真实 `record_turn`，直接执行 `get_trajectory`。确认一片叶子、`chain` 角色为 `user → assistant`、一个样本的 token/mask/logprob/奖励及空 `response`，并验证会话移除、重复调用与未知 `sid` 都返回空列表。
- 为观察本层与子函数的交接，只在 `_chain_to_samples` 外包一层记录返回值的观察函数，实际组装仍执行原方法；观察到子函数返回时 `reward=0.0`，本函数返回时 `reward=1.0`，两处 `response` 均为空。没有运行真实模型、HTTP、沙箱或训练，也没有验证多轮及分叉算法。
- 后续压缩追问的局部执行：用实际 `Sample` 类和轨迹实现、构造消息与整数 ID，对照正常续接、摘要替换旧 user 消息、早期 token 前缀变化、最近回复区域重新对齐四种输入，核对叶子数、样本数、token、mask、logprob 与奖励。结果及其适用条件保存在[补充例子](../../../../../references/trajectory-compaction.md)；没有运行真实 CLI 压缩或训练。此项补充验证不改变上一轮单轮实验的范围。
- 后续分叉追问的局部执行：构造共享 `A → B` 后分成 `C → D` 与 `E → F` 的消息树，确认两条完整路径、两份样本及共享回复在后份样本的零 mask；每条路径组装后，会话和两个叶子都仍存在。全部导出后目标 `sid` 的树与计数移除，另一个会话保留，重复导出为空。未运行真实模型或训练。
- 样例来源与 tokenizer 版本见 [finish_session 的完整输入输出与验证](../adapters/common.py/BaseAdapter.finish_session.md)。本页和父卡为同一教学场景、两个观察终点；数据中的回复、logprob 与评分不作为真实任务结果。
- 形成过程：[Step 3 · 进入 get_trajectory](../../../../../../step-004-trajectory-to-samples/04-flow.md#get-trajectory-reading)。此前写入树的认识见[继承的 record_turn](../../../../../03-long-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md)。
- 后续问题：[Step 3 · 压缩后的轨迹与卡片边界](../../../../../../step-004-trajectory-to-samples/04-flow.md#trajectory-after-compaction)。
- 分叉与移除范围：[Step 3 · 先遍历整棵树，再移除会话](../../../../../../step-004-trajectory-to-samples/04-flow.md#whole-session-export)。
- 个人复述与澄清：[Step 3 · 取得路径与组装样本](../../../../../../step-004-trajectory-to-samples/04-flow.md#trajectory-first-restatement)。
- 2026-10-22 复述与去重疑问：[Step 3 · 不同叶子与共享训练信号](../../../../../../step-004-trajectory-to-samples/04-flow.md#trajectory-leaves-and-shared-prefix)。本轮静态复核 `MessageNode:46–108`、`get_trajectory:307–344`、`_split_chain_into_builders:456–477` 与 `_chain_to_samples:479–502`，沿用此前分叉实例，没有新增执行实验。

</details>
