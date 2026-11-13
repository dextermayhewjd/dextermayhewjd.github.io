# 02 · Step 017 的短期记录

[本步 scope](../01-scope.md#reading-order) · [形成过程](../04-flow.md#step-017-opened) · [任务链路总结](../05-task-flow.md)

| 记录 | 来源与本步用途 | 认识状态 |
| --- | --- | --- |
| [RolloutManager.eval](functions/slime/ray/rollout.py/RolloutManager.eval.md#mental-model) | 周期评估入口：取得评估数据、按配置保存并记录结果 | 用户已直接概括本步所需职责；评分等内部实现未展开，没有真实运行 |
| [RolloutManager.resume_rollout_admission](functions/slime/ray/rollout.py/RolloutManager.resume_rollout_admission.md#mental-model) | 权重同步后下一入口：按原状态恢复新任务接纳 | 用户表示大概理解当前职责；调度和异常细节仍保留边界 |
| [RolloutManager.pause_rollout_admission](functions/slime/ray/rollout.py/RolloutManager.pause_rollout_admission.md#mental-model) | 第三步的暂停接口：请求、确认和返回原状态 | 用户明确表示当前心智模型已理解；实现细节与真实运行边界保留 |
| [AsyncRolloutWorker._loop](functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md#phase-3) | 从本步 03 完整调取，回查 not self.paused 如何控制取组与创建任务 | 保留 Step 012 的原话、日期与未知；本轮补证据，不视为重新掌握全部循环 |
| [RayTrainGroup.update_weights](functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md#mental-model) | 已读职责：Megatron 向生成侧同步已有新权重 | 用户已概括发送方向；内部等待、返回与外层恢复已提醒，底层实现未展开 |
| [RolloutManager.training_completed](functions/slime/ray/rollout.py/RolloutManager.training_completed.md#mental-model) | 第二步已采用分层伪代码版：转交通知、核对批次、更新消费记录 | 用户已概括分层转交及本批数据已用过的登记；物理回收与其他精确边界保留待反馈 |
| [RayTrainGroup.async_train](functions/slime/ray/actor_group.py/RayTrainGroup.async_train.md#remote-return-versus-train-return) | 第一段回顾已给出总体反馈；读完回 train 的等待和完成通知 | 用户表示差不多理解整合模型并要求继续；精确 API 用法未单独检验，其他未知保留 |
| [train](functions/train.py/train.md#whole-loop-restatement-20261101) | 整体回顾：数据来路到训练、发布及周期评估 | 2026-11-01 已连贯复述主线；通知发起者、发布含义和恢复条件的精确校准保留，未新增运行 |
| [BatchBuilder.split_by_dp](functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-return-refs) | 从本步 03 完整调取，回顾上一阶段交回的数据引用列表 | 保留 Step 016 原话、认识时间与未知；调取不表示新增理解 |
