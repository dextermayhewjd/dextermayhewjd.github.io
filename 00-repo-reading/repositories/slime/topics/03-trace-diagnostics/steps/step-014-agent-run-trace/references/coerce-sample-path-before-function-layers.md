# 分层前的 Sample 调用链说明

这是 2026-10-27 从 trace_span 父卡拆分前保留的历史文本。当前请从[分层阅读入口](../01-scope.md#trace-function-layers)进入。

<a id="coerce-sample-path"></a>

#### 当前展开：_coerce_handles 怎样处理这个 Sample

用户明确指出这句仍是黑盒。本轮只跟随 target 是 base_sample 的路径；函数对已有 TraceHandle、列表等输入的其他分支先保留位置。

```text
trace_span：handles = _coerce_handles(base_sample)     等待右侧调用返回
    │
    └─ _coerce_handles(base_sample)                   616
         ├─ _adapt_trace_target(base_sample)          617 → 742–743
         │    └─ 已经是 Sample，原样返回
         └─ bind_trace(base_sample)                   621 → 238
              ├─ _ensure_trace_carrier(...)          240 → 213
              │    └─ 取得 trace 字典，补齐必需字段后返回
              └─ 创建并返回 TraceHandle              245
                   carrier 指向 base_sample.trace

bind_trace 返回 handle → _coerce_handles 返回 [handle]
    → trace_span 得到 handles，再继续 timestamp = time.time()
```

先读 _coerce_handles 当前经过的语句（616–621，教学裁剪）：

```python
target = _adapt_trace_target(target)   # 这个 Sample 原样回来
if isinstance(target, Sample):
    return [bind_trace(target)]
```

`return [bind_trace(target)]` 的次序是：先调用 bind_trace 得到一个 handle，再把它放进列表，最后把列表返回。所以 handles 最终是 **[一个 TraceHandle]**。

接着只看 bind_trace 的正常路径（238–251，省略辅助字段和异常处理）：

```python
sample.trace = _ensure_trace_carrier(
    getattr(sample, "trace", None),
    sample_id=sample.index,
    group_id=sample.group_index,
)
return TraceHandle(
    trace_id=sample.trace["trace_id"],
    carrier=sample.trace,
    # 其他身份字段省略
)
```

- _ensure_trace_carrier 做的是字典准备：没有 trace 就建字典，补齐 version、trace_id、events 等字段，再返回该字典；已有 trace 和 events 会复用，已有事件不清空。
- TraceHandle 是供后续追踪代码使用的对象，带有追踪编号和 carrier。这里 carrier=sample.trace，两个名字指向同一份字典，不是复制一份样本。
- _coerce_handles 把支持的输入整理成统一的 TraceHandle 列表，后续才可以统一写 for handle in handles。
- **这句返回时只完成了记录准备，尚未写本阶段的 span_start。** 看到 handles 已取得，就回到 trace_span:362；开始事件在后面的 372 行写入。

源码回查：[适配当前 Sample:739–751](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L739-L751) · [准备字典与绑定:213–254](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L213-L254)。这些说明属于第一段的当前回查，未标记用户已经理解。

