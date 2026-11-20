# U53 · get_result 与 write_job_manifest 对齐最终物理尝试

<a id="u53"></a>

[结果、样本与最终选择目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[rollout.py 802](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L802)

```python
bundle = plugin.get_result(trial_name, str(final_result.id))
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage rollout.py 795–813](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L795-L813) | 用最终 result 的物理 ID 取 bundle，保留未采用尝试作对照。 |
| ② 结果　[Dressage rollout.py 865–872](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L865-L872) · [Dressage artifacts.py 561–571](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L561-L571) | 在整组验收后看 Store 实收的 `selected_keys`，按物理 ID 核对 manifest 的选中项和 `superseded`。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L850) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/result.py#L237) | 按 trial_name 接住 Harbor 最终结果，再以 `(trial_name, str(final_result.id))` 查 bundle。整组检查决定 final_keys | 真实 Job 与插件的默认结束入口已实测 | 取得相应 bundle 并出具 manifest，未采用尝试保留历史且不能参与训练 | 真实 Job 重试后最终 UUID 与默认 manifest、两段转换样本一致，训练分区的整组验收仍待实测 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L1207) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/job/result.py#L237) | 按 trial_name 接住 Harbor 最终结果，再以 `(trial_name, str(final_result.id))` 查 bundle。整组检查决定 final_keys | 真实 Job 与插件的默认结束入口已实测 | 取得相应 bundle 并出具 manifest，未采用尝试保留历史且不能参与训练 | 真实 Job 重试后最终 UUID 与默认 manifest、两段转换样本一致，训练分区的整组验收仍待实测 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L1219) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/result.py#L253) | 按 trial_name 接住 Harbor 最终结果，再以 `(trial_name, str(final_result.id))` 查 bundle。整组检查决定 final_keys | 真实 Job 与插件的默认结束入口已实测 | 取得相应 bundle 并出具 manifest，未采用尝试保留历史且不能参与训练 | 真实 Job 重试后最终 UUID 与默认 manifest、两段转换样本一致，训练分区的整组验收仍待实测 |

**接续**　按公开训练分区的整组选键和返回批次核对。 [rollout.py 864-872](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L864-L872) · [artifacts.py 553](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L553) · [问题 13](../../investigations/13-final-attempt/README.md)

[22 · 哪些错误产生第二次尝试](../../investigations/22-retry-policy/README.md#evidence)
