> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/paddock/lifecycle.py/schedule_terminate_paddock.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/02-short-term-memory/functions/dressage/paddock/lifecycle.py/schedule_terminate_paddock.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

# schedule_terminate_paddock

- 源码：[dressage/paddock/lifecycle.py:175–188](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L175)。
- 首次单独展开：Step 009，2026-11-08。
- 最近说明更新：2026-11-08；本轮先看正常成功路径上的回收安排。

[来自 generate 的 finally](../../rollout/generate/blackbox_dispatch.py/generate.md#normal-return) → **本函数：安排回收** → schedule_lifecycle_task 创建并跟踪任务 → 正常返回 generate；后台释放还可能继续运行。

调用及返回位置见 [scope 3.2 阅读导航](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/01-scope.md#lifecycle-scheduling-relation)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 正常完成任务与 Proxy 收尾，准备返回 Sample 列表；环境已初始化，需要安排回收。
2. **具体内容**：把 Paddock、会话 ID 和环境参数副本交给 terminate_paddock_best_effort，形成待运行的协程，再交由 schedule_lifecycle_task 调度和跟踪。
3. **建议构建的心智模型**：

   > 把这次沙箱的回收交给一个会被跟踪的后台任务，然后让 generate 继续返回结果。

   安排成功不等于远端资源已经删除；完整释放行为留到后台函数阅读。

4. **调用代码**（generate:407–412）：

   ```python
   if initialized and paddock is not None:
       schedule_terminate_paddock(
           paddock,
           session_id=session_id,
           env_args=env_args,
       )
   ```

## 本场景的输入与输出

### 为什么现在先看它，而不是 discard_session_context

当前是已成功执行 Proxy finalize 的正常路径：context_owned=False，所以不会进入 `_discard_session_context`。该 helper 处理尚由本调用负责的 Proxy 会话上下文，与释放沙箱不同；失败或取消发生在此前时，再回查这条分支。

initialized=True 且 paddock 非 None，因而当前路径实际进入本函数。输入仍是本次执行使用的 Paddock、session_id 和 env_args，不是新建一个环境。

### 完整函数：组装回收任务并提交

```python
def schedule_terminate_paddock(
    paddock: Any,
    *,
    session_id: str,
    env_args: dict[str, Any],
) -> None:
    schedule_lifecycle_task(
        # 这是 async 函数调用，先产生协程对象，随后交给调度器执行。
        terminate_paddock_best_effort(
            paddock,
            session_id=session_id,
            env_args=dict(env_args),  # 浅拷贝参数字典，供后台任务使用。
        ),
        name=f"paddock-terminate:{session_id}",
    )
```

schedule_lifecycle_task 内部使用 asyncio.create_task，并把创建的 Task 交给 track_lifecycle_task 登记。本函数没有 await，也不把 Task 返回给调用者；正常返回 None。下层 schedule_lifecycle_task 返回的是 Task，只是本函数没有接住它；不要把 None 标到下层函数。实际回收结果不在此时交付，任务可能仍在进行。

读完本函数后有两条不同的线：

- **generate 的正常返回线**：这次安排完成，finally 正常结束，Sample 列表交给外部调用者。
- **后台回收线**：继续执行 terminate_paddock_best_effort，最终委派 Paddock 的 terminate。调度、跟踪和等待边界后续按问题逐段看。

本轮已进入 [schedule_lifecycle_task](schedule_lifecycle_task.md) 与 [track_lifecycle_task](track_lifecycle_task.md)，弄清 Task 的创建、保存和完成回调。本轮已接续 [terminate_paddock_best_effort](terminate_paddock_best_effort.md)，先看实际释放与限时等待；不扩大到所有取消分支。

## 我的直接表述（原话）

> 我知道的
> 那么这里看一下吧
> 关于这里的这个discard session context还有还是这里的schedule terminate apddock?

根据当前正常路径选择本函数。

后续用户概括：

> 好的 那么这里就是schedule life cycle task的内容
> 然后考虑使用terminate paddock best effort来直接让paddock 中纸雕这个session对吗?

助手校准：调度器安排 terminate_paddock_best_effort 执行，后者委派 Paddock 回收这个 session_id 关联的环境。当前 BlackboxAgentPaddock.terminate 会按该标识取出并移除 state/lease 登记，再调用 provider.terminate；不只是清除一个 Proxy 会话编号，也不代表调用调度器时已经删除成功。

## 尚不清楚

- 后台 Task 如何保存、何时移除或集中等待。
- 释放请求超时与取消时怎样保留回收工作。
- context_owned=True 的路径如何完成会话清理，留到失败/取消路径。

<details>
<summary>来源与验证</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 调用处：blackbox_dispatch.py:407–412；责任标记更新：:304。
- lifecycle.py:166–173 创建/登记后台任务；:49–77 为后台执行体。仅核对接口交接，未完整带读。
- 静态核对，未调用清理方法、终止任务或删除资源。
- [Step 009 形成过程](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/04-flow.md#schedule-terminate-entry)。

</details>
