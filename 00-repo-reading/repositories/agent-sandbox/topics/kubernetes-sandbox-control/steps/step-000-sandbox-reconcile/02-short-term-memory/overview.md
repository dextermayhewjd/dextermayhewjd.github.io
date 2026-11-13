# 02 · 本步短期记录

[本步 scope](../01-scope.md) · [实际过程](../04-flow.md)

| 入口 | 当前记录重点 | 首次接触与状态 |
| --- | --- | --- |
| [SandboxReconciler.Reconcile](functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md) | req 与 Sandbox 的关系、普通路径、子资源及状态交接、返回与后续协调 | Kubernetes Step 000，2026-11-05；已有外层主线复述与校准，未知保留 |
| [SandboxReconciler.reconcileChildResources](functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md) | 子资源协调、内存 Status 更新、返回延迟与错误，再交回父函数 | Kubernetes Step 000，2026-11-05；本轮开始单独阅读，尚无内部机制复述 |

updateStatus、SetupWithManager 及具体资源辅助函数暂以源码入口导航；实际选定并展开后再建立对应记录。当前不预建整个 sandbox_controller.go 的函数卡。
