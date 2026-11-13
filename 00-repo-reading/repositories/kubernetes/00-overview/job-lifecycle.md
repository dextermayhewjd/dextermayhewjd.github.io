# 一次 Job：从提交到容器运行，再到状态反馈

[总览入口](README.md) · [资料总入口](../README.md)

设想一项简单工作：运行一个容器，处理输入，成功后退出。下面选择资源与服务可用的正常路径，先看各方职责。

## 先分清对象与组件

- **对象**保存描述和状态：例如 Job、Pod。
- **组件**持续执行职责：例如 API Server、控制器、Scheduler、kubelet。
- **容器进程**最终执行用户提供的工作。

## 沿一次任务看交接

| 顺序 | 谁在行动 | 交接的对象或结果 |
| --- | --- | --- |
| 1. 提交期望 | 客户端向 API Server 提交 Job | 保存 Job 对象，其 `spec.template` 描述要运行的 Pod |
| 2. 准备执行单元 | Job 控制器观察 Job，并通过 API 管理所需 Pod | 出现等待调度的 Pod 对象 |
| 3. 选择节点 | Scheduler 观察尚未绑定节点的 Pod，选择合适节点 | Pod 被绑定到一个 Node |
| 4. 执行工作 | 对应节点的 kubelet 协调容器运行时等节点能力 | 根据 Pod 配置准备并运行容器 |
| 5. 反馈状态 | kubelet 更新 Pod 状态，Job 控制器观察关联 Pod | Job 的成功、失败等状态逐步更新 |
| 6. 收束与清理 | 客户端或其他观察者读取结果；系统按已配置的策略清理 | 完成状态与资源删除是两个动作；是否自动删除取决于清理配置 |

这些组件通过 API 对象的读写与观察协作。下面的线表示各自与 API 的关系，而非一次同步函数调用链：

```text
client          -> API Server <-> etcd
Job controller <-> API Server
Scheduler      <-> API Server
kubelet        <-> API Server
kubelet -> container runtime -> container process
```

## 回顾时检查三个关系

1. **提交成功与工作完成**：API 接受对象后，执行仍需后续组件推进。
2. **Job 与 Pod**：Job 描述完成目标并管理执行，Pod 是具体的执行单元。
3. **期望与观察**：`spec` 描述想达到什么，`status` 记录系统已经观察到什么；协调循环持续缩小两者的差距。

理解主线后，再按问题进入[架构](../01-architecture/README.md)、[工作负载](../03-workloads/README.md)、[运行环境](../04-runtime-environment/README.md)或[运维排查](../06-operations/README.md)。

## 官方来源

- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
- [Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)
- [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
