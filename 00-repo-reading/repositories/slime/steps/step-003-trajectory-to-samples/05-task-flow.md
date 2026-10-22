# 05 · 任务链路：会话轨迹与奖励怎样交成训练样本

> `finish_session` 先给当前会话收尾，再把已有轨迹、任务基础字段与奖励交给 manager 导出样本，最后补上样本文本，交回 `generate`。

[本步 scope](01-scope.md) · [步骤入口](README.md) · [函数记录](02-short-term-memory/overview.md) · [本次收拢](../step-003-trajectory-to-samples/04-flow.md#sample-export-flow-closure)

## 1. 本步接住前面哪两份结果

- **Step 1 留下轨迹**：CLI 运行期间，`_run_turn` 通过 `manager.record_turn` 把消息和每轮生成记录存进同一个 `sid` 的消息树。
- **Step 2 得到奖励**：CLI 结束后，`generate` 调用 `run_evaluation` 评测代码补丁，接到 `reward, applied_cleanly`。
- **Step 3 将它们交成样本**：沿 `evaluation=False` 路径，`generate` 把 `sid`、`base_sample`、`reward` 和附加元数据交给 `finish_session`。轨迹已在 manager 中，不从 `base_sample` 中重新取得。

本页终点是 `finish_session` 返回 `list[Sample]`。`evaluation=True` 在此前另行返回评估结果，不经过这次样本导出。

## 2. 已读函数怎样完成交接

图中行号指向本步固定版本；只保留职责和数据变化，等待取消、token 拼接等内部代码从函数卡片回查。

```text
generate.py:237：交入会话标识、任务基础字段、奖励与元数据
└─ BaseAdapter.finish_session                         common.py:245
   │
   ├─ 1. shutdown_session                            common.py:261
   │     → 关闭这个 sid 的请求入口，等待并处理尚未结束的请求
   │     → 正常完成收尾后，再导出其轨迹
   │
   ├─ 2. 取出并移除会话配置                           common.py:262–263
   │     → 得到 max_sample_tokens；轨迹树仍在 manager 中
   │
   ├─ 3. manager.get_trajectory                       common.py:264–270
   │     ├─ 取出 sid 对应的根节点                     trajectory.py:324
   │     ├─ 按叶子取 chain，交给 _chain_to_samples    trajectory.py:328–337
   │     │  → 汇总为 Sample 列表，此时尚未补文本 response
   │     └─ 给每个样本赋 reward，移除该 sid 的树与计数 trajectory.py:339–344
   │        → 返回 samples
   │
   ├─ 4. 逐个调用 tokenizer.decode                    common.py:271–275
   │     → 取各样本 tokens 的 response_length 长度尾部
   │     → 将解码文本写入各自的 response
   │
   └─ return samples                                 common.py:276

generate：接住样本列表；对非空结果继续补 agent_exit_code
```

需要展开时回到：[会话收尾](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md)、[路径遍历与导出](02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)、[finish_session 的配置读取与文本补全](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md)。解码职责复用[此前的 decode 记录](03-long-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md)。

## 3. 最后交出的数据是什么

沿用两张函数卡片的单轮构造例：已经记录回复“已修复。”，输入奖励为 `1.0`；本例无分叉和长度截断，返回一个样本。完整 token 数组见 [finish_session 的输入与输出](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md#本场景的输入与输出)。

| 样本中的内容 | 来自哪次交接 |
| --- | --- |
| `index`、`group_index`、`prompt` 等任务基础字段 | `base_sample` 提供；不是将其所有字段原样复制 |
| `tokens`、`response_length`、`loss_mask`、`rollout_log_probs` | manager 读取路径上的生成记录并组装 |
| `reward = 1.0` | `get_trajectory` 将传入奖励赋给每个导出的样本 |
| `response = "已修复。<\|im_end\|>"` | `finish_session` 解码样本尾部；保留特殊标记 |
| 评分、任务标识及轨迹相关 `metadata` | 调用方的附加元数据与组装层共同提供；返回后 `generate` 再补 `agent_exit_code` |

- 一般情况下，一个会话可以返回零个、一个或多个样本；多条路径可以共享历史，组装层避免给同一个共享生成节点重复分配训练信号。
- 多轮样本的 response 区可能包含工具结果等上下文，不等于最后一条助手回复。哪些位置参与训练由 `loss_mask` 区分；导出本身没有执行训练。
- 正常导出后，会话配置和 manager 中该 sid 的轨迹登记已移除，样本数据由返回列表保存。此时 sid 的关闭标记仍在；重复导出得到空列表。

## 4. 哪些函数还没有逐段展开

当前 scope 所需的入口、收尾、导出与文本补全已能连起来，因此可以在这里总结。下面保留的是进一步的问题，不要求全部读完才生成本页。

| 尚未展开的部分 | 什么时候值得继续读 |
| --- | --- |
| `_chain_to_samples`、`_split_chain_into_builders` | 想具体说明一条 chain 为什么拆成多个样本、如何避免共享生成的重复训练信号 |
| `_SampleBuilder` 的拼接、对齐与 `to_sample` | 想逐项推导 token、mask、logprob、长度截断和最终 Sample 字段 |
| `generate` 外层 `finally` 中的 `drop_session` | 想把成功、空结果和异常路径的最终清理接完整；调用在 `generate.py:282`，位于本页终点之外 |

`store.pop` 与长度读取已在父函数中解释；`leaves()`、`path_from_root()` 已保留路径接口；`decode` 复用前序卡片。这些调用无需仅因出现了函数名就各建一份新卡片。

外层边界：`generate` 会检查空结果，为非空样本补元数据；它真正返回之前还会执行 `finally` 的清理。因此，本页完成的是样本导出的交接，不代表整个外层任务已经结束。后续继续读哪一处，仍按具体问题确认。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 调用与外层边界：[generate.py:215–283](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L215-L283)。
- 收尾与样本导出：[common.py:225–276](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L225-L276)。路径遍历、奖励与移除：[trajectory.py:307–344](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L307-L344)。
- 本页由 LLM 对已发生的阅读整理。2026-10-22 用户表示大致理解 `get_trajectory` 与 `finish_session` 的整体内容；具体算法仍保留上面的阅读边界。
- 示例沿用此前执行过的单轮构造数据；分叉、两轮与本地 Task 的验证分别保留在函数卡片和 references。本次静态核对调用与返回位置，没有新增模型、HTTP、真实沙箱或训练实验。

</details>
