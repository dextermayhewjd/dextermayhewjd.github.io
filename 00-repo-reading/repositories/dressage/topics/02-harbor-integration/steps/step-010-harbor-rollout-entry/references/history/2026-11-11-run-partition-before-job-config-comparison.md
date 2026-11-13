> 历史快照：2026-11-11，重写“1. 创建 Job”的三个对象对照前保存。

# _run_partition

- 源码：[dressage/integrations/harbor/rollout.py:675–900](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L675)。
- 首次单独展开：2026-11-10，初建于 Step 011；同日按用户确认归回 Step 010。此前仅定位 Job/插件关键调用。
- 最近认识更新：2026-11-10，用户进一步串起 pending 分区、工作内容、运行配置与 Job 执行对象；插件准备的作用仍待继续确认。

[_run_round](../../02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) → 内部 `run_partition` → **_run_partition** → Harbor Job · [本步导航](../../01-scope.md#reading-navigation)

**进入这里时**：上游已经确定当前 `partition`，并取得路由额度；现在把这份工作交给本函数，要求它执行并返回各组结果。上游调度细节回看 [_run_round](../../02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：需要为当前分区中的工作创建并运行 Harbor Job，再将结果归回原工作组。
2. **具体内容**：为分区创建临时 Harbor Job，建立 Trial 与模板的对应关系并挂接 Dressage 插件；运行 Job 后取出最终结果与轨迹 bundle，转换 Sample，按原组返回。
3. **建议构建的心智模型**：

   > 用一个 Harbor Job 跑完这一份工作，再把执行结果和轨迹整理回各自的工作组。

4. **调用代码**（内部 `run_partition`，950 行；其他参数省略）：

   ```python
   return await _run_partition(..., partition=partition)
   ```

## 本场景的输入与输出

| 交接 | 当前函数关心的内容 |
| --- | --- |
| 输入 | `partition`：这次需要执行的工作组；以及已有的 Job 配置和运行条件。 |
| 最终输出 | `list[_GroupOutcome]`：按本区原顺序，每个工作组对应一份结果，包含 Sample 或失败信息。 |

**用已有配置把这份工作组织成 Harbor Job，运行后将结果整理回各个工作组。** `job` 是第 1 段产生的执行对象，`result` 是 Job 运行后的中间结果；它们都不是本函数最终返回的组结果列表。

<details>
<summary>按需核对：完整参数、结果字段与副作用</summary>

- `partition` 是运行指纹相同的 `_GroupWork` 列表，可能包含多个组。
- `args`、`config`、`data_source`、`runtime` 提供配置、数据源和 Gateway 运行条件；`rollout_id`、`retry_round` 标识当前批次与执行轮次；`expected_weight_version` 传递期望权重版本。
- `evaluation` 决定使用训练还是评估 Job 配置；当前沿 `evaluation=False`，使用 `data_source.job_config`。
- 每个 `_GroupOutcome` 保存 `work`、`samples/error`、`versions`、`bundles`、`final_keys`、`routing_tasks`。失败或取消的处理边界见第 4 段。
- 本函数还会运行 Job、写入产物 manifest，并关闭插件。它不直接调用原生 Paddock 创建沙箱；Environment 的选择在 Job 配置中。
- `_temporary_job_config` 用与路由需求相同的计算设置 `n_concurrent_trials`；此处只需知道它是 Job 的并发配置，额度取得与归还回看上游卡片。

</details>

<a id="partition-mainline"></a>

### 本函数内部：每段产生什么，交给下一段什么

下面是数据交接示意，不是可执行代码。[1]–[4] 对应下方段落。**当前读 [2] 准备插件**；[1] 已有主线复述，[3]–[4] 保留后续入口。

```python
_run_partition
  # [1] 创建执行对象；job 是本段产物。
  source_job_config + partition → job_config → job

  # [2] 建立结果归属关系，并准备插件。
  job + partition → templates、bindings
  bindings + runtime + artifact_store → plugin

  # [3] 接入插件、运行 Job，取得中间结果。
  await plugin.on_job_start(job)
  result = await job.run()
  await plugin.on_job_end(result)

  # [4] 将执行结果和轨迹整理回原工作组。
  result + 插件保存的轨迹 → 各组 outcome
  # 写入 manifest；交回组结果前，finally 中关闭插件。
```

| 阶段 | 源码位置 | 本段产物及去向 |
| --- | --- | --- |
| [1. 创建 Job](#create-job) | 687–704 | `job` → 下一段绑定 Trial 与模板 |
| [2. 准备插件 · 当前](#prepare-plugin) | 705–730 | `templates`、`bindings`、`plugin` → 执行与结果归组 |
| [3. 运行 Job](#run-job) | 759–762 | `result`（JobResult）→ 下一段查最终 Trial 结果 |
| [4. 整理结果与收尾](#collect-outcomes) | 764–900 | 各组 `_GroupOutcome` → 本函数最终返回 |

<a id="create-job"></a>

### 1. 创建 Job

**这份配置从哪里来？** `data_source.job_config` 已在 [HarborDataSource.__init__ 的配置加载处](../../02-short-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.__init__.md#data-source-precondition) 通过 `_load_job_config(...)` 加载并保存。这里先取出它作为 `source_job_config`，再结合当前 `partition` 生成本次运行使用的 `job_config`。

源码 687–704 行，保留本段连续代码，只补阶段注释。当前沿 `evaluation=False` 的训练分支阅读。

```python
# 1. 取出原始配置：已包含任务、Agent、环境等执行安排。
source_job_config = (
    getattr(data_source, "eval_job_config", None)
    if evaluation
    else getattr(data_source, "job_config", None)
)
if source_job_config is None:
    raise HarborRolloutError("Harbor data source has no job configuration")
# 2. 生成当前分区的临时配置：选用本区任务和对应 Agent，设置尝试数、并发等。
run_id = str(getattr(data_source, "run_id", "harbor"))
job_config = _temporary_job_config(
    source_job_config=source_job_config,
    partition=partition,
    config=config,
    run_id=run_id,
    rollout_id=rollout_id,
    retry_round=retry_round,
)
_validate_temporary_job_task_sources(job_config)
# 3. 根据临时配置创建 Job 对象；后面调用 job.run() 才执行任务。
job = await _CREATE_JOB(job_config)
```

- `source_job_config` 是原始的整体执行配置，已有任务、Agent、环境等信息，不只是题目描述；当前取 `data_source.job_config`，评估分支取 `eval_job_config`。
- `job_config` 是以原始配置为基础、按当前 `partition` 调整出的本次执行配置。它同样包含任务和 Agent 等安排；这里的“本次/局部”指配置用途，不表示 Agent 必须运行在本机。
- `job` 是 `_CREATE_JOB` 创建的具体 Harbor 执行对象，可以通过后面的 `job.run()` 组织多个 Trial。默认创建路径是 `_default_create_job` → `Job.create(job_config)`。

<a id="job-config-changes"></a>

**`_temporary_job_config` 到底改了什么？** 每次为当前 `partition` 生成一份新的 Job 配置。原来的 `source_job_config` 保留；下面这些字段被覆盖，未覆盖的字段从原配置复制保留。

| 主要字段 | 本次临时配置具体采用什么 |
| --- | --- |
| `tasks` | 当前 partition 中每项 `spec.task_config` 的副本；每个任务的 `source` 设为 None |
| `agents` | 只放当前分区共用的一份 Agent 配置，取自第一项的 `spec.agent_config`；其 `n_concurrent` 设为 None |
| `n_attempts` | 第一项工作中的模板数量 `len(partition[0].templates)`；原代码要求本分区各组的模板数量相同 |
| `n_concurrent_trials` | 当前分区的 Trial 总数与 `max_active_routes` 两者中的较小值，即前面讨论的路由需求额度 |

例如当前 partition 只有 A、C 两项工作，各有两份模板，那么临时 Job 的 tasks 只包含 A、C，`n_attempts=2`；若路由上限至少为 4，`n_concurrent_trials=4`。这是静态示例，原配置本来的具体数值取决于输入。

<details>
<summary>其余覆盖项：命名、目录、数据集与环境</summary>

| 字段 | 修改内容 |
| --- | --- |
| `job_name` | 根据 run_id、rollout_id、retry_round、公开 Agent 标识和随机后缀生成本次名称 |
| `jobs_dir` | 设为配置的产物根目录下的 `harbor-jobs` |
| `datasets` | 设为空列表；本次工作已作为上面的显式 tasks 提供 |
| `quiet` | 设为 True |
| `environment` | 仅在 `config.environment.mode == "bwrap"` 时覆盖：以原环境配置为基础，将 type 设为 None、import_path 设为 DressageEnvironment；其他模式沿用原配置 |

这些更新在 [_temporary_job_config:505–578](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L505) 中汇集，再由 `_validated_model_update` 复制/校验为新对象，不原地改写源配置。这里的 `agents[0].n_concurrent` 与 Job 的 `n_concurrent_trials` 是不同字段，不能混为一个限制。

</details>

**本段产物是 `job`，还不是整个函数的返回结果。** 下一段用它绑定 Trial 与原始模板，并准备插件；后面才调用 `job.run()`。接下来进入第 2 段。

<a id="prepare-plugin"></a>

### 2. 准备插件 · 当前

**进入本段时已有 `job` 和 `partition`。现在需要解决：将来每个 Trial 的结果属于哪个原始模板，以及由谁配合 Harbor 保存这些结果。**

<a id="assign-trials-call"></a>

源码 705–730 行的节选，保留 Trial 绑定与插件参数，省略产物存储的详细配置；完整原函数在文末。

当前先进入 [_assign_partition_trials 函数卡](../../02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_assign_partition_trials.md#assign-mainline)。读完回到下面的 `templates, bindings = ...`，接清两个返回值，再继续 `reward_key` 与 `HarborArtifactStore(...)`。

```python
# 1. 给 Job 中的 Trial 建立模板对应表与任务身份绑定。
templates, bindings = _assign_partition_trials(
    job,
    partition,
    rollout_id=rollout_id,
    retry_round=retry_round,
    expected_weight_version=expected_weight_version,
)

# 2. 准备产物存储对象，供插件后续保存轨迹等结果。
reward_key = str(config.training.reward_key)
artifact_store = HarborArtifactStore(...)

# 3. 将身份绑定、Gateway runtime 和产物存储交给插件。
plugin = _PLUGIN_FACTORY(
    config=config,
    gateway_runtime=runtime,
    artifact_store=artifact_store,
    trial_bindings=bindings,
    defer_final_selection=True,
)
```

| 本段得到的对象 | 记住它的用途 |
| --- | --- |
| `templates` | 按 `trial_name` 找到原来的 Sample 模板，留给本函数第 4 段转换结果。 |
| `bindings` | 按 `trial_name` 记录 `instance_id`、`attempt_ordinal` 和期望权重版本，交给插件识别任务与尝试。 |
| `artifact_store` | 后续保存轨迹与产物记录的存储对象。 |
| `plugin` | 默认是 `DressageHarborPlugin`，让 Dressage 的模型路由与结果采集配合 Harbor 的执行生命周期。 |

可以把前两个对象理解为“查模板的表”和“查任务身份的表”：它们使用同一个 `trial_name` 关联，服务于后面的不同处理。`bindings` 当前没有 session_id 字段，不把这里误记成已完成会话登记。

**本段只是准备这些对象。** 当前还没有调用 `plugin.on_job_start(job)` 挂接生命周期回调，也没有调用 `job.run()`。下一段才把已经准备的插件接到 Job 上并开始运行；本段不进入插件内部或 Trial 执行。

<details>
<summary>按需核对：绑定来源与最终结果选择</summary>

`_assign_partition_trials`（rollout.py:581 起）取得 Job 的 Trial 计划，按 task_index 找到原工作组、按 attempt_index 找到组内模板，并将两份对应关系存到 templates 和 bindings。`TrialBinding`（plugin.py:95 起）包含任务实例、尝试序号和期望权重版本。

`defer_final_selection=True` 让最终采用哪些结果留到本函数整理成功组时决定；具体产物选择逻辑在第 4 段按需回查。当前已单独建立 _assign_partition_trials 卡片；其余辅助实现仍按需回查。

</details>

<a id="run-job"></a>

<details>
<summary>3. 运行 Job（后续阅读）</summary>

```python
await plugin.on_job_start(job)     # 在运行前接入插件配置与生命周期回调。
result = await job.run()           # Harbor 调度多个 Trial，等待 Job 结果。
await plugin.on_job_end(result)    # Job 返回后，完成插件的 Job 级收尾。
```

运行期间，各 Trial 到相应阶段才触发插件回调。这里的 `result` 是 `JobResult`，包含最终 Trial 结果；轨迹 bundle 由后面通过插件取回。

一个静态例子：本区有两组，每组两份模板，就会安排四个逻辑 Trial；Harbor 还可能按其配置重试。一个 Job 不等于一道题，一个 Trial 也不等于一次模型调用。

| 后续观察点 | 进入方式 | 返回本函数的位置 |
| --- | --- | --- |
| [Trial.run 已有卡片](../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle) | `job.run()` 经 Harbor 调度器进入，非当前函数直接调用 | 等 Job 汇总完成后，回到 `plugin.on_job_end(result)` 与第 4 段 |

</details>

<a id="collect-outcomes"></a>

<details>
<summary>4. 整理结果与收尾：先看交接，需要时展开</summary>

原函数先建立三份索引：`by_trial` 找到最终 Trial 结果，`outcomes_by_position` 保存每个工作组的 outcome，`trial_to_work` 将 Trial 归回原工作组。

循环内的正常路径节选如下；省略索引建立、缺失检查和异常处理，完整实现见文末：

```python
for trial_name, template in templates.items():
    work = trial_to_work[trial_name]
    outcome = outcomes_by_position[work.position]
    final_result = by_trial.get(trial_name)
    # 根据最终尝试身份取已提交的轨迹。
    bundle = plugin.get_result(trial_name, str(final_result.id))
    outcome.bundles.append(bundle)
    outcome.final_keys.append((bundle.trial_name, bundle.trial_id))
    converted = _bundle_samples(
        template=template, bundle=bundle, args=args, reward_key=reward_key,
    )
    outcome.samples.extend(converted)
    outcome.versions = tuple(
        dict.fromkeys((*outcome.versions, *bundle.observed_weight_versions))
    )
```

之后检查组内轨迹数量与可选的单权重版本要求，选择成功组的 final_keys，写入 `completed` 或 `partial` manifest。再附上路由摘要，按原分区顺序返回各组 outcome。

这里 `outcome.succeeded` 仅检查没有 error 且 samples 不为 None，不表示答案正确或评测满分。缺少最终结果、缺少 bundle、转换失败或组检查失败，会把对应组标为失败；父函数再决定是否重试。

`try` 内的普通异常还会走产物中止处理并返回失败 outcome；取消则在中止处理后继续抛出。`finally` 关闭插件。Job/插件创建在该 try 之前，早期异常由上游调度包装处理，不能说本 finally 覆盖所有初始化失败。

本段读到按原工作组产生结果列表即可，Sample 转换与产物提交的内部实现留作按需回查。

</details>

**读完本函数，接回上游**：组结果列表交回 [_run_round](../../02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) 汇总；额度归还由它的内部包装负责，本卡不重复展开。

## 我的直接表述（原话）

> 好的
> 那么就看一下这里的这个run round 和这里的run partition吧

以上是本轮范围确认。随后用户对第 1 段的理解：

> 简单来说
> 先考虑这里的和job config相关的内容
> 找到对应的所有的config
> 然后把这个config
> 深成为一个job
> 产生了一个job
> 然后在交给下面的插件部分

助手校准：当前按 evaluation 选择数据源已有的训练或评估 Job 配置，再结合 partition 生成本次临时 job_config，并由 _CREATE_JOB 创建 job；并非搜集所有配置。接下来先用 job 和 partition 建立 Trial 与模板的对应关系，再准备插件，后续才调用 on_job_start(job) 和 job.run()。用户已表达第 1 段主线，不据此认定插件或 Job 执行内部已读懂。

随后用户指出仍不清楚这些对象的含义：

> 我这里其实不是特别清楚了
> 这里的job我的理解是从字面来看是一个特定的问题或者数据
> 然后这里的partition是什么呢? 我不是特别理解
> 以及这里的后难免的这个2部分的1,2,3是在做什么
> 我其实没有在抽象的过程当中理解这一点

助手补充区分工作数据与执行对象，并用同一例子解释三项准备；不将此前对“配置 → Job”的复述等同于已理解 Job/partition 的抽象。

补充解释后，用户重新表述三者的关系：

> 好的 也就是partition
> 是具体的work
> 从pending那本分割下来的
> 然后通过配置上了job config
> 然后变成一个job
> 也就是工作是什么
> 和打算怎么运行的
> 最后变成一个需要执行的job是我对于这三者的理解?
> 我说对了吗?

助手核对：主线正确。partition 是从 pending 按运行指纹归成的一组工作，不一定只有一个 work；已有配置与 partition 共同生成本次 job_config，再创建 job 对象。此时还未调用 job.run()。不是原列表原地变成了 Job，而是利用这些数据创建执行对象。


用户进一步追问第 2 段的必要性：

> 好的 那么我们在有了这个job和partition的情况下
> 为什么还需要这里的这个assign parttition trial呢?
> 并且产出这里的2部分的1,2,3 我其实没有特别理解

助手说明：Job 的运行计划与 partition 保留的原始模板需要建立明确对应；assign 函数命名 Trial 并产出映射，artifact_store 准备结果存储，plugin 使用身份、路由运行时和存储对象参与后续生命周期。解释效果尚待用户反馈。

2026-11-11，用户再次核对三者的含义：

> 也就是source job config
> 是这个问题具体是什么样子的config
> 然后这里的job config是本地的这个agent 使用的是什么样子的agent以及生么人物?
> 最后生成的job 是一个具体的对象?
>
> 我觉得是否需要考虑一下 这里的内容需要在这个md文件旁边写一下这个备注上面写清楚?

助手校准：原始 source_job_config 已包含任务、Agent、环境等整体执行安排；job_config 是依据当前分区调整后的同类执行配置，不以“题目配置/Agent 配置”划分。“本地变量”也不意味着本机执行。job 才是根据该配置创建、可调用 run() 的执行对象。已将这些区别写在第 1 段原有注释和说明中。


## 尚不清楚

- job 与 partition 的早先混淆已通过示例及用户后续复述澄清；第 2 段三项准备的作用尚未获得用户进一步复述，继续保留为当前问题。
- 本轮先对齐 Job 创建、插件接入、执行和结果归组；辅助函数参数、转换与失败修复机制尚未逐段阅读。
- Harbor Job 经哪个调度器运行 Trial，此处只保留跨层入口；Trial.run 的既有卡片继续保留。
- Kubernetes 环境替换位置仍在后续 Environment 主题核对，本卡不代表已完成集群适配。

<details>
<summary>完整源码与验证依据（675–900 行）</summary>

Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`；2026-11-10 按本地源码静态核对。以下保留原函数；未运行 Harbor Job、模型或沙箱。卡内省略参数的片段仅用于阅读导航。

```python
async def _run_partition(
    *,
    args: Any,
    config: Any,
    data_source: Any,
    partition: Sequence[_GroupWork],
    runtime: Any,
    rollout_id: int,
    retry_round: int,
    evaluation: bool,
    expected_weight_version: str | None,
) -> list[_GroupOutcome]:
    source_job_config = (
        getattr(data_source, "eval_job_config", None)
        if evaluation
        else getattr(data_source, "job_config", None)
    )
    if source_job_config is None:
        raise HarborRolloutError("Harbor data source has no job configuration")
    run_id = str(getattr(data_source, "run_id", "harbor"))
    job_config = _temporary_job_config(
        source_job_config=source_job_config,
        partition=partition,
        config=config,
        run_id=run_id,
        rollout_id=rollout_id,
        retry_round=retry_round,
    )
    _validate_temporary_job_task_sources(job_config)
    job = await _CREATE_JOB(job_config)
    templates, bindings = _assign_partition_trials(
        job,
        partition,
        rollout_id=rollout_id,
        retry_round=retry_round,
        expected_weight_version=expected_weight_version,
    )
    reward_key = str(config.training.reward_key)
    artifact_store = HarborArtifactStore(
        config.artifacts.root,
        run_id=run_id,
        reward_key=reward_key,
        mode=str(config.artifacts.mode),
        require_token_versions=bool(config.training.require_single_weight_version),
        require_trainable_tokens=bool(config.trajectory.require_trainable_tokens),
        file_mode=int(config.artifacts.file_mode),
        dir_mode=int(config.artifacts.dir_mode),
        fsync=bool(config.artifacts.fsync),
    )
    plugin = _PLUGIN_FACTORY(
        config=config,
        gateway_runtime=runtime,
        artifact_store=artifact_store,
        trial_bindings=bindings,
        defer_final_selection=True,
    )

    def failed_outcomes(
        error: BaseException,
        routing_tasks: Mapping[str, str],
    ) -> list[_GroupOutcome]:
        return [
            _GroupOutcome(
                work=item,
                error=error,
                routing_tasks=dict(routing_tasks),
            )
            for item in partition
        ]

    async def abort_artifacts() -> None:
        # Wait for shielded END commits before reconciling every physical
        # attempt to an explicitly aborted, non-trainable state.
        await plugin.aclose()
        routing = _plugin_routing_summary(plugin)
        await artifact_store.write_job_manifest(
            job,
            final_keys=[],
            state="aborted",
            routing_guarantee=str(routing["routing_guarantee"]),
            public_network_tasks=int(routing["public_network_tasks"]),
            restricted_network_tasks=int(routing["restricted_network_tasks"]),
        )

    try:
        await plugin.on_job_start(job)
        result = await job.run()
        await plugin.on_job_end(result)

        by_trial: dict[str, Any] = {
            str(item.trial_name): item for item in (result.trial_results or [])
        }
        outcomes_by_position: dict[int, _GroupOutcome] = {
            item.position: _GroupOutcome(work=item, samples=[])
            for item in partition
        }
        trial_to_work: dict[str, _GroupWork] = {}
        for trial_name, template in templates.items():
            del template
            match = next(
                (
                    item
                    for item in partition
                    if any(
                        sample is templates[trial_name] for sample in item.templates
                    )
                ),
                None,
            )
            if match is None:
                raise HarborRolloutError(
                    f"lost source mapping for Harbor trial {trial_name}"
                )
            trial_to_work[trial_name] = match

        for trial_name, template in templates.items():
            work = trial_to_work[trial_name]
            outcome = outcomes_by_position[work.position]
            if outcome.error is not None:
                continue
            final_result = by_trial.get(trial_name)
            if final_result is None:
                outcome.error = HarborRolloutError(
                    f"Harbor JobResult is missing final trial {trial_name}"
                )
                outcome.samples = None
                continue
            bundle = plugin.get_result(trial_name, str(final_result.id))
            if bundle is None:
                outcome.error = HarborRolloutError(
                    "Dressage Plugin did not commit final trial "
                    f"{trial_name}/{final_result.id}"
                )
                outcome.samples = None
                continue
            outcome.bundles.append(bundle)
            outcome.final_keys.append((bundle.trial_name, bundle.trial_id))
            try:
                converted = _bundle_samples(
                    template=template,
                    bundle=bundle,
                    args=args,
                    reward_key=reward_key,
                )
            except Exception as exc:  # group failure is retried atomically
                outcome.error = exc
                outcome.samples = None
                continue
            assert outcome.samples is not None
            outcome.samples.extend(converted)
            outcome.versions = tuple(
                dict.fromkeys((*outcome.versions, *bundle.observed_weight_versions))
            )

        expected_attempts = len(partition[0].templates)
        for item in partition:
            outcome = outcomes_by_position[item.position]
            if outcome.succeeded:
                parents = {
                    _metadata(sample).get("parent_traj_id")
                    for sample in outcome.samples or []
                }
                if len(parents) != expected_attempts:
                    outcome.error = HarborRolloutError(
                        f"Harbor group {item.group_index} returned {len(parents)} "
                        f"trajectories; expected {expected_attempts}"
                    )
                    outcome.samples = None
                elif (
                    config.training.require_single_weight_version
                    and len(outcome.versions) != 1
                ):
                    outcome.error = HarborRolloutError(
                        f"Harbor group {item.group_index} observed weight versions "
                        f"{list(outcome.versions)!r}; expected exactly one"
                    )
                    outcome.samples = None

        selected_keys = [
            key
            for outcome in outcomes_by_position.values()
            if outcome.succeeded
            for key in outcome.final_keys
        ]
        manifest_state = (
            "completed"
            if all(outcome.succeeded for outcome in outcomes_by_position.values())
            else "partial"
        )
        routing = _plugin_routing_summary(plugin)
        await artifact_store.write_job_manifest(
            result,
            final_keys=selected_keys,
            state=manifest_state,
            routing_guarantee=str(routing["routing_guarantee"]),
            public_network_tasks=int(routing["public_network_tasks"]),
            restricted_network_tasks=int(routing["restricted_network_tasks"]),
        )

        routing_tasks = _plugin_routing_tasks(plugin)
        for outcome in outcomes_by_position.values():
            outcome.routing_tasks = dict(routing_tasks)
        return [outcomes_by_position[item.position] for item in partition]
    except asyncio.CancelledError:
        try:
            await abort_artifacts()
        except Exception:
            logger.exception("failed to reconcile cancelled Harbor Job artifacts")
        raise
    except Exception as exc:
        routing_tasks = _plugin_routing_tasks(plugin)
        error: BaseException = exc
        try:
            await abort_artifacts()
        except Exception as abort_exc:
            error = HarborRolloutError(
                "Harbor Job failed and artifact abort reconciliation also failed: "
                f"job={type(exc).__name__}: {exc}; "
                f"abort={type(abort_exc).__name__}: {abort_exc}"
            )
        return failed_outcomes(error, routing_tasks)
    finally:
        try:
            await plugin.aclose()
        except Exception:
            logger.exception("failed to close Harbor Plugin after partition execution")
```

形成过程：[Step 011 本次回查](../../../step-011-harbor-trial-lifecycle/04-flow.md#round-and-partition)。

</details>
