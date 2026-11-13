> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/paddock/lifecycle.py/terminate_paddock_best_effort.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/terminate_paddock_best_effort.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/02-short-term-memory/functions/dressage/paddock/lifecycle.py/terminate_paddock_best_effort.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

# terminate_paddock_best_effort

- 源码：[lifecycle.py:49–77](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L49)。
- 首次单独展开：Step 009，2026-11-09。
- 本轮说明：先看实际释放的发起与限时等待；异常仅保留理解所需的去向，不扩展全部清理链。

[安排来源：schedule_terminate_paddock](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/schedule_terminate_paddock.md) → [schedule_lifecycle_task 创建外层 Task](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/schedule_lifecycle_task.md) → **该 Task 执行本函数** → 内层 release_task 调用 Paddock 的释放入口。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 已经安排了后台回收，本函数在那个被跟踪的外层 Task 中开始运行。
2. **具体内容**：取得等待时限，为真正调用 Paddock 创建 release_task，受保护地限时等待；若等待超时或本任务被取消，把 release_task 交给生命周期登记继续管理。普通调用错误只记录日志。
3. **建议构建的心智模型**：

   > 发起一次环境释放，限时等待；如果不能继续等，就保留并跟踪已经发出的释放任务，而不是因等待结束而放弃它。

   best_effort 不保证资源必定已释放，也不是不断重试。正常返回 None，不返回资源释放确认凭据。

4. **调用代码**（此前调度处）：

   ```python
   schedule_lifecycle_task(
       terminate_paddock_best_effort(
           paddock,
           session_id=session_id,
           env_args=dict(env_args),
       ),
       name=f"paddock-terminate:{session_id}",
   )
   ```

## 本场景的输入与输出

输入是本次 Paddock、session_id 和环境参数。session_id 在这里用于定位对应环境；不是再次请求 Proxy finalize。正常返回 None；对外最重要的是已发起释放，以及必要时留下持续被跟踪的内层任务。取消分支继续抛出 CancelledError，不伪装正常返回。

<a id="start-release-and-wait"></a>

### 1. 两个 Task 分别做什么

上层按源码直接传入回收协程，省略参数后是：

```python
schedule_lifecycle_task(
    terminate_paddock_best_effort(...),
    name=f"paddock-terminate:{session_id}",
)
```

进入 schedule_lifecycle_task 后，参数 awaitable 接住这个协程对象。该函数实际执行：

```python
return track_lifecycle_task(asyncio.create_task(awaitable, name=name))
```

因此这里创建的 Task 开始执行时，会进入当前函数体；当前函数内随后创建 release_task。此前图中的 cleanup_coro 是辅助说明的变量名，源码并无该名字，本轮已恢复原调用形状。参见 [scope 阅读导航第 2–6 项](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/01-scope.md#lifecycle-scheduling-relation)。

- **外层 Task**：前面 schedule_lifecycle_task 创建，已经由 track_lifecycle_task 保存；执行本函数，负责等待与交接。
- **内层 release_task**：本函数现在创建，负责真正调用释放接口。将实际调用单独放进 Task，外层停止等待时仍能留下它。

不是再次回收两遍，也不是从已有集合取出另一个旧 Task；这里只有一次新的 _call_paddock_terminate 调用。

### 2. 先看三行主干

以下为原函数主体节选，省略后面的 except 分支：

```python
timeout = terminate_timeout_sec()  # 默认等待 30 秒，可通过环境变量配置。
release_task = asyncio.create_task(
    _call_paddock_terminate(paddock, session_id, env_args)
)
await asyncio.wait_for(asyncio.shield(release_task), timeout=timeout)
```

**时间顺序校准：不是先等 30 秒再创建任务。** `terminate_timeout_sec()` 只读取并返回一个数值，不做 sleep；接着立即 create_task 安排释放，最后 wait_for 才开始等待。释放调用若 2 秒完成，就在约 2 秒时结束等待，不必等满 30 秒。

为什么要等待：释放通常包含异步调用，需要观察它是否完成或报错；当前是外层清理 Task 在等待，不是让已经返回的 generate 再等待一次。设时限则避免这个外层清理 Task 无限等下去；超时后继续保留内层释放工作。

1. create_task 安排实际释放调用，无需等外层再次 await 才创建这个任务。
2. wait_for 限制的是本函数的等待时长。
3. shield 隔开外层等待的取消传播，让它不因这次等待超时而自动取消 release_task；它不阻止别人直接取消内层任务。

例如等待时限 30 秒：释放调用 5 秒正常结束，本函数就结束；30 秒后仍未完成，则外层停止等待，把尚未结束的 release_task 留给登记机制。例子是行为说明，未真实执行。

### 3. 等待结束后，任务交给谁

| 情况 | 本函数的动作 | release_task 的去向 |
| --- | --- | --- |
| 释放调用正常返回 | 等待完成，本函数返回 None | 已完成；外层任务也完成，按已有回调清理外层登记 |
| 等待超时 | 记录日志，track_lifecycle_task(release_task)，本函数返回 None | 仍可运行，成为单独被跟踪的生命周期任务 |
| 本函数所在 Task 被取消 | track_lifecycle_task(release_task)，再抛出取消 | 不因外层等待被取消而被放弃；完成后由登记回调收束 |
| 释放调用抛普通异常 | 记录失败日志，本函数结束 | 失败结果已被接住；这里没有重试循环 |

超时/取消分支复用前面读过的 [track_lifecycle_task](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md)。外层 Task 结束后被移除登记，内层任务若尚未完成，则由自己的登记继续保留。

这与前面的 shell 命令超时有所不同：execute_shell_command 的超时分支会主动终止命令进程组；这里超时后不主动取消释放请求，而是让它继续。

### 4. 当前从哪里继续

<a id="call-paddock-terminate"></a>

下一跳 `_call_paddock_terminate`（lifecycle.py:216）很短，只作调用适配；就地理解即可，不单独开卡：

```python
async def _call_paddock_terminate(
    paddock: Any,
    session_id: str,
    env_args: dict[str, Any],
) -> Any:
    terminate = paddock.terminate
    if inspect.iscoroutinefunction(terminate):
        return await terminate(session_id, env_args)  # 异步实现：直接等待。
    return await maybe_await(await asyncio.to_thread(terminate, session_id, env_args))
    # 同步实现：放到线程执行；返回值若可等待，再等待它。
```

当前 BlackboxAgentPaddock.terminate 是 async def，因此走直接 await 分支。这里没有额外的沙箱删除算法，实际环境交接发生在 Paddock 的 terminate 中。

**本轮停止边界（2026-11-09 用户确认）：暂不继续下潜。** [BlackboxAgentPaddock.terminate:279](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L279) 只保留接口定位：按标识处理 state/lease，并委派 provider.terminate；具体释放实现不作为本轮下一张卡。随后接回 Task 完成与登记清理的关系。

正常释放返回后，本函数的等待完成；返回不是把结果重新交给已返回的 generate。它结束的是自己的外层后台 Task，由已注册的完成回调处理结果和登记。

**引用归属补充：** 正常路径中 release_task 由外层等待，并未单独加入 _LIFECYCLE_TASKS；等待超时或取消时才调用 track_lifecycle_task(release_task)。外层与内层的登记在各自结束时分别移除。

## 我的直接表述（原话）

> 好的那么现在堪舆ixia这个terminate paddock best effort把

用户明确进入本函数；此前已大致理解创建、登记和 done 回调。

随后用户表述：

> 好的 我差不多理解了
> 简单来说就是先等30秒? 为什么要等
> 然后在创建这个task这个task call paddock terminate的task
> 然后如果没有成功的话 记录下这里的asyncio的原因是我的理解

助手校准：先取等待上限，再创建并安排释放 Task，最后限时等待；不是先延迟 30 秒。超时只说明尚未在时限内完成，记录超时并继续跟踪内层任务；取消时跟踪内层任务并继续抛出取消；释放调用抛普通异常时记录错误。不能把三者统称为失败后记录 asyncio 原因。

## 尚不清楚

- Paddock terminate 如何查回环境记录并委派 provider，尚未逐段阅读。
- 事件循环关闭、集中 drain 与外部直接取消内层任务的完整处理，本轮不展开。

<details>
<summary>完整源码与验证来源</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。主函数 49–77，等待时限配置 30–46，调用适配 216–224。仅静态核对，未运行回收或删除环境。

```python
async def terminate_paddock_best_effort(
    paddock: Any,
    *,
    session_id: str,
    env_args: dict[str, Any],
) -> None:
    timeout = terminate_timeout_sec()
    release_task = asyncio.create_task(
        _call_paddock_terminate(paddock, session_id, env_args)
    )
    try:
        await asyncio.wait_for(asyncio.shield(release_task), timeout=timeout)
    except asyncio.CancelledError:
        track_lifecycle_task(release_task)
        raise
    except asyncio.TimeoutError:
        logger.warning(
            "timed out waiting for sandbox release RPC for session_id=%s "
            "after %.3fs; release continues in background",
            session_id,
            timeout,
        )
        track_lifecycle_task(release_task)
    except Exception as exc:
        logger.warning(
            "failed to terminate sandbox for session_id=%s: %s",
            session_id,
            exception_summary(exc),
        )

```

形成过程：[Step 009](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/04-flow.md#terminate-best-effort)。

</details>
