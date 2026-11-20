# Job 与 Agent 路由 · U11–U22

跟随一份 Job 配置，从解析题目、创建 Trial 计划，到挂插件、运行 Job 和收回结果。结果交给插件后的用途在第六组。 [全部用法](../README.md)

| 编号 | 交接 |
| --- | --- |
| [U11](U11-Job._resolve_task_configs%20展开任务来源.md#u11) | Job._resolve_task_configs 展开任务来源 |
| [U12](U12-model_validate%20重建每个分区的临时%20JobConfig.md#u12) | model_validate 重建每个分区的临时 JobConfig |
| [U13](U13-EnvironmentFactory%20按%20import_path%20选择具体后端.md#u13) | EnvironmentFactory 按 import_path 选择具体后端 |
| [U14](U14-Job.create%20在插件设置路由前创建%20Job.md#u14) | Job.create 在插件设置路由前创建 Job |
| [U15](U15-Job._task_configs%20提供已经解析的任务对象.md#u15) | Job._task_configs 提供已经解析的任务对象 |
| [U16](U16-Job._remaining_trial_configs%20提供待执行配置.md#u16) | Job._remaining_trial_configs 提供待执行配置 |
| [U17](U17-build_trial_plan%20配对原对象并写回%20trial_name.md#u17) | build_trial_plan 配对原对象并写回 trial_name |
| [U18](U18-Job._init_job_lock%20使用解析记录生成%20lock.md#u18) | Job._init_job_lock 使用解析记录生成 lock |
| [U19](U19-JobPlugin.on_job_start%20接收%20Job%20并登记路由与回调.md#u19) | JobPlugin.on_job_start 接收 Job 并登记路由与回调 |
| [U20](U20-复制%20AgentConfig%20时保留并发分组.md#u20) | 复制 AgentConfig 时保留并发分组 |
| [U21](U21-注入%20AgentConfig.env%20并设置%20extra_allowed_hosts.md#u21) | 注入 AgentConfig.env 并设置 extra_allowed_hosts |
| [U22](U22-Job.run%20将本次%20Job%20的最终结果交给插件与分区.md#u22) | Job.run 将本次 Job 的最终结果交给插件与分区 |
