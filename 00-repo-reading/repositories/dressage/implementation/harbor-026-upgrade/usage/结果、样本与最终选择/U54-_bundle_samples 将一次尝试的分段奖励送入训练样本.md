# U54 · _bundle_samples 将一次尝试的分段奖励送入训练样本

<a id="u54"></a>

[结果、样本与最终选择目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[rollout.py 813–818](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L813-L818)

```python
converted = _bundle_samples(
    template=template,
    bundle=bundle,
    args=args,
    reward_key=reward_key,
)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage rollout.py 813–818](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L813-L818) | 在分区传入一个含两段的 trainable bundle，记下源 Trial ID、目标键和原奖励。 |
| ② 结果　[Dressage rollout.py 669–672](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L669-L672) · [Dressage rollout.py 823–824](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L823-L824) | 看 `converted` 加入本组时的两个 Sample。核对相同 Trial ID、前段零奖励和末段完整奖励。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/result.py#L80) | 同一 Trial 的 bundle、模板、两份轨迹片段、reward_key。这是 Dressage 的下游转换 | 样本模板及两段夹具实测接受 | 给两个样本保留同一 Trial ID，前一段奖励为零，末段拿到完整目标与辅助分数映射 | 实测 [{reward: 0}, {reward: 0.75, aux: 0.25}] |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/result.py#L86) | 同一 Trial 的 bundle、模板、两份轨迹片段、reward_key。这是 Dressage 的下游转换 | 样本模板及两段夹具实测接受 | 给两个样本保留同一 Trial ID，前一段奖励为零，末段拿到完整目标与辅助分数映射 | 同输入实测两段奖励与基线一致 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/result.py#L109) | 同一 Trial 的 bundle、模板、两份轨迹片段、reward_key。这是 Dressage 的下游转换 | 样本模板及两段夹具实测接受 | 给两个样本保留同一 Trial ID，前一段奖励为零，末段拿到完整目标与辅助分数映射 | 与基线实测一致 |

**接续**　三版真实 Job 选出的最终 bundle 经夹具模板转换，两段样本与 manifest 的最终物理 ID 一致。公开 Slime 训练入口由 U55 验收。 [rollout.py 650-674](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L650-L674) · [0.18 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.18.0.txt) · [0.25 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.25.0.txt) · [0.26 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-output.txt) · [结果探测实际调用的范围](../../investigations/12-reward-validity/result_contract_probe.py) · [问题 12](../../investigations/12-reward-validity/README.md) · [问题 13](../../investigations/13-final-attempt/README.md)

[三版结果、两段奖励与物理 ID](../../investigations/22-retry-policy/job-trial-output.txt)
