# 补齐 Trace 工具与收集路径前的 scope

2026-10-27 保存。以下为当时的完整使用视角 scope，仅重算相对链接；当前入口见 [01-scope.md](../01-scope.md)。

---

# 01 · 阅读范围：怎样使用 Trace，并观察数据变化

[步骤入口](../README.md) · [本步短期记录](../02-short-term-memory/overview.md) · [前序记录](../03-long-term-memory/overview.md)

## 1. 阅读目标

**学会给一段业务使用 trace_span，并说明每个使用环节前后，哪些数据发生了变化。** 当前仍只跟随一个 agent_run：进入 with、执行业务、补充属性、离开 with。

本步以调用者的使用过程为主线。内部函数用于解释某次数据变化，不再要求先沿调用树逐层读完。模块用途先看[主题入口](../../../README.md#trace-utils-purpose)；完整记录的形成见[连续 procedure](history/procedures/trace-span-lifecycle.md)。

读完应能指出：记录写在哪里、as span 得到什么、属性何时进入结束事件，以及异常退出时的行为。材料已写出不代表用户已经掌握。

## 2. 入口与同一个观察样本

- **业务入口**：[examples/coding_agent_rl/generate.py:286–296](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L296)。
- **组织追踪的函数**：[trace_span:345–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345-L425)。
- **本次使用的接口**：trace_span(...) 及其交出的对象的 set(...)。bind_trace 等由内部调用，不要求业务在这里再手动调用。
- **边界**：一份 Sample、一个 agent_run 阶段，记录组件正常工作。harness.run 的业务实现保持已有黑箱；trace_event、trace_function、多目标、子 Trace 和跨进程传播不在本次展开。

所有前后状态使用同一组教学值：

| 名称 | 本页约定 |
| --- | --- |
| base_sample | 当前样本，index=7、group_index=2 |
| trace_id | T1；进入前已有的其他记录保留 |
| 本次 span_id | S1，由进入阶段时生成；名字是 agent_run |
| 开始 / 结束时间 | 10.0 / 12.0；用于示例，不是实际运行日志 |
| agent_exit_code | 假设本次正常返回 0 |
| h | 内部为当前样本取得的 TraceHandle，carrier 指向 base_sample.trace |

下面只显示 **S1 的事件**，不把所有样本事件都重新列出。业务内部可能产生子阶段，它们在本页折叠；“只有开始事件”指本次 S1，不指整份 sample.trace。

## 3. 使用骨架与前后数据

<a id="overall-position"></a>

### 3.1 放回整体：只给现有业务增加观察点

```text
generate → _generate：一份 Coding Agent 任务
├─ 准备会话、沙箱与工作区                   既有背景
├─ agent_run：执行 Agent CLI               本步观察范围
│  ├─ ① 进入 with：得到 span，出现开始记录
│  ├─ ② 执行 harness.run：得到业务返回值
│  ├─ ③ span.set：给本阶段补充属性
│  └─ ④ 离开 with：出现结束记录，恢复上下文
└─ 提取改动、评测、整理样本                 返回业务主线
```

<a id="trace-span-core"></a>

### 3.2 使用代码：先从调用方读

下面保留真实调用关系，只省略 harness.run 和 collect_metrics 的实参。注释是使用环节编号，不是新增函数。

```python
with trace_span(base_sample, "agent_run", record_error=False) as span:  # ①：286
    agent_exit_code = await harness.run(...)                         # ②：287–294
    span.set("exit_code", agent_exit_code)                           # ③：295

agent_metrics = await harness.collect_metrics(...)                  # ④退出后：296
```

① 的调用会进入 trace_span，写完开始记录后才把 span 交给 with 内部；④ 是缩进块结束时自动发生的退出，不需要再手动调用一个“结束函数”。

<a id="reading-order"></a>
<a id="current-reading"></a>

### 3.3 四个使用环节：使用前 → 代码 → 使用后

**本轮从使用环节①读起。** 下列四段均沿用上面的同一个样本；先看可观察变化，再按需进入末尾的回查入口。它们与旧的内部 1–10 编号分开。

<a id="use-enter"></a>

#### ① 进入 with：开始记录，并取得本阶段对象

入口代码节选，省略号代表 with 内接下来的业务：

```python
with trace_span(base_sample, "agent_run", record_error=False) as span:
    ...
```

```text
使用前
  base_sample.trace：已有 T1 的记录，但没有本次 S1
  span：尚未由这次 with 绑定

使用后（刚进入 with 内部，尚未运行 harness.run）
  base_sample.trace["events"]：新增 S1 的 span_start，ts=10.0
  span：本次 TraceSpanContext
    handles      → [h]
    span_records → [(h, "S1")]
    start_ts     = 10.0
    end_attrs    = {}
    end_events   = []
    closed       = False
```

**这一环要弄清**：输入是样本，新增的是开始事件，交回的是阶段对象；不会返回另一个 Sample。当前的阶段上下文也已登记，供内部嵌套记录使用。

**必要时回查**：[trace_span 的进入与交出](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-enter)、[TraceSpanContext 构造](../02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md#construct-context)。读完回到本环，再继续②。

<a id="use-run"></a>

#### ② 执行业务：拿到返回值，Trace 不代替业务执行

```python
agent_exit_code = await harness.run(...)
```

```text
使用前
  本次 harness.run 的返回值尚未得到
  S1 的事件：span_start
  span.end_attrs = {}

使用后（本例假设正常返回 0）
  agent_exit_code = 0
  S1 的事件：仍是 span_start
  span.end_attrs = {}
```

**这一环要弄清**：返回值来自 harness.run；Trace 不会仅因业务返回就自动把退出码写入属性。这里仍处于 with 内，本阶段尚未结束。业务可能产生的子阶段记录不在本快照中展开。

**必要时回查**：[父卡中的调用方片段](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-body)。本轮不重读 harness 内部；继续③。

<a id="use-attrs"></a>

#### ③ 补充属性：将结果交给当前阶段

```python
span.set("exit_code", agent_exit_code)
```

```text
使用前
  agent_exit_code = 0
  span.end_attrs = {}
  span.end_events = []

使用后
  agent_exit_code = 0
  span.end_attrs = {"exit_code": 0}
  span.end_events = []
  S1 的事件：仍只有 span_start，没有新加结束事件
```

**这一环要弄清**：改变的是阶段对象里暂存的属性，业务返回值没有被改写。退出时再用这份属性写结束记录。

**字段限制**：set 的 key 约定为字符串，没有预设名称白名单；它扩展的是事件中的 attrs。同名键再次设置会覆盖之前的值。type、name、ts、trace_id、span_id 等事件顶层字段由记录逻辑填写，set 不会直接改写它们。value 在这里没有类型校验，通常使用方便保存和展示的字符串、数字、布尔值、列表或字典。

**必要时回查**：[set 与同步入口](../02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md#set-and-sync)。当前 end_events 为空，内部同步直接返回；读完返回③，再继续④。

<a id="use-exit"></a>

#### ④ 离开 with：形成结束事件，回到业务主线

缩进结束触发退出；以下省略已经展示的 with 内部：

```python
with trace_span(base_sample, "agent_run", record_error=False) as span:
    ...
# 正常退出 with 完成后，才会执行这一行：
agent_metrics = await harness.collect_metrics(...)
```

```text
使用前（with 内最后一行之后）
  S1 的事件：span_start
  span.end_attrs = {"exit_code": 0}
  span.end_events = []
  span.closed = False
  当前阶段上下文中登记着 S1

使用后（刚退出 with，尚未调用 collect_metrics）
  S1 的事件：
    span_start，ts=10.0
    span_end，  ts=12.0，attrs={"exit_code": 0}
  span.end_attrs = {"exit_code": 0}
  span.end_events → 刚写入的 span_end 字典
  span.closed = True
  阶段上下文恢复进入前的状态；事件记录仍然保留
```

**这一环要弄清**：开始/结束使用同一个 S1；恢复上下文不是删除事件。结束后再继续 collect_metrics。

需要解释内部原因时，将原来的嵌套调用按求值顺序展开看。下面是等价的阅读展开，源码未修改：

```python
end_attrs = span_context.build_end_attrs()  # 复制暂存属性
end_events = _record_span_end(span_records, name=name, attrs=end_attrs)
span_context.finalize(end_events)           # 保存结束事件引用并标记关闭
```

build_end_attrs 不解析或检查错误；它返回属性副本，空时返回 None。真正追加结束事件的是 _record_span_end。

**必要时回查**：[父卡的正常退出](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-exit)、[完整数据 procedure](history/procedures/trace-span-lifecycle.md)。读完返回④，沿原业务继续。

### 3.4 一个必要边界：业务抛出异常时

仍限定当前 record_error=False 的调用，以及追踪组件正常工作的前提：

| 使用情况 | 使用后的数据 | 控制流 |
| --- | --- | --- |
| harness.run 正常返回 0，并执行 set | 结束事件带 exit_code=0 | 正常退出后进入 collect_metrics |
| harness.run 抛异常，尚未执行 set | 尝试写结束事件；没有这次 exit_code 属性，也不自动附加异常类型/消息 | 原异常继续抛出，上下文仍执行恢复；不会接着执行这里的 collect_metrics |

record_error 只控制是否自动附加异常类型与消息，不是是否终止业务的开关。True 的对照见[完整 procedure](history/procedures/trace-span-lifecycle.md)，不在本轮同时展开全部异常、取消与降级实现。

### 3.5 回查与停止位置

只有某个使用环节的前后变化解释不通，才进入对应函数或类卡；每次带着结果回到同一个使用环节。无需在①前先读完所有基础设施。

**停止位置**：能够沿①–④说明调用方式、事件与临时属性的变化，以及当前异常边界，就回到业务主线。既有内部知识保留，但不以逐个读完辅助函数作为完成条件。

<a id="trace-function-layers"></a>
<a id="internal-reading-map"></a>

<details>
<summary>旧内部 1–10 编号：保留给已有卡片回查，不是新的使用顺序</summary>

此前卡片中的“第 7 项”“第 9 项”等，继续指下表；本页的①–④则是使用环节。

| 旧内部编号 | 原观察点与卡片 | 对应使用环节 |
| --- | --- | --- |
| 1 | [_coerce_handles：统一输入](../02-short-term-memory/functions/slime/observability/trace_utils.py/_coerce_handles.md) | ①进入 |
| 2 | [读取旧栈、准备列表](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#entry-preparation) | ①进入 |
| 3 | [生成本次编号与确定父编号](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#span-identifiers) | ①进入 |
| 4 | [_append_event：写开始](../02-short-term-memory/functions/slime/observability/trace_utils.py/_append_event.md) | ①进入 |
| 5 | [保存配对和上下文条目](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#record-bookkeeping) | ①进入 |
| 6 | [登记上下文](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#context-registration) | ①进入 |
| 7 | [创建对象并 yield](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#span-context-yield) | ①进入 |
| 8 | [业务执行与属性](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-body) | ②、③ |
| 9 | [写结束、保存结束状态](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-exit) | ④退出 |
| 10 | [恢复上下文](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#context-reset) | ④退出 |

完整旧骨架与调用层级保存在[改写前快照](../references/scope-before-usage-data-flow.md)。开始登记的细节仍见[P1–P4 procedure](history/procedures/trace-span-start.md)；这些材料的已读事实和未知没有清空。

</details>

<details>
<summary>固定版本、来源与改写记录</summary>

- 本页绑定本地源码 18868a79；[原有源码证据](../references/source-evidence.json)保留。
- [Trace 官方使用文档](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/trace.md)；[真实调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L296)。
- [使用视角改写前的完整 scope](../references/scope-before-usage-data-flow.md)与[本轮确认及修改](../04-flow.md#step014-usage-scope-rewrite)。
- 时间、编号与返回值是固定教学输入。现有隔离验证不等于运行真实 Sample、Agent 或模型；本轮改写文档，没有新增真实运行。

</details>

