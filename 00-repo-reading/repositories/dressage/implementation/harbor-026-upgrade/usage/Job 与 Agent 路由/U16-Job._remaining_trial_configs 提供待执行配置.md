# U16 · Job._remaining_trial_configs 提供待执行配置

<a id="u16"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[compat.py 75](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L75)

```python
configs = job._remaining_trial_configs
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage compat.py 71–89](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L71-L89) | 查看 `job._remaining_trial_configs` 的长度及每项的 trial 名、task、agent。 |
| ② 结果　[Dressage plugin.py 337–348](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L337-L348) · [Dressage plugin.py 384–386](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L384-L386) | 在插件处理同一批待执行配置时核对名称和实际替换的 Agent，记下哪一个 TrialConfig 接到了改动。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L327) | Job 私有成员应为 list，元素带 `trial_name`、`agent`、`task` | 本地单题与两题输入实测接受 | 得到 tuple，Dressage 对原 Trial 配置命名并注入路由 | 单 Trial 与八 Trial 的数量和路由配置实测 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L425) | Job 私有成员应为 list，元素带 `trial_name`、`agent`、`task` | 本地单题与两题输入实测接受 | 得到 tuple，Dressage 对原 Trial 配置命名并注入路由 | 单 Trial 与八 Trial 的数量和路由配置实测 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L427) | Job 私有成员应为 list，元素带 `trial_name`、`agent`、`task` | 本地单题与两题输入实测接受 | 得到 tuple，Dressage 对原 Trial 配置命名并注入路由 | 单 Trial 与八 Trial 的数量和路由配置实测 |

**接续**　续跑 Job 被该集成拒绝，当前证据来自新建 Job。 [compat.py 71-89](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L71-L89) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 09](../../investigations/09-trial-plan/README.md) · [问题 11](../../investigations/11-trial-events/README.md)
