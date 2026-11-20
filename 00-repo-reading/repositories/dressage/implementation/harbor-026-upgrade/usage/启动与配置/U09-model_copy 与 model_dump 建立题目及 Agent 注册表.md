# U09 · model_copy 与 model_dump 建立题目及 Agent 注册表

<a id="u09"></a>

[启动与配置目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[data_source.py 712–713](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L712-L713)

```python
task_config=_deepcopy_model(task),
agent_config=_deepcopy_model(agent),
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage data_source.py 683–713](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L683-L713) | 看循环正在配对哪一个 task、哪一个 agent，以及哪两个对象被复制进 `HarborPromptSpec`。 |
| ② 结果　[Dressage data_source.py 182–189](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L182-L189) · [Dressage data_source.py 258–275](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L258-L275) | 从注册表取回相同的 spec，比较 task、agent 的实际字段和身份，检查模板复用时有无串改。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/config.py#L61-L163) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/config.py#L320-L377) | 从 resolver 得到的 Trial 任务引用和 Agent 配置。`model_copy(deep=True)` 与 JSON 模式 dump | 源码可接收 | 复制后的 task/agent 配置及序列化数据进入 `HarborPromptSpec`。同一模板可反复取用 | 源码追到注册表。完整 registry 与同一输入的逐字段对照待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L65-L209) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L398-L455) | 从 resolver 得到的 Trial 任务引用和 Agent 配置。`model_copy(deep=True)` 与 JSON 模式 dump | 源码可接收 | 复制后的 task/agent 配置及序列化数据进入 `HarborPromptSpec`。同一模板可反复取用 | 源码追到注册表。完整 registry 与同一输入的逐字段对照待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/config.py#L66-L210) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/config.py#L407-L464) | 从 resolver 得到的 Trial 任务引用和 Agent 配置。`model_copy(deep=True)` 与 JSON 模式 dump | 源码可接收 | 复制后的 task/agent 配置及序列化数据进入 `HarborPromptSpec`。同一模板可反复取用 | 源码追到注册表。完整 registry 与同一输入的逐字段对照待验 |

**接续**　核对一个 spec 的原始任务身份、Agent 配置和运行指纹。U10 单独判断恢复。 [data_source.py 712-713](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L712-L713) · [data_source.py 683-687](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L683-L687) · [data_source.py 729-750](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L729-L750) · [两份 YAML 和三版字段](../../investigations/18-example-configs/job-config-output.txt) · [同输入的摘要与哈希种子](../../investigations/19-checkpoint-digests/hash-seed-output.txt) · [问题 09](../../investigations/09-trial-plan/README.md) · [问题 19](../../investigations/19-checkpoint-digests/README.md)
