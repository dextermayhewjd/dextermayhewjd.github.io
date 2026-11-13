> 历史快照：2026-11-03，落实已确认的八类知识目录之前。本文保留当时结构，现行内容从项目 k8s/ 入口查看。

# Pod 与 Job：执行单元和完成任务的管理

[本层入口](README.md) · [资料总入口](../README.md)

**Pod 是 Kubernetes 创建和管理的最小可部署单元，可以包含一个或多个容器。Job 描述需要运行到完成的工作，并管理为此创建的 Pod。**

| 对象 | 主要职责 |
| --- | --- |
| Pod | 承载容器运行；同一 Pod 内的容器共享网络等运行环境 |
| Job | 按任务配置管理 Pod，跟踪所需的成功完成数量和失败情况 |

## Job 与 Pod 怎样关联

```text
Job + Pod template
        |
        v
Kubernetes Job controller
        |
        v
      Pod(s) -> container workload
```

Job 中的 `spec.template` 描述要创建的 Pod。Kubernetes 内置的 **Job 控制器**观察 Job 和相关 Pod 的状态，决定是否需要创建 Pod、更新完成情况等。一个 Job 可以管理多个 Pod，数量与并行方式由配置决定。

向 API Server 提交 Job 的客户端程序，与 Kubernetes 内置 Job 控制器是不同角色。前者表达任务要求，后者在控制平面中持续推进执行。

## 读资源对象时先认三个部分

- `metadata`：名称、namespace、labels 等标识信息。
- `spec`：期望的配置，例如 Pod 模板与执行约束。
- `status`：系统观察到的情况，例如活动 Pod 数量、成功完成数量和状态条件。

Job 与 Pod 都有自己的状态。读取 Job 状态与读取某个 Pod 的状态，需要区分对象层次。

## 官方来源

- [Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)
