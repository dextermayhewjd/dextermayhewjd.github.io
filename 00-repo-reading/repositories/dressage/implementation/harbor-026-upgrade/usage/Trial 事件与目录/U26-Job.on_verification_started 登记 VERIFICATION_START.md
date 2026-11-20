# U26 · Job.on_verification_started 登记 VERIFICATION_START

<a id="u26"></a>

[Trial 事件与目录目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 410–412](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L410-L412)

```python
job.on_verification_started(
    self._safe(self._on_verification_start, "VERIFICATION_START")
)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage plugin.py 410–412](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L410-L412) · [Harbor single_step.py 96](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/single_step.py#L96) | 在 single-step 路径等 VERIFICATION_START 真正发出，记下 attempt 进入时的 phase。 |
| ② 结果　[Dressage plugin.py 717–729](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L717-L729) | 看正常已停接的 attempt 是否保持原状态。若进来时仍 ACTIVE，查失败码及停接调用。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L161-L163) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `VERIFICATION_START`。触发时，正常已停接的 route 无额外动作。仍 ACTIVE 时标记失败并等待停接。 | 单步与两步夹具在开始评测前均已停接对应 turn，状态为 ready |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L251-L253) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `VERIFICATION_START`。触发时，正常已停接的 route 无额外动作。仍 ACTIVE 时标记失败并等待停接。 | 单步与两步夹具在开始评测前均已停接对应 turn，状态为 ready |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L252-L254) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `VERIFICATION_START`。触发时，正常已停接的 route 无额外动作。仍 ACTIVE 时标记失败并等待停接。 | 单步与两步夹具在开始评测前均已停接对应 turn，状态为 ready |

**接续**　用真实 verifier 与 Gateway 核对评测期间的路由状态。 [plugin.py 717](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L717) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 11](../../investigations/11-trial-events/README.md)

[三版生命周期及替身范围](../../investigations/22-retry-policy/probe.py) · [三版运行输出](../../investigations/22-retry-policy/job-trial-output.txt)

单步 Agent 抛普通 RuntimeError、物理重试关闭时，0.18/0.25 跳过 verifier，0.26 按默认策略发 VERIFICATION_START。受控 verifier 返回 0.75。 [三版评分与失败码](../../investigations/12-reward-validity/lifecycle-rewards.txt)
