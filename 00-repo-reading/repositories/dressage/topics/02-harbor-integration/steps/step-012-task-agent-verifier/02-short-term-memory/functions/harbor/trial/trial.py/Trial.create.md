# Trial.create

- 源码：[src/harbor/trial/trial.py:469–524](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L469)，Harbor v0.25.0 发布提交 fdba28fc411e47e8765420a1a063b4918fce3def。
- 首次单独展开：Step 012，2026-11-12。
- 本轮范围：沿 hello-world 普通任务，source_trial=None、user_agent=None；先看题目取得、具体类型选择与返回，不展开下载器。

[队列创建 Trial 的位置](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L201) → **Trial.create** → [题目加载](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L532) / [SingleStepTrial.__init__](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L20) · [scope](../../../../../01-scope.md#current-reading)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Job 已安排某份 TrialConfig 运行，队列需要先得到这一次尝试的 Trial 对象，再挂回调并调用 run。
2. **具体内容**：按配置取得题目，检查配置组合；选择单步、多步或重评实现，构造对象并返回。
3. **建议构建的心智模型**：

   > 根据一份尝试配置找到题目，再创建适合这份题目的 Trial 对象，交回队列运行。

4. **调用代码**（TrialQueue._execute_trial_with_retries:201–203）：

   ```python
   trial = await Trial.create(trial_config)  # 当前：传入一份尝试配置，等待对象创建。
   self._setup_hooks(trial)                 # 返回后，才向这个 Trial 挂接回调。
   result = await trial.run()               # 然后进入 Step 011 已读的生命周期。
   ```

## 本场景的输入与输出

<a id="job-to-trial-create"></a>

### 从 Job.create 怎样来到这里？

先回到 [Step 010 的 _run_partition](../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_partition.md#run-job)。下面是同一个函数内的先后位置，省略模板绑定和插件构造代码：

```python
job = await _CREATE_JOB(job_config)  # Job.create 返回：已拿到 Job，配置也已准备。
# 中间绑定模板并创建 plugin，省略。
await plugin.on_job_start(job)
result = await job.run()            # 运行期间，由队列逐次创建 Trial。
await plugin.on_job_end(result)
```

`Job.create` 返回后，程序回到调用方，直到上面的 [job.run()](../../../../../../step-011-harbor-trial-lifecycle/02-short-term-memory/functions/harbor/job.py/Job.run.md#job-mainline) 才进入队列执行。`Job.run → _run_trials_with_queue` 创建 Task，Task 运行 `TrialQueue._run_trial → _execute_trial_with_retries`，最后到上方的 `await Trial.create(trial_config)`。

**因此 Job.create 没有直接调用 Trial.create。** 前者准备整份 Job，后者在这份 Job 的运行期间按一份配置创建一次尝试；我们现在下钻的是 `await job.run()` 内部。

### 接住上一部分的那份 TrialConfig

沿用前面的静态例子：config.task.path 指向 examples/tasks/hello-world，config.agent 指定 Claude Code，config.environment 指定 Docker。配置里保存的是任务来源；本函数需要先据此取得 Task 对象及任务材料信息。

**正常返回一个具体 Trial 子类的实例，本例是 SingleStepTrial。** 它已经初始化，持有本次 config、读取出的 task、自己的尝试身份及 Agent/Environment 对象；这不表示已经启动运行环境或执行题目。结果 TrialResult 是后面 trial.run 才交出的。

<a id="trial-create-mainline"></a>

### 从配置到 Trial：说明直接跟着代码读

以下为普通路径节选，保留类方法签名与单步/多步选择；省略配置警告和 source_trial 非空的重评分支。cls 在本次 Trial.create 调用中指向 Trial 类。

```python
@classmethod
async def create(cls, config: TrialConfig) -> "Trial":
    # 本轮 source_trial=None：解析配置里的 skills 来源，不在此安装 Agent。
    cls._resolve_agent_skills(config)

    # 按 config.task 的来源取得材料，并读取为 Task 对象。
    task, task_download_result = await cls._load_task(config)
    # 原代码在这里检查配置组合并记录警告；重评分支也在此处，本轮省略。

    if task.has_steps:  # task.toml 的 steps 非空，使用多步 Trial。
        from harbor.trial.multi_step import MultiStepTrial

        trial = MultiStepTrial(
            config,
            _task=task,
            _task_download_result=task_download_result,
        )
    else:               # hello-world 没有多步定义，本轮走这里。
        from harbor.trial.single_step import SingleStepTrial

        trial = SingleStepTrial(
            config,     # 原来的尝试配置：Agent、环境、评测等运行安排。
            _task=task,  # 刚刚读取的题目对象。
            _task_download_result=task_download_result,
        )               # 构造时进入 SingleStepTrial.__init__，再到 Trial.__init__。

    await trial._create_bridge()  # 本轮 user_agent=None，内部直接返回。
    return trial                  # 交回队列，再挂 hooks、执行 trial.run。
```

这里根据题目的工作步骤选择 Trial 类型，**不是根据 Claude/Codex 选择类型，也不是按尝试次数选择类型**。Agent 的具体对象由构造器内部根据 config.agent 初始化。

实际判断是 `bool(task.config.steps)`：显式定义了非空 steps 就走 MultiStepTrial；并不要求步骤数量大于 1，也不按模型调用次数划分。普通 SingleStepTrial 的 Agent 仍可以多轮调用模型和工具。

**_create_bridge 本轮不用下钻。** user_agent 是可选的“模拟用户 Agent”：通过 bridge 与执行题目的主 Agent 交互，不是指正在使用系统的人，也不是 config.agent 的另一个名字。

```python
# 我们的 hello-world 示例只配置了主 Agent，没有配置模拟用户。
# JobConfig.user_agent 默认为 None，并传入 TrialConfig.user_agent。
if self.config.user_agent is None:
    return  # 不需要模拟用户与主 Agent 之间的 bridge。
```

Bridge 的职责是连接模拟用户 Agent 与目标 Agent；当前普通任务直接把 instruction 交给主 Agent，不启用该交互模式。此处的 None 表示功能未配置，不表示主 Agent 不存在或安装失败。

| 当前读到哪里 | 下一层入口 | 返回后继续哪里 |
| --- | --- | --- |
| task, task_download_result = await cls._load_task(config) | [_load_task:532](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L532) → [Task.__init__:51](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/task/task.py#L51) | 回到当前函数，才能根据 task.has_steps 选择实现 |
| trial = SingleStepTrial(...) | [SingleStepTrial.__init__:20](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L20) → [Trial.__init__:164](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L164) | 初始化完成后回到当前赋值处，再经过 _create_bridge 和 return trial |
| return trial | [队列:201–203](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/queue.py#L201) | 接住对象、挂回调，再调用已有的 Trial.run |

本轮先接清这条创建路径。需要知道题目文件怎样变成 Task 时，下一处看 _load_task；不在本卡提前展开 Agent 初始化或环境启动。

## 我的直接表述（原话）

> 好的 我大概理解了
> 那么我们来看一下这个trial是如何根据这个config来生成的吧

随后用户要求优先使用本地 Harbor 0.25 源码，无需联网。

本轮复述与问题：

> 那么这里你会选择怎么拆分呢?
> 一般来说就是按照 harbor的这个格式来定义吗?
> 也就是定义工作步骤和使用多个步骤的trial
> 如果不是那么就走single的部分
> 简单来说这里就是配置agent和对应的题目的是我的理解
> 那么这里还有别的内容吗?
> 这里的create bridge我需要考虑吗?

助手校准：依据任务文件中的非空 steps 选择 Trial 实现，而不是模型对话轮数；这里读取题目并把已有配置交给具体 Trial 构造器。当前无 user_agent，_create_bridge 直接返回，暂不展开。该精确边界尚待用户反馈。

补充疑问：

> 也就是这里的这个bridge我可以理解为 是用来建立和逼得agent的联系的?
> 还是什么为什么user agent 这里填写的部分是none?

助手根据 BaseBridge 与 UserAgentConfig 定义区分主 Agent 和可选模拟用户 Agent，并说明本例未配置 user_agent，默认 None 经 JobPlan 传给 TrialConfig；不把它解释为主 Agent 缺失。

本轮调用背景卡点：

> 我们之前看的都是job cretate对吧
> 在哪里到的trial create 我没有连上

助手补齐创建返回调用方、随后 await job.run、队列 Task 内部创建 Trial 的时机；保留已读事实，不把来路不清楚解释为需要重读全部函数。

## 尚不清楚

- _load_task 怎样根据来源取得目录并读入 instruction/task.toml，后续再进入。
- SingleStepTrial 与基类初始化怎样创建 Agent/Environment 对象，沿 scope 后续位置继续。
- 多步、重评和 user-agent bridge 的实现，本轮不展开。

<details>
<summary>完整源码与本地验证依据</summary>

本轮从 /home/fredkeira/projects/harbor 用 git show v0.25.0:src/harbor/trial/trial.py 读取，未联网、切换 checkout、运行任务或下载材料。文中的 GitHub 固定提交链接仅作为源码定位。

```python
@classmethod
async def create(cls, config: TrialConfig) -> "Trial":
    if config.source_trial is None:
        # Regrades carry the source trial's already-resolved agent config
        # verbatim; the agent is never re-run, so don't re-resolve skills.
        cls._resolve_agent_skills(config)
    task, task_download_result = await cls._load_task(config)
    for warning in check_trial_config(
        task.config, config.environment, config.verifier
    ):
        global_logger.warning("Task %s: %s", task.name, warning)
    if config.source_trial is not None:
        # TODO: one example could be harbor analyze
        if config.source_trial.action != "regrade":
            raise NotImplementedError(
                f"source_trial action '{config.source_trial.action}' "
                "is not implemented."
            )
        from harbor.trial.regrade import (
            MultiStepRegradeTrial,
            RegradeTrial,
            resolve_source_trial_dir,
        )

        source_trial_dir = await resolve_source_trial_dir(
            source_trial_path=config.source_trial.path,
            source_trial_id=config.source_trial.trial_id,
            trials_dir=config.trials_dir,
        )
        regrade_trial_cls = (
            MultiStepRegradeTrial if task.has_steps else RegradeTrial
        )
        return regrade_trial_cls(
            config,
            _task=task,
            _task_download_result=task_download_result,
            _source_trial_dir=source_trial_dir,
        )

    if task.has_steps:
        from harbor.trial.multi_step import MultiStepTrial

        trial = MultiStepTrial(
            config,
            _task=task,
            _task_download_result=task_download_result,
        )
    else:
        from harbor.trial.single_step import SingleStepTrial

        trial = SingleStepTrial(
            config,
            _task=task,
            _task_download_result=task_download_result,
        )
    await trial._create_bridge()
    return trial
```

BaseBridge 的职责见固定版 src/harbor/bridges/base.py；TrialConfig.user_agent 默认为 None，说明为 optional simulated-user agent；JobPlan.build_trial_configs 直接传递 config.user_agent。相关源码均从本地 git 对象读取。

本地 main HEAD 为 500af91374dcc43b59fac54cf90295646617b14d，比 v0.25.0 发布提交多 123 个提交；虽 pyproject 都写 0.25.0，正文仍按发布标签核对，不混用行号。

[形成过程](../../../../../../step-012-task-agent-verifier/04-flow.md#trial-create-reading)。

</details>
