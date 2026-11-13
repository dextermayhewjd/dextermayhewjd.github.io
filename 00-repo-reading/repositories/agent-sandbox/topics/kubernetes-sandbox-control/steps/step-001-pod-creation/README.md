# Kubernetes 主题 · Step 001：从 Sandbox 需求创建 Pod

[主题入口](../../README.md) · [唯一进度](../../../../README.md#current-reading) · [前一步总结](../step-000-sandbox-reconcile/05-task-flow.md)

## 本步问题

Sandbox 已存在、要求 Running，但没有对应 Pod 时，reconcilePod 怎样组装并提交 Pod 对象？

用户于 2026-11-05 确认按共享基础与正常创建路径的方案继续。本步只关注确认缺少 Pod、从 podTemplate 组装、设置归属、Create 与返回；不把整个函数的失败恢复分支纳入首轮。

## 阅读入口

1. [Scope：整体位置与局部导航](01-scope.md)。
2. [02：本步函数记录索引](02-short-term-memory/overview.md)。已打开 [reconcilePod 函数卡](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md)，从查询与分支开始；直接调用方已从 03 调取，其他 helper 不预建卡。
3. [03：继承的外层模型](03-long-term-memory/overview.md)。完整继承本主题 Step 000 的两张函数卡，来源和未知保留。
4. [04：实际过程](04-flow.md)。
5. [05：正常创建路径总结](05-task-flow.md)，接到 [Step 002：状态汇总与就绪判断](../step-002-sandbox-readiness/01-scope.md)。

继承与建立 scope 不表示 Pod 创建已读懂。当前没有运行实验，具体进度以项目入口为准。

2026-11-05，用户确认继续下一函数。本步按正常创建路径收束，原有未知与源码证据保留；Step 002 合并继承本步 03 + 02，不从这里搬走原件。
