# Job.create

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../step-014-model-routing-and-api-contract/03-long-term-memory/functions/harbor/job.py/Job.create.md) 完整继承；不改变原认识时间或掌握状态。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job.create.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../step-012-task-agent-verifier/02-short-term-memory/functions/harbor/job.py/Job.create.md) 完整继承；复制不改变原认识时间或已掌握状态。

- 源码：[src/harbor/job.py:171–225](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L171)，Harbor v0.25.0。
- 首次单独展开：Step 012，2026-11-12；此前仅用于定位 JobPlan 的调用背景。
- 本轮范围：普通创建路径，config.source_jobs 为空、非 diff/regrade；先看材料准备、实例初始化与返回，不深入加载器。

[从 Step 010 的创建 Job 调用进入](../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#create-job) → **当前：Job.create** → [到 cls(...) 时进入 Job.__init__](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline) · [scope](../../../../../step-012-task-agent-verifier/01-scope.md#reading-sequence)

进入时只有 JobConfig 和 Job 类；本函数准备材料并构造实例。Job.__init__ 完成后回到 cls(...)，最后返回 Job 对象给调用方。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_run_partition 已经生成本分区的 job_config，现在需要拿到一个可以交给后续代码使用的 Job 对象。
2. **具体内容**：解析/检查配置，取得任务、指标与本地任务材料，再构造 Job；初始化完成后返回该对象。
3. **建议构建的心智模型**：

   > 先备齐创建材料，再完成 Job 初始化，最后把这个 Job 交回去；任务执行是后面的 job.run。

4. <a id="job-create-callsite"></a>**调用代码**：从 _run_partition:704 进入默认创建函数。

   ```python
   # 先算完右边的 await，才把返回对象赋给左边的 job。
   job = await _CREATE_JOB(job_config)
   ```

   _CREATE_JOB 默认指向下面这个函数（Dressage rollout.py:101–108，完整执行语句）：

   ```python
   async def _default_create_job(config: Any) -> Any:
       from dressage.integrations.harbor.compat import require_harbor_runtime

       require_harbor_runtime()
       from harbor.job import Job  # 导入的是类 Job，不是一份已创建的 job 实例。

       return await Job.create(config)  # 在类上调用 create，再把它的结果交回去。
   ```

   Dressage 的旧版依赖限制仍需适配；本卡按 Harbor 0.25 分析创建机制，没有实际执行以上跨版本调用。

## 本场景的输入与输出

<a id="job-create-mainline"></a>

### 先分清 Job、cls 和 job

调用前已经存在的是 **Job 类和 config 配置**，不是本次要创建的 job 实例。`@classmethod` 允许通过类调用方法；本次写 `Job.create(config)`，Python 就把 Job 类传给 cls。 **起作用的是 @classmethod，cls 只是约定的参数名；普通实例方法不会因为把 self 改名为 cls 就变成类方法。**

### 创建代码：在哪里才产生实例？

以下保留类声明、方法声明和普通创建路径；省略类的其他方法、diff/source_jobs 分支及构造后的包数据集通知。调用当前方法不是再次执行类定义；类声明在这里是为了展示该方法属于谁。

```python
class Job:
    @classmethod  # 本次由 Job.create(...) 调用，所以 cls 指向 Job 类。
    async def create(cls, config: JobConfig) -> "Job":
        # 先准备创建材料。这几行还没有创建本次的 Job 实例。
        cls._resolve_agent_skills(config)
        if not config.source_jobs:
            cls._preflight_agents(config, config.agents)
        task_configs = await cls._resolve_task_configs(config)
        EnvironmentFactory.validate_resource_policies(config.environment)
        metrics, datasets = await cls._resolve_metrics(config, task_configs)
        task_download_results = await cls._cache_tasks(task_configs)
        source_job_dirs = None  # 当前只看普通路径。

        # 这里才构造实例：本次 cls(...) 就是在调用 Job(...)。
        # 构造过程中进入 Job.__init__；初始化完成后才赋给这里的 job。
        job = cls(
            config,
            _task_configs=task_configs,
            _metrics=metrics,
            _task_download_results=task_download_results,
            _source_job_dirs=source_job_dirs,
        )

        # 原代码在这里还有可选的包数据集通知，本轮省略。
        return job  # 交回这个实例，不是在这里运行 job.run()。
```

<a id="job-create-return"></a>

返回到 _default_create_job，再返回 _run_partition 后，最外层的 `job = await _CREATE_JOB(job_config)` 才取得同一个实例。随后调用方继续绑定模板、准备插件、运行 Job。

输入为 JobConfig，输出为初始化完成的 Job；任务解析与缓存可能执行文件/下载操作，但这里尚未执行 Trial 的解题流程。

### 下一处只从 cls(...) 进入 Job.__init__

之前的 JobPlan.build_trial_configs 是 Job.__init__ 内部生成尝试配置时使用的下游函数。**先看清初始化，再沿它的真实调用进入配置组装，不直接跨过去。**

| 当前代码位置 | 进入哪里、回来继续什么 |
| --- | --- |
| job = cls(...) | [Job.__init__ 函数卡](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline)：接收上面的创建材料，完成初始化；回来后继续可选通知与 return job |
| 初始化内部的配置组装 | [已有 JobPlan.build_trial_configs 卡](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md#trial-plan-mainline)：只在读到 _init_trial_configs 的委派时进入 |
| return job | 回到 [Step 010 的创建调用](../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#create-job)，外层变量接住对象后继续 |

## 我的直接表述（原话）

> 那么看一下这里的这个create了这个job之后
> 是怎么一步步走下去的
> 是否需要考虑一下每一个都按照这种方式来构建一下short term memory呢?

助手补充：当前正在查看的初始化和 Trial 配置组成仍属于 Job 创建过程，只有 return job 之后，调用方才拿到初始化完成的 Job。逐个进入当前需要的函数，薄转发先保留真实语句，不一次性预建全部卡片。尚无本函数的独立复述。

本轮进一步追问：

> 但是我在这里 其实没有看出来这个job是如何调用create的?
> 我可以理解当前先创建一个job
> 但是下面这个只是给了一下骨架图
> 是不是有点简略了呢?
> 作为一个资深的程序员和认知学家 你会如何构建这个job create呢?

助手校准：这里不是先创建 job 实例再调用 create，而是调用已经定义的 Job 类上的类方法；进入 create 时 cls 是类，执行 cls(...) 时才构造本次实例，返回后外层 job 才接住它。旧卡省略声明使这一关系不清楚，本轮补回，不把解释记为用户已掌握。

最新表述与下一处询问：

> 好的 也就是通过先拿到这样子的一个class然后通过cls的方式
> 来构建这个cls?
> 那么你现在看一下
> 我们目前应该看哪一个short term memory呢?
> 先看这个job init吗?
> 还是什么?

助手校准：本次 cls 指向 Job 类，cls(...) 构造新的 Job 实例；不是构建 cls 这个类。下一处推荐 Job.__init__，只看接收材料、保存字段及尝试配置初始化的交接，尚未开始该函数的独立卡片。

## 尚不清楚

- Job 类、cls 与本次 job 实例的关系已补源码解释，仍待用户确认；Job.__init__ 的具体字段与调用顺序下一处再看。
- task_configs、metrics 与任务缓存的详细加载机制，本轮不深入。
- resume、diff/regrade 与包数据集通知的特殊分支，当前不展开。

<details>
<summary>来源与验证</summary>

- Harbor v0.25.0 固定提交 fdba28fc411e47e8765420a1a063b4918fce3def；本地 git show 核对 Job.create:171–225、__init__:77–145、配置选择:448–462。
- Dressage 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，rollout.py:101–111、704–705；默认别名、委派和返回位置已核对。
- [本轮重排前的完整卡片](../../../../../step-012-task-agent-verifier/references/history/2026-11-12-job-create-before-class-context.md)保留旧稿与来源。
- 未执行创建、下载、安装、Job.run 或集群操作。源码节选不是完整可执行脚本。
- [Step 012 形成过程](../../../../../step-012-task-agent-verifier/04-flow.md#job-create-context)。

</details>
