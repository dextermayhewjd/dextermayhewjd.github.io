# _append_event

> 当前调用链：[trace_span 的开始记录](trace_span.md#span-records) → **_append_event**。返回后继续 trace_span:381 保存配对，再在 382 准备上下文条目。

- 源码定位：[trace_utils.py:587–613](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L587-L613)，固定版本 18868a79。
- 首次接触：Step 014 已定位事件写入，本轮因用户明确要求仔细理解而独立展开。
- 最近认识更新：2026-10-27，用户概括为通过 handle 追加内容，并追问完整结构；type 的归属与字段层级尚待澄清。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手按固定源码整理。

1. **使用场合**：trace_span 已经确定记录目标与阶段编号，需要实际写入一条开始事件；同一个工具也供结束事件等调用使用。
2. **具体内容**：把调用方提供的类型、名称、时间、阶段编号等信息和 handle 携带的身份信息组装成字典，追加到 carrier["events"]，再返回这个字典。
3. **建议构建的心智模型**：

   > 写一条事件的工具：组装 event → 放进目标的事件列表 → 返回 event。它使用上层已经给出的 span_id，不负责生成编号或管理整个阶段。

4. **调用代码**（trace_span:372–380）：

   ```python
   _append_event(
       handle,
       kind="span_start",
       name=name,
       timestamp=timestamp,
       span_id=span_id,
       parent_span_id=parent_span_id,
       attrs=attrs,
   )
   ```

## 本场景的输入与输出

本轮只跟随 agent_run 的开始事件。下列 T1、S1、S0、10.0 为教学值，与 [trace_span 卡](trace_span.md#runtime-start-yield) 一致；实际编号与时间由运行时产生，未运行真实 Agent。

**先分清数据层级**：[TraceHandle 结构卡](../../../../classes/slime/observability/trace_utils.py/TraceHandle.md)列全六个声明字段及 carrier/event 的结构。这里的 type 是 event 字典的键；本函数不向 handle 增加字段。

| 输入 | 本场景的含义 |
| --- | --- |
| handle | 已从 handles 中取出的一个 TraceHandle；carrier 指向本次写入的追踪字典 |
| kind、name、timestamp | "span_start"、"agent_run"、开始时间 |
| span_id | 上层已生成的本阶段编号 S1 |
| parent_span_id | 上层确定的父阶段编号；示例取 S0，无父阶段时可以为 None |
| attrs | 调用方提供的附加属性；当前 agent_run 调用未传，默认为 None |

输出有两部分：**向 handle.carrier["events"] 追加一条字典**，并且 **return 这个 event 字典**。当前 trace_span 开始记录处没有变量接收返回值，依靠的是列表已经被追加这一副作用。

### ① 组装基本字段

源码 597–605：

```python
event = {
    "type": kind,
    "name": name,
    "ts": timestamp,
    "trace_id": handle.trace_id,
    "sample_id": handle.sample_id,
    "group_id": handle.group_id,
    "attempt": int(handle.carrier.get("attempt", handle.attempt)),
}
```

类型、名称、时间由调用方给出；trace_id 等身份信息从 handle 取得。这一段先在本函数里创建字典，还没写进事件列表。

### ② 补充可选字段，再实际写入

源码 606–613：

```python
if span_id is not None:
    event["span_id"] = span_id
if parent_span_id is not None:
    event["parent_span_id"] = parent_span_id
if attrs:
    event["attrs"] = dict(attrs)
handle.carrier["events"].append(event)
return event
```

当前调用提供了 span_id，所以会写入 S1；父阶段编号存在时也写入。attrs 为 None 时没有 attrs 字段。最后两行才把字典放入目标列表，并交回调用者。

本次输出事件的完整字段（attrs 为 None，未加入）：

```python
{
    "type": "span_start",
    "name": "agent_run",
    "ts": 10.0,
    "trace_id": "T1",
    "sample_id": 7,
    "group_id": 2,
    "attempt": 0,
    "span_id": "S1",
    "parent_span_id": "S0",
}
```

**读完返回**：[trace_span:381](trace_span.md#span-records) 接着把 (handle, span_id) 存入 span_records。那一行保存的是供退出配对的信息，event 已在本函数中写进事件列表。

## 我的直接表述（原话）

> 这里的append event的部分？（我觉得我需要仔细的了解一下）

这是最初指定的疑问。[当时的数据归属与阅读安排](../../../../../04-flow.md#step014-data-roles-and-event-writer)。

2026-10-27，用户进一步表述：

> 我的理解是这里的append event 做的内容其实就是在使用handle 把这里的内容追加上去？

随后追问 handle 的完整结构和 type 的归属，完整原话保存在 [TraceHandle 结构卡](../../../../classes/slime/observability/trace_utils.py/TraceHandle.md#user-statement)。这表明用户在描述追加动作，不代表已经确认对象各层级。

## 尚不清楚

- handle → carrier → events → event 的层级区别，以及 type 属于 event 而非 handle 的澄清，尚待用户反馈。
- event 的组装与返回，以及调用方不接收返回值仍完成记录的关系，尚待用户反馈。
- parent_span_id 由外层怎样决定，以及嵌套上下文怎样恢复，归 trace_span 的后续问题。

<details>
<summary>来源与验证</summary>

- [函数实现](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L587-L613)与[当前调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L369-L382)。
- [结束事件复用本函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L499-L518)，本轮只定位。
- 示例为静态源码推导，未运行真实 Agent，不代表用户已掌握。

</details>
