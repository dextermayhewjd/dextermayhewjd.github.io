# U55 · generate_rollout_harbor_sync 返回训练数据

<a id="u55"></a>

[结果、样本与最终选择目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[rollout.py 1277](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1277)

```python
return RolloutFnTrainOutput(samples=groups, metrics=metrics)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage rollout.py 1265–1277](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1265-L1277) | 从公开训练入口传相同的 `rollout_id`、buffer 和 `evaluation=False`，看它返回的类型、样本组与 metrics。 |
| ② 结果　[Slime rollout.py 647–656](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/ray/rollout.py#L647-L656) | 在 Slime 接回后检查 `data.samples` 和 `data.metrics`。随后核对每个 Sample 的 `rollout_id`。本地分段夹具只覆盖转换。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/result.py#L243) | Dressage 入口接收 args、rollout_id、data_buffer、evaluation=False，前面已按 JobResult 收齐有效组 | 接口形状已确认，完整 Slime 调用待验 | 有 Slime 输出类型时返回 RolloutFnTrainOutput(samples=groups, metrics=metrics)，兼容分支返回 groups | 局部样本转换已有证据。公开训练入口返回的类型和 metrics 仍待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/job/result.py#L243) | Dressage 入口接收 args、rollout_id、data_buffer、evaluation=False，前面已按 JobResult 收齐有效组 | 接口形状已确认，完整 Slime 调用待验 | 有 Slime 输出类型时返回 RolloutFnTrainOutput(samples=groups, metrics=metrics)，兼容分支返回 groups | 局部样本转换已有证据。公开训练入口返回的类型和 metrics 仍待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/result.py#L259) | Dressage 入口接收 args、rollout_id、data_buffer、evaluation=False，前面已按 JobResult 收齐有效组 | 接口形状已确认，完整 Slime 调用待验 | 有 Slime 输出类型时返回 RolloutFnTrainOutput(samples=groups, metrics=metrics)，兼容分支返回 groups | 局部样本转换已有证据。公开训练入口返回的类型和 metrics 仍待验 |

**接续**　在实际 Slime 环境接住函数返回，检查组、样本身份和 metrics。 [run_harbor_training_qwen3.5_4b.sh 67](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh#L67) · [0.18 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.18.0.txt) · [0.25 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-0.25.0.txt) · [0.26 结果对象和样本输出](../../investigations/12-reward-validity/result-contract-output.txt) · [结果探测实际调用的范围](../../investigations/12-reward-validity/result_contract_probe.py) · [问题 12](../../investigations/12-reward-validity/README.md) · [问题 13](../../investigations/13-final-attempt/README.md)
