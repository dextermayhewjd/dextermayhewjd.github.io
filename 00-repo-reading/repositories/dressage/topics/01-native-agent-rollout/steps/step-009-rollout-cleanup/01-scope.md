# 01 · Dressage Step 009：generate 返回与取消时谁回收资源

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一阶段范围](../step-008-segments-to-samples/01-scope.md) · [后续规划](../../../../references/topics-and-step-scopes-after-step006.md)

> 状态：2026-11-09，本轮按用户后续收紧的范围完成正常回收主线的首轮阅读。具体释放和完整失败/取消路径保留回查，见[任务链路总结](05-task-flow.md)。

## 1. 阅读目标

**把原生 generate 的正常返回、普通失败和取消出口与清理责任接起来，收束单任务闭环。**

1. 区分正常 result、普通失败的 ABORTED sample 和继续向外传播的取消。
2. 用 context_owned、initialized、paddock 判断哪些清理仍由当前调用负责。
3. 区分安排回收、后台 RPC 仍在进行和实际资源已释放。

## 2. 指挥官、入口与停止位置

指挥官是 [generate:349–412](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L349)。正常路径接住上一阶段的 result；失败/取消路径沿用已有对象、会话标识与责任标记。本轮先读成功返回与后台释放的必要等待语义；原拟跟踪的完整取消案例，按用户后续选择保留为回查，不作为本轮已读内容。

**停止在能够列清返回物和清理所有者，并说明后台释放任务怎样被跟踪。** 不把调用 schedule_terminate_paddock 当作已证明远端环境被删除；真实回收状态要靠后续运行证据。本步结束只表示原生路线阅读范围收束。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在原生任务中的位置

下面是正常路径的教学骨架，省略参数、日志和大部分失败包装。它保留整个原生任务的位置；Step 编号表示阅读范围，不表示并发执行顺序。

```python
session_id = ensure_blackbox_session_id(...)
instance_id = _instance_id(...)
env_args = paddock_env_args_from_metadata(...)
initialized = False
paddock = None
try:
    proxy_client = get_proxy_client(...)
    handle = await claim_prewarm(...)
    ...  # 此图选择预热未命中路径，身份更新等细节折叠。
    paddock = get_paddock_from_env(...)
    state = await maybe_await(paddock.init(...))
    initialized = True

    await maybe_await(paddock.register_agent(...))
    await execute_blackbox_cmds_for_stage(...)  # before_agent
    ...  # 按接口能力登记 Proxy 会话，记录 context_owned。
    call_payload = await maybe_await(paddock.call_agent(...))
    agent_response = agent_response_text(call_payload)
    ...  # Step 006：执行结果的结构化失败检查。

    # Step 007：执行后置命令，给 Proxy 会话收尾并取得轨迹。
    await execute_blackbox_cmds_for_stage(...)  # after_agent
    await proxy_client.finalize_session(...)
    context_owned = False
    trajectory_payload = await proxy_client.read_trajectory(...)

    # Step 008：从轨迹中取段，形成 Sample 列表。
    segments = trajectory_payload.get("data") or []
    result = multi_segment.expand_segments_to_samples(...)
    return result  # return 交回调用方之前仍要执行 finally。
finally:
    # Step 009（本步）：处理尚未释放的会话责任，并安排环境回收。
    try:
        if context_owned:
            await _discard_session_context(...)
    finally:
        if initialized and paddock is not None:
            schedule_terminate_paddock(...)
```

普通失败和取消的分支在 Step 009 单独定位；此图不是可直接执行的完整函数。

<a id="reading-navigation"></a>

### 3.2 本步调用骨架与阅读顺序

本轮正常主线已读至第 **7** 项并首轮收束，复习见 [05-task-flow](05-task-flow.md)。以下保留原阅读导航；具体 Paddock/provider 释放与集中 drain 未深入。

<a id="lifecycle-scheduling-relation"></a>

图中编号与阅读表一一对应：按 **1 → 2 → 3 → 4 → 5 → 6 → 7** 阅读，缩进用于看清调用归属。第 6 项挂在创建它的第 3 项下，第 7 项挂在注册它的第 4 项下。

```python
[1] generate：进入 finally
├─ [2] schedule_terminate_paddock(...)  # 传入回收协程与任务名称。
│  └─ [3] schedule_lifecycle_task(...)  # awaitable 接收第 2 项传入的协程。
│     ├─ asyncio.create_task(awaitable, name=name)
│     │  └─ [6] [后台执行] terminate_paddock_best_effort(...)
│     │       # 这是上面创建的 Task 所执行的函数；发起释放并限时等待。
│     │       └─ _call_paddock_terminate(...)  # 释放接口，本轮不再下潜。
│     └─ [4] track_lifecycle_task(...)  # 保存第 3 项创建的 Task。
│          └─ task.add_done_callback(_discard_lifecycle_task)
│               └─ [7] [完成后触发] _discard_lifecycle_task(...)
│                    # 第 6 项所在 Task 完成后，移除登记、处理结果。
└─ [5] 回到 generate  # 第 2 项返回、finally 正常结束，交回 Sample 列表。
```

| 阅读顺序与入口 | 从哪里进入 | 读完接到哪里 |
| --- | --- | --- |
| 1. generate：finally | [generate 卡](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#normal-return)，源码 :407–412 | 从回收调用进入第 2 项 |
| 2. schedule_terminate_paddock | [本函数卡](02-short-term-memory/functions/dressage/paddock/lifecycle.py/schedule_terminate_paddock.md)，lifecycle.py:175 | 将 terminate_paddock_best_effort(...) 产生的协程传给第 3 项的 awaitable 参数 |
| 3. schedule_lifecycle_task | [本函数卡](02-short-term-memory/functions/dressage/paddock/lifecycle.py/schedule_lifecycle_task.md)，lifecycle.py:166 | 创建 Task 后，进入第 4 项登记 |
| 4. track_lifecycle_task | [本函数卡](02-short-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md)，lifecycle.py:149 | 沿调用返回第 3 → 2 项，再接回第 5 项 generate |
| 5. 回到 generate | [generate 卡](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#normal-return) | 确认 finally 正常结束后交回 result；阅读转到已创建 Task 的执行体，即第 6 项 |
| 6. terminate_paddock_best_effort | [本函数卡](02-short-term-memory/functions/dressage/paddock/lifecycle.py/terminate_paddock_best_effort.md#start-release-and-wait)，lifecycle.py:49 | 从第 3 项的 create_task 切入执行体；看释放等待，本任务完成后触发第 7 项 |
| <a id="current-reading"></a>**7. _discard_lifecycle_task · 本轮停止位置** | [track 卡的完成回调段](02-short-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md#discard-on-done)，lifecycle.py:227 | 看登记收束；本轮正常主线到此停止 |

第 5 → 6 项是切换阅读对象，不表示后台执行必须等到 generate 返回才开始。

<details>
<summary>其他路径：只保留回查入口</summary>

| 要回查什么 | 入口 |
| --- | --- |
| 普通失败与取消出口 | [generate:350–388](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L350) |
| 未收尾的 Proxy 会话上下文 | [generate:396](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L396) → [_discard_session_context:71](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L71) |
| 释放等待超时或取消 | [terminate_paddock_best_effort 卡](02-short-term-memory/functions/dressage/paddock/lifecycle.py/terminate_paddock_best_effort.md) |
| 集中等待清理任务 | [drain_lifecycle_tasks:191](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L191) |

</details>

<details>
<summary>源码与证据边界</summary>

- 固定版本：Dressage `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 主要位置：generate:349–412、_discard_session_context:71–112；lifecycle.py:49–77、149–209。环境创建中取消的补偿路径先保留已有来源，除非所选案例需要，不继续扩成第二条完整案例。
- 本步已开始正常返回路径的静态阅读；未运行 Agent、模型、HTTP 请求或清理实验，不表示相关函数已经读懂。
- 已完整继承前一步并调取 generate 当前片段；未读 helper 不建卡，已生成首轮任务总结；未读分支不计为已掌握。

</details>
