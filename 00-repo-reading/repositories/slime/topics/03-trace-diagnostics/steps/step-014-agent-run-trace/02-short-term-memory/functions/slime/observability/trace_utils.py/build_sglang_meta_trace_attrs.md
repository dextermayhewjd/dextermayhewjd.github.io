# build_sglang_meta_trace_attrs

> [返回 scope 的工具总览](../../../../../01-scope.md#tool-catalog)。使用角色：**官方展示的组合工具**。

- 源码定位：[trace_utils.py:140–158](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L140-L158)，固定版本 18868a79。
- 首次接触：Step 014，2026-10-27 的完整工具用法核对；本轮从 scope 迁入函数卡。
- 最近认识更新：尚无针对本函数的直接理解表述。迁移与补充助手说明不计为用户新增认识。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手按官方指南及固定源码整理。

1. **使用场合**：SGLang 请求返回 output["meta_info"] 后，把其中适合追踪的元信息交给当前 span。
2. **具体内容**：选取相关字段、整理 finish_reason 和请求编号；存在 PD 时延数据时另外构造子阶段描述。它本身不写事件。
3. **建议构建的心智模型**：

   > meta_info → 属性/子阶段描述 → span.update → 当前目标上的记录。只有组合起来才完成业务需要的记录。

4. **调用代码**：见下节真实 generate 调用；保留业务侧的 max_new_tokens 开始属性，并接上响应元信息。

<a id="usage-method"></a>

## 使用方法：Slime 中的真实调用

**具体数据案例**：[具体服务器响应怎样变成开始/结束属性](../../../../examples/sglang-meta-update/README.md)，含 input.json、expected.json 与隔离核对结果。

**这里在做什么**：向 SGLang 请求生成后，把服务器返回的 token 数、结束原因、请求编号等元信息附在这次生成阶段上，方便查看这次请求的规模和结果。它服务于记录，不生成模型回答。

**真实调用位置**：[slime/rollout/sglang_rollout.py::generate，219–230](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L219-L230)。只省略 post 的请求参数，保留阶段名、开始属性及后续组合：

```python
with trace_span(sample, "sglang_generate", attrs={"max_new_tokens": sampling_params["max_new_tokens"]}) as span:
    output = await post(...)
    span.update(build_sglang_meta_trace_attrs(output["meta_info"]))
```

**真实输入**：output 来自这一次 post 响应，helper 接收其中的 output["meta_info"]；不是由 trace_utils 自己构造元信息。

| 时刻 | 业务数据 | Trace 中的结果 |
| --- | --- | --- |
| 进入 with | 已有 sample、请求参数 | 新增 sglang_generate 开始事件，带 max_new_tokens |
| post 返回 | 得到 output，其中包含 meta_info 与生成文本 | 开始事件仍在，本阶段尚未结束 |
| helper 返回并交给 update | output 保留；helper 产出整理后的 attrs | 普通属性进入 span.end_attrs；若存在子阶段描述，由 update 展开 |
| 正常离开 with | 继续处理 output | 新增结束事件，其中 attrs 带本次响应提供的相关元信息 |

**后续用途**：生成文本和 token/logprob 继续交给 [sample.append_response_tokens，240–255](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L240-L255)，最后返回 sample。Trace 中的元信息供时间线详情查看。记录元信息与填充训练样本是两个不同动作。

具体 token 数、请求编号及时间戳依赖真实响应；没有响应的字段不会凭空产生。下面保留一份明确标注的教学 meta，仅用于核对字段映射。

本节以固定源码 18868a79 的外部业务调用为依据；结果是正常路径的静态推导，未取得本轮真实 Agent/模型运行日志。[调用证据](../../../../../references/real-usage-evidence.json) · [本轮补充](../../../../../../step-014-agent-run-trace/04-flow.md#step014-real-business-usage)。

## 本场景的输入与输出

先隔离观察属性整理，再接回上面的真实组合。meta 的值为教学构造，没有执行模型请求。

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

### 返回后谁接住

1. 本函数返回上述 attrs，此刻 sample 的事件并未因本函数而变化。
2. [span.update](../../../../classes/slime/observability/trace_utils.py/TraceSpanContext.md#update-usage)接住它：普通属性进入 span.end_attrs。
3. 离开 with 后，trace_span 将普通属性放进该阶段的 span_end；若带 _trace_children，update 在调用时另外展开子事件。

因此单独调用这个 helper 既不会开始阶段，也不会保存一份 Trace 文件。


## 我的直接表述（原话）

尚无针对本函数用法的直接表述。用户本轮明确的是“scope 为总，short-term memory 具体描述”的记录分工，不能把该要求写成本函数已掌握。

## 尚不清楚

- 本轮保留普通元信息组合；PD 时延字段如何换算成子阶段仍按需要深入。
- 用户尚未独立表述本函数与 update 的边界。

<details>
<summary>来源、验证与完整例子</summary>

- [官方指南](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/trace.md)；[官方角色核对](../../../../../references/official-trace-api-review.json)；[本轮记录分工](../../../../../../step-014-agent-run-trace/04-flow.md#step014-scope-summary-short-term-usage)。
- 既有工具示例曾使用原 trace_utils 与从 types.py 提取的原 Sample 类隔离核对；本轮迁移既有说明，未执行真实 Agent 或模型请求。
- 原 scope 的完整正文保留在[迁移前快照](../../../../../references/scope-before-short-term-usage.md)。

</details>
