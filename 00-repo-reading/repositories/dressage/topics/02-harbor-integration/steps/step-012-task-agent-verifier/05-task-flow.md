# 05 · Step 012：运行配置怎样接成题目与 Agent 对象

> Job 创建期间先组成每一次尝试的 TrialConfig；Job 运行期间，队列把其中一份配置交给 Trial.create，取得 Task，再进入单步 Trial 的初始化，按配置创建主 Agent 对象。本步在环境创建入口停止，环境启动与 Agent 安装由后续步骤接续。

[本步 scope](01-scope.md) · [步骤入口](README.md) · [函数记录](02-short-term-memory/overview.md) · [收尾过程](04-flow.md#step012-first-pass-closure)

## 1. 本步在任务中的位置

Step 010 已定位 Dressage._run_partition 的 Job 创建与运行调用；Step 011 已读 Trial 的准备、执行、评测、收尾及结果返回。本步补上此前的一个关系：那些执行对象和输入配置从哪里来？

沿用 hello-world 普通单步题目：要求创建 hello.txt 并写入 Hello, world!，主 Agent 选择 claude-code，环境配置选择 docker，启用评测，user_agent=None、source_trial=None。模型名与路径仍使用前面卡片的静态示意，没有运行任务。

**本步终点是 Trial.__init__ 的 _init_agent_environment 调用入口。** 当前已接清配置、题目、尝试对象与 Agent 对象的关系；环境对象创建内部与实际启动留到 Step 013，不在此提前补读。

## 2. 已读部分怎样完成交接

下图是正常路径的教学裁剪。缩进表示实际调用归属，先区分创建 Job 与运行 Job，再沿运行中的 Trial 创建进入；省略恢复、重评、差异任务、全部检查与可选通知。

### 2.1 创建 Job：先得到每一次尝试的运行配置

```text
_run_partition：job = await _CREATE_JOB(job_config)
└─ 默认创建入口 → Job.create
   ├─ 准备题目来源、指标等创建材料（本轮按接口回查）
   ├─ job = cls(...) → Job.__init__
   │  ├─ 保存 config、题目来源与已有材料
   │  ├─ _init_trial_configs：选择普通任务分支
   │  │  └─ _build_standard_trial_configs
   │  │     └─ JobPlan.build_trial_configs
   │  │        → 按尝试次数 × 题目 × Agent 组合 list[TrialConfig]
   │  │     ← 原样 return 列表
   │  │  ← 保存为 self._trial_configs
   │  └─ 准备 Job 的记录目录、剩余配置、队列及回调登记
   │     → 初始化结束，回到 Job.create 的 cls(...) 调用
   └─ return job
_run_partition：接住 Job，随后才进入插件准备和 job.run()
```

创建入口与返回：[Job.create](02-short-term-memory/functions/harbor/job.py/Job.create.md)、[Job.__init__](02-short-term-memory/functions/harbor/job.py/Job.__init__.md)。配置支路：[选择配置生成方式](02-short-term-memory/functions/harbor/job.py/Job._init_trial_configs.md) → [转交创建材料](02-short-term-memory/functions/harbor/job.py/Job._build_standard_trial_configs.md) → [组成 TrialConfig 与静态例子](02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md)。

此时产生的是尝试配置列表。Job.create 返回的是初始化好的 Job；它没有在内部直接运行 Trial.create。要来到 Trial 创建，需要先返回 _run_partition，再进入下面的 await job.run()。

### 2.2 运行 Job：队列把一份配置交给 Trial 创建

```text
_run_partition
├─ await plugin.on_job_start(job)        运行前准备插件与回调
└─ result = await job.run()
   └─ Job.run
      ├─ 建立 JobResult
      └─ await _run_trials_with_queue
         ├─ submit_batch：以剩余 TrialConfig 得到协程对象
         └─ TaskGroup 创建并调度 Task，正常退出时等待全部完成
            └─ 各 Task 执行 TrialQueue._run_trial
               └─ 在 semaphore 额度内进入 _execute_trial_with_retries
                  ├─ trial = await Trial.create(trial_config) ← 本步继续下钻这里
                  ├─ _setup_hooks(trial)                      返回对象后挂回调
                  └─ await trial.run()                        后续运行，沿用 Step 011
```

运行交接卡：[Job.run](02-short-term-memory/functions/harbor/job.py/Job.run.md)、[协程到 Task 的队列函数](02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md)、[Trial.create](02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md)。

Task 在 create_task 时就返回并收进 tasks；正常离开 TaskGroup 后才逐个取 result，返回 list[TrialResult]。Job.run 将已有结果与本次结果两个列表用 + 拼接，再计算统计、填入 JobResult 并返回。这里的异步结果对象 asyncio.Task 与下一节的题目对象 Harbor Task 用途不同。

### 2.3 创建单步尝试：读取题目，再准备 Agent 对象

```text
Trial.create(config)                                      [trial.py:469]
├─ 解析 skills 来源（只定位，不在此安装）
├─ task, task_download_result = await _load_task(config)    [trial.py:532]
│  ├─ config.task.get_task_id() → 题目来源标识
│  ├─ TaskClient.download_tasks(...) → 取 results[0] 的材料记录
│  └─ Task(task_dir=download_result.path, ...)
│     → 读取题目定义与 instruction，按开关检查评测材料
│  ← 返回 (Task, TaskDownloadResult)，父函数分别接住
└─ 根据 task.has_steps 选择具体 Trial；hello-world 为 False
   └─ SingleStepTrial(...) → SingleStepTrial.__init__       [single_step.py:20]
      ├─ 检查题目没有非空 steps
      └─ super().__init__(...) → Trial.__init__             [trial.py:164]
         ├─ 保存 config、task 与材料记录，准备本次身份和记录目录
         ├─ 准备状态；self._result 初值为 None
         ├─ _init_logger / _init_timeouts 等共用准备
         ├─ _init_agent
         │  ├─ 按需组合附加参数
         │  ├─ AgentFactory.create_agent_from_config(config.agent, ...)
         │  │  → 返回对象，保存为 self.agent
         │  └─ 设置 Agent 的 session_id、context_id，并检查轨迹加载支持
         ├─ _init_user_agent：本例未配置模拟用户，直接返回
         └─ _init_agent_environment ← 本步在调用入口停止，内部交给 Step 013
```

题目读取：[Trial._load_task](02-short-term-memory/functions/harbor/trial/trial.py/Trial._load_task.md)。初始化支路：[SingleStepTrial.__init__](02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial.__init__.md) → [Trial.__init__](02-short-term-memory/functions/harbor/trial/trial.py/Trial.__init__.md) → [Trial._init_agent](02-short-term-memory/functions/harbor/trial/trial.py/Trial._init_agent.md)。

**返回关系仍要保留：**基类其余初始化正常完成后，回到 SingleStepTrial.__init__，设置 _are_artifacts_collected=False；随后回到 Trial.create 的构造调用。当前 user_agent=None，_create_bridge 直接返回，Trial.create 再交出 trial，队列才挂 hooks 并调用 run。这是完整路径的返回位置；本步停止在环境入口，未展开该入口及其后续实现。

## 3. 本步留下的状态与后续去向

| 对象或状态 | 在本场景中表示什么 | 后续由谁使用 |
| --- | --- | --- |
| TrialConfig，也就是此处的 config | 这一次怎样运行：题目来源、Agent/模型、环境、评测和记录安排 | Trial.create 及各组件初始化入口 |
| config.task | 题目来源配置，本例指向 hello-world 目录 | _load_task 取得材料 |
| Task，也就是读取后的 task | 问题具体是什么：instruction、从 task.toml 解析的定义与材料位置 | Trial 类型选择、后续环境准备与 Agent 执行 |
| task.config | 题目自身的 task.toml 定义 | 按题目要求准备环境、步骤与评测 |
| TaskDownloadResult | 材料取得记录；当前明确使用其 path | 构造 Task，并交给 Trial 保存与记录 |
| Trial 的 paths、UUID 与状态 | 这一次尝试自己的记录位置和身份；task.paths 则是题目材料位置 | 日志、产物、组件关联与生命周期 |
| self.agent | 工厂按 config.agent 创建的 Agent 对象，带 session_id/context_id | 后续 setup 和执行阶段 |
| self._result = None | 当前只是结果的初始状态 | Trial.run 后续调用 _init_result，逐步记录运行信息 |

沿同一个例子，可以用下面的关系恢复模型：

```text
config：这次用 Claude Code、选定模型和 Docker 去做题，并启用评测
 task：这道题要求创建 hello.txt，写入 Hello, world!
trial：组织这次尝试，保存题目、运行安排、身份与组件
agent：这次尝试要使用的 Agent 对象，当前已创建
```

用户已明确说清 config 与 task 的分工，也明确指出“目前只是对象”。因此，本步留下的 Agent 创建结果不能等同于容器内安装完成。对象创建后，还要接环境创建与启动，再由后续 Agent.setup 处理环境内准备；已有 CLI 也可能被复用。具体安装和真实执行不属于本步新增阅读范围。

## 4. 本步收束与后续衔接

2026-11-13，按用户“目前把这里的这个step 收尾一下吧”的要求，收束 **Step 012 的首轮创建主线阅读**：配置计划、运行期进入 Trial.create 的来路、题目读取、单步初始化与 Agent 对象创建已经接上。用户已表达的关系保存在函数卡原话区；材料检查、部分身份字段和内部参数机制仍由助手提供解释，不据收尾写成全部已掌握。

| 暂未展开的部分 | 后续何时需要回查 |
| --- | --- |
| TaskClient 来源适配、缓存与 overwrite | 排查题目取得、缓存或来源切换的问题时 |
| AgentFactory 的具体类选择、参数展开 | 接入或替换 Agent、排查配置与实现不匹配时 |
| MCP 合并、skills 和轨迹恢复 | 实际启用对应能力时 |
| 多步、重评、模拟用户 bridge | 进入相应业务分支时 |
| 环境创建、启动与后端合同 | 下一步 Step 013 的已准备范围 |

**下一处建议：**从 Trial.__init__ 的 _init_agent_environment 进入 [Step 013](../step-013-harbor-kubernetes-environment/01-scope.md)，先看 config.environment 与题目环境要求怎样得到 self.agent_environment，再接 _prepare 中实际的 start。该步 scope 已存在，尚未开始阅读或创建函数卡；本次收尾不提前生成它的记忆目录，也不推进安装、模型或集群实验。

本步 02 保留实际用到的函数记录，03 保留进入本步时的前序快照。后续正式进入下一步时，再按 03 + 02 继承，保留来源、原话和未知。

<details>
<summary>源码版本、形成依据与验证范围</summary>

- Harbor：v0.25.0 发布提交 fdba28fc411e47e8765420a1a063b4918fce3def。关键创建路径固定链接：[job.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py)、[job_plan.py:140](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job_plan.py#L140)、[trial/queue.py](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py)、[trial/trial.py:469](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L469)、[trial/single_step.py:20](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L20)。_init_agent 本轮按固定版本符号定位，不使用网页解析后的重排行号。
- Dressage：固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，[rollout.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py)。调用方仍锁定 Harbor 0.18，阅读 0.25 不代表运行升级已完成。
- 本步前段沿记录中的本地 checkout 静态读取，后段因当前环境没有该 checkout，使用官方同一固定提交核对；版本归属与历史证据没有改成其他 HEAD。
- 本页由助手根据已发生的阅读整理。用户对 config/task、工厂创建对象、对象与安装的边界有明确表述；其他细节按各卡保留未知和说明来源。[完整形成过程](04-flow.md)。
- 本步没有真实创建 Harbor Job/Trial/Agent、启动运行环境、安装 CLI、调用模型或执行训练与 Kubernetes 实验。hello-world 和模型名为静态场景，文档检查不作为运行验证。

</details>
