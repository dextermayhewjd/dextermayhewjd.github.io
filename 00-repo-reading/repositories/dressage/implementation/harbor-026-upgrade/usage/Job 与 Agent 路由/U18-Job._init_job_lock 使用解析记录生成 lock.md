# U18 · Job._init_job_lock 使用解析记录生成 lock

<a id="u18"></a>

[Job 与 Agent 路由目录](README.md) · [全部用法](../README.md)

**Dressage 原行**　[rollout.py 550–553](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L550-L553)

```python
_validated_model_update(
    _copy_model(item.spec.task_config),
    source=None,
)
```

## 在原调用中核对

| 观察位置 | 到这一行看什么 |
| --- | --- |
| ① 输入　[Harbor job.py 961–967](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L961-L967) | 在 `build_job_lock` 看临时 Job 解析出的 task 及 download results。 |
| ② 结果　[Harbor job.py 969–978](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L969-L978) | 从 Job 读取实际生成的 lock，核对 schema 和任务标识。需要验证落盘时再打开该 Job 的 `lock.json`。 |

## 三个版本的输入和输出

| Harbor 版本 | 传入什么 | 输入是否匹配 | 产出或副作用 | 下游是否得到预期结果 |
| --- | --- | --- | --- | --- |
| [0.18.0](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L639-L644) | 本地任务标识能在已创建 Job 的解析记录中找到 | 三个本地 Agent 配置实测接受 | Job lock 的 schema 为 2 | 本地 lock 已构建。真实远程分区落盘待验 |
| [0.25.0](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/job.py#L949-L955) | 本地任务标识能在已创建 Job 的解析记录中找到 | 三个本地 Agent 配置实测接受 | Job lock 的 schema 为 3 | 本地 lock 已构建。真实远程分区落盘待验 |
| [0.26.0](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/job.py#L961-L967) | 本地任务标识能在已创建 Job 的解析记录中找到 | 三个本地 Agent 配置实测接受 | Job lock 的 schema 为 3 | 本地 lock 已构建。真实远程分区落盘待验 |

**接续**　目标版按 schema 3 验收。变更远程 task.source 时要查同一任务 ID 能否在 lock 找回。 [rollout.py 551-552](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L551-L552) · [rollout.py 556-565](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L556-L565) · [三版 Job 和 lock 输出](../../investigations/10-job-lock/job-lock-output.txt) · [问题 10](../../investigations/10-job-lock/README.md)
