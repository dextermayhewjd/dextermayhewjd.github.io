# Job status：条件与 Pod 计数

[工作负载入口](README.md) · [Pod 与 Job](pods-and-jobs.md) · [资源对象模型](../02-resource-model/objects-spec-status.md)

`Job.status` 是一组观测字段，包含条件列表和 Pod 计数。它不是单一的 Running/Failed 字符串，也不同于某个 Pod 的 `status.phase`。

## 同一个 status 中的两类信息

下面是一个成功 Job 的字段节选，省略元数据、配置与时间字段；零值字段在实际响应中也可能省略。这是教学数据，没有查询真实集群。

```json
{
  "status": {
    "conditions": [{"type": "Complete", "status": "True"}],
    "active": 0,
    "succeeded": 1,
    "failed": 0
  }
}
```

| 字段 | 数据类型 | 含义 |
| --- | --- | --- |
| `conditions` | 对象列表 | 对 Job 当前条件的描述 |
| `conditions[i].type` | 字符串 | 条件名称，例如 Complete、Failed |
| `conditions[i].status` | 字符串 | 该条件是否成立：`"True"`、`"False"`、`"Unknown"` |
| `succeeded` | 整数 | 已进入 Succeeded 阶段的 Pod 数量 |
| `failed` | 整数 | 已进入 Failed 阶段的 Pod 数量 |
| `active` | 整数 | 尚未终止、处于 Pending 或 Running 的 Pod 数量 |

`conditions` 与这些计数在同一层；列表内部又有每条条件自己的 `status`。同名字段要结合所属对象看。

## True 表示这条条件成立

- `type="Complete"` 与 `status="True"`：成功完成条件成立。
- `type="Failed"` 与 `status="True"`：失败条件成立。
- `"False"` 表示对应条件不成立，不能直接读成任务失败；没有失败条件也不能直接推出成功。

因此不能单凭 `status == "True"` 把所有条件判断为健康。`Complete`、`Failed` 是 Job 的终态条件；条件列表还可能包含其他类型，不应把所有条件都当成终态。

## 为什么计数与条件不能相互替代

计数回答“多少 Pod 已经进入某阶段”，终态条件回答“Job 是否已经成功完成或失败”。完成目标和失败策略会影响后者。例如要求多个 Pod 成功的 Job，仅出现一个成功 Pod 并不保证完成；允许重试的 Job 出现失败 Pod，也不必然意味着整项 Job 已失败。

这些字段的发布时机也有区别。Kubernetes 文档说明，v1.31 及以后，Job 控制器等待该 Job 的所有 Pod 终止后才添加 Complete/Failed 终态条件。不能假设看到一个计数就一定同时看到对应终态条件。

客户端对所取得的对象反复读取字段，读取的是这次查询得到的数据；本地读字段本身不会向 API Server 发起刷新，也不会修改集群状态。

## 官方来源与边界

- [JobStatus 与 JobCondition 字段](https://kubernetes.io/docs/reference/kubernetes-api/batch/job-v1/#JobStatus)：核对字段类型、计数与条件的含义。
- [Jobs：终态条件](https://kubernetes.io/docs/concepts/workloads/controllers/job/#terminal-job-conditions)：核对完成/失败判定与版本相关的发布时机。
- 2026-11-03 查阅官方文档；没有绑定或运行某个真实 Kubernetes 集群。具体客户端怎样解释这些字段，应回到对应客户端源码核对。
