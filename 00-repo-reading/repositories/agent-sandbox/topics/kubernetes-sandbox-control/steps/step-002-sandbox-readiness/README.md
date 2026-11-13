# Kubernetes 主题 · Step 002：状态汇总与就绪判断

[主题入口](../../README.md) · [唯一进度](../../../../README.md#current-reading) · [前一步总结](../step-001-pod-creation/05-task-flow.md)

## 本步问题

取得 Pod 等资源的观察结果后，控制器怎样形成 Sandbox 状态，什么时候报告 Ready？

第一处是 computeConditions，已看它怎样组织状态条目；当前进入 [computeReadyCondition](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.computeReadyCondition.md)。其他条件计算方法先按职责理解，不因出现名字就预建卡片。

## 本步入口

1. [Scope：位置、局部骨架与停止点](01-scope.md)。
2. [02：当前函数记录](02-short-term-memory/overview.md)。
3. [03：前序累计模型](03-long-term-memory/overview.md)，继承本主题 Step 001 的 03 + 02，按函数路径合并为三张卡。
4. [04：实际阅读过程](04-flow.md)。
5. [05：本步任务链路总结](05-task-flow.md)，按状态汇总与 Ready 普通路径收束。

2026-11-05，用户已概括 Pod 与按需 Service 两项主判断，并询问本步结束。本步在补充提前返回前提后按既定范围收束；其他条件与错误细节的未知继续保留，没有把整个控制器标为已经读懂。

后续用户已确认进入 [Step 003：状态写回与版本冲突](../step-003-status-writeback/01-scope.md)。本步 03 + 02 合并为五张完整函数记录继承到下一步，原件保留。
