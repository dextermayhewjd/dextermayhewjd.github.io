> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/paddock/lifecycle.py/schedule_lifecycle_task.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/schedule_lifecycle_task.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/02-short-term-memory/functions/dressage/paddock/lifecycle.py/schedule_lifecycle_task.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

# schedule_lifecycle_task

- 源码：[lifecycle.py:166–172](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L166)。
- 首次单独展开：Step 009，2026-11-08。
- 最近说明更新：2026-11-08；本轮读创建 Task 与登记的交接，未执行实际资源回收。

[来自 schedule_terminate_paddock](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/schedule_terminate_paddock.md) → **当前函数：创建并登记 Task** → [track_lifecycle_task](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md) → 返回同一个 Task 给调用方。

调用及返回位置见 [scope 3.2 阅读导航](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/01-scope.md#lifecycle-scheduling-relation)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：上层已经提供 `terminate_paddock_best_effort(...)` 产生的协程对象，希望回收在后台进行。
2. **具体内容**：用 asyncio.create_task 创建并命名 Task，立刻交给 track_lifecycle_task 保存和登记完成回调，返回这个 Task。
3. **建议构建的心智模型**：

   > 把待执行的回收协程安排成 Task，并把它登记好，交回任务句柄。

4. **调用代码**（schedule_terminate_paddock 内）：

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

输入是待执行的回收协程对象和任务名称；不是已经释放的环境，也不是环境的返回结果。正常输出是新创建的 asyncio.Task。

**图中的 cleanup_coro 是什么：** 只是为拆解嵌套表达式而补出的临时变量名，源码没有这个名字。它表示 terminate_paddock_best_effort(...) 返回的协程对象；本函数用参数 awaitable 接住该对象，不是再调用一个名为 cleanup_coro 的函数。

**与后续执行图的连接：** 本次 awaitable 正是 terminate_paddock_best_effort(...) 产生的协程。create_task(awaitable) 返回的这个 Task 之后执行的就是该协程体；执行图里的“外层 task”与本函数创建、交给 track 的 task 是同一个对象。

完整函数，仅增加注释：

```python
def schedule_lifecycle_task(
    awaitable: Awaitable[Any],
    *,
    name: str,
) -> asyncio.Task[Any]:
    """Create and strongly track one background lifecycle operation."""
    # 先创建 Task，再把同一个 Task 交给 track 登记，最后返回它。
    return track_lifecycle_task(asyncio.create_task(awaitable, name=name))
```

阅读时可把最后一行等价展开为两步（局部变量 task 是教学展开，原函数没有这个赋值）：

```python
task = asyncio.create_task(awaitable, name=name)
return track_lifecycle_task(task)
```

这是普通同步函数调用的嵌套：先执行 create_task，再调用 track，最后返回。track 没有再包一层后台任务；name 用于给创建的 Task 命名，不决定它的执行逻辑。

create_task 将协程安排到当前运行的事件循环，后续不必靠调用方再 await 才开始执行。这里的后台不是新建一个操作系统进程或线程；本函数不等待回收工作结束。

为什么还要 track：上层 schedule_terminate_paddock 没有保存这个返回 Task，所以共享登记负责保留引用，供完成后的移除和需要时的集中等待。登记不能让任务在事件循环或进程已经关闭后继续运行。

读完进入 [track_lifecycle_task](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md)，看同一个 Task 被存在哪里；返回本函数后，Task 被交回 schedule_terminate_paddock，而后者正常返回 None 给 generate。

## 我的直接表述（原话）

> 那么再看一下这里的schedule和track的函数卡片吧

本轮明确要求阅读这两个函数；尚无对 create_task 与跟踪关系的独立复述。

## 尚不清楚

- Task 内部怎样发起、等待实际释放，由 terminate_paddock_best_effort 接续。
- 事件循环退出时如何集中等待后台工作，当前不展开。

<details>
<summary>来源与验证</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。静态核对 lifecycle.py:149–188，未调用后台回收或删除环境。

[Step 009 形成过程](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/04-flow.md#schedule-and-track)。

</details>
