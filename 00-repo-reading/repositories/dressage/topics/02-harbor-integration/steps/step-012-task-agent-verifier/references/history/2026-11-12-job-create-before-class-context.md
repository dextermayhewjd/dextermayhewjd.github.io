# Job.create

- 源码：[src/harbor/job.py:171–225](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L171)，Harbor v0.25.0。
- 首次单独展开：Step 012，2026-11-12；此前仅用于定位 JobPlan 的调用背景。
- 本轮范围：普通创建路径，config.source_jobs 为空、非 diff/regrade；先看材料准备、实例初始化与返回，不深入加载器。

[Step 010 创建调用](../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#create-job) → [_default_create_job](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L101) → **Job.create** → [Job.__init__](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L77) · [本步 scope](../../01-scope.md#current-reading)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_run_partition 已经生成本分区的 job_config，现在需要拿到一个可以交给后续代码使用的 Job 对象。
2. **具体内容**：解析/检查配置，取得任务、指标与本地任务材料，再构造 Job；初始化完成后返回该对象。
3. **建议构建的心智模型**：

   > 先备齐创建材料，再完成 Job 初始化，最后把这个 Job 交回去；任务执行是后面的 job.run。

4. **调用代码**：_CREATE_JOB 默认绑定 _default_create_job（Dressage rollout.py:101–111）。

   ```python
   # _run_partition 中：等待整个创建过程完成。
   job = await _CREATE_JOB(job_config)

   # 默认 _default_create_job 内：版本检查、导入之后委派给 Harbor。
   return await Job.create(config)
   ```

   两段属于不同函数的调用位置，不是连续源码。Dressage 的旧版依赖限制尚未升级，本卡按 Harbor 0.25 分析内部创建过程，不声称组合已运行。

## 本场景的输入与输出

<a id="job-create-mainline"></a>

输入 config 是已经组织好的 JobConfig。输出是初始化完成的 Job 对象；不是 JobResult，也不是 TrialConfig 列表。任务来源解析与缓存可能有文件或下载操作，但这里不执行 Trial 的解题过程。

### 创建主干：材料 → 初始化 → 返回

以下为普通路径的源码节选。省略 source_jobs/diff 分支和构造后针对包数据集的通知；保留构造所需的实参。cls 在本次 Job.create 调用中就是 Job。

```python
# 检查 Agent 配置，并把任务来源解析为可用的任务列表。
cls._resolve_agent_skills(config)
cls._preflight_agents(config, config.agents)
task_configs = await cls._resolve_task_configs(config)
EnvironmentFactory.validate_resource_policies(config.environment)
metrics, datasets = await cls._resolve_metrics(config, task_configs)
task_download_results = await cls._cache_tasks(task_configs)
source_job_dirs = None  # 当前普通路径不引用已有 Job。

# cls 是 Job；构造实例时进入 Job.__init__，初始化完成后本行才赋值给 job。
job = cls(
    config,
    _task_configs=task_configs,
    _metrics=metrics,
    _task_download_results=task_download_results,
    _source_job_dirs=source_job_dirs,
)

# 原代码这里还可能通知包数据集：下载后处理已可进行；本轮省略。
return job  # 交回 _default_create_job，最终由 _run_partition 的 job 接住。
```

### 之前的 build_trial_configs 在哪里？

它位于上面 cls(...) 的初始化内部，不是在 return job 之后调用。

```text
Job.create
├─ 取得任务、指标与任务材料
├─ job = cls(...)                 ← 下一处需要进入的调用
│  └─ Job.__init__
│     ├─ 保存配置、任务等字段
│     ├─ _init_trial_configs
│     │  └─ _build_standard_trial_configs
│     │     └─ JobPlan.build_trial_configs → 返回 TrialConfig 列表
│     └─ 完成剩余初始化，包括待运行配置与 TrialQueue
└─ return job                     ← 初始化完成，才把 Job 交出去
```

| 本函数的位置 | 进入哪里、返回后做什么 |
| --- | --- |
| job = cls(...) | [Job.__init__:77](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L77)：看对象保存什么、何时生成尝试配置；返回本行后，继续 Job.create 的后续通知与 return job |
| __init__ 内的配置生成 | [已有 JobPlan.build_trial_configs 卡](../../02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-plan-mainline)：暂保留，读到初始化调用处再进入，不另起独立执行阶段 |
| return job | 回到 [_run_partition:704](../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#create-job)：接着建立模板/身份绑定和插件，再到已有的 job.run 主线 |

当前先看清 cls(...) 与 return job 之间的关系，任务解析、指标和下载器只认返回材料。

## 我的直接表述（原话）

> 那么看一下这里的这个create了这个job之后
> 是怎么一步步走下去的
> 是否需要考虑一下每一个都按照这种方式来构建一下short term memory呢?

助手补充：当前正在查看的初始化和 Trial 配置组成仍属于 Job 创建过程，只有 return job 之后，调用方才拿到初始化完成的 Job。逐个进入当前需要的函数，薄转发先保留真实语句，不一次性预建全部卡片。尚无本函数的独立复述。

## 尚不清楚

- Job.__init__ 具体保存哪些字段、哪些初始化先后影响执行，下一处围绕已有调用继续。
- task_configs、metrics 与任务缓存的详细加载机制，本轮不深入。
- resume、diff/regrade 与包数据集通知的特殊分支，当前不展开。

<details>
<summary>来源与验证</summary>

- Harbor v0.25.0 固定提交 fdba28fc411e47e8765420a1a063b4918fce3def；本地 git show 核对 Job.create:171–225、__init__:77–145、配置选择:448–462。
- Dressage 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，rollout.py:101–111、704–705；默认别名、委派和返回位置已核对。
- 未执行创建、下载、安装、Job.run 或集群操作。源码节选不是完整可执行脚本。
- [Step 012 形成过程](../../04-flow.md#job-create-context)。

</details>
