# _coerce_handles

> 当前调用链：[trace_span](trace_span.md#coerce-sample-path) → **_coerce_handles**。先调用 [_adapt_trace_target](_adapt_trace_target.md)，返回后在 Sample 分支调用 [bind_trace](bind_trace.md)。本函数读完返回 trace_span:353，继续 362 行。

- 源码定位：[trace_utils.py:616–627](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L616-L627)，固定版本 18868a79。
- 首次接触：2026-10-27，Step 014 的记录位置回查。
- 最近认识更新：2026-10-27，用户已用“统一格式”和 isinstance 概括输入整理，并强调 handles 数据结构；此前已表述 Sample 委派及列表逐项处理。助手进一步区分 Sample 本体、TraceHandle 与 list[TraceHandle]，细化说明尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手核对源码后整理。

1. **使用场合**：trace_span 接到 target 后，需要统一得到可操作的追踪句柄列表。
2. **具体内容**：先适配 target，再按类型处理；已有 TraceHandle 包成列表，Sample 委托 bind_trace，列表逐项递归并汇总，其他结果返回空列表。
3. **建议构建的心智模型**：

   > 本函数接收三种形态，统一交回句柄列表：已有句柄直接使用，Sample 先绑定，一组对象逐项整理后合并。
   >
   > ```text
   > _coerce_handles
   > ├─ TraceHandle → [原句柄]
   > ├─ Sample      → [bind_trace 返回的句柄]
   > └─ list        → 逐项走上述规则，合成句柄列表
   > ```
   >
   > 分支依据是适配后的输入类型；三条路共享同一种返回形式。

4. **调用代码**（trace_span:353）：

   ```python
   handles = _coerce_handles(target)
   ```

## 本场景的输入与输出

本轮按用户要求完整对照三种入口。当前 agent_run 真正传入的仍是 base_sample；另外两种用于理解同一个函数的接口。下面 sample_a、sample_b 代表 Sample 对象，handle_b 代表已经准备好的 TraceHandle。示例中的对象名称是教学示意，未运行真实 Agent。

### 返回值的数据结构：handles 里面是什么

下面对应当前 **Sample → bind_trace → [handle]** 的正常路径，只展示理解本次交接所需的字段：

```text
handles：列表
└─ handle：TraceHandle
   ├─ trace_id：追踪编号
   └─ carrier ──→ sample.trace：追踪字典
                    └─ events：事件列表
```

handles 是本函数交回的列表；handle 是其中一个元素。当前路径中，handle.carrier 与 sample.trace 指向同一份字典，因此后续向 handle.carrier["events"] 追加事件，就会写入这份样本的追踪记录。TraceHandle 的其他字段在本图中省略。

若输入已经是 TraceHandle，carrier 由该句柄自身携带，不要求它一定关联某个当前可见的 Sample；列表输入则可能得到多个这样的句柄。

<a id="input-forms"></a>

### 先区分输入本身的形态

| 手里已有的东西 | 实参示意 | 为什么需要这条路 | 返回形式 |
| --- | --- | --- | --- |
| 一个 TraceHandle | handle_b | 前面已经准备好句柄，可直接复用 | [handle_b] |
| 一个 Sample | sample_a | 业务调用方持有样本，需要从样本取得句柄 | [handle_a] |
| 一组目标 | [sample_a, handle_b] | 调用方把多个目标一起交来，需要逐个整理 | [handle_a, handle_b] |

**三种类型不是三个必须依次执行的阶段。** 每次看当前传入什么，选择对应分支；列表分支内部会对各元素再次调用本函数。三条路最终都返回 list[TraceHandle]，因此 trace_span 后面可以统一写 for handle in handles。

### ① 已有 TraceHandle：直接使用

真实使用例：Adapter 的 Session.trace 类型是 TraceHandle；common.py:412 将它传给 trace_span。这说明调用方可能已经持有句柄，而不是只有 Sample。

本分支源码（618–619）：

```python
if isinstance(target, TraceHandle):
    return [target]
```

输入是 handle_b，输出是 [handle_b]：新建外层列表，里面仍是原来的句柄。本分支不再调用 bind_trace。

### ② 手里是 Sample：先取得句柄，再装进列表【当前 agent_run】

真实使用例：generate.py:286 把 base_sample 传给 trace_span，它随后作为 target 进入本函数。

本分支源码（620–621）：

```python
if isinstance(target, Sample):
    return [bind_trace(target)]
```

调用与返回按这个顺序发生：

```text
sample_a
   → bind_trace(sample_a)
   → 得到 handle_a
   → 构造 [handle_a]
   → 返回列表
```

这里 Sample 是业务对象，TraceHandle 是供追踪代码使用的对象。bind_trace 创建的句柄通过 carrier 关联 sample_a.trace；具体绑定过程在 [bind_trace 卡](bind_trace.md)。本层只需接住一个句柄，再把它放进列表。

### ③ 手里是一组目标：逐项整理，再合并

这是源码明确支持的接口形态。下面的混合列表是教学构造，不声称当前 agent_run 或已检查的调用现场实际使用它。

输入示意：

```python
[sample_a, handle_b]
```

本分支源码（622–626）：

```python
if isinstance(target, list):
    handles = []
    for item in target:
        handles.extend(_coerce_handles(item))
    return handles
```

| 当前元素 | 再次调用本函数时走哪里 | 该次调用返回 | 合并后的 handles |
| --- | --- | --- | --- |
| sample_a | Sample 分支，绑定得到 handle_a | [handle_a] | [handle_a] |
| handle_b | TraceHandle 分支，复用它 | [handle_b] | [handle_a, handle_b] |

_coerce_handles(item) 表示把同一套规则用于一个元素。extend 将返回列表里的各个元素加入 handles，所以最终得到一层句柄列表，而不是 [[handle_a], [handle_b]]。

如果输入是 [sample_a, sample_b]，就逐个通过 Sample 分支取得两个句柄。输入列表也可以为空，结果就是 []；嵌套列表会继续用同一规则处理。本轮先用上面两个元素的例子理解这一层循环。

### 三条路为什么要统一返回列表

后面的 trace_span 使用的是同一种代码形态：

```python
for handle in handles:
    _append_event(..., kind="span_start")
```

一个目标对应一个列表元素，多个目标对应多个列表元素；调用方不必再次区分最初拿来的是句柄、样本还是列表。

三个分支之前仍有 target = _adapt_trace_target(target)。当前 Sample 和 TraceHandle 都原样返回；其他适配用途见[适配函数卡](_adapt_trace_target.md)。如果适配后的对象不匹配三个分支，本函数末尾返回 []。

**回到实际场景**：本次 base_sample 选中②。得到 [handle] 后，返回 [trace_span:353](trace_span.md#runtime-enter) 完成 handles 的赋值，继续 362 行准备时间。本函数还没有写入这个阶段的开始事件。

## 我的直接表述（原话）

本次对统一格式和数据结构的概括：

> 也就是可以简单的理解为这里的在做的内容更多的是再处理这里的sample 并且将其转化为统一的格式？
>
> 也就是这里的tracehandle这个格式是我的理解
> 所以使用isinstance来做出对应的判断是我的理解
>
> 我的大致的理解是这里的数据结构非常重要
> 也就是到底是如何构建这里的handles 我觉得会非常重要

用户随后询问下一处阅读入口。[本次核对与接续建议](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-after-coerce-next)。统一的是返回接口：list[TraceHandle]；原 Sample 继续存在，句柄通过 carrier 关联其 trace 字典。这项细化由助手说明，不代填用户理解。

本次关于 Sample 和列表路径的理解：

> 这里的bind trace 是否也需要查看一下呢？
> 简单来看好象是返回了一个tracehandle 这是我的理解
>
> 也就是如果是一个sample
> 那么就先初始化了这里的sample之后
> 返回了一个这里的tracehandle？
>
> 这是我的理解 具体如何处理这里的target是发生在bind trace的部分
> 最后如果只是一个list的话
> 就会对于其中的每一个item进行处理来得到一个handles
> 这里是我的理解
>
> 对于coerce handles的理解

[本次核对与继续 bind_trace](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-bind-trace-reading)。助手认可返回句柄与逐项处理的关系；“初始化 sample”及 target 的处理职责另行收窄，不能将助手修正直接写成用户确认。

本次要求完整说明三个入口：

> 是否应该把三种入口写清楚呢？
> 否则我感觉我完全不清楚这里到底是在干什么这件事情
> 我觉得是否需要讲清楚和讲透这三个分支呢？
> 这样我才能够继续考虑如何
> 这里这一步到底是在做什么这件事情

以下保留此前问题：

> 我感觉开头的coerce handles 对我来说就是黑盒 我都不知道这中间是在做什么这件事情

这是此前的黑盒问题；本次新增表述见上方，原讨论保留。[原讨论](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-coerce-sample-path)。

## 尚不清楚

- 用户已说清 Sample 委托 bind_trace、列表逐项处理并汇总的关系；已有 TraceHandle 分支及 extend 合并的具体语句，尚无独立复述。
- bind_trace 处理的是已有 Sample 的追踪绑定；类型分派和列表遍历仍在本函数。对这一职责边界的修正尚待用户反馈。
- 用户已指出统一格式与 isinstance 判断；统一结果为 list[TraceHandle]、Sample 与句柄共享 trace 字典的细化，尚待确认。
- _adapt_trace_target 对 Sample 以外包装对象的适配，本轮只定位。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：[本函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L616-L627)；[适配函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L739-L751)。
- TraceHandle 入口依据：[Session.trace 类型与调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L412)，字段声明在同文件 57 行；Sample 入口依据：[agent_run 调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286)。列表示例按本函数接口构造，未定位成当前业务路径。
- extend 的语言依据：本地《Fluent Python》英文 ch02:438，原文“Append items from iterable `it`”；中文 ch02:424，“追加可迭代对象 `it` 中的项”。
- [补充三个入口之前的卡片](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/coerce-handles-before-three-inputs.md)保留原文与出处。
- [分层整理依据](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-function-layers)。当前为静态源码说明，未运行真实 Agent，不代表用户已掌握。

</details>
