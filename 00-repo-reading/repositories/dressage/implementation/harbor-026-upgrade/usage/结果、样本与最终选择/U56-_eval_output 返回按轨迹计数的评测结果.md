# U56 · _eval_output 返回按轨迹计数的评测结果

<a id="u56"></a>

[结果、样本与最终选择目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[rollout.py 1254](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1254)

```python
return RolloutFnEvalOutput(data=data, metrics=metrics)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage rollout.py 1273–1274](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1273-L1274) · [Dressage rollout.py 1227–1254](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1227-L1254) | 从公开评测入口传 `evaluation=True`，给同一条轨迹两个分段，查看 `data.harbor` 与 metrics。 |
| ② 结果　[Slime rollout.py 573–581](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/ray/rollout.py#L573-L581) | 在 Slime 接收处查看 `result.data`、`result.metrics` 与奖励条数。两段的同一轨迹应只贡献一次。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/result.py#L80) | evaluation=True。按 parent_traj_id（缺失时取 rollout_id）从同一轨迹选最高 segment_index | 两段样本夹具实测 | data.harbor 包含 rewards、truncated、samples。可用时封装 RolloutFnEvalOutput 并附 metrics，否则返回字典 | 两段只产生 [0.75] 一项。未完整断言其他字段 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/result.py#L86) | evaluation=True。按 parent_traj_id（缺失时取 rollout_id）从同一轨迹选最高 segment_index | 两段样本夹具实测 | data.harbor 包含 rewards、truncated、samples。可用时封装 RolloutFnEvalOutput 并附 metrics，否则返回字典 | 两段只产生 [0.75] 一项，与基线一致 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/result.py#L109) | evaluation=True。按 parent_traj_id（缺失时取 rollout_id）从同一轨迹选最高 segment_index | 两段样本夹具实测 | data.harbor 包含 rewards、truncated、samples。可用时封装 RolloutFnEvalOutput 并附 metrics，否则返回字典 | 两段只产生 [0.75] 一项，与基线一致 |

**接续**　用真实 eval 入口确认返回类型、truncated 和 metrics。 [rollout.py 1227-1254](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1227-L1254) · [rollout.py 1274](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1274) · [0.18 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.18.0.txt) · [0.25 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.25.0.txt) · [0.26 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-output.txt) · [结果探测实际调用的范围](../../investigations/12-reward-validity/result_contract_probe.py) · [问题 12](../../investigations/12-reward-validity/README.md) · [问题 13](../../investigations/13-final-attempt/README.md)
