# U29 · TrialHookEvent 的物理 ID、结果对象与输出目录

<a id="u29"></a>

[Trial 事件与目录目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 1240](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1240)

```python
return str(getattr(event, "trial_name")), str(getattr(event, "trial_id"))
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor trial.py 597–606](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L597-L606) | 在 Harbor 分发事件时记录 `config.trial_name`、`result.id` 与 `result` 对象。 |
| ② 结果　[Dressage plugin.py 769–778](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L769-L778) · [Dressage plugin.py 1239–1251](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1239-L1251) | 在插件实际提交时，比较同一次运行里事件的 result 身份、物理 ID 和传给 Store 的 `trial_dir`。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L334-L343) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/hooks.py#L55-L56) | 事件提供 config、result、由它们得到的 trial_name 和 trial_id | 主动发 END，真实对象已接收 | Dressage 得到 `(trial_name, str(trial_id))`、`trials_dir / trial_name` 及同一份 TrialResult | 实测对象身份、键和目录吻合 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L590-L599) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/hooks.py#L55-L56) | 事件提供 config、result、由它们得到的 trial_name 和 trial_id | 主动发 END，真实对象已接收 | Dressage 得到 `(trial_name, str(trial_id))`、`trials_dir / trial_name` 及同一份 TrialResult | 实测对象身份、键和目录吻合 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/trial.py#L597-L606) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/trial/hooks.py#L55-L56) | 事件提供 config、result、由它们得到的 trial_name 和 trial_id | 主动发 END，真实对象已接收 | Dressage 得到 `(trial_name, str(trial_id))`、`trials_dir / trial_name` 及同一份 TrialResult | 实测对象身份、键和目录吻合 |

**接续**　三版受控 Job 已自然发出事件，早期主动触发实验另外核对了事件携带对象的身份。 [plugin.py 1244-1248](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1244-L1248) · [plugin.py 778](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L778) · [0.18 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.18.0.txt) · [0.25 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.25.0.txt) · [0.26 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-output.txt) · [结果探测实际调用的范围](../../investigations/12-reward-validity/result_contract_probe.py) · [问题 11](../../investigations/11-trial-events/README.md) · [问题 12](../../investigations/12-reward-validity/README.md)

[三版生命周期及替身范围](../../investigations/22-retry-policy/probe.py) · [三版运行输出](../../investigations/22-retry-policy/job-trial-output.txt)
