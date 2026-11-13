# Step 010 · 本步短期记录

| 函数 | 当前范围 |
| --- | --- |
| [generate_rollout_harbor_sync](functions/dressage/integrations/harbor/rollout.py/generate_rollout_harbor_sync.md#batch-entry) | 配置入口、批次输入、run 等待异步工作及返回样本组/指标 |
| [_run_harbor_rollout](functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md) | 单一父函数卡、六个卡内阶段；第 3 段连接两张 Job 编排卡，其余按需打开 |
| [_run_round](functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) | 本次补读：分区、路由额度、并发与组结果汇总；由 Step 011 纠正归回 |
| [_run_partition](functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline) | 本次补读：创建 Job、插件交接、执行与结果归组；由 Step 011 纠正归回 |
| [_assign_partition_trials](functions/dressage/integrations/harbor/rollout.py/_assign_partition_trials.md#assign-mainline) | 当前：按 Job 计划中的任务/尝试序号对回原模板，建立 templates 与 bindings；命名兼容层不深入 |
| [HarborDataSource.get_samples](functions/dressage/integrations/harbor/data_source.py/HarborDataSource.get_samples.md#get-samples-mainline) | 本次按请求建卡：组数、每组模板数与返回结构；未认定已掌握 |
| [HarborDataSource._sample_group](functions/dressage/integrations/harbor/data_source.py/HarborDataSource._sample_group.md#sample-group-mainline) | 本次按请求建卡：Sample 的 URI、身份、尝试槽位与 group；未认定已掌握 |
| [_resolve_work](functions/dressage/integrations/harbor/rollout.py/_resolve_work.md#resolve-work-mainline) | 本次按请求建卡：模板组到工作项的配置与身份交接；未认定已掌握 |
| [HarborDataSource.__init__](functions/dressage/integrations/harbor/data_source.py/HarborDataSource.__init__.md#data-source-precondition) | 前置回查：两份配置、spec/运行指纹与 ID 查询表；其余初始化只识别用途 |

数据源的规格轮换、持久化、Harbor 调度器及详细失败策略未另建卡。
