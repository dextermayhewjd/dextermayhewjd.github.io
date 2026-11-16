# JobPlan.build_trial_configs

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../step-012-task-agent-verifier/02-short-term-memory/functions/harbor/job_plan.py/JobPlan.build_trial_configs.md) 完整继承；复制不改变原认识时间或已掌握状态。

- 源码：[src/harbor/job_plan.py:140–168](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job_plan.py#L140)，Harbor v0.25.0。
- 首次单独展开：Step 012，2026-11-12。
- 本轮范围：普通任务的 Trial 配置组成；不重新追踪 Job 创建与配置加载器。

[从 _build_standard_trial_configs 的 return 调用进入](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job._build_standard_trial_configs.md#standard-trial-configs-mainline) → **当前：JobPlan.build_trial_configs** → [读完先返回 _build_standard_trial_configs](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job._build_standard_trial_configs.md#standard-trial-configs-mainline) · [scope](../../../../../step-012-task-agent-verifier/01-scope.md#reading-sequence)

进入时已有 config、task_configs 和 job_id。这里组合并返回 list[TrialConfig]；上层先原样转交，再由 _init_trial_configs 写入 Job，不直接跳回运行阶段。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：创建普通 Job 时，已经知道要跑哪些任务、使用哪些 Agent，需要列出每一次尝试的运行配置。
2. **具体内容**：按尝试次数、任务、Agent 三层组合创建 TrialConfig，继承环境与评测等运行参数，返回配置列表。
3. **建议构建的心智模型**：

   > 把“哪些题、谁来做、各做几次”列成一份份尝试配置，交给后面的 Trial 执行。

4. **调用代码**（Job._build_standard_trial_configs:459–462）：

   ```python
   return JobPlan.build_trial_configs(
       self.config, self._task_configs, job_id=self._id
   )
   ```

## 本场景的输入与输出

<a id="caller-context"></a>

### 从上一张 _build_standard_trial_configs 卡接进来

Job.__init__ 已保存材料，_init_trial_configs 已选择普通分支；上一张卡现在执行下面的 return，将三项资料交给本函数。返回后仍按这两个调用层次交回：

```python
# 上一张 _build_standard_trial_configs 卡里的这一行，调用当前函数。
return JobPlan.build_trial_configs(
    self.config, self._task_configs, job_id=self._id
)
```

因此传进来的是 **整份运行配置、题目来源列表、Job ID**。返回的是 **list[TrialConfig]**；这次调用没有创建可执行的 Trial 对象，也没有开始做题。

<a id="trial-plan-mainline"></a>

### 组装主干：注释跟着代码读

JobPlan 内的原方法节选，省略目录、超时和额外指令等继承字段，保留签名与组合顺序。`@staticmethod` 表示调用时不自动传入 self 或 cls，这三个参数由调用方明确提供。

```python
@staticmethod
def build_trial_configs(
    config: JobConfig,
    task_configs: Sequence[TaskConfig],
    *,
    job_id: UUID,
) -> list[TrialConfig]:
    return [
        TrialConfig(
            task=task_config,                # 本次尝试做哪道题。
            agent=agent_config,              # 由哪个 Agent 做。
            environment=config.environment,  # 运行后端的配置。
            verifier=config.verifier,        # 运行时评测选项。
            job_id=job_id,                    # 属于哪份 Job。
            # 其他从 config 继承的字段省略。
        )
        for _ in range(config.n_attempts)    # 每种组合尝试几次。
        for task_config in task_configs      # 遍历题目来源。
        for agent_config in config.agents    # 遍历选择的 Agent 配置。
    ]
```

<a id="trial-config-example"></a>

### 静态例子：实际会组成什么样的 TrialConfig？

选用仓库的 hello-world 题目：要求创建 hello.txt，内容为 Hello, world!。下面是按真实模型字段构造的输入示意，省略 import；model_name 是示意值，不是本次实际调用的模型。没有执行 Harbor 或模型请求。

```python
# 题目来源列表：指向题目目录，不把 instruction 和测试脚本直接塞在这里。
task_configs = [TaskConfig(path=Path("examples/tasks/hello-world"))]

config = JobConfig(
    job_name="hello-demo",
    jobs_dir=Path("jobs"),
    n_attempts=1,                         # 本题与所选 Agent 的组合尝试一次。
    tasks=task_configs,
    agents=[AgentConfig(
        name="claude-code",
        model_name="anthropic/example-model",
    )],
    environment=EnvironmentConfig(type="docker"),
    verifier=VerifierConfig(disable=False), # 启用评测；判定规则仍在题目 tests/ 中。
)
job_id = UUID("00000000-0000-4000-8000-000000000001")

trial_configs = JobPlan.build_trial_configs(
    config, task_configs, job_id=job_id
)
```

**静态推导的返回值是一份长度为 1 的列表，里面是一项 TrialConfig 对象。** 为便于看字段，下方用 JSON 展示第一项的内容节选；实际返回的不是字典，未列出的字段沿用原模型默认值。

```json
{
  "trial_name": "hello-world__<随机7字符>",
  "task": {
    "path": "examples/tasks/hello-world"
  },
  "agent": {
    "name": "claude-code",
    "model_name": "anthropic/example-model"
  },
  "environment": {
    "type": "docker",
    "force_build": false,
    "delete": true
  },
  "verifier": {
    "disable": false
  },
  "trials_dir": "jobs/hello-demo",
  "install_only": false,
  "job_id": "00000000-0000-4000-8000-000000000001"
}
```

这一项的意思就是：**使用选定的 Claude Code 配置，在 Docker 后端准备这道题并启用评测；本次尝试归属于这个 Job，记录目录位于 jobs/hello-demo 下。** 它仍是执行安排，没有运行输出或奖励。

trial_name 的随机后缀由 TrialConfig 初始化时自动生成，上面只写占位符。若只把 n_attempts 改为 2，列表就会包含两项，任务/Agent 等安排相同，各自生成尝试名称。这是配置列表的生成顺序，不保证后面按这个顺序串行执行。


这里的 task_config 来自 models/trial/config.py，是题目来源引用（例如目录路径）。实际题目描述与判定规则仍在题目文件里；verifier 是本次运行的评测选项，不是把整个测试脚本塞进这份对象。

### 返回后，继续 Job 初始化

```python
# 回到 _init_trial_configs 的赋值处，得到完整的尝试配置列表。
self._trial_configs = self._build_standard_trial_configs()
# 再回到 Job.__init__，继续目录/记录、待运行配置与队列初始化。
```

[回到 Job.__init__ 函数卡](../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/harbor/job.py/Job.__init__.md#job-init-mainline)。等整个初始化完成后，Job.create 才返回 Job；之后 Job.run 和队列才使用这些配置创建并运行 Trial。任务文件的读取继续按 scope 后面的 Trial.create 入口进行，本次不跳过去。

## 我的直接表述（原话）

用户确认校准并接续 Step 012：

> 好的 校准一下 然后看一下这里的这个step把

尚无本函数的独立复述；上述组装关系为源码核对和静态示意，不记为用户已掌握。

本轮补充卡点：

> 那么这个应该是_create_job
> 怎么就突然变成了这个job._build_standard_trial config了呢?
> 我不是很理解

助手补清 _CREATE_JOB 的函数变量绑定，以及 Job.create 里的 cls(...) 会调用 Job.__init__，继而进入普通尝试配置的生成。当前尚未据此认定用户已接清这条链。

本轮接续：

> 好的 那么看一下这里的
> 这个函数吧
> 生成一下这个short term memroy吧

2026-11-12，已从 Job.__init__ 的 _init_trial_configs 调用恢复本函数的实际输入与返回位置；本轮尚无组合逻辑的独立复述。

本轮要求补例子：

> 好的这里是否能够给一个对应的样例 example呢?
> 也就是这里的这个trialconfig具体可能是什么样子的
> 来修改这里的这个静态例子

已按固定版本字段补同一组输入与输出节选；这是静态推导，不是实际执行证据。

关于具体配置例子的反馈：

> 好的 我大概知道了这里这个config大概是什么样子了
> 那么我们下一个部分需要看的是什么呢?

用户表示已大致知道配置形状；不据此推断所有字段或组合机制已掌握。接续建议先返回 _init_trial_configs 的赋值和 Job.__init__ 剩余初始化，再回 Job.create 返回 Job；之后沿已有 job.run/队列进入下一新入口 Trial.create。

## 尚不清楚

- 题目目录中的 instruction、task.toml、环境定义与验证脚本怎样被后续组件使用，接下来用同一例子看。
- 所有运行参数的合并优先级、本次未选择的 regrade/diff 路径，暂不展开。

<details>
<summary>来源与验证</summary>

- [完整组装函数](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job_plan.py#L140)，普通调用方为 [Job._init_trial_configs / _build_standard_trial_configs](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L448)。
- 任务来源 [TaskConfig:398](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L398)、[TrialConfig:488](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L488)；题目文件配置 [TaskConfig:853](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/task/config.py#L853)。
- 通过本地 git show v0.25.0 核对；示例构造器字段分别来自 models/job/config.py::JobConfig 与 models/trial/config.py 的 TaskConfig、AgentConfig、EnvironmentConfig、VerifierConfig。TrialConfig.set_default_trial_name/generate_trial_name 决定随机名称，默认 install_only=False，不触发禁用评测的特殊分支。
- 示例输出为静态推导的字段节选，没有执行真实配置构造、任务或安装。模型名与 Job ID 为教学值，随机名称是明确占位，不冒充运行输出。
- [Step 012 形成过程](../../../../../step-012-task-agent-verifier/04-flow.md#start-step012)。

</details>
