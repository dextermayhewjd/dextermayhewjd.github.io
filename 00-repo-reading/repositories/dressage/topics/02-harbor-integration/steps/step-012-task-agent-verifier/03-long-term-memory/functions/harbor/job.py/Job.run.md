# Job.run（Harbor）

本步继承：[Step 011 来源记录](../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job.run.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

- 源码：[src/harbor/job.py:1082–1227](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1082)，Harbor v0.25.0 发布版。
- 首次单独建卡：Step 011，2026-11-11；此前已定位上层交接。
- 最近认识更新：2026-11-11，用户复述初始化、队列执行、结果合并与指标汇总的主线；队列接收对象与合并对象由助手补充校准。

[调用方 _run_partition](../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#partition-mainline) → **Job.run** → [_run_trials_with_queue 源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1229) · [本步导航](../../../../../step-011-harbor-trial-lifecycle/01-scope.md#current-reading)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Job 已经创建，任务和 Trial 计划已准备，现在需要执行待运行的尝试，并取得整份 Job 的结果。
2. **具体内容**：建立 JobResult，等待队列执行 Trial，再汇总各次尝试的结果、奖励相关统计和结束状态，返回 JobResult。
3. **建议构建的心智模型**：

   > 把这份 Job 中待运行的尝试交出去，等结果收回来，再整理成整份 Job 的结果。

   具体 Agent 的启动、工具执行与评测在下游 Trial 中；本函数负责组织与汇总。

4. **调用代码**：来自已读 Dressage `_run_partition:760–762`，用于恢复调用背景。

   ```python
   await plugin.on_job_start(job)    # 调用前：插件挂接路由与事件。
   result = await job.run()          # 当前进入：执行 Job 并接住 JobResult。
   await plugin.on_job_end(result)   # 返回后：把结果交给插件收尾。
   ```

   Dressage 仍锁定 Harbor 0.18；本卡直接阅读 Harbor 0.25，以上调用背景不代表跨版本运行已验证。

## 本场景的输入与输出

<a id="job-mainline"></a>
<a id="caller-context"></a>

### 从调用方带进来的上下文

我们停在 `_run_partition` 的 `result = await job.run()`。这里的 job 是根据当前 partition 的临时配置创建的执行对象；不是一条题目，也不是一个 Sample。

**带着一个问题进入：已经准备好一份 Job，它怎样把待运行的 Trial 执行完，再交回一份结果？**

- **输入**：通过 self 使用已经保存的配置与 Trial 计划；`run()` 没有额外业务实参。`self._remaining_trial_configs` 表示尚待运行的尝试，`self._existing_trial_results` 保存已有结果；首次运行通常没有已有结果。
- **输出**：正常返回 `JobResult`，其中有 `trial_results`、`stats` 和时间等状态。调用方以 `result` 接住，再调用 `plugin.on_job_end(result)`；后续才继续结果匹配和 Sample 转换。
- **副作用**：写配置、运行状态和结果文件，组织 Trial 执行。返回了结果不意味着所有题都答对。

下面按真实源码顺序分三段。代码为教学裁剪，省略 UI、配置落盘细节、遥测、异常和具体指标算法；`...` 表示省略，不能独立运行。

### 1. 建立整份 Job 的结果记录（1085–1109 行）

```python
# 准备汇总容器，记录 Job 身份、时间、尝试总数和初始统计。
self._job_result = JobResult(
    id=self._id,
    started_at=started_at,
    updated_at=started_at,
    n_total_trials=len(self._trial_configs),
    stats=JobStats.from_trial_results(...),
)
# 中间还有配置与运行状态写入，此处省略。
self._write_job_result(exclude_trial_results=True)
```

此时建立的是结果记录，还没有通过本函数下面的队列调用执行剩余 Trial。已有结果会参与初始统计；本轮不展开恢复运行。

<a id="queue-handoff"></a>

### 2. 交给队列运行，等待各个 Trial 的结果（1114–1163 行）

```python
# 进度展示准备省略；quiet 与非 quiet 两条分支都调用这个方法。
trial_results = await self._run_trials_with_queue(...)
```

这一步是本函数的核心交接：下游使用待运行的 Trial 配置提交工作，等待完成后返回 `list[TrialResult]`。这里拿到的是尝试结果列表，还不是最终的 JobResult。

| 按需查看真实子函数 | 具体看什么 | 返回本函数的位置 |
| --- | --- | --- |
| [_run_trials_with_queue 函数卡](../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md#queue-mainline) | 找到 submit_batch、等待任务和结果列表；事件 UI 暂不展开 | `trial_results` 接住列表，继续 1165 行合并结果 |

本次已展开 [_run_trials_with_queue](../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md#queue-mainline)，更深的队列包装仍只定位。读清队列交接后，再沿 [scope](../../../../../step-011-harbor-trial-lifecycle/01-scope.md#reading-sequence) 进入 Trial.run，不能把它画成 Job.run 的直接调用。

### 3. 汇总结果，返回调用方（1165–1216 行）

```python
# 合并已有结果和本次取得的结果；首次运行通常只有后者。
combined_trial_results = self._existing_trial_results + trial_results

# 中间按 Agent、模型与数据集组织奖励，并计算统计和指标；算法暂略。
final_stats = JobStats.from_trial_results(...)
# 此处还会补入各项 metrics 与 pass_at_k，省略具体循环。

# 把明细与统计装回整份 Job 的结果。
self._job_result.stats = final_stats
self._job_result.trial_results = combined_trial_results
finished_at = datetime.now()
self._job_result.finished_at = finished_at
self._refresh_job_progress(updated_at=finished_at)
self._write_job_result(exclude_trial_results=True)

# 遥测省略；离开函数时还会通过 finally 关闭日志处理器。
return self._job_result
```

`exclude_trial_results=True` 作用于这里写出的结果文件，不表示返回对象没有明细：上面已经把 `combined_trial_results` 赋给返回对象的 `trial_results`。

读到这里返回 [_run_partition](../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#collect-outcomes)：先完成 `plugin.on_job_end(result)`，再进入已有的结果整理。**Job.run 本身不负责把结果变成 Slime Sample。**

## 我的直接表述（原话）

> 我可以简单理解为这里首先写了一下这里的这个job result应该是怎样的
> 简单初始化一下
> 然后再把这个job交给这里这个queue是我的理解
> 然后通过run trial with queue拿到最后的结果
> 最后把这个当前的结果和这一次trrial的结合过合并
> 甲酸指标
> 把这个指标返还给这里的result
> 鸡蛋来说就是这个层次

助手校准：队列接收的是 Job 中待运行的 TrialConfig，不是整个 Job；合并的是已有 TrialResult 列表与本次取得的 TrialResult 列表，不是将初始化的 JobResult 与单条 Trial 合并。统计写入 JobResult.stats，结果明细写入 JobResult.trial_results，最终返回整个 JobResult。上述校准尚待用户反馈。

## 尚不清楚

- 队列怎样根据 TrialConfig 创建并执行具体 Trial，尚未逐段阅读。
- 各个 Trial 在执行过程中怎样更新 Job 的状态与回调，后续按需要回查。
- 恢复、重试、取消和统计算法暂不深入；本卡不证明 Dressage 与 Harbor 0.25 的运行兼容性。

<details>
<summary>来源、验证与完整源码</summary>

- Harbor v0.25.0，提交 fdba28fc411e47e8765420a1a063b4918fce3def；2026-11-11 使用本地 git show 读取发布标签，未切换 main。[完整 Job.run](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1082)。
- `_run_trials_with_queue:1309–1314` 提交 `self._remaining_trial_configs`，通过 TaskGroup 等待并返回结果；仅作为本卡交接依据，内部未新建函数记忆。
- Dressage 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，rollout.py:760–762 为插件与 Job 的调用位置。
- 仅静态源码核对，没有执行 Job、模型、Kubernetes 或训练实验。
- [本步形成过程](../../../../../step-011-harbor-trial-lifecycle/04-flow.md#job-run-card-025)。

</details>
