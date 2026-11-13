# Step 011 · 一次 Harbor Trial 怎样准备、执行和结束

[项目唯一进度](../../../../../../../README.md) · [scope](../../../01-scope.md) · [前一步总结](../../../../step-010-harbor-rollout-entry/05-task-flow.md)

本步从 Harbor Job 下的一次 Trial 开始，关注准备、执行、收尾与生命周期事件。Trial.run 正常主干已有初步介绍，子方法尚未展开。

上游批次与 Job 交接归属 [Step 010](../../../../step-010-harbor-rollout-entry/01-scope.md#current-reading)：[_run_round](../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) → [_run_partition](../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline)。两张卡曾误放本步，2026-11-10 按用户确认归回；这里仅保留导航。

- [Trial.run 已有函数卡](../../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle)
- [02 本步函数](../../../02-short-term-memory/overview.md)
- [03 前序累计](../../../03-long-term-memory/overview.md)
- [04 形成过程](../../../04-flow.md)

2026-11-11 用户确认 Step 010 结束，现接续本步的 Trial.run，先恢复三段生命周期的整体位置。03 已补入 Step 010 收束记录，原始继承快照另存于 references/history；此前 Trial 卡保留。尚无完成总结，卡片建立不代表已运行或掌握。
