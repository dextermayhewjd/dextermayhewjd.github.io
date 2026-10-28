# _coerce_handles

> 当前调用链：[trace_span](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#coerce-sample-path) → **_coerce_handles**。先调用 [_adapt_trace_target](../02-short-term-memory/functions/slime/observability/trace_utils.py/_adapt_trace_target.md)，返回后在 Sample 分支调用 [bind_trace](../02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md)。本函数读完返回 trace_span:353，继续 362 行。

- 源码定位：[trace_utils.py:616–627](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L616-L627)，固定版本 18868a79。
- 首次接触：2026-10-27，Step 014 的记录位置回查。
- 最近认识更新：用户指出这里是黑盒，后要求分层；尚无对本函数机制的确认。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手核对源码后整理。

1. **使用场合**：trace_span 接到 target 后，需要统一得到可操作的追踪句柄列表。
2. **具体内容**：先适配 target，再按类型处理；已有 TraceHandle 包成列表，Sample 委托 bind_trace，列表逐项递归并汇总，其他结果返回空列表。
3. **建议构建的心智模型**：

   > 本函数负责“把输入整理成 TraceHandle 列表”。当前 Sample 怎样绑定追踪数据，由下一层 bind_trace 负责。

4. **调用代码**（trace_span:353）：

   ```python
   handles = _coerce_handles(target)
   ```

## 本场景的输入与输出

输入：target 是 generate.py 传给 trace_span 的同一个 base_sample，类型为 Sample。

输出：正常绑定后返回 [handle]；handle 是 bind_trace 返回的 TraceHandle。这里组织列表，不创建当前阶段的开始或结束事件。

### 本函数的调用顺序

下面仅保留本次 Sample 路径（616–621），其他类型的分支在后表定位：

```python
target = _adapt_trace_target(target)
if isinstance(target, Sample):
    return [bind_trace(target)]
```

- 当前主读本函数。第一句的 [_adapt_trace_target](../02-short-term-memory/functions/slime/observability/trace_utils.py/_adapt_trace_target.md#sample-path) 已作局部说明：当前 Sample 原样返回；接回 617 完成赋值，随后继续本函数的类型判断。说明已提供不代表用户已确认理解。
- 走到 bind_trace(target) 时，带着同一个 Sample 进入 [bind_trace 卡](../02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md)。
- bind_trace 返回一个 handle 后，本函数将其放进列表并返回。先完成括号内的调用，再构造外层列表。

### 为什么有三个条件，当前读哪一个

三个 if 按适配后的输入类型分路处理，最终都交回句柄列表。每个匹配分支执行 return 后就结束本次调用，不会再继续执行后面的分支。

| 条件分支 | 本函数怎样处理 | 当前阅读 |
| --- | --- | --- |
| ① TraceHandle | 已有句柄，直接返回 [target] | 了解用途；当前 Sample 不走这里 |
| **② Sample** | **调用 bind_trace，再将得到的句柄装进列表返回** | **当前只沿这条路** |
| ③ list | 逐项调用 _coerce_handles，将结果汇总到同一个列表 | 了解用途，暂不展开递归 |
| 都不匹配 | 返回 [] | 函数末尾的兜底返回 |

本次 target 来自 base_sample；前面的 _adapt_trace_target 原样返回这个 Sample。因此先跳过 TraceHandle 条件，再进入 Sample 条件，并在 return [bind_trace(target)] 结束。当前下一处观察是这一行如何先得到 handle，再返回 [handle]。

**返回上一层**：[trace_span 的第一段](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md#runtime-enter)接住 handles，继续到 362 行准备时间；本次得到的是含一个句柄的列表。

## 我的直接表述（原话）

> 我感觉开头的coerce handles 对我来说就是黑盒 我都不知道这中间是在做什么这件事情

这是当前疑问，尚无独立的机制复述。[原讨论](../04-flow.md#step014-coerce-sample-path)。

## 尚不清楚

- 输入整理、子调用返回与列表构造的顺序，仍待用户阅读反馈。
- _adapt_trace_target 对 Sample 以外包装对象的适配，本轮只定位。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：[本函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L616-L627)；[适配函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L739-L751)。
- [分层整理依据](../04-flow.md#step014-function-layers)。当前为静态源码说明，未运行真实 Agent，不代表用户已掌握。

</details>
