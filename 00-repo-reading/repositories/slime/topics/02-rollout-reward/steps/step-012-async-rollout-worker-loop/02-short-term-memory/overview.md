# 02 · Step 012 本步函数记录

[阅读范围](../01-scope.md) · [前序累计记录](../03-long-term-memory/overview.md)

| 源码 | 记录 | 本步用途与状态 |
| --- | --- | --- |
| slime/rollout/fully_async_rollout.py | [AsyncRolloutWorker._loop](functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md) | 本步入口；初始化与完成项移除已有初步反馈，Task 登记、状态和轮询关系待校准 |
| slime/rollout/sglang_rollout.py | [generate_and_rm_group](functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md) | 调取完整组级记录，作为本层子调用 |
| slime/rollout/sglang_rollout.py | [GenerateState](classes/slime/rollout/sglang_rollout.py/GenerateState.md) | 调取共享状态与采样参数背景，保留原认识与未知 |
| slime/rollout/fully_async_rollout.py | [AsyncRolloutWorker 类卡](classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md) | 当前对象接口与最短输入来路；完整字段和协调实现放参考，暂不展开 |
