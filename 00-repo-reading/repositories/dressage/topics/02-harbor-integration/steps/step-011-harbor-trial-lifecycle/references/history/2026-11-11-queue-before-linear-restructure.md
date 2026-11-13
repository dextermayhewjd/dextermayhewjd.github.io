# Job._run_trials_with_queue

- 源码：[src/harbor/job.py:1229–1314](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1229)，Harbor v0.25.0。
- 首次单独展开：Step 011，2026-11-11。
- 当前范围：待运行配置 → 协程 → Task → TrialResult 列表；进度显示与队列重试内部暂不展开。

[Job.run 第二段](../../02-short-term-memory/functions/harbor/job.py/Job.run.md#queue-handoff) → **Job._run_trials_with_queue** → [TrialQueue 源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L253) · [本步导航](../../01-scope.md#current-reading)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Job.run 已建立整份 Job 的结果记录，现在需要执行尚未完成的 Trial，并等待它们的结果。
2. **具体内容**：先注册进度回调，再由队列根据配置返回协程；用 TaskGroup 创建任务并等待完成，最后按列表顺序收集各个结果。
3. **建议构建的心智模型**：

   > 取出待运行的尝试配置，安排执行，等这一批完成，再交回结果列表。

4. **调用代码**（Job.run:1137 或 1161，两种进度显示分支）：

   ```python
   trial_results = await self._run_trials_with_queue(...)
   # 回到 Job.run:1165，合并已有结果与本次结果。
   combined_trial_results = self._existing_trial_results + trial_results
   ```

## 本场景的输入与输出

### 从 Job.run 带进来的上下文

整份 Job 的结果记录已经初始化。待运行的配置在 `self._remaining_trial_configs`，队列对象在 `self._trial_queue`；调用参数 `loading_progress`、`loading_progress_task`、`running_progress` 用于进度展示，不是待运行题目本身。

本次要交回的是 `list[TrialResult]`。Job.run 接住后才进行整份 Job 的合并与统计；这里不生成 Sample，也不返回 JobResult。

<a id="queue-mainline"></a>

### 当前只看执行主干（1309–1314 行）

下面保留连续真实代码，只添加阶段注释。前面的进度回调注册暂略；本段按正常完成路径阅读。

```python
# 1. 把待运行配置交给队列，取得各个尝试对应的协程。
coros = self._trial_queue.submit_batch(self._remaining_trial_configs)

# 2. 将协程创建为 Task；离开 async with 前，等待组内任务完成。
async with asyncio.TaskGroup() as tg:
    tasks = [tg.create_task(coro) for coro in coros]

# 3. 此时任务已经完成，依次读取结果并返回。
return [t.result() for t in tasks]
```

- **submit_batch 返回协程，不在这里直接得到运行结果。** 队列内部依次调用 submit，返回 `_run_trial(...)` 的协程；实际由这里的 `tg.create_task(coro)` 安排运行。
- **等待发生在退出 TaskGroup 时。** 循环负责创建 Task；正常退出 async with 后，才能走到读取结果的语句。实际并发还受队列内部限流约束，创建多个 Task 不意味着所有沙箱同时开始运行。
- **t.result() 在这里取已有结果，不负责等待。** 返回列表按 tasks 的顺序，因此保持提交配置顺序，不是按任务完成先后排列。

静态示意：若有 A、B 两份配置，B 先完成、A 后完成，函数仍等两者都完成，再返回 `[A 的结果, B 的结果]`。这不表示两份尝试一定答对；结果中也可能记录执行异常。

<a id="queue-to-trial"></a>

### 队列与 Trial.run 之间的连接

**Job 已经存在。下面沿同一次调用，看它怎样取得协程、安排运行，再取回 TrialResult。** 骨架中的 [1]、[2]、[3] 与下方说明一一对应；子分支表示对应阶段内部的工作。

```text
_run_trials_with_queue
│
├─ [1] 取得待执行的协程
│    └─ submit_batch
│         └─ submit
│              └─ 返回 _run_trial(...) 的协程
│
├─ [2] 用 TaskGroup 创建 Task，并等待完成
│    └─ 每个 Task 运行 _run_trial
│         ├─ 等待并发额度
│         └─ _execute_trial_with_retries
│              ├─ Trial.create：创建一次尝试
│              ├─ _setup_hooks：挂接回调
│              └─ Trial.run：执行这次尝试
│
└─ [3] 读取各个 Task 的结果，返回列表
```

**[1] 取得协程，[2] 才安排它运行。** _run_trial 在图中出现两次，分别对应“创建协程”和“执行协程体”；Trial.create/run 属于 [2] 内部，不是 [3] 返回后的新一步。

#### 对照本函数：三个阶段各在哪一行？

job.py:1309–1314，完整保留执行段：

```python
# [1] 取得协程。
coros = self._trial_queue.submit_batch(self._remaining_trial_configs)

# [2] 安排运行，并在退出 TaskGroup 前等待完成。
async with asyncio.TaskGroup() as tg:
    tasks = [tg.create_task(coro) for coro in coros]

# [3] 取回结果列表。
return [t.result() for t in tasks]
```

先追第一行的 coros 从哪里来，再追 create_task 安排运行的代码；最后回到这里取结果。不是把下面的函数定义插在这几行之间执行。

<a id="queue-stage-1"></a>

#### [1] 取得协程：submit_batch 返回什么？

queue.py:244–260，按调用顺序列出两个方法；仅省略类型标注和文档，保留实际检查与返回。这里 self 是 TrialQueue 对象。

```python
def submit_batch(self, configs):
    self._validate_agent_concurrency(configs)
    return [self.submit(config) for config in configs]

def submit(self, trial_config):
    self._validate_agent_concurrency([trial_config])
    return self._run_trial(trial_config)
```

**关键是最后一行。** _run_trial 是 async 方法，这里调用它得到协程对象，尚未执行其函数体。每份配置得到一个协程，组成 coros，返回本函数的 [1]；随后在 [2] 由 tg.create_task(coro) 安排这些协程运行。

<a id="queue-stage-2"></a>

#### [2] 运行并等待：Task 怎样进入 Trial.run？

queue.py:239–242 和 194–206，按调用顺序节选。_run_trial 保留完整执行体；_execute_trial_with_retries 只展示到无异常记录时的返回，后续失败判断、重试与最终抛错不在此展开。

```python
async def _run_trial(self, trial_config):
    # 拿到并发额度后，才继续运行这个尝试。
    async with self._semaphore:
        return await self._execute_trial_with_retries(trial_config)

async def _execute_trial_with_retries(self, trial_config):
    from harbor.trial.trial import Trial

    for attempt in range(self._retry_config.max_retries + 1):
        trial = await Trial.create(trial_config)  # 这里才创建 Trial。
        self._setup_hooks(trial)
        result = await trial.run()               # 下一处阅读的位置。

        if result.exception_info is None:
            return result
        # 以下失败与重试分支未展示。
```

这就是之前省略的中间交接：**Task 运行 _run_trial，_run_trial 等待 _execute_trial_with_retries，后者创建 Trial 并等待 Trial.run。**

<a id="queue-stage-3"></a>

#### [3] 收集结果：沿原路返回

正常路径中，Trial.run 的 TrialResult 经 _execute_trial_with_retries、_run_trial 返回，成为该 Task 的结果。[2] 的 TaskGroup 等所有 Task 完成后，才走到 [3] 的 `[t.result() for t in tasks]`，把结果列表交回 Job.run。

**因此，Trial 的创建和执行发生在当前函数等待 TaskGroup 的期间，不是当前函数返回后才开始。** 本节补齐真实委派，不要求现在读完并发检查和重试策略，也不另建这些辅助函数的卡片。

| 接续位置 | 当前看多深、回来做什么 |
| --- | --- |
| [Job.run:1165](../../02-short-term-memory/functions/harbor/job.py/Job.run.md#job-mainline) | 本函数返回后，trial_results 参与合并和统计；父函数这段已读 |
| [Trial.run 函数卡](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#normal-lifecycle) | 下一处阅读候选：顺着队列进入一次尝试的准备、执行和收尾 |

<details>
<summary>前半段与失败边界：本轮只保留职责</summary>

1229–1307 行主要注册用于显示的生命周期回调：运行进度存在时更新各阶段显示，否则注册结束回调来推进总进度。advanced_trials 等集合避免重复推进。这里只认清职责，不逐个阅读 UI 回调。

TaskGroup 正常退出后的取结果路径不涵盖所有失败情况：如果异常从子任务中传播出来，TaskGroup 会处理取消与异常传播，函数不保证总能返回完整列表。TrialResult 中记录了异常，与 Task 本身向外抛出异常，是两个不同层面的情况；失败治理后续再展开。

</details>

## 我的直接表述（原话）

用户确认继续阅读本函数，尚无对其内部机制的独立复述。此前关于 Job.run 的理解保留在父函数卡，不作为本函数已理解的依据。

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

## 尚不清楚

- 队列怎样创建具体 Trial、控制并发与决定重试，当前只定位。
- Trial.run 怎样准备环境、执行 Agent、收集评测与回收，接下来按主线阅读。
- 进度回调去重、TaskGroup 的异常传播细节，本轮暂不展开。

<details>
<summary>来源与验证</summary>

- 固定提交 fdba28fc411e47e8765420a1a063b4918fce3def；2026-11-11 从本地 git show v0.25.0 核对 job.py:1229–1314 与 trial/queue.py:194–260。
- [完整本函数](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1229)；[队列提交](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L244)；[实际 trial.run 调用](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L201)。
- 仅静态源码阅读，未运行 Job、模型或集群。静态例子不是运行结果。
- [本步讨论](../../04-flow.md#queue-function-reading)。

</details>
