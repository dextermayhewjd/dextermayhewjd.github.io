# _run_partition

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

- 本步调取补记：Step 011 曾回查运行返回、组检查和产物选用；2026-11-12 接续时复制[已更新的原卡](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md)，保留全部原话、日期与来源。

- 源码：[dressage/integrations/harbor/rollout.py:675–900](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L675)。
- 首次单独展开：2026-11-10，初建于 Step 011；同日按用户确认归回 Step 010。此前仅定位 Job/插件关键调用。
- 最近认识更新：2026-11-11，用户已串起原始配置、分区具体配置与 Job 的主干关系；任务选择及 job 已是 Harbor Job 两点由助手校准。

[_run_round](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) → 内部 `run_partition` → **_run_partition** → Harbor Job · [本步导航](../../../../../../../step-010-harbor-rollout-entry/01-scope.md#reading-navigation)

**进入这里时**：上游已经确定当前 `partition`，并取得路由额度；现在把这份工作交给本函数，要求它执行并返回各组结果。上游调度细节回看 [_run_round](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline)。

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

下面是数据交接示意，不是可执行代码。[1]–[4] 对应下方段落。**第 [1]–[3] 段已有主线介绍与复述；当前按整体流程阅读 [4] 的结果归组与返回。** 插件与 Harbor 调度内部未逐段展开。

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
| [2. 准备插件](#prepare-plugin) | 705–730 | `templates`、`bindings`、`plugin` → 执行与结果归组 |
| [3. 运行 Job](#run-job) | 759–762 | `result`（JobResult）→ 下一段查最终 Trial 结果 |
| [4. 整理结果与收尾](#collect-outcomes) | 764–900 | 各组 `_GroupOutcome` → 本函数最终返回 |

<a id="create-job"></a>

### 1. 创建 Job

**这里有两个配置对象和一个执行对象。** `source_job_config` 与 `job_config` 都保存“怎样运行”的安排；`job` 是根据安排创建、负责组织运行的 Harbor 对象。不是同一个对象先后换了三个名字。

<a id="job-config-objects"></a>

先用同一份静态例子区分三者：假设原配置定义了 A、B、C 三个任务，使用 Claude；本次取得的 partition 只含 A、C 两项工作，每项有两份尝试模板。这里只展示区别，不是完整配置或真实运行输出。

| 变量 | 在当前 Harbor 路径中是什么 | 同一个例子中，它表示什么 |
| --- | --- | --- |
| `source_job_config` | 数据源已经保存的原始 `JobConfig` 对象；本行只是取出引用 | 原来定义的 A、B、C、Claude、环境等整套执行配置 |
| `job_config` | `_temporary_job_config` 生成的另一份 `JobConfig` 对象 | 这次只运行 A、C，使用对应的 Claude 配置，每项尝试 2 次；并发数等也按本次分区设置 |
| `job` | `_CREATE_JOB` 创建的 `Harbor Job` 执行对象 | 按上面这份本次配置，准备组织 A、C 的尝试；随后可以调用 `job.run()` |

因此前两者的区别是**配置适用的范围和具体值**；第三者与前两者的区别是**对象的职责**。配置对象保存安排，Job 对象负责按安排组织执行。原来的 `source_job_config` 不会被这里原地改写。

**原始配置从哪里来？** 数据源初始化时已通过 `_load_job_config(...)` 保存到 `data_source.job_config`，见 [HarborDataSource.__init__ 的配置加载处](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.__init__.md#data-source-precondition)。当前训练分支取它，评估分支则取 `data_source.eval_job_config`。

下面是源码 687–704 行的连续代码，保留训练/评估分支和检查；注释对应上表三种角色。

```python
# 1. 取一个引用：source_job_config 指向数据源已经保存的配置对象。
source_job_config = (
    getattr(data_source, "eval_job_config", None)
    if evaluation
    else getattr(data_source, "job_config", None)
)
if source_job_config is None:
    raise HarborRolloutError("Harbor data source has no job configuration")
# 2. 创建新配置对象：以原配置为基础，改成当前 partition 的运行安排。
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
# 3. 创建执行对象：job 是 Harbor Job，后面调用 job.run() 才开始执行。
job = await _CREATE_JOB(job_config)
```

当前实际链条是：**引用已有配置 → 创建本分区的新配置 → 按新配置创建 Job**。默认 `_CREATE_JOB` 经 `_default_create_job` 调用 Harbor 的 `Job.create(job_config)`；“本次配置”不表示 Agent 必须在本机运行。

<a id="job-config-changes"></a>

<details>
<summary>按需回查：原始配置到本次配置，具体覆盖了哪些字段</summary>

**`_temporary_job_config` 到底改了什么？** 每次为当前 `partition` 生成一份新的 Job 配置。原来的 `source_job_config` 保留；下面这些字段被覆盖，未覆盖的字段从原配置复制保留。

| 主要字段 | 本次临时配置具体采用什么 |
| --- | --- |
| `tasks` | 当前 partition 中每项 `spec.task_config` 的副本；每个任务的 `source` 设为 None |
| `agents` | 只放当前分区共用的一份 Agent 配置，取自第一项的 `spec.agent_config`；其 `n_concurrent` 设为 None |
| `n_attempts` | 第一项工作中的模板数量 `len(partition[0].templates)`；原代码要求本分区各组的模板数量相同 |
| `n_concurrent_trials` | 当前分区的 Trial 总数与 `max_active_routes` 两者中的较小值，即前面讨论的路由需求额度 |

例如当前 partition 只有 A、C 两项工作，各有两份模板，那么临时 Job 的 tasks 只包含 A、C，`n_attempts=2`；若路由上限至少为 4，`n_concurrent_trials=4`。这是静态示例，原配置本来的具体数值取决于输入。

**其余覆盖项：命名、目录、数据集与环境**

| 字段 | 修改内容 |
| --- | --- |
| `job_name` | 根据 run_id、rollout_id、retry_round、公开 Agent 标识和随机后缀生成本次名称 |
| `jobs_dir` | 设为配置的产物根目录下的 `harbor-jobs` |
| `datasets` | 设为空列表；本次工作已作为上面的显式 tasks 提供 |
| `quiet` | 设为 True |
| `environment` | 仅在 `config.environment.mode == "bwrap"` 时覆盖：以原环境配置为基础，将 type 设为 None、import_path 设为 DressageEnvironment；其他模式沿用原配置 |

这些更新在 [_temporary_job_config:505–578](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L505) 中汇集，再由 `_validated_model_update` 复制/校验为新对象，不原地改写源配置。这里的 `agents[0].n_concurrent` 与 Job 的 `n_concurrent_trials` 是不同字段，不能混为一个限制。

</details>

**本段结束时只有 Job 创建完成，还没有调用 `job.run()`。** 下一段拿着这个 `job` 和原来的 `partition`，建立 Trial 与模板的对应关系并准备插件；`job` 也不是整个 `_run_partition` 函数最终返回的组结果列表。

<a id="prepare-plugin"></a>

### 2. 准备插件

**进入本段时已有 `job` 和 `partition`。现在需要解决：将来每个 Trial 的结果属于哪个原始模板，以及由谁配合 Harbor 保存这些结果。**

<a id="assign-trials-call"></a>

源码 705–730 行的节选，保留 Trial 绑定与插件参数，省略产物存储的详细配置；完整原函数在文末。

当前已从 [_assign_partition_trials 函数卡](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_assign_partition_trials.md#assign-mainline) 回到 `templates, bindings = ...`。本轮继续下面第 2 项：读取 `reward_key`，创建 `HarborArtifactStore(...)` 存储对象。

```python
# 1. 给 Job 中的 Trial 建立模板对应表与任务身份绑定。
templates, bindings = _assign_partition_trials(
    job,
    partition,
    rollout_id=rollout_id,
    retry_round=retry_round,
    expected_weight_version=expected_weight_version,
)

# 2. 创建产物存储对象：供插件保存每次尝试的轨迹 bundle、身份与相关信息。
# 这里只创建管理对象；实际产物在后续运行和收尾时保存。
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

`artifact_store` 在构造时保存根目录、run_id、奖励字段与存储规则，并初始化提交任务和结果的记录容器；这里尚未保存本次 Trial 的轨迹。第 3 项会把这个对象交给插件，供后续使用。

`reward_key` 是后续奖励字典中的字段名，不是奖励算法。例如评测结果为 `{"accuracy": 0.8}`，配置 `reward_key="accuracy"` 就表示读取其中的 accuracy；本段还没有计算出 0.8。`run_id` 标记这些产物所属的运行，不描述任务怎样执行。

创建 `plugin` 时，是把各有职责的对象和资料交给它使用：`trial_bindings` 提供身份对应，`gateway_runtime` 管模型请求的路由运行环境，`artifact_store` 负责产物保存。它们不是合并成一份执行结果；下一段 `on_job_start(job)` 才把插件接到具体 Job 的生命周期上。


可以把前两个对象理解为“查模板的表”和“查任务身份的表”：它们使用同一个 `trial_name` 关联，服务于后面的不同处理。`bindings` 当前没有 session_id 字段，不把这里误记成已完成会话登记。

**本段只是准备这些对象。** 当前还没有调用 `plugin.on_job_start(job)` 挂接生命周期回调，也没有调用 `job.run()`。下一段才把已经准备的插件接到 Job 上并开始运行；本段不进入插件内部或 Trial 执行。

<details>
<summary>按需核对：绑定来源与最终结果选择</summary>

`_assign_partition_trials`（rollout.py:581 起）取得 Job 的 Trial 计划，按 task_index 找到原工作组、按 attempt_index 找到组内模板，并将两份对应关系存到 templates 和 bindings。`TrialBinding`（plugin.py:95 起）包含任务实例、尝试序号和期望权重版本。

`defer_final_selection=True` 让最终采用哪些结果留到本函数整理成功组时决定；具体产物选择逻辑在第 4 段按需回查。当前已单独建立 _assign_partition_trials 卡片；其余辅助实现仍按需回查。

</details>

<a id="run-job"></a>

### 3. 运行 Job

```python
await plugin.on_job_start(job)     # 在运行前接入插件配置与生命周期回调。
result = await job.run()           # Harbor 调度多个 Trial，等待 Job 结果。
await plugin.on_job_end(result)    # Job 返回后，完成插件的 Job 级收尾。
```

运行期间，各 Trial 到相应阶段才触发插件回调。这里的 `result` 是 `JobResult`，包含最终 Trial 结果；轨迹 bundle 由后面通过插件取回。

**两种交接分开看：** Trial 的 END 会在 `await job.run()` 尚未返回时调用已登记的 `_on_end`；只有整份 Job 返回后，当前函数才继续调用 `on_job_end(result)`。前者是运行期间的回调，后者是本函数下一条语句。此处保留调用现场，插件注册和具体回调实现按各自函数进入，不在本卡展开。

一个静态例子：本区有两组，每组两份模板，就会安排四个逻辑 Trial；Harbor 还可能按其配置重试。一个 Job 不等于一道题，一个 Trial 也不等于一次模型调用。

| 后续观察点 | 进入方式 | 返回本函数的位置 |
| --- | --- | --- |
| [Job.run 函数卡](../../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job.run.md#job-mainline) | 从 `await job.run()` 进入，再经队列与 Task 运行各个 Trial | 所有相关 Trial 执行结束并由 Job 汇总后，`result` 接住 JobResult，再进入 `plugin.on_job_end(result)` |


<a id="collect-outcomes"></a>

### 4. 整理结果与收尾 · 当前

**进入本段时已有 JobResult、原工作分区和模板对应表。这里把各 Trial 的结果与轨迹接回原工作组，生成各组 outcome，再记录并返回。**

下面参照第 2 段的粒度，按实际顺序看三个动作。代码是正常路径的阅读骨架：省略索引构建的内部语句、缺失/失败处理、附加字段累计及校验细节；完整源码保留在文末。

```python
# 1. 准备对应关系：Trial 的结果、所属工作，以及各工作组的结果容器。
by_trial = {
    str(item.trial_name): item for item in (result.trial_results or [])
}
outcomes_by_position = {
    item.position: _GroupOutcome(work=item, samples=[]) for item in partition
}
trial_to_work: dict[str, _GroupWork] = {}
# 原代码接着按模板对象查找所属工作，填入 trial_to_work；此处省略该循环。

# 2. 逐个 Trial 取回结果与轨迹，转换 Sample 并归回原工作组。
for trial_name, template in templates.items():
    work = trial_to_work[trial_name]
    outcome = outcomes_by_position[work.position]
    final_result = by_trial.get(trial_name)
    bundle = plugin.get_result(trial_name, str(final_result.id))
    converted = _bundle_samples(
        template=template,
        bundle=bundle,
        args=args,
        reward_key=reward_key,
    )
    outcome.samples.extend(converted)
    # 原代码同时累计 bundles、final_keys 和 versions。

# 3. 检查组结果是否完整、满足配置要求；不是重新判题。
# 原代码检查每组不同 parent_traj_id 的数量是否等于预期尝试数，
# 并在要求单一权重版本时，检查 outcome.versions 是否只有一个版本。
# 不满足就记录 error，并将该组 samples 设为 None；检查语句此处省略。

# 只把结果处理成功的组，其最终尝试身份列入选用清单。
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
# artifact_store 管理前面各次尝试的轨迹 bundle、身份与相关信息。
# 此处记录最终选用结果：采用哪些尝试、产物在哪里、Job 是完整还是部分完成。
# 同时更新产物的选用标记；调用参数与后续路由摘要语句省略。
await artifact_store.write_job_manifest(...)

# 成功组和失败组都返回；每组仍在原位置，失败原因留给上层处理。
return [outcomes_by_position[item.position] for item in partition]
```

这里的“成功”是 `error is None and samples is not None`，不是奖励大于零。比如一组预期两次尝试，就检查是否得到两条不同的父轨迹；一条轨迹拆成多个 Sample，不算多次尝试。`write_job_manifest` 在磁盘模式写出选用索引和完成状态，也会把未选用的尝试产物标为 superseded、不可训练；详细文件写入机制暂不展开。

| 本段使用的对象 | 记住它的用途 |
| --- | --- |
| <a id="result-by-trial"></a>`by_trial` | 按 Trial 名称找到 Job 返回的执行结果 |
| <a id="group-result-containers"></a>`outcomes_by_position` | 按原工作位置保存组结果，接收转换后的 Sample |
| `trial_to_work` | 按 Trial 名称找到它所属的原工作组 |
| `bundle` → `converted` | 插件保存的轨迹结果，结合原模板转换成 Sample 列表 |

**本段最终交回的是各组 `_GroupOutcome` 列表，不是 JobResult 本身。** 外层 `_run_round` 收集各分区结果，再由批次父函数处理完成组与后续工作。离开本函数的 try 时，finally 还会执行插件关闭。

<details>
<summary>按需回查：索引细节与失败边界</summary>

by_trial 按名称保留原 Trial 结果对象；outcomes_by_position 为每项原工作创建 `_GroupOutcome(work=item, samples=[])`；trial_to_work 通过此前保存的模板对象找到所属工作。已展开的逐项解释和例子保留在[调整前记录](../../../../../../../step-010-harbor-rollout-entry/references/history/2026-11-11-run-partition-before-result-overview.md#result-by-trial)，当前先沿上面三步读通。

原代码检查组内轨迹数量与可选的单权重版本要求，选择成功组产物，写入 completed 或 partial manifest。`outcome.succeeded` 表示没有 error 且 samples 不为 None，不等于答案正确或评测满分。缺少最终结果、缺少 bundle、转换失败或组检查失败，会将对应组标为失败。

try 内普通异常会走产物中止处理并返回失败 outcome，取消则继续抛出；finally 关闭插件。Job/插件创建在该 try 之前，早期异常由上游包装处理。具体转换、提交和错误分支按后续问题回查，不在本段逐项展开。

</details>

**读完本函数，接回上游**：组结果列表交回 [_run_round](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_round.md#round-mainline) 汇总；额度归还由它的内部包装负责，本卡不重复展开。

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


2026-11-11，三对象对照改写后，用户表述：

> 好的 我的简单理解就是这里的这个source job 是最基础的部分
> 也几乎是所有的配置
> job config是根据对应的claude或者codex配置
> 给出的对应的并发 等属性
> 然后给出对应的具体执行的方案
> 最后在这里的这个job给出的更多的是通过这个job转化为harbor job之后到底应该考虑如何运行这一点
> 是我的理解

助手校准：主线是原始执行配置 → 当前分区的具体执行配置 → Harbor Job 执行对象。source_job_config 是原始 Harbor 执行配置，不等于所有 Dressage 接入配置；临时 job_config 同时选择本区任务、对应 Agent、尝试次数与并发等。默认 _CREATE_JOB 返回的 job 已经是 Harbor Job，无需之后再次转化；后面调用 job.run()。用户已表达三个角色的主干关系，不据此认定 Job 内部调度已经掌握。


2026-11-11，用户对第 2 段的疑问：

> 好的 那么现在看一下这里的这个部分吧
> 我其实不是特别理解这里的这个reward key或者artifact store
> 这里是吧对应的什么run id 还有怎么奖励的什么放在一块
> 这样子最后就能够把这个job是怎么运行的 放在一块?
>
> 然后最后在是杂糅
> 吧省份绑定什么的 gateway runtime什么的都放在一起?
> 这是我的理解
> 那么是否考虑一下继续吧
> 看一下现在还有什么需要理解的呢

助手校准：本段准备后续执行要使用的对象；reward_key 选择奖励字段，不计算评分。artifact_store 记住保存位置、运行标识和规则；插件接收身份、Gateway 与存储对象以协同工作，而不是将它们合成结果。下一处阅读入口为 on_job_start(job) 的接入动作，Job 仍由后面的 job.run() 运行。


2026-11-11，用户对第 3 段主线的复述：

> 好的
> 我大概清楚了
> 然后就是把这里的这个job run运行起来对吗?
> 等待job结果
> 我大概理解是这里就是把这个job 交给harbor 让harbor开始调度和运行了
> 同时这里的这个plugin 应该也是有如何接入这些插件或者部分
> 最后job run了之后返回结果
> 然后plugin on job end 之后给出一个类似于hook的结束步骤
> 那么我们现在是否需要考虑一下下一步了呢?

助手确认 on_job_start → await job.run → on_job_end 的顺序；Job 运行期间由已注册的生命周期回调参与。当前返回的是 JobResult，尚需第 4 段整理轨迹与组结果；on_job_end 的完成不等于已返回训练 Sample。主线复述不代表插件/调度器内部已逐段阅读。


2026-11-11，用户对 by_trial 表述：

> 好的 我感觉我差不多理解了
> 就是按照名字来查询
> 好的 那么我们现在继续吧
> 还有什么需要看的吗?
> 关于这里的run partition的部分?

助手确认按名称查询的作用，接着介绍 outcomes_by_position 的空组结果容器；不将此理解扩展为整段结果整理已掌握。


2026-11-12，接回本段时的复述与卡点：

> 好的 简单来说这里的这个trial run之后的给出的结果
> 那么我们目前是需要看什么呢?
> 或者说我应景知道了
> 这里就是job run 汇总为job result
> 然后run partition接住了
> 然后做的内容是
> 把这里的trial的结果按照位置还原
> 以及这里逐个按照trial 来把这里trial的内容
> 转化为samples的格式
> 是我理解
> 检查结果和记录产物什么的我不是特别理解
> 也就是这里的4部分的#3

助手核对：本段用最终 TrialResult 匹配插件保存的轨迹 bundle，再结合模板转为 Sample，归入原工作组。#3 检查轨迹条数及可选单版本要求，筛选结果处理成功组的最终尝试身份并做产物对账，最后按原分区顺序返回全部组的 outcome。不是重新评分或只返回高奖励结果；此解释尚待用户反馈。

2026-11-12，对最终产物记录的追问：

> 好的 简单来说就是这里把成功或者失败的部分全都写到这里的这个artifact store对吗?
> 是我的理解
> 或者说这里的成功组还是失败组这类的内容
>
> 那么现在考虑一下当前是否需要继续读下一个step了呢?

助手校准：ArtifactStore 管理已经收集的尝试产物及最终选用状态；成功组的 final_keys 被选入清单，缓存中未选用的本 Job 尝试被标记为未采用/不可训练，并记录 completed/partial。它不直接把所有 _GroupOutcome（包括完整 error）全部写入；组错误仍保留在返回的 outcome 里，部分失败也可能没有完整产物。此处不再下钻存储实现。

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

形成过程：[Step 011 本次回查](../../../../../../../step-011-harbor-trial-lifecycle/04-flow.md#round-and-partition)。

</details>
