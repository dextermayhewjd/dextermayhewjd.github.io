> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md) 完整继承；不改变原认识时间或掌握状态。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# PrewarmStore.start

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

- 源码定位：[store.py:78–113](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L78)。
- 首次定位：Step 002 的预热来源回查；2026-11-06 本轮单独展开并建卡。
- 最近认识更新：Step 002，2026-11-06；用户已串联创建 Task、登记 record 与后续等待，助手校准“启动”和“完成”的区别。

[从 claim 回查](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.claim.md#prewarm-origin) → 本页 start → [回到 claim 的等待处](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.claim.md)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：在任务进入 blackbox_dispatch.generate 之前，预热调度器要求为某份 sample 提前初始化环境。当前只回查记录怎样产生，不展开整个调度器。
2. **具体内容**：确保会话 ID，拒绝重复记录，复制环境参数，创建执行 paddock.init 的异步 Task，将它与身份/配置存入 _PrewarmRecord，并登记组索引。
3. **建议构建的心智模型**：

   > start 发起初始化并记账，claim 以后取账并等待结果。record.task 正是 start 创建后放进去的 Task；它不是由 _take 或 session_id 生成的。

4. **调用代码**（同文件 start_prewarm 包装函数）：

   ```python
   return _DEFAULT_STORE.start(
       sample,
       group_id=group_id,
       paddock=paddock,
       env_args=env_args,
   )
   ```

   上游 [PrewarmScheduler._prefetch_and_prewarm:121](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/scheduler.py#L121)调用 start_prewarm；后续 claim_prewarm 调用的是同一个 _DEFAULT_STORE.claim。

## 本场景的输入与输出

教学场景：一份 sample 已带 session_id="bbs-demo"，metadata 可提供 env_type；group_id=2，已有 paddock 对象，env_args 是该环境所需参数。store 中尚无该 ID。

- 返回："bbs-demo"。此返回只说明已创建并登记初始化任务，不表示环境已准备好。
- 状态变化：sample.session_id 得到确认；self._records["bbs-demo"] 保存记录，记录的 task 字段指向下面创建的 Task；self._group_sessions[2] 包含 "bbs-demo"。
- 若该 ID 已在记录中：返回 None，不重复创建 Task。

### 完整函数：先定义工作，再调度和登记

```python
def start(
    self,
    sample: Any,
    *,
    group_id: int,
    paddock: Any,
    env_args: dict[str, Any],
) -> str | None:
    """Start and own one sandbox prewarm, or reject a duplicate session."""
    session_id = ensure_blackbox_session_id(sample)
    if session_id in self._records:
        return None
    metadata = getattr(sample, "metadata", None)
    env_type = metadata.get("env_type") if isinstance(metadata, dict) else None
    owned_env_args = copy.deepcopy(env_args)

    async def _initialize() -> Any:
        return await maybe_await(
            paddock.init(session_id, env_type, owned_env_args)
        )

    task = asyncio.create_task(_initialize(), name=f"prewarm:{session_id}")
    self._records[session_id] = _PrewarmRecord(
        session_id=session_id,
        group_id=group_id,
        paddock=paddock,
        env_args=owned_env_args,
        task=task,
    )
    self._group_sessions.setdefault(group_id, set()).add(session_id)
    logger.debug(
        "sandbox prewarm started for session_id=%s group_id=%d",
        session_id,
        group_id,
    )
    return session_id
```

1. **87–92 行：准备任务身份与参数。** env_type 来自 metadata，owned_env_args 是输入参数的深拷贝。
2. **94–97 行：定义内部协程 _initialize。** 这只是定义待执行的工作；它的工作是调用并等待 paddock.init，最终返回初始化结果 state。
3. **99 行：创建 Task。** 调用 _initialize() 得到协程对象，再由 asyncio.create_task 调度运行。start 自身没有在这里等待它完成。
4. **100–106 行：将同一个 Task 存入记录。** 左边 self._records[session_id] 是存放位置；右边 task=task 把刚创建的对象放入 _PrewarmRecord.task。
5. **107–113 行：登记组归属并返回 ID。** 初始化随后由事件循环推进；远端完成条件由 paddock.init 和 provider 负责。

### 返回 claim：读的是同一条记录和同一个 Task

下面分别来自同文件 _take 与 claim，是跨函数对照，不是一段原始连续代码：

```python
# _take：取出 start 之前登记的记录
record = self._records.pop(session_id, None)

# claim：在 record 存在时，等待其 Task 的结果
state = await record.task
```

record.task 与 start 中的局部变量 task 指向同一个 Task。_initialize 正常返回 state 后，等待方取得该结果，随后构造 PrewarmHandle。当前回查到这条数据交接即可；不用先通读整个 rollout worker。

## 我的直接表述（原话）

本轮问题节选：

> 这个信息又是哪里来的呢?
> 我这里只有看到的一个_take和一个session id
> 这个预热的部分在哪里发生的呢?

此前曾说明仍不理解 record.task 如何反映远端环境就绪，完整追问保存在原始过程记录。这里不将源码说明代写成用户理解。

本轮后续表述：

> 好的 我简单理解为这个store 在调用start的过程中也会给出基础的一系列星系
> 然后这个paddock初始化的内容放在这里
> 并且创建一个task
> 然后把这里的一系列内容全部都放到这里的这个records里面
> 作为一个prewarmRecord
> 这里存放的是一个task
> 所以在后续的内容中才会需要通过await的方式
> 因为我也不知道这里 是否有没有被正常的启动?
> 是我的理解
> 同时这里的这个claim的部分是怎么回这里的start中的task联系在一起的 我目前也是理解

助手校准：用户已串联 start 创建初始化 Task、将它与身份/参数放入 _PrewarmRecord、后续领取同一记录的关系。create_task 已将协程提交给事件循环调度；await 不是只确认是否启动，而是等待初始化正常完成并取回 state，失败或取消则抛出对应异常。记录存在不能代表初始化已完成。start 写入和 _take 取出使用同一个 store 的 _records 与同一 session_id，record.task 指向原来的 Task。

## 尚不清楚

- Task 的启动与成功完成已由助手进一步区分，尚待用户对该区别的确认。
- 调度器如何选择预热组数、协调并发和资源预算，仍按后续阅读安排。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 同文件：_PrewarmRecord:58；start:78；claim:115；_take:186；模块默认 store:198；start_prewarm:201；claim_prewarm:217。
- 静态源码核对，示例状态为教学构造；没有运行远端环境。
- [原始讨论](../../../../../../../../../01-native-agent-rollout/steps/step-002-proxy-client-and-prewarm-claim/04-flow.md)。

</details>
