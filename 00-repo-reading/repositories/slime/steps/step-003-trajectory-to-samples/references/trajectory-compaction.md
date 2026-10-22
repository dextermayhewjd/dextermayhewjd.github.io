# 上下文压缩后，轨迹怎样导出为样本

[返回 get_trajectory 卡片](../02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md) · [本次问题与说明](../04-flow.md#trajectory-after-compaction)

这是当前函数卡片的补充例子。源码固定为 Slime `2f2318653f6f794dddd321eff7c9d4b7b174643f`。这里假定“压缩”指 CLI 将旧对话改写成较短的摘要后，继续使用同一 `sid` 请求模型；实际 CLI 的压缩报文尚未采集。

## 先分清两层处理

| 发生时机 | 负责的函数 | 处理什么 |
| --- | --- | --- |
| 每轮记录时 | `record_turn` | 将这一轮实际传入的消息接入消息树，把实际生成的 `TurnRecord` 挂到 assistant 节点上 |
| 会话导出时 | `get_trajectory` | 取得各条根到叶的路径，委托组装样本，汇总后赋奖励并移除会话记录 |
| 每条路径组装时 | `_chain_to_samples` 及内部组装函数 | 读取路径上的生成记录，判断 token 能否续接，得到样本及其 mask、logprob |

所以需要分别问：**新消息接到了树的哪里？路径上的生成记录又能否拼成同一份 token 序列？** 消息树的一条路径，不保证只对应一个 `Sample`。

## 一个压缩前后各生成一次的例子

下列消息和 token ID 均为教学构造；整数只用于观察拼接，不代表这些文字的真实编码。使用真实 `record_turn`、`get_trajectory` 及内部组装实现执行。

| 这轮实际使用的数据 | 第一轮：压缩前 | 第二轮：压缩后 |
| --- | --- | --- |
| `prompt_messages` | `[{"role": "user", "content": "修复加法函数。"}]` | `[{"role": "user", "content": "摘要：已找到错误。继续修复。"}]` |
| `turn.prompt_ids` | `[10, 11, 12, 13]` | `[10, 30]` |
| `turn.output_ids` | `[21, 22]` | `[41, 42]` |
| `turn.output_log_probs` | `[-0.1, -0.2]` | `[-0.3, -0.4]` |
| 回复用途 | 检查旧代码的工具调用 | 修复后的文本回复 |

1. 第一轮先记下旧 user 消息和生成记录。
2. 第二轮的 user 消息已经改变，无法匹配旧节点。这个例子在根下面接入新分支，旧分支仍然存在。
3. 导出时分别取得两条路径；每条路径各有一个生成记录，最终得到两个样本。

```text
同一个 sid 的消息树
root
├─ 旧 user 消息
│  └─ assistant：旧 prompt → 输出 [21, 22]
└─ 摘要 user 消息
   └─ assistant：摘要 prompt → 输出 [41, 42]
```

设传入的任务奖励为 `1.0`，长度上限为 `4096`，本例没有截断。`get_trajectory` 返回结果的关键字段为：

```python
sample_1.tokens = [10, 11, 12, 13, 21, 22]
sample_1.response_length = 2
sample_1.loss_mask = [1, 1]
sample_1.rollout_log_probs = [-0.1, -0.2]
sample_1.reward = 1.0

sample_2.tokens = [10, 30, 41, 42]
sample_2.response_length = 2
sample_2.loss_mask = [1, 1]
sample_2.rollout_log_probs = [-0.3, -0.4]
sample_2.reward = 1.0
```

- **每份样本有自己的生成条件**：第一份保留旧 prompt，第二份保留摘要 prompt。无需根据摘要恢复旧对话或重新计算旧输出的 logprob；这里使用当轮保存的记录。
- **摘要在第二份样本里是输入**：该样本初始 prompt 的 token 保存在 `tokens` 前缀，`loss_mask` 与 `rollout_log_probs` 只覆盖其后的 response 区。本例训练位置对应 `[41, 42]`。若摘要本身也是通过 Adapter 生成的，那次生成是否形成样本要另看它的记录；本例没有模拟该次生成。
- **奖励按样本赋值**：两份都是传入的 `1.0`，本函数不按样本数量均分，也不根据奖励选择保留哪一段。
- **调用方继续收尾**：此刻两份 `response` 文本仍为空，随后才由 `finish_session` 解码补上。`Sample.prompt` 仍来自 `base_sample`；实际模型输入的 token 前缀以各份 `tokens` 为准。

## 与正常续接对照

若第二轮保留旧消息，并把工具结果追加进来，第二轮 prompt 是：

```python
prompt_2 = [10, 11, 12, 13, 21, 22, 31, 32]
#           原 prompt       旧输出    新工具结果
output_2 = [41, 42]
```

它完整延续了已有 token 前缀，可以合成一个样本：

```python
sample.tokens = [10, 11, 12, 13, 21, 22, 31, 32, 41, 42]
sample.response_length = 6
sample.loss_mask = [1, 1, 0, 0, 1, 1]
sample.rollout_log_probs = [-0.1, -0.2, 0.0, 0.0, -0.3, -0.4]
```

初始 prompt 不在这份 `loss_mask` 中；response 区里，旧生成与新生成对应 `1`，中间插入的工具结果对应 `0`。所以多轮样本的 `response_length` 可能包含作为上下文的 token，不能直接当作参与训练的 token 数。

<a id="shared-prefix-export"></a>

## 路径中间分叉时，先导出所有路径，再移除会话

这是另一个构造例子，先假设 token 能正常续接，也没有触发长度截断。每个字母代表一条消息：`A` 是初始 user 任务，`B` 是共同的 assistant 回复；`C`、`E` 是两种后续 user 输入，`D`、`F` 是各自的 assistant 回复。

```text
root
└─ A
   └─ B
      ├─ C
      │  └─ D（叶子甲）
      └─ E
         └─ F（叶子乙）
```

执行顺序如下：

1. 取得叶子 `D`，沿父节点回溯并反转，得到 `chain=[A, B, C, D]`，交给样本组装。
2. 取得叶子 `F`，同样得到 `chain=[A, B, E, F]`，交给样本组装。共同的 `A、B` 没有在第一步被删除。
3. 两条路径的样本全部合入 `samples` 后，逐个赋传入的奖励。
4. 最后执行 `self._trees.pop(sid, None)`，从 manager 的字典移除这个会话的整棵树的入口；再移除轮次计数，返回 `samples`。其他会话不受影响。

这里 `pop` 的键是会话标识 `sid`。它返回原来登记的根对象，但代码没有接住这个返回值；`get_trajectory` 最后交给调用者的是此前组装好的样本列表。

对于很长的共同历史，遍历方式一样：每个叶子仍对应从根开始的完整路径。之后能否成为一份样本、是否需要 token 分段或长度截断，由组装层处理，不会因为走过第一条路径就丢掉其他分支需要的前半段。

为了观察共享回复，把 `A` 编为 `[10, 11]`，`B/C/D/E/F` 分别用 `[20]/[30]/[40]/[50]/[60]` 表示。这些整数只是构造输入，不是实际文字编码。

| 导出的路径 | `tokens` | `loss_mask` | `rollout_log_probs` |
| --- | --- | --- | --- |
| `[A, B, C, D]` | `[10, 11, 20, 30, 40]` | `[1, 0, 1]` | `[-0.1, 0.0, -0.2]` |
| `[A, B, E, F]` | `[10, 11, 20, 50, 60]` | `[0, 0, 1]` | `[0.0, 0.0, -0.3]` |

- 初始 prompt `A` 不在返回的 mask 区域内。两份样本的 `response_length` 都是 `3`，都取得本例传入的 `reward=1.0`。
- 共同回复 `B=[20]` 在两份 token 序列中都存在。第一份为它分配训练位置；第二份只把它作为上下文，所以对应 mask 和 logprob 为零。新输入 `C/E` 也作为上下文，分支回复 `D/F` 各自保留训练位置。
- 内部 `response_trained` 是本次导出中防止重复分配训练信号的标记，不表示此时已经执行过模型训练。
- 本次实际执行确认：第一条和第二条路径各自组装完成时，树上都仍有两个叶子，`sid` 仍在 manager 中；函数返回后这个 `sid` 被移除，另一个会话仍在，重复导出目标会话返回 `[]`。

## 需要保留的边界

局部对照执行得到以下结果；四个场景相互独立：

| 构造条件 | 树的叶子数 | 导出的样本数 | 观察 |
| --- | --- | --- | --- |
| 消息与 token 都正常续接 | 1 | 1 | 两轮输出保留训练位置，工具结果为上下文 |
| 旧 user 消息被摘要 user 消息替换 | 2 | 2 | 各用自己的 prompt 与输出，正是上面的压缩例子 |
| 消息仍正常续接，但第二轮 token 从早期 prompt 处变化 | 1 | 2 | 消息树未分叉，token 组装仍可能拆成两个样本 |
| 消息仍正常续接，token 只从最近一次回复区域变化，且满足重新对齐条件 | 1 | 1 | 使用新 prompt 对齐；该次旧回复所在区域不再保留训练信号 |

最后两种输入分别把正常续接的 `prompt_2` 改为 `[10, 99, 12, 13, 21, 22, 31, 32]` 与 `[10, 11, 12, 13, 21, 99, 31, 32]`，保持同样的消息路径和新输出 `[41, 42]`。最后一种实际得到 `loss_mask=[0, 0, 0, 0, 1, 1]`。

因此现在可保留的规则是：**每轮使用实际记录的生成条件；能直接续接时合并，存在变化时再判断重新对齐或分段。压缩后的实际样本数，需要结合消息与 token 才能判断。** 当前例子回答数据如何保留，尚未逐段讲解所有分支。

<details>
<summary>对齐、改写与共享前缀的源码边界</summary>

- **消息匹配**：[`_find_mount_point:352–368`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L352-L368) 按 role 和消息字典相等查找，不用 token 判断树是否分叉。
- **短 assistant 改写**：[`_try_merge_assistant_rewrite:370–426`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L370-L426) 在特定条件下吸收改写，并移除那个旧节点的生成记录、保留其消息路由用途。因此不能推广成“任何压缩或改写都一定保留全部旧训练信号”。上面的 user 消息替换不触发该分支。
- **token 分类**：[`classify_token_drift:169–191`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L169-L191) 先看已有 token 是否为新 prompt 的完整前缀；不匹配时，仅在变化位置位于最近一次回复区域、且本轮新输出长度小于阈值时允许 `REALIGN`，否则为 `FORK`。这里阈值比较的是新输出长度，不是“压缩了多少 token”。
- **对齐的代价**：[`append_turn / _align_to_prompt:193–224`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L193-L224) 用新 prompt 替换最近回复区域，将替换部分的 mask 与 logprob 置零，再接上本轮输出。
- **共享前缀**：[`_split_chain_into_builders:456–477`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L456-L477) 给共享的生成节点登记 `response_trained`，后续路径重遇时以 mask 为零的上下文处理，避免重复分配训练信号。一个路径可能形成多个 builder；[`_chain_to_samples:479–502`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L479-L502) 只将仍有训练位置的 builder 导出为样本。
- **长度限制是另一项处理**：[`to_sample:234–261`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L234-L261) 的 `max_sample_tokens` 限制导出长度；它不负责替 CLI 生成摘要。

</details>

<details>
<summary>验证方式与下一处阅读位置</summary>

- 2026-10-21：从固定版本源码提取实际 `Sample` 类并加载实际轨迹模块，构造两轮消息、整数 token、logprob 和奖励，通过原 `record_turn` 与 `get_trajectory` 执行上表四种情况；核对叶子数、样本数、token、mask、logprob、完整奖励及空 `response`。整数 ID 未经过 tokenizer，也没有调用模型、CLI、HTTP、沙箱或训练。
- 上表是受控输入下的实现结果，不能当作真实 CLI 压缩报文已经验证。压缩四组对照中的短 assistant 改写和共享前缀只查源码；后续追问另用上方共享前缀例子验证了分支路径、mask 与会话移除，短 assistant 改写没有重复运行历史实验。
- 回到主线时，从 `get_trajectory` 的委托调用进入 `_chain_to_samples:479`，先看它读取什么、返回什么；当前压缩问题的关键判断再沿 `_split_chain_into_builders:456` 看能否续接。这是后续阅读建议，本轮没有为所有辅助函数提前建立卡片。

</details>
