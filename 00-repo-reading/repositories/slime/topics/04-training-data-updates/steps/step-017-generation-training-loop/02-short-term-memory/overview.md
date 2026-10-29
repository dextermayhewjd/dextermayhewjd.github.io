# 02 · Step 017 的短期记录

[本步 scope](../01-scope.md#reading-order) · [形成过程](../04-flow.md#step-017-opened)

| 记录 | 来源与本步用途 | 认识状态 |
| --- | --- | --- |
| **[RayTrainGroup.update_weights](functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md#training-finished-before-sync)** | 第三步两侧状态已整理；下一观察点回父卡 92–93 行的恢复条件 | 用户要求保存解释；恢复条件尚待带读，无新运行 |
| [RolloutManager.training_completed](functions/slime/ray/rollout.py/RolloutManager.training_completed.md) | 第二步停在职责层：收到完成通知，按需更新批次管理记录 | 用户暂按职责继续，内部保持未知 |
| [RayTrainGroup.async_train](functions/slime/ray/actor_group.py/RayTrainGroup.async_train.md) | 已读第一步；提交 worker 训练并返回结果引用列表 | 用户明确表示大概理解，未据此扩展为全部后端或失败细节已掌握 |
| [train](functions/train.py/train.md#weight-handoff) | 父函数组合：暂停新接纳 → 更新权重 → 按原状态恢复 | 用户已提出暂停接纳的初步理解；暂停粒度与 was_paused 的含义待反馈 |
| [BatchBuilder.split_by_dp](functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-return-refs) | 从本步 03 完整调取，回顾上一阶段交回的数据引用列表 | 保留 Step 016 原话、认识时间与未知；调取不表示新增理解 |
