# 01 · 阅读范围：单个 agent_run 的 Trace

[步骤入口](../README.md) · [函数索引](../02-short-term-memory/overview.md) · [前序记录](../03-long-term-memory/overview.md)

## 1. 阅读目标

先看清 trace_span 怎样运行：**进入 with 时开始记录，在 yield 处交回业务，离开 with 时恢复并结束记录。** 本步只跟随一个正常执行的 agent_run；scope 保留整体位置、骨架和阅读入口，具体语句与中间数据的变化写在 trace_span 函数卡。

用户已确认主题 03，并沿用此前明确收窄的 agent_run 场景。harness.run 的业务职责沿用已有阅读；本轮重点是外面的追踪包装。

## 2. 入口与最小前置

- 业务入口：[generate.py 中 _generate 的 agent_run 片段，286–295 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L295)。这只是完整任务中的一个执行阶段。
- 组织本次追踪的是 [trace_span:345–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345-L425)：进入记录开始，把控制交给业务，退出记录结束。
- base_sample 是本次任务的 Sample，携带 trace 字典；as span 得到用于设置当前阶段属性的 TraceSpanContext。当前先看 base_sample 怎样交给 _coerce_handles；as span 的交出放到阶段②。
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

### 3.3 一点一点读：先分清数据用途，再进入事件写入

<a id="current-reading"></a>

**当前已从输入整理返回 trace_span，进入阶段②的 362–384。** 先补清两份旧上下文与两个本次空列表各做什么，再沿循环进入 _append_event。数据准备与登记要保留在骨架；ContextVar 的完整机制和 yield 按后续问题展开。

```python
stack_before = _TRACE_STACK.get()
handle_stack_before = _TRACE_HANDLE_STACK.get()
span_records = []
new_entries = []
for handle in handles:
    span_id = _new_span_id()
    _append_event(..., kind="span_start")
    span_records.append((handle, span_id))
    new_entries.append((handle.trace_id, span_id))
token = _TRACE_STACK.set(stack_before + tuple(new_entries))
handle_token = _TRACE_HANDLE_STACK.set(handle_stack_before + (tuple(handles),))
```

上面是导航裁剪；具体参数、输入和状态变化进入[trace_span 卡的当前段](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#span-records)。timestamp 在 362 行准备；handles 已由 _coerce_handles 返回。[本段的记录归属](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#record-ownership)解释哪些留在父卡，哪些进入子卡。

| 本次小步 | 当前看清什么 | 读到哪里停 |
| --- | --- | --- |
| 准备 · 363–366 | 两个 before 读取旧上下文，两个空列表保存本次新增数据；set 的返回 token 用于退出恢复 | 当前先接清这组关系，再进入循环 |
| 第一步 · 369–370 | 从 handles 取出一个句柄，为这次阶段分配 span_id | 回到循环内，尚未写事件 |
| **第二步 · [_append_event](../02-short-term-memory/functions/slime/observability/trace_utils.py/_append_event.md)** | **当前细读：组装 event、追加到 handle.carrier["events"]、返回字典** | **回到 381；当前调用方不接返回值，依靠追加的副作用** |
| 第三步 · 381 | span_records 保存 (handle, span_id)，供退出时写结束事件 | 留在父卡，接清用途后继续 382 |
| 第四步 · 382–383 | new_entries 保存 (trace_id, span_id)，交给上下文栈 | 留在父卡，先理解登记和查父编号的用途，栈的完整实现按需展开 |

本次停止条件：能区分 handles、事件列表、span_records、new_entries 的用途，并看清开始事件实际写在哪里。结束事件在退出 with 时执行，本次只借它说明配对信息为什么需要保留。

<details>
<summary>此前阶段①：输入整理与逐层回查路线</summary>

#### 第一步 · 先看清三种入口，再对回当前 Sample【已讨论，保留回查】

从 trace_span:353 的这行进入：

```python
handles = _coerce_handles(target)  # target 是本次的 base_sample
```

打开 [_coerce_handles 函数卡](../02-short-term-memory/functions/slime/observability/trace_utils.py/_coerce_handles.md#input-forms)，先对照三种输入的来源、形态、处理和返回：已有 TraceHandle 直接装入列表，Sample 绑定后装入列表，一组目标逐项整理并合并。列表分支用两个元素的例子看清递归与 extend；随后再回到本次实际的 Sample 路径：

此处回查的是 _coerce_handles；第一句的 _adapt_trace_target 已作局部说明，当前 Sample 原样返回，需要复查时可打开[适配函数卡](../02-short-term-memory/functions/slime/observability/trace_utils.py/_adapt_trace_target.md#sample-path)。下面只是当前实际经过的片段，不是函数的全部分支。

```python
target = _adapt_trace_target(target)  # 当前 Sample 原样返回
if isinstance(target, Sample):
    return [bind_trace(target)]
```

本轮先把三种入口为什么存在、各自怎样得到句柄列表接清，再定位当前：传进来的是 Sample，选中第二个分支；bind_trace 返回一个 handle，本函数返回 [handle]。**能说明三种输入如何统一为列表，并对回当前调用后，返回 trace_span:353。** 后面的开始事件和 yield 随后接续。

如果仍不清楚 bind_trace 交出的对象是什么，才进入第二步；如果这一层的交接已经清楚，就直接走第四步返回主线。

#### 后续入口 · 按当前疑问进入，并带着结果返回

```text
第一步：_coerce_handles 三种入口与统一返回                  已讨论
    ├─ 继续看 Sample 怎样得到句柄 → 第二步：bind_trace      【前一处定位】
    │      └─ trace 字典怎样准备仍不清楚 → 第三步：_ensure_trace_carrier
    │             └─ 返回字典 → 回第二步创建 handle
    │      └─ 返回 handle → 回第一步构造 [handle]
    └─ 返回列表 → 第四步：回到 trace_span:353，再继续 362
```

| 阅读小步 | 何时进入、这次看什么 | 读完带什么返回 |
| --- | --- | --- |
| 第一步 · [_coerce_handles](../02-short-term-memory/functions/slime/observability/trace_utils.py/_coerce_handles.md) | 已有初步表述，保留回查；理解三种输入与统一返回，再对回实际 Sample 路径 | [handle] 回到 trace_span:353 |
| **第二步 · [bind_trace](../02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md)** | 准备或复用 sample.trace，再创建 TraceHandle；已有 Sample 不会被重新创建 | 一个 handle 回到 _coerce_handles:621，随后放进列表 |
| 第三步 · [_ensure_trace_carrier](../02-short-term-memory/functions/slime/observability/trace_utils.py/_ensure_trace_carrier.md) | 第二层仍不清楚字典准备时；看传入字典或 None，怎样得到可用字典 | 字典回到 bind_trace:240，赋值后继续创建句柄 |
| 第四步 · [返回 trace_span](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-enter) | 句柄列表的交接已清楚；先完成 353 的赋值，再接 362 的时间准备 | 返回主线后再进入阶段②，当前不预先展开 |

本轮局部入口是 _coerce_handles，向下最多回查 bind_trace、_ensure_trace_carrier 两层。每个子调用读完先回直接调用者；更深问题另记，保持当前返回路线。

<details>
<summary>句柄准备接清后，再读的三个运行阶段</summary>

| 后续阶段 | 入口与问题 | 返回位置 |
| --- | --- | --- |
| ② 开始与交出 | [trace_span:369–398](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-start-yield)：写开始、保存编号，yield 交出什么 | generate.py:287 |
| ③ 业务与属性 | [generate.py:287–295](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-body)：业务退出码怎样补进当前 span | 离开 with，恢复 trace_span:398 |
| ④ 恢复与收尾 | [trace_span:412–425](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-exit)：正常结束事件和上下文恢复 | generate.py:296 |

</details>

</details>

<a id="trace-function-layers"></a>

### 3.4 已展开部分的调用层级：一层一张卡

下面的缩进表示谁调用谁；输入整理与事件写入是 trace_span 内的不同调用。父卡保存自己的处理和对下一层的交接，详细实现进入子卡。

```text
trace_span                              组织阶段的进入与退出
├─ _coerce_handles                      把输入整理成句柄列表
│  ├─ _adapt_trace_target               Sample 原样返回
│  └─ bind_trace                        绑定字典，创建一个句柄
│     └─ _ensure_trace_carrier          准备追踪字典
└─ _append_event                        当前细读：组装并写入一条事件

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

阅读从 _coerce_handles 的类型分派接到 bind_trace 的 Sample 绑定；需要知道句柄如何关联字典时，进入 bind_trace，再按需回查字典准备。结束事件的 [_record_span_end:499–518](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L499-L518)仍只在第四段按需回查。

**停止位置**：能沿同一次调用指出进入、yield、业务执行、恢复的先后关系，以及开始、结束事件各何时出现。取消与异常可在正常路径理解后按问题作对照；本次不预展开全部错误处理、父子栈、跨进程传播、文件导出或查看器。

<details>
<summary>版本、调取与来源</summary>

- 本地 HEAD 与本次查询官方 main 都是 18868a79，工作区干净；[核对证据](source-evidence.json)。
- [完整相关源码摘录](source-excerpts.md)仅供按需回查，长函数不代表必须整段展开。
- [历史 trace_span 卡](trace-span-step001-source.md)来自 Step 001，其模型请求场景与本步的 agent_run 场景分开保存。
- [范围确认与第一观察点](../04-flow.md#step014-start)。未运行真实 CLI、模型或 Trace 测试。

</details>
