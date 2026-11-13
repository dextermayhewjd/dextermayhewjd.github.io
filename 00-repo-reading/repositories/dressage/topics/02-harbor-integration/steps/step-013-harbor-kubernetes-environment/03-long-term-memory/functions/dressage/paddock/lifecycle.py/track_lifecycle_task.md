> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/02-short-term-memory/functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

# track_lifecycle_task

- 源码：[lifecycle.py:149–154](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L149)。
- 首次单独展开：Step 009，2026-11-08。
- 最近说明更新：2026-11-08；用户已概括按 Task 所属 loop 登记已有任务并添加 done 回调；具体回调内部仍仅按职责理解。

[来自 schedule_lifecycle_task](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/schedule_lifecycle_task.md) → **当前函数：保存已有 Task** → 返回原 Task。回收执行体与完成回调不在此时同步执行。

调用及返回位置见 [scope 3.2 阅读导航](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/01-scope.md#lifecycle-scheduling-relation)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：schedule_lifecycle_task 刚创建了回收 Task，需要保留它以免上层不保存句柄后失去集中管理入口。其他已有生命周期任务也可交给此函数登记。
2. **具体内容**：按 Task 所属的事件循环找出任务集合，加入该 Task，注册完成回调，再返回同一个 Task。
3. **建议构建的心智模型**：

   > 把正在安排执行的回收 Task 放进登记表，并约定它结束后从表里移除。

4. **调用代码**：

   ```python
   return track_lifecycle_task(asyncio.create_task(awaitable, name=name))
   ```

## 本场景的输入与输出

输入是已经创建的 Task；返回的还是它，没有复制、没有重新创建第二个 Task。副作用是登记表增加引用、Task 增加一个完成回调。

### 先看登记表保存在哪里

```python
# lifecycle.py 模块级变量，不属于某个 Paddock 实例。
_LIFECYCLE_TASKS: dict[
    asyncio.AbstractEventLoop,
    set[asyncio.Task[Any]],
] = {}
```

这份表是“事件循环 → 该循环的生命周期 Task 集合”，不是“session_id → sandbox”。集合是普通 set，不是 asyncio.TaskGroup；lifecycle 只是这类资源清理工作的命名。任务知道自己属于哪个 loop，使用 task.get_loop() 就能找到对应集合。

### 完整函数：存起来，登记完成回调，再交回

```python
def track_lifecycle_task(task: asyncio.Task[Any]) -> asyncio.Task[Any]:
    """Keep a background cleanup task alive until completion or shutdown."""
    tasks = _LIFECYCLE_TASKS.setdefault(task.get_loop(), set())
    # 没有这个 loop 的集合时就建立；tasks 指向表中保存的那个集合。
    tasks.add(task)  # 保存已有 Task 的强引用。
    task.add_done_callback(_discard_lifecycle_task)  # 等 Task 完成后再调用。
    return task  # 原对象返回，没有创建新的工作。
```

1. setdefault 确保该事件循环有任务集合；add 保存引用。
2. add_done_callback 只登记回调，此时不执行 _discard_lifecycle_task。Task 成功、异常或取消而结束，都会触发其完成回调。
3. _discard_lifecycle_task 的职责是移除该 Task（集合为空时再移除 loop 条目），读取结果并按源码处理异常；这里删除的是登记，不是再次删除沙箱。本轮先知道职责，不另开回调函数卡。

这不是轮询 Task 的状态，也不是重新启动回收。业务回收已经由上层 create_task 安排，track 负责的是对象引用与完成后的收束。

读完返回 [schedule_lifecycle_task](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/lifecycle.py/schedule_lifecycle_task.md)，再回到 schedule_terminate_paddock。至此可解释“任务已安排并被跟踪”；实际环境是否释放，还要看后台执行体。

<a id="discard-on-done"></a>

### 完成回调：从登记集合移除已结束的 Task

2026-11-09 接回已登记的 `_discard_lifecycle_task`，只看收束职责，不另开卡。此时 Task 已经结束，回调不是主动终止它。

```python
# _discard_lifecycle_task 的登记清理部分，lifecycle.py:228–233。
loop = task.get_loop()
tasks = _LIFECYCLE_TASKS.get(loop)
if tasks is not None:
    tasks.discard(task)  # 从普通 set 中移除这个 Task；不存在也不报错。
    if not tasks:
        _LIFECYCLE_TASKS.pop(loop, None)  # 集合空了，删掉 loop 对应的表项。
```

随后执行 `task.result()` 读取已完成任务的结果，不需要再等待：成功时不保留返回值；取消则忽略；普通异常记日志。不会再次运行任务，也不会关闭事件循环或再次释放沙箱。

至此主线是：create_task 创建 → track 保存引用并登记回调 → 后台任务执行 → done 回调移除引用、处理结果。超时后另行登记的 release_task 也在它自己完成时按同样规则收束，不会因为外层 Task 完成而被一并移除。

## 我的直接表述（原话）

> 那么再看一下这里的schedule和track的函数卡片吧

后续用户复述：

> 好的这里就是拿到了这个task loop之后考虑加入现有的这个task
> 然后加上一个done之后的hook是我的理解

助手核对：这个理解准确。task.get_loop() 取得已有 Task 所属的事件循环，以它为键取得或建立任务集合；添加的是已有 Task，不创建另一份任务。add_done_callback 注册完成回调，稍后任务完成时调用，并非登记时立即执行。

2026-11-09 用户进一步表示三个函数仍混淆，并追问 scope 执行图。补充校准：track 不创建或主动结束 Task；它只登记已有 Task。完成回调在 Task 结束后清除登记，不是结束 Task 的操作。完整原话见本步形成过程。

本轮对完成回调的概括：

> 好的 那么简单看一下这个吧
> 和之前的一样  就是把这个task 从group里面移除

助手核对：移除已结束 Task 的理解正确，group 在这里指普通 set 登记集合，不是 TaskGroup。另补充空集合清理和 task.result 的结果处理；用户是否理解异常细节不作推断。

## 尚不清楚

- 完成回调已简读移除登记和结果处理；drain_lifecycle_tasks 的集中等待仍只定位职责。
- 超时/取消后的释放任务跟踪见本步 terminate_paddock_best_effort 卡，具体远端释放按用户选择不深入。

<details>
<summary>来源与验证</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。核对 lifecycle.py:14–17、149–154、227–239。源码静态核对，未创建实际清理任务。

[Step 009 形成过程](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/04-flow.md#schedule-and-track)。

</details>
