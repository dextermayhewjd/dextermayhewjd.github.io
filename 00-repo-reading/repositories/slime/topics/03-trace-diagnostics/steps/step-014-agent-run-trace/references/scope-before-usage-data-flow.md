# 使用视角改写前的 scope 快照

2026-10-27 保存。以下保留改写前的完整内容，仅重算相对链接；当前阅读入口以 [01-scope.md](../01-scope.md) 为准。

---

# 01 · 阅读范围：单个 agent_run 的 Trace

[步骤入口](../README.md) · [函数索引](../02-short-term-memory/overview.md) · [前序记录](../03-long-term-memory/overview.md)

## 1. 阅读目标

先看清 trace_span 怎样运行：**进入 with 时开始记录，在 yield 处交回业务，离开 with 时恢复并结束记录。** 本步只跟随一个正常执行的 agent_run；scope 保留整体位置、骨架和阅读入口，具体语句与中间数据的变化写在 trace_span 函数卡。

用户已确认主题 03，并沿用此前明确收窄的 agent_run 场景。harness.run 的业务职责沿用已有阅读；本轮重点是外面的追踪包装。

## 2. 入口与最小前置

- 业务入口：[generate.py 中 _generate 的 agent_run 片段，286–295 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L295)。这只是完整任务中的一个执行阶段。
- 组织本次追踪的是 [trace_span:345–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345-L425)：进入记录开始，把控制交给业务，退出记录结束。
- base_sample 是本次任务的 Sample，携带 trace 字典；as span 得到用于设置当前阶段属性的 TraceSpanContext。输入整理从 base_sample 进入 _coerce_handles；as span 的交出在后面的交付阶段。
- TraceHandle、TraceSpanContext 先按必要字段和接口理解；绑定过程按当前卡点逐层回查；完整类卡、ContextVar 栈和线程传播保留后续。

## 3. 核心骨架与阅读导航

<a id="overall-position"></a>

### 3.1 整体位置：任务执行中的一个观察点

这里按业务职责定位，其他阶段只留背景，不枚举它们的 trace_span。

```text
generate → _generate：一份 Coding Agent 任务
├─ 准备会话、沙箱与工作区                       既有背景
├─ agent_run：执行 Agent CLI                   本步唯一观察点
│  └─ trace_span 包装 harness.run
│     ├─ 进入：记录阶段开始
│     ├─ 执行业务：获得 agent_exit_code
│     ├─ span.set：补充退出码属性
│     └─ 离开：记录阶段结束
└─ 提取改动、评测、整理样本                     既有背景
```

### 3.2 局部骨架：with 两边怎样接起来

这里的 **span 是一次有开始、有结束的具名执行阶段**，例如这一次 agent_run。它的记录让后续查看者知道该阶段何时开始、何时结束，以及退出码是什么。

调用现场仍是 generate.py:286–295，仅省略 harness.run 的实参：

```python
with trace_span(base_sample, "agent_run", record_error=False) as span:
    agent_exit_code = await harness.run(...)  # 业务在这里执行
    span.set("exit_code", agent_exit_code)    # 为本阶段补充结果属性
```

产物是 base_sample.trace["events"] 中配对的 span_start、span_end；同一个 span_id 将它们关联，结束事件可带上退出码。[函数卡](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md)保留完整的当前输入、产物示例与逐段代码。

<a id="trace-span-core"></a>

**保留交接的教学骨架。** 保留进入前的四行准备、两套上下文登记及退出恢复；省略时间与编号生成、父编号选择、具体调用参数和异常分支内部。注释中的①至④对应运行阶段；③发生在调用方。代码只用于导航，不能独立运行。

```python
@contextmanager
def trace_span(target, name, *, attrs=None, record_error=True):
    # ① with 进入后运行到这里，取得记录位置
    handles = _coerce_handles(target)                   # 353

    stack_before = _TRACE_STACK.get()                   # 363：读取旧编号上下文
    handle_stack_before = _TRACE_HANDLE_STACK.get()     # 364：读取旧句柄上下文
    span_records: list[tuple[TraceHandle, str]] = []      # 365：本次结束配对
    new_entries: list[tuple[str, str]] = []              # 366：本次编号条目

    # ② 准备时间与编号后，写开始并保存配对信息
    for handle in handles:
        _append_event(..., kind="span_start")           # 372
        span_records.append((handle, span_id))
        new_entries.append((handle.trace_id, span_id))
    token = _TRACE_STACK.set(stack_before + tuple(new_entries))
    handle_token = _TRACE_HANDLE_STACK.set(handle_stack_before + (tuple(handles),))
    span_context = TraceSpanContext(...)

    try:
        yield span_context                             # 398：转到③调用方业务
    except BaseException:
        ...  # 原码尝试记录异常结束，再重新抛出
        raise
    else:
        # ④ with 正常结束后恢复，写结束事件
        span_context.finalize(_record_span_end(...))    # 414
    finally:
        _TRACE_STACK.reset(token)                      # 419
        _TRACE_HANDLE_STACK.reset(handle_token)        # 423
```

```text
① 进入 with → ② trace_span 写开始，yield 交回操作对象
                                  ↓
                ③ 调用方 harness.run → span.set
                                  ↓ 离开 with
                ④ trace_span 恢复，写结束，恢复上下文
```

@contextmanager 提供的管理器由 with 驱动进入和退出；调用 trace_span(...)、运行到 yield、恢复退出是不同的时刻。[函数卡的运行对照](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#normal-lifecycle)逐段说明此时在哪个文件、已有数据、发生的变化和下一次交接。

<details>
<summary>回到原文件时，怎样认出暂时折叠的代码</summary>

- 352–360、385–388：取得记录位置或初始化失败时的降级路径，可能 yield target。
- 363–384：读取、登记父子阶段关系和当前追踪上下文；419、423 恢复进入前的上下文。
- 399–411：业务抛出异常时也尝试写结束事件，然后重新抛出；record_error 决定是否自动附加异常类型和消息。
- 412–416：上面骨架的正常结束记录实际位于 else；上下文恢复实际位于 finally，不只在成功时执行。
- 调用处省略 as 仍会记录开始与结束；nullcontext 则是其他调用现场选择的空上下文。两者与此处降级分支分开。

本轮的目标就是追踪，因此开始/结束事件和时间戳属于核心动作。不能因为通用剪枝规则提到“日志与耗时统计”，就在这里把它们删掉。

</details>


<a id="reading-order"></a>
<a id="current-reading"></a>

### 3.3 完整阅读顺序：从输入整理到退出恢复

本节保存 **Step 014 的完整阅读路线**。编号表示这一轮按什么顺序理解本场景；已经讨论过的节点继续保留，后续回顾仍从同一编号进入。具体讲解在函数卡，实际问答在 04-flow，详细进度以[唯一路线的“当前接续”](../../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准；本页只标本轮进入的编号，整条路线保持不变。

**本轮阅读入口：先看 [trace_utils 的模块职责与最终用途](../../../README.md#trace-utils-purpose)，再看[同一个阶段的 Trace 怎样逐步形成](history/procedures/trace-span-lifecycle.md)。** 用户仍不清楚模块做什么，先把“业务打点 → 样本记录 → 保存并查看时间线”接起来；下方十项继续作内部源码定位，不要求先逐层读完，不因讲解连通就标为已掌握。

第 3–6 项的连续执行和数据变化，配合短期记忆中的 [Procedure：开始阶段的状态流转](history/procedures/trace-span-start.md)阅读；完整编号路线仍保留在下面。

下面十项覆盖本步正常路径，不要求一次全部读完。第 3–5 项属于同一个 for 循环：对一个 handle 完成这三项后，才处理下一个 handle。

```text
1. 统一输入：_coerce_handles → handles
   ├─ 输入外形不清楚：回查 _adapt_trace_target，返回第 1 项
   └─ Sample 怎样取得句柄：bind_trace → _ensure_trace_carrier
      逐层返回，接回第 1 项的 handles
    ↓
2. 准备本次状态：读两个旧栈，创建两个空列表
    ↓
对 handles 中的每个 handle，依次完成：
   3. 生成 span_id，确定 parent_span_id
   4. _append_event：写入 span_start
   5. 保存 span_records 与 new_entries
    ↓ 循环结束
6. 登记当前上下文：set 两个栈，保存恢复用的 token
    ↓
7. 创建 TraceSpanContext，yield 交给 as span
    ↓ 转到调用方
8. harness.run 执行业务，span.set 补充退出码
    ↓ 正常离开 with，回到 trace_span
9. _record_span_end：写结束事件，finalize 保存结束记录
    ↓
10. reset 两个上下文 → 返回 _generate，继续后面的业务
```

| 编号与阅读入口 | 关键源码 | 这一项要看清什么 | 返回或继续位置 |
| --- | --- | --- | --- |
| **1. [统一输入与句柄列表](../02-short-term-memory/functions/slime/observability/trace_utils.py/_coerce_handles.md)** | trace_span:353 → _coerce_handles:616–627 | 三种输入怎样统一返回 list[TraceHandle]；需要时从卡片进入适配、绑定和字典准备 | 返回 trace_span:353 完成赋值，再到 362 |
| **2. [进入前的状态准备](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#entry-preparation)** | trace_span:362–366 | timestamp、两个 before、两个空列表分别给后面哪一步使用；按需进入[编号栈](../references/trace-stack.md)与[句柄栈](../references/trace-handle-stack.md)说明，区分模块级对象和本次局部变量 | 两份状态说明读完都回到本项，再进入 369 的循环 |
| **3. [本阶段与父阶段编号](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#span-identifiers)** | trace_span:370–371；[_get_current_parent_span_id:630–639](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L630-L639) | trace_id、span_id、parent_span_id 各标识什么；父编号明确给出与从旧栈查询的区别 | 带着本次编号进入 372 |
| **4. [写入开始事件](../02-short-term-memory/functions/slime/observability/trace_utils.py/_append_event.md)** | trace_span:372–380 → _append_event:587–613 | 传入的身份、阶段与时间怎样组成 event，写进哪里；返回值与写入副作用分开看 | 返回 trace_span:381 |
| **5. [保存配对与上下文条目](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#record-bookkeeping)** | trace_span:381–382 | (handle, span_id) 和 (trace_id, span_id) 为什么各存一份，之后分别由谁使用 | 本轮循环完成；所有 handle 处理完后到 383 |
| **6. [登记当前上下文](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#context-registration)** | trace_span:383–384 | 两个旧栈怎样加上本次内容；set 返回的 token 与旧栈值有什么区别 | 带着已登记的上下文到 390；恢复在第 10 项 |
| **7. [交出本阶段操作对象](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#span-context-yield)** | trace_span:390–398；[类卡](../02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md) | 创建的是本次 span 的操作对象；as span 拿到同一对象，end_attrs 用来接住业务附加信息 | 转到 generate.py:287，再看第 8 项的 span.set |
| **8. [业务执行与附加属性](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-body)** | generate.py:287–295；TraceSpanContext.set:78–81 | harness 返回退出码，span.set 将其写到哪个对象；此时 trace_span 在哪里暂停 | 正常离开 with，恢复 trace_span:398，接第 9 项 |
| **9. [写入结束并关闭阶段](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-exit)** | trace_span:414；[_record_span_end:499–518](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L499-L518)；finalize:100–104 | 怎样复用开始时的句柄和编号，附上结束属性，再保存返回的结束事件 | 回 trace_span 的 finally |
| **10. [恢复进入前的上下文](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#context-reset)** | trace_span:419、423 → generate.py:296 | reset 使用哪个 token，恢复后业务从哪里继续；不把结束记录与上下文恢复混为一件事 | 完成本步正常路径，回到 _generate 后续业务 |

读到子函数时，只展开解决该项问题所需的部分，按表中返回位置接回父函数。辅助调用的深层实现不自动成为新阅读项；本轮每次下钻仍控制在两层以内。异常、取消与降级分支保留在 3.2 的回查说明中，待正常路径接清后按问题补充。

<a id="trace-function-layers"></a>

### 3.4 已展开部分的调用层级：一层一张卡

下面的缩进表示谁调用谁；输入整理与事件写入是 trace_span 内的不同调用。父卡保存自己的处理和对下一层的交接，详细实现进入子卡。

```text
trace_span                              组织阶段的进入与退出
├─ _coerce_handles                      把输入整理成句柄列表
│  ├─ _adapt_trace_target               Sample 原样返回
│  └─ bind_trace                        绑定字典，创建一个句柄
│     └─ _ensure_trace_carrier          准备追踪字典
├─ _append_event                        组装并写入一条事件
└─ TraceSpanContext(...)                构造本次阶段的操作对象

trace_span 的 yield 把上述对象交给调用方 as span
└─ 调用方 span.set(...)                 将退出码暂存到 end_attrs

返回时逐层回到调用处：
字典 → bind_trace 创建 handle → _coerce_handles 返回 [handle]
     → trace_span 接住 handles，继续下一句
```

| 当前层 | 本层只解决什么 | 向下入口与返回位置 |
| --- | --- | --- |
| [trace_span](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-enter) | 何时准备、写开始、交给业务、写结束 | 353 进入 _coerce_handles；返回后继续 362 |
| [_coerce_handles](../02-short-term-memory/functions/slime/observability/trace_utils.py/_coerce_handles.md) | 根据输入类型，统一返回句柄列表 | 621 进入 bind_trace；返回后装入列表 |
| [bind_trace](../02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md) | 把追踪字典关联到 Sample，再创建句柄 | 240 进入 _ensure_trace_carrier；返回后赋值并创建 TraceHandle |
| [_ensure_trace_carrier](../02-short-term-memory/functions/slime/observability/trace_utils.py/_ensure_trace_carrier.md) | 创建或复用字典，准备字段 | 235 返回字典，回到 bind_trace:240 |
| [_append_event](../02-short-term-memory/functions/slime/observability/trace_utils.py/_append_event.md) | 组装、追加并返回一个事件字典 | 回到 trace_span:381，继续保存配对信息 |
| [TraceSpanContext](../02-short-term-memory/classes/slime/observability/trace_utils.py/TraceSpanContext.md) | 关联本次阶段，让业务代码补充结束属性 | trace_span:390 创建，398 交给调用方；set 由 generate.py:295 调用 |

阅读从 _coerce_handles 的类型分派接到 bind_trace 的 Sample 绑定；需要知道句柄如何关联字典时，进入 bind_trace，再按需回查字典准备。结束事件的 [_record_span_end:499–518](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L499-L518)仍只在第四段按需回查。

**停止位置**：能沿同一次调用指出进入、yield、业务执行、恢复的先后关系，以及开始、结束事件各何时出现。取消与异常可在正常路径理解后按问题作对照；本次不预展开全部错误处理、父子栈、跨进程传播、文件导出或查看器。

<details>
<summary>版本、调取与来源</summary>

- 本地 HEAD 与本次查询官方 main 都是 18868a79，工作区干净；[核对证据](../references/source-evidence.json)。
- [完整相关源码摘录](../references/source-excerpts.md)仅供按需回查，长函数不代表必须整段展开。
- [历史 trace_span 卡](../references/trace-span-step001-source.md)来自 Step 001，其模型请求场景与本步的 agent_run 场景分开保存。
- [范围确认与第一观察点](../04-flow.md#step014-start)；[完整路线重构前的 scope](../references/scope-before-stable-reading-route.md)。未运行真实 CLI、模型或 Trace 测试。

</details>

