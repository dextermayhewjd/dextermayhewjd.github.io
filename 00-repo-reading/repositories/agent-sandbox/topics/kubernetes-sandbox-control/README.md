# Kubernetes 沙箱资源与生命周期

[项目入口与唯一进度](../../README.md#current-reading) · [岗位目标与五项范围](../../references/tencent-k8s-learning-scope.md) · [本主题第一步](steps/step-000-sandbox-reconcile/01-scope.md)

## 本主题解决什么问题

一份 Agent 沙箱需求，怎样在 Kubernetes 上成为可用环境，被任务使用，并在失败或结束后正确回收。

先建立单个 Sandbox 的协调模型，再按问题进入 WarmPool、Claim、访问与隔离，最后结合部署和排障形成实践证据。具体选题沿用项目已有五项范围，不把所有相关函数预先列成必读课。

## 编号与记忆

1. 本主题独立从 Step 000 编号，不延续旧 Fleet 步骤的序号。
2. 首步不继承旧主题的全部函数卡。旧记录现归入 [Fleet 主题](../fleet-environment-orchestration/README.md)，需要时回查；这不是删除或否定已有学习。
3. 本主题内部逐步积累：后续步骤的 03 合并本主题前一步的 03 + 02；02 保存当步实际使用的记录。
4. 创建 scope 不等于读懂其中所有函数。短期卡按实际阅读建立，源码解释与用户理解分开保存。

## 步骤索引

| 步骤 | 核心问题 | 入口 |
| --- | --- | --- |
| Step 000 · 单个 Sandbox 的协调与状态反馈 | Reconcile 收到什么、怎样交给子资源协调、结果怎样写回？ | [scope](steps/step-000-sandbox-reconcile/01-scope.md) · [步骤说明](steps/step-000-sandbox-reconcile/README.md) |
| Step 001 · 从 Sandbox 需求创建 Pod | 没有对应 Pod 时，怎样组装、设置归属并提交创建？ | [scope](steps/step-001-pod-creation/01-scope.md) · [步骤说明](steps/step-001-pod-creation/README.md) |
| Step 002 · 状态汇总与就绪判断 | 已取得 Pod 等观察结果，怎样形成条件条目并判断 Ready？ | [scope](steps/step-002-sandbox-readiness/01-scope.md) · [步骤说明](steps/step-002-sandbox-readiness/README.md) |
| Step 003 · 状态写回与版本冲突 | 新的观察状态怎样写回，怎样避免过期写入？ | [scope](steps/step-003-status-writeback/01-scope.md) · [步骤说明](steps/step-003-status-writeback/README.md) |
| Step 004 · 预热池数量协调 | 备用数量与观察结果不一致时怎样补充或缩减？ | [scope](steps/step-004-warmpool-reconcile/01-scope.md) · 仅准备范围 |
| Step 005 · Claim 领取与归属 | 怎样热领取、冷创建、处理竞争并确定回收责任？ | [scope](steps/step-005-claim-ownership/01-scope.md) · 仅准备范围 |
| Step 006 · 环境访问与隔离 | 调用方如何执行命令、传输文件，并定位连接或权限问题？ | [scope](steps/step-006-access-and-isolation/01-scope.md) · 仅准备范围 |

Step 004–006 按用户本次要求预先准备 01-scope.md，尚未生成短期记忆、长期继承或完成记录；与 Dressage 的 [Harbor 环境接入](../../../dressage/topics/02-harbor-integration/steps/step-013-harbor-kubernetes-environment/01-scope.md)相互引用，不重复建立控制器阅读。当前阅读位置只在项目入口维护。

## 可回查的旧材料

- [旧 Fleet Step 000 总结](../fleet-environment-orchestration/steps/step-000-warmpool-reconcile/05-task-flow.md)：应用侧如何提供配置、任务和回调。
- [旧 Fleet Step 001](../fleet-environment-orchestration/steps/step-001-start-warmpools/README.md)：预热入口与适用范围讨论，未展开的内部机制继续保留为未知。
- [与 Dressage 的比较](../../references/dressage-prewarm-comparison.md)：任务级预取与 Kubernetes 环境供给的分工。
