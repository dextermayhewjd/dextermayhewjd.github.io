# 01 · Dressage Step 012：从运行配置到 Task 与 Agent 对象

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一范围](../step-011-harbor-trial-lifecycle/05-task-flow.md) · [下一范围](../step-013-harbor-kubernetes-environment/01-scope.md)

> 状态：2026-11-12 按真实调用交接调整。本步已开始，当前由 Job.create 的 cls(...) 进入 Job.__init__，先接清初始化，再沿调用进入已有的配置组装卡。 Harbor 入口统一依据 v0.25.0 发布版；没有运行任务、安装、模型或集群验证。

## 1. 阅读目标

**沿创建路径看清：运行安排怎样组成 TrialConfig，题目怎样读入，怎样创建选定的 Agent 对象。读到环境入口就交给 Step 013。**

## 2. 指挥官、入口条件与边界

1. **入口**：[JobPlan.build_trial_configs:140](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job_plan.py#L140)；随后沿已读队列进入 [Trial.create:469](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L469)。本步不是重新通读 Job.run。
2. **已有输入**：JobConfig、任务来源列表；普通单步任务、user_agent=None。用 hello-world 一题、一个 Agent、一次尝试作为静态例子。
3. **停止位置**：知道 TrialConfig.task 指向哪份题目，Task 提供哪些文件与配置，Agent 对象按什么配置创建；在 Trial.__init__ 即将调用 _init_agent_environment 时交给 Step 013。
4. **不在本步展开**：实际启动环境、Agent.setup/install/run、Verifier.verify。可以指出其配置位置，但不提前阅读后期执行内部；这些是后续消费位置。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

沿用 Step 010、011 的整体主线，各步保持相同图形结构。**本步回查 Job 的尝试配置与 Trial 创建，停在环境对象创建入口；环境启动、Agent 执行和评测均是后续位置。** 具体入口与返回位置见 3.2；图中回调和 HTTP 均标明交互方式，不当作同一同步调用栈。

图内标注直接对应本步：**[本步]** 是当前展开位置，**[交给 Step …]** 是停止与交接位置；其余节点保留作整体背景。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> _CREATE_JOB(job_config)  # [本步] 经 Job.create 回查 JobPlan.build_trial_configs：组成尝试配置。
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> _run_trials_with_queue -> TrialQueue -> Trial.run  # [本步] 回查 Trial.create 的 Task 读取与 _init_agent；到环境入口停。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start  # [交给 Step 013] 环境对象的创建和实际启动。
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup  # [交给 Step 014] 环境就绪后才准备 Agent。
                      -> _run
                           -> _run_agent         # 把题目交给 Agent，执行中请求模型。
                           -> _collect_artifacts # 收集产物；按评测模式安排环境停止。
                           -> _run_verifier  # [交给 Step 015] 本步只定位验证配置，不提前展开评分。
                      -> _finalize               # 清理环境并发出生命周期事件。
                           == END 事件 ==> plugin._on_end
                                            # 回调内部的轨迹处理留到实际接入时回查。
            <- JobResult
            -> plugin.on_job_end(...)           # 整份 Job 返回后的插件收尾。
            -> _bundle_samples                   # 训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

<a id="reading-start"></a>

**从已读调用现场进入：** [Step 010 · _run_partition「1. 创建 Job」](../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#create-job)中的 `job = await _CREATE_JOB(job_config)`，经默认创建函数进入第 1 张 Job.create 卡。

本节只链接本地函数卡；未建卡的部分先保留名称。**每一行是一处阅读位置，编号不表示调用层级；缩进表示调用归属。** 第 1–5 张卡按实际函数逐层进入，返回时先按 5 → 4 → 3 → 2 接回，随后读第 6 项。

```python
# 调用关系示意；不是可执行代码。
_run_partition: job = await _CREATE_JOB(job_config)
  -> _default_create_job
       -> [1] Job.create(...)
            -> job = cls(...) -> [2] Job.__init__(...)
                 -> [3] self._init_trial_configs()
                      -> [4] self._build_standard_trial_configs()
                           -> [5] JobPlan.build_trial_configs(...)
                           <- list[TrialConfig]
                      <- 原样转交列表
                 -> 保存 self._trial_configs，完成剩余初始化
            -> [6] 回到 Job.create，return job

# 拿到 Job 后，沿已读运行链恢复后续入口。
[7] _run_partition
  -> plugin.on_job_start(...)
  -> [8] await job.run(...)
       -> [9] await _run_trials_with_queue(...)
            -> Task 执行 _run_trial -> _execute_trial_with_retries
                 -> [10] await Trial.create(...)
                      -> _load_task -> Task(...)        # 待按需建卡。
                      -> SingleStepTrial -> Trial.__init__
                           -> [11] _init_agent(...)
                           -> [12] _init_agent_environment(...)  # 交给 Step 013。
```

<a id="reading-sequence"></a>

| 阅读位置 | 点击后具体看什么 | 下钻及返回位置 |
| --- | --- | --- |
| 1. Job.create | [从创建主干读到 job = cls(...)](02-short-term-memory/functions/harbor/job.py/Job.create.md#job-create-mainline) | [进入第 2 张 Job.__init__ 卡](02-short-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline)；初始化结束后才回到当前构造调用。 |
| 2. Job.__init__ | [从保存创建材料读到 self._init_trial_configs()](02-short-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline) | [进入第 3 张 _init_trial_configs 卡](02-short-term-memory/functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline)；返回后继续目录、记录和队列初始化。 |
| 3. Job._init_trial_configs | [读普通分支：右侧 _build_standard_trial_configs() 调用](02-short-term-memory/functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline) | [进入第 4 张 _build_standard_trial_configs 卡](02-short-term-memory/functions/harbor/job.py/Job._build_standard_trial_configs.md#standard-trial-configs-mainline)；列表回来后，当前函数才赋值 self._trial_configs。 |
| 4. Job._build_standard_trial_configs · 补齐入口 | [读完整短方法：从 Job 取三项数据并转交](02-short-term-memory/functions/harbor/job.py/Job._build_standard_trial_configs.md#standard-trial-configs-mainline) | [进入第 5 张 JobPlan.build_trial_configs 卡](02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-plan-mainline)；列表回来后本方法原样 return 给第 3 张。 |
| 5. JobPlan.build_trial_configs | [读组合逻辑](02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-plan-mainline) · [看具体 TrialConfig 例子](02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-config-example) | [先返回第 4 张的 return](02-short-term-memory/functions/harbor/job.py/Job._build_standard_trial_configs.md#standard-trial-configs-mainline) → [第 3 张保存列表](02-short-term-memory/functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline) → [第 2 张完成初始化](02-short-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline)。 |
| 6. 回到 Job.create，取得 Job | [回看 Job.create 的 return job](02-short-term-memory/functions/harbor/job.py/Job.create.md#job-create-return) | [回到 Step 010 的创建调用，让 job 接住对象](../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#create-job)，接着找第 7 项运行位置。 |
| <a id="job-to-trial-route"></a>7. 回到 _run_partition · 回看 | [回看 Step 010 第 3 段：只定位 result = await job.run()](../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#run-job) | [进入第 8 项 Job.run 的队列等待位置](02-short-term-memory/functions/harbor/job.py/Job.run.md#queue-handoff)。 |
| <a id="current-reading"></a>8. Job.run · 当前回看 | [回看 Step 011 第 2 段：await self._run_trials_with_queue(...)](02-short-term-memory/functions/harbor/job.py/Job.run.md#queue-handoff) | [进入第 9 项队列函数的 Task 执行部分](../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md#queue-stage-2)。 |
| 9. 队列内的 Task · 回看 | [回看 _run_trial → _execute_trial_with_retries 中的 Trial.create 调用](../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md#queue-stage-2) | [从调用处进入本步第 10 张 Trial.create 卡](02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline)。 |
| 10. Trial.create · 后续接续 | [恢复调用来路](02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#job-to-trial-create) → [读取得题目并构造 Trial 的主干](02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline) | _load_task、Task.__init__ 尚待建卡；需要展开时先建对应卡，加载完成后返回本函数选择 Trial 类型。 |
| 11. 创建 Agent 对象 · 待进入 | Trial.__init__ → _init_agent：待建卡 | 从 [Trial.create 的 SingleStepTrial(...) 构造处](02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline)进入；读清后返回 Trial.__init__。 |
| 12. 到达环境入口 · 待进入 | Trial.__init__ 的 _init_agent_environment 调用处：待建卡 | 本步在该调用位置停止，环境创建与启动交给 Step 013；不使用网络源码替代函数卡。 |

这次补齐第 4 张卡与第 5 项显式入口，不把后面尚未阅读的函数提前建卡。原来 4A–4C 的回看改为连续编号 7–9，避免“第几项”和字母编号混淆；当前阅读对象仍保留为 Trial.create，未因修导航而重置已读记录。

**最小前置**：[回看 JobPlan 卡的配置例子：区分任务来源与题目文件配置](02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-config-example)。两类 TaskConfig 的源码出处留在卡片中，本节不直接跳到网络源码。

**本步留下什么**：能从一份 TrialConfig 指出“题目从哪里来、Agent 选谁、环境和验证要求从哪里取得”。安装、执行和评分代码不是完成此目标的前提。

**读后接续**：沿 Trial.__init__ 的 _init_agent_environment 进入 Step 013；本节当前只提供已存在的函数卡链接，后续实际进入时再补对应卡片。


<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0），本轮按本地 git show 定位相关符号；本地 main 与发布标签有差异，不混用。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](references/history/2026-11-12-before-call-order-scope.md)完整保留。本次只改 scope 与导航，不将未读函数提前建卡或标为掌握。

</details>
