# Step 014 · 一个 agent_run 阶段怎样留下 Trace

[主题入口](../../README.md) · [前一步](../../../02-rollout-reward/steps/step-013-completed-group-handoff/README.md) · [唯一进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

> **状态：暂缓研究。** 2026-10-28 用户明确将整个 Step 014 暂时搁置，Trace 留待以后继续。已有函数卡、样例、运行证据和未解决问题全部保留，未标记为完成。状态以[唯一路线](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准；下文是暂缓前的范围与材料导航。

2026-10-26，用户确认新建主题 03，重点阅读 Trace。本步沿用单个 agent_run 调用，把进入、业务执行、记录退出码、退出四个时刻接起来。先明确[trace_utils.py 的用途](../../README.md#trace-utils-purpose)，再看一次调用具体留下什么。

- [01 · 阅读范围与使用路线](01-scope.md)：官方工具分类、整体位置、核心骨架及阅读导航。
- [02 · 本步函数与数据结构卡](02-short-term-memory/overview.md)：用途、真实调用、输入输出与按需回查的机制。
- [examples · 真实调用的具体数据](02-short-term-memory/examples/README.md)：四个案例各含说明、输入和预期结果，保留原代码隔离核对的边界。 bind_trace 案例现补有 [agent_model_turn 实际输出](02-short-term-memory/examples/bind-trace/README.md#actual-agent-model-turn)及复现脚本。
- [03 · 前序累计记录](03-long-term-memory/overview.md)：从 Step 013 继承的 66 份记录，包含 3 份历史占位。
- [04 · 理解形成过程](04-flow.md)：范围确认、问答、修正与本次归并依据。

**现行读法：scope 定位 → 对应函数卡 → examples 对照数据。** agent_run 沿[①进入 → ②业务 → ③属性 → ④退出](01-scope.md#reading-order)阅读；开始状态和异常边界归 trace_span 卡，Adapter 组合归 bind_trace 卡。需要保存或查看记录时，再查[Trace 的保存与查看](references/trace-output-and-viewing.md)。

用户已确认移除本步 02 中的 procedures 层。examples 与函数/类卡随本步 02 继承，保留来源、具体数据、未知及验证边界；不再另设 procedure 阅读入口。当前用户仍表示不清楚，结构整理不计为掌握，本步不预写完成或任务链路总结，不处理 Hugo。

<details>
<summary>此前安排与归档</summary>

- 本步先按内部调用层级阅读，后转为使用视角；旧 1–10 编号在 [scope 折叠回查表](01-scope.md#internal-reading-map)保留。
- 用户此前将具体执行过程归入短期 procedure；在函数用法与 examples 建立后，本轮确认归并该层。[完整旧稿及现行归属](references/history/procedures/README.md)只用于历史回查，原话与未知保留在 [04-flow](04-flow.md#step014-procedures-retired)。
- [迁移前完整 scope](references/scope-before-short-term-usage.md)与[早期分层 scope](references/scope-before-usage-data-flow.md)保留。trace_span 的 Step 001 原卡在 [references](references/trace-span-step001-source.md)调取存档，不改变前序 66 份继承快照。
- trace_event 当前没有外部 Python 调用证据，不列为真实业务案例；官方入口与内部组合的边界继续保留。

</details>
