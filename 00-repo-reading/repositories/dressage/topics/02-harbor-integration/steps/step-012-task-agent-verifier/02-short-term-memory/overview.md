# Step 012 · 本步函数记录

| 函数 | 本轮范围 |
| --- | --- |
| [Job.run（回看）](functions/harbor/job.py/Job.run.md#step012-runtime-context) | 当前按要求调取：从初始化字段接到建立结果、执行等待与汇总 |
| [Job.create](functions/harbor/job.py/Job.create.md#job-create-mainline) | 已看类方法的创建入口，当前从 cls(...) 下钻 |
| [Job.__init__](functions/harbor/job.py/Job.__init__.md#job-init-mainline) | 已看初始化主干，现沿配置生成调用下钻 |
| [Job._init_trial_configs](functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline) | 已定位普通分支与配置保存 |
| [Job._build_standard_trial_configs](functions/harbor/job.py/Job._build_standard_trial_configs.md#standard-trial-configs-mainline) | 补齐已查看的短委派：取 Job 字段、调用 JobPlan、原样返回列表 |
| [JobPlan.build_trial_configs](functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-plan-mainline) | 已补具体 TrialConfig 输入/输出例子；组合机制按需回查 |
| [Trial.create](functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline) | 已建立配置到 Trial 的记录，内部待继续 |

前序完整记录见 [03](../03-long-term-memory/overview.md)。未来入口只保留在 scope，不提前建立函数卡。
