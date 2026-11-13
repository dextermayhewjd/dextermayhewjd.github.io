# 02 · 本步函数记录

[本步 scope](../01-scope.md) · [继承来源](../03-long-term-memory/overview.md)

| 函数 | 当前用途 | 状态 |
| --- | --- | --- |
| [SandboxReconciler.computeConditions](functions/controllers/sandbox_controller.go/SandboxReconciler.computeConditions.md) | 汇总状态条目，理解可选条目与返回列表 | 用户已明确计算状态不执行调度；精确条件与可选条目机制仍按原记录保留 |
| [SandboxReconciler.computeReadyCondition](functions/controllers/sandbox_controller.go/SandboxReconciler.computeReadyCondition.md) | 默认 False、提前返回、Pod/Service 要求及 Ready 结果 | 用户已概括两项主判断；提前返回前提由助手补充，细节未知保留 |
| [SandboxReconciler.reconcileChildResources](functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md) | 调用 computeConditions，并接住结果更新内存状态 | 从本步 03 调取；旧内容与未知保留 |

本步按状态汇总与 Ready 普通路径收束；其余三个条件函数和辅助诊断方法仍按职责定位，不预建卡片。
