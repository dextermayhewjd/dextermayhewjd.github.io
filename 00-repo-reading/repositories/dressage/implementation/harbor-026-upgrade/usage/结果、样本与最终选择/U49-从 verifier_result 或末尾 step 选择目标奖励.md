# U49 · 从 verifier_result 或末尾 step 选择目标奖励

<a id="u49"></a>

[结果、样本与最终选择目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[artifacts.py 1057–1064](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1057-L1064)

```python
verifier_result = getattr(result, "verifier_result", None)
rewards = getattr(verifier_result, "rewards", None)
if rewards is None:
    for step in reversed(getattr(result, "step_results", None) or []):
        step_verifier = getattr(step, "verifier_result", None)
        rewards = getattr(step_verifier, "rewards", None)
        if rewards is not None:
            break
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage artifacts.py 1056–1069](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1056-L1069) | 分别给出顶层分数、只在 step 有分数、只有辅助键三种输入，看取分走哪一条分支。 |
| ② 结果　[Dressage artifacts.py 431–439](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L431-L439) · [Dressage artifacts.py 459–461](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L459-L461) | 看 bundle 的完整 `rewards`、`reward_key` 与选出的 `reward`。检查缺目标键时是否误用辅助分。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/result.py#L80) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/verifier/result.py#L5) | 先读 `result.verifier_result.rewards`。值为 `None` 才倒序找 step 的奖励，空字典会保留。Dressage 从所得映射选择配置指定的键 | 用真实 TrialResult 及受控输入实测 | 选中目标分数或报 REWARD_MISSING。Harbor 无 reward_valid 字段 | 四组受控输入实测选分符合 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/result.py#L86) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/verifier/result.py#L5) | 先读 `result.verifier_result.rewards`。值为 `None` 才倒序找 step 的奖励，空字典会保留。Dressage 从所得映射选择配置指定的键 | 用真实 TrialResult 及受控输入实测 | 同一 Dressage 取分路径。Harbor 有 reward_valid | 同四组实测，正常 0.75，只有辅助键时为 None，只有 step 时回退取 0.75 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/result.py#L109) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/verifier/result.py#L5) | 先读 `result.verifier_result.rewards`。值为 `None` 才倒序找 step 的奖励，空字典会保留。Dressage 从所得映射选择配置指定的键 | 用真实 TrialResult 及受控输入实测 | 同一 Dressage 取分路径。Harbor 另按异常策略判断 reward_valid | 四组实测，正常 0.75，只有辅助键时为 None，只有 step 时回退取 0.75 |

**接续**　原 step-only 夹具未触发实际的末步异常。Harbor 的正常多步运行另有把所选奖励写回顶层的环节。 [artifacts.py 1056-1069](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L1056-L1069) · [0.18 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.18.0.txt) · [0.25 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.25.0.txt) · [0.26 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-output.txt) · [结果探测实际调用的范围](../../investigations/12-reward-validity/result_contract_probe.py) · [问题 12](../../investigations/12-reward-validity/README.md)

两步题选 final、末步 verifier 失败时，真实 Harbor 顶层没有分数。三版 Dressage 均回退到第一步的 0.25 并拒绝训练。原 step-only 用例另行考查无异常的手工输入。 [三版评分与失败码](../../investigations/12-reward-validity/lifecycle-rewards.txt)
