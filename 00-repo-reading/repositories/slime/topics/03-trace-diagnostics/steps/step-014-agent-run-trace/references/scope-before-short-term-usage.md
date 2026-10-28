# 01 · 阅读范围：怎样使用 Trace，并观察数据变化

[步骤入口](../README.md) · [本步短期记录](../02-short-term-memory/overview.md) · [前序记录](../03-long-term-memory/overview.md)

## 1. 阅读目标

**先列全 trace_utils 可使用的工具，再逐项看使用例子、前后数据和产物归属，最后接清内存记录如何收集、保存与查看。** agent_run 的四个使用环节继续作为 trace_span 的详细主例；其他公开工具先做到接口级理解，不要求一并下钻全部实现。

本步以调用者的使用过程为主线。内部函数用于解释某次数据变化，不再要求先沿调用树逐层读完。模块用途先看[主题入口](../../../README.md#trace-utils-purpose)；完整记录的形成见[连续 procedure](history/procedures/trace-span-lifecycle.md)。

读完应能指出：记录写在哪里、as span 得到什么、属性何时进入结束事件，以及异常退出时的行为。材料已写出不代表用户已经掌握。

## 2. 入口与同一个观察样本

- **业务入口**：[examples/coding_agent_rl/generate.py:286–296](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L296)。
- **组织追踪的函数**：[trace_span:345–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345-L425)。
- **工具范围**：本版本定义的全部公开函数及 TraceSpanContext 的公开方法，见下表。每个例子说明调用前后；已有 agent_run 仍保留真实业务入口。
- **深入边界**：具体业务执行和存储系统内部保持黑箱；新增工具按公开用法、产物与交付位置说明。跨目标传播讲清容器归属，不展开网络、队列或分布式协议。

下文 agent_run 四个环节继续使用同一组教学值；其他工具的独立例子会单独说明输入：

| 名称 | 本页约定 |
| --- | --- |
| base_sample | 当前样本，index=7、group_index=2 |
| trace_id | T1；进入前已有的其他记录保留 |
| 本次 span_id | S1，由进入阶段时生成；名字是 agent_run |
| 开始 / 结束时间 | 10.0 / 12.0；用于示例，不是实际运行日志 |
| agent_exit_code | 假设本次正常返回 0 |
| h | 内部为当前样本取得的 TraceHandle，carrier 指向 base_sample.trace |

下面只显示 **S1 的事件**，不把所有样本事件都重新列出。业务内部可能产生子阶段，它们在本页折叠；“只有开始事件”指本次 S1，不指整份 sample.trace。


<a id="tool-catalog"></a>

### 2.1 模块工具全表：按使用角色区分

这里列全此版本定义的 **9 个非下划线函数**及相关对象方法，**不把无下划线等同于官方推荐的业务 API**。以下按官方文档与真实调用位置区分角色；这是使用定位，不是 Python 访问限制或接口稳定性承诺。

| 使用角色 | 包含哪些接口 | 依据与阅读方式 |
| --- | --- | --- |
| 官方文档的业务入口 | trace_span、trace_event、trace_function、bind_trace | 文档明确列出；优先理解如何打点。它们不是必须依次执行的四步 |
| 官方展示的组合工具 | build_sglang_meta_trace_attrs 与 span.update | 元信息先整理，再交给阶段对象；不单独产生完整 Trace |
| 业务中的阶段属性接口 | span.set、span.update | set 见 Coding Agent；update 见官方文档与 SGLang 调用 |
| Adapter/上下文集成工具 | bind_trace_carrier、export_trace、import_trace | 有真实跨组件组合调用；按集成需求使用，不是每次打点的前置步骤 |
| 仅有实现、当前未找到调用 | trace_next_attempt | 本固定版本 Python 源码只找到定义；保留能力说明，不列为推荐必用入口 |
| 框架内部生命周期方法 | TraceSpanContext.build_end_attrs、finalize | 当前实际调用位于 trace_span 收尾，业务代码不需要手动组合这两步 |

官方指南与本地当前读取文件已逐字核对；[核对证据](official-trace-api-review.json)记录固定提交与官方当前提交。下表保留完整产物索引，具体角色以上表为准。

| 工具 | 用来做什么 | 使用后留下什么 | 在哪里 |
| --- | --- | --- | --- |
| [bind_trace](#tool-bind-trace) | 为 Sample 准备追踪容器 | TraceHandle；必要时初始化 trace，尚无新事件 | sample.trace |
| [bind_trace_carrier](#tool-bind-carrier) | 在普通字典上绑定追踪 | TraceHandle；初始化或补足容器 | 传入的 carrier |
| [trace_span](#trace-span-core) | 包住一个有持续时间的阶段 | 开始/结束事件；with 内取得 TraceSpanContext | 目标 carrier 的 events |
| [trace_event](#tool-event) | 记录一个瞬间 | 单条 type=event 的记录 | 目标 carrier 的 events |
| [trace_function](#tool-function) | 给整个同步/异步函数加阶段记录 | 函数被调用时产生开始/结束事件；原业务返回值照常返回 | 目标 carrier 的 events |
| [trace_next_attempt](#tool-next-attempt) | 标记一次新的尝试 | attempt 加一，以及 attempt_start 事件 | carrier、返回的句柄及 events |
| [export_trace](#tool-export) | 生成可传递的追踪上下文 | 包含身份与父阶段的字典，不包含 events | 返回值 payload |
| [import_trace](#tool-import) | 从上下文创建接收侧的句柄 | TraceHandle 与接收侧容器，不自动搬运旧事件 | 接收侧 carrier |
| [build_sglang_meta_trace_attrs](#tool-sglang-meta) | 整理 SGLang 返回的元信息 | attrs 字典；有 PD 信息时还可有子事件描述 | 先只在返回值，需再交给 span.update |

**并非每次调用都会产生 Trace 事件，也并非每次调用都会写文件。** 内存中实际写事件的目标，是传入对象最终对应的 carrier["events"]。保存到文件的两条路径见[记录收集与保存](#trace-collection)。

下面的示例均假定已从 slime.observability.trace_utils 导入对应函数。每个工具例子独立使用新样本或新字典，不把前一例的状态暗中沿用到下一例；编号 T1/S1 只是展示名称。合法目标、记录组件正常工作是本页示例的前提。

普通业务可按需要从下面的入口选择，不要求全部使用：

```python
from slime.utils.types import Sample
from slime.observability.trace_utils import (
    trace_span, trace_event, trace_function, bind_trace,
)
```

其他集成工具在各自例子中单独导入。trace_span 接收 Sample 时内部会完成绑定，简单使用不必先手动调用 bind_trace。

### 2.2 官方用法中的组合关系

**整个函数打点**：官方的 @trace_function("generate_and_rm", target="sample") 在内部使用 trace_span 包住函数调用；业务使用装饰器即可。需要观察某个子阶段时，才另外在函数内部使用 trace_span。

**SGLang 元信息组合**：下面的形式同时出现在[官方指南](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/trace.md)与 [sglang_rollout.py:219–230](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L219-L230)，仅省略请求的具体实参：

```python
from slime.observability.trace_utils import build_sglang_meta_trace_attrs

with trace_span(sample, "sglang_generate") as span:
    output = await post(url, payload)
    span.update(build_sglang_meta_trace_attrs(output["meta_info"]))
```

build_sglang_meta_trace_attrs 产出属性，span.update 接住属性/子事件描述，trace_span 负责阶段的开始与结束。这是配套使用，不是三个功能完全独立的打点入口。

**上下文集成组合**：Coding Agent 的 [generate.py:270–275](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L270-L275) 把 bind_trace → export_trace → import_trace 的结果交给 adapter.open_session；Adapter 的 [common.py:412–414](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L412-L414) 从已有 carrier 得到句柄再记录阶段。只有需要这类交接时才深入这些工具。

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

**trace_span 的详细用法仍按①–④阅读。** 需要其他工具时从上面的完整表直接进入独立例子；各工具不是必须顺序执行的流水线。下列四段沿用同一个样本，与旧的内部 1–10 编号分开。

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

**停止位置**：对所选工具能说明怎样调用、返回什么或修改什么、产物在哪里，并知道如何送到保存/查看入口，就回到业务主线。trace_span 的内部用①–④解释；其他工具不因被列全就要求一次深入所有实现。

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

完整旧骨架与调用层级保存在[改写前快照](scope-before-usage-data-flow.md)。开始登记的细节仍见[P1–P4 procedure](history/procedures/trace-span-start.md)；这些材料的已读事实和未知没有清空。

</details>

<details>
<summary>固定版本、来源与改写记录</summary>

- 本页绑定本地源码 18868a79；[原有源码证据](source-evidence.json)保留。
- [Trace 官方使用文档](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/trace.md)；[真实调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L296)。
- [使用视角改写前的完整 scope](scope-before-usage-data-flow.md)与[本轮确认及修改](../04-flow.md#step014-usage-scope-rewrite)。
- 时间、编号与返回值是固定教学输入。工具例子与临时 JSONL 写入做过隔离验证，未运行真实 Agent、训练或模型；完整验证边界见文末。

</details>

### 3.6 其他工具的使用前、调用和使用后

trace_span 已在上面的四个使用环节完整展示。这里补齐其他 8 个工具；展开一个例子只需理解该次调用的产物，不要求顺序执行全部例子。

<a id="tool-bind-trace"></a>

#### bind_trace：让样本拥有记录位置

```python
sample = Sample(index=7, group_index=2, prompt="demo")
handle = bind_trace(sample)
```

- **使用前**：新样本尚未绑定 trace，getattr(sample, "trace", None) 为 None。
- **使用后**：sample.trace 有 version、trace_id、sample_id、group_id、attempt、events 六个基础键，events=[]；返回 handle，且 handle.carrier is sample.trace。
- **留下在哪里**：容器在样本上；尚未追加任何事件。已有容器时复用，不清空旧事件。
- [源码 238–254](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L238-L254)。

<a id="tool-bind-carrier"></a>

#### bind_trace_carrier：集成场景中的容器绑定

```python
from slime.observability.trace_utils import bind_trace_carrier

carrier = {}
handle = bind_trace_carrier(
    carrier, trace_id="T1", sample_id=7, group_id=2
)
```

- **使用前**：carrier={}。
- **使用后**：carrier 补齐六个基础键，trace_id="T1"、sample_id=7、group_id=2、attempt=0、events=[]；handle.carrier is carrier。
- **留下在哪里**：这个普通字典，没有自动挂到某个 Sample，也没有自动写文件。carrier=None 时会创建新的字典，由 handle.carrier 持有。
- **使用定位**：Adapter 有实际调用；官方普通打点示例没有要求业务先调用它。
- [源码 257–286](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L257-L286)。

<a id="tool-event"></a>

#### trace_event：只记录一个时间点

```python
sample = Sample(index=7, group_index=2, prompt="demo")
trace_event(sample, "tool_started", attrs={"tool": "pytest"})
```

- **使用前**：样本没有这条事件；不需要手动先调用 bind_trace。
- **使用后**：events 新增一条记录，关键内容为 type="event"、name="tool_started"、ts=当前时间、attrs={"tool": "pytest"}，并带目标身份；返回 None。
- **留下在哪里**：sample.trace["events"]。它不会自动生成一对开始/结束事件；有当前父阶段时记录父编号。
- [源码 326–341](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L326-L341)。

<a id="tool-function"></a>

#### trace_function：整个函数调用就是一个阶段

score 是演示用的业务函数，不是 Slime 新增的工具接口：

```python
@trace_function("score", target="sample", record_error=False)
def score(sample):
    return 0.8

sample = Sample(index=7, group_index=2, prompt="demo")
value = score(sample)
```

- **使用前**：定义/装饰函数本身还没有运行业务，不会因此为样本追加事件。
- **使用后**：value=0.8；sample.trace["events"] 新增 name="score" 的 span_start 与 span_end，二者的 span_id 相同。
- **留下在哪里**：参数 sample 对应的容器。target="sample" 指参数名，不是固定要求所有业务都叫 sample。异步函数也有对应的 await 包装。
- **配套参数**：attrs_getter 可提供开始属性；目标需从多个参数组合取得时可用 target_getter。优先明确指定目标，找不到有效目标时可能只执行业务、不产生追踪。
- [源码 451–496](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L451-L496)。

<a id="tool-next-attempt"></a>

#### trace_next_attempt：能力示例，当前未见实际调用

这项保留完整清单，但不是官方指南推荐的常规打点步骤。对固定版本所有 Python 源码检索，仅找到本函数定义；下面用于说明现有实现会做什么，不表示必须接入。

```python
from slime.observability.trace_utils import trace_next_attempt

sample = Sample(index=7, group_index=2, prompt="demo")
handle = bind_trace(sample)
handle = trace_next_attempt(handle, attrs={"reason": "retry"})
```

- **使用前**：carrier["attempt"]=0，handle.attempt=0，events=[]。
- **使用后**：两处 attempt 都变为 1；追加 type="event"、name="attempt_start" 的记录，attrs={"attempt": 1, "reason": "retry"}。
- **留下在哪里**：同一个 carrier 和事件列表；单目标返回句柄，多目标返回句柄列表。它不会再次调用 Agent，也不负责调度重试。
- [源码 428–448](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L428-L448)。

<a id="tool-export"></a>

#### export_trace：上下文集成，传递身份与父阶段

```python
from slime.observability.trace_utils import bind_trace_carrier, export_trace

handle = bind_trace_carrier(
    {}, trace_id="T1", sample_id=7, group_id=2, parent_span_id="S0"
)
payload = export_trace(handle)
```

使用后返回：

```python
{
    "version": 1,
    "trace_id": "T1",
    "sample_id": 7,
    "group_id": 2,
    "attempt": 0,
    "parent_span_id": "S0",
}
```

- **使用前后**：handle 和原有 events 不因这次调用而改变。
- **留下在哪里**：payload 返回值，里面没有 events；它给接收方说明“属于哪条追踪、接在哪个阶段下”，没有写出任何文件。
- [源码 289–308](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L289-L308)。

<a id="tool-import"></a>

#### import_trace：上下文集成，接到接收侧容器

假定 payload 是上例所示的六字段字典：

```python
from slime.observability.trace_utils import import_trace

received_trace = {}
remote_handle = import_trace(payload, received_trace)
```

- **使用前**：接收侧 received_trace={}。
- **使用后**：received_trace 包含 T1、样本 7、组 2、attempt=0 和空 events；remote_handle.parent_span_id="S0"，remote_handle.carrier is received_trace。
- **留下在哪里**：接收侧字典和返回句柄。import_trace 不会从发送方复制旧事件；之后对 remote_handle 写的事件只进入 received_trace，不会自动汇总回发送方。
- **当前仓库例子**：Coding Agent 在 [generate.py:272](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L272) 把 export/import 与同一个 base_sample.trace 一起交给 adapter.open_session，因此该处仍复用本地容器；不据此推断所有跨进程调用都共享字典。
- [源码 311–323](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L311-L323)。

<a id="tool-sglang-meta"></a>

#### build_sglang_meta_trace_attrs：官方组合中的元信息整理

```python
from slime.observability.trace_utils import build_sglang_meta_trace_attrs

meta = {
    "prompt_tokens": 12,
    "completion_tokens": 7,
    "finish_reason": {"type": "stop"},
    "id": "req-1",
    "unused": 99,
}
attrs = build_sglang_meta_trace_attrs(meta)
```

使用后返回：

```python
{
    "prompt_tokens": 12,
    "completion_tokens": 7,
    "finish_reason": "stop",
    "sglang_request_id": "req-1",
}
```

- **使用前后**：只整理输入中的相关信息，不因此给任何 sample 追加事件；不是把所有 meta 字段原样复制。
- **留下在哪里**：返回的 attrs。通常在已有 span 内调用 span.update(attrs)，让普通属性进入该阶段的结束记录。
- **有 PD 时延时**：返回值还可能包含 _trace_children 子阶段描述；span.update 会将它转换为实际的子事件，单独调用本工具仍只是返回描述。
- [源码 140–210](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L140-L210)。

<a id="context-methods"></a>

### 3.7 返回对象的接口与框架内部方法

| 对象 | 在使用代码中怎样取得 | 持有什么 |
| --- | --- | --- |
| TraceHandle | handle=bind_trace(sample)，或 bind_trace_carrier / import_trace | 身份与 carrier 引用，记录写入该 carrier |
| TraceSpanContext | with trace_span(...) as span | 本次阶段的句柄、配对和属性；不是另一份持久 Trace |

类定义中的字段可在[TraceHandle 卡](../02-short-term-memory/classes/slime/observability/trace_utils.py/TraceHandle.md)和[TraceSpanContext 卡](../02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md)回查。以下虽有 4 个无下划线方法，角色并不相同：set/update 提供给业务补充信息，build_end_attrs/finalize 由框架收尾调用；不能按名称形式把四者都当成业务步骤。

#### set：补一项属性

```python
span.set("exit_code", 0)
```

end_attrs 从 {} 变为 {"exit_code": 0}，返回 span 自身；当前阶段未结束时没有新增事件。完整使用前后见[环节③](#use-attrs)。

#### update：批量补属性，可接收子 Trace 描述

```python
with trace_span(sample, "sglang_generate") as span:
    span.update({"completion_tokens": 7, "finish_reason": "stop"})
```

- 使用前：end_attrs={}。
- 调用 update 后：end_attrs={"completion_tokens": 7, "finish_reason": "stop"}，返回 span 自身；普通属性暂不新建事件。
- 离开 with 后：这些属性进入父阶段的 span_end。
- 特殊键 _trace_children 会被单独取出，转换为子阶段或瞬时事件，不作为普通属性直接保留。set 不具备这项专门解析步骤。
- [源码 83–95](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L83-L95)。

#### build_end_attrs：框架内部取得属性副本

在已有 span 上，假设 end_attrs={"exit_code": 0}：

```python
attrs = span.build_end_attrs()
```

返回 {"exit_code": 0} 的浅拷贝；span.end_attrs 和事件列表不变。原字典为空时返回 None，不检查错误或决定终止。通常由 trace_span 收尾调用，业务不必手动调用。

#### finalize：框架内部保存结束事件

这是 trace_span 的内部收尾用法，不是要求业务在 with 后再手动调用：

```python
# end_events 是 _record_span_end 刚刚返回的事件列表
span.finalize(end_events)
```

调用前 end_events 字段为空、closed=False；调用后该字段引用传入列表、closed=True，并把已有属性同步到这些结束字典；返回 None。不会再新增一条事件，已有字典仍在原 carrier["events"] 中。[源码 97–111](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L97-L111)。

<a id="trace-collection"></a>

### 3.8 留下的 Trace 在哪里收集、怎样保存

#### 第一层：写入目标的内存容器

```text
目标是 Sample              → sample.trace["events"]
目标是 TraceHandle         → handle.carrier["events"]
目标是多个目标的列表        → 分别写进每个目标的容器
绑定的是独立字典 carrier   → 只留在该 carrier，调用者负责交付/保存
```

trace_utils 没有一个自动搜集全系统事件的全局队列。两个 ContextVar 栈用于确定当前目标/父阶段，实际事件保存在 carrier。export_trace/import_trace 也不会自动把远端 events 拉回本地。

#### 第二层 A：通用 rollout debug dump

启用 --save-debug-rollout-data 后，正常生成路径是：

```text
RolloutManager._generate 取得 data
    → save_debug_rollout_data(path_template, data, ...)
    → 各 sample.to_dict() 保留 trace
    → torch.save({"rollout_id": ..., "samples": [...]}, path)
```

配置示例，仅展示保存参数，不在本轮启动训练：

```text
--save-debug-rollout-data /tmp/rollout_{rollout_id}.pt
```

当 rollout_id=0 时，文件是 /tmp/rollout_0.pt。其中第 i 个样本的事件位置为：

```text
dump["samples"][i]["trace"]["events"]
```

- path_template 为 None 时不写文件；内存里的事件仍可能存在。
- 这条路径保存传给 helper 的样本，不因此承诺保留此前被过滤掉的每次尝试。
- evaluation=True 时会从各评估分组提取样本。
- 文件名以 .straw.json 结尾时走 RolloutArchive.save 归档分支；它不是普通 .pt 或下文逐行 JSON。此处只定位，不声称查看器可直接打开该归档。

来源：[RolloutManager._generate:335–365](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L335-L365)、[保存函数:136–163](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/rollout_data_utils.py#L136-L163)、[Sample.to_dict:246–251](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L246-L251)。

#### 第二层 B：Coding Agent 的每次轨迹 JSONL

当前业务还有一条独立的收集路径：

```text
examples/coding_agent_rl/generate.py::generate
    → finally（无论 _generate 正常返回还是抛出）
    → 检查 SWE_TRACE_DIR
    → 追加到 rollouts-<本工作进程标识>.jsonl
```

示例配置：

```bash
export SWE_TRACE_DIR=/tmp/slime-traces
```

这只是说明如何启用后续运行的写盘，不代表本轮已运行 Agent。环境变量未设置或为空时，不生成这些 JSONL 文件。

每次写入的一行包含：

```text
{
  "index": ...,
  "group_index": ...,
  "trace": base_sample.trace,
  "status": ...,
  "reward": ...,
  "response_length": ...,
  "metadata": ...
}
```

所以事件位于每行 record["trace"]["events"]。这条路径在返回给后续组过滤前就尝试写入，目标是覆盖包括被过滤或被打断的轨迹；写文件异常会记录日志。它与通用 rollout dump 的保存时机、样本范围不同。

来源：[generate:225–251](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L225-L251)、[Coding Agent 输出说明](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/README.md#outputs-and-restart)。

#### 第三层：查看器读取已有文件

以下是使用示例，不在本轮执行：

```bash
python tools/trace_timeline_viewer.py /tmp/rollout_0.pt --no-serve

cat /tmp/slime-traces/rollouts-*.jsonl > /tmp/coding-traces.jsonl
python tools/trace_timeline_viewer.py /tmp/coding-traces.jsonl --no-serve
```

查看器支持 .pt 与 .jsonl，读取每个样本/记录里的 trace，再生成同名的 .trace_timeline_cache.json 和 .trace_timeline_viewer.html。它是消费已有记录，不会重新执行 Agent。

来源：[文件读取:571–589](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tools/trace_timeline_viewer.py#L571-L589)、[输出路径:615–622](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tools/trace_timeline_viewer.py#L615-L622)。

<details>
<summary>清单范围、示例验证与内部辅助函数</summary>

- 清单根据固定版本 trace_utils.py 的函数定义核对：9 个无下划线函数、2 个数据类和相关方法，使用角色另依据官方文档及调用位置确定。TRACE_VERSION、TRACE_CHILDREN_KEY 和 SGLang 键/阶段常量提供格式约定，不是另外的调用工具。
- _ensure_trace_carrier、_coerce_handles、_append_event、_record_span_end、目标推断、子阶段展开等属于上述接口的内部实现；已有函数卡继续回查，不为它们建立第二份公共用法清单。
- 对 9 个函数及 4 个可见方法做了隔离示例验证，沿用原 trace_utils 实现，并从 types.py 提取原 Sample 类，避开当前环境缺少 numpy 的无关模块导入。验证说明这些用法的现有行为，不等于官方建议业务逐个手动调用。
- 另外提取原 generate 函数，替代业务协程，在临时目录验证正常返回和异常时的 JSONL 追加；检查记录中的 trace，并在完成后删除临时文件。此演示没有运行真实 Agent。
- .pt 保存与查看器路径依据源码静态核对；没有启动训练、实际 .pt 保存或时间线服务。示例验证不等于完整环境集成已经验证。

</details>
