# 整体总览：先把一次工作串起来

[Kubernetes 资料总入口](../README.md)

建立整体模型时，先跟随一个完整任务：**用资源对象表达期望 → 控制器持续协调 → 调度到节点 → 容器实际执行 → 状态反馈。**

- [一次 Job 从提交到完成](job-lifecycle.md)：沿同一个任务定位对象、组件与交接。
- [资源对象、spec 与 status](../02-resource-model/objects-spec-status.md)：读懂“期望”和“观察”分别保存在何处。
- [控制器与协调循环](../01-architecture/reconciliation.md)：理解系统怎样反复观察并推进工作。

总览负责连接关系，主题目录负责保存各概念的正文。回查一个概念后，返回同一条任务主线继续。
