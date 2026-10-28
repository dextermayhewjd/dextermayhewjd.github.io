# 02 · Step 013 本步函数记录

[阅读范围](../01-scope.md) · [前序累计记录](../03-long-term-memory/overview.md)

| 记录 | 本步用途 | 认识状态 |
| --- | --- | --- |
| [AsyncRolloutWorker._make_done_cb（含内部 _cb）](functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._make_done_cb.md) | [①创建并返回回调](functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._make_done_cb.md#phase-1)；[②执行 _cb、处理结果](functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._make_done_cb.md#phase-2) | 已讨论；用户已复述正常结果入队，具体未知仍保留在卡片中 |
| [AsyncRolloutWorker.get_completed_groups](functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.get_completed_groups.md) | 第三步：按需取走已完成的组，遇空返回 | 用户已表示理解，并提出“节流器”类比；本轮补充按次领取上限与生成侧背压的区别 |
| [_generate_rollout_async](functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md) | 第四步父卡：[接收、过滤与收集](functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md#collect-filter-retain)，其余阶段保留骨架 | 已确认建卡；用户已说明结果来路，分支、计数与最终交付由助手整理，尚待具体阅读反馈 |
| [call_dynamic_filter](functions/slime/rollout/filter_hub/base_types.py/call_dynamic_filter.md) | 第四步内回查：已有奖励统计 → 调用过滤器 → 统一返回判定 | 用户已概括为实现筛选；统一接口的作用与运行效率分开，三段机制的具体理解仍待反馈 |
| [AsyncRolloutWorker._loop](functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md) | 背景调取：前一步的注册点与任务集合 | 保留原认识、原话与未知，不重新展开整段循环 |
| [AsyncRolloutWorker 类卡](classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md) | 背景调取：认出同一个 output_queue 及对象接口 | 保留精简版与历史来源，不增加字段前置 |

新增卡片首次独立阅读在 Step 013；此前定位与每份卡片原有认识时间均在卡片开头保留。任务交接关系见 scope，本页只做索引。
