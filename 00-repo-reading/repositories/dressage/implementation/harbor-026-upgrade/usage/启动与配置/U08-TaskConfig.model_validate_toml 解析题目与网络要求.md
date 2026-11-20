# U08 · TaskConfig.model_validate_toml 解析题目与网络要求

<a id="u08"></a>

[启动与配置目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[plugin.py 1136](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1136)

```python
task_config = TaskConfig.model_validate_toml(config_path.read_text(encoding="utf-8"))
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage plugin.py 1132–1136](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1132-L1136) | 记下该 Trial 实际读取的 `task.toml` 和声明的阶段网络设置。 |
| ② 结果　[Dressage plugin.py 1141–1150](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1141-L1150) | 看解析后生成的 `digest` 与 `network_class`，再按相同题目核对两版的分类以及摘要差异。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/task/config.py#L899-L901) | UTF-8 的 `task.toml` 文本。这里使用 `harbor.models.task.config.TaskConfig` | 同一生成题目可经 Harbor `Task` 解析其配置，插件的网络归类仅对源码 | 题目配置提供 environment、agent、steps。插件用这些字段归类并对 JSON 表示求摘要 | 题目解析有实测，插件消费的逐阶段网络类别与摘要待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/task/config.py#L978-L980) | UTF-8 的 `task.toml` 文本。这里使用 `harbor.models.task.config.TaskConfig` | 同一生成题目可经 Harbor `Task` 解析其配置，插件的网络归类仅对源码 | 题目配置提供 environment、agent、steps。插件用这些字段归类并对 JSON 表示求摘要 | 题目解析有实测，插件消费的逐阶段网络类别与摘要待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/task/config.py#L979-L981) | UTF-8 的 `task.toml` 文本。这里使用 `harbor.models.task.config.TaskConfig` | 同一生成题目可经 Harbor `Task` 解析其配置，插件的网络归类仅对源码 | 题目配置提供 environment、agent、steps。插件用这些字段归类并对 JSON 表示求摘要 | 题目解析有实测，插件消费的逐阶段网络类别与摘要待验 |

**接续**　任务里有多个 step 时，观察各阶段配置如何影响最终网络类别。 [plugin.py 1100-1114](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1100-L1114) · [三版 DAPO 文件交接原始输出](../evidence/dapo-files.txt) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [问题 14](../../investigations/14-phase-network-policy/README.md)
