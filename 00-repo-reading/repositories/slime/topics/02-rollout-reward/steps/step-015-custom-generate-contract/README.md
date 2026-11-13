# Step 015 · 自定义 generate 的接口约定与接入验证

> **后续讨论已推进，不能只按下方最初入口判断。** 本步后来已明确进入[生成接口测试](04-flow.md#plugin-contract-test-entry)，用户已区分[签名与结果检查](04-flow.md#contract-check-boundary)，并在[跳过 await 反例](04-flow.md#skip-await-demo-next-data-handoff)后确认转入 [Step 016](../step-016-sample-to-train-data/04-flow.md#step016-start)。未运行该 pytest 的事实单独保留，不代表生成接口尚未学习。2026-11-01 的历史核对见[纠正记录](../../../../slime后续阅读顺序/2026-10-29-existing-foundation-and-remaining-scope.md#contract-history-correction-20261101)。

[主题入口](../../README.md) · [前一步](../../../03-trace-diagnostics/steps/step-014-agent-run-trace/README.md) · [唯一进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

2026-10-28，用户在敲定后续计划后明确要求：“好的那么按照这个scope来继续阅读吧”。本步沿用[已确认范围](../../../../slime后续阅读顺序/current-goal-slime-reading-order.md#reading-agreement-20261028)，以 Slime `18868a79` 为源码基准。

**本步问题：如果由我接入一个新的 Agent 生成函数，需要接收什么、返回什么，怎样确认它与框架正确配合？** 复用已读的 Coding Agent 实现、generate_and_rm、组级生成和结果交付；新增的是从调用者与真实实现中提取可使用的接口约定。

## 从哪里读

1. [01 · scope](01-scope.md#reading-order)：整体位置、局部源码、固定的三步阅读顺序。
2. [02 · 短期记忆](02-short-term-memory/overview.md)：本步使用的 generate_and_rm、Coding Agent generate、Sample 类及一个接入测试卡片。
3. [03 · 前序记录](03-long-term-memory/overview.md)：从 Step 014 的 03 + 02 继承 77 份函数／类记录、17 份配套文件，包含 3 份历史空白占位；Trace 暂缓状态与未知保留。
4. [04 · 理解形成过程](04-flow.md)：范围确认、第一观察点、源码证据与实际反馈。

本步最初从 [generate_and_rm 中的调用约定](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md#step015-call-contract)开始，把调用处和具体函数签名放在一起。随后已经实际展开返回样本、状态与奖励、生成契约测试和两类断言；用户原话与后续转向见本页开头的记录入口。这里的起点介绍不代表当前仍停在第一项。

## 本步证据与边界

- 早期用户已表述按 function path 加载、前三个参数按位置对应，并追问签名是否足够；后续又区分签名与结果字段检查，明确接受当前接口的可等待要求。各项技术边界仍以[实际讨论](04-flow.md#contract-check-boundary)中的原话和校准为准。
- 本步已有接口讨论与静态源码核对，未运行插件、契约测试、真实 Agent 或训练；不处理 Hugo。
- [继承清单](references/inheritance-manifest.json)保存来源和内容校验；[源码证据](references/source-evidence.json)保存固定版本与片段哈希。
- generate 的旧累计文件是空白占位。本步在 02 中按真实源码补齐函数记录，03 保留原占位；这不抹去主题 01 已有阅读，也不代表用户新增掌握。

本步停止标准：能解释输入、输出与责任边界，并通过一个最小接入核对正常返回及一个错误/失败情形的行为。读完后再按实际证据整理 task flow；现在不预填完成总结。
