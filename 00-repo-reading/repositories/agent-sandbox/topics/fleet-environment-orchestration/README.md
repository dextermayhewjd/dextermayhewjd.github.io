# Fleet：训练侧环境使用与编排

[项目入口与唯一进度](../../README.md#current-reading) · [Kubernetes 主题](../kubernetes-sandbox-control/README.md) · [与 Dressage 的对照](../../references/dressage-prewarm-comparison.md)

## 本主题记录什么

从应用侧理解配置和任务如何进入 SandboxFleet，运行策略怎样安排环境准备、任务执行与清理，以及预热机制的用途和边界。

这里收纳此前实际读过的两个步骤，包括完整 scope、短期与长期记录、讨论、历史快照和备用材料。2026-11-05 按用户要求整体整理到 topics 下；原步骤编号和目录名称保留，正文只修正迁移所需的链接。

## 步骤索引

| 步骤 | 内容 | 保留的状态 |
| --- | --- | --- |
| [Step 000 · 整体调用骨架](steps/step-000-warmpool-reconcile/README.md) | main、Fleet 构造、任务加载、run 分派、run_naive；[scope](steps/step-000-warmpool-reconcile/01-scope.md)、[总结](steps/step-000-warmpool-reconcile/05-task-flow.md) | 已按整体骨架范围收束，具体未知保留 |
| [Step 001 · 预热入口与环境需求](steps/step-001-start-warmpools/README.md) | setup、start_warmpools、预热池与任务需求、Dressage 对照；[scope](steps/step-001-start-warmpools/01-scope.md) | 已读与未完成部分一并保留，不因整理目录标为完成 |

## 与新主题怎样衔接

1. 本主题的 Step 000、001 及当时的记忆继承关系不变。
2. Kubernetes 主题独立从自己的 Step 000 开始，按需引用本主题，不自动复制这里的全部记忆。
3. 两个主题研究的层次不同：这里看训练侧怎样请求和使用环境，Kubernetes 主题看资源需求如何由控制器落实。
4. 之后是否继续深入本主题，由具体问题决定；整理到 topics 不表示重新开启或重读所有内容。

项目当前阅读位置仍只在根 README 中维护。
