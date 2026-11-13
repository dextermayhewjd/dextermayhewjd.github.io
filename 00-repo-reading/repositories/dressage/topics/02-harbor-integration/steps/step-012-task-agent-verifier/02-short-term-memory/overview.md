# Step 012 · 本步函数记录

| 函数 | 本轮范围 |
| --- | --- |
| [Job.run（回看）](functions/harbor/job.py/Job.run.md#step012-runtime-context) | 本轮回看结果列表拼接及 JobResult 字段回填，保留用户复述与助手校准 |
| [Job._run_trials_with_queue（回看）](functions/harbor/job.py/Job._run_trials_with_queue.md#coroutine-to-task) | 已补协程到 Task 的交接；用户表示已有此基础、只是遗忘，结束本轮异步复习并询问下一处 |
| [Job.create](functions/harbor/job.py/Job.create.md#job-create-mainline) | 已接清类方法创建入口、cls(...) 初始化及返回调用方 |
| [Job.__init__](functions/harbor/job.py/Job.__init__.md#job-init-mainline) | 已看初始化主干与配置生成支路，保留内部未知 |
| [Job._init_trial_configs](functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline) | 已定位普通分支与配置保存 |
| [Job._build_standard_trial_configs](functions/harbor/job.py/Job._build_standard_trial_configs.md#standard-trial-configs-mainline) | 补齐已查看的短委派：取 Job 字段、调用 JobPlan、原样返回列表 |
| [JobPlan.build_trial_configs](functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-plan-mainline) | 已补具体 TrialConfig 输入/输出例子；组合机制按需回查 |
| [Trial.create](functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline) | 用户已回顾 skills、题目加载、类型选择与可选模拟用户；已接清 _load_task 与具体 Trial 构造调用 |
| [Trial._load_task](functions/harbor/trial/trial.py/Trial._load_task.md#load-task-mainline) | 用户已归类题目相关配置；已补 verifier 材料检查用途与两项返回，具体下载器未展开 |
| [SingleStepTrial.__init__](functions/harbor/trial/single_step.py/SingleStepTrial.__init__.md) | 本轮已确认进入：单步约束、基类委派与产物收集标记；暂无独立复述 |
| [Trial.__init__](functions/harbor/trial/trial.py/Trial.__init__.md) | 用户已概括共用初始化主干，并确认 config/task 分工；已接 _init_agent 子卡，具体工厂与环境创建未展开 |
| [Trial._init_agent](functions/harbor/trial/trial.py/Trial._init_agent.md) | 用户已说清工厂按配置创建对象，并主动区分对象初始化与容器安装；身份字段由助手补充，工厂实现未展开 |

本步首轮已收束，跨函数交接见 [任务链路总结](../05-task-flow.md)。前序完整记录见 [03](../03-long-term-memory/overview.md)，该快照未改；后续未读入口只保留在 scope，不提前建立函数卡。
