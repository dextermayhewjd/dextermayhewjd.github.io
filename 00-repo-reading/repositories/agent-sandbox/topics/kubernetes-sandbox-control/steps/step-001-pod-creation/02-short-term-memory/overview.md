# 02 · 本步函数记录索引

[本步 scope](../01-scope.md) · [继承背景](../03-long-term-memory/overview.md)

已确认并开始阅读 reconcilePod 的正常创建路径；当前从查询与分支进入，helper 只保留所需接口与源码定位。

**本步新读的是 reconcilePod。** reconcileChildResources 作为它的直接调用方从 03 调入，供需要时回看“从哪里进入、返回哪里”；它不是又新增的一项学习任务。

| 入口 | 本步用途 | 来源与状态 |
| --- | --- | --- |
| [SandboxReconciler.reconcilePod](functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md) | 查询现状、组装 Pod、设置归属、Create 与返回 | 已说清 AND 查询条件；字段与归属有初步概括，两路查询及名称解析仍待校准 |
| [SandboxReconciler.reconcileChildResources](functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md) | 本次直接调用方与返回位置 | 从本步 03 完整调取，只补当前子卡导航；首次认识与未知保留 |

03 中继续保留前一步两张卡的完整快照；Reconcile 只作背景，尚未调入当前 02。

当前继续形成的认识写在本步 02；Step 000 原件与本步 03 保留历史及入步快照。后续继承再按同一函数路径合并 03 与 02 的有效内容，不把它们算作两个不同函数。
