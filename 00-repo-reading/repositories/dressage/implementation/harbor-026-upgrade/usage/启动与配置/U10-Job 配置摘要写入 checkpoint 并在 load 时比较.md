# U10 · Job 配置摘要写入 checkpoint 并在 load 时比较

<a id="u10"></a>

[启动与配置目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[data_source.py 832](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L832)

```python
"job": _redact_public(_dump_model(job_config, reveal_sensitive=True)),
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage data_source.py 357–369](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L357-L369) | 在 save 路径记下 checkpoint 的 source、registry 摘要和使用的配置。 |
| ② 结果　[Dressage data_source.py 410–421](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L410-L421) | 把同一个已保存 checkpoint 交给 load。看哪个字段相等、哪个字段首先触发漂移错误。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/config.py#L338) | 相同 YAML、seed、采样数与 shuffle，分别控制 `PYTHONHASHSEED` | 三版已用相同输入求摘要 | source 摘要随两个哈希种子变化 | 本地两题的同版 checkpoint 在同种子下恢复；换种子后拒绝。 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/job/config.py#L430) | 相同 YAML、seed、采样数与 shuffle，分别控制 `PYTHONHASHSEED` | 三版已用相同输入求摘要 | source 摘要随两个哈希种子变化 | 摘要差异已测。旧 checkpoint 是否可恢复仍待真实 load |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L439) | 相同 YAML、seed、采样数与 shuffle，分别控制 `PYTHONHASHSEED` | 三版已用相同输入求摘要 | 两种种子下 source 摘要一致，与旧版输出不同 | 本地两题用 0.26 读取 0.18 的 checkpoint 时拒绝；0.26 同版切换种子可恢复。 |

**接续**　触发 save/load 的场景或配置序列化变化时才复测恢复。已存的两个种子输出可以直接引用。 [data_source.py 357-382](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L357-L382) · [data_source.py 829-854](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L829-L854) · [同输入的摘要与哈希种子](../../investigations/19-checkpoint-digests/hash-seed-output.txt) · [两份 YAML 和三版字段](../../investigations/18-example-configs/job-config-output.txt) · [问题 19](../../investigations/19-checkpoint-digests/README.md) [两个写入进程与五个 load 的真实输出](../../investigations/19-checkpoint-digests/checkpoint-output.txt)
