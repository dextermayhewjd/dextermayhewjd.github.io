# U12 · model_validate 重建每个分区的临时 JobConfig

<a id="u12"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[rollout.py 575–578](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L575-L578)

```python
return _validated_model_update(
    source_job_config,
    **updates,
)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Dressage rollout.py 550–578](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L550-L578) | 用同一分区，看 `model_validate` 收到的 task 副本、agents、datasets 和本次 Job 名。 |
| ② 结果　[Dressage rollout.py 695–705](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L695-L705) | 看约束检查之后传给 `_CREATE_JOB` 的实际 `job_config` 类型和值，以及是否交回 Job。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/job/config.py#L311-L453) · [相关源码](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/trial/config.py#L320-L377) | 复制源配置，再写 tasks、agents、jobs_dir、n_attempts、并发数。清空 datasets 并将临时 task.source 置空 | 实测接收本地题目、两份模板和一个 Agent 配置 | 得到同类型的临时 `JobConfig`，供 `Job.create` 使用 | 实测将临时配置交给 Job.create 并成功建本地 lock。远程数据集分区待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/job/config.py#L399-L560) · [相关源码](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/models/trial/config.py#L398-L455) | 复制源配置，再写 tasks、agents、jobs_dir、n_attempts、并发数。清空 datasets 并将临时 task.source 置空 | 实测接收本地题目、两份模板和一个 Agent 配置 | 得到同类型的临时 `JobConfig`，供 `Job.create` 使用 | 实测将临时配置交给 Job.create 并成功建本地 lock。远程数据集分区待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/job/config.py#L401-L587) · [相关源码](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/models/trial/config.py#L407-L464) | 复制源配置，再写 tasks、agents、jobs_dir、n_attempts、并发数。清空 datasets 并将临时 task.source 置空 | 实测接收本地题目、两份模板和一个 Agent 配置 | 得到同类型的临时 `JobConfig`，供 `Job.create` 使用 | 实测将临时配置交给 Job.create 并成功建本地 lock。远程数据集分区待验 |

**接续**　同输入的 lock 探测使用本地题目。核对真正从 dataset 展开的分区时，留存临时配置及生成的 lock。 [rollout.py 430-445](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L430-L445) · [rollout.py 550-576](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L550-L576) · [三版 Job 和 lock 输出](../../investigations/10-job-lock/job-lock-output.txt) · [问题 06](../../investigations/06-agent-credential-preflight/README.md) · [问题 10](../../investigations/10-job-lock/README.md)
