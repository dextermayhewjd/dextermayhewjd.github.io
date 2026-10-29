# 02 · Step 016 的短期记录

[本步范围与阅读编号](../01-scope.md#reading-order) · [形成过程](../../step-016-sample-to-train-data/04-flow.md#first-field-assembly)

| 记录 | 来源与本步用途 | 认识状态 |
| --- | --- | --- |
| [BatchBuilder.convert](functions/slime/data/batch_builder.py/BatchBuilder.convert.md#response-loss-mask) | 基础字段拼装之后，简读响应 mask 的补齐、检查、屏蔽与收集 | 用户已理解基本字段，并初步关联 mask 与 response；mask 规则的具体反馈待补 |
| [BatchBuilder.split_by_dp](functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-eight-samples) | 沿用 A–H 计划接清字段选择、微批安排、张量准备与引用返回 | 用户确认样本、配套字段和微批安排一同交给 Ray 的职责，反馈“大概理解”；后续训练消费未展开，未运行 Ray |
| [build_dp_schedule · 配置、微批与 DP 索引计划](functions/slime/utils/dp_schedule.py/build_dp_schedule.md#schedule-flow) | 将并行配置和样本归属转成微批及 rank 分配；完整概念回查 reference | 用户已能概括样本分配职责；校准为按 DP 副本制定计划，建议返回父函数连接实际字段与返回引用，未开启新 Step |
| [BatchBuilder._post_process_rewards](functions/slime/data/batch_builder.py/BatchBuilder._post_process_rewards.md) | 算法、开关与返回奖励对照，rollout 去重及映射 | 用户明确反馈“差不多理解了”，要求保存并返回父函数 |
| [Sample](classes/slime/utils/types.py/Sample.md) | 从本步 03 完整调取；沿用已有字段视图 | 保留原认识时间、原话与未知；调取不代表新增掌握 |
| [RolloutManager._generate](functions/slime/ray/rollout.py/RolloutManager._generate.md) | 保留此前的上层回查；generate 与 begin 的短分支仅作调用方背景 | 本轮静态定位交接；尚无用户对实现的直接表述 |

奖励后处理、DP 交接与固定调度例子已建立独立方法卡；动态装箱、负载均衡、传输和训练消费内部继续作为边界。
