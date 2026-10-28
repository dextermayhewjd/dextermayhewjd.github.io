# Step 012 · 多组生成任务怎样持续运行

[主题入口](../../README.md) · [前一步](../step-011-generate-and-rm-group/README.md) · [后续 Step 013](../step-013-completed-group-handoff/README.md) · [唯一进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

前一步已有“一组输入 → 多个单次生成 → 按位置收齐”的模型。本步按用户确认，进入本地 AsyncRolloutWorker._loop，围绕持续取组、在途任务集合、结果积压与完成后补充建立外层调度模型。

- [01 · 阅读范围与完整骨架](01-scope.md)：同一代码块内保留初始化、回收、接纳与等待；先从接纳新组进入。
- [02 · 本步函数记录](02-short-term-memory/overview.md)：父函数逐段配源码、标记与紧邻解释；AsyncRolloutWorker 类卡只保留当前接口、最短输入来路；完整字段与暂停协议按需回查；调取组级函数与 GenerateState。
- [03 · 前序累计记录](03-long-term-memory/overview.md)：继承前一步完整 03 + 02，共 60 份记录，含 3 份历史空白占位。
- [04 · 理解形成过程](04-flow.md)：范围确认、分支边界、源码证据及后续反馈。

本步明确选择本地 worker。当前 Coding Agent 示例默认 straw，选择分布式实现；此差别在 scope 与函数卡中标明，后续再接对应关系。函数卡初稿不代表用户已经理解内部机制；源码版本沿用 18868a79。
