# 01 · 阅读范围：Trace 的工具总览与使用路线

[步骤入口](README.md) · [本步短期记录](02-short-term-memory/overview.md) · [前序记录](03-long-term-memory/overview.md)

> **本步暂缓研究（2026-10-28）。** 以下范围和阅读顺序保留供以后恢复，不作为当前待推进的任务；见[步骤状态](README.md)与[暂停记录](04-flow.md#step014-deferred-for-queue-review)。

## 1. 阅读目标

**先知道官方提供哪些用法、它们怎样配合，再进入对应短期记录看代码与数据变化。** 本页保留整体位置、接口分类、核心骨架、阅读入口与停止位置；每个工具的调用示例、输入输出和具体行为统一放在 02。

本步仍以一次 agent_run 的 trace_span 为主例。其他入口按使用问题选择，不要求依次调用全部工具，也不要求逐层读完所有内部实现。先看[模块用途](../../README.md#trace-utils-purpose)，再按下面的入口进入。

## 2. 官方工具与本步入口

- **业务位置**：[generate.py:286–296](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L296)，围住已有的 Agent 运行。
- **组织追踪的入口**：[trace_span:345–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345-L425)，负责阶段开始、交出对象、结束与上下文恢复。
- **范围**：官方四个业务入口、已核对的组合工具及收集出口。内部 helper 只在需要解释行为时回查；业务执行和存储系统内部继续保持黑箱。

<a id="tool-catalog"></a>

### 2.1 完整清单：先分使用角色，再进入短期记录

[examples · 四个具体数据案例](02-short-term-memory/examples/README.md)与下表卡片互相链接；scope 继续只保留总览和入口。

[官方指南](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/trace.md)明确介绍 trace_span、trace_event、trace_function、bind_trace，并展示 SGLang 属性组合。无下划线仅是命名形式，不能据此把所有函数和方法都当成推荐的业务 API。[版本与调用核对证据](references/official-trace-api-review.json)保留。

| 使用角色 | 工具 | 一句话用途 | 具体说明放在哪里 |
| --- | --- | --- | --- |
| 官方业务入口 | trace_span | 为一段执行记录开始与结束 | [函数卡](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#usage-method) · [四环节用法](02-short-term-memory/examples/trace-span-agent-run/README.md#use-enter) |
| 官方业务入口，未找到外部调用 | trace_event | 记录一个瞬间；当前仅有文档说明 | [函数卡](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_event.md) |
| 官方业务入口 | trace_function | 把整个函数调用记为一个阶段 | [函数卡](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_function.md#usage-method) |
| 官方业务入口 | bind_trace | 为已有 Sample 准备追踪句柄 | [函数卡](02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md#usage-method) · [会话中的使用方式](02-short-term-memory/examples/bind-trace/README.md) |
| 官方组合工具 | build_sglang_meta_trace_attrs | 整理模型元信息，交给 span.update | [函数卡及组合用法](02-short-term-memory/functions/slime/observability/trace_utils.py/build_sglang_meta_trace_attrs.md#usage-method) |
| 业务属性接口 | span.set / span.update | 给当前阶段补充属性 | [阶段对象卡](02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md#business-methods) |
| 集成组合 | bind_trace_carrier | 从普通字典取得追踪句柄 | [配套说明](02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md#tool-bind-carrier) · [后续请求中的使用](02-short-term-memory/examples/bind-trace/README.md#bind-carrier-step) |
| 集成组合 | export_trace / import_trace | 传递身份与父阶段，绑定接收侧容器 | [配套说明](02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md#tool-export) · [会话交接中的作用](02-short-term-memory/examples/bind-trace/README.md#export-trace-step) |
| 当前未见调用 | trace_next_attempt | 标记新的尝试，不负责运行重试 | [源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L428-L448) · [原能力示例](references/scope-before-short-term-usage.md#tool-next-attempt)；不建本轮必读卡 |
| 框架内部收尾 | build_end_attrs / finalize | 取出结束属性、保存结束事件引用 | [类卡回查](02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md) · [父函数收尾](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-exit) |

这张表覆盖本版本 9 个无下划线函数和相关对象方法；完整清单不等于九个并列使用步骤。具体产物与“使用前 → 调用 → 使用后”保存在右侧记录。

### 2.2 组合关系只在这里定位

```text
trace_function          → 内部用 trace_span 包住整个函数
trace_span 的 as span   → 业务可用 set / update 补属性
SGLang meta_info        → build_sglang_meta_trace_attrs → span.update
Adapter 上下文交接      → bind_trace → export_trace → import_trace
trace_span 退出         → 内部取属性、写结束、finalize、恢复上下文
```

这些行表示各自的配合关系，不是一条必须顺序执行的流水线。具体代码与数据变化从上表进入。

## 3. 核心骨架与阅读导航

<a id="overall-position"></a>

### 3.1 整体位置：给已有业务增加观察点

```text
generate → _generate：一份 Coding Agent 任务
├─ 准备会话、沙箱与工作区                  既有背景
├─ agent_run：执行 Agent CLI              本步主例
│  ├─ ① 进入 with：出现开始记录，得到 span
│  ├─ ② harness.run：得到业务返回值
│  ├─ ③ span.set：补充阶段属性
│  └─ ④ 离开 with：出现结束记录，恢复上下文
└─ 提取改动、评测、整理样本                返回业务主线
```

<a id="trace-span-core"></a>

### 3.2 调用方的最小骨架

保留本次关注的实参，省略 run / collect_metrics 的参数；注释编号是使用环节。完整输入、返回值及四个时刻的状态见[案例 A](02-short-term-memory/examples/trace-span-agent-run/README.md)。

```python
with trace_span(base_sample, "agent_run", record_error=False) as span:  # ①：286
    agent_exit_code = await harness.run(...)                         # ②：287–294
    span.set("exit_code", agent_exit_code)                           # ③：295

agent_metrics = await harness.collect_metrics(...)                  # ④退出后：296
```

退出由 with 自动驱动。record_error=False 只影响自动附加的异常信息，不能理解成吞掉异常或省略结束记录；具体对照留在短期记录。

<a id="reading-order"></a>
<a id="current-reading"></a>

### 3.3 从哪里读、读完返回哪里

先从 trace_span 卡的用途与最终事件进入，再沿案例 A 的①–④看同一组数据怎样变化。表中是使用顺序；旧内部编号另外折叠保留。

<a id="use-enter"></a>
<a id="use-run"></a>
<a id="use-attrs"></a>
<a id="use-exit"></a>

| 阅读环节 | 本环只解决什么 | 短期记录入口 | 读完返回 |
| --- | --- | --- | --- |
| ① 进入 | 输入 Sample 后，为什么得到 span，记录写在哪里 | [进入前后](02-short-term-memory/examples/trace-span-agent-run/README.md#use-enter) | 同一案例的② |
| ② 业务 | 哪个返回值属于 Agent，Trace 此刻有什么 | [执行业务前后](02-short-term-memory/examples/trace-span-agent-run/README.md#use-run) | 同一案例的③ |
| ③ 属性 | 退出码写到哪个位置，何时进入事件 | [补属性前后](02-short-term-memory/examples/trace-span-agent-run/README.md#use-attrs) · [set/update](02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md#business-methods) | 同一案例的④ |
| ④ 退出 | 结束事件留下什么，上下文怎样恢复 | [退出前后](02-short-term-memory/examples/trace-span-agent-run/README.md#use-exit) · [异常对照](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#exception-boundary) | generate.py:296 的业务主线 |

需要瞬时事件、函数级阶段或模型元信息时，再从 2.1 选择对应卡片。各卡单列“使用方法”：先给 trace_utils.py 外的真实业务调用、目的及结果，再按需补教学数据；未找到实际调用时如实标注。

<a id="trace-collection"></a>

### 3.4 Trace 收集在哪里：只保留整体交接

```text
trace_utils → 目标 carrier["events"]（Sample 对应 sample.trace）
  ├─ rollout debug dump → save_debug_rollout_data → .pt
  └─ Coding Agent generate 的 finally → SWE_TRACE_DIR → JSONL

.pt / JSONL → trace_timeline_viewer → 时间线文件
```

两条保存路径各有启用条件和保存时机。独立 carrier 不会自动汇入文件；export/import 也不搬运 events。配置、记录结构与查看命令统一见[辅助参考：Trace 的保存与查看](references/trace-output-and-viewing.md)。

### 3.5 回查与停止位置

对所选工具能说明“何时用、怎么调用、返回或改变什么、记录在哪里、下一步谁接住”就回到业务主线。只有具体变化解释不通时，再下钻相关机制。不会因为清单完整就把所有 helper 变成本轮必读项。

<a id="trace-function-layers"></a>
<a id="internal-reading-map"></a>

<details>
<summary>旧内部 1–10 编号：保留给已有卡片回查，不是新的使用顺序</summary>

此前卡片中的“第 7 项”“第 9 项”等，继续指下表；本页的①–④则是使用环节。

| 旧内部编号 | 原观察点与卡片 | 对应使用环节 |
| --- | --- | --- |
| 1 | [_coerce_handles：统一输入](02-short-term-memory/functions/slime/observability/trace_utils.py/_coerce_handles.md) | ①进入 |
| 2 | [读取旧栈、准备列表](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#entry-preparation) | ①进入 |
| 3 | [生成本次编号与确定父编号](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#span-identifiers) | ①进入 |
| 4 | [_append_event：写开始](02-short-term-memory/functions/slime/observability/trace_utils.py/_append_event.md) | ①进入 |
| 5 | [保存配对和上下文条目](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#record-bookkeeping) | ①进入 |
| 6 | [登记上下文](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#context-registration) | ①进入 |
| 7 | [创建对象并 yield](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#span-context-yield) | ①进入 |
| 8 | [业务执行与属性](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-body) | ②、③ |
| 9 | [写结束、保存结束状态](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-exit) | ④退出 |
| 10 | [恢复上下文](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#context-reset) | ④退出 |

完整旧骨架与调用层级保存在[改写前快照](references/scope-before-usage-data-flow.md)。开始登记的细节归回[trace_span 卡](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-start-yield)；这些材料的已读事实和未知没有清空。

</details>

<details>
<summary>原工具锚点的兼容入口</summary>

旧链接继续有效，正文已迁到对应的短期记录：

<a id="tool-bind-trace"></a>

- [bind_trace 用法](02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md#usage-method)

<a id="tool-bind-carrier"></a>

- [bind_trace_carrier 的组合用法](02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md#tool-bind-carrier)

<a id="tool-event"></a>

- [trace_event 用法](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_event.md)

<a id="tool-function"></a>

- [trace_function 用法](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_function.md#usage-method)

<a id="tool-next-attempt"></a>

- [trace_next_attempt 原能力示例](references/scope-before-short-term-usage.md#tool-next-attempt)

<a id="tool-export"></a>

- [export_trace 用法](02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md#tool-export)

<a id="tool-import"></a>

- [import_trace 用法](02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md#tool-import)

<a id="tool-sglang-meta"></a>

- [SGLang 元信息的组合用法](02-short-term-memory/functions/slime/observability/trace_utils.py/build_sglang_meta_trace_attrs.md#usage-method)

<a id="context-methods"></a>

- [阶段对象的方法及内外边界](02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md#business-methods)

</details>

<details>
<summary>固定版本、证据与迁移</summary>

- 本步源码固定在 18868a79；[源码证据](references/source-evidence.json)、[官方用法核对](references/official-trace-api-review.json)。
- [本轮迁移前完整 scope](references/scope-before-short-term-usage.md)；旧版本、原话及未知继续保留。
- [scope 为总、短期记录写具体用法的本轮讨论](04-flow.md#step014-scope-summary-short-term-usage)。整理不代表新增掌握或真实 Agent 运行。

</details>
