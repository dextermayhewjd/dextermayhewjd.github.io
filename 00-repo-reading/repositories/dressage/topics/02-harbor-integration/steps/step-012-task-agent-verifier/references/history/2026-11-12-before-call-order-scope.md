# 01 · Dressage Step 012：区分任务、Agent 与评测的替换位置

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [前一步总结](../../../step-011-harbor-trial-lifecycle/05-task-flow.md) · [下一步环境接口](../../../step-013-harbor-kubernetes-environment/01-scope.md)

> 状态：2026-11-12 按用户要求开始接续，源码校准为 Harbor v0.25.0。只用一个 hello-world 任务看清配置与接口；已有生命周期知识直接复用，尚未运行任务或验证三方兼容。

## 1. 阅读目标

**用一个具体任务看清：题目是什么、由哪个 Agent 做、用什么规则评测；换这三者分别改哪里。** 为 Step 013 接沙箱提供边界，不重新通读安装、队列或完整执行过程。

## 2. 指挥官、入口条件与边界

1. **本轮入口**：[JobPlan.build_trial_configs:140](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job_plan.py#L140)。v0.25.0 的 Job._init_trial_configs 在普通分支经 _build_standard_trial_configs 委派到这里，将任务来源、Agent 与运行配置组成 TrialConfig。
2. **进入时已有**：JobConfig 与已经解析的任务来源列表；先用一个任务、一个 Agent、一次尝试理解。任务样本为 [examples/tasks/hello-world](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/examples/tasks/hello-world)，不运行远端依赖或安装脚本。
3. **停止位置**：能指出换题目来源、换 Agent 名称/模型、换题目验证规则的位置，以及这些配置在哪个已读 Trial 阶段被使用。
4. **本轮暂缓**：数据集下载器、全部配置校验、其他 Agent、安装脚本细节、并行调度、独立评测环境内部和 Proxy 协议。它们不构成本步结束门槛。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

沿用 Step 010、011 的整体主线，只标出 Step 012 关注的配置、Agent 与评测位置。具体从哪个函数读、读到哪里停，见 3.2。Harbor 按 v0.25.0 核对，Dressage 保留原调用方背景；这不是跨版本运行验证，也不把回调画成同一条同步调用栈。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> _CREATE_JOB(job_config)          # Step 012 当前回查：创建 Job 时怎样组成 TrialConfig。
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> _run_trials_with_queue -> TrialQueue -> Trial.run  # 队列交接后进入一次尝试。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup        # Step 012：已选 Agent 的配置在这里被使用。
                      -> _run
                           -> _run_agent         # Step 012：题目 instruction 在这里交给 Agent。
                           -> _collect_artifacts # 收集产物；按评测模式安排环境停止。
                           -> _run_verifier      # Step 012：题目的验证规则与评分在这里被使用。
                      -> _finalize               # 清理环境并发出生命周期事件。
                           == END 事件 ==> plugin._on_end
                                            # 回调内部的轨迹处理留到实际接入时回查。
            <- JobResult 与插件结果
            -> _bundle_samples                   # 训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

```python
# [1] 当前：运行安排怎样变成每一次尝试的配置。
JobConfig + 任务来源列表
  -> JobPlan.build_trial_configs(...)
  -> list[TrialConfig]

# [2] 追一份题目：来源路径对应哪些文件。
Task.__init__(task_dir, ...)
  -> task.toml + instruction.md + environment/ + tests/

# [3] 复用已读准备阶段：只认清所选 Agent 从哪里来。
Trial._prepare -> agent.setup(environment)

# [4] 验证入口：题目的检查怎样给出评分。
SingleStepTrial._run -> _run_verifier -> Verifier.verify(...)

# [5] 回到同一例子：分清换题、换 Agent、换评测、换环境的位置。
```

编号是阅读顺序，不表示 Task 构造发生在 Job 计划构造的同一调用栈。每次只打开当前入口；下面是导航，不是待逐行通读的函数清单。

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 看清什么后停、回哪里 |
| --- | --- | --- |
| <a id="current-reading"></a>1. 组成 Trial 配置 · 当前 | [本步函数卡](../../02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-plan-mainline) · [源码:140](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job_plan.py#L140) | 任务来源、Agent 配置、尝试次数怎样组成列表；其余运行参数只认继承关系，随后选一份任务看 [2] |
| 2. 一份题目的文件 | [Task.__init__:51](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/task/task.py#L51) · [hello-world](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/examples/tasks/hello-world) | 看 instruction、task.toml、环境定义与 tests 的用途，不遍历所有字段；接 [3]/[4] |
| 3. Agent 选择与准备 · 短回顾 | [AgentConfig:65](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L65) · [已读 _prepare](../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-mainline) | 选择来自运行配置；setup/install 复用前一步，只有具体不清楚时再看源码 |
| 4. 题目的评测 | [已读执行入口](../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) · [Verifier.verify:198](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/verifier/verifier.py#L198) | 对上本题 tests/test.sh、检查规则、reward 文件和返回值；不深入完整评分框架 |
| 5. 替换位置与返回主线 | [JobConfig:399](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/job/config.py#L399) · [TrialConfig:488](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L488) | 用同一道题区分改任务、Agent、验证规则与环境；读后进入 Step 013 的环境接口 |

**避免同名混淆**：`models/trial/config.py::TaskConfig`（:398）是任务来源引用，例如目录路径；`models/task/config.py::TaskConfig`（:853）是题目 task.toml 的内容。第 [1] 项使用前者，不是把整份 task.toml 直接传给组装函数。

**按需回查，不重复必读**：[BaseInstalledAgent.setup:1126](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/base.py#L1126)、[ClaudeCode.install:635](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/claude_code.py#L635)、[Codex.install:653](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/agents/installed/codex.py#L653)。安装/执行失败与正常低分仍须分开理解。

<details>
<summary>版本校准与当前记录边界</summary>

- 当前使用 v0.25.0 发布提交 fdba28fc411e47e8765420a1a063b4918fce3def；通过本地 git show 读取，不把 main 当作发布版，也没有切换 checkout。
- [原 0.18 预备 scope](2026-11-12-harbor-018-scope.md)保留。旧 Job._init_trial_configs 入口在新版普通路径中委派给 JobPlan；当前源码定位已逐项更新。
- 前序记录按 Step 011 的 03 + 02 完整继承；只在实际阅读时调入本步 02，不预建其他函数卡。
- Dressage 仍固定其源码提交和 Harbor 0.18 依赖；本步阅读不是已完成升级或接入。无 Job、模型、安装、容器或集群运行证据。

</details>
