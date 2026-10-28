# Step 011 · 一组生成任务怎样并发、汇总和交付

[主题入口](../../README.md) · [前一步：单任务生成与奖励](../step-010-generate-and-rm/README.md) · [唯一进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

前一步跟随 generate_and_rm，已有“受控生成 → 后处理 → 奖励归属”的外层模型。本步按用户指定进入它的调用者 generate_and_rm_group，围绕任务下标、Task、结果形状和交付，接向岗位所需的异步并发与结果一致性。

- [01 · 范围与完整骨架](01-scope.md)：在同一份完整代码中用①准备成员、②创建任务、③汇总结果、④评分交付标出边界；下方简表对照数据交接与阅读重点，正常路径先采用 group_rm=False。
- [02 · 本步函数记录](02-short-term-memory/overview.md)：组级父卡按四段配连续源码、短标记和紧邻解释；已有函数按交接需要回查。
- [03 · 前序累计记忆](03-long-term-memory/overview.md)：完整继承上一实际步骤；保留原话、未知、版本与来源。
- [04 · 理解形成过程](04-flow.md)：用户的范围确认、助手解释与后续反馈分别记录。

本步已收到用户对成员、任务与结果收集的初步表述，session、两种副本与评分分工已给源码校准，尚待反馈。现有函数卡和骨架不是完成状态；异常与取消按后续问题补充。下一候选是实际示例的 AsyncRolloutWorker._loop，尚未展开。不处理 Hugo；没有实际训练或 Agent 运行。

2026-10-26 用户随后确认继续，接到[下一步：Step 012 的持续调度](../step-012-async-rollout-worker-loop/README.md)。上文保留本步形成时的状态。
