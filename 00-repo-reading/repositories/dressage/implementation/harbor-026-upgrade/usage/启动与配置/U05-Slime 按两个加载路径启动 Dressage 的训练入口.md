# U05 · Slime 按两个加载路径启动 Dressage 的训练入口

<a id="u05"></a>

[启动与配置目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[run_harbor_training_qwen3.5_4b.sh 66–67](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh#L66-L67)

```bash
--data-source-path dressage.integrations.harbor.data_source.HarborDataSource
--rollout-function-path dressage.integrations.harbor.rollout.generate_rollout_harbor_sync
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage run_harbor_training_qwen3.5_4b.sh 66–67](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh#L66-L67) | 在随仓训练脚本展开参数，记下 data source 和 rollout 的两个导入路径。 |
| ② 结果　[Slime rollout.py 443–446](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/ray/rollout.py#L443-L446) | 看 Slime 构造的 `self.data_source` 类型以及 `self.generate_rollout` 的模块和函数名。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L121-L134) | 训练配置交给 `HarborDataSource`，`args, rollout_id, data_buffer, evaluation` 交给 Dressage 入口。到 Harbor 时是临时 `JobConfig` | 加载路径已定位，完整入口待测 | Dressage 得到任务组并调 Job。最终训练输出见 U55，评测输出见 U56 | 两个随仓加载路径可查，Slime 真运行待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L171-L224) | 训练配置交给 `HarborDataSource`，`args, rollout_id, data_buffer, evaluation` 交给 Dressage 入口。到 Harbor 时是临时 `JobConfig` | 加载路径已定位，完整入口待测 | Dressage 得到任务组并调 Job。最终训练输出见 U55，评测输出见 U56 | 两个随仓加载路径可查，Slime 真运行待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L171-L225) | 训练配置交给 `HarborDataSource`，`args, rollout_id, data_buffer, evaluation` 交给 Dressage 入口。到 Harbor 时是临时 `JobConfig` | 加载路径已定位，完整入口待测 | Dressage 得到任务组并调 Job。最终训练输出见 U55，评测输出见 U56 | 两个随仓加载路径可查，Slime 真运行待验 |

**接续**　保留两个路径作为一个启动点，运行训练与评测分支分别验收最终返回。 [run_harbor_training_qwen3.5_4b.sh 66-67](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh#L66-L67) · [data_source.py 123](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L123) · [rollout.py 1257-1277](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1257-L1277) · [问题 07](../../investigations/07-agent-routing/README.md) · [问题 13](../../investigations/13-final-attempt/README.md)
