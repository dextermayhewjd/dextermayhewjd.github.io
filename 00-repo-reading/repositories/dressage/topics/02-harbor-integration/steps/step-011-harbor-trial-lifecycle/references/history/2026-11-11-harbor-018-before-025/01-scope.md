# 01 · Dressage Step 011：看清一次 Harbor Trial 的准备、执行和结束

[主题入口](../../../../../README.md) · [项目进度](../../../../../../../README.md) · [整体规划](../../../../../../../references/topics-and-step-scopes-after-step006.md) · [前一范围](../../../../step-010-harbor-rollout-entry/01-scope.md) · [后一范围](../../../../step-012-task-agent-verifier/01-scope.md)

> 状态：2026-11-11 在 Step 010 收束后接续本步。保留先前 Trial.run 初读，当前从已有卡恢复正常生命周期主干，再按问题进入子方法；未提前建立新子函数卡。

## 1. 阅读目标

**建立 Harbor 中一次尝试的完整骨架，知道环境、Agent、Verifier 与 Dressage 回调分别处于哪里。**

## 2. 指挥官、入口条件与边界

1. **指挥官与入口**：[Trial.run](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L322) 是本步编排入口。Step 010 的 Job 负责批量组织，Trial 负责一次具体尝试。
2. **进入前已有**：Step 010 创建并运行 Harbor Job，插件已接入。本步沿一份有效 TrialConfig 进入普通单步 Trial；批次分区、Job 创建与组结果整理回查 Step 010。
3. **停止位置**：能沿 _prepare → _run → _finalize 说明一份任务怎样尝试执行，并标出 START、AGENT_START、AGENT_END、VERIFICATION_START、CANCEL、END 的使用位置。
4. **本轮不展开**：只识别生命周期和调用归属；不一次展开所有 Agent、模型代理、环境实现和队列重试。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

这是稳定的职责图，不是把所有异步回调合成同一调用栈。原生 blackbox_dispatch/Paddock/BlackboxServer 路线作为前序背景，不嵌入本图。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> Harbor 调度器 -> Trial.run                    # Step 011 本步：一次尝试的组织者。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup        # 按配置准备所选 Agent。
                      -> _run
                           -> Agent.run          # 执行任务，并在过程中请求模型。
                           -> Verifier.verify    # 收集评测结果。
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

**本次先看上层交接：** [Harbor Job.run:729](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L729)，确认它经 [_run_trials_with_queue:861](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L861) 提交并等待 Trial，最后汇总 JobResult；队列内部暂时只定位。随后接回 [Trial.run 已有函数卡](../../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle)。上游的 [_run_round](../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) 和 [_run_partition](../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline) 属于 Step 010，在此只保留导航。

编号对应下表阅读顺序；插件注册实际先于 Job.run，单独画出，避免与事件触发混为同一次调用。

```python
# [0] 上层交接：_run_partition -> Job.run -> _run_trials_with_queue -> TrialQueue。
# 队列内部尚未逐段展开；以下单独看被执行的 Trial 生命周期。
[1] Trial.run
  -> [2] _prepare                       # 准备环境与 Agent。
  -> [3] _run                           # 普通实现：SingleStepTrial._run。
       -> Agent.run
       -> Verifier.verify
  -> [4] _finalize                      # 清理环境、保存结果、发出结束事件。
  -> [6] 返回 TrialResult，由 Job 汇总

# [5] 回查事件如何接入；注册发生在上面的 Trial 执行之前。
DressageHarborPlugin.on_job_start
  -> 注册 Trial / Agent / Verifier / 取消 / 结束回调
# Trial 到达相应阶段时，事件才触发对应回调。
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| <a id="current-reading"></a>0. Job.run · 当前上层交接 | [源码 :729](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L729) | 建立 JobResult → 等待 _run_trials_with_queue → 汇总返回；不展开 UI、恢复和全部指标，接回下面 Trial 主干。 |
| 1. Trial.run · 已有初读 | [本步函数卡](../../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle) | 接清 _prepare → _run → finally 中 _finalize；本轮按正常生命周期阅读。 |
| 2. 准备区域 | [Trial._prepare:352](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L352) | 识别 Environment 和 Agent 的准备归属，返回 Trial.run。 |
| 3. 执行区域 | [SingleStepTrial._run:34](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/single_step.py#L34) | 定位 Agent.run 与 Verifier.verify，返回 Trial.run 进入收尾。 |
| 4. 结束区域 | [Trial._finalize:359](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L359) | 找到环境停止、结果记录与事件交接，返回 TrialResult。 |
| 5. 回查插件接入 | [on_job_start:400](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L400) | 对齐事件与回调注册；具体回调内部留到后续对应步骤。 |
| 6. 返回上游 | [Step 010 的结果归组](../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#collect-outcomes) | 知道 Trial 结果由 Job 汇总，再回到 Dressage；本步不重复展开批次处理。 |

最小边界：Agent 执行结果、Verifier 分数和 Trial 成败不是同一个概念；取消事件与最终 END 也不能互相替代。

**读后接续**：读后进入 Step 012，先用一个任务例子说明 Task、Agent 和 Verifier 怎样替换。

<details>
<summary>源码版本与准备状态</summary>

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮通过本地源码定位入口、调用与返回边界。
- Harbor 使用 0.18.0 / 527d50deb63a5d279e8c20593c18a2cbc7f61f9e；沿用[前次固定版本证据](../../../../../../../references/agent-sandbox-harbor-integration-evidence.json)。当前无本地 Harbor checkout；本轮已在线核对该固定版本 trial.py 与 single_step.py，未下载或安装运行环境。
- 现有项目参考 /home/fredkeira/projects/slime_api_data_collecting，登记提交 151db30d1f4533773948695f4033ebe4353521d8；接口匹配以实际分支行为为准。
- [适配研究与版本差异](../../../../../../../references/agent-sandbox-harbor-integration-research.md)保留来源。相关外部文档示例不自动证明当前版本可导入或可运行。
- _run_round、_run_partition 卡片已归回 Step 010；本步保留 Trial.run 初读记录，其他入口仅导航。未执行 Harbor、模型、Kubernetes 或训练实验，不将卡片建立视为掌握或验证完成。

</details>
