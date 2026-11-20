# U25 · Job.on_agent_ended 登记 AGENT_END

<a id="u25"></a>

[Trial 事件与目录目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 409](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L409)

```python
job.on_agent_ended(self._safe(self._on_agent_end, "AGENT_END"))
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage plugin.py 409](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L409) · [Harbor trial.py 796](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L796) | 登记后观察模型阶段 finally 发出的 AGENT_END，按 Trial ID 找到仍活跃的 attempt。 |
| ② 结果　[Dressage plugin.py 708–715](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L708-L715) | 等 `_quiesce(record)` 返回，再观察该 attempt 的 phase 和 route 是否已经停接。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L157-L159) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `AGENT_END`。触发时，正常 ACTIVE attempt 等待 route 停接该轮模型请求。 | 离线 Job 的 AGENT_END 对每个 turn 调用一次 quiesce，随后回到 ready |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L247-L249) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `AGENT_END`。触发时，正常 ACTIVE attempt 等待 route 停接该轮模型请求。 | 离线 Job 的 AGENT_END 对每个 turn 调用一次 quiesce，随后回到 ready |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L248-L250) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `AGENT_END`。触发时，正常 ACTIVE attempt 等待 route 停接该轮模型请求。 | 离线 Job 的 AGENT_END 对每个 turn 调用一次 quiesce，随后回到 ready |

**接续**　用实际飞行中的请求核对停止接收及排空。 [plugin.py 707](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L707) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 11](../../investigations/11-trial-events/README.md)

[三版生命周期及替身范围](../../investigations/22-retry-policy/probe.py) · [三版运行输出](../../investigations/22-retry-policy/job-trial-output.txt)
