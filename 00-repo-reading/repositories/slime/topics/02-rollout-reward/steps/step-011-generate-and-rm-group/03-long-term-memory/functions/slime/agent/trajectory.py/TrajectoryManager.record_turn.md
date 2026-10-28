# TrajectoryManager.record_turn

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../step-010-generate-and-rm/03-long-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/trajectory.py:283–305](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L283-L305)，由助手核对。
- 首次接触：Step 1，2026-10-21，用户指定接续 `_run_turn` 中的 `manager.record_turn`。
- 最近认识更新：2026-10-21，用户提出“每轮信息交给 manager，逐步接入树并复用已有部分”的初步理解，随后从分叉联想到按成功率延长或剪除路径；当前记录树与搜索决策的职责区别由助手补充，尚待反馈。

- 继承自：[Step 1 的完整函数记录](../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md)；只继承与重算链接，原认识时间、原话和未知保留。

- 本次继承自：[Step 2 的完整记录](../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/03-long-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据当前源码与本页局部例子整理，作为理解参考。

1. **使用场合**：`_run_turn` 已取得 `_respond` 返回的响应对象，并执行调试回调，现在把本轮生成留在轨迹管理器中，随后返回 HTTP 响应。`self.manager` 是 Adapter 初始化时创建的 `TrajectoryManager`，内部按 `sid` 区分会话。

2. **具体内容**：用输入消息在该会话的消息树中找到位置，补上尚未记录的消息，再接入本轮 assistant 节点。节点保存内部回复消息、`TurnRecord`、元数据和轮次编号；会话计数随之增加。

3. **建议构建的心智模型**：

   > 把这一轮“看到了什么、回答了什么、实际生成了哪些 token”接到该会话的消息树上。
   >
   > 消息决定接到哪里，`TurnRecord` 保存本轮的 token 与生成信息。函数返回 `None`，记录结果留在 `manager` 的内部状态中，供后续整理训练样本。

4. **调用代码**（`common.py:384–391`）：

   ```python
   self.manager.record_turn(
       sid,
       turn=turn,
       prompt_messages=translated,
       response_message=reply.manager_message,
       metadata={"sid": sid},
   )
   return response
   ```

## 本场景的输入与输出

接续 [_build_reply](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md) 和 [_respond](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) 的场景：用户要求读取 `README.md`，本轮 assistant 提出读取文件，工具还没有执行。这里先看**该会话第一次调用 `record_turn`**，已有历史的处理放在后面简要说明。

**输入。** `prompt_messages` 接收 `translated`，`response_message` 接收 `reply.manager_message`；后者是内部 assistant 消息，和 HTTP 的 `response` 对象分开。以下按被调用函数的参数名列出数据：

```python
sid = "demo-session"
prompt_messages = [
    {"role": "system", "content": "你是代码助手。"},
    {"role": "user", "content": "读取 README.md 并概括内容。"},
]
response_message = {
    "role": "assistant",
    "content": "我先读取文件。",
    "reasoning_content": "需要先读取 README.md。",
    "tool_calls": [
        {
            "type": "function",
            "function": {"name": "read_file", "arguments": {"path": "README.md"}},
        }
    ],
}
turn = TurnRecord(
    prompt_ids=[101] * 100,
    output_ids=[701] * 40,
    finish_reason="stop",
    output_log_probs=[-0.2] * 40,
    ill_formed=False,
)
metadata = {"sid": sid}
```

消息沿用前卡；为验证存储，这里单独构造 100 个输入编号、40 个输出编号及对应 logprob，与前卡的 `100/40` 数量一致。重复的 `101`、`701` 和 `-0.2` 都是占位值，不能据此推断文本的真实编码或生成概率。实际调用传入的是生成阶段已有、又由 `_run_turn` 补过 `ill_formed` 的 `turn`。

**输出：返回值为 `None`，变化保存在 manager 中。** 本例使用新建的 `TrajectoryManager()`，调用前 `_trees` 和 `_turn_count` 都为空。调用后，可把它的状态画成下面这样（对象关系示意，不是实际打印格式）：

```text
manager._trees["demo-session"]        # 此会话的根节点
└─ system：你是代码助手。              # message = prompt_messages[0]
   └─ user：读取 README.md 并概括内容。 # message = prompt_messages[1]
      └─ assistant
         ├─ message = response_message
         ├─ turn = turn              # 保存上面整份 TurnRecord
         ├─ metadata = {"sid": "demo-session"}
         ├─ turn_index = 1
         └─ response_trained = False

manager._turn_count = {"demo-session": 1}
返回值：None
```

**节点与轮次。** 树主要按消息建节点，一次调用可能补入多个输入消息节点，再新增本轮 assistant 节点。`system` 和 `user` 节点保存输入消息，`turn` 为 `None`；本轮新生成的 assistant 节点同时保存回复消息和整份 `turn`。因此，`turn.prompt_ids`、`output_ids`、`output_log_probs`、`finish_reason`、`ill_formed` 都随这份记录保留。本版本直接保存传入的消息和 `turn` 对象，元数据另建字典。

<a id="first-record-flow"></a>

**内部怎样得到这个结果？** 下面摘录 `trajectory.py:300–305`，增加阅读注释；输入检查见折叠来源。

```python
# 取出该 sid 的根节点；没有时新建
root = self._trees.setdefault(sid, MessageNode())

# 找到输入历史与已有树匹配到哪里
node, depth = self._find_mount_point(root, prompt_messages)
# 检查是否需要合并被改写的旧 assistant 消息；本例没有旧消息
node, depth = self._try_merge_assistant_rewrite(sid, node, prompt_messages, depth)
# 将剩余输入消息逐条接入；本例接入 system 和 user
node = self._mount_prompt_messages(node, prompt_messages[depth:])
# 接入本轮 assistant，挂上 turn，并更新编号和会话计数
self._attach_assistant_leaf(sid, node, turn=turn, response_message=response_message, metadata=metadata)
```

本例一开始只有根节点，找到的 `depth=0`，所以整段输入消息都需要接入。最后一步把计数从 0 加到 1，并把 1 写入新 assistant 节点的 `turn_index`。

**已有历史时。** `_find_mount_point` 按消息角色和完整字典内容匹配已有路径；如果下一轮原样带回此前历史，就复用已有节点，再补入工具结果等新消息。未匹配的部分通常从最后匹配的位置接出新分支，仍属于同一 `sid` 的树；该 `sid` 尚无树时，则先新建它的根节点。匹配依据是消息内容，token 编号保存在 `turn` 中。特殊的短 assistant 历史改写可能触发合并，改写旧节点并清除它原来的 `turn`；这里仅标出这条分支，具体条件尚未逐步展开。

<a id="tree-growth-and-branches"></a>

**对照：什么时候继续一条链，什么时候分叉？** 下面两个例子分别从空树开始，同一例子中的记录都使用同一个 `sid`。`S` 是系统消息，`U` 是读取 README 的用户请求，`A1` 是助手提出工具调用，`T1` 是工具结果，`A2` 是助手的后续回答；这些是消息的简写。

① 每次原样带回已有历史，再追加新内容，就沿一条链增长。下方箭头左边是 `prompt_messages`，右边是本轮 `response_message`：

```text
第 1 次：[S, U]         → A1
第 2 次：[S, U, A1, T1] → A2

得到：S → U → A1 → T1 → A2
```

② 回到同一段历史再次生成，新回答会接在同一个位置，形成兄弟节点：

```text
第 1 次：[S, U] → A1
第 2 次：[S, U] → A1′

得到：S → U
          ├─ A1
          └─ A1′
```

第二次没有把 `A1` 放入输入历史，所以接入位置仍是 `U`，而不是 `A1` 后面。你提出的“固定输入生成不同输出”就是这个场景，但需要在同一个 `sid` 下记录；不同 `sid` 会分别保存自己的树。

完整输入相同不是分叉的必要条件。例如，同一 `sid` 中先记录 `[S, U, A1, T1]`，随后又记录 `[S, U, A1, T1′]`，两个不同工具结果会成为 `A1` 下的两个分支。系统消息或用户历史的变化也能形成分支。关键是本次从树的哪个位置接入，以及那里是否已经有另一条后续；不能仅根据模型输出有没有变化来判断。

这说明代码支持哪些情况，不代表实际 CLI 经常分叉。若请求始终原样延续同一条历史，就保持单链；它仍然可以用树来存储。

<details>
<summary>实现补充：相同输入得到相同回答，会去重吗？</summary>

当前 `_attach_assistant_leaf` 每次成功记录都会新建本轮 assistant 节点，没有按 `response_message` 去重。因此在同一 `sid` 下重复记录 `[S, U]`，即使两次回答文字完全相同，也会有两个生成节点。这和后续请求携带历史时 `_find_mount_point` 复用已有节点，是两个不同动作。

</details>

<a id="recording-versus-search"></a>

**这棵树会挑成功率高的路径继续、剪掉错误路径吗？** 这是可以在路径记录之上增加的搜索策略。当前 `TrajectoryManager` 的职责和它之间还隔着两部分：

| 能力 | 当前实现 |
| --- | --- |
| 保存收到过的消息与生成路径，复用共同历史 | `record_turn` 已实现；树只包含实际传入的记录，不覆盖所有可能路径 |
| 评价各条路径的正确性或预期成功率 | 当前 manager 没有这项判断；token 的 `output_log_probs` 也不等于任务成功率 |
| 根据评价选择哪条继续生成、哪条停止扩展 | 当前 manager 没有这项调度；需要另有选择和停止规则，并实际发起后续生成 |

因此，要实现你的设想，需要把“生成候选 → 评价路径 → 选择继续或停止 → 再生成”接成循环。评价和选择规则决定是否值得继续探索；保存成树本身不会完成这些判断。这里的“剪枝”可以只是停止继续扩展某条路径，失败记录仍可保留用于分析或训练。

已有的 `_try_merge_assistant_rewrite` 会在特定的历史改写情况下清除旧 `turn`，依据是节点结构和回复长度等条件，服务于训练记录的整理，没有判断哪条路径做错了。当前训练路径的 `reward` 来自任务结束后的评估，`get_trajectory` 将传入的同一个奖励赋给该次导出的各个样本；这也不是生成途中逐分支评分和剪枝。这里只核对职责边界，尚不展开样本导出实现。

**返回哪里。** 回到 [_run_turn 的第 391 行](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#after-respond)，继续 `return response`；离开时执行其 `finally`。本函数保存的是 Python 内存中的消息树，训练 `Sample` 由后续 `get_trajectory` 另行整理。

## 我的直接表述（原话）

在上一张 `_respond` 卡片的总体说明后，用户反馈并指定本次入口：

> 好的我大概理解了
> 那么现在看一下这里的manager.record_turn的部分吧

“大概理解了”对应此前响应说明，这次发言确认了阅读 `record_turn` 的入口。

随后对记录职责与树的增长给出初步理解：

> 我简单可以理解为这里把每一轮的一个信息
> 作为输入放到了这里的manager里面 作为一个节点
> 后续的过程则是一点点地 把这里的信息接入到这个树里面
>
> 如果找到了已有的部分就续写这个树
> 如果没有的话就另外考虑 但这个就是manager需要考虑怎么写的部分了对吗？

节点与轮次的区别、未匹配部分的去向见上方输入输出中的助手说明；本次复述与澄清保存于[对应过程记录](../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#record-turn-tree-understanding)。

随后追问分叉的场景：

> 但是我比较好奇的点在与 这个树是否只是一味地继续张下去呢？
> 我的意思是一般来说不会出现分叉对吗
> 还是除非把固定的内容 变成为固定的输入才会出现在一个树上出现不同的输出呢？

进一步联想到按成功率选择路径与剪枝：

> 这岂不是完美得到的了可能的路径 让成功率比较高的路径不断的延长？
> 后续就可能做到如果某一个方向出错了砍掉这个路径？
> 变成了一种变相的剪去枝丫 pruning？

## 尚不清楚

- 输入消息怎样匹配旧路径、短 assistant 历史改写在什么条件下合并，尚未逐步带读。
- `get_trajectory` 怎样把消息树整理成训练 token、loss mask 和样本，本轮不展开。
- 用户已提出存入树、复用已有部分的总体理解；“一条消息一个节点、本轮生成记录挂在 assistant 节点上”的粒度区别由助手补充，尚无对此的进一步反馈。
- 单链增长、重复历史生成与不同工具结果分支已由助手对照说明，尚无用户反馈；本轮没有实际 CLI 请求统计，不能判断实际分叉频率。
- 用户提出按成功率选择和剪枝的设想；当前记录、路径评价和生成调度之间的区别已由助手说明，尚待反馈。该设想没有作为现有功能或实现任务接入。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：Slime `2f2318653f6f794dddd321eff7c9d4b7b174643f`，本机 `/home/hongshi/projects/slime`。`manager` 的创建见 [common.py:161–166](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L161-L166)，实际调用见 [common.py:376–393](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L376-L393)。
- 数据结构：[TurnRecord:28–38](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L28-L38)、[MessageNode:46–91](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L46-L91)。
- 内部定位：[_find_mount_point:352–368](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L352-L368)、[_try_merge_assistant_rewrite:370–426](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L370-L426)、[_mount_prompt_messages:428–435](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L428-L435)、[_attach_assistant_leaf:437–454](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L437-L454)。
- 输入检查：空的 `prompt_messages` 会记录警告并直接返回；非空的 `output_log_probs` 长度必须与 `output_ids` 一致，否则断言失败。主例满足这两项条件。已有测试入口为 `tests/test_agent/test_trajectory_manager_branching.py`，本轮仅阅读相关测试，没有运行整套测试。
- 局部验证：按 AST 提取原文件的 `TurnRecord`、`MessageNode`、`TrajectoryManager`，保留类实现，隔离未使用的训练依赖。以上述构造输入核对首次记录返回 `None`、节点关系、消息和 `turn` 的保存、元数据及计数。另以构造的下一轮消息验证原样历史复用；以短 assistant 消息被改写的场景验证旧 `turn` 可能被清除，避免把行为误写为始终只追加。未运行 HTTP、CLI、模型、训练或 `get_trajectory`。
- 过程记录：[Step 1 本次接续](../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#record-turn-first-record)。上面的局部验证只证明这些构造场景，不代表用户已经理解分支规则。
- 分叉追问的验证：使用同一固定源码的三个类，局部核对原样延续历史只有一条叶路径、同历史重复生成产生兄弟节点、相同回答也不去重、不同工具结果产生分支，以及不同 `sid` 分别建树。消息和 token 均为构造输入，未调用模型或运行 CLI，也未调用 `get_trajectory`。已有测试场景参考 `tests/test_agent/test_trajectory_manager_branching.py:402–503`；实际复述和解释见[本次讨论](../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#record-turn-branching-cases)。
- 记录与剪枝的职责核对：本页 `record_turn` 及其四个辅助方法不按奖励评价或调度生成；历史改写合并依据见 `trajectory.py:370–426`。训练路径的任务评估与奖励传入见 [generate.py:203–240](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L203-L240)、[common.py:245–270](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L245-L270)；导出时遍历叶节点、统一赋入传入奖励见 [trajectory.py:307–344](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L307-L344)。本次为静态核对，没有新增运行实验；讨论见[本步记录](../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#record-turn-pruning-boundary)。

</details>
