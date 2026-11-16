# 01 · Dressage Step 015：收集产物、执行评测并交付最终结果

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一范围](../step-014-model-routing-and-api-contract/01-scope.md) · [下一范围](../step-016-cancellation-and-retries/01-scope.md)

> 状态：本步已推进到 _run_partition 的结果归组与检查。当前接续以 3.2 和项目进度为准；未运行任务、模型或集群验证。

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
                           -> _run_agent         # 执行 Agent；收尾 _sync_agent_output 取得日志、按需整理轨迹。
                           -> _upload_agent_logs  # [本步] 把本地已有日志同步回环境；轨迹来路见 3.2 reference。
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

**当前进入第 6.1 项：HarborArtifactStore.write_job_manifest。** 从 _run_partition 的组检查之后进入，重点区分“单次结果已经保存”和“整组检查后最终采用”。先看 final_keys 怎样对应到 bundle 的选用状态，再看清单与提交标记；读完返回 _run_partition 的组结果返回处。

**本步穿过两个仓库，编号表示阅读阶段，不表示同一仓库内的调用：**

| 阅读阶段 | 代码归属 | 这一段负责什么 |
| --- | --- | --- |
| 1、2 | **Harbor**：`src/harbor/` | 日志、任务产物、执行评测，形成 TrialResult |
| 3 的入口 | **Harbor → Dressage** | Harbor 发出 END 事件，调用提前登记的 Dressage 插件回调 |
| 3 的回调内部、4–6.1 | **Dressage**：`dressage/integrations/harbor/` | 从 Proxy 取得模型交互记录，结合尝试结果保存 bundle；Job 返回后选用结果，需要训练时转换 Sample |

注意：`dressage/integrations/harbor/` **属于 Dressage 仓库**，只是目录名表示它负责接入 Harbor。不能看到路径里有 harbor 就当成 Harbor 源码。

下面是普通单步任务的教学裁剪。按编号进入当前局部，弄清交接后回到真实调用方；前置回查、能力对照和验证不会冒写成一条连续执行栈。

```python
# 【Harbor】主线：同一次 Agent 已结束，回到 SingleStepTrial._run。
# 前置：_run_agent 收尾中的 _sync_agent_output 已尝试取回日志、整理轨迹。
[1] _upload_agent_logs -> _collect_artifacts
[2] _run_verifier(...)
  -> _run_shared_verifier(...)          # 本轮代表路径；separate 分支按需回查。
       -> _verify_with_timeout -> Verifier.verify(...)
            -> 运行题目 tests，读取 reward 文件
       <- VerifierResult
  -> self.result.verifier_result
# shared 模式随后停止 Agent 环境；_run 返回 Trial.run 的 finally。

[3a] 【Harbor】Trial._finalize == END ==> [3b] 【Dressage】plugin._on_end
  -> 创建/取得 finalize_task，并 await shield 等待
       # 下列均在 Dressage；该 Task 执行 [3c] _finalize_attempt：
       -> [3d] commit_attempt  # 已讨论：查找/创建/复用提交 Task，等待并返回 bundle。
            -> _commit_attempt_once  # Task 执行；随后只选读结果包构造。
                 -> ProxyClient.finalize_session(...)
                 -> ProxyClient.read_trajectory(..., drain=False)  # 读取 Proxy 记录，不是 Harbor 的 trajectory.json。
                 -> HarborTrajectoryBundle(...)  # [3e] 选读：身份 + Harbor 评分 + Proxy segments。
                 -> 判断 trainable、保存 bundle，再 drain=True
       -> finally 关闭本次路由和凭据归属

# [4] 【Harbor】Trial 与 Job 返回 JobResult，回到【Dressage】_run_partition。
plugin.on_job_end(...)  # 当前推迟最终选用：跳过清单写入，先收尾资源。
plugin.get_result(...) -> [5] _bundle_samples(...)
[6] _run_partition 继续：收集 Sample -> 检查轨迹数量与版本 -> 得到 selected_keys
  -> [6.1] artifact_store.write_job_manifest(..., final_keys=selected_keys)
       # 当前：已保存的 bundle，哪些最终采用？更新状态并记录最终清单。
  -> 按 partition 原顺序返回各组 outcome
# 只展开最终选用的业务含义；底层原子文件写入和恢复协议暂不下钻。
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 【Harbor】日志与产物 · 已读主干 | [Trial._upload_agent_logs](02-short-term-memory/functions/harbor/trial/trial.py/Trial._upload_agent_logs.md) → [SingleStepTrial._collect_artifacts](02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._collect_artifacts.md)；[轨迹来路 reference](references/claude-code-trajectory.md) | 回忆日志上传与产物收集的区别；轨迹来源按需回查。返回 SingleStepTrial._run，接评测，不重读底层传输。 |
| 2. 【Harbor】评测 · 已读主干 | [SingleStepTrial._run_verifier](02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run_verifier.md) → [Verifier.verify](02-short-term-memory/functions/harbor/verifier/verifier.py/Verifier.verify.md) | 经共享评测分支与超时包装进入 verify，接清测试脚本 → 奖励文件 → VerifierResult。结果写回后，沿 _run 返回 Trial.run 的 finally。 |
| 3a. 【Harbor】Trial._finalize · 已回查 | [Trial._finalize 函数卡](02-short-term-memory/functions/harbor/trial/trial.py/Trial._finalize.md) | 找到收尾时的 END 事件；它会调用提前登记的回调，接到 3b。 |
| 3b. 【Dressage】_on_end · 已读主干 | [DressageHarborPlugin._on_end 函数卡](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_end.md) | 看清创建或复用 finalize_task，并用 shield 等待；这个 Task 执行 3c。 |
| 3c. 【Dressage】_finalize_attempt · 已读主干 | [DressageHarborPlugin._finalize_attempt 函数卡](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._finalize_attempt.md) | 委托提交结果 → 登记 bundle → 最后关闭本次路由。在委托处进入 3d，返回后继续 record.bundle = bundle。 |
| 3d. 【Dressage】commit_attempt · 已讨论主干 | **[HarborArtifactStore.commit_attempt 函数卡](02-short-term-memory/functions/dressage/integrations/harbor/artifacts.py/HarborArtifactStore.commit_attempt.md)** | 按 Trial 身份查找提交 Task → 创建或复用 → 等待并返回 bundle。先读清这一层，再到 3e 看返回的包装了什么。 |
| 3e. 【Dressage】结果包构造 · 已讨论局部 | **[HarborArtifactStore._commit_attempt_once 函数卡](02-short-term-memory/functions/dressage/integrations/harbor/artifacts.py/HarborArtifactStore._commit_attempt_once.md)** | 只选读 _commit_attempt_once 中身份、Harbor 评分、Proxy segments 怎样组成 bundle，以及 trainable 的含义；不精读整个长函数。随后返回 3c，接清结果登记与关闭。 |
| 4. 【Dressage】Job 返回后的收尾 · 已讨论 | **[DressageHarborPlugin.on_job_end 函数卡](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin.on_job_end.md)**；[返回 _run_partition](../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md) | 当前 defer_final_selection=True：on_job_end 跳过清单写入，调用 aclose 后返回外层。外层取结果、转换并检查组，再汇总 selected_keys 写清单；本轮先读清 on_job_end 的分支与返回。 |
| 5. 【Dressage】bundle 转 Sample · 已讨论 | **[_bundle_samples 函数卡](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_bundle_samples.md)**；[当前子函数与具体示例](02-short-term-memory/functions/dressage/rollout/multi_segment.py/expand_segments_to_samples.md) | 先接清 get_result 取回已有 bundle，再看展开 segments、补来源字段和奖励、返回 Sample 列表；返回 _run_partition 的 outcome.samples.extend(converted)，组检查随后接续。 |
| 6. 【Dressage】归组与检查 · 已讨论，等待子调用返回 | [_run_partition 本步函数卡](02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md) | Sample 归组、轨迹数量与版本检查已讨论；带着成功组的 selected_keys 进入 6.1，返回后接按原顺序返回各组 outcome。 |
| <a id="current-reading"></a>**6.1. 【Dressage】write_job_manifest · 当前，已确认范围** | [HarborArtifactStore.write_job_manifest 函数卡](02-short-term-memory/functions/dressage/integrations/harbor/artifacts.py/HarborArtifactStore.write_job_manifest.md) | 看 final_keys 如何更新 bundle.superseded、未选中时的 trainable=False，以及 manifest 如何记录最终选择；辨明 committed 的用途后停止，不下钻底层文件写入。返回 _run_partition:875–878 的组结果返回处。 |

**6.1 的核心问题：保存成功，不代表最终采用。** 一次尝试的 bundle 可以已经保存，但其所属组仍可能因轨迹数量不足或版本不符合要求而失败。

```text
保存各次尝试的 bundle
    ↓
转换 Sample，检查整组
    ↓
write_job_manifest：登记最终采用的尝试，并更新未采用结果的状态
    ↓
返回各组结果（成功组或带错误的失败组）
```

这一步区分三件事：结果是否保存、数据是否满足训练要求、最终是否采用。选中不会在这里自动将 trainable 改成 True；未选中会标记 superseded，并将 trainable 设为 False。本轮函数卡已建立，阅读状态仍为待逐段核对，不标记读完。


<a id="bundle-handoff"></a>

**3e. 结果包的数据交接**

```text
Trial / session 身份 ────────────────────┐
Harbor 的评分 ──────────────────────────┼→ bundle → 返回 _finalize_attempt 登记
Proxy 的模型交互记录 ───────────────────┘
```

具体代码、字段示例和 trainable 判断见上表第二列的函数卡。本轮只选读 `_commit_attempt_once` 的这部分，保存与恢复暂不展开。

**第 1 项的配套说明**：reference 集中说明“CLI 原生日志 → 下载或挂载 → Harbor 解析转换 → trajectory.json”，包含前后数据样例和源码出处。它是上传之前的数据来路，不是新增阅读步骤，也不是 `_upload_agent_logs` 的内部实现；入口在上表第二列。

**两处 trajectory 不要接成一条文件读取链：**

```text
CLI 原生会话日志 → Harbor 转换 → agent/trajectory.json（统一的执行步骤）
模型 API 请求   → Dressage Proxy 记录 → read_trajectory → bundle（模型交互数据与尝试结果）
```

两条记录描述同一次尝试的不同侧面。第 3 项的 `ProxyClient.read_trajectory` 不表示读取第 1 项生成的 JSON 文件；也不能用 Harbor 的轨迹文件直接替代训练所需的 token/logprob 数据。

**本步局部验证**：用同一个试次的 ID 对齐执行日志、Verifier 奖励和 Proxy 轨迹，确认 bundle 保存后能被最终尝试选择。需要训练时再验证实际训练字段；API-only 成功不能替代 trainable bundle 合同。

**保留边界**：逐步读取、存储与删除轨迹有真实顺序；不能把“读到数据”当成“已持久化”。但原子写文件、全部异常恢复和归一化算法不列为本步默认下钻对象。

**读后接续**：正常结果交接清楚后，在 [Step 016](../step-016-cancellation-and-retries/01-scope.md)选一条异常路径回看；它是另一种执行情景，不是成功返回后的下一条业务调用。

<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0），本轮按本地源码定位相关符号；2026-11-16 核对本地 HEAD 与发布标签一致，旧环境的 main 差异保留在项目历史记录。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](references/history/2026-11-12-before-call-order-scope.md)完整保留。本次只改 scope 与导航，不将未读函数提前建卡或标为掌握。

</details>


### 2026-11-16：日志与产物阅读重点澄清

用户指出 Proxy 已采集 token、采样与概率资料，但 Harbor 仍有日志上传和产物收集，需要知道各自到底处理什么。此前“仅认传输职责”不足以回答这个问题，调整为先厘清来源、具体内容、传输方向与用途，再进入评分。已确认首张新增短期卡为 Trial._upload_agent_logs，并核对完整函数；_collect_artifacts 接续，尚未展开，也不将模型轨迹、CLI 事件日志与任务文件视为互斥无重叠的格式分类。
