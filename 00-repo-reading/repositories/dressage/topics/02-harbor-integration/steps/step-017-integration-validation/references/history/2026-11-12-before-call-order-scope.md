# 01 · Dressage Step 017：验证最小任务、Agent、K8s 与采集闭环

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [整体规划](../../../../../../references/topics-and-step-scopes-after-step006.md) · [前一范围](../../../step-016-cancellation-and-retries/01-scope.md)

> 状态：按已确认规划预先准备 scope；尚未据此开始逐函数阅读或实施验证。本步未创建短期、长期记忆及完成记录。

## 1. 阅读目标

**将前面已明确的接口串成一个可复跑案例，用真实结果检查接入、资源回收和失败处理，而不是继续增加泛读模块。**

## 2. 指挥官、入口条件与边界

1. **指挥官与入口**：[Harbor Job.run](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py) 是首个 API-only/确定性验证的执行入口，[Trial.run](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L345) 是单次尝试的观察主线。需要训练输出时，再使用已读的 generate_rollout_harbor_sync；不虚构一个新的统领函数。
2. **进入前已有**：先核对 Step 013 的兼容 Environment 是否已实现、选定 Harbor 版本是否可运行、任务/模型凭据和资源限制是否满足本次验证。当前 scope 只定义检查顺序，没有运行或创建资源。
3. **停止位置**：形成一份可复跑配置与结果记录：一题成功、换一个 Agent、少量并发/热领取、一次取消或重试；能指认输出、奖励、轨迹和已释放资源的证据。若只完成子集，如实保留其余缺口。
4. **本轮不展开**：不要求完整 GPU 训练、多集群、所有 Agent、全部隔离运行时或性能最优。没有瓶颈证据不做大规模压测。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

这是稳定的职责图，不是把所有异步回调合成同一调用栈。原生 blackbox_dispatch/Paddock/BlackboxServer 路线作为前序背景，不嵌入本图。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # Step 017 本步：训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_partition
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> Trial.run                    # Step 017 本步：一次尝试的组织者。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup        # 按配置准备所选 Agent。
                      -> _run
                           -> Agent.run          # 执行任务，并在过程中请求模型。
                           -> Verifier.verify    # 收集评测结果。
                      -> _finalize               # Step 017 本步：清理环境并发出生命周期事件。
                           == END 事件 ==> plugin._on_end
                                            -> commit_attempt
            <- JobResult 与插件结果
            -> _bundle_samples                   # Step 017 本步：训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

下面是计划验证的运行入口与检查点，不是本次已执行日志。先证明环境与验证链，再消耗模型调用；已有同等案例可直接复用。

```python
# 检查点一：一题 + Oracle/确定性执行 + 冷创建。
Harbor Job.run
  -> Trial.run
       -> Environment.start
       -> Agent.setup / Agent.run
       -> Verifier.verify
       -> Trial._finalize -> Environment.stop
  <- JobResult

# 检查点二：同一路线加入真实 Agent 与已适配的模型/采集合同。
Agent == HTTP ==> Gateway / 已选模型后端
Trial END ==> Dressage 结果与轨迹提交

# 检查点三：更换 Agent、少量并发、预热、一次取消或重试。
# 对齐每个 trial/attempt/session 和环境资源，核对最终产物及回收。
# 只有需要且具备真实训练字段时，再验证 Slime 批量返回。
```

<a id="reading-sequence"></a>

下表数字只表示本步阅读顺序。原始源码、调用方、子调用与返回位置分别列出；未读方法只链接源码，不预建函数卡。

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 复核运行前的具体合同 | [Environment 接缝](../../../step-013-harbor-kubernetes-environment/01-scope.md) 与 [模型接缝](../../../step-014-model-routing-and-api-contract/01-scope.md) | 列清实现完成项、缺失项和本次版本；不凭文档示例推断接口已经存在。 |
| 2. 冷创建基线 | [Job.run → Trial.run](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L345) | 用 Oracle/确定性任务核对文件、命令、Verifier、结果与删除；保存失败证据而非绕过。 |
| 3. 一个 Agent 的真实模型请求 | [任务/Agent 边界](../../../step-012-task-agent-verifier/01-scope.md) 与 [路由合同](../../../step-014-model-routing-and-api-contract/01-scope.md) | 取得一次真实请求、执行结果与采集收尾；区分任务成功和接口全部兼容。 |
| 4. 替换与并发验证 | [K8s 主题](../../../../../../../agent-sandbox/topics/kubernetes-sandbox-control/README.md) | 同题换一个 Agent；少量并发领取不同环境；证明热命中而非仅配置池名称。 |
| 5. 一次失败验证 | [取消与重试](../../../step-016-cancellation-and-retries/01-scope.md) | 核对最终尝试选择、取消后的环境与路由关闭；失败不能伪装成正常零分。 |
| 6. 整理可复跑证据 | [HarborArtifactStore](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L174) | 关联配置、代码/模型版本、输入、日志与产物；需要训练时另验真实 token/logprob/mask。 |

版本兼容与缺失接口可能阻塞某一检查点，必须先解决或明确记录；本页不把待适配的 K8s Environment、商业 API 控制接口或训练数据能力写成已经具备。

**读后接续**：完成选定验收后按结果决定修复或结束这一轮接入。完整 TITO、更多 Agent 和规模优化只由具体新问题触发。

<details>
<summary>源码版本与准备状态</summary>

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮通过本地源码定位入口、调用与返回边界。
- Harbor 使用 0.18.0 / 527d50deb63a5d279e8c20593c18a2cbc7f61f9e；沿用[前次固定版本证据](../../../../../../references/agent-sandbox-harbor-integration-evidence.json)。本轮未找到此前临时 Harbor 源码，也未重新下载，正式逐函数阅读时先恢复并核对该版本。
- 现有项目参考 /home/fredkeira/projects/slime_api_data_collecting，登记提交 151db30d1f4533773948695f4033ebe4353521d8；接口匹配以实际分支行为为准。
- [适配研究与版本差异](../../../../../../references/agent-sandbox-harbor-integration-research.md)保留来源。相关外部文档示例不自动证明当前版本可导入或可运行。
- 本页只有预备 scope。未执行 Harbor、模型、Kubernetes 或训练实验，不把范围准备当作用户已读、已掌握或验证完成。

</details>
