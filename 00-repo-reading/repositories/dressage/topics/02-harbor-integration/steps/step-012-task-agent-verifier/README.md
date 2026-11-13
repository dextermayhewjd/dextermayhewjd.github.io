# Step 012 · 从运行配置到 Task 与 Agent 对象

[项目唯一进度](../../../../README.md) · [scope](01-scope.md) · [前一步总结](../step-011-harbor-trial-lifecycle/05-task-flow.md)

2026-11-12 按用户要求使用本地 Harbor v0.25.0 发布标签接续。Job 创建、配置初始化与 TrialConfig 静态例子已有讨论；当前按用户要求回看 Job.run，先把初始化好的 Job 接到执行等待与结果汇总；Trial.create 的已有记录保留供随后接续。更深的 Task/Agent/Environment 初始化仍按 scope 逐处进入，未运行任务。

- [从哪里开始：调用现场与进入路径](01-scope.md#reading-start)
- [从 Job.create 到 Trial.create：跨步跳转位置](01-scope.md#job-to-trial-route)
- [创建入口：Job.create](02-short-term-memory/functions/harbor/job.py/Job.create.md#job-create-mainline)
- [调用方：Job.__init__](02-short-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline)
- [配置初始化：Job._init_trial_configs](02-short-term-memory/functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline)
- [当前回看：Job.run](02-short-term-memory/functions/harbor/job.py/Job.run.md#step012-runtime-context)
- [随后接续：Trial.create](02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline)
- [配置组装及调用背景](02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#caller-context)
- [本步函数索引](02-short-term-memory/overview.md)
- [前序累计：76 份记录](03-long-term-memory/overview.md)
- [形成过程](04-flow.md)

当前仅开始配置组装与样例定位，未完成本步，也未运行任务。题目目标是创建 hello.txt 并写入 Hello, world!；后续沿同一例子查看题目文件和 Agent 对象选择；评分规则在此只定位文件，实际评测放回 Step 015 的执行位置。
