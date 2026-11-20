# U17 · build_trial_plan 配对原对象并写回 trial_name

<a id="u17"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[compat.py 158–165](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L158-L165)

```python
if config.task is not tasks[task_index]:
    raise HarborCompatibilityError(
        f"TrialConfig position {position} violates Harbor v0.18 task-major ordering"
    )
if config.agent is not agents[agent_index]:
    raise HarborCompatibilityError(
        f"TrialConfig position {position} violates Harbor v0.18 agent-minor ordering"
    )
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage compat.py 150–166](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L150-L166) | 在同一次运行里，将计划位置上的 task、agent 与原对象逐个比较。 |
| ② 结果　[Dressage compat.py 190–200](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L190-L200) | 写名后重新读取计划，核对 attempt、task、agent 的排列，以及名称是否落到正确的 TrialConfig 上。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L327) | 原 task/agent 引用、`job.config.n_attempts`、按 attempt → task → agent 排列的 TrialConfigs | 两题、两 Agent、两次尝试实测接受 | 生成位置三元组，在 `TrialConfig.trial_name` 写入唯一名并重新读取计划 | 八个位置实测顺序吻合，引用身份检查通过 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L425) | 原 task/agent 引用、`job.config.n_attempts`、按 attempt → task → agent 排列的 TrialConfigs | 两题、两 Agent、两次尝试实测接受 | 生成位置三元组，在 `TrialConfig.trial_name` 写入唯一名并重新读取计划 | 八个位置实测顺序吻合，引用身份检查通过 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L427) | 原 task/agent 引用、`job.config.n_attempts`、按 attempt → task → agent 排列的 TrialConfigs | 两题、两 Agent、两次尝试实测接受 | 生成位置三元组，在 `TrialConfig.trial_name` 写入唯一名并重新读取计划 | 八个位置实测顺序吻合，引用身份检查通过 |

**接续**　私有计划或 Pydantic 对象构建方式变化时复用这组八 Trial 输入。 [compat.py 162-166](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L162-L166) · [compat.py 199](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L199) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 09](../../investigations/09-trial-plan/README.md)
