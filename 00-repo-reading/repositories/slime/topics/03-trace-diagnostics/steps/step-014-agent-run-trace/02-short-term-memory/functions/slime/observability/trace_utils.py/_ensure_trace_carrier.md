# _ensure_trace_carrier

> 当前调用链：[_coerce_handles](_coerce_handles.md) → [bind_trace](bind_trace.md) → **_ensure_trace_carrier**。读完返回 bind_trace:240，接住返回字典。

- 源码定位：[trace_utils.py:213–235](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L213-L235)，固定版本 18868a79。
- 首次接触：2026-10-27，Step 014 的 trace 字典准备回查。
- 最近认识更新：尚无本函数的独立理解确认；本卡从已有绑定说明拆出。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手核对源码后整理。

1. **使用场合**：bind_trace 要给 sample.trace 赋值，需要先得到字段齐备的追踪字典。
2. **具体内容**：输入为 None 时创建字典，否则复用原字典；补齐字段并返回。已有 events 列表会保留。
3. **建议构建的心智模型**：

   > 准备保存追踪数据的字典，再交回调用者。这里不创建 TraceHandle，也不追加本阶段的事件。

4. **调用代码**（bind_trace:240–244）：

   ```python
   sample.trace = _ensure_trace_carrier(
       getattr(sample, "trace", None),
       sample_id=sample.index,
       group_id=sample.group_index,
   )
   ```

## 本场景的输入与输出

| 输入 | 本次来源 |
| --- | --- |
| carrier | sample 原有的 trace；取不到时为 None |
| sample_id、group_id | sample.index、sample.group_index |
| trace_id、attempt | 调用方未显式传入，使用默认值 None、0 |

输出：准备好的字典。输入字典不为 None 时返回同一对象；输入为 None 时返回新字典。调用方随后将它赋给 sample.trace。

### 本函数怎样准备字典

以下保留本函数体（221–235），参数定义见源码入口：

```python
if carrier is None:
    carrier = {}
carrier.setdefault("version", TRACE_VERSION)
carrier.setdefault("trace_id", trace_id or _new_trace_id())
carrier.setdefault("events", [])
if sample_id is not None:
    carrier["sample_id"] = sample_id
else:
    carrier.setdefault("sample_id", None)
if group_id is not None:
    carrier["group_id"] = group_id
else:
    carrier.setdefault("group_id", None)
carrier["attempt"] = int(carrier.get("attempt", attempt))
return carrier
```

- version、trace_id、events 缺失时补入；已有值保留。events 已存在时不会被重置为空列表。
- 传入非 None 的 sample_id、group_id 时更新对应字段；否则保留旧值或补 None。
- attempt 取已有值或默认值，并转换为 int。

**返回上一层**：[bind_trace 的赋值处](bind_trace.md)接住 carrier，然后创建 TraceHandle。本函数的工作到 return carrier 就结束。

## 我的直接表述（原话）

尚无对本函数的独立复述。用户当前要求分层看清调用关系，不能将本页源码说明视为已掌握。

## 尚不清楚

- None 与已有字典两条路径、已有字段的保留和更新，尚待用户阅读反馈。
- 本轮只定位 _new_trace_id 的用途，不展开标识生成实现。

<details>
<summary>来源、验证与完整例子</summary>

- [固定源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L213-L235)。
- [本次分层整理](../../../../../04-flow.md#step014-function-layers)。只做静态核对，未运行真实 Agent；返回对象关系以源码为依据。

</details>
