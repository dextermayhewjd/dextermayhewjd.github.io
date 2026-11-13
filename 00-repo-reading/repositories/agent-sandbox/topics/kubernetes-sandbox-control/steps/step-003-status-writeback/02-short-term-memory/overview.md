# 02 · 本步函数记录

[Scope](../01-scope.md) · [前序累计模型](../03-long-term-memory/overview.md)

| 函数 | 本步用途 | 来源与状态 |
| --- | --- | --- |
| [SandboxReconciler.updateStatus](functions/controllers/sandbox_controller.go/SandboxReconciler.updateStatus.md) | 从比较、补丁依据进入实际状态写回与版本冲突 | 本步新读，尚无个人机制复述 |
| [SandboxReconciler.Reconcile](functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md) | 提供旧状态、旧版本及写回调用后的接收位置 | 从本步 03 调取，原认识与未知保留 |

其他函数继续作为 03 背景或源码定位，不因出现调用就提前建卡。
