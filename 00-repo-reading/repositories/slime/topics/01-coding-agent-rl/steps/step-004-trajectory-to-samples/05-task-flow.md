# 05 · 任务链路：会话轨迹与奖励怎样交成训练样本

> `finish_session` 在会话收尾后取出长度配置，委托 manager 将已有轨迹、基础字段与奖励组织成样本，再补上响应文本，返回 `Sample` 列表。

[本步 scope](01-scope.md) · [步骤入口](README.md) · [函数记录](02-short-term-memory/overview.md) · [本次整理](04-flow.md#task-flow-handoff-refinement)

## 1. 本步在任务中的位置

- Step 001 已将逐轮消息与生成记录保存在 manager 中，用 `sid` 关联同一次执行。
- Step 003 已给出 `reward`；`base_sample` 提供编号、prompt 等任务基础字段。
- Step 002 的 `agent_metrics` 与任务标识等一起放入 `extra_metadata`。

当前沿 `evaluation=False` 路径，从 `_generate:326` 进入 `finish_session`，到样本列表返回为止。跨循环收尾细节按用户要求留待后续，本轮先使用 `shutdown_session` 的“关闭入口并处理未结束请求”职责。

## 2. 各部分怎样完成交接

先看 `finish_session` 直接执行的①–⑤，再沿③进入 manager 内部。编号表示执行顺序，缩进表示调用归属；“遍历叶子”“补写文本”是函数内的处理阶段。入口在 `examples/coding_agent_rl/generate.py`，Adapter 在 `slime/agent/adapters/common.py`，轨迹处理在 `slime/agent/trajectory.py`；下图使用缩写路径。

```text
_generate:326–336 交入 session_id、base_sample、reward、extra_metadata
└─ BaseAdapter.finish_session [adapters/common.py:314–345]
   ├─ ① await self.shutdown_session(sid) [330 → 294–312]
   │  → 标记 sid 关闭，等待未结束的请求 Task；超时后取消仍未结束的 Task
   │  → 等收尾完成后回到 finish_session:331；配置与轨迹仍在
   │
   ├─ ② 取出会话配置，读长度上限 [common.py:331–332]
   │  → self.store.pop(sid, None) 交出并移除 Session
   │  → max_context_tokens → max_sample_tokens；无配置时取 0
   │
   ├─ ③ self.manager.get_trajectory(...) [333–339 → trajectory.py:405–442]
   │  → 接收 sid、base_sample、reward、extra_metadata 和长度上限
   │  ├─ 按 sid 取 root [422–424]
   │  │  → 无树时直接返回 []；有树时继续
   │  ├─ 遍历叶子，跳过占位根 [427–435]
   │  │  ├─ root.leaves() → 叶子节点
   │  │  ├─ routing_leaf.path_from_root() → 本条节点路径 chain
   │  │  └─ self._chain_to_samples(chain, ...) → 本路径的样本列表
   │  │     → 用 samples.extend(...) 汇总各路径结果
   │  └─ 赋奖励并移除会话记录 [437–442]
   │     → 每个 Sample 赋完整 reward，移除该 sid 的树与轮次计数
   │     → samples 返回 finish_session:340；响应文本待补
   │
   ├─ ④ 逐个补写 s.response [common.py:340–344]
   │  → 读取 response_length，取样本末尾的响应 token
   │  └─ self.tokenizer.decode(..., skip_special_tokens=False)
   │     → 文本写回同一个 Sample；无响应 token 时写入空字符串
   │
   └─ ⑤ return samples [common.py:345]
      → 同一份列表交回 _generate:337，随后由调用方检查结果
```

①在调用方等待收尾完成后继续；③是同步调用，内部结果返回后才进入④。`_chain_to_samples` 接收节点路径与组装参数，返回该路径的样本；这里保留它的交接，拼接、分段与 mask 算法仍由后续阅读展开。

对应卡片：[整体编排 finish_session](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md) · [① 收尾 shutdown_session](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md) · [③ 导出 get_trajectory](02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)。对象回查：[Adapter 字段](02-short-term-memory/classes/slime/agent/adapters/common.py/BaseAdapter.md) · [manager 字段](02-short-term-memory/classes/slime/agent/trajectory.py/TrajectoryManager.md) · [消息节点与路径](02-short-term-memory/classes/slime/agent/trajectory.py/MessageNode.md#tree-example)。

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

正常导出这棵树后，会话配置、manager 中该 sid 的树与轮次计数已移除，样本保存在返回列表中；Adapter 的 `closed` 标记此时仍保留。

返回之后，`_generate` 检查空结果，给样本补退出信息及必要的截断状态，最终还会执行会话清理。本步先停在列表交回处，不展开这些外层处理或训练端消费。

## 4. 本轮收束与后续回访

本轮将正常主线接到 `Sample` 列表返回：**会话收尾 → 配置取出 → 轨迹导出与赋奖励 → 补文本 → 交回列表**。

按用户的阅读取舍，以下问题留待后续，不阻塞当前主线：

- `tasks[0].get_loop()`、`run_coroutine_threadsafe`、`wrap_future` 的跨循环细节。
- `_chain_to_samples`、分段、共享前缀与 mask 的具体算法。
- 外层异常清理、远端取消，以及训练器如何消费样本。

2026-10-24，用户询问 `finish_session` 这一层是否可以结束。按当前 scope，助手判断本轮主线可在样本列表交回处收束，依据见[收束记录](04-flow.md#finish-session-reading-closure)。既有原话与未展开问题继续保留；下一步的具体范围另行接续。

<details>
<summary>源码、版本与验证范围</summary>

- 固定提交：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。
- [调用与返回后的处理](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L325-L349)、[最终清理](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L411-L413)。
- [会话收尾与导出](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L294-L345)、[轨迹导出](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L405-L442)。
- [样本字段组装](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L311-L359)：新版还保留权重版本、统计、追踪和可选 replay 字段；本轮只核对输出边界，未展开这些机制。
- 本次参照 [Step 003 的交接总结](../step-003-swe-evaluation/05-task-flow.md#2-已读函数怎样把数据交接起来)与 [Step 007 的调用层级样例](../../../../../../../.agents/skills/repo-reading-task-flow/references/step-007-harness-call-hierarchy.md#2-run-的四个部分各自继续调用谁)，补齐第 2 部分的输入、变化与逐层返回；[本次调整记录](04-flow.md#task-flow-handoff-refinement)与[调整前全文](references/task-flow-before-handoff-expansion.md)保留对照。只有静态源码、链接与排版核对，未新增真实任务运行或个人掌握结论。
- [旧版 task flow](references/task-flow-at-2f231865.md)保留原图、原例子与历史来源。函数卡片中的数值例子仍沿用原实验，本轮做静态源码与文档核对，没有运行模型、真实沙箱或训练。

</details>
