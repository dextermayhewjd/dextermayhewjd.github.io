# Kubernetes 主题 · Step 003：状态写回与版本冲突

[主题入口](../../README.md) · [唯一进度](../../../../README.md#current-reading) · [前一步总结](../step-002-sandbox-readiness/05-task-flow.md)

## 本步问题

内存中已经算出新的 Sandbox 状态，怎样通过 Kubernetes API 写回，并避免旧观察覆盖更新后的对象？

用户已确认继续前一轮建议；这里的实际入口是 SandboxReconciler.updateStatus。沿 Ready=False 变为 True 的普通写入，再看版本冲突这一项代表性边界。事件和指标方法先按职责理解，不新增一组辅助函数必读任务。

## 阅读入口

1. [Scope：完整位置与四段骨架](01-scope.md)。
2. [02：本步函数记录](02-short-term-memory/overview.md)。
3. [03：进入本步时的累计模型](03-long-term-memory/overview.md)：按函数路径合并前一步 03 + 02，继承五张卡。
4. [04：实际讨论与核对](04-flow.md)。

本步当前开始阅读，尚无用户对具体写入机制的独立复述；没有创建集群或调用真实 API。
