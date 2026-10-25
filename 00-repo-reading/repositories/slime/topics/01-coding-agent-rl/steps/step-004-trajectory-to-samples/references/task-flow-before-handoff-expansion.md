> 2026-10-24，第 2 部分补充调用层级与数据交接前的完整快照。源码依据为 `18868a79`；正文保留，仅调整相对链接。当前总结见 [05-task-flow.md](../05-task-flow.md)。

---

# 05 · 任务链路：会话轨迹与奖励怎样交成训练样本

> `finish_session` 在会话收尾后取出长度配置，委托 manager 将已有轨迹、基础字段与奖励组织成样本，再补上响应文本，返回 `Sample` 列表。

[本步 scope](../01-scope.md) · [步骤入口](../README.md) · [函数记录](../02-short-term-memory/overview.md) · [本轮接续](../04-flow.md#step-four-mainline-closure)

## 1. 本步在任务中的位置

- Step 001 已将逐轮消息与生成记录保存在 manager 中，用 `sid` 关联同一次执行。
- Step 003 已给出 `reward`；`base_sample` 提供编号、prompt 等任务基础字段。
- Step 002 的 `agent_metrics` 与任务标识等一起放入 `extra_metadata`。

当前沿 `evaluation=False` 路径，从 `_generate:326` 进入 `finish_session`，到样本列表返回为止。跨循环收尾细节按用户要求留待后续，本轮先使用 `shutdown_session` 的“关闭入口并处理未结束请求”职责。

## 2. 各部分怎样完成交接

先取配置，再导出已有轨迹，最后补文本。下面的缩进表示调用归属；行号采用本轮固定版本。

```text
_generate:326
└─ finish_session                             common.py:314–345
   ├─ shutdown_session(...)                  330: close and drain
   ├─ store.pop(sid)                         331: take session config
   │  └─ max_sample_tokens                   332: read length limit
   ├─ manager.get_trajectory(...)            333–339
   │  ├─ _trees[sid] -> leaf paths           trajectory.py:422–430
   │  ├─ _chain_to_samples(...) -> samples   431–435
   │  └─ set reward; remove sid records      437–442
   ├─ tokenizer.decode(...) -> response      common.py:340–344
   └─ return samples                         345 -> _generate:337
```

- **取配置**：`store.pop` 交出并移除会话配置，读出样本长度上限；轨迹此时仍在 manager 中。
- **导出轨迹**：`get_trajectory` 按 sid 找树，逐条路径委托组装，汇总样本并给每个样本赋完整的 `reward`，随后移除 manager 中该 sid 的树和计数。
- **补文本并返回**：`finish_session` 按每个样本的 `response_length` 解码尾部 token，写入 `response`，再把同一个列表交回 `_generate`。

对应卡片：[finish_session](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md) · [get_trajectory](../02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md) · [shutdown_session](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md)。

## 3. 最后交出的内容与去向

返回值是 `list[Sample]`，可能为空、一个或多个样本。它同时承接几类信息：

| 内容 | 来源 |
| --- | --- |
| 编号、prompt、label 等基础字段 | `base_sample` |
| token、响应长度、mask、生成 logprob | manager 读取路径上的生成记录并委托组装 |
| `reward` | Step 003 的评分，在 `get_trajectory` 中赋给每个样本 |
| `response` 文本 | Adapter 使用 tokenizer 解码样本的响应区 |
| 任务、评分与运行统计等 metadata | 调用方的 `extra_metadata`，以及组装层补充的信息 |

`base_sample` 提供基础字段，已有轨迹由 manager 保存；导出会创建新样本。多轮样本的响应区还可能包含工具结果等上下文，不能一概当成最后一句模型回复。

返回之后，`_generate` 检查空结果，给样本补退出信息及必要的截断状态，最终还会执行会话清理。本步先停在列表交回处，不展开这些外层处理或训练端消费。

## 4. 本轮收束与后续回访

本轮将正常主线接到 `Sample` 列表返回：**会话收尾 → 配置取出 → 轨迹导出与赋奖励 → 补文本 → 交回列表**。

按用户的阅读取舍，以下问题留待后续，不阻塞当前主线：

- `tasks[0].get_loop()`、`run_coroutine_threadsafe`、`wrap_future` 的跨循环细节。
- `_chain_to_samples`、分段、共享前缀与 mask 的具体算法。
- 外层异常清理、远端取消，以及训练器如何消费样本。

2026-10-24，用户询问 `finish_session` 这一层是否可以结束。按当前 scope，助手判断本轮主线可在样本列表交回处收束，依据见[收束记录](../04-flow.md#finish-session-reading-closure)。既有原话与未展开问题继续保留；下一步的具体范围另行接续。

<details>
<summary>源码、版本与验证范围</summary>

- 固定提交：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。
- [调用与返回后的处理](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L325-L349)、[最终清理](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L411-L413)。
- [会话收尾与导出](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L294-L345)、[轨迹导出](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L405-L442)。
- [样本字段组装](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L311-L359)：新版还保留权重版本、统计、追踪和可选 replay 字段；本轮只核对输出边界，未展开这些机制。
- [旧版 task flow](task-flow-at-2f231865.md)保留原图、原例子与历史来源。函数卡片中的数值例子仍沿用原实验，本轮做静态源码与文档核对，没有运行模型、真实沙箱或训练。

</details>
