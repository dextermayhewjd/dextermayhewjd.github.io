# ensure_blackbox_session_id

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../step-005-agent-registration/03-long-term-memory/functions/dressage/rollout/prewarm/store.py/ensure_blackbox_session_id.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

- 源码定位：[store.py:22](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L22)。
- 首次单独展开：Step 001，2026-11-05；此前已在 generate 骨架中出现。
- 最近认识更新：Step 001，2026-11-05；用户概括其为创建 session ID，复用语义由助手补充。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 准备任务身份时，为当前 sample 确定 blackbox 会话 ID，后续用于预热领取等关联。
2. **具体内容**：优先取 metadata 中的确定性 ID，并按重试计数添加后缀；否则复用 sample.session_id，缺失时生成 UUID。统一字符串与 bbs- 前缀，写回 sample 并返回。
3. **建议构建的心智模型**：

   > 确定并保存这份 sample 的会话编号。这里准备关联标识，不创建沙箱，也不启动 Proxy 会话。

4. **调用代码**（generate:138–141，真实连续代码）：

   ```python
   session_id = ensure_blackbox_session_id(sample)
   instance_id = _instance_id(sample)
   metadata["session_id"] = session_id
   metadata["instance_id"] = instance_id
   ```

## 本场景的输入与输出

教学输入：sample.metadata 为 {"dressage_deterministic_session_id": "task-7", "dressage_retry_count": 2}，sample.session_id 原为 "old"。

输出：返回 "bbs-task-7-retry-2"，并令 sample.session_id 等于同一字符串。确定性 ID 优先于旧属性。metadata["session_id"] 由调用者随后写入，不是本函数写入。

完整函数源码：

```python
def ensure_blackbox_session_id(sample: Any) -> str:
    """Ensure *sample* has a ``bbs-`` prefixed session ID and return it."""
    metadata = getattr(sample, "metadata", None)
    deterministic_session_id = (
        metadata.get("dressage_deterministic_session_id")
        if isinstance(metadata, dict)
        else None
    )
    if isinstance(deterministic_session_id, str):
        retry_count = int(metadata.get("dressage_retry_count", 0))
        session_id = deterministic_session_id
        if retry_count:
            session_id = f"{session_id}-retry-{retry_count}"
    else:
        session_id = getattr(sample, "session_id", None)
        if session_id is None:
            session_id = str(uuid.uuid4())
    session_id = str(session_id)
    if not session_id.startswith("bbs-"):
        session_id = f"bbs-{session_id}"
    sample.session_id = session_id
    return session_id

```

按执行顺序读：

1. 取 sample.metadata；只有它是 dict 时才查询 dressage_deterministic_session_id。
2. 该值为字符串时，以它为基础。读取 dressage_retry_count，默认 0；非零时追加 -retry-N。此分支不会优先采用已有 sample.session_id。
3. 否则读取 sample.session_id；仅在它为 None 时生成 UUID。已有非 None 的值会保留，再转成字符串。
4. 将结果转为字符串；尚无 bbs- 前缀时才添加，避免重复加前缀。
5. 写回 sample.session_id，再返回同一个值，供 generate 的局部变量接住。

补充静态例子：无确定性 ID 且 sample.session_id 为 "abc" 时得到 "bbs-abc"；已有 "bbs-abc" 时保持不变；两处都无可用 ID 时得到 "bbs-<新 UUID>"。同样的确定性 ID 与重试计数会重建相同编号，不会不断追加重试后缀。

读完返回 generate:139，下一处是 _instance_id(sample)。两个 ID 的关系留到下一函数再核对，不在这里提前展开。

## 我的直接表述（原话）

用户本轮表述：

> 简单的来说就是创造session id
> 别的没有了
> 那么我们继续吧

助手补充：更准确是确保并保存 session ID，也可能复用已有值；该补充尚未得到用户单独确认。

## 尚不清楚

- 确定性 ID 和重试计数具体由谁写入，本轮未展开。
- instance_id 与 session_id 的关系，留待下一处阅读。
- 预热领取如何使用这个编号，属于 Step 002。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮核对源码工作区干净。
- 本地源码：/home/fredkeira/projects/Dressage/dressage/rollout/prewarm/store.py:22–43。
- 调用者：dressage/rollout/generate/blackbox_dispatch.py:138–141。
- 例子为静态推导；未运行 Agent、沙箱或训练。
- [本轮过程](../../../../../../../step-001-task-identity-and-parameters/04-flow.md)。

</details>
