# _run_harbor_rollout

- 源码：[dressage/integrations/harbor/rollout.py:1026–1224](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1026)。
- 首次单独展开：Step 010，2026-11-09。
- 本轮范围：2026-11-11 已接清父函数六段主线及批次返回；第 3 段涉及的工作/Job 交接已有补读，深层插件、调度和全部失败分支仍按需回查。

[来自 generate_rollout_harbor_sync](generate_rollout_harbor_sync.md#batch-entry) → **当前批次组织函数** → [_run_round](_run_round.md#round-mainline) → [_run_partition](_run_partition.md#partition-mainline)。读完本函数后返回外层的 groups, metrics。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：同步入口将配置、当前 rollout_id 和数据源交进来，要求完成本轮批量执行。当前选择 evaluation=False。
2. **具体内容**：检查配置与 Proxy 能力、准备 Gateway 运行环境；从数据源取组并解析为工作项；组织执行轮次及失败策略；按原位置收拢 Sample 组，检查可训练性和权重版本，返回组列表与统计。
3. **建议构建的心智模型**：

   > 为这一批取出任务组、安排执行，再把各组的结果按原顺序收回来。

   这里组织整批工作，具体 Harbor Job 在下游 _run_partition 中创建，不在当前取组阶段直接启动。

4. **调用代码**：

   ```python
   groups, metrics = run(
       _run_harbor_rollout(
           args,
           rollout_id,
           data_buffer,
           evaluation=evaluation,
       )
   )
   ```

## 本场景的输入与输出

**输入**：args 提供本轮配置，rollout_id 标识批次，data_source 是上层传来的 data_buffer，当前具有有效的 Harbor training 配置；本次沿 evaluation=False 读取训练组。

**输出**：正常返回 `(ordered, metrics)`。ordered 是按原始工作位置排列的 Sample 组列表，metrics 是整批统计；外层接到 groups、metrics 后再包装返回。没有工作项时可返回空组与摘要，合同不满足或失败策略要求中止时可抛错。

<a id="batch-mainline"></a>

### 本函数的局部骨架

下面的 [1]–[6] 只对应本卡内部段落，不是六个新函数或六张卡。重试与替换都发生在 [3] 的批次循环里。

```python
_run_harbor_rollout
├─ [1] 准备运行条件
│    ├─ _read_proxy_capabilities(...)
│    └─ _ensure_root_gateway_lease(...)
├─ [2] 取组并解析工作
│    ├─ data_source.get_samples(target)
│    └─ _resolve_work(data_source, source_groups)
├─ [3] 执行轮次并处理各组结果
│    ├─ pending = list(work)
│    └─ while pending
│         ├─ await _run_round(...)  # 子函数返回 outcomes 后仍回到本段。
│         ├─ 更新 completed / final_errors / next_pending
│         └─ 按策略重试或替换，再决定是否继续循环
├─ [4] 按原位置收拢结果，检查可训练组
├─ [5] 检查权重版本，登记批次状态
└─ [6] 汇总 metrics，返回 ordered, metrics
```

### 卡内阅读导航

**父函数六段主干已逐段介绍。** 第 3 段按用户要求继续折叠保留。2026-11-10 按用户确认补齐本步的 [_run_round](_run_round.md#round-mainline) 与 [_run_partition](_run_partition.md#partition-mainline) 卡片，先接清 Job 交接，再接续 Step 011 的 Trial 生命周期。

| 段落 | 源码范围 | 本段交接 | 读完接哪里 |
| --- | --- | --- | --- |
| [1. 准备运行条件](#prepare-runtime) | 1033–1048 | 配置 → Proxy 能力、期望版本、Gateway runtime | 第 2 段取组 |
| [2. 取组与工作整理](#load-source-groups) | 1050–1071 | target → source_groups → work | 第 3 段初始化 pending |
| [3. 执行与结果处理](#pending-and-outcomes) | 1073–1164 | pending → outcomes → completed / 后续工作 | 循环结束后第 4 段 |
| [4. 恢复顺序与有效性检查](#restore-order) | 1165–1178 | completed → ordered、live_groups | 第 5 段版本检查 |
| [5. 版本与批次状态](#validate-batch-version) | 1180–1198 | ordered 中的版本 → 校验、数据源状态 | 第 6 段统计 |
| [6. 指标与返回](#return-batch) | 1200–1224 | ordered → metrics；返回二元组 | 外层 groups、metrics 赋值处 |

<a id="prepare-runtime"></a>

### 1. 准备运行条件

<details>
<summary>回查第 1 段：准备条件；Gateway 内部暂缓</summary>

本段在取任务组之前，先做四件事：取得正确配置、对齐训练侧约定、核对 Proxy 能力、取得 Gateway 使用权。

> 先确认训练侧和轨迹采集侧配套，再准备后面 Agent 请求模型要经过的 Gateway。

原函数 1033–1048 的节选，省略无效配置的报错正文：

```python
# 1. 取得数据源已持有的集成配置。
config = getattr(data_source, "integration_config", None)
# 原代码要求 execution_mode == "training" 且 config.training 存在。

# 2. 检查训练侧的奖励字段与扩展钩子配置。
_validate_slime_contract(args, config)

# 3. 向 Proxy 获取能力说明，再判断是否满足本次要求。
capabilities = await _read_proxy_capabilities(config)
_validate_proxy_capabilities(args, config, capabilities)
expected_weight_version = (
    str(capabilities["current_weight_version"])
    if config.training.require_single_weight_version
    else None
)

# 4. 取得可复用的 Gateway runtime 和使用租约。
runtime, _root_lease = await _ensure_root_gateway_lease(config)
```

1. **config**：来自 data_source.integration_config。先确认这是一份用于 training 路线的配置，里面有后续要用的模型后端、路由和训练要求。
2. **训练侧约定**：_validate_slime_contract 检查 reward_key 是否一致，以及奖励后处理、Sample 转训练数据的 hook 是否接在此集成要求的位置。不是现在执行奖励计算。
3. **Proxy 能力**：_read_proxy_capabilities 用临时 ProxyClient 请求 GET /integration/capabilities，返回一个能力字典后关闭客户端；_validate_proxy_capabilities 才判断是否兼容。例如 tokenizer/模板资料、partial-rollout 模式，以及启用单版本要求时的权重版本能力。expected_weight_version 保存本批期望的版本，稍后传给执行轮次；这里不更新模型权重，也不发起生成。
4. **Gateway runtime 与根租约**：_ensure_root_gateway_lease 按配置查找或取得进程级 Gateway 使用租约，必要时启动 Gateway，让监听器能跨后续执行轮次复用。runtime 交给 _run_round；根租约保存在共享表中维持使用期，不是任务沙箱的租约。

本段做完后，已有配套的配置、能力资料、期望版本和 Gateway runtime。**此时尚未取任务组、创建 Harbor Job 或启动任务 Pod。** 下一处才是第 2 段的 get_samples。

<a id="data-source-precondition"></a>

| 按需查看真实子函数 | 具体做什么、本轮看多深 | 返回本函数的位置 |
| --- | --- | --- |
| [HarborDataSource.__init__](../data_source.py/HarborDataSource.__init__.md#data-source-precondition)（前置回查） | 看数据源怎样保存两份配置、建立带运行指纹的 spec 并提供按 ID 查询；其余初始化按需回查 | 回到 1033 行读取 integration_config，再接本段运行条件；这是进入 rollout 前的初始化，不是本函数里的调用 |
| [_read_proxy_capabilities:171](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L171) | 用 ProxyClient 获取 Proxy 实际能力字典并关闭该客户端；当前先认清返回内容，不展开 HTTP 内部 | capabilities 接住字典，再由 validate 校验；随后按配置取得 expected_weight_version |
| [_ensure_root_gateway_lease:131](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L131) | 按配置查找或取得可复用的 Gateway 租约，返回 runtime 和 lease；当前不展开 Gateway 实现 | runtime、_root_lease 接住返回值，再进入第 2 段取组 |

当前先知道这四项职责，子函数不自动成为新的必读卡。evaluation=True 也会先经过这段 training 模式的入口校验。

**本段读到这里即可：** config 是已经加载好的配置对象，此时读取并检查它，不要求现在掌握全部配置写法；capabilities 是 Proxy 返回的能力信息，后续按要求核对，不是在压缩上下文。配置细节在部署/修改相关接口时回查。

Gateway 的当前最小模型：Agent 的模型请求先进入 Gateway，再交给 Dressage Proxy，随后由 Proxy 对接模型并记录交互。Gateway 是面向 Agent 的请求入口，负责路由与尝试身份衔接；不是沙箱或模型本身。runtime 是管理这项服务的对象，_root_lease 保留使用关系，使其监听器在执行轮次之间继续可用。此处准备监听器并不自动证明未来 Pod 的网络已经可达，真实接网在后续模型路由与环境适配中验证。

本轮无需独立阅读 Gateway 内部，职责明白后返回第 2 段取组；Gateway 与 Proxy 的详细请求链在 Step 014 按已定范围展开。

</details>

<a id="load-source-groups"></a>

### 2. 取得本轮任务组，再整理成工作项

<details>
<summary>回查第 2 段：准备模板组与工作项</summary>


入口已有配置和 runtime。本段要得到待执行的 work，尚未创建 Harbor Job。

以下保留原来的评估/训练分支和数量检查；当前沿 evaluation=False 阅读。

```python
if evaluation:  # 评估时取评估组；当前训练路径走下面的 else。
    getter = getattr(data_source, "get_eval_samples", None)
    if not callable(getter):
        raise HarborRolloutError("HarborDataSource does not support evaluation")
    source_groups = getter()
else:
    target = int(getattr(args, "rollout_batch_size", 1))  # 本轮需要的训练组数。
    source_groups = data_source.get_samples(target)      # 取得待执行的 Sample 模板组。
    if len(source_groups) != target:
        raise HarborRolloutError(
            f"HarborDataSource returned {len(source_groups)} groups; expected {target}"
        )
work = _resolve_work(data_source, source_groups)  # 将模板组与任务规格整理为工作项，尚不执行。
```

1. **target**：本批要求取得的组数，不是单组内的 Sample 数量。
2. **source_groups**：一组组待执行的 Sample 模板，不是 Harbor 已经跑完的结果。
3. **work**：由 _resolve_work 组成的 _GroupWork 列表，保留模板、任务 spec、原始 position、group_index 与 instance_id 等。后面的 pending 从它初始化。

**当前阶段的边界：** target 由 args.rollout_batch_size 读取，不是数据源返回的；get_samples 返回待执行模板组；_resolve_work 校验组的归属并找到任务规格，生成 _GroupWork，不在此运行任务。实际执行仍要通过后面的 _run_round 和 _run_partition。

例如 target=2，本次期望取得两组模板，再解析为两个工作项。每组有几个模板、执行后产生几份分段 Sample，不能只由 target 推断。

**评估分支需要知道到哪一步：** evaluation=False 按 target 取训练模板组；evaluation=True 改用 get_eval_samples 取已配置的评估模板组。两路都继续交给 _resolve_work。这里的 evaluation 是 Slime 批量 hook 中的训练/评估分支，不是“是否运行 Verifier”的开关；训练 rollout 同样需要评分。独立评测还有示例的 `harbor run --plugin dressage` 入口，不能把它和这里设置 evaluation=True 视为同一个入口。

本段可以收拢为“按模式准备模板组与执行资料”，暂不深入两种取样方法。后面的执行主线仍会使用 work。

如果 work 为空，原函数在这里直接返回空组与摘要统计；非空才继续第 3 段。这个早返回保留在文末完整源码中。

| 按需查看真实子函数（本次已建卡） | 带着什么进去、具体看什么 | 读完回哪里 |
| --- | --- | --- |
| [HarborDataSource.get_samples](../data_source.py/HarborDataSource.get_samples.md#get-samples-mainline) | 从本段传入 target 组数；看它按每组尝试数生成并收集 list[list[Sample]]，区分组数与组内模板数 | source_groups 接住整批模板组，检查数量，再进入 _resolve_work |
| [HarborDataSource._sample_group](../data_source.py/HarborDataSource._sample_group.md#sample-group-mainline)（经 get_samples 进入） | 传入 spec、尝试数、组号、样本编号起点和实例 ID；看 Sample 的 prompt/metadata 怎样填写，形成一个 group | 先回 get_samples 的 group = ...，推进编号并收集组，再由 get_samples 返回本段 |
| [_resolve_work](_resolve_work.md#resolve-work-mainline) | 从本段传入 data_source 与 source_groups；看规格 ID 怎样找回 spec，原模板怎样保存在 _GroupWork.templates 中 | work 接住工作项列表，再到第 3 段 pending = list(work) |

这两处当前仍按接口职责理解，未另建子函数卡。**下一小段是第 3 段的 pending/completed 初始化，不直接跳到最终返回。**

</details>

<a id="pending-and-outcomes"></a>

### 3. 执行轮次，收集结果并处理仍未成功的组

<details>
<summary>展开第 3 段：执行轮次、结果收集与失败组处理</summary>

本段只管理**当前批次**：把 pending 交给执行函数，接回 outcomes，保存成功结果，再决定哪些工作需要继续。跨批调用与任务来源见[入口卡的层级说明](generate_rollout_harbor_sync.md#batch-owner-and-source)。

#### 初始化本批的状态

```python
# 先取得失败处理规则。
max_retries = _max_group_retries(config)
failed_group_policy = str(config.training.failed_group_policy)
max_replacements = int(config.training.max_replacement_groups)

# 原先准备好的 work 全部进入第一轮待执行列表。
pending = list(work)
completed: dict[int, list[Any]] = {}
final_errors: dict[int, BaseException] = {}

# 记录这一批执行过程中的轮次与计数。
retry_count = 0
replacement_count = 0
execution_round = 0
routing_tasks: dict[str, str] = {}
```

pending 是本轮待执行名单；completed 按原位置保存结果；final_errors 保存尚未解决的失败。pending 不是在这里逐项 pop 的队列。

#### 交出工作，等待本轮结果

下面调用位于 `while pending` 内的组重试循环中：

```python
outcomes = await _run_round(
    args=args,
    config=config,
    data_source=data_source,
    pending=pending,
    runtime=runtime,
    rollout_id=rollout_id,
    retry_round=execution_round,
    evaluation=evaluation,
    expected_weight_version=expected_weight_version,
)
execution_round += 1
exhausted = []
next_pending: list[_GroupWork] = []
```

_run_round 负责分区和调度，其内部 run_partition 协程再调用 _run_partition。当前父函数只接收它返回的 outcomes；Job 的创建与插件执行不写进本段。

| 需要展开的真实函数 | 读取目的 | 接回当前父函数 |
| --- | --- | --- |
| [_run_round 函数卡](_run_round.md#round-mainline) | 分区、容量控制、收集各分区 outcome；目前按职责理解 | outcomes 赋值之后 |
| [_run_partition 函数卡](_run_partition.md#partition-mainline) | 一个分区如何创建 Job、挂插件、调用 job.run | 先返回 _run_round 汇总，再回到本段的 outcomes |

<a id="receive-outcomes"></a>

#### 接回结果，形成下一轮名单

```python
for outcome in outcomes:
    # 原代码先合并并检查各任务的网络类别，具体字段暂折叠。
    if outcome.succeeded:  # 没有 error 且 samples 不是 None；不按 reward 高低判断。
        completed[outcome.work.position] = outcome.samples or []
        final_errors.pop(outcome.work.position, None)
    else:
        # 记录这个组的失败，再判断是否还能重试原组。
        error = outcome.error or HarborRolloutError("unknown Harbor group failure")
        final_errors[outcome.work.position] = error
        exhausted.append(outcome.work)
        if group_retry < max_retries:  # 重试次数还有余额，才加入下一轮并记录重试日志。
            next_pending.append(outcome.work)
            retry_count += 1
            # 原代码在这里记录重试日志。
pending = next_pending  # 下一轮只运行待重试的组，已成功的结果留在 completed。
if not pending:
    break  # 退出当前组重试循环。
```

这里的成功，更准确地说是**“这一组结果处理成功”，不是答对题**。直接判断是：

```python
outcome.error is None and outcome.samples is not None
```

结合前面的处理，它需要取得结果和轨迹、完成 Sample 转换并通过组内检查。

例如：

- reward = 0，但轨迹和 Sample 正常：仍可算成功。
- Agent 运行结束，但没有取得轨迹：失败。
- 有 reward，但 Sample 转换失败：仍然失败。

失败后，还有重试次数才重新运行原组，并记录重试日志；次数耗尽后，再按配置决定替换、保留失败或中止。

所以这一段可以理解为：

> 结果处理成功就保存；失败且允许重试，就安排下一轮。不是根据奖励高低决定是否重试。

<details>
<summary>一个两组例子：只重试尚未成功的组</summary>

假设本批有 A、B 两组，第一次 A 成功、B 失败，且还允许重试：保存 A，只将 B 放进 next_pending。第二次 B 成功后，completed 有两组结果，pending 为空。A/B 是工作组的教学代号，不是源码新变量；此例未运行真实 Job。

补充边界：转换时还会检查选定 reward 字段是有限数值；后面第 4、5 段仍会进行批次级可训练性与版本验收。

</details>

#### 重试耗尽后的去向

| 条件/策略 | 父函数接下来做什么 |
| --- | --- |
| 没有失败组，或不走 replace，或 evaluation=True | 退出批次执行循环，继续结果处理 |
| 训练分支 replace 且预算允许 | 再取新组，保留失败位置，加入 pending 继续执行 |
| 替换预算耗尽 | 抛错中止批次 |
| 仍有错误且策略要求 abort_batch，或评估路径配置为 replace | 抛错中止批次 |
| 其余允许保留失败的情况 | 用 _failed_group 填入对应结果位置，再进入第 4 段 |

重试继续执行原组；替换向数据源取得新组。详细条件、计数和错误文本保留在文末完整函数中。到这里才从当前批次的执行循环接到第 4 段，不重新展开整个 Slime 训练循环。

</details>

<a id="restore-order"></a>

### 4. 恢复原顺序，检查可训练结果

<details>
<summary>回查第 4 段：顺序与可训练组比例</summary>

前一段已经把各位置的结果写入 completed（允许保留的失败组也已填入相应结果）。这里不再运行任务，而是整理并检查这一批产物。

```python
# 1. 按最初的工作位置排列各组结果。
ordered = [completed[position] for position in range(len(work))]

# 2. 统计其中有多少组包含可训练数据。
live_groups = sum(
    1 for group in ordered if _group_has_trainable_tokens(group)
)
live_ratio = live_groups / len(ordered)

# 3. 检查有效组比例，以及训练时是否允许整批没有可训练数据。
if live_ratio < float(config.training.min_live_group_ratio):
    raise HarborRolloutError(
        f"Harbor live group ratio {live_ratio:.3f} is below configured minimum "
        f"{config.training.min_live_group_ratio:.3f}"
    )
if not evaluation and not _allow_empty_train_batch() and live_groups == 0:
    raise HarborRolloutError(
        "Harbor rollout produced no trainable groups; refusing an empty update"
    )
```

- **ordered**：按原始 position 的 0、1、2…排列结果，不按谁先完成来排列；组结构继续保留。
- **live_groups**：一组中至少有一份满足可训练条件的 Sample，就算一个有效组。它不是答对题目的组数，也不是 Sample 总数。
- **live_ratio**：有效组数除以总组数。低于配置的最低比例时报错，不在这一段重新发起重试。 这里是对整批验收，不会在本段删除不合格的组。

例如共两组：其中一组有可训练数据，另一组全被标为不可训练，则 live_groups=1、live_ratio=0.5。若配置要求比例为 1.0，这一批不能继续交给后续训练流程。低分或零分本身不等于没有可训练数据。

_group_has_trainable_tokens 当前按接口理解：组内任一样本没有被 remove_sample 排除、response_length 为正，且未提供 loss_mask 或 mask 中有非零位置，即满足它的判定。不单独展开辅助函数卡。

本段输出仍是分组列表 ordered，并新增 live_groups/live_ratio 供后面统计。正常通过后进入第 5 段检查权重版本；本轮先停在这里。

</details>

<a id="validate-batch-version"></a>

### 5. 检查权重版本，登记批次状态

<details>
<summary>回查第 5 段：模型版本一致性与批次状态</summary>

前一段确认有足够的可训练组。本段再检查本批数据的模型版本是否满足约定，并记录批次信息。

```python
# 1. 汇总未被排除样本中的权重版本，按配置要求检查是否只有一个。
versions = {
    version
    for group in ordered
    for sample in group
    if not getattr(sample, "remove_sample", False)
    for version in (_metadata(sample).get("harbor_weight_versions", []) or [])
}
if config.training.require_single_weight_version and len(versions) != 1:
    raise HarborRolloutError(
        f"Harbor batch observed weight versions {sorted(map(str, versions))!r}; "
        "expected exactly one"
    )

# 2. 训练分支中，向数据源记录本批版本和 Proxy 运行配置指纹。
record_state = getattr(data_source, "record_batch_state", None)
if callable(record_state) and not evaluation:
    record_state(
        weight_version=_batch_weight_version(ordered),
        runtime_incarnation=_runtime_incarnation(capabilities),
    )
```

- **versions**：集合会去重。例如相关样本都标为 v12，得到 {v12}；如果混有 v11 和 v12，得到 {v11, v12}。只有启用 require_single_weight_version 时，才要求这里恰好一个版本，零个也不通过。
- **record_batch_state**：数据源支持且不是 evaluation 分支时，保存 last_batch_weight_version 和 last_runtime_incarnation，供后续状态管理使用；这次调用本身不是保存模型 checkpoint，也不执行权重更新。
- **runtime_incarnation**：本实现根据 Proxy 的部分能力/配置字段计算指纹，例如 tokenizer 和 token 构建模式；不是操作系统进程 ID。capabilities 正是第 1 段取得的资料。

版本含义补充：这里记录的是产生样本的模型权重版本，不是 rollout_id 这个批次编号，也不是检查版本够不够新。单版本要求约束同一批；不同批次可以在训练更新后使用新的权重版本。关闭此要求只跳过这一处校验，不等于所有训练配置都自动兼容混合版本。

为什么检查版本：本训练配置要求同批可用样本采用一致的模型权重版本，避免在没有明确处理混合版本的约定下直接交给后续训练。这里只验证样本声明的版本集合，不重新计算 token，也不在此检查每个数值来自哪个真实 GPU。

当前先记住“校验本批版本，记录批次状态”即可，不必展开版本汇总与指纹辅助函数。通过后进入第 6 段统计和返回。

需要时回查 [HarborDataSource.record_batch_state:341](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L341)，正常返回仍接本函数的第 6 段。

</details>

<a id="return-batch"></a>

### 6. 汇总指标，返回样本组与统计

<details>
<summary>回查第 6 段：指标、返回与 Job 交接定位</summary>

这段只做指标整理和结果交付。ordered 保留 Sample 分组；flat 是临时展开的列表，供统计使用。


```python
flat = [sample for group in ordered for sample in group]
metrics: dict[str, Any] = compute_multi_segment_metrics(flat)
metrics.update(
    _reward_distribution_metrics(ordered, reward_key=reward_key)
)
# 原代码还补入组数、重试/替换次数、有效比例、路由类别等指标。
return ordered, metrics
```

metrics 包含轨迹分段统计、已有奖励的分布，以及组数、有效组数、失败组数、重试/替换次数、路由类别等。本段不重新执行任务，也不重新调用 Verifier 评分。

本函数的 return 回到 [generate_rollout_harbor_sync](generate_rollout_harbor_sync.md#batch-entry) 的 `groups, metrics = run(...)`。训练路径在那里包装为 RolloutFnTrainOutput；不是从当前函数直接返回单个 Sample。

读到这里，父函数的六段主干已逐段介绍；本步仍有下游 Harbor Job 创建与插件挂接待展开，不将父卡读到结尾等同于整个 Step 010 完成。指标 helper 目前按职责理解即可。

### 转到 Trial 前的最小交接定位

2026-11-10 用户询问是否停止过多下潜、转入 Step 011。当前父函数的六段主线已介绍；_run_round 与 _run_partition 内部不继续全面展开，只补最小的 Job/插件调用位置。

下列是 `_run_partition` 的调用节选（原文件 :704、:724、:760–762），不是当前父函数直接执行的连续代码：

```python
job = await _CREATE_JOB(job_config)
plugin = _PLUGIN_FACTORY(...)  # 原代码传入配置、Gateway runtime、产物存储和 Trial 绑定。
await plugin.on_job_start(job)
result = await job.run()
await plugin.on_job_end(result)
```

完整来路为本函数 → _run_round → 其内部 run_partition 协程 → _run_partition → Harbor Job。当前只确认接口关系，不视为已深入 Job 内部或插件生命周期。

2026-11-10 用户选择基于这份最小交接继续 Step 011 的 Trial.run；_run_partition 全部实现仍未逐段阅读。

</details>

## 我的直接表述（原话）

用户先确认下一入口：

> 我下一个应该看一下这里的这个run harbor rollout了对吗?

随后要求：

> 那么生成一下这里的这个函数卡片吧
> 油麻?

当前确认了阅读对象，尚无对本函数内部取组和执行流程的独立复述。

用户对讲解范围的反馈：

> 这里这么长的一个run harbor rollout怎么金额就这么简短的就结束了呢?
> 我不是特别理解

本轮据此补齐整批状态、失败去向、结果验收与返回的全貌，并明确卡片生成不等于函数已读完。当前仍逐小段推进，不把一页骨架作为已经理解所有实现的证明。

本轮确认记录方式：

> 好的 那么就按照这个方式重新设计和产出这里的这个run harbor rollout吧

本轮按一函数一文件重排展示；六段是卡内导航，不是新增函数或已完成阅读。原话与未知继续保留。

本轮用户对准备与取组的理解：

> 好的 那么一开始的准备条件就是read proxy capabilities
> 虽然我其实不是特别清楚这里到底做了什么
> 我可以简单理解为这里尝试使用这里的harbor data source来获取到taget和sample
> 然后让这里的resolve work的部分是通过让source groups 来完成和理解之后去实际运行这里的这个人物?
>
> 或者我还是需要看一下这里的这个两个子函数具体是什么?

助手核对：能力查询是前置准备的一部分，校验由后续 validate 完成；target 来自 args，模板组来自数据源。_resolve_work 只准备工作项，不启动任务。当前建议先独立阅读 HarborDataSource.get_samples，再读 _resolve_work，明确“取输入、补任务规格、执行”三个边界；这仍是推荐，未提前创建两个子函数卡。

2026-11-10 回查：

> 我们上次看到的是这个run harbor rollout对吗?
> 我可以简单这么理解
> 但是我记得 我们说了这里的run harbor rollout太长了需要分开单独理解
> 我记得是
> 先看一下这里的准备条件吧
> 这里的准备条件在做什么

本轮回到卡内第 1 段，按职责解释准备的资料和资源，没有扩展新的 helper 卡或把后续阶段标记为已读。

本轮对准备条件的表述：

> 我可以简单理解为首先了解一下这里第二集成配置
> 这方面都是需要考虑这里的配置到底应该怎么写
>
> 第二部是查看这里的config
> 是否符合slime的contract
> 同时看一下proxy本身的能力
> 通过压缩的方式来判断这里是否是能力足够
> 这里的gateway我是没有太看懂
>
> 综合来看一下 你觉得我目前需要看这些吗?
> 还是简单知道这里有什么?

助手校准：当前先认清已有配置、训练约定校验、Proxy 能力查询/核对和 Gateway 请求入口四项职责；不在本段学习全部配置写法或追入 Gateway 内部。能力核对不涉及上下文压缩。按用户此前的主线优先要求，补清 Gateway 角色后即可接取组，不追加新的必读卡。

2026-11-10 本轮选择：

> gateway感觉还是比较复杂?
> 那么我们现在看第二个部分吧

按用户选择继续取组，不再将 Gateway 内部作为本段阅读前置；Gateway 的运行机制仍保留未知。

2026-11-10 本轮概括与评估疑问：

> 价单来说这里是把data source哪里获取到对应的sample模板还有对应的组数?
> 是我简单的理解
> 但是我们当前需要做的不是评估的方案也需要看吗?
> 这样子是不是就需要看也关注这里的 evaluation部分呢?
>
> 不过对于这里的理解我认为是否就可以停留在这里的是准备模板
> 就可以考虑继续了呢?

助手校准：模板来自数据源；训练分支的请求组数由 args 决定。准备模板与执行资料的职责理解足够继续；evaluation 的两路来源与外层返回需要知道，但本轮不因此展开完整评估取样。独立评测入口、训练中的评估分支和 Verifier 评分分别理解。

2026-11-10 本轮接续：

> 好的 那么看一下下面的第三个部分吧
> 看一下这里的执行轮次和手机解雇耦合处理未成功组的部分吧

本轮从父函数角度讲解 pending、outcomes、completed 和失败工作去向；_run_round 内部未展开，也不把局部示意算作真实运行证据。

2026-11-10 对 pending 的疑问：

> 简单来说就是往pengding里面家内容
> 然后每次从pengding里面取走要运行的group?
> 我没有特别理解

助手校准：pending 是当前一轮的完整工作名单；本函数未逐个 pop，而是整份传给 _run_round，结果回来后构建 next_pending，再用它替换 pending。只有仍允许重试的失败组进入下一次重试名单，成功组的结果另存 completed。

2026-11-10 关于多批次的追问：

> 我的意思是这里不能只有一个批次的rollout吧
> 应该有比较多批次的rollout?
> 这里是怎么组织的呢?

本轮核对同步训练外层循环，区分 rollout_id 对应的批次与本函数 execution_round/group_retry 对应的批内轮次；不把本函数内的 while pending 当成整个训练循环。

2026-11-10 关于数据来源的追问：

> 但是这里的数据难道不是从harbor这里来看的吗?
> 我其实没有特别理解

助手校准：任务来自 Harbor JobConfig 指定的任务集/本地任务，Dressage HarborDataSource 对接其任务规格；Slime 只组织外层多批调用并消费结果，不因此成为题目来源。

2026-11-10 对第 3 段的职责概括：

> 好的 简单来说就是上一次 拿到工作
> 这里是直接运行具体的批次
> 我是这么理解的处理
> 哪些到底得到了对应的结果还是没有得到对应的结果
> 是否需要重跑等一系列内容都是在这个3这里完成的是我的理解

助手核对：第 2 段准备 work，第 3 段组织本批工作执行、接回各组结果、保存完成结果，并按策略决定重试/替换/失败去向。具体 Harbor Job 执行委派给 _run_round 及下层；“执行成功”不等同于任务得高分，整批可训练性与版本检查还在后面的第 4、5 段。用户已表达该段主线职责，不据此认定所有失败策略细节均已掌握。

2026-11-10 接续第 4 段：

> 好的 那么我们来看一下下一个部分的内容吧

在前一轮已确认第 3 段职责后，本轮继续父函数第 4 段，解释结果顺序和可训练组检查。具体 Harbor Job 执行内部仍未下钻。

2026-11-10 对第 4 段的理解与第 5 段接续：

> 价单来说这里的就是检查一下顺序是否?
> 然后看一下里面到底有多少可训练的数据
> 以及邮箱比例
> 训练的时候是否允许这样子
> 如果可以的话就继续
> 对吗?
>
> 那么我们是否需要看一下 下面的这个5呢?

助手校准：先按原位置组织顺序，再统计含可训练数据的组数与比例，而不是 token 总量；通过后继续。本轮进入第 5 段，介绍版本校验和数据源状态登记，不据此推断辅助实现已掌握。

2026-11-10 对版本的理解与继续请求：

> 我可以简单理解为这里的batch 版本吗?
> 只要版本是足够的
> 如果配置允许多个版本那么多个版本没有问题
> 如果需要的是固定或者单一的版本那么就不可以
> 我是这么理解的
> 那么继续吧
> 还有什么需要看的内容呢?

助手校准：这是同批样本的模型权重版本，不检查版本新旧；开启单版本约束时版本集合恰有一个值才通过。关闭该约束只是不在这里拒绝，不能扩大为整个训练系统必然接受任意混合版本。随后接第 6 段统计与返回。

2026-11-10 对第 6 段的理解：

> 最后是统计一下每一份sample这里 对应的需要计算的指标是我的理解

助手校准：用已生成的样本及本批执行状态作为原料统计，方向正确；metrics 主要是轨迹/组/批次层面的汇总，如分段统计、奖励分布、有效组数、失败组数与重试次数，不是逐份给 Sample 附加一套指标。最后分别返回 ordered（样本组）和 metrics（统计字典）。

2026-11-11，返回父函数后对第 4 段的复述：

> 好的那么我们继续吧下面看的内容是什么
> 是这里的第四段对吗?
> 我是否可以理解为
> 更多的是
> 把这里的顺序宠幸回复一下
> 然后看一下到底哪些是适合训练的?
>
> 简单来说就是调整位置
> 和检查是否可以供于训练是我的理解
> 那么现在考虑一下吧
> 还有什么需要做的呢?

助手确认主线：按原工作位置恢复组顺序，统计含可训练数据的组及比例，并验证本批是否满足要求。这里没有删除不合格组来重新组成列表，不按 reward 高低判断；比例不足或不允许空训练批次时会报错。下一段是权重版本与批次状态，随后统计和返回。


2026-11-11，用户概括最后两段并判断本函数已接近读完：

> 第五段落是查看权重的版本
> 登记批次状态
> 然后这里的这个6的内容就是汇总一下这里的指标
>
> 那么这个函数还有什么需要看的吗?
> 我觉得好像也没有什么特别需要注意的了?

助手确认本轮主线可在此收束：最终返回按组保留的 ordered 与 metrics，外层训练入口接成 groups/metrics 并包装为 RolloutFnTrainOutput。各指标实现、全部失败分支及插件/调度内部仍是按需回查，不视为已经掌握；不再为本轮追加辅助函数。


## 尚不清楚

- Gateway 内部仍不清楚，按用户选择暂缓；当前只保留请求入口这一职责。
- 数据源各组模板如何生成、任务规格如何解析，当前先按接口理解。
- pending 到 Harbor Job 的交接，本次在 _run_round / _run_partition 卡片补读；尚不据材料建立认定已掌握其内部机制。
- 整组重试与替换策略、可训练性和权重校验，只定位用途。

<details>
<summary>完整函数与验证来源</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。静态核对，无 Harbor Job、Proxy、模型或训练运行。

```python
async def _run_harbor_rollout(
    args: Any,
    rollout_id: int,
    data_source: Any,
    *,
    evaluation: bool,
) -> tuple[list[list[Any]], dict[str, Any]]:
    config = getattr(data_source, "integration_config", None)
    if config is None or getattr(config, "execution_mode", None) != "training":
        raise HarborRolloutError(
            "generate_rollout_harbor_sync requires HarborDataSource in training mode"
        )
    if config.training is None:
        raise HarborRolloutError("Harbor training configuration is missing")
    _validate_slime_contract(args, config)
    capabilities = await _read_proxy_capabilities(config)
    _validate_proxy_capabilities(args, config, capabilities)
    expected_weight_version = (
        str(capabilities["current_weight_version"])
        if config.training.require_single_weight_version
        else None
    )
    runtime, _root_lease = await _ensure_root_gateway_lease(config)

    if evaluation:
        getter = getattr(data_source, "get_eval_samples", None)
        if not callable(getter):
            raise HarborRolloutError("HarborDataSource does not support evaluation")
        source_groups = getter()
    else:
        target = int(getattr(args, "rollout_batch_size", 1))
        source_groups = data_source.get_samples(target)
        if len(source_groups) != target:
            raise HarborRolloutError(
                f"HarborDataSource returned {len(source_groups)} groups; expected {target}"
            )
    work = _resolve_work(data_source, source_groups)
    if not work:
        return [], {
            "harbor/groups": 0.0,
            "harbor/routing_enforced": float(
                config.security.routing_guarantee == "enforced"
            ),
            "harbor/public_network_tasks": 0.0,
            "harbor/restricted_network_tasks": 0.0,
        }

    max_retries = _max_group_retries(config)
    failed_group_policy = str(config.training.failed_group_policy)
    max_replacements = int(config.training.max_replacement_groups)
    pending = list(work)
    completed: dict[int, list[Any]] = {}
    final_errors: dict[int, BaseException] = {}
    retry_count = 0
    replacement_count = 0
    execution_round = 0
    routing_tasks: dict[str, str] = {}
    while pending:
        exhausted: list[_GroupWork] = []
        for group_retry in range(max_retries + 1):
            outcomes = await _run_round(
                args=args,
                config=config,
                data_source=data_source,
                pending=pending,
                runtime=runtime,
                rollout_id=rollout_id,
                retry_round=execution_round,
                evaluation=evaluation,
                expected_weight_version=expected_weight_version,
            )
            execution_round += 1
            exhausted = []
            next_pending: list[_GroupWork] = []
            for outcome in outcomes:
                for digest, network_class in outcome.routing_tasks.items():
                    existing = routing_tasks.setdefault(
                        digest,
                        network_class,
                    )
                    if existing != network_class:
                        raise HarborRolloutError(
                            "resolved Harbor task changed network class within one batch"
                        )
                if outcome.succeeded:
                    completed[outcome.work.position] = outcome.samples or []
                    final_errors.pop(outcome.work.position, None)
                else:
                    error = outcome.error or HarborRolloutError(
                        "unknown Harbor group failure"
                    )
                    final_errors[outcome.work.position] = error
                    exhausted.append(outcome.work)
                    if group_retry < max_retries:
                        next_pending.append(outcome.work)
                        retry_count += 1
                        logger.warning(
                            "retrying complete Harbor group %s (%d/%d): %s",
                            outcome.work.group_index,
                            group_retry + 1,
                            max_retries,
                            error,
                        )
            pending = next_pending
            if not pending:
                break

        if not exhausted or failed_group_policy != "replace" or evaluation:
            break
        if replacement_count + len(exhausted) > max_replacements:
            first = min(item.position for item in exhausted)
            raise HarborRolloutError(
                f"Harbor replacement budget exhausted ({max_replacements} groups)"
            ) from final_errors[first]

        replacement_groups = data_source.get_samples(len(exhausted))
        replacement_work = _resolve_work(data_source, replacement_groups)
        pending = []
        for failed, replacement_item in zip(exhausted, replacement_work):
            item = replace(replacement_item, position=failed.position)
            work[failed.position] = item
            final_errors.pop(failed.position, None)
            pending.append(item)
        replacement_count += len(pending)

    if final_errors and (
        failed_group_policy == "abort_batch"
        or (evaluation and failed_group_policy == "replace")
    ):
        first = min(final_errors)
        raise HarborRolloutError(
            f"Harbor group {work[first].group_index} exhausted retries"
        ) from final_errors[first]

    reward_key = str(config.training.reward_key)
    for position, error in final_errors.items():
        completed[position] = _failed_group(
            work[position], error, reward_key=reward_key
        )
    ordered = [completed[position] for position in range(len(work))]
    live_groups = sum(
        1 for group in ordered if _group_has_trainable_tokens(group)
    )
    live_ratio = live_groups / len(ordered)
    if live_ratio < float(config.training.min_live_group_ratio):
        raise HarborRolloutError(
            f"Harbor live group ratio {live_ratio:.3f} is below configured minimum "
            f"{config.training.min_live_group_ratio:.3f}"
        )
    if not evaluation and not _allow_empty_train_batch() and live_groups == 0:
        raise HarborRolloutError(
            "Harbor rollout produced no trainable groups; refusing an empty update"
        )

    versions = {
        version
        for group in ordered
        for sample in group
        if not getattr(sample, "remove_sample", False)
        for version in (_metadata(sample).get("harbor_weight_versions", []) or [])
    }
    if config.training.require_single_weight_version and len(versions) != 1:
        raise HarborRolloutError(
            f"Harbor batch observed weight versions {sorted(map(str, versions))!r}; "
            "expected exactly one"
        )

    record_state = getattr(data_source, "record_batch_state", None)
    if callable(record_state) and not evaluation:
        record_state(
            weight_version=_batch_weight_version(ordered),
            runtime_incarnation=_runtime_incarnation(capabilities),
        )

    flat = [sample for group in ordered for sample in group]
    metrics: dict[str, Any] = compute_multi_segment_metrics(flat)
    metrics.update(
        _reward_distribution_metrics(ordered, reward_key=reward_key)
    )
    metrics.update(
        {
            "harbor/groups": float(len(ordered)),
            "harbor/live_groups": float(live_groups),
            "harbor/failed_groups": float(len(final_errors)),
            "harbor/group_retries": float(retry_count),
            "harbor/replacement_groups": float(replacement_count),
            "harbor/live_group_ratio": live_ratio,
            "harbor/routing_enforced": float(
                config.security.routing_guarantee == "enforced"
            ),
            "harbor/public_network_tasks": float(
                sum(value == "public" for value in routing_tasks.values())
            ),
            "harbor/restricted_network_tasks": float(
                sum(value == "restricted" for value in routing_tasks.values())
            ),
        }
    )
    return ordered, metrics

```

辅助依据：_resolve_work:361；_run_round:903；外层入口:1257。get_samples 具体实现本轮未展开。

形成过程：[Step 010](../../../../../../../step-010-harbor-rollout-entry/04-flow.md#harbor-rollout-card)。

</details>
