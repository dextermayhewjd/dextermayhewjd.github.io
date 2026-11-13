# 01 · Dressage Step 012：从运行配置到 Task 与 Agent 对象

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [前一范围](../../../step-011-harbor-trial-lifecycle/05-task-flow.md) · [下一范围](../../../step-013-harbor-kubernetes-environment/01-scope.md)

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

**先从调用现场进入：** [Step 010 · _run_partition 的「1. 创建 Job」](../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#create-job)，找到 `job = await _CREATE_JOB(job_config)`（rollout.py:704）。[回看 Job.create 卡的调用代码：_CREATE_JOB 怎样委派到 Job.create](../../02-short-term-memory/functions/harbor/job.py/Job.create.md#job-create-callsite)，后者调用下面的 [1] Job.create。

**本节只链接本地函数卡。** 尚未建立的卡片标为“待建卡”，实际进入时再补；源码出处在对应卡片中查看。

编号与下表对应。先看一个函数，走到委派位置再下钻；子函数返回后回到原调用点。**[1]–[4] 属于创建 Job，之后才通过已读的运行链进入 [5]–[7]。**

```python
# 关系示意，保留调用和返回位置；不是可执行代码。
_run_partition: job = await _CREATE_JOB(job_config)
  -> _default_create_job
       -> [1] await Job.create(...)
            -> 准备任务、指标与任务材料
            -> [2] job = cls(...) -> Job.__init__(...)
                 -> [3] self._init_trial_configs()
                      -> self._build_standard_trial_configs()
                           -> JobPlan.build_trial_configs(...)
                           <- list[TrialConfig]
                 -> 保存 _trial_configs，完成待运行配置与队列初始化
            -> [4] 回到 Job.create，继续到 return job
       <- 初始化完成的 Job，交给 _run_partition

# [4A] 回到 Step 010 的 _run_partition，继续绑定模板并准备插件。
_run_partition
  -> await plugin.on_job_start(...)
  -> [4B] result = await job.run(...)     # 进入 Step 011 已读的 Job.run。
       -> [4C] await _run_trials_with_queue(...)
            -> TaskGroup 创建 Task，执行队列协程
                 -> _run_trial -> _execute_trial_with_retries
                      -> [5] await Trial.create(...)
                           -> _load_task(...) -> Task(...)  # 取得题目。
                           -> SingleStepTrial(...) -> Trial.__init__(...)
                                -> [6] self._init_agent()
                                -> [7] self._init_agent_environment()  # 到入口停，交 Step 013。
  # Trial.create 仍在 job.run 等待期间；不是整个 Job 返回后的新步骤。
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 点击后具体看哪里 | 读完回哪里、接着看什么 |
| --- | --- | --- |
| 1. Job.create · 已看创建入口 | [读 Job.create 创建主干：找到 job = cls(...)](../../02-short-term-memory/functions/harbor/job.py/Job.create.md#job-create-mainline) | 走到构造调用时，[进入 Job.__init__：看传入材料怎样保存到 self](../../02-short-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline)。加载器细节暂缓。 |
| 2. Job.__init__ · 已看初始化主干 | [读 Job.__init__ 初始化主干：找到 self._init_trial_configs()](../../02-short-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline) | 在这次调用处，[进入 Job._init_trial_configs：看普通分支怎样保存配置列表](../../02-short-term-memory/functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline)。 |
| 3. Job._init_trial_configs · 已定位普通分支 | [读 Job._init_trial_configs：最后一行的调用与赋值](../../02-short-term-memory/functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline) | 组合细节进入 [JobPlan.build_trial_configs：看具体 TrialConfig 例子](../../02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-config-example)；列表保存后，[返回 Job.__init__：继续目录、记录和队列初始化](../../02-short-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline)。 |
| 4. 回到 Job.create，再交回调用方 | [回看 Job.create：cls(...) 完成后，执行 return job](../../02-short-term-memory/functions/harbor/job.py/Job.create.md#job-create-return) | 回到 [Step 010 · _run_partition 第 1 段：job 接住创建结果](../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#create-job)，然后沿 4A 找到运行位置。 |
| <a id="job-to-trial-route"></a>4A. 回到调用方的运行位置 · 回看 | [回看 Step 010 · _run_partition 第 3 段：只定位 result = await job.run()](../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#run-job) | 从这一行[进入 Step 011 · Job.run 第 2 段：看队列等待调用](../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job.run.md#queue-handoff)，此时还没有执行 plugin.on_job_end。 |
| 4B. 进入 Job.run 的等待位置 · 回看 | [回看 Step 011 · Job.run 第 2 段：找到 await self._run_trials_with_queue(...)](../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job.run.md#queue-handoff) | 沿这个调用[进入队列函数第 2 段：看 Task 内怎样到达 Trial.create](../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md#queue-stage-2)。 |
| 4C. 跟到 Task 内部 · 回看 | [回看队列函数第 2 段：_run_trial → _execute_trial_with_retries](../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md#queue-stage-2) | 找到 trial = await Trial.create(trial_config) 后，[回到本步 Trial.create 卡：阅读创建主干](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline)。 |
| <a id="current-reading"></a>5. Trial.create · 当前 | [先恢复 Trial.create 的来路：Job 创建完成后怎样到这里](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#job-to-trial-create) → [读 Trial.create：取得题目并构造具体 Trial](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline) | 题目加载需要继续时，先建 Trial._load_task 卡（当前待建），Task.__init__ 按需再进入；读完[返回 Trial.create，继续 task.has_steps 的类型选择](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline)。 |
| 6. 创建 Agent 对象 · 待进入 | Trial.__init__ → _init_agent：均待建卡，实际进入时补链接 | 从 [Trial.create 卡的 SingleStepTrial(...) 构造处](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.create.md#trial-create-mainline)进入；读清 Agent 对象创建后，返回 Trial.__init__，继续环境初始化位置。 |
| 7. 到达环境入口 · 待进入 | Trial.__init__ 中的 _init_agent_environment 调用处：待相应函数卡建立后补链接 | 本步在调用位置停止；内部创建和启动环境交给 Step 013，不用外部源码链接代替函数卡。 |

[1]、[2]、[3]、[5] 已有函数卡；其余位置保留真实函数名及“待建卡”状态，不提前生成未读卡片。

**最小前置**：[回看 JobPlan 卡的配置例子：区分任务来源与题目文件配置](../../02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-config-example)。两类 TaskConfig 的源码出处留在卡片中，本节不直接跳到网络源码。

**本步留下什么**：能从一份 TrialConfig 指出“题目从哪里来、Agent 选谁、环境和验证要求从哪里取得”。安装、执行和评分代码不是完成此目标的前提。

**读后接续**：沿 Trial.__init__ 的 _init_agent_environment 进入 Step 013；本节当前只提供已存在的函数卡链接，后续实际进入时再补对应卡片。


<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0），本轮按本地 git show 定位相关符号；本地 main 与发布标签有差异，不混用。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](2026-11-12-before-call-order-scope.md)完整保留。本次只改 scope 与导航，不将未读函数提前建卡或标为掌握。

</details>
