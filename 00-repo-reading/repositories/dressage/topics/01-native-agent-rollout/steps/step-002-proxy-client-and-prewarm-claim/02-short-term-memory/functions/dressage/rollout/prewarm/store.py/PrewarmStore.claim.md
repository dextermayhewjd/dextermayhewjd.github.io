# PrewarmStore.claim

- 源码定位：[store.py:115](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L115)。
- 首次单独展开：Step 002，2026-11-06。
- 最近认识更新：2026-11-06，用户已串联 start 保存 Task、claim 取回并等待的关系；助手补充等待“初始化完成”，不只是确认“已经启动”。本轮精简不新增掌握判断。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 通过 claim_prewarm，按当前 session_id 领取提前准备的环境。
2. **具体内容**：取走预热记录，等待其中的初始化 Task，成功后返回 PrewarmHandle。
3. **建议构建的心智模型**：

   > start 先把初始化工作存成记录；claim 取回这项工作，等到结果，再交出环境使用资料。

4. **调用代码**（claim_prewarm 内）：

   ```python
   return await _DEFAULT_STORE.claim(session_id)
   ```

## 本场景的输入与输出

**输入**：session_id="bbs-demo"；同一个 store 中已有对应 record，里面保存 paddock、env_args 和初始化 Task。

**输出**：Task 成功后返回 handle，含 session_id、group_id、paddock、state 和 env_args。无记录或普通初始化异常返回 None；取消则安排清理并继续抛出取消异常。

### 完整源码

```python
async def claim(self, session_id: str | None) -> PrewarmHandle | None:
    """Atomically transfer one ready prewarm to active rollout ownership."""
    if session_id is None:
        return None
    record = self._take(session_id)
    if record is None:
        return None
    try:
        state = await record.task
    except asyncio.CancelledError:
        self._schedule_dispose(record)
        raise
    except Exception as exc:
        logger.warning(
            "sandbox prewarm failed for session_id=%s: %s; "
            "falling back to inline init",
            session_id,
            exception_summary(exc),
        )
        return None
    return PrewarmHandle(
        session_id=record.session_id,
        group_id=record.group_id,
        paddock=record.paddock,
        state=state,
        env_args=copy.deepcopy(record.env_args),
    )
```

### 按三个动作读

1. **取记录**：_take 从 _records 取出并移除对应项，同时更新组索引。取出的是 Python 记录，不是 Pod 或容器。
2. **等结果**：await record.task 等待 start 已经创建的初始化 Task，取得它返回的 state；已完成就直接取结果，不会再启动一次初始化。
3. **交资料**：把 state 与原记录的身份、paddock、环境参数一起放入 [PrewarmHandle](../../../../../classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md) 返回；env_args 在这里做深拷贝。

**返回调用者**：generate 有 handle 就取出环境资料继续注册；得到 None 则走按需初始化路径。普通异常返回 None 不等于这里已经完成所有底层资源清理。

<a id="prewarm-origin"></a>

### 需要时回查

| 问题 | 去哪里看 |
| --- | --- |
| record.task 在哪里创建、存入？ | [PrewarmStore.start](PrewarmStore.start.md)：第 99 行创建 Task，第 100–106 行写入记录；看完回到本卡的 await |
| 谁在 generate 之前启动预热？ | [Step 000 的上游关系](../../../../../../../step-000-slime-bridge-and-interfaces/01-scope.md#prewarm-upstream)；[原有详细追踪](../../../../../../references/history/prewarmstore-claim-before-trim-2026-11-06.md#prewarm-origin) |
| 初始化根据什么判断环境可用？ | [BlackboxAgentPaddock.init](../../../../../../../step-004-paddock-environment-preparation/02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md)：provider 返回、取得服务端点、默认执行健康检查，再返回 state |
| handle 如何在 generate 中使用？ | [调用者的环境取得段](../../generate/blackbox_dispatch.py/generate.md#environment-init) |

## 我的直接表述（原话）

本轮串联的原话节选：

> 并且创建一个task
> 然后把这里的一系列内容全部都放到这里的这个records里面
> 作为一个prewarmRecord
> 这里存放的是一个task
> 所以在后续的内容中才会需要通过await的方式

完整表述见 [start 卡](PrewarmStore.start.md)；更早关于 record、Pod 和远端就绪的追问保留在[精简前记录](../../../../../../references/history/prewarmstore-claim-before-trim-2026-11-06.md)。助手对“启动”和“完成”的校准尚待用户进一步确认。

## 尚不清楚

- 预取容量、并发预算和不同运行模式的完整调度策略。
- 取消及初始化失败时，底层资源释放的完整链路。

<details>
<summary>来源、验证与历史记录</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；源码为 store.py 的 start、claim、_take 及 PrewarmHandle，调用者为 generate:182–242。
- 输入情境是教学构造，仅静态核对，没有运行真实环境。
- [原始讨论](../../../../../../04-flow.md)；[精简前完整快照](../../../../../../references/history/prewarmstore-claim-before-trim-2026-11-06.md)保留全部原话、扩展说明和原来源。
- 本次只精简当前函数卡，不修改其他步骤的记忆快照。

</details>
