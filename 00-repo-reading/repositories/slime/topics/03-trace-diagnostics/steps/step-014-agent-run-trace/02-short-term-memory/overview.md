# 02 · Step 014 本步短期记录

[阅读范围](../01-scope.md) · [前序累计记录](../03-long-term-memory/overview.md)

> 所属 Step 014 已按用户要求**暂缓研究**，以下卡片与数据保留供回查。见[步骤状态](../README.md)。

各工具卡单列“使用方法”，优先展示 trace_utils.py 外的真实调用、业务目的、输入、结果与后续消费者；源码推导与运行记录分开。

scope 只保留[工具分类与阅读导航](../01-scope.md#tool-catalog)。具体使用、输入输出与产物位置在本目录维护；索引不代替卡片，也不把已有卡片数量当作必读清单。

## 官方入口与配套用法

[examples · 四个真实调用的数据案例](examples/README.md)：每例都有具体输入、预期结果与验证边界；只收录已找到真实业务调用的用法。

| 记录 | 本步用途 | 来源与认识状态 |
| --- | --- | --- |
| [trace_span](functions/slime/observability/trace_utils.py/trace_span.md#usage-method) | 记录一段执行；四个时刻见[案例 A](examples/trace-span-agent-run/README.md#use-enter) | 历史卡已调取；本轮补明确用法入口，机制认识状态保留 |
| [trace_event](functions/slime/observability/trace_utils.py/trace_event.md#usage-method) | 添加一个瞬时事件 | 官方列出；当前未找到外部 Python 调用，旧教学例子已折叠；尚无独立理解表述 |
| [trace_function](functions/slime/observability/trace_utils.py/trace_function.md#usage-method) | 记录整个同步或异步函数调用 | 从已有 scope 用例迁入；官方用法及内部组合已核对，尚无独立理解表述 |
| [bind_trace](functions/slime/observability/trace_utils.py/bind_trace.md#usage-method) | 为已有 Sample 准备 trace 与句柄；[会话中的使用案例](examples/bind-trace/README.md) | 保留已有绑定机制卡；使用说明已按反馈重组，不计新增掌握 |
| [build_sglang_meta_trace_attrs](functions/slime/observability/trace_utils.py/build_sglang_meta_trace_attrs.md#usage-method) | 整理元信息并交给 span.update | 官方配套用法，从 scope 迁入；尚无独立理解表述 |

上面前四项是官方明确介绍的业务入口，最后一项是官方展示的组合工具。bind_trace_carrier、export_trace、import_trace 在 [bind_trace 的配套组合](functions/slime/observability/trace_utils.py/bind_trace.md#tool-export)与[案例 C](examples/bind-trace/README.md)中解释；当前未见调用的 trace_next_attempt 保留在 scope 的能力索引中。

## 按需回查的内部函数

| 记录 | 本步用途 | 来源与认识状态 |
| --- | --- | --- |
| [_coerce_handles](functions/slime/observability/trace_utils.py/_coerce_handles.md) | 将当前 Sample 整理成句柄列表 | 从父卡已展开内容拆出；用户仍在确认调用与返回关系 |
| [_adapt_trace_target](functions/slime/observability/trace_utils.py/_adapt_trace_target.md) | 当前只看 Sample 原样返回及恢复到调用方 | 用户明确追问后独立展开；尚待理解反馈 |
| [_ensure_trace_carrier](functions/slime/observability/trace_utils.py/_ensure_trace_carrier.md) | 准备并返回追踪字典 | 分层保存已讨论的字典准备；尚无独立理解确认 |
| [_append_event](functions/slime/observability/trace_utils.py/_append_event.md) | 组装、追加并返回一条事件字典 | 用户概括为通过 handle 追加；event 的归属和完整结构仍需澄清 |

## 类与数据结构卡

| 记录 | 本步用途 | 来源与认识状态 |
| --- | --- | --- |
| [TraceHandle](classes/slime/observability/trace_utils.py/TraceHandle.md) | 六个声明字段、carrier 与 event 的完整层级，以及追加前后的变化 | 由本轮结构问题建立；助手模型尚待反馈 |
| [TraceSpanContext](classes/slime/observability/trace_utils.py/TraceSpanContext.md) | 本次阶段对象的构造、set/update 用法与内部收尾边界 | 构造说明保留；最新追问是属性快照、异常归属和整条记录的形成，尚待反馈 |

Step 013 的 66 份累计记录完整保存在本步 03。trace_span 的历史卡未包含在该集合中，本次从 Step 001 补回 02，见[调取记录](../references/historical-retrieval.json)。局部状态与异常边界归父函数卡，具体数据与连续变化归 examples；保存出口按需查阅 [Trace 的保存与查看](../references/trace-output-and-viewing.md)。
