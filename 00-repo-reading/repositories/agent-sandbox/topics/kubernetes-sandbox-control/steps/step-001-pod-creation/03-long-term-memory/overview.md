# 03 · 本主题此前累计记录

[本步 scope](../01-scope.md) · [前一步总结](../../step-000-sandbox-reconcile/05-task-flow.md)

继承来源：Kubernetes Step 000 的 03 + 02。前一步 03 无函数记录，02 中两张函数卡完整继承到本目录；没有跨主题复制 Fleet 卡片。

**两张卡已经继承到这里。** 继承采用完整复制并重定位链接，Step 000 的原件继续作为当时的阅读记录保留；不是把原文件搬走。它们在本目录保存进入 Step 001 时的累计快照。

| 函数 | 已有背景与保留的未知 |
| --- | --- |
| [SandboxReconciler.Reconcile](functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md) | 外层读取、快照、子资源与状态写回；版本和状态细节继续按原记录保留 |
| [SandboxReconciler.reconcileChildResources](functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md) | 子资源协调与信息摘取、条件与返回；各资源内部机制尚未逐项展开 |

首次接触、最近认识、原话和来源不因继承改变。复制和链接重定位不代表新增理解。

两张卡按调用层级分工：Reconcile 连接读取、委托、重排与状态写回；reconcileChildResources 展开资源协调及内存状态形成。两处都会说明调用交接，具体子资源细节仍归后者。

当前实际使用或更新的记录看 [本步 02 索引](../02-short-term-memory/overview.md)；其中 reconcileChildResources 是从这里调取的工作副本，不会因此删除本目录的继承快照。
