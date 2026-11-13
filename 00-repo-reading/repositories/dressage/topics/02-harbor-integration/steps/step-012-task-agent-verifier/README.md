# Step 012 · 从运行配置到 Task 与 Agent 对象

[项目唯一进度](../../../../README.md) · [scope](01-scope.md) · [前一步总结](../step-011-harbor-trial-lifecycle/05-task-flow.md)

2026-11-13，按用户要求收束首轮阅读。已将 Job 的配置组装、运行队列进入 Trial.create、题目读取、单步初始化与 Agent 对象创建接成主线，停在环境创建入口。用户已明确 config/task 分工及对象创建与容器安装的区别；下载器、具体工厂和可选接入内部仍保留未知。本步为 Harbor v0.25.0 固定版本静态阅读，没有实际任务运行。

**复习先看 [本步任务链路总结](05-task-flow.md)**，需要下钻时再由 scope 和函数卡进入。

- [从哪里开始：调用现场与进入路径](01-scope.md#reading-start)
- [从 Job.create 到 Trial.create：跨步跳转位置](01-scope.md#job-to-trial-route)
- [创建入口：Job.create](02-short-term-memory/functions/harbor/job.py/Job.create.md#job-create-mainline)
- [调用方：Job.__init__](02-short-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline)
- [配置初始化：Job._init_trial_configs](02-short-term-memory/functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline)
- [运行交接回看：Job.run](02-short-term-memory/functions/harbor/job.py/Job.run.md#step012-runtime-context)
- [调用方：Trial.create 的构造调用](02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline)
- [单步初始化：SingleStepTrial.__init__](02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial.__init__.md)
- [Agent 对象创建：Trial._init_agent](02-short-term-memory/functions/harbor/trial/trial.py/Trial._init_agent.md)
- [调用方：Trial.__init__](02-short-term-memory/functions/harbor/trial/trial.py/Trial.__init__.md)
- [已讨论：Trial._load_task](02-short-term-memory/functions/harbor/trial/trial.py/Trial._load_task.md#load-task-mainline)
- [父函数中的进入与返回位置](02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#load-task-handoff)
- [配置组装及调用背景](02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#caller-context)
- [本步函数索引](02-short-term-memory/overview.md)
- [前序累计：76 份记录](03-long-term-memory/overview.md)
- [形成过程](04-flow.md)
- [本步总结与收束边界](05-task-flow.md)

下一处建议是 [Step 013](../step-013-harbor-kubernetes-environment/01-scope.md) 的 Trial._init_agent_environment：先看环境对象创建，再接实际 start。Step 013 尚未开始；本次只收尾 Step 012，未创建下一步函数卡或记忆继承目录。本步 03 快照保留原样，进入下一步时再按 03 + 02 继承。
