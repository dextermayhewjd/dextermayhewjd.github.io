# Step 013 · 完成的组结果怎样交给消费方

[主题入口](../../README.md) · [前一步](../step-012-async-rollout-worker-loop/README.md) · [唯一进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

Step 012 关注持续取组、创建并登记 Task、回收与等待。本步沿已注册的完成回调接下去：一组 Task 完成后，结果怎样进入 output_queue，又怎样被上层按需取走。

本步主读 _make_done_cb 与 get_completed_groups 两个 worker 方法。后者由 _generate_rollout_async 调用；用户已确认增加[父函数卡](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md)，保留整体骨架并重点展开接收、过滤与收集，完整位置见 [scope 3.1](01-scope.md#overall-position)。

- [01 · 范围、完整骨架与阅读入口](01-scope.md)：同一主题内的新交接问题，先看正常完成路径。
- [02 · 本步记录](02-short-term-memory/overview.md)：两个 worker 方法卡、收集父函数卡及其 call_dynamic_filter 子卡；上一阶段的 _loop 与精简 worker 类卡作为背景调取。
- [03 · 前序累计记录](03-long-term-memory/overview.md)：完整继承 Step 012 的 03 + 02，共 62 份记录，含 3 份历史空白占位。
- [04 · 理解形成过程](04-flow.md)：范围确认、第一观察点及后续反馈。
- [05 · 任务链路总结](05-task-flow.md)：后台入队、上层领取、过滤收集与本轮收束。

首个观察点是同一行中的两个动作：先执行 _make_done_cb 得到一个函数，再把这个函数交给 add_done_callback。用户随后已表达正常完成 Task 的结果入队，并指出队列属于 worker、存在重试分支；具体核对与仍未展开的部分见 04。这些局部理解不等于整个步骤已掌握。

继续选择本地 AsyncRolloutWorker 分支。默认 straw 的分布式实现仍是另一条路径；失败、中止重试、线程协调与队列持久化本轮暂不展开。不处理 Hugo。

2026-10-26 本轮首轮范围已收束，完整交接见 05；各卡片中的个人表述与未知继续保留。后续入口以唯一路线为准。

后续已进入[主题 03 · Trace 与运行诊断](../../../03-trace-diagnostics/README.md)的 Step 014，围绕单个 agent_run span；本步首轮快照保留。
