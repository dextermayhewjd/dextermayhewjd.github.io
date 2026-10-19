# 第 5 章 并发、任务数据、背压与恢复

[阅读路线](../../repo-reading-route.md) · [总目录](../../README.md)

**目录 ID：** `05-concurrency-recovery`
**产物状态：** planned
**学习状态：** 统一见[阅读路线的当前接续](../../repo-reading-route.md#当前接续)。

**问题：** 怎样持续处理慢任务、控制积压，并在取消、重启和部分失败后保持结果与任务身份一致？

**前置：** 03、04；知道组级输出合同与验证方式。

**图文对照：** 7.7、4.5、4.6；6.2 为独立服务对照。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 持续运行的生成工作者 | [slime/rollout/fully_async_rollout.py · AsyncRolloutWorker](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_rollout.py#L78) | explain | 本地池的任务、完成队列与暂停；先读 _get_worker 分支，持久化 reader_config 模式还需 DistributedRollout。 |
| 批次生成与取消 | [slime/rollout/sglang_rollout.py · generate_rollout_async](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L476) | trace | 区分线程中的事件循环、进程/Ray 调度和服务端生成请求的取消。 |
| 持久化分布式生成 | [slime/rollout/fully_async_distributed.py · DistributedRollout.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L474) | trace | 从 _get_worker 的 reader_config 分支进入；每节点 worker、局部池、全局 demand/prefetch 与 worker 恢复。 |
| 任务领取与确认 | [slime/data/queue_data_source.py · QueueReader.get_samples](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L1068)、[slime/data/queue_data_source.py · RolloutQueueController.take](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L488)、[slime/data/queue_data_source.py · RolloutQueueController.complete](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L563) | trace | task、lease、result_ref 与 receipt；结果 accepted、训练 completed、checkpoint committed 分开理解。 |
| 任务数据源 | [slime/data/queue_data_source.py · QueueDataSource](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L1292) | trace | 这是 job-level reader/checkpoint 包装；具体租约与确认在 QueueReader/RolloutQueueController，外部 straw 语义另行核对。 |
| 结果打包与共享存储 | [slime/data/transport.py · pack_rollout_payload](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/transport.py#L350) | trace | Ray object-store 与 straw 数据引用两种路径；完成确认、接受批次和持久化 checkpoint 不等价。 |
| 共同清理预算 | [slime/utils/cleanup.py · Cleanup](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/cleanup.py#L9) | explain | 每项清理使用剩余时间；清理工具不是通用强制中断器。 |
| 恢复计划 | [slime/data/checkpoint.py · resolve_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L237) | locate | 先辨认数据进度与模型/优化器状态的共同恢复边界，再看恢复实现。 |

**章内顺序：**

1. 先看 GenerateState.semaphore、generation_pacer 与 _get_worker；再比较本地 AsyncRolloutWorker 和持久化 DistributedRollout 两条任务池，解释并发上限、启动节奏和各自的队列背压。
2. 追一个正常组、一个 ABORTED 组和一个超时请求；记录排队、重入、结果接受和资源释放。
3. 对照 data_source.py、QueueReader、RolloutQueueController 与 transport.py；区分 prompt buffer、租约、持久化结果、批次接受和训练消费确认。
4. 读 tests/test_fully_async_rollout.py 和恢复测试，提出慢任务、满队列、取消、服务重启与重复结果的行为验证。
5. 第二遍对照 slime_plugins/rollout_buffer/README.md：它是独立 HTTP Rollout Buffer 服务，不能与 trajectory.py 或主链数据队列混为一谈。

**验收问题：** 暂停生成和取消请求有什么区别？任务完成、结果已收集、训练已消费和 checkpoint 已提交有哪些不同？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](../../repo-reading-route.md#当前接续)。
