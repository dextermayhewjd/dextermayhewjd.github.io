# 01 · Dressage Step 010：找到 Slime 与 Harbor 的批量交接入口

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [整体规划](../../../../references/topics-and-step-scopes-after-step006.md) · [前一范围](../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/01-scope.md) · [后一范围](../step-011-harbor-trial-lifecycle/01-scope.md)

> 状态：2026-11-11 用户确认本步主线阅读结束。数据源、分区、Job/插件与结果返回的必要交接已补读；未将全部辅助函数、异常或运行验证计为完成。接续 Step 011 已有 Trial.run 入口。

## 1. 阅读目标

**看清一批任务怎样从 Slime 交给 Dressage，再由 Dressage 创建并运行 Harbor Job。**

## 2. 指挥官、入口条件与边界

1. **指挥官与入口**：[generate_rollout_harbor_sync](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1257) 是外层入口；内部以 _run_harbor_rollout 组织批次，_run_round 负责本轮分区和调度，_run_partition 组织一次 Harbor Job。
2. **进入前已有**：已有原生 generate 的整体背景。当前只选 evaluation=False、配置有效的一批任务，输入包括 args、rollout_id、HarborDataSource；不把单条 Sample 回调误作整批入口。 数据源的配置、spec 与运行指纹来源作为本步前置回查，入口见下方 3.2。
3. **停止位置**：接清 pending → 分区 → Job/插件 → 各组 outcomes → Sample 组与 metrics。job.run 内部的 Trial 生命周期交给 Step 011；结果字段的详细转换留到 Step 015。
4. **本轮不展开**：不重读 Slime 训练主循环，不展开所有批次重试、数据源持久化或权重校验规则。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

这是稳定的职责图，不是把所有异步回调合成同一调用栈。原生 blackbox_dispatch/Paddock/BlackboxServer 路线作为前序背景，不嵌入本图。

当前同步训练路径由 Slime 外层按 rollout_id 反复调用 rollout hook；下图展示其中一批的交接。_run_harbor_rollout 内部的 pending 循环属于这一批，不是外层训练批次循环。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # Step 010 本步：训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> Trial.run                    # 一次尝试的组织者。
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

**当前接续：** 2026-11-11 已接清父函数第 5、6 段，回到第 8 项批次出口：ordered 与 metrics 返回外层训练包装。本轮主线可收束，未把所有辅助实现和异常分支列为已读。

**前置回查：** [HarborDataSource.__init__ 函数卡](02-short-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.__init__.md#data-source-precondition)。数据源在进入 rollout 前已创建，读清配置与规格来源后回到父函数第 1 段；具体说明集中在函数卡。

下图为教学裁剪，编号对应下方阅读表。缩进表示调用归属；第 6、7 项是子调用返回后，父函数继续执行的部分。

```python
# [1] 训练脚本用 rollout-function-path 选择下面的入口。
[2] generate_rollout_harbor_sync
  -> run(_run_harbor_rollout(...))
       [3] _run_harbor_rollout               # 准备配置、模板组和 pending。
         -> [4] await _run_round(...)
              -> _partition_work(...)       # 按运行配置分区。
              -> run_partition(...)         # 内部包装：取得额度，结束后归还。
                   -> [5] await _run_partition(...)
                        -> await _CREATE_JOB(...)
                        -> _assign_partition_trials(...)  # 当前局部下钻：建立模板与身份对应。
                        -> _PLUGIN_FACTORY(...)
                        -> await plugin.on_job_start(...)
                        -> result = await job.run()  # Trial 内部留到 Step 011。
                        -> await plugin.on_job_end(...)
                        -> 整理各组 outcome，并完成清理
              -> 汇总并返回 outcomes
         [6] 接住 outcomes，更新 completed / next_pending
         [7] 恢复顺序、验收，返回 ordered, metrics
  [8] 包装为 RolloutFnTrainOutput
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 前置：数据源与规格来源 | [HarborDataSource.__init__](02-short-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.__init__.md#data-source-precondition) | 看 __init__ 的两份配置、_build_registry 的 spec/指纹和 _spec_by_id；返回第 3 项父函数读取 integration_config 的位置。 |
| 1. 训练脚本 hook | [训练脚本](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh#L66) | 对齐 data-source-path 与 rollout-function-path，进入批量入口。 |
| 2. 批量入口 | [generate_rollout_harbor_sync](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/generate_rollout_harbor_sync.md#batch-entry) | 看输入与同步等待，进入 _run_harbor_rollout；返回包装留到第 8 项。 |
| 3. 批次父流程 | [_run_harbor_rollout](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md#pending-and-outcomes) | 父函数六段已有介绍；从第 3 段的 outcomes = await _run_round(...) 进入第 4 项。 |
| 4. 本轮分区与调度 | [_run_round](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) | 看 pending → partitions → 额度约束下运行各区 → 展平结果。内部 run_partition 委派到第 5 项。 |
| 5. 创建并运行 Job | [_run_partition](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline) | 看创建 Job、绑定模板与插件、job.run、结果归组。返回 _run_round 汇总，再回父函数；不深入 Trial 或转换 helper。 |
| 6. 回到父函数收集结果 | [父函数接回 outcomes](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md#receive-outcomes) | 接清 completed、next_pending 和失败组去向；区分本批内的重试与下一批。 |
| 7. 组织批次与验收 | [父函数第 4–6 段](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md#restore-order) | 按原位置组成 ordered，检查有效性/版本并汇总 metrics。 |
| <a id="current-reading"></a>**8. 返回外层 · 本轮停止处** | [外层返回源码](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1264) | 确认 Sample 组和指标包装为训练输出，在此停止。 |

最小边界：_run_harbor_rollout 要求 HarborDataSource 处于 training 模式，并校验 Proxy 能力。不能把 API-only Job 的成功当成训练 hook 已经兼容。

**读后接续**：本步补读后接回 [Step 011 的 Trial.run](../step-011-harbor-trial-lifecycle/01-scope.md#reading-navigation)。保留此前初读事实，不重复开启一个新步骤。

<details>
<summary>源码版本与准备状态</summary>

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮通过本地源码定位入口、调用与返回边界。
- Harbor 使用 0.18.0 / 527d50deb63a5d279e8c20593c18a2cbc7f61f9e；沿用[前次固定版本证据](../../../../references/agent-sandbox-harbor-integration-evidence.json)。本轮未找到此前临时 Harbor 源码，也未重新下载，正式逐函数阅读时先恢复并核对该版本。
- 现有项目参考 /home/fredkeira/projects/slime_api_data_collecting，登记提交 151db30d1f4533773948695f4033ebe4353521d8；接口匹配以实际分支行为为准。
- [适配研究与版本差异](../../../../references/agent-sandbox-harbor-integration-research.md)保留来源。相关外部文档示例不自动证明当前版本可导入或可运行。
- 本步已开始外层入口的静态阅读。未执行 Harbor、模型、Kubernetes 或训练实验，批次/Job 内部不视为已读。

</details>
