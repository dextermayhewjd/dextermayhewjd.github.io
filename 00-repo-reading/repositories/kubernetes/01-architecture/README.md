# 架构：谁负责推进工作，彼此怎样协作

[Kubernetes 资料总入口](../README.md)

这一层保存 Kubernetes 自身的组件与工作机制。先从控制平面、节点和运行时的职责接起整体，再按问题展开具体组件。

- [API Server](api-server.md)：客户端从哪里查询或修改资源，API Server 与控制器分别承担什么职责。
- [控制器与协调循环](reconciliation.md)：怎样反复观察并推进资源达到期望。
- 组件在同一任务中的位置，见[一次 Job 的完整交接](../00-overview/job-lifecycle.md)。

继续复习资源的命名与筛选，可进入[资源组织](../02-resource-model/README.md)。
