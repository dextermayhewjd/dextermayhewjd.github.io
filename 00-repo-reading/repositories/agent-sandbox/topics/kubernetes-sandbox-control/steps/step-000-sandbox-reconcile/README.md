# Kubernetes 主题 · Step 000：单个 Sandbox 的协调与状态反馈

[主题入口](../../README.md) · [项目唯一进度](../../../../README.md#current-reading) · [打开 scope](01-scope.md)

## 本步问题

控制器收到一个 Sandbox 的协调请求后，怎样读取需求、协调 Pod 等子资源、计算并写回状态？为什么一次 Reconcile 返回不代表环境已经就绪？

入口为 `SandboxReconciler.Reconcile`。首先只读运行中的普通 Sandbox 路径；`reconcileChildResources` 展开到内部职责和返回位置，Pod 创建与状态计算算法先按接口理解。

## 本步入口

1. [范围与完整导航](01-scope.md)。
2. [短期记录](02-short-term-memory/overview.md)：[Reconcile 函数卡](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md)及其调用的 [reconcileChildResources 函数卡](02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md)。
3. [此前累计记录](03-long-term-memory/overview.md)：本主题首步暂无前序继承。
4. [实际讨论记录](04-flow.md)。
5. [本步任务链路总结](05-task-flow.md)：按职责骨架收束，继续到 [Step 001 的 Pod 创建范围](../step-001-pod-creation/01-scope.md)。

## 起点与边界

本主题按用户最新授权独立编号、按需引用旧材料；不把旧 Fleet 主题的卡片整体复制进来。首步不要求部署集群，也不把源码静态核对当作实践经验或个人已掌握。

源码固定在 `37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1`，本地 `/home/fredkeira/projects/agent-sandbox`。已保留用户对外层主线的复述与待澄清问题；没有真实集群运行结果。实时阅读位置以项目入口为准。

2026-11-05，用户反馈当前问题已差不多并确认下一步方案。本步按已确认的外层协调与子资源职责深度收束，原有未知继续保留；两张函数卡完整继承到本主题 Step 001 的 03。
