# 01 · Dressage Step 015：收集产物、执行评测并交付最终结果

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一范围](../step-014-model-routing-and-api-contract/01-scope.md) · [下一范围](../step-016-cancellation-and-retries/01-scope.md)

> 状态：2026-11-12 按真实调用交接调整。本页是已确认的后续 scope；本轮只更新范围与导航，尚未开始本步阅读或创建函数卡。 Harbor 入口统一依据 v0.25.0 发布版；没有运行任务、安装、模型或集群验证。

## 1. 阅读目标

**用同一次尝试接清产物、评测结果、模型轨迹和最终选用结果；需要训练时再核对 Sample 的数据合同。**

## 2. 指挥官、入口条件与边界

1. **主线入口**：[SingleStepTrial._run:41–54](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L41) 接住 Agent 执行之后的阶段；核心问题从题目 tests 与 [Verifier.verify:198](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/verifier/verifier.py#L198) 的评分交接开始。
2. **已有输入**：题目与验证规则、已执行 Agent、相关输出与 attempt/session 标识。先沿 shared 评测、正常成功路径；separate 的环境差别只回查 Step 013 的合同。
3. **后续交接**：回到 Trial._finalize 的 END，再由插件提交轨迹 bundle；整个 Job 返回后，_run_partition 选择最终尝试并转换 Sample。这两段不能画成同一直接调用。
4. **停止位置**：同一任务、物理尝试、评分、轨迹和 bundle 能对应起来；分清保存、最终选用、trainable 和实际返回训练入口。已有 Step 007/008/010 的通用 finalize/read、分段转换和 manifest 职责不重新逐函数读。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

沿用 Step 010、011 的整体主线，各步保持相同图形结构。**本步接 Agent 执行之后的日志/产物与 Verifier，再跟到 END 的轨迹提交和 Job 返回；已读转换与存储职责直接复用。** 具体入口与返回位置见 3.2；图中回调和 HTTP 均标明交互方式，不当作同一同步调用栈。

图内标注直接对应本步：**[本步]** 是当前展开位置，**[交给 Step …]** 是停止与交接位置；其余节点保留作整体背景。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> _CREATE_JOB(job_config)          # 创建 Job 时组成各次尝试的配置。
            -> plugin.on_job_start(job)          # 挂接路由配置与生命周期回调。
            -> Harbor Job.run
                 -> _run_trials_with_queue -> TrialQueue -> Trial.run  # 队列交接后进入一次尝试。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup        # 环境就绪后准备已选定的 Agent。
                      -> _run
                           -> _run_agent         # 把题目交给 Agent，执行中请求模型。
                           -> _collect_artifacts  # [本步] 接前面的日志上传，收集本次任务产物。
                           -> _run_verifier  # [本步] 进入 Verifier.verify，执行测试并读取评分。
                      -> _finalize  # [本步] 接回 END 触发位置；已读清理不重复深挖。
                           == END 事件 ==> plugin._on_end  # [本步] _finalize_attempt / commit_attempt 提交本次轨迹与结果。
                                            # 此处只展开当前尝试的正常提交，具体入口见 3.2。
            <- JobResult  # [本步] 单次结果汇总成 Job 结果，回到 _run_partition。
            -> plugin.on_job_end(...)           # 整份 Job 返回后的插件收尾。
            -> _bundle_samples  # [本步按需] 训练路线核对字段；已有转换流程直接复用。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

下面是普通单步任务的教学裁剪。按编号进入当前局部，弄清交接后回到真实调用方；前置回查、能力对照和验证不会冒写成一条连续执行栈。

```python
# 主线：同一次 Agent 已结束，回到 SingleStepTrial._run。
[1] _upload_agent_logs -> _collect_artifacts
[2] _run_verifier(...)
  -> _run_shared_verifier(...)          # 本轮代表路径；separate 分支按需回查。
       -> _verify_with_timeout -> Verifier.verify(...)
            -> 运行题目 tests，读取 reward 文件
       <- VerifierResult
  -> self.result.verifier_result
# shared 模式随后停止 Agent 环境；_run 返回 Trial.run 的 finally。

[3] Trial._finalize == END ==> plugin._on_end
  -> 创建/取得 finalize_task，并 await shield 等待
       # 该 Task 执行 _finalize_attempt：
       -> commit_attempt -> _commit_attempt_once
            -> ProxyClient.finalize_session(...)
            -> ProxyClient.read_trajectory(..., drain=False)
            -> 校验与保存 bundle，再 drain=True
       -> finally 关闭本次路由和凭据归属

# [4] Trial 与 Job 沿正常路径返回后，才回到 _run_partition。
plugin.on_job_end(...)
plugin.get_result(...) -> _bundle_samples(...)  # 训练路线按需核对。
# 组检查、产物选用清单与返回复用已读卡，不重新深挖写文件。
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 执行产物的用途 | [已读 SingleStepTrial._run](../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) | 沿一题看需要哪些文件供验证；传输方向已知则跳过内部实现，接 _run_verifier。 |
| 2. 真实评分入口 | [_run_verifier:88](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L88) → [Verifier.verify:198](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/verifier/verifier.py#L198) | 对上 tests/test.sh、检查命令、reward.txt/json 与 VerifierResult；返回当前 Trial 的 verifier_result。 |
| 3. END 提交尝试结果 | [_on_end / _finalize_attempt:742](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L742) → [commit_attempt:256](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L256) | 只跟正常尝试的身份与数据，接 [_commit_attempt_once:307](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L307) 的 finalize/read/保存/drain；重复 END 的幂等与恢复只按需。 |
| 4. Job 返回后的最终结果 | [已读 _run_partition](../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#collect-outcomes) | 按最终 trial_id 查插件 bundle、检查并选用结果；正常低分不当运行失败，不重读整个组循环。 |
| 5. 训练数据或评测产物 | [_bundle_samples:624](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L624) · [原生 Sample 背景](../../../01-native-agent-rollout/steps/step-008-segments-to-samples/01-scope.md) | 评测先验评分、产物和身份；训练再验真实 token/logprob/mask/reward、父轨迹与版本，已有转换机制仅对照差异。 |

**本步局部验证**：用同一个试次的 ID 对齐执行日志、Verifier 奖励和 Proxy 轨迹，确认 bundle 保存后能被最终尝试选择。需要训练时再验证实际训练字段；API-only 成功不能替代 trainable bundle 合同。

**保留边界**：逐步读取、存储与删除轨迹有真实顺序；不能把“读到数据”当成“已持久化”。但原子写文件、全部异常恢复和归一化算法不列为本步默认下钻对象。

**读后接续**：正常结果交接清楚后，在 [Step 016](../step-016-cancellation-and-retries/01-scope.md)选一条异常路径回看；它是另一种执行情景，不是成功返回后的下一条业务调用。

<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0），本轮按本地 git show 定位相关符号；本地 main 与发布标签有差异，不混用。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](references/history/2026-11-12-before-call-order-scope.md)完整保留。本次只改 scope 与导航，不将未读函数提前建卡或标为掌握。

</details>
