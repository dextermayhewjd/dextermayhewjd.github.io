# Job.__init__

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../step-014-model-routing-and-api-contract/03-long-term-memory/functions/harbor/job.py/Job.__init__.md) 完整继承；不改变原认识时间或掌握状态。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job.__init__.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../step-012-task-agent-verifier/02-short-term-memory/functions/harbor/job.py/Job.__init__.md) 完整继承；复制不改变原认识时间或已掌握状态。

- 源码：[src/harbor/job.py:77–145](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L77)，Harbor v0.25.0，提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 012，2026-11-12。
- 本轮范围：由 Job.create 创建普通新 Job；不展开恢复旧 Job、source_jobs/diff/regrade、日志和状态统计内部。

[从 Job.create 的 cls(...) 进入](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job.create.md#job-create-mainline) → **当前：Job.__init__** → [到 self._init_trial_configs() 时进入下一张](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline) · [scope](../../../../../step-012-task-agent-verifier/01-scope.md#reading-sequence)

进入时 self 是正在初始化的新实例，调用方已提供配置、任务和指标材料；先保存字段，读到 _init_trial_configs 再下钻，回来后继续剩余初始化。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Job.create 已解析好任务、指标与任务材料，执行 cls(...) 构造 Job，进入这里初始化新实例。
2. **具体内容**：保存材料，生成每次尝试的配置，建立记录与待运行列表，创建 TrialQueue 并登记 Job 自己的状态回调。
3. **建议构建的心智模型**：

   > 把创建材料和运行管理需要的东西装到这份 Job 上，供后面的 job.run 使用。

4. **调用代码**（Job.create:209–215）：

   ```python
   # cls 是 Job 类；进入 __init__ 时，self 是正在初始化的新实例。
   job = cls(
       config,
       _task_configs=task_configs,
       _metrics=metrics,
       _task_download_results=task_download_results,
       _source_job_dirs=source_job_dirs,
   )
   # __init__ 正常结束后，这一行才把初始化好的实例赋给 job。
   ```

## 本场景的输入与输出

### 沿用创建时已经准备好的材料

config 是整份 JobConfig，_task_configs 是任务来源列表，_metrics 是指标对象，_task_download_results 记录任务材料的取得结果；普通新建路径中 _source_job_dirs 为 None。这里不重新加载所有输入。

**__init__ 正常隐式返回 None，但外层 cls(...) 表达式得到的是完成初始化的 Job 实例。** 字段变化保存在 self 上。此时尚未运行任何 Trial，也还没有生成本次 JobResult；Job.run 才开始组织执行。

<a id="job-init-mainline"></a>

### 初始化主干：解释直接跟着代码读

下面按源码顺序节选主要语句；省略必需参数检查、旧结果读取/ID/锁初始化、日志字段默认值和特殊作业分支。完整函数保留在文末。当前按新的普通 Job 理解，不把节选当成独立可运行代码。

```python
# 保存 Job.create 传来的材料，后续方法都从 self 取用。
self.config = config  # 保存传入对象的引用，不自动复制配置。
self._task_configs = _task_configs
self._task_download_results = _task_download_results
self._metrics = _metrics

# 生成“每一次尝试怎样运行”的配置，写入 self._trial_configs。
# 普通路径内部：_build_standard_trial_configs -> JobPlan.build_trial_configs。
self._init_trial_configs()

# 建立本 Job 的记录目录和日志；此处创建的是本地目录，不是运行沙箱。
self.job_dir.mkdir(parents=True, exist_ok=True)
self._init_logger()

# 准备已有结果、任务缓存与进度记录；首次运行没有旧结果要恢复。
self._maybe_init_existing_job()
self._seed_hub_source_trial_caches()
self._init_progress_tracking()

# 从完整计划中确定剩余工作；新 Job 没有已完成记录，通常全部待运行。
self._init_remaining_trial_configs()  # 写入 self._remaining_trial_configs。
self._live_rewards = self._existing_rewards.copy()

# 创建执行管理对象；此时不提交协程、不创建执行 Trial 的 Task。
self._trial_queue = TrialQueue(
    n_concurrent=self.config.n_concurrent_trials,
    retry_config=self.config.retry,
)

# 给队列登记 Job 自己的状态回调；只是保存函数，尚未执行回调。
self._trial_queue.add_hook(TrialEvent.START, self._on_trial_started)
self._trial_queue.add_hook(TrialEvent.CANCEL, self._on_trial_cancelled)
self._trial_queue.add_hook(TrialEvent.END, self._on_trial_completed)
# 正常走完后回到 Job.create 的 cls(...) 调用处。
```

**实例与配置引用分开看**：这里每次成功构造得到不同的 Job 实例；但 self.config = config 直接保存引用。如果两个实例收到同一个 config 对象，它们的 config 仍可能指向同一对象。实例独立不等于所有输入数据都被深拷贝。

现在可以接回前面读过的队列函数：它使用的 **_remaining_trial_configs 和 _trial_queue 就是在这次初始化中准备好的**。这里登记的是 Job 自身的状态处理；Dressage 插件的回调由后面的 plugin.on_job_start(job) 另外登记。

| 到达哪一行 | 按需进入哪里 | 读完回来做什么 |
| --- | --- | --- |
| self._init_trial_configs() | [当前函数卡](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline)，需要时再进入下游 JobPlan | 配置列表写入 self._trial_configs，回到 __init__ 继续记录与队列准备 |
| self._init_remaining_trial_configs() | [源码:395–425](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L395) | 当前只确认生成待运行列表；恢复记录的比较细节暂缓 |
| __init__ 正常结束 | [回到 Job.create](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job.create.md#job-create-mainline) | cls(...) 得到此实例；后续可选通知完成后，由 create 返回 job 给 _run_partition |

本次先把初始化主干接清；下一处先读 [Job._init_trial_configs](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job._init_trial_configs.md#init-trial-configs-mainline)，再按实际调用进入下游配置组装，不为每个日志和记录方法另开一张卡。

## 我的直接表述（原话）

> 好的 那么请考虑构建一下这个job init的short term memory吧

本轮复述与问题：

> 好的
> 也就是这里更多的是
> 当前的通过config传经来的都保存下来
> 然后每一次都是通过这个config来初始化
> 同时记录这个job的记录目录和日志
> 准备一下可能的结果和任务缓存和进度?
> 确定生于工作的方法
> 创建执行的对象?
> 以及在trial中加入非常多的hookk
>
> 感觉都是初始化的内容
> 以及我想问的是写一个cls就是每一个class不需要构建instace就可以直接调用这个方法
> 并且这里的这个cls产生的instance是独立的吗?
> 不是class共享的吧

助手校准：初始化主线基本接清；这里先向 TrialQueue 登记 Job 的三个状态回调，创建具体 Trial 时才挂过去。无需预先创建实例就能调用当前 create，原因是 @classmethod，而不是参数恰好叫 cls。cls(...) 构造新 Job 实例，传入的配置引用则可能共享。后者仍待用户反馈。

后续确认与接续问题：

> 好的 能供通过类直接使用是因为@classmethod
> 然后这里的cls 使用来创建一个新的实例的
> 好的
> 那么我们下一个需要看的是什么呢?

助手补充：cls 指向类，cls(...) 执行实例构造。下一处从本函数的 self._init_trial_configs() 进入，普通分支经 _build_standard_trial_configs 委派到已有的 JobPlan.build_trial_configs 卡；这两处转交先连起来定位，不自动新增两张包装函数卡。

## 尚不清楚

- 每份 TrialConfig 的具体内容与原始任务来源怎样对应，沿已有配置组装卡继续。
- 旧作业恢复、日志、进度记录和并发回调内部，本轮暂缓。
- Job 自身的回调与插件回调怎样共同影响状态，只认登记归属，尚未完整验证。

<details>
<summary>完整函数与源码依据</summary>

以下为 v0.25.0 原函数。源码要求通过 Job.create 准备必需材料；__init__ 开头的弃用说明不表示创建过程中不会执行它。

```python
def __init__(
    self,
    config: JobConfig,
    *,
    _task_configs: list[TaskConfig] | None = None,
    _metrics: dict[str, list[BaseMetric[Any]]] | None = None,
    _task_download_results: dict[TaskIdType, TaskDownloadResult] | None = None,
    _source_job_dirs: list[Path] | None = None,
):
    """Deprecated. Use ``await Job.create(config)`` instead."""
    if _task_configs is None or _metrics is None or _task_download_results is None:
        raise ValueError(
            "Instantiating Job directly is deprecated. "
            "Use `await Job.create(config)` instead."
        )

    self.config = config
    self._source_job_dirs = _source_job_dirs
    self._existing_job_result = (
        JobResult.model_validate_json(self._job_result_path.read_text())
        if self._job_result_path.exists()
        else None
    )
    self.is_resuming = self._existing_job_result is not None

    self._trial_completion_lock = asyncio.Lock()

    self._id = (
        uuid4()
        if self._existing_job_result is None
        else self._existing_job_result.id
    )

    self._task_configs = _task_configs
    self._task_download_results = _task_download_results
    self._metrics = _metrics
    # Derive trial configs before touching the filesystem so a derivation
    # failure (e.g. an unregradable source job) leaves no empty job_dir.
    self._hub_source_trial_dirs: dict[UUID, Path] = {}
    self._init_trial_configs()
    if config.source_jobs:
        inference_agents: list[AgentConfig] = []
        for trial in self._trial_configs:
            if not trial.is_regrade and trial.agent not in inference_agents:
                inference_agents.append(trial.agent)
        self._preflight_agents(config, inference_agents)
    if self.config.is_regrade:
        self._ensure_regrade_metrics()

    self.job_dir.mkdir(parents=True, exist_ok=True)
    self._job_lock: JobLock | None = None
    self._log_file_handler: logging.Handler | None = None
    self._console_handler: logging.Handler | None = None
    self._init_logger()

    self._maybe_init_existing_job()
    self._seed_hub_source_trial_caches()
    self._init_progress_tracking()

    self._init_remaining_trial_configs()
    self._live_rewards = self._existing_rewards.copy()

    self._trial_queue = TrialQueue(
        n_concurrent=self.config.n_concurrent_trials,
        retry_config=self.config.retry,
    )
    self._trial_queue.add_hook(TrialEvent.START, self._on_trial_started)
    self._trial_queue.add_hook(TrialEvent.CANCEL, self._on_trial_cancelled)
    self._trial_queue.add_hook(TrialEvent.END, self._on_trial_completed)
```

- 创建调用：[Job.create:209–215](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L209)；普通配置选择：[448–462](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L448)；已有结果初始化：[290 起](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L290)；待运行列表：[395–425](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L395)。
- 另用独立教学缩减例验证 classmethod + cls(config) + self.config = config：两次构造的实例身份不同，同一个输入 config 的身份相同。输出为 same_instance: False、same_config: True；该实验未导入或执行 Harbor。
- 通过本地 git show v0.25.0 静态核对；未执行 Job 构造、文件创建、下载、模型或集群任务。
- [本次形成过程](../../../../../step-012-task-agent-verifier/04-flow.md#job-init-reading)。

</details>
