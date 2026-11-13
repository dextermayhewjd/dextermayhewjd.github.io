# 资料来源与项目阅读入口

[共享专题](../README.md)

## 原有资料

2026-11-05，从 Agent Lightning 的 k8s 目录整体迁入 20 份 Markdown，保留原有八类职责、正文与来源。旧入口保留跳转；各项目历史中的相关链接重新定位，个人学习状态没有随迁移改变。

原有资料涵盖 Job 任务流程、API Server、对象模型、Namespace、Labels、Pod/Job、镜像与命令，以及 kr8s v0.20.15 的用法。官方来源与客户端版本继续保存在各页。

## 本轮补充来自哪些问题

| 基础关系 | 原始项目材料 |
| --- | --- |
| 本地对象、状态写回与版本依据 | [Agent Sandbox · Reconcile](../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-000-sandbox-reconcile/02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.Reconcile.md) |
| 对象归属、Pod 信息、PVC 和 Service 的职责 | [Agent Sandbox · reconcileChildResources](../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-000-sandbox-reconcile/02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcileChildResources.md) |
| List/Get 与本地筛选的区别、归属引用的写入与读取 | [Agent Sandbox Step 001 · reconcilePod](../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-001-pod-creation/02-short-term-memory/functions/controllers/sandbox_controller.go/SandboxReconciler.reconcilePod.md) |
| Job 与项目任务的交接 | [Agent Lightning · Kubernetes 对应关系](../../agent-lightning/references/kubernetes-integration.md) |

Agent Sandbox 的源码证据固定为 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。共享正文抽取通用含义，项目特有函数、字段和判定继续在原项目维护。

本轮只在 API Server 与所有者关系正文补充通用区别；nameHash、resolvePodName、缓存索引键及两路查询的具体组合继续留在项目卡中。AND 条件、metadata/spec 和 Pod Ready 的已有基础直接复用，不重复建一份课程。

## 验证与学习状态

本轮是静态源码核对与资料整理，没有创建集群资源或进行网络、存储实验。文档存在不代表个人已经掌握；阅读进度分别见 [Agent Sandbox](../../agent-sandbox/README.md#current-reading) 与 [Agent Lightning](../../agent-lightning/README.md#current-reading)。
