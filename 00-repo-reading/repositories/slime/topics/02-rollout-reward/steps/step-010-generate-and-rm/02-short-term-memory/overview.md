# 02 · Step 010 的短期记忆

[本步范围](../01-scope.md) · [前序累计记忆](../03-long-term-memory/overview.md)

| 源码文件 | 函数或类记录 | 首次接触 | 个人表述状态 |
| --- | --- | --- | --- |
| `slime/rollout/sglang_rollout.py` | [generate_and_rm](functions/slime/rollout/sglang_rollout.py/generate_and_rm.md) | Step 010，2026-10-25 正式展开 | 已提出 acquire 的初步理解及 pacer、aborted 的疑问，校准待反馈 |
| `slime/rollout/sglang_rollout.py` | [GenerateState.dp_rank_context](functions/slime/rollout/sglang_rollout.py/GenerateState.dp_rank_context.md) | Step 010 控制骨架；2026-10-25 展开 | 已提出阅读问题，尚无机制复述 |
| `slime/utils/types.py` | [Sample（类）](classes/slime/utils/types.py/Sample.md) | 前一主题已接触；Step 010 建立独立类卡 | 已初步概括为单份样本的状态；数据范围补充与字段机制待核对 |
| `slime/rollout/sglang_rollout.py` | [GenerateState（类）](classes/slime/rollout/sglang_rollout.py/GenerateState.md) | Step 010 的执行骨架；2026-10-25 建卡 | 已初步概括为群体状态；进程内共享范围的校准待反馈 |
| `slime/agent/harness/common.py` | [HarnessContext（类，对照调取）](classes/slime/agent/harness/common.py/HarnessContext.md) | 沿用前序类卡的记录 | 本轮只比较数据对象与上下文管理器，原话与认识时间保留 |

函数卡片保存入口模型，类卡片保存对象职责、当前字段与用法；个人认识按真实反馈增量补充。[入口形成过程](../../step-010-generate-and-rm/04-flow.md#topic-two-start) · [两张类卡的建立](../../step-010-generate-and-rm/04-flow.md#sample-state-class-cards)。
