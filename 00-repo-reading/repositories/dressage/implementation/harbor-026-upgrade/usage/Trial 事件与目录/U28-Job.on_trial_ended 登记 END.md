# U28 · Job.on_trial_ended 登记 END

<a id="u28"></a>

[Trial 事件与目录目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 414](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L414)

```python
job.on_trial_ended(self._safe(self._on_end, "END"))
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage plugin.py 414](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L414) · [Harbor trial.py 675–676](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L675-L676) | 从运行中的 Trial 自然收尾进入 END，记下 `event.result` 和 attempt 的取消标记。 |
| ② 结果　[Dressage plugin.py 743–749](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L743-L749) · [Dressage plugin.py 797–806](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L797-L806) | 等该 attempt 的 `finalize_task`。正常时看 bundle 的登记，取消时看跳过提交后是否仍关闭 route。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L165-L167) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L386-L390) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `END`。触发时，等待 finalize。正常尝试提交一次，已标记取消的尝试跳过提交，两条路径都尝试关闭 route。 | 正常 END 一次 Store 提交，取消后 END 零次，两条路径均调用一次 route handle.close |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L255-L257) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L660-L667) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `END`。触发时，等待 finalize。正常尝试提交一次，已标记取消的尝试跳过提交，两条路径都尝试关闭 route。 | 正常 END 一次 Store 提交，取消后 END 零次，两条路径均调用一次 route handle.close |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L256-L258) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L667-L676) | 登记一个异步 callback。触发时 Harbor 传 `TrialHookEvent` | 真实 Job 实测接受该 callback | 方法返回同一 Job。登记 `END`。触发时，等待 finalize。正常尝试提交一次，已标记取消的尝试跳过提交，两条路径都尝试关闭 route。 | 正常 END 一次 Store 提交，取消后 END 零次，两条路径均调用一次 route handle.close |

**接续**　在真实 Gateway、Proxy 下核对请求和资源的收尾。 [plugin.py 742](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L742) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [结果探测实际调用的范围](../../investigations/12-reward-validity/result_contract_probe.py) · [0.18 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.18.0.txt) · [0.25 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.25.0.txt) · [0.26 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-output.txt) · [问题 11](../../investigations/11-trial-events/README.md)

[三版生命周期及替身范围](../../investigations/22-retry-policy/probe.py) · [三版运行输出](../../investigations/22-retry-policy/job-trial-output.txt)
