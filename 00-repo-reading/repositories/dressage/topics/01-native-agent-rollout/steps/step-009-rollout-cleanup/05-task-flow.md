# 05 · Step 009：返回 Sample，同时安排并跟踪环境回收

> generate 准备返回已有 Sample 列表，在 finally 中安排后台回收；调度器创建并登记 Task，后台执行体发起释放并限时等待，已结束的 Task 由完成回调移除登记。

[本步 scope](01-scope.md) · [函数记录](02-short-term-memory/overview.md) · [形成过程](04-flow.md#close-step009) · [项目唯一进度](../../../../README.md)

## 1. 本步在任务中的位置

Step 008 已把本次轨迹段转换为 Sample 列表 result。本轮选择 Proxy finalize 已成功、环境已初始化的正常返回路径：context_owned=False、initialized=True 且 paddock 存在。

generate 的 return result 不跳过 finally。当前无需再次清理 Proxy 会话上下文，但需要安排当前环境回收。普通失败、完整取消路径与具体 provider 释放，按本轮用户选择保留回查，未逐项深入。

## 2. 已读部分怎样完成交接

沿用本轮认可的结构图：显示调用归属，标出后台执行和完成回调；不把每一个返回值画成额外节点。

```python
generate 的 finally
└─ schedule_terminate_paddock(...)  # 准备回收协程、参数和名称。
   └─ schedule_lifecycle_task(...)
      ├─ asyncio.create_task(...)  # 为传入的回收协程创建 Task。
      │  └─ [后台执行] terminate_paddock_best_effort(...)
      │       # 创建 release_task，发起实际释放并限时等待。
      └─ track_lifecycle_task(...)  # 登记上面创建的同一个 Task。
         └─ [完成回调] _discard_lifecycle_task(...)
              # 已结束的 Task 从集合移除，并读取结果。
```

图为关系示意，不是逐行运行代码。正常同步调用按以下交接完成：

- [schedule_terminate_paddock](02-short-term-memory/functions/dressage/paddock/lifecycle.py/schedule_terminate_paddock.md) 把 terminate_paddock_best_effort(...) 返回的协程直接传入通用调度器。源码没有 cleanup_coro 这个变量。
- [schedule_lifecycle_task](02-short-term-memory/functions/dressage/paddock/lifecycle.py/schedule_lifecycle_task.md) 创建 Task，再交给 [track_lifecycle_task](02-short-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md) 保存。登记表按 loop 区分普通 set 集合，不是 TaskGroup。
- track 和调度器返回同一个 Task；最外层不接这个值，正常返回 None。generate 的 finally 正常结束后交回原 result，无需等待远端资源实际释放。

后台执行与调用者返回分开理解：

- [terminate_paddock_best_effort](02-short-term-memory/functions/dressage/paddock/lifecycle.py/terminate_paddock_best_effort.md) 在已创建的外层 Task 中运行，内部再创建 release_task 调用 _call_paddock_terminate。两个 Task 分工不同，不是重复释放两次。
- timeout 默认 30 秒，可配置；它是发起释放后的等待上限，不是启动延迟。wait_for/shield 限制外层等待，同时避免因这次超时自动取消内层释放。
- 释放调用正常完成，外层任务结束。等待超时或外层被取消时，内层 release_task 单独交给 track 登记；外层取消仍继续传播。普通释放异常记录日志，不是自动重试。
- [已在 track 卡中简读的完成回调](02-short-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md#discard-on-done) 由事件循环触发：移除结束的 Task；对应集合空了，再移除 loop 条目；读取结果并记录普通异常。这个动作不关闭 loop，也不再次删除沙箱。

## 3. 本步结果与资源状态怎样区分

| 观察点 | 能得出的结论 |
| --- | --- |
| schedule_terminate_paddock 正常返回 | 回收任务已安排，不能据此断言资源已删除 |
| generate 的 finally 正常结束 | 原 Sample 列表可以交回外部；后台清理可能仍在进行 |
| 外层 Task 完成 | 等待和处理已结束；若曾超时，内层释放仍可能单独运行 |
| 某个 Task 的 done 回调执行 | 该 Task 已结束，其登记可以移除；并非其他 Task 一并结束 |

源码表明调用会交给 Paddock/provider，但本轮没有实际运行远端释放，也没有验证所有资源都已删除。实际释放接口按职责理解，保持用户确认的停止边界。

## 4. 首轮收束与下一范围

2026-11-09 用户表示大致理解并询问是否结束。本轮正常回收主线已覆盖创建、登记、执行、限时等待与完成收束，适合结束首轮阅读。

仍保留的回查项：

- _discard_session_context 与 generate 普通失败/取消出口的完整协作。
- drain_lifecycle_tasks 的集中等待及进程/事件循环退出时的运行治理。
- Paddock/provider 具体释放实现与真实集群验证。

这些未深入部分不记作已掌握。最初 scope 还计划完整追踪取消案例；本轮按用户后来明确的主线优先与不下潜选择收束，取消仅解释到释放等待处的必要语义。

下一范围是 [Step 010：Dressage 的 Harbor 批量入口](../../../02-harbor-integration/steps/step-010-harbor-rollout-entry/01-scope.md)。这里只提供入口，不自动开始新的主题或创建未读函数卡。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- generate:349–412；lifecycle.py:49–77、149–188、216–239。
- 核心对应：schedule_terminate_paddock → schedule_lifecycle_task → track_lifecycle_task；Task 运行 terminate_paddock_best_effort；完成回调 _discard_lifecycle_task。
- 仅静态源码与笔记导航核对；未启动真实清理、删除沙箱或验证集群资源。
- 大致理解、结构图认可和文档检查，不等于全部取消/回收机制已掌握。

</details>
