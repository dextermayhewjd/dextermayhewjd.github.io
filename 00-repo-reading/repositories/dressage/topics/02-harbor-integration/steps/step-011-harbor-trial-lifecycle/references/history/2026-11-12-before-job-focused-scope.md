# 01 · Dressage Step 011：看清一次 Harbor Trial 的准备、执行和结束

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [整体规划](../../../../../../references/topics-and-step-scopes-after-step006.md) · [前一范围](../../../step-010-harbor-rollout-entry/01-scope.md) · [后一范围](../../../step-012-task-agent-verifier/01-scope.md)

> 状态：2026-11-11 用户确认直接阅读 Harbor v0.25.0 发布版。本步从 Job.run 接到 Trial.run；保留旧版初读历史，不要求先读完 0.18，也不提前建立未读子函数卡。

## 1. 阅读目标

**建立 Harbor 中一次尝试的完整骨架，知道环境、Agent、Verifier 与 Dressage 回调分别处于哪里。**

## 2. 指挥官、入口条件与边界

1. **指挥官与入口**：先看 [Job.run:1082](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1082) 怎样组织 Trial，再进入 [Trial.run](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L601) 看一次尝试的编排。Step 010 的 Job 负责批量组织，Trial 负责一次具体尝试。
2. **进入前已有**：Step 010 已读 Dressage 创建 Job、挂接插件和调用 job.run 的意图。当前直接研究 Harbor 0.25 中一份有效 TrialConfig 的普通单步路径（install_only=False、无 user-agent bridge）。Dressage 源码仍锁定 0.18，跨版本运行兼容性尚未验证；该调用方背景不代表三方已经接通。
3. **停止位置**：能沿 _prepare → _run → _finalize 说明一份任务怎样尝试执行，并标出 START、AGENT_START、AGENT_END、VERIFICATION_START、CANCEL、END 的使用位置。
4. **本轮不展开**：只识别生命周期和调用归属；不一次展开所有 Agent、模型代理、环境实现和队列重试。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

这是接入职责图：Harbor 内部按 v0.25.0 核对，Dressage 部分保留调用方背景，接入兼容性待验证；不是把所有异步回调合成同一调用栈。原生 blackbox_dispatch/Paddock/BlackboxServer 路线作为前序背景，不嵌入本图。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> _run_trials_with_queue -> TrialQueue -> Trial.run  # 队列交接后进入一次尝试。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup        # 按配置准备所选 Agent。
                      -> _run
                           -> _run_agent         # 内部运行 Agent，并在过程中请求模型。
                           -> _collect_artifacts # 收集产物；按评测模式安排环境停止。
                           -> _run_verifier      # 内部运行评测；本步只认清交接。
                      -> _finalize               # 清理环境并发出生命周期事件。
                           == END 事件 ==> plugin._on_end
                                            -> commit_attempt
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

**本次先看上层交接：** [Job.run 本步函数卡](../../02-short-term-memory/functions/harbor/job.py/Job.run.md#job-mainline)；[Harbor Job.run:1082](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1082)，确认它经 [_run_trials_with_queue:1229](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1229) 提交并等待 Trial，最后汇总 JobResult；队列内部暂时只定位。随后接回 [Trial.run 已有函数卡](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle)。上游的 [_run_round](../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) 和 [_run_partition](../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline) 属于 Step 010，在此只保留导航。

编号对应下表阅读顺序；0.1 是 Job.run 内的下钻入口。第 5 项按登记、挂接、触发拆为 5A–5C；它是在读完生命周期后回查已有机制，实际登记早于 Job.run。

```python
[0] Job.run
  -> [0.1] _run_trials_with_queue        # 提交待运行配置，安排并等待协程，收集结果。
       -> TrialQueue.submit_batch       # 返回协程；由上层 TaskGroup 创建 Task 运行。
       # 队列内部先折叠：submit -> _run_trial -> _execute_trial_with_retries
       # 最终创建 Trial、挂接 hooks，再 await trial.run()。
# 以下展开队列实际运行的 Trial；不是说 0.1 直接调用它。
[1] Trial.run
  -> [2] _prepare                       # 准备环境与 Agent。
  -> [3] _run                           # 普通实现：SingleStepTrial._run。
       -> _run_agent
       -> _upload_agent_logs -> _collect_artifacts
       -> _run_verifier                  # 环境按 shared/separate 模式在评测前后停止。
  -> [4] run 的 finally
       -> _finalize                     # 收尾、保存结果、发出 END。
       -> _scrub_jobs_dir -> _close_logger_handler  # 回到 run，嵌套 finally 继续清理。
  -> [6] 返回 TrialResult，由 Job 汇总

# [5] 回查 END 注册与触发；5A–5C 是阅读顺序，不是三个函数直接相互调用。
# [5A] Job 运行前：登记函数，尚未执行这个回调。
DressageHarborPlugin.on_job_start
  -> Job.on_trial_ended -> Job.add_hook -> TrialQueue.add_hook
       # 包装后的 _on_end 存入队列的 END 回调列表。

# [5B] 队列创建一个 Trial 后、调用 trial.run 前：挂到具体 Trial。
TrialQueue._setup_hooks(trial)
  -> Trial.add_hook                      # 保存到该 Trial 的对应事件列表。

# [5C] Trial 执行到 _finalize：明确发出 END，再调用已登记的函数。
Trial._emit(TrialEvent.END)
  -> _safe 返回的 wrapper -> plugin._on_end(event)
       # event 带着当前结果；回调返回后继续 Trial 的收尾和正常返回。
# 整个 Job 汇总返回后，才在 _run_partition 执行 plugin.on_job_end(result)。
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 0. Job.run · 已看主干 | [本步 Job.run 函数卡](../../02-short-term-memory/functions/harbor/job.py/Job.run.md#job-mainline) · [源码 :1082](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1082) | 建立 JobResult → 等待 _run_trials_with_queue → 汇总返回；不展开 UI、恢复和全部指标；第二段的下钻入口是 0.1。 |
| 0.1. _run_trials_with_queue · 已看主干 | [本步函数卡](../../02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md#queue-mainline) · [源码 :1229](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1229) | 重点看 1309–1314 行：提交配置 → TaskGroup 等待 → 返回结果列表；读完回接 Job.run:1165。随后沿队列定位到 Trial.run，先不逐个展开队列包装。 |
| 1. Trial.run · 已看正常主干（v0.25.0） | [本步函数卡](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle) | 接清 _prepare → _run → finally 中 _finalize；本轮按正常生命周期阅读。 |
| 2. Trial._prepare · 已看主干 | [本步函数卡](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-mainline) · [Trial._prepare:641](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L641) | 识别 Environment 和 Agent 的准备归属，返回 Trial.run。 |
| 3. SingleStepTrial._run · 已看主干 | [本步函数卡](../../02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) · [SingleStepTrial._run:37](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L37) | 定位 _run_agent → 产物收集 → _run_verifier；认清环境停止与评测模式有关，再返回 Trial.run。 |
| 4. Trial._finalize · 已看主干 | [本步函数卡](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._finalize.md#finalize-mainline) · [Trial._finalize:660](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L660) | 找到环境收尾、结果记录与 END；回到 run 的嵌套 finally 完成目录和日志清理，再返回 TrialResult。 |
| <a id="current-reading"></a><a id="end-hook-registration"></a>5A. 登记回调 · 当前 | [on_job_start 登记段:407–414](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L407)；从 [Step 010 的调用现场](../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#run-job)回查 | 只追包装后的 _on_end 如何存入队列的 END 列表；明确此时保存函数而非调用。停在登记完成，接 5B；不通读插件配置与路由准备。 |
| 5B. 挂到具体 Trial | [TrialQueue._setup_hooks:112](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L112)，来自队列 [201–203 行](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L201) | 看 122–124 行怎样把队列回调挂到刚创建的 Trial；确认发生在 trial.run 前，接 5C。并发控制钩子只定位。 |
| 5C. 触发并调用 | 从 _finalize 的 END 调用进入 [Trial._emit:590](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L590) | 事件类型选回调列表，当前 result 装入事件；跟到 wrapper 调用 [_on_end:742](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L742) 即停。接收方内部不展开；沿原路返回后接第 6 项。 |
| 6. 沿正常返回链回到 Step 010 | [Job.run 的汇总返回](../../02-short-term-memory/functions/harbor/job.py/Job.run.md#job-mainline) → [_run_partition 第 3 段](../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#run-job) | TrialResult 经队列 Task 交回 Job，Job 汇总为 JobResult；_run_partition 接住后才调用 on_job_end(result)。与 5C 的单次 Trial 回调分开；结果归组沿用 Step 010。 |

**第 5 项的最小回查**：登记经过 [Job.on_trial_ended / add_hook](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L230)、[TrialQueue.add_hook:50](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L50)，挂接落在 [Trial.add_hook:552](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L552)；只需确认“转交、append 到事件列表”。[_safe:604–637](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L604) 只看“返回 wrapper”和“wrapper 内 await callback(event)”，异常处理暂缓。

**第 5 项停止标准**：能区分回调列表保存函数、event/result 携带数据、_emit 明确调用函数，以及 Job 返回后的 on_job_end 是另一调用。scope 只留此骨架与入口；实际展开时按函数记录，不再以跨函数 reference 代替主线，也不提前生成未读卡片。

本轮进入 Trial.run 前，最后一个计划单独阅读的函数是 **0.1 _run_trials_with_queue**。中间的队列包装只定位：见 [TrialQueue:194–260](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L194)。这是一项阅读边界，不表示实际代码没有中间调用；以后若并发或重试成为具体问题，再回查。

最小边界：Agent 执行结果、Verifier 分数和 Trial 成败不是同一个概念；取消事件与最终 END 也不能互相替代。上图为正常路径教学裁剪，省略检查、日志和异常恢复；环境可能在 _run 中先停止，不把 _finalize 当作唯一停止位置。

**读后接续**：读后进入 Step 012，先用一个任务例子说明 Task、Agent 和 Verifier 怎样替换。

<details>
<summary>源码版本与准备状态</summary>

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮通过本地源码定位入口、调用与返回边界。
- Harbor 当前阅读版本：v0.25.0 / fdba28fc411e47e8765420a1a063b4918fce3def。通过本地 /home/fredkeira/projects/harbor 的 git show 读取发布标签，未切换本地 main；main 不等于此发布版。
- [切换前的 0.18 scope 与记录](2026-11-11-harbor-018-before-025/01-scope.md)保留历史；03 继承快照不改写。Step 012–017 现有 scope 仍有旧版证据，实际进入时按目标版本核对，不预先宣称已全部迁移。
- 现有项目参考 /home/fredkeira/projects/slime_api_data_collecting，登记提交 151db30d1f4533773948695f4033ebe4353521d8；接口匹配以实际分支行为为准。
- [适配研究与版本差异](../../../../../../references/agent-sandbox-harbor-integration-research.md)保留来源。相关外部文档示例不自动证明当前版本可导入或可运行。
- _run_round、_run_partition 卡片已归回 Step 010；本步已有 Job、队列与 Trial 生命周期的函数记录。第 5 项新导航仍链接源码，单独函数卡随实际展开再建。未执行 Harbor、模型、Kubernetes 或训练实验，不将卡片建立视为掌握或验证完成。

</details>
