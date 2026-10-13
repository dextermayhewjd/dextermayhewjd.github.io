# Trajectory Management 专题阅读入口

> **本目录专门用于理解 Slime 的轨迹管理。** 已经读过 `coding_agent_rl.generate()` 和 `BaseAdapter._run_turn()` 后，从这里继续：一次模型调用怎样接入历史，历史改写怎样处理，最终怎样导出训练 Sample。

这是 4.1 主线之后的专题深入，对应[阅读路线第 2 章](../../../code-reading/chapters/02-model-context/README.md)。它不是新的 CLI 执行阶段，也不是另起一套阅读顺序。学习顺序与状态仍以[唯一阅读路线](../../../code-reading/repo-reading-route.md)为准。

[返回 4.1 阅读入口](../README.md) · [源码核对记录](SOURCE-CHECK.md)

## 先明确：这里要理解哪一种轨迹

本专题关注三层关系：

| 层次 | Slime 处理什么 | 本次要区分的边界 |
| --- | --- | --- |
| 一次模型交互 | 当前请求的消息、真实输入 token、采样输出与 logprob | 这是模型实际使用的上下文，不是 CLI 全部内部状态 |
| 会话消息树 | 哪些历史可以共享，哪里继续，哪里分叉或改写 | 消息分支不自动等于子任务，也不自动说明发生过压缩 |
| 训练片段 | 每条路径怎样成为 Sample，哪些 token 的 loss mask 为 1 | 训练 Sample 集合不等于完整任务执行时间线 |

前后 messages 的比较确实有用：可以观察历史延续、替换和分支。但仅有这些变化，不能唯一确定是自动压缩、子 agent、新会话还是其他上下文重组。想确认 CLI 内部 task、agent teams 的身份和依赖，还需要相应的执行事件及关联 ID。

## 在已读主线中从哪里进入

下面是**阅读伪代码**，用于定位职责；CLI 的多轮请求发生在运行期间，不能把它理解成 `generate()` 内的一串普通同步调用。

```python
coding_agent_rl.generate():
    # 已读：准备 Session、沙箱和工作区，启动 Harness
    # CLI 运行期间通过 HTTP 反复进入 Adapter
    BaseAdapter._run_turn():
        # 已读：转换消息、编码、模型生成、解析和返回响应
        manager.record_turn(...)  # 专题入口：维护会话消息树
    # CLI 结束后：收集 diff，独立评分
    BaseAdapter.finish_session():
        manager.get_trajectory(...)  # 将树导出为训练 Sample
    # 已读主线后续：返回样本、清理资源
```

**当前输入：** `sid` 标识会话；`prompt_messages` 是转换后的本次输入历史；`response_message` 是本次助手回复；`TurnRecord` 保存真实输入／输出 token、logprob 与结束原因。

**本专题出口：** `record_turn()` 更新内存中的消息树后返回 `_run_turn()`；整次任务结束时，`finish_session()` 调用 `get_trajectory()`，接收 `list[Sample]`。

<details>
<summary>展开固定源码入口</summary>

源码仓库：`/home/fredkeira/projects/slime`。阅读快照：`22a89f96835969a47055a659c588f46151f8b07a`。

- [Adapter 调用 record_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L384)
- [TrajectoryManager.record_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L283)
- [TrajectoryManager.get_trajectory](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L307)
- [BaseAdapter.finish_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L245)

</details>

## 单元 1：新请求怎样接回历史

**问题：** 为什么有些请求接在已有历史后，有些请求形成另一条分支？

先读 `record_turn()`，再沿它的调用进入 `_find_mount_point()`、`_mount_prompt_messages()` 和 `_attach_assistant_leaf()`。第一遍暂时把 `_try_merge_assistant_rewrite()` 留给单元 2，只走正常续写和非 assistant 消息变化。

实际入口的核心代码如下，省略了输入检查和根节点初始化：

```python
node, depth = self._find_mount_point(root, prompt_messages)
node, depth = self._try_merge_assistant_rewrite(sid, node, prompt_messages, depth)
node = self._mount_prompt_messages(node, prompt_messages[depth:])
self._attach_assistant_leaf(sid, node, turn=turn, response_message=response_message, metadata=metadata)
```

`_find_mount_point()` 按 role 和消息字典相等逐条匹配。`node` 是已经匹配到的最深节点，`depth` 是匹配过的消息数；剩余消息作为新节点挂上去，最后保存本次生成的 assistant 节点。

用下面一份**说明性构造数据**贯穿阅读，字母代表完整消息，不是真实 CLI 日志：

```text
existing: [system S, user Q] -> assistant A
incoming: [system S, user Q, assistant A, tool T] -> assistant B

root
  system S
    user Q
      assistant A
        tool T
          assistant B
```

这时 `depth = 3`，新增输入只有 `tool T`。再把 incoming 换成 `[system S, user Summary]`：匹配在 `system S` 后停止，`user Summary` 从这里形成分支。可以确认历史变了，不能仅据此断言是某次自动压缩。

**配套案例：** `test_1_2_clean_multiturn_with_tool`、`test_1_4_user_fork_shared_system`。

**读完应能复述：** 匹配在哪里停止？新节点挂在哪里？为什么这里的 parent 是消息路径关系，而不是任务依赖关系？

## 单元 2：历史中的 assistant 被改写怎么办

**问题：** 上次生成的是 `"ok"`，CLI 下次重放成 `"ok "`，一定要保留两条训练分支吗？

进入 `_try_merge_assistant_rewrite()`。它使用结构和长度条件，不通过语义判断两个版本是否等价：

- 分歧处是 assistant 消息；
- 挂载点只有一个 assistant 子节点；
- 该子节点是没有后续节点的叶子，并保存着本地生成记录；
- 原回应短于 `fork_threshold`，默认 1024 个输出 token。

满足条件时，节点消息替换成重放版本，原 `turn` 和 `turn_index` 被清除，并记录 `merged_rewrite`。该节点此后只负责路由和上下文，不再作为原生成输出训练。

如果有多个候选、原回应较长、已存在后续节点或关闭此功能，则不合并，继续保留分叉。

**配套案例：** `test_3_1_rewrite_merge_absorbs_short`、`test_3_2_rewrite_merge_long_forks`、`test_3_4_rewrite_merge_ambiguous_forks`。

**读完应能复述：** 什么条件允许替换？为什么清除原生成记录？哪几种情况必须分叉？

## 单元 3：消息树怎样变成可训练片段

**问题：** 消息看起来连续，token 一定能直接拼接吗？一段共享历史会不会被重复训练？

从 `get_trajectory()` 进入 `_chain_to_samples()`、`_split_chain_into_builders()`，再读 `_SampleBuilder.classify_token_drift()` 和 `append_turn()`：

| 判断 | 行为 |
| --- | --- |
| `CLEAN` | 新输入准确延续已有 token，继续追加 |
| `REALIGN` | 分歧落在最近输出区域，且本次输出短于阈值；用输入中的重放内容重对齐，替换区域作为非训练上下文 |
| `FORK` | 不能按上述条件吸收变化，另开一个 Sample builder |

消息树分叉和 token 层拆片是两次不同判断。同一消息路径也可能因 token 对齐变化导出多个 Sample。共享的生成节点通过 `response_trained` 避免在多个叶子路径中重复承担训练损失。

导出的片段继承同一个 `rollout_id`；当前实现将传入的 outcome reward 完整赋给每个片段。`get_trajectory()` 随后移除这个 session 的树。

**配套案例：** `test_2_3_drift_case_A_forks`、`test_2_4_drift_case_B1_short_replaces`、`test_2_10_cross_leaf_dedup`。

**读完应能复述：** 哪里断开 Sample？哪些内容只是上下文？共享生成为什么只训练一次？

## 读完以后，再看什么

三个单元都在 `slime/agent/trajectory.py` 内展开，不要求先通读整个仓库。

之后再用 `examples/multi_agent/agent_system.py::run_agent_system()` 对照“调度权在自己手里时怎样安排阶段”，再读 `slime/observability/trace_utils.py` 理解执行事件。前者不经过这里的 Adapter／TrajectoryManager，也不是解释 Claude 内部 teams 的源码。

## 当前记录状态

- 本文件是专题阅读标记、范围说明和最小案例，不表示三个单元已经完成逐段讲解或用户已经掌握。
- 代码位置与关键条件已按固定快照静态核对；本文件中的 S/Q/A/T/Summary 是构造示例。
- 本次写入不启动真实 CLI、模型、沙箱或训练；此前对话中的隔离验证不等于完整运行环境验证。
- 后续每轮只展开一个单元，讲完回到 `record_turn()` 或 `get_trajectory()` 的调用主线。

源码摘录来自 [THUDM/slime 固定提交](https://github.com/THUDM/slime/tree/22a89f96835969a47055a659c588f46151f8b07a)，按 [Apache 2.0](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/LICENSE) 保留来源。详细入口与验证边界见 [SOURCE-CHECK.md](SOURCE-CHECK.md)。
