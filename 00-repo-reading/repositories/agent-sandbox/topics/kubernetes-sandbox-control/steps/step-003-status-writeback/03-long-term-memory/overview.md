# 03 · 进入本步时的累计模型

[本步 scope](../01-scope.md) · [前一步总结](../../step-002-sandbox-readiness/05-task-flow.md)

合并本主题 Step 002 的 03 + 02，同路径使用包含本步有效增量的版本，共五张完整函数卡。原步骤文件保留，不因继承清空未知或改写认识时间。

| 函数 | 来源 |
| --- | --- |
| [SandboxReconciler.Reconcile](functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md) | Step 002/03，原始接触在 Step 000 |
| [SandboxReconciler.reconcileChildResources](functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md) | Step 002/02，包含原模型与状态汇总的导航 |
| [SandboxReconciler.reconcilePod](functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md) | Step 002/03，来源于 Step 001 |
| [SandboxReconciler.computeConditions](functions/controllers/sandbox_controller.go/SandboxReconciler.computeConditions.md) | Step 002/02，状态汇总与实际表述 |
| [SandboxReconciler.computeReadyCondition](functions/controllers/sandbox_controller.go/SandboxReconciler.computeReadyCondition.md) | Step 002/02，正常就绪判断与前置限定 |

本目录是进入本步时的快照；当前实际使用与新增认识写在 02。
