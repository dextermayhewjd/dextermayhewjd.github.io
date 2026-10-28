> 历史归档（2026-10-27）：本稿退出当前阅读入口，仅保留此前解释、原话与验证边界。当前归属见[归档说明](README.md)。

# Procedure · 一次 agent_run 的 Trace 怎样逐步形成

[scope 的整体位置与阅读导航](../../../01-scope.md#reading-order) · [trace_span 父函数](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#normal-lifecycle)

本页只跟一个样本、一个 agent_run 阶段。先看最终新增了什么，再沿时间观察同一份数据，不要求按每个辅助函数跳转。源码版本为 18868a79；这是固定输入下的执行说明，不是 Slime 的历史演化。

当前场景：base_sample 的追踪编号 T1，句柄 h 指向 base_sample.trace；已有外层阶段 S0，本次阶段编号 S1。已有其他事件继续保留，下面只展示本次新增的两条。10.0、12.0、S1 与退出码 0 是教学值。

## 1. 先看最终结果：本阶段留下两条事件

调用方是 generate.py:286–295，以下省略 harness.run 的实参：

```python
with trace_span(base_sample, "agent_run", record_error=False) as span:
    agent_exit_code = await harness.run(...)
    span.set("exit_code", agent_exit_code)
```

正常完成后，base_sample.trace["events"] 追加了：

```python
[
    {
        "type": "span_start", "name": "agent_run", "ts": 10.0,
        "trace_id": "T1", "sample_id": 7, "group_id": 2, "attempt": 0,
        "span_id": "S1", "parent_span_id": "S0",
    },
    {
        "type": "span_end", "name": "agent_run", "ts": 12.0,
        "trace_id": "T1", "sample_id": 7, "group_id": 2, "attempt": 0,
        "span_id": "S1", "attrs": {"exit_code": 0},
    },
]
```

相同的 S1 把开始和结束配成一对。当前 _record_span_end 没有传 parent_span_id，因此结束事件没有这个键。Trace 记录这份样本运行过的阶段；TraceSpanContext 只保存本次阶段所需的临时状态，不代表整份样本本身。

## 2. 按使用顺序看：使用前 → 调用 → 使用后

下面四环节来自原 scope，沿用上面的 T1/S1 和退出码 0。只跟本次 S1，业务内部的其他阶段仍折叠；这四步是调用方的使用顺序。

<a id="use-enter"></a>

### ① 进入 with：开始记录，并取得本阶段对象

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

**必要时回查**：[trace_span 的进入与交出](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-enter)、[TraceSpanContext 构造](../../../02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md#construct-context)。读完回到本环，再继续②。

<a id="use-run"></a>

### ② 执行业务：拿到返回值，Trace 不代替业务执行

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

**必要时回查**：[父卡中的调用方片段](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-body)。本轮不重读 harness 内部；继续③。

<a id="use-attrs"></a>

### ③ 补充属性：将结果交给当前阶段

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

**必要时回查**：[set 与同步入口](../../../02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md#set-and-sync)。当前 end_events 为空，内部同步直接返回；读完返回③，再继续④。

<a id="use-exit"></a>

### ④ 离开 with：形成结束事件，回到业务主线

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

**必要时回查**：[父卡的正常退出](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-exit)、[完整数据 procedure](trace-span-lifecycle.md)。读完返回④，沿原业务继续。

<details>
<summary>需要解释这些变化时，再对照内部执行位置</summary>

只盯住两个位置：**events 是已写下的事件；end_attrs 是尚待写入结束事件的附加属性。**

| 时刻 | 当前动作与源码 | 本阶段已写进 events 的内容 | span_context 中的变化 |
| --- | --- | --- | --- |
| 进入前 | 已绑定 h → base_sample.trace | 尚无 S1 的事件 | 尚未创建 |
| 写开始 | _append_event，372–380 | S1 开始 | 尚未创建 |
| 包装本次状态 | TraceSpanContext(...)，390–395 | 仍是 S1 开始 | 关联 h、配对列表和开始时间；end_attrs={} |
| 交给业务、得到结果 | yield，398；调用方 span.set，295 | 仍是 S1 开始 | end_attrs={"exit_code": 0} |
| 取出结束属性 | build_end_attrs，97–98 | 仍是 S1 开始 | 原对象不变，返回属性字典副本 |
| 写结束 | _record_span_end，499–518 | S1 开始、S1 结束 | 结束事件已有 exit_code |
| 保存结束状态 | finalize，100–104 | 没有再新增事件 | end_events 指向刚写入的结束字典；closed=True |
| 离开阶段 | 两次 reset，419、423 | 两条事件保留 | 恢复先前上下文，随后回到调用方 |

这几种对象是分工合作，不是每经过一个函数就复制一份 Trace。h.carrier 与 base_sample.trace 指向同一个字典；finalize 保存的结束字典也就是 events 里那一条。

编号栈和句柄栈暂时作为“当前正在记录哪个阶段、哪个目标”的机制回查；恢复它们不会删除已经写下的事件。开始准备的细节见[原 P1–P4 procedure](trace-span-start.md)，当前不必重新下钻。

</details>

## 3. 把结束处的一行拆成三个动作

原码 trace_span:414：

```python
span_context.finalize(_record_span_end(span_records, name=name, attrs=span_context.build_end_attrs()))
```

按这条正常路径的实际求值顺序，等价地展开阅读如下。下面的局部变量是教学展开，未修改源码：

```python
end_attrs = span_context.build_end_attrs()
end_events = _record_span_end(span_records, name=name, attrs=end_attrs)
span_context.finalize(end_events)
```

三步分别是：**取属性 → 写结束事件 → 保存结束状态。** finalize 不再生成第三条事件，也不终止 Agent。

build_end_attrs 的完整实现只有：

```python
def build_end_attrs(self) -> dict[str, Any] | None:
    return dict(self.end_attrs) or None
```

它返回已有属性的浅拷贝，空字典时返回 None。没有解析 Trace、校验错误或决定终止；调用它也不会把新内容写回 span_context.end_attrs。

## 4. 异常来自哪里：只与同一阶段作对照

异常分支在 trace_span:399–411。外层捕获 with 内传出的异常，先取属性副本；record_error 为 True 时，才在这份局部属性中加入 error_type 和 error_message，再写结束事件。随后原异常继续向外抛出。

| 情况 | 谁提供异常信息 | 结束记录与控制流 |
| --- | --- | --- |
| 当前 agent_run 的 record_error=False | 不自动添加 Python 异常类型和消息 | 仍尝试写结束事件，原异常继续抛出 |
| 对照：record_error=True | trace_span 的 except 分支从捕获的 exc 取得 | 尝试在结束事件中加上异常信息，原异常仍继续抛出 |

不是“TraceSpanContext 里有错误内容，build_end_attrs 就发现并终止它”。业务退出码、Python 异常、是否记录异常属性是三个不同问题。False 不等于吞掉异常；True 也不是启动终止操作的开关。

## 5. 在当前样本场景中怎样读、怎样用

- 业务侧：用 with 标记一个阶段，有后续才知道的属性时通过拿到的 span 补充。
- 读记录：先找到同一 trace_id 和 span_id 的开始、结束事件，再看时间与 attrs。
- 读实现：先在上表找到“哪份数据发生了变化”，只有该动作不清楚时才打开函数卡，读完回到同一行。

当前只维持一个目标、一段执行与一份事件列表。多目标、子 Trace、跨进程传播、导出和降级机制仍按具体问题回查，不为当前正常路径继续增加前置。

## 我的直接表述与仍未确认的部分

用户要求显示 Trace 如何逐步构建，并指出按层跳转已经难以理解；原话与方法判断见[本轮记录](../../../04-flow.md#step014-trace-growth-reading)。

本页由助手按源码整理；build_end_attrs、异常归属及整体过程是否已理解，仍以用户后续反馈为准。

<details>
<summary>来源、示例与验证边界</summary>

- [trace_span:345–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345-L425)。
- [TraceSpanContext:68–111](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L68-L111)、[_record_span_end:499–518](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L499-L518)。
- [业务调用方](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L295)。
- 隔离执行原 trace_span、TraceHandle、TraceSpanContext 及所需辅助函数，以 TraceHandle 作为入口；时间固定为 10.0/12.0，UUID 仍由原函数生成，在说明中记作 S1。检查正常路径的两条事件、属性副本、结束事件的同一引用与上下文恢复；并用 record_error=False/True 对照异常属性、原异常重抛和上下文恢复。
- 演示未运行真实 Sample 类型、Agent、网络或并发任务；Sample 绑定后的对应关系来自固定源码。本页输出不是实际 Agent 日志。

</details>

本轮将具体用法从 scope 迁入本 procedure，内部解释保留作按需回查。[迁移记录](../../../04-flow.md#step014-scope-summary-short-term-usage)。
