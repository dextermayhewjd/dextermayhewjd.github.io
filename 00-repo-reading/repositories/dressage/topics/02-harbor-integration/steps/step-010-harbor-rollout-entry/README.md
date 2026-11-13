# Step 010 · Dressage 如何把一轮批量 rollout 交给 Harbor

[项目唯一进度](../../../../README.md) · [scope](01-scope.md) · [前一主题收束](../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/05-task-flow.md)

前序已读原生单任务路径，本步切换到 Dressage 自带的 Harbor 集成。先对齐批量 hook 的层级、输入与返回，再逐段看数据源、Job 和插件交接；不把旧原生 generate 嵌入每个 Harbor Trial。

- [已补读主线：_run_round](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) → [_run_partition](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline)
- [外层入口函数卡](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/generate_rollout_harbor_sync.md#batch-entry)
- [02 本步函数记录](02-short-term-memory/overview.md)
- [03 前序累计](03-long-term-memory/overview.md)
- [04 形成过程](04-flow.md)

2026-11-11 用户确认本步结束：已接通批次入口、数据源与工作分区、Job/插件交接、组结果处理和返回主线。指标算法、全部异常分支及 Harbor 内部调度未逐项展开；没有运行实验。

[本步总结](05-task-flow.md)保留首轮记录及本次收束说明；下一处接续 [Step 011 的 Trial.run](../step-011-harbor-trial-lifecycle/01-scope.md#current-reading)，不重新开始上游阅读。
