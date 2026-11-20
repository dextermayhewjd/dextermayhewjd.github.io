# U06 · JobConfig.model_validate 读取随仓 Job YAML

<a id="u06"></a>

[启动与配置目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[data_source.py 603](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L603)

```python
return job_config_type.model_validate(dict(payload))
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage data_source.py 596–603](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L596-L603) | 在 YAML 交给 `JobConfig.model_validate` 时看 dataset、agent 和 environment 的原值。 |
| ② 结果　[Dressage data_source.py 182–188](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L182-L188) | 在数据源检查 `self.job_config` 的对应字段，再确认任务解析和注册表使用这一实例。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/config.py#L311-L453) | 解析后的 Job YAML 映射。传入现有 `JobConfig` 时走复制分支 | 实测两份 YAML 均接受 | 带 dataset、Agent 模型、环境类型的 `JobConfig` | 实测三个消费字段吻合，摘要另见 U10 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/job/config.py#L399-L560) | 解析后的 Job YAML 映射。传入现有 `JobConfig` 时走复制分支 | 实测两份 YAML 均接受 | 带 dataset、Agent 模型、环境类型的 `JobConfig` | 实测三个消费字段吻合，摘要另见 U10 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L401-L587) | 解析后的 Job YAML 映射。传入现有 `JobConfig` 时走复制分支 | 实测两份 YAML 均接受 | 带 dataset、Agent 模型、环境类型的 `JobConfig` | 实测三个消费字段吻合，摘要另见 U10 |

**接续**　更换 YAML 或解析入口时复验。从这个测试不能判断远程 dataset 能否下载。 [data_source.py 562-607](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L562-L607) · [test_contracts.py 167](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/tests/integrations/harbor/test_contracts.py#L167) · [两份 YAML 和三版字段](../../investigations/18-example-configs/job-config-output.txt) · [问题 18](../../investigations/18-example-configs/README.md)
