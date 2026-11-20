# U11 · Job._resolve_task_configs 展开任务来源

<a id="u11"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[compat.py 113](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L113)

```python
configs = await resolver(job_config)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage compat.py 108–116](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L108-L116) | 在 `await resolver(job_config)` 前看显式 tasks 与 datasets 的来源。 |
| ② 结果　[Dressage data_source.py 615–632](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L615-L632) | 回到数据源，核对展开后的任务数量、顺序和本地目录。远程 dataset 需要用真实来源单独回放。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L347-L362) | 显式 tasks 或 datasets 所在的 Harbor `JobConfig` | 本地单题与两题输入实测接受 | Harbor 返回非空 `list[Trial TaskConfig]`，Dressage 检查后转为 tuple | 本地 dataset 限两题时按目录枚举取到 zeta、lambda。远程来源另验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L445-L446) | 显式 tasks 或 datasets 所在的 Harbor `JobConfig` | 本地单题与两题输入实测接受 | Harbor 返回非空 `list[Trial TaskConfig]`，Dressage 检查后转为 tuple | 同目录先按路径排序，限两题时取到 alpha、beta。远程来源另验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L447-L448) | 显式 tasks 或 datasets 所在的 Harbor `JobConfig` | 本地单题与两题输入实测接受 | Harbor 返回非空 `list[Trial TaskConfig]`，Dressage 检查后转为 tuple | 同目录先按路径排序，限两题时取到 alpha、beta。全量采样的顺序也改变。远程来源另验 |

**接续**　按实际题目身份核对本地目录升级前后的样本。新数据集来源单独回放。[问题 23](../../investigations/23-local-dataset-selection/README.md) · [同目录三版输出](../../investigations/23-local-dataset-selection/local-selection-output.txt) [compat.py 105-118](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L105-L118) · [data_source.py 610-632](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L610-L632) · [三版真实 Job、计划和钩子登记](../../investigations/09-trial-plan/trial-plan-output.txt) · [Job 探测的断言与替身](../../investigations/09-trial-plan/probe.py) · [问题 09](../../investigations/09-trial-plan/README.md) · [问题 10](../../investigations/10-job-lock/README.md)
