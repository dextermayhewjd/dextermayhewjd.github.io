# U23 · Job.on_trial_started 登记 START

<a id="u23"></a>

[Trial 事件与目录目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 407](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L407)

```python
job.on_trial_started(self._safe(self._on_start, "START"))
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage plugin.py 407](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L407) · [Harbor trial.py 610](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L610) | 先看登记的 START 回调，再在 Trial 自然发 START 时记下 trial 名与物理 ID。 |
| ② 结果　[Dressage plugin.py 640–665](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L640-L665) · [Dressage plugin.py 692](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L692) | 在处理同一事件后看 `_attempts[(trial_name, trial_id)]` 和 route 的 READY 状态。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L145-L147) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `START`。触发时，找到 Trial 对应 slot，建 AttemptRecord 并注册该 attempt 的模型 route。 | 真实 Job 发 START 后按相同物理 ID 找到 ready 状态的 attempt |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L235-L237) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `START`。触发时，找到 Trial 对应 slot，建 AttemptRecord 并注册该 attempt 的模型 route。 | 真实 Job 发 START 后按相同物理 ID 找到 ready 状态的 attempt |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L236-L238) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `START`。触发时，找到 Trial 对应 slot，建 AttemptRecord 并注册该 attempt 的模型 route。 | 真实 Job 发 START 后按相同物理 ID 找到 ready 状态的 attempt |

**接续**　用真实网关核对 route 注册。 [plugin.py 639](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L639) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 11](../../investigations/11-trial-events/README.md)

[三版生命周期及替身范围](../../investigations/22-retry-policy/probe.py) · [三版运行输出](../../investigations/22-retry-policy/job-trial-output.txt)
