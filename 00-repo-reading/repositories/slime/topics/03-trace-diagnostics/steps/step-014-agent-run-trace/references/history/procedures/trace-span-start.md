> 历史归档（2026-10-27）：本稿退出当前阅读入口，仅保留此前解释、原话与验证边界。当前归属见[归档说明](README.md)。

# Procedure · trace_span 开始阶段的状态流转

[完整阅读路线](../../../01-scope.md#reading-order) · [返回 trace_span 函数卡](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#span-identifiers)

- **记录类型**：本步短期记忆中的 procedure，串联一段连续执行及其数据变化。
- **所属函数**：slime/observability/trace_utils.py::trace_span，固定版本 18868a79。
- **过程范围**：362–366 的已备输入 → 368–384 的正常开始登记 → 返回 390 的下一段。
- **对应旧内部编号**：P1、P2、P3、P4 分别对应 scope 保留的内部第 3、4、5、6 项，见[内部回查表](../../../01-scope.md#internal-reading-map)；当前使用顺序是 scope 的①–④。
- **理解状态**：按用户 2026-10-27 的要求从 reference 迁入；内容由助手根据源码整理，尚未确认已理解全部步骤。

[短期记忆索引](../../../02-short-term-memory/overview.md)


只看 **trace_utils.py:368–388 中没有发生异常的路径**，对应 scope 的旧内部第 3–6 项，整体属于新使用环节①的进入准备。362–366 行提供输入，390 行之后构造操作对象和执行 with 的部分留在后面。

全页只跟一个句柄。T1、S0、S1、10.0 是为看清关系而固定的教学值；实际 span_id 由运行时生成。示例只画新增事件，原有事件继续保留。

代码按单次循环拆段显示：下面第 2、3 段仍在同一个 for 内执行，第 4 段在循环结束后执行。

## 入口状态：执行本过程前已具备的数据

| 名称 | 本例的值或形状 | 先记住什么 |
| --- | --- | --- |
| handles | `[h]` | h 是一个 TraceHandle，随后循环取出它 |
| h.trace_id | `"T1"` | 所属追踪编号 |
| h.carrier | 与 `base_sample.trace` 同一个字典 | 里面的 events 保存追踪事件 |
| h 的其他字段 | sample_id=7、group_id=2、attempt=0、parent_span_id=None | 后面用于组装事件 |
| name、timestamp、attrs | `"agent_run"`、`10.0`、`None` | 本阶段名称、开始时间、附加属性 |
| stack_before | `(("T1", "S0"),)` | 已有外层阶段 S0 |
| handle_stack_before | `((h_outer,),)` | 已有外层句柄分组 |
| span_records、new_entries | `[]`、`[]` | 本次的两个空列表 |

h_outer 表示外层阶段原有的句柄。这里没有重新创建 Sample，也还没有写入本次的开始事件。

若不清楚 h 内部有什么，先看 [TraceHandle 结构卡](../../../02-short-term-memory/classes/slime/observability/trace_utils.py/TraceHandle.md)：六个声明字段与 carrier/events 分层放在一处；读完回到下面 P1，procedure 继续追踪数据怎样变化。

## P1 · 取出当前句柄，确定两个阶段编号

**执行位置：369–371。输入是 handles 中的 h，以及旧编号栈 stack_before。**

```python
for handle in handles:                     # 369：本轮 handle 就是 h
    span_id = _new_span_id()                # 370：本例用 S1 表示生成结果
    parent_span_id = handle.parent_span_id or _get_current_parent_span_id(
        handle.trace_id, stack=stack_before
    )                                      # 371：本例从旧栈找到 S0
```

此时新得到两个字符串：

```python
span_id = "S1"
parent_span_id = "S0"
```

**本步更新**：只新增 span_id 与 parent_span_id 两个局部值，h 与两个空列表保持原状。关系是追踪 T1 中，S1 挂在已有的 S0 下面。

**继续位置**：同一轮循环的 372 行，进入 P2。

<a id="p2-write-event"></a>

## P2 · 写入开始事件

**执行位置：372–380。输入沿用 P1 的 h、S1、S0，以及 name、timestamp、attrs。**

```python
_append_event(                             # 372–380
    handle,
    kind="span_start",
    name=name,
    timestamp=timestamp,
    span_id=span_id,
    parent_span_id=parent_span_id,
    attrs=attrs,
)
```

[_append_event](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/_append_event.md) 使用 h 的身份字段与传入参数，创建下面这条事件 E1：

```python
E1 = {
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

E1 被追加到 **h.carrier["events"]**，也就是本例的 base_sample.trace["events"]。attrs 为 None，因此没有 attrs 字段。这个函数也返回 E1，但当前调用处没有接收返回值；记录已通过追加完成。

**本步更新**：事件列表新增 E1；h 的六个字段没有增减，type 等键属于 E1；两个局部列表仍为空。完整归属见 [结构卡](../../../02-short-term-memory/classes/slime/observability/trace_utils.py/TraceHandle.md#trace-data-layers)。

**返回位置**：_append_event 完成后回到 trace_span:381，继续 P3。

## P3 · 保存结束配对与编号条目

**执行位置：381–382。输入继续沿用同一个 h 和 S1。**

```python
span_records.append((handle, span_id))       # 381
new_entries.append((handle.trace_id, span_id))  # 382
```

执行后：

```python
span_records = [(h, "S1")]
new_entries = [("T1", "S1")]
```

| 保存的位置 | 保存的类型 | 为什么保存它 |
| --- | --- | --- |
| span_records | `(TraceHandle, str)` | 结束时要找到同一个事件列表，沿用 S1 写结束事件 |
| new_entries | `(str, str)` | 向编号栈登记：追踪 T1 现在进入 S1 |

**本步更新**：两个局部列表各新增一项；E1 仍在事件列表里，h 仍是同一个句柄。

**继续位置**：本例只有一个句柄，循环结束后到 383，继续 P4。若有多个句柄，对其余句柄重复 P1–P3。

## P4 · 循环结束后登记当前上下文

**执行位置：383–384。输入是两个旧栈、P3 填好的 new_entries，以及原来的 handles。**

```python
token = _TRACE_STACK.set(                  # 383：登记阶段编号
    stack_before + tuple(new_entries)
)
handle_token = _TRACE_HANDLE_STACK.set(    # 384：登记本次句柄分组
    handle_stack_before + (tuple(handles),)
)
```

| 对象 | 进入前的值 | 登记后的值 |
| --- | --- | --- |
| _TRACE_STACK | `(("T1", "S0"),)` | `(("T1", "S0"), ("T1", "S1"))` |
| _TRACE_HANDLE_STACK | `((h_outer,),)` | `((h_outer,), (h,))` |

**本步更新**：当前上下文改为表中的新值；两个 set 分别返回 token、handle_token，留给之后的 finally 恢复。两个 before 仍保留旧值，两个列表仍保留 P3 的结果。

**继续位置**：正常路径走出这段 try，到 trace_span:390。

## 出口状态与下一次交接

```text
同一个 h 和本次编号 S1
├─ 生成 E1 → h.carrier["events"]：实际事件
├─ (h, S1) → span_records：结束时的配对信息
└─ (T1, S1) → new_entries → _TRACE_STACK：当前阶段编号

handles 中的 h → 本次句柄分组 → _TRACE_HANDLE_STACK：当前目标
两个 set 的返回值 → token / handle_token：之后恢复用的凭据
```

此时业务还没有执行，S1 的结束事件也还没有写入。下一段才把 handles、span_records、开始时间交给 TraceSpanContext，并运行到 yield。

回到主线时，对照[使用环节①](../../../01-scope.md#use-enter)、[旧内部编号 3–6](../../../01-scope.md#internal-reading-map)与[父函数卡](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#span-identifiers)。更细的对象说明按需进入：[编号栈](../../trace-stack.md)、[句柄栈](../../trace-handle-stack.md)。

## 我的直接表述与尚未确认

> 我觉得这里的reference 也太笼统了 要不还是在short term中作为procedure的方式存在会比较好一点 reference是用来存放别的内容的

本次确认的是记录形式。P1–P4 的数据变化仍以用户之后的实际反馈为准，不因迁入短期记忆就标为掌握。

<details>
<summary>源码与验证边界</summary>

- 本过程从原 references/trace-span-try-data-flow.md 迁入并按入口、操作、更新、返回位置重排；旧路径仅留迁移指针。
- 固定版本 18868a79：[try 前的准备与开始登记](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L362-L388)、[事件组装与写入](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L587-L613)。
- 这里是单个句柄的正常路径。异常降级、多个句柄、with 内的业务执行和结束处理不在本页展开。
- 展示值经过教学替换；不把它们当成真实 Agent 运行日志。
- 已隔离执行固定源码中开始阶段 try 的正常语句，并使用真实的 TraceHandle、编号生成、父编号查找、事件写入函数：核对新事件字段、旧事件保留、两个局部列表和两个上下文值全部一致，恢复 token 后回到旧上下文。没有执行完整 trace_span 或真实 Agent。

</details>
