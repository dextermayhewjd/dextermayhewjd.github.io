# Step 010 · 自定义生成怎样接入，返回后谁负责评分

[主题入口](../../README.md) · [前一步：CLI 经 Adapter 请求模型](../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/README.md) · [当前进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

上一主题沿 Coding Agent 看过单题运行、评测与样本导出。本步回到调用它的框架层，以 `generate_and_rm` 为书签，接清共享状态下的受控生成、异步结果交接和奖励归属。

用户要求“那么现在开始第二个topic吧”，沿此前确定的“Rollout 接入与奖励”主题开始。首轮选一个新的输入 `Sample`，采用 Coding Agent 自定义生成、`evaluation=False`、`group_rm=False`；短期记忆先保留这一入口函数的职责、关键选择和返回边界。

- [01 · 阅读范围](01-scope.md#execution-skeleton)：已采用“共享状态 → 受控生成 → 结果处理 → 评分交付”的执行骨架，阅读导航与这四段对应。
- [完整执行结构讲解](../../../../../../../slime_photo/code-reading/chapters/03-strategy-evaluation/walkthrough.md#state-and-execution-skeleton)：说明 state、准入、分批启动、中止检查与 finally 释放的作用及源码依据。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：`generate_and_rm`、`dp_rank_context` 函数卡片，Sample、GenerateState 两张简短类卡，以及本轮对照调取的 HarnessContext 旧卡；个人表述按后续实际反馈补充。
- [03 · 前序累计记忆](03-long-term-memory/overview.md)：合并 Step 009 的 43 份累计记录与 6 份短期记录，同名合并后为 46 份记录；保留旧版本、来源和未知。
- [04 · 理解形成过程](04-flow.md)：本轮问题、源码观察与尚未反馈的解释。
- [连贯讲解](../../../../../../../slime_photo/code-reading/chapters/03-strategy-evaluation/walkthrough.md)：与[本地网页](http://localhost:1313/projects/slime/rollout-reward/)共用正文。

本轮先辨认 `state` 与 acquire/try/finally 的控制范围，再进入其中的函数选择和等待，最后看结果与评分交付。`rm_hub` 内部、组级调度与失败清理仍是后续问题；采用骨架不表示已掌握这些机制。

## 版本与证据

2026-10-25 核对本地 `/home/fredkeira/projects/slime`，HEAD 与官方 `THUDM/slime` 的 `main` 均为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。本步采用静态源码证据；继承卡片继续保留各自版本，不将历史记录整体改写为当前 HEAD。

历史对照：[本次替换前的 scope](references/scope-before-execution-structure-2026-10-25.md)、[最初重排前版本](references/scope-before-core-skeleton-review-2026-10-25.md)及[数据交接分块提案](references/scope-by-data-handoffs-proposal.md)保留过程；当前正式骨架以 `01-scope.md` 为准。
