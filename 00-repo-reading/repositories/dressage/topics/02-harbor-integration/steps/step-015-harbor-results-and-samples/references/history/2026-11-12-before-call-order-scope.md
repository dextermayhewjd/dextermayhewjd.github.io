# 01 · Dressage Step 015：将 Trial 结果、奖励与轨迹交成上层产物

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [整体规划](../../../../../../references/topics-and-step-scopes-after-step006.md) · [前一范围](../../../step-014-model-routing-and-api-contract/01-scope.md) · [后一范围](../../../step-016-cancellation-and-retries/01-scope.md)

> 状态：按已确认规划预先准备 scope；尚未据此开始逐函数阅读或实施验证。本步未创建短期、长期记忆及完成记录。

## 1. 阅读目标

**看清一次尝试结束后，哪份结果被持久化、哪份被选为最终尝试，以及训练路线怎样取得 Sample 组。**

## 2. 指挥官、入口条件与边界

1. **指挥官与入口**：[DressageHarborPlugin._on_end / _finalize_attempt](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L742) 接住 END 事件；[HarborArtifactStore.commit_attempt](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L256) 组织一次尝试的收尾与产物。
2. **进入前已有**：已有 TrialResult、attempt/session 标识和本次模型轨迹。先选正常成功的最终尝试与 disk/both 产物模式，复用原生 Step 008 的 Sample 字段背景；API-only 与训练消费分别标明。
3. **停止位置**：能用同一组标识对齐任务、物理尝试、奖励、轨迹与 bundle；区分保存成功、被选中、trainable 和已返回 Slime。
4. **本轮不展开**：不展开所有存储格式、所有失败恢复和完整归一化算法；训练字段仅追本次数据流需要的内容。

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
                 -> Trial.run                    # 一次尝试的组织者。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup        # 按配置准备所选 Agent。
                      -> _run
                           -> Agent.run          # 执行任务，并在过程中请求模型。
                           -> Verifier.verify    # 收集评测结果。
                      -> _finalize               # Step 015 本步：清理环境并发出生命周期事件。
                           == END 事件 ==> plugin._on_end
                                            -> commit_attempt
            <- JobResult 与插件结果
            -> _bundle_samples                   # Step 015 本步：训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

END 回调与外层 Job 返回不是同一条简单调用栈。先看事件触发的提交，再回到 _run_partition 查询插件结果。下面保留关键数据与等待关系。

```python
Trial._finalize == END 事件 ==> plugin._on_end
  -> create_task(_finalize_attempt(...))
  -> await shield(finalize_task)
       -> commit_attempt(...)
            -> _commit_attempt_once(...)
                 -> ProxyClient.finalize_session(...)
                 -> ProxyClient.read_trajectory(..., drain=False)
                 -> 校验并保存 bundle
                 -> ProxyClient.read_trajectory(..., drain=True)
       <- HarborTrajectoryBundle
       -> 关闭本次路由与凭据归属

# Job 完成后，回到外层批次：
_run_partition
  -> plugin.get_result(trial_name, final_result.id)
  -> _bundle_samples(...) -> expand_segments_to_samples(...)
  <- 分组结果 -> groups, metrics -> RolloutFnTrainOutput
```

<a id="reading-sequence"></a>

下表数字只表示本步阅读顺序。原始源码、调用方、子调用与返回位置分别列出；未读方法只链接源码，不预建函数卡。

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. END 的触发位置 | [Trial._finalize](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py) | 确认事件带哪个物理尝试结果；再进入插件回调。 |
| 2. 插件只启动一份最终处理 | [_on_end / _finalize_attempt](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L742) | 看 finalize_task、等待与清理边界；先走正常路径。 |
| 3. 一次尝试的持久化 | [commit_attempt](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L256) | 按 trial_name/trial_id 找提交 Task，理解一次尝试的重复 END 如何接回同一处理。 |
| 4. 轨迹读取与保存次序 | [_commit_attempt_once](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L304) | 定位 finalize、非破坏性读取、校验/保存、再 drain；不把已读到轨迹当作已持久化。 |
| 5. 返回批次选择结果 | [_run_partition](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L763) | 按 JobResult 的最终 trial id 调 plugin.get_result；区分旧尝试与最终尝试。 |
| 6. 转换训练输出 | [_bundle_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L624) | 看 trainable、reward_key 与 Sample 元数据；回到 Step 010 的返回对象。 |

最小边界：正常低分可以是合法结果，执行失败或不满足训练合同则不能伪装成正常零分。API-only 产物与 _bundle_samples 要求的 trainable bundle 分别验收。

**读后接续**：读后进入 Step 016，用一种取消/超时案例检查这些归属和提交规则是否仍成立。

<details>
<summary>源码版本与准备状态</summary>

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮通过本地源码定位入口、调用与返回边界。
- Harbor 使用 0.18.0 / 527d50deb63a5d279e8c20593c18a2cbc7f61f9e；沿用[前次固定版本证据](../../../../../../references/agent-sandbox-harbor-integration-evidence.json)。本轮未找到此前临时 Harbor 源码，也未重新下载，正式逐函数阅读时先恢复并核对该版本。
- 现有项目参考 /home/fredkeira/projects/slime_api_data_collecting，登记提交 151db30d1f4533773948695f4033ebe4353521d8；接口匹配以实际分支行为为准。
- [适配研究与版本差异](../../../../../../references/agent-sandbox-harbor-integration-research.md)保留来源。相关外部文档示例不自动证明当前版本可导入或可运行。
- 本页只有预备 scope。未执行 Harbor、模型、Kubernetes 或训练实验，不把范围准备当作用户已读、已掌握或验证完成。

</details>
