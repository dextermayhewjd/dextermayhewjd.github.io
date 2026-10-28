# straw 队列调度与腾讯混元岗位：阅读价值及边界

[返回选读目录](README.md) · [岗位依据](../../../../slime_photo/code-reading/job-alignment.md) · [唯一进度](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

记录日期：2026-10-28。本文件是选题评估，未创建新阅读 step；不将候选函数记为已经读懂。

## 用户要求与结论

用户要求将整个 Step 014 暂时停止研究，Trace 留待以后；随后提供 straw 队列调度文档的 diff，询问它是否对应腾讯混元 Agent 强化学习框架岗位。

**结论：适合作为下一处候选，优先研究 Slime Python 层的任务领取、归还与跨 worker 续跑。** 最直接对应 JD 第 1 条并发编程和第 5 条模块化、测试、性能与稳定性；也覆盖第 2 条的任务执行、上下文交接，以及第 4 条的一部分 RL 数据链路。无需由此扩展为通读 straw 存储引擎或完整分布式训练系统。

这接续了此前的 group 生成、AsyncRolloutWorker、完成结果交付与 queue context 阅读。已有生成/评分函数继续承担计算，当前新增问题是：谁分配任务、未完成的工作存在哪里、换一个 worker 后如何继续。

## 版本边界

- 用户粘贴的改动与本地 Git 历史中的 `89bfada990a00663846e0ac804de1454685ceed3` 一致，对应 [PR #2426](https://github.com/THUDM/slime/pull/2426)，2026-09-28 合并。已在线核对 PR 身份和合并记录，并从本地历史定位相关文档变更。
- 当前阅读 checkout 为 `/home/hongshi/projects/slime`，HEAD `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本轮工作区干净。下面的行号均属于这个版本。没有更新或修改 Slime checkout。
- 用户随后追问本地是否已经更新。再次运行 `git merge-base --is-ancestor 89bfada990a00663846e0ac804de1454685ceed3 HEAD`，返回成功，确认本地已经包含该 PR。2026-10-28 实时 `git ls-remote` 得到官方 HEAD/main 为 `540ea919e45b8b929198abce008a103be9cfc779`，与本地 HEAD 不同。本地已包含粘贴改动，与是否对齐此刻远端最新引用是两个判断；本轮没有 fetch、pull 或改动 checkout。
- 当前模块为 `slime/data/queue_data_source.py`，默认内存源为 `slime/data/data_source.py`；粘贴差异中的 `slime/rollout/queue_data_source.py` 是历史路径。
- 当前中文指南和代码已包含 dataset cursor checkpoint 及选择旧 checkpoint 的恢复处理。不能继续把这份旧 diff 中“游标尚未保存、任意旧 step 回退尚未实现”当作当前结论。当前恢复也不意味着恢复 GPU KV cache 或生成 RNG，参见 [当前恢复说明](/home/hongshi/projects/slime/docs/zh/advanced/straw.md:77)。
- 旧文档中的 256 MiB pack 默认值和 PyPI 0.1.0 限制也不是本轮安装建议；当前文档已经更新。调度学习无需先展开安装、pack 大小或底层存储调优。

## 这次改变解决什么问题

```text
worker A 的 QueueReader
  └─ get_samples：领取一个 group，带上本次 lease
       └─ 原来的生成/评分逻辑：得到完整结果或未完成的前缀
            └─ add_samples：发布可续跑的数据，归还任务
                 └─ 共享持久队列中的 pending 任务
                      └─ worker B 的 QueueReader.get_samples
                           └─ 同一工作的新 lease，接回保存的前缀
```

重点是任务归属与生命周期改变：归还的 continuation 不再只能由原 reader 的本地 buffer 再次取得。QueueReader 本地仍维护正在执行的 lease；调度器也仍有有界的结果窗口。因此“去掉 reader 的 continuation buffer”不等于“所有本地队列都消失”。

Ray 仍承载 actor、调度和 RPC；straw 提供持久队列与共享数据引用。默认 object-store 与 straw 是传输/数据管理方式的选择，不是“使用 Ray”和“不使用 Ray”的二选一。同步与 fully async 执行方式也需分别配置。

## 对照用户提供的 JD

| 要求 | 对应程度 | 本段能具体练习什么 | 边界 |
| --- | --- | --- | --- |
| 1. Python、Asyncio、并发与工程实践 | 高 | get_samples_async 如何把阻塞 RPC/文件读取放入专用执行器；后台续租与本地 lease 状态的同步；任务与结果的有界管理 | 需看实际异步接入，单读队列文档不等于具备并发开发能力 |
| 2. Agent 的模型/工具/上下文/任务/Trace/评估链路 | 对任务执行与上下文交接直接相关 | 一个 prompt group 的领取、部分结果、重新领取、完成交付；解释 Sample 上 queue context 的来源和用途 | 不包含模型协议、工具实现、对话上下文管理的全部内容，也不替代暂停的 Trace 学习 |
| 3. Kubernetes 与容器化、集群部署排障 | 间接相关 | 建立 worker 故障、共享存储与执行进程的边界认识，为以后集群排障提供应用语义 | Ray actor 与持久队列的阅读不能替代实际 Pod 部署、资源、网络及重启排障 |
| 4. 了解至少一类训练或自动化评估流程 | 部分相关 | 了解 rollout 的 partial/completed、新旧生成策略版本、采样到训练的数据交接；区分调度排序与样本淘汰 | 不需要由此追加 PPO、所有 loss、模型并行或优化器恢复的通读 |
| 5. 模块化、测试、日志、性能和稳定性 | 最直接 | get/add 接口稳定而内部从本地 buffer 转为共享队列；lease/attempt 的有效性；丢回复、换 worker、保存失败等测试；引用传递与重复搬运的取舍 | 第一轮只选择一个具体失败边界，WAL 与 GC 内部暂作接口 |
| 6. 问题解决、协作与 owner 意识 | 适合作为练习载体 | 说明为什么移除本地 buffer、哪些消费者受影响、如何保持接口并验证迁移 | 阅读 PR 无法证明协作与 owner 能力，需要自己完成一个改动、测试或问题复现 |

加分项中，这属于强化学习框架经验的素材；只有实际借助 AI 工具实现/核对，才构成相应工具使用经验。无需为了“跨语言”加分项立即下钻 straw 的 Rust 实现。

## 建议的第一轮范围

本轮候选问题：**一个未完成的 group 如何归还到共享队列，再被另一位 worker 继续处理？**

1. 先看 [QueueReader.get_samples](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1050) 的输入输出，定位从 controller 领取引用、加载 group、附加 lease；配套 [get_samples_async](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1102) 解释为何不会让阻塞读取占住事件循环。
2. 再看 [QueueReader.add_samples](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1106)，只跟可用 partial 的正常归还路径。需要解释原子交接时回查 [RolloutQueueController.return_groups](/home/hongshi/projects/slime/slime/data/queue_data_source.py:388)，把外部 yield_tasks 的事务能力先当作接口约定。
3. 用 [test_returned_partial_is_available_to_another_reader](/home/hongshi/projects/slime/tests/test_distributed_rollout.py:337) 对照行为：A 归还后不再保留本地 buffer/lease，B 取得相同 token 前缀与新 attempt。再选择 [test_lost_return_reply_preserves_one_pending_task](/home/hongshi/projects/slime/tests/test_distributed_rollout.py:390) 看一次回复丢失边界。

上层定位只需知道 [_GenerationActor](/home/hongshi/projects/slime/slime/rollout/fully_async_distributed.py:256) 从 reader_config.open 创建 reader，并用异步接口取组；它是分布式路径的执行者，不把它误称为前面读过的本地 AsyncRolloutWorker。生成/奖励和完整分布式调度循环继续沿用已有职责认识。

第一轮记录可以是一张 QueueReader 职责/状态卡、get/add 的成对输入输出与一条跨 worker 交接图。QueueDataSource 的 job 级 reader/consumer/checkpoint 职责先定位；复杂 R3/SC 续跑、存储所有权图、GC、WAL 内部和完整 checkpoint 回滚另按问题展开。

## 随后按需补充

- 续租与失效：[_heartbeat_loop](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1029)，解释旧 attempt 失效、关闭/失联后的任务处置；不承诺推理绝不重复执行。
- 排序策略：[test_queue_orders_stage_then_staleness_then_fifo](/home/hongshi/projects/slime/tests/test_distributed_rollout.py:357)。先按 completed delivery、partial、fresh 分层，同层按最旧数值型权重版本再按 FIFO；staleness 排序不自动淘汰样本，不能把它解释成奖励过滤。
- 训练交接：需要时再回到 BatchBuilder 的输入输出；当前仅评估队列生命周期，不添加完整训练子系统要求。

## 证据与状态

本轮读取了固定源码中的 QueueReader、QueueDataSource、controller 的领取/归还接口、默认数据源选择、分布式 worker 接入口及相关测试。测试代码作为行为规范参照，**本轮未运行这些测试**，也未执行 worker 故障、共享文件系统或 GPU 训练实验。

Step 014 已按用户要求暂缓；上述是下一步候选范围，不因保存本文件自动开始新的 step 或认定任何机制已经掌握。实际状态只在唯一路线维护。
