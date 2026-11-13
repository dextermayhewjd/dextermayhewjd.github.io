# Step 001 · 资源计划怎样进入预热与就绪等待

[项目唯一进度](../../../../README.md#current-reading) · [打开 scope](01-scope.md) · [上一步总结](../step-000-warmpool-reconcile/05-task-flow.md)

## 承接哪一个问题

Step 000 已连接配置、任务加载、运行分派及准备／执行／清理。当前沿 run_naive 中的 setup 调用，进入 SandboxFleet.start_warmpools，理解已有资源计划怎样按预算交给预热，以及何时可以返回继续执行任务。

本步核心入口沿用上一轮推荐的 start_warmpools。用户随后明确要求先打开调用方 setup，第一张函数卡据此从原步骤记录调入；不重新选择仓库或另造阅读路线。

## 本步入口

1. [范围与面包屑导航](01-scope.md)。
2. [本步短期记录](02-short-term-memory/overview.md)：第一张为按用户要求调入的 setup 卡；其他未读函数不预建。
3. [继承记录](03-long-term-memory/overview.md)：来自 Step 000 的 03 + 02。
4. [实际讨论过程](04-flow.md)。

## 本步准备保留什么

1. 资源计划 entries、单个条目的 replicas 与创建预算之间的关系。
2. start_warmpools 怎样提交一波条目，以及等待发生在哪一次调用。
3. 需要下钻时，_warm_entries 和 _warm_entry 各自接收与交出什么。

这些是待阅读的问题，不是个人已掌握的结论。Step 000 的理解、疑问与引用完整继承；本步尚无新的机制复述或运行实验。
