# U50 · 从 trial 与 step 的 exception_info 生成训练失败记录

<a id="u50"></a>

[结果、样本与最终选择目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[artifacts.py 1074](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1074)

```python
top = getattr(result, "exception_info", None)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage artifacts.py 431–433](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L431-L433) · [Dressage artifacts.py 1072–1090](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1072-L1090) | 用带非零 Agent 退出且分数为 0.75 的结果，查看 trial 与 step 异常及本版的奖励有效性判定。 |
| ② 结果　[Dressage artifacts.py 466–477](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L466-L477) | 观察 `failures`、`reward` 和 `trainable` 的组合。保留分数与能否训练是两个要核对的输出。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/result.py#L81) | 读取 trial/step 异常类型、消息与 step 名。受控例子含分数 0.75 与非零退出异常 | 用真实 TrialResult 及受控输入实测 | Dressage 生成致命 HARBOR_TRIAL_EXCEPTION，保留得分并将 bundle.trainable 置 False | 实测 `trainable=False`，选中 0.75。该版没有 `reward_valid` |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/result.py#L123-L128) | 读取 trial/step 异常类型、消息与 step 名。受控例子含分数 0.75 与非零退出异常 | 用真实 TrialResult 及受控输入实测 | Dressage 生成致命 HARBOR_TRIAL_EXCEPTION，保留得分并将 bundle.trainable 置 False | 实测 `reward_valid=False`、`trainable=False`，选中 0.75 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/result.py#L142-L148) | 读取 trial/step 异常类型、消息与 step 名。受控例子含分数 0.75 与非零退出异常 | 用真实 TrialResult 及受控输入实测 | Dressage 生成致命 HARBOR_TRIAL_EXCEPTION，保留得分并将 bundle.trainable 置 False | 实测 `reward_valid=True`、`trainable=False`，选中 0.75 |

**接续**　按默认策略运行时，失败记录的 retryable、Harbor 实际重试次数及外层整组重试各有不同的判定。 [artifacts.py 1072-1103](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1072-L1103) · [0.18 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.18.0.txt) · [0.25 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.25.0.txt) · [0.26 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-output.txt) · [结果探测实际调用的范围](../../investigations/12-reward-validity/result_contract_probe.py) · [问题 12](../../investigations/12-reward-validity/README.md)

[22 · 错误类型和重试范围](../../investigations/22-retry-policy/README.md#evidence)

单步普通 RuntimeError 的运行对照还改变了失败码。0.18/0.25 无分，额外记 REWARD_MISSING；0.26 默认进入评分，得到 0.75，仅记 HARBOR_TRIAL_EXCEPTION，仍不训练。 [三版评分与失败码](../../investigations/12-reward-validity/lifecycle-rewards.txt)
