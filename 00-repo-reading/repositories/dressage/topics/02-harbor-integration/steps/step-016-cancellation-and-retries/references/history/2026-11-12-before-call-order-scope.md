# 01 · Dressage Step 016：追通一次并发中的取消与重试

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [整体规划](../../../../../../references/topics-and-step-scopes-after-step006.md) · [前一范围](../../../step-015-harbor-results-and-samples/01-scope.md) · [后一范围](../../../step-017-integration-validation/01-scope.md)

> 状态：按已确认规划预先准备 scope；尚未据此开始逐函数阅读或实施验证。本步未创建短期、长期记忆及完成记录。

## 1. 阅读目标

**在已有正常生命周期上，追踪一次取消或超时，明确环境、模型路由和结果各由谁收尾。**

## 2. 指挥官、入口条件与边界

1. **指挥官与入口**：[TrialQueue 的执行与重试入口](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/queue.py#L194) 负责批量运行边界；本步核心故障路径沿 Trial._finalize 到插件 _on_cancel/_on_end。
2. **进入前已有**：已完成正常路径的接口阅读。先选一个可控情景：两项尝试中外部取消一项。超时与重试按实际条件对照，不假定所有超时都会触发相同 CANCEL 事件。
3. **停止位置**：写清并发限制、取消传播、环境所有权、END 提交与重试身份；能够提出或执行一个小验证，证明被取消尝试不成为可训练成功结果且不重复提交。
4. **本轮不展开**：不重写队列，不通读所有错误类别和原生 AsyncRolloutWorker；多集群/大规模压力测试不属于本步。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

这是稳定的职责图，不是把所有异步回调合成同一调用栈。原生 blackbox_dispatch/Paddock/BlackboxServer 路线作为前序背景，不嵌入本图。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_partition
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> Trial.run                    # Step 016 本步：一次尝试的组织者。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup        # 按配置准备所选 Agent。
                      -> _run
                           -> Agent.run          # 执行任务，并在过程中请求模型。
                           -> Verifier.verify    # 收集评测结果。
                      -> _finalize               # Step 016 本步：清理环境并发出生命周期事件。
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

取消回调不是最终清理的替代者。下面突出一个具体约束：CANCEL 标记尝试，后续 END 仍负责最终关闭。重试在其外层决策，不画成同一 Agent 继续运行。

```python
TrialQueue._execute_trial_with_retries(...)
  -> Trial.run(...)                    # 每次物理尝试有自己的身份。
       ...  # 选定的外部取消发生在执行期间。
       == CANCEL 事件 ==> plugin._on_cancel
                            -> 标记 cancel_requested / poisoned
                            -> 必要时 _quiesce(...)
       -> Trial._finalize(...)         # 环境处理与 END 归属在此核对。
       == END 事件 ==> plugin._on_end
                         -> _finalize_attempt(...)
                              -> 取消分支不生成训练 bundle
                              -> finally: _close_attempt(...)
  -> 按策略决定是否创建新的尝试         # 核对新旧身份及最终结果选择。
```

<a id="reading-sequence"></a>

下表数字只表示本步阅读顺序。原始源码、调用方、子调用与返回位置分别列出；未读方法只链接源码，不预建函数卡。

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 定位并发与重试所有者 | [TrialQueue](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/queue.py#L194) | 只找并发限制、执行调用与重试判定；为选定情景记录输入和出口。 |
| 2. 取消怎样到达最终处理 | [Trial.run / _finalize](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L345) | 追选定的取消路径，查环境停止是否仍被调用；超时行为只按实际分支对照。 |
| 3. CANCEL 回调 | [_on_cancel](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L731) | 看尝试标记与 quiesce；这里不直接替代 END 的最终关闭。 |
| 4. END 回调与清理 | [_on_end / _finalize_attempt](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L742) | 追取消分支和 finally 的 _close_attempt；确认训练产物是否允许产生。 |
| 5. 重试后的结果选择 | [_run_partition](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L763) | 区分逻辑任务、物理 trial id、attempt_ordinal、session；查旧结果是否会被误当最终结果。 |
| 6. 核对资源和产物 | [Step 013 的环境合同](../../../step-013-harbor-kubernetes-environment/01-scope.md) 与 [Step 015 的提交合同](../../../step-015-harbor-results-and-samples/01-scope.md) | 只用选定故障验证清理与提交；看清后停止继续枚举分支。 |

验证应区分取消信号发出、后台收尾完成和远端环境实际释放。没有运行证据时只记录待验证条件，不写成“已证明不泄漏”。

**读后接续**：读后进入 Step 017，把前面局部验证串成最小可复跑的整合记录。

<details>
<summary>源码版本与准备状态</summary>

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮通过本地源码定位入口、调用与返回边界。
- Harbor 使用 0.18.0 / 527d50deb63a5d279e8c20593c18a2cbc7f61f9e；沿用[前次固定版本证据](../../../../../../references/agent-sandbox-harbor-integration-evidence.json)。本轮未找到此前临时 Harbor 源码，也未重新下载，正式逐函数阅读时先恢复并核对该版本。
- 现有项目参考 /home/fredkeira/projects/slime_api_data_collecting，登记提交 151db30d1f4533773948695f4033ebe4353521d8；接口匹配以实际分支行为为准。
- [适配研究与版本差异](../../../../../../references/agent-sandbox-harbor-integration-research.md)保留来源。相关外部文档示例不自动证明当前版本可导入或可运行。
- 本页只有预备 scope。未执行 Harbor、模型、Kubernetes 或训练实验，不把范围准备当作用户已读、已掌握或验证完成。

</details>
