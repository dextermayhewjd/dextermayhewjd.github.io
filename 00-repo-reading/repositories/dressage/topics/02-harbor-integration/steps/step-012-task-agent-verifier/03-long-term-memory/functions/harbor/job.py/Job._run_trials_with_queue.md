# Job._run_trials_with_queue

本步继承：[Step 011 来源记录](../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job._run_trials_with_queue.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

- 源码：[src/harbor/job.py:1229–1314](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1229)，Harbor v0.25.0。
- 首次单独展开：Step 011，2026-11-11。
- 当前范围：待运行配置 → 协程 → Task → TrialResult 列表；进度显示与队列重试细节暂不展开。
- 本次结构调整：2026-11-11，按同一条主线合并重复内容；保留[调整前完整卡片](../../../../../step-011-harbor-trial-lifecycle/references/history/2026-11-11-queue-before-linear-restructure.md)。结构调整不代表已理解下游机制。

[Job.run 第二段](../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job.run.md#queue-handoff) → **Job._run_trials_with_queue** → [TrialQueue 源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L253) · [本步导航](../../../../../step-011-harbor-trial-lifecycle/01-scope.md#current-reading)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Job.run 已建立整份 Job 的结果记录，现在需要执行剩余的 Trial，并等待它们的结果。
2. **具体内容**：注册进度回调，取得每次尝试的执行协程，用 TaskGroup 安排运行并等待，最后按提交顺序返回结果列表。
3. **建议构建的心智模型**：

   > 取出待运行的尝试配置，安排执行，等这一批完成，再交回结果列表。

4. **调用代码**（Job.run:1161，参数齐全的显示分支）：

   ```python
   trial_results = await self._run_trials_with_queue(
       loading_progress, progress_task, running_progress
   )
   # 返回后才继续合并和统计。
   combined_trial_results = self._existing_trial_results + trial_results
   ```

## 本场景的输入与输出

### 调用前已有什么，返回后交出什么？

- **工作**：`self._remaining_trial_configs` 是待运行的 TrialConfig 列表；`self._trial_queue` 是组织执行的 TrialQueue 对象。二者在 Job 创建时已准备好，两处 self 都是当前 Job。
- **显示**：三个实参依次是总体进度对象、其中的进度条目编号、各个运行中 Trial 的进度对象。第二个在函数内叫 loading_progress_task，并非 asyncio.Task；quiet 分支不传第三个参数。
- **结果**：返回 `list[TrialResult]`，由 Job.run 的 trial_results 接住；填写整份 JobResult 和计算统计是返回后的工作。

<a id="queue-mainline"></a>
<a id="queue-to-trial"></a>

### 先看骨架，再按同一编号往下读

本轮保留正常执行路径，前面的显示回调只知道职责即可。图中 [2] 的子分支，是 Task 开始运行后发生的工作。

```text
_run_trials_with_queue
│
├─ [1] 取得待执行的协程 coros
│    └─ submit_batch → submit
│         └─ 返回 _run_trial(...) 的协程
│
├─ [2] 创建 Task，并由 TaskGroup 等待完成
│    └─ 每个 Task 运行 _run_trial
│         ├─ 等待并发额度
│         └─ _execute_trial_with_retries
│              ├─ Trial.create：创建一次尝试
│              ├─ _setup_hooks：挂接回调
│              └─ Trial.run：执行并返回 TrialResult
│
└─ [3] 读取各个 Task 的结果，交回 Job.run
```

**[1] 取得协程，[2] 才安排执行它的函数体。** 所以 _run_trial 在图中有两个位置；Trial 的创建和运行都属于 [2]，发生在 [3] 返回之前。

<a id="queue-stage-1"></a>

### [1] 提交配置，取得协程（job.py:1309）

```python
coros = self._trial_queue.submit_batch(self._remaining_trial_configs)
```

**TrialQueue 的名称怎么理解？** 它是 Harbor 自定义的执行组织对象，不是 asyncio.Queue 那种通过 put/get 存取任务的容器。这里 submit_batch 根据配置返回协程，由外面的 TaskGroup 安排运行；内部用 Semaphore 控制并发，并处理 Trial 创建、回调挂接与重试。可以先把它理解为“Trial 的执行管理器”。

**每份待运行的 TrialConfig 对应一个协程。** 这些协程组成 coros 列表，等待 [2] 安排运行；此时还没有在协程内部创建或运行 Trial。

#### [1] submit_batch / submit 怎样得到 coros？

queue.py:244–260，按调用顺序节选；只省略类型和文档。这里 self 是 TrialQueue。

```python
def submit_batch(self, configs):
    self._validate_agent_concurrency(configs)
    return [self.submit(config) for config in configs]

def submit(self, trial_config):
    self._validate_agent_concurrency([trial_config])
    return self._run_trial(trial_config)
```

_run_trial 是 async 方法，调用它先得到协程对象。每份配置对应一个协程，列表返回本函数的 coros；**读完回到 [2]，还没有进入 Trial.run。**


<a id="queue-stage-2"></a>

### [2] 运行协程，等待各次尝试完成（job.py:1311–1312）

```python
async with asyncio.TaskGroup() as tg:
    tasks = [tg.create_task(coro) for coro in coros]
```

**每个协程创建一个 Task 来运行；TaskGroup 等它们都完成，才正常退出这个 async with。** 各个 Task 可以先后结束，并不要求同时结束。例如 A 先完成、B 仍在运行，就继续等 B；正常退出后才能进入 [3]。

Task 运行队列代码，内部才创建 Trial 并调用 Trial.run；实际同时运行多少个 Trial，仍受队列并发额度限制。

**当前要找的 Trial.run 就在这一阶段内部。** 若只看本函数，可以继续 [3]；若想看一次尝试如何执行，从本阶段进入下方代码，再打开 Trial.run 卡。

#### [2] Task 内部怎样创建并运行 Trial？

queue.py:239–242 和 194–206，按调用顺序节选。只展示正常路径的返回，失败重试分支暂略；下面是两个独立方法，不是父函数中紧接着执行的语句。

```python
async def _run_trial(self, trial_config):
    async with self._semaphore:
        return await self._execute_trial_with_retries(trial_config)

async def _execute_trial_with_retries(self, trial_config):
    from harbor.trial.trial import Trial

    for attempt in range(self._retry_config.max_retries + 1):
        trial = await Trial.create(trial_config)
        self._setup_hooks(trial)
        result = await trial.run()

        if result.exception_info is None:
            return result
        # 后续失败判断、重试与最终抛错未展示。
```

在 `result = await trial.run()` 处进入 [Trial.run 函数卡](../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle)。返回的 TrialResult 沿 _execute_trial_with_retries → _run_trial 交回对应 Task；所有 Task 正常完成后，回到本函数 [3]。


<a id="queue-stage-3"></a>

### [3] 读取结果列表，返回 Job.run（job.py:1314）

```python
return [t.result() for t in tasks]
```

**对每个已完成的 Task 调用 t.result()，取得它返回的 TrialResult，再组成结果列表。** 等待已经在 [2] 完成，这里只取值。列表按 tasks 的顺序排列：A、B 两个尝试即使 B 先完成，也按 A、B 的提交顺序交回。

本函数结束，返回 [Job.run 的队列调用处](../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job.run.md#queue-handoff)，再执行 1165 行的结果合并。这时才回到整份 Job 的汇总；本函数不负责填写 JobResult 或转换 Sample。

<details>
<summary>暂缓阅读：进度回调与失败边界</summary>

1229–1307 行注册显示用回调，在 Trial 开始、阶段变化或结束时更新进度；advanced_trials 等集合避免重复推进。本轮先沿 1309–1314 的执行主干阅读。

TaskGroup 子任务若向外抛异常，会触发相应的取消与异常传播，函数不保证返回完整列表；上文按正常完成路径解释。TrialResult 内记录了失败，与 Task 向外抛异常，是不同层面的情况。

</details>

## 我的直接表述（原话）

首次建卡时尚无本函数的独立复述；随后发生的主干表述与追问按原话保留在下方。

最新主干表述：

> 算了当前还是切回到了一开始的某一种状态
> 我对于这个函数的一开始的一个状态吧
> 当前这里内容是向trialqueue提交当前还剩下的trial的configs
> 然后得到的这些tasks和对应的可能结果
>
> 是通过协程来解决的
>
> 好的 那么考虑一下下一步应该做什么或者这里还有什么需要看的吗?
> 是开始下一个函数了吗?

助手校准：submit_batch 先返回协程，由本函数创建 Task；正常完成后读取并返回 TrialResult 列表。当前以这条主干作为阅读停点，不要求继续展开显示参数和队列包装。下一处建议是已有 Trial.run 卡，尚不据推荐展开新的阅读或改动卡片结构。

补充追问：

> 但是这里这个run trials withh queue好像也没有立马就直接生成了当前的这个job?
> 我不是特别理解
> 是不是哪里跳过了

助手补充：已有 Job 与下游新建 Trial 要区分；省略的是队列协程执行到 Trial.create 的中间路径，不是遗漏了本函数内的 Job 创建。上述说明尚待用户确认。

本轮复述与反馈：

> 这里感觉每一个步骤其实没有说的特别清楚
> 感觉真的需要展开才能看到吗?
>
> 1. 然后就是这里的每一步
> 简单来说现在每一个任务提交一个协程
> 然后通过运行这里的taskgroup
> 能够确保这里的tasks是一并结束的?
> 最后就可以通过这个result来获取这里tasks的值是我的理解

助手校准：每份待运行配置对应一个协程，由 create_task 安排运行；TaskGroup 正常退出前等待所有 Task 完成，各个 Task 不必同时结束。之后 t.result() 取得各自的 TrialResult。每阶段的可见说明应足以理解这条主线，折叠代码仅解释内部如何实现。尚不将校准内容记为用户已确认。

## 尚不清楚

- 队列怎样创建具体 Trial、控制并发与决定重试，当前只定位。
- Trial.run 怎样准备环境、执行 Agent、收集评测与回收，接下来按主线阅读。
- 进度回调去重、TaskGroup 的异常传播细节，本轮暂不展开。

<details>
<summary>来源与验证</summary>

- 固定提交 fdba28fc411e47e8765420a1a063b4918fce3def；2026-11-11 从本地 git show v0.25.0 核对 job.py:1229–1314 与 trial/queue.py:194–260。
- [完整本函数](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1229)；[队列提交](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L244)；[实际 trial.run 调用](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L201)。
- 仅静态源码阅读，未运行 Job、模型或集群。静态例子不是运行结果。
- [本步讨论](../../../../../step-011-harbor-trial-lifecycle/04-flow.md#queue-function-reading)。

</details>
