# Step 011 · 一次 Harbor Trial 怎样准备、执行和结束

[项目唯一进度](../../../../README.md) · [scope](01-scope.md) · [前一步总结](../step-010-harbor-rollout-entry/05-task-flow.md)

本步按 Harbor **v0.25.0 发布版**阅读，2026-11-12 按用户请求收束首轮职责与正常返回主线，见 [05 任务链路总结](05-task-flow.md)。回调内部、具体后端与失败机制保留为按需回查；这不表示已完成运行验证。下一步先用 Step 012 的一个任务例子接清 Task、Agent、Verifier，再进入环境适配，尚未开始新步骤。

旧版 Trial.run 初读与来源保存在[切换前快照](references/history/2026-11-11-harbor-018-before-025/README.md)；已有生命周期函数卡已校准新版源码，更深实现仍按需留白。Dressage 仍固定 0.18，其调用处用作背景，不表示已与 0.25 运行兼容。

上游批次与 Job 交接归属 [Step 010](../step-010-harbor-rollout-entry/01-scope.md#current-reading)：[_run_round](../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) → [_run_partition](../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline)。两张卡曾误放本步，2026-11-10 按用户确认归回；这里仅保留导航。

- [Job.run 本步函数卡](02-short-term-memory/functions/harbor/job.py/Job.run.md#job-mainline)
- [Trial.run 已有函数卡](02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle)
- [02 本步函数](02-short-term-memory/overview.md)
- [03 前序累计](03-long-term-memory/overview.md)
- [04 形成过程](04-flow.md)
- [05 任务链路总结](05-task-flow.md)
- [第 5 项：回调只认职责，源码按需回查](01-scope.md#end-hook-registration)

2026-11-11 用户确认 Step 010 结束，现接续本步的 Trial.run，先恢复三段生命周期的整体位置。03 已补入 Step 010 收束记录，原始继承快照另存于 references/history；此前 Trial 卡保留。此为当时接续记录；本轮首读总结现已生成，卡片建立仍不代表已运行或掌握。

2026-11-11 用户确认直接阅读 0.25；本步更新阅读版本与导航，不改写前序 03、不新建未读函数卡，也不更新 Dressage 依赖。后续步骤实际进入时再校准版本。
