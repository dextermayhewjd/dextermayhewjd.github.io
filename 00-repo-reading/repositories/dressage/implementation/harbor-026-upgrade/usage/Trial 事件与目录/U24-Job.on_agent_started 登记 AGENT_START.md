# U24 · Job.on_agent_started 登记 AGENT_START

<a id="u24"></a>

[Trial 事件与目录目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 408](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L408)

```python
job.on_agent_started(self._safe(self._on_agent_start, "AGENT_START"))
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage plugin.py 408](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L408) · [Harbor trial.py 722](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L722) | 登记后沿同一 Trial 运行到 AGENT_START。记下收到的物理 ID 与进入时的 phase。 |
| ② 结果　[Dressage plugin.py 698–705](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L698-L705) | 看 `open_turn` 收到的 `turn_id`，返回后核对序号与 ACTIVE 状态。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L153-L155) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `AGENT_START`。触发时，READY 状态的 attempt 打开本次模型 turn，进入 ACTIVE。 | 离线 Job 每个 Agent 阶段打开一次 turn，序号和物理 ID 一致，回调返回时为 active |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L243-L245) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `AGENT_START`。触发时，READY 状态的 attempt 打开本次模型 turn，进入 ACTIVE。 | 离线 Job 每个 Agent 阶段打开一次 turn，序号和物理 ID 一致，回调返回时为 active |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L244-L246) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `AGENT_START`。触发时，READY 状态的 attempt 打开本次模型 turn，进入 ACTIVE。 | 离线 Job 每个 Agent 阶段打开一次 turn，序号和物理 ID 一致，回调返回时为 active |

**接续**　使用实际模型请求核对每个 turn 的请求归属。 [plugin.py 694](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L694) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 11](../../investigations/11-trial-events/README.md)

[三版生命周期及替身范围](../../investigations/22-retry-policy/probe.py) · [三版运行输出](../../investigations/22-retry-policy/job-trial-output.txt)
