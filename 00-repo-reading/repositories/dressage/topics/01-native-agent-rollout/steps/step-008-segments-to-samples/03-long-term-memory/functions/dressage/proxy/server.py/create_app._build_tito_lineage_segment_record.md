> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../step-007-proxy-finalization-and-trajectory/02-short-term-memory/functions/dressage/proxy/server.py/create_app._build_tito_lineage_segment_record.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# create_app._build_tito_lineage_segment_record

- 源码：[server.py:1509–1638](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L1509)。定义在 create_app 内。
- 首次单独展开：Step 007，2026-11-08。
- 最近说明更新：2026-11-08；本轮从 token/mask 拼接接续到说明信息、logprob 和 record 返回；辅助函数按职责理解。

[分段函数](_split_session_into_lineage_segments.md) → 返回 [finalize](create_app.finalize_session.md) 的循环 → **每次调用本函数处理一段** → 返回 record 给 records.append。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：finalize 的 TITO 分支已得到 lineage_segments，正在遍历其中一段。输入 segment 包含刚才归好组的 StepRecord 列表。
2. **具体内容**：按段内顺序拼接 concat token、mask 和可选版本信息，汇总对应 logprob、计数与状态，再加入段和轨迹标识，返回一个记录字典。
3. **建议构建的心智模型**：

   > 把已经分好的一段模型交互记录，整理为一份带 token、logprob、mask 和归属信息的轨迹记录。

   前一步决定哪些 step 放在一起；这里才组合它们的数据。不会跨分段边界把全部 session 合成一条。

4. **调用代码**（finalize 的 lineage 循环）：

   ```python
   for segment_index, segment in enumerate(lineage_segments):
       records.append(
           _build_tito_lineage_segment_record(
               session=session,
               trajectory_id=trajectory_id,
               segment=segment,
               segment_index=segment_index,
               segment_count=len(lineage_segments),
               instance_id=effective_instance_id,
               label=label,
           )
       )
   ```

## 本场景的输入与输出

输入为一段 segment、整个会话 session（用于历史改写等上下文信息）、轨迹和任务标识、段序号/段数与可选 label。核心原料在 segment["steps"]，不是重新发起模型请求。

输出为一个 record 字典，包含 tokens、full_logprobs、full_loss_mask、aligned_response_length，以及轨迹/任务/段标识、messages、tools、finish_reason、extra_info 等；可按配置包含版本与专家路由字段。不是 Step 008 的 Slime Sample，也不是最终全部 records。

<a id="join-token-mask"></a>

### 1. 拿出一段，拼接 token 和 mask（1520–1548）

```python
steps = segment["steps"]              # 只取当前这一段的模型记录。
base_step = steps[-1]                  # 本段最后一条，不是第一条。
turn_ids = segment["turn_ids"]
messages = base_step.messages_snapshot # 记录的消息快照取自最后一步。
tools = base_step.tools

tokens: list[int] = []
step_logprobs = [step.concat_response_logprobs for step in steps]
response_mask: list[int] = []
# 原代码还初始化版本、计数和错误标记，见文末。

for step in steps:
    tokens.extend(step.concat_token_ids)             # 顺序接上本条的 token。
    response_mask.extend(step.concat_response_mask)  # 对应的 mask 同顺序接上。
    # 原代码还拼接可选版本、累加计数、合并无效标记。
```

以上为连续流程的教学裁剪，不可据此认为原函数只有这些字段。extend 是把列表中的元素接到末尾；输入 step 的数组没有在这里被改写。

复用 StepRecord 类卡的静态示例：两条 step 在同一分段，正常复用前缀，不含分支和 tokenizer 特殊边界。

```python
# 输入两份已经准备好的拼接材料。
# step1: concat_token_ids = [10, 11, 20]
#        concat_response_mask = [0, 0, 1]
# step2: concat_token_ids = [30, 40]
#        concat_response_mask = [0, 1]

# 经过上面的 extend 循环：
tokens = [10, 11, 20, 30, 40]
response_mask = [0, 0, 1, 0, 1]
```

第二次请求的完整输入可能已有 [10, 11, 20, 30]，但 concat 材料只贡献 [30, 40]，因此不会在此重复放入历史。前缀复用与边界判断已在前面完成，这个循环不负责重新去重。

0 表示上下文位置，1 表示模型输出位置；先记住 mask 与 tokens 对应即可。最终训练消费的处理留在 Step 008。

<a id="assemble-record"></a>

### 2. 保留这段的来源与处理信息（1550–1591）

接着构造 extra_info，主要保留这段包含哪些 step/turn、属于哪条 lineage、切段原因及计数。版本选项、无效标记、请求耗时和 hook 元数据仍保留在完整源码中，先知道它们补充来源和状态即可，不逐个下钻。

### 3. 把 logprob 接到同一条 token 序列上（1593–1610）

```python
# step_logprobs 是前面收集的每个 step.concat_response_logprobs。
response_logprobs = build_concatenated_logprobs(
    step_logprobs,
    [len(step.concat_token_ids) for step in steps],
    token_count=len(tokens),
)
# 随后检查 tokens 与 response_mask 的长度；启用版本记录时也检查版本长度。
```

当前以内存列表路径理解：辅助函数顺序拼接各份 logprob，并检查总长度与 tokens 一致；不重新调用模型计算概率。TransferQueue 引用路径返回描述数据排列的 layout，本轮不展开，不把所有配置都描述为直接返回列表。

延续同一静态教学例子：

```python
# 两个 step 已保存的 concat logprob：
step_logprobs = [[0.0, 0.0, -0.2], [0.0, -0.3]]
# 拼接后的三份数据按位置对应：
tokens =            [10,  11,   20,  30,   40]
response_mask =     [0,    0,    1,   0,    1]
response_logprobs = [0.0, 0.0, -0.2, 0.0, -0.3]
```

上下文位置的 0.0 是准备 concat 材料时放入的占位，不意味着对应 token 的真实概率为 1。`response_mask` 标出模型输出位置，不能只根据 logprob 数值判断哪些位置参与后续处理。

### 4. 将数据与归属信息组成 record，返回调用方（1612–1638）

下面保留完整 record 字典，只添加中文注释：

```python
record = {
    "uid": str(uuid.uuid4()),
    "trajectory_id": trajectory_id,       # 哪条任务轨迹。
    "turn_id": turn_ids[-1],              # 顶层取本段最后一个 turn；完整列表在 extra_info。
    "instance_id": instance_id,
    "segment_index": segment_index,       # 当前第几段。
    "segment_count": segment_count,
    "messages": messages,                 # 前面取自本段最后一个 step 的快照。
    "tools": tools,
    "tokens": tokens,                     # 拼好的 token 序列。
    "full_logprobs": response_logprobs,    # 对应的 logprob 数据。
    "full_loss_mask": response_mask,      # 对应的输出位置标记。
    "aligned_response_length": sum(response_mask),
    "label": label,
    "finish_reason": base_step.finish_reason,
    "extra_info": extra_info,             # 来源、分段原因、计数和状态等。
}
# 原函数后面还按配置加入版本/专家路由字段。
# 最后：return record
```

`aligned_response_length` 是 mask 中输出位置的数量，不是整条 tokens 的长度；本例为 2。这里返回的是一段的轨迹字典，还不是 Slime Sample。

返回后，finalize 的 `records.append(...)` 收下这份字典，继续处理下一段。等所需记录都构造好，finalize 才调用 trajectory_store.write_many(records)；当前构建函数不负责存储。

## 我的直接表述（原话）

上一处用户已概括同一 lineage 内仍可有边界，记录在分段函数卡。本轮接续请求：

> 好的那么极细吧
> 看一下下一个部分吧

结合当前阅读位置，沿主线进入本构建器；尚无对具体拼接行为的独立复述。

本轮接续请求：

> 好的 那么看一下这里的这个build tito lineage segment record吧

本轮补齐函数正常路径的后半段，不据此将字段含义记为个人已掌握。

后续用户反馈：

> 好的 我大概明白了 生成了函数卡片吗?
> 生成了就继续看下一个吧?

记录为大致理解本构建器，继续返回 finalize；不推断已掌握所有可选字段。

## 尚不清楚

- logprob 的内存列表组合已在当前场景解释，TransferQueue layout 路径和数组无效状态如何影响后续消费未展开。
- 可选版本与专家路由信息，当前只定位。
- 不同分支/失败回退如何准备 concat 材料，暂不回查完整请求管线。

<details>
<summary>完整函数与验证来源</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。静态核对；示例是字段拼接示意，没有运行模型、tokenizer 或真实轨迹。

```python
def _build_tito_lineage_segment_record(
    *,
    session: Session,
    trajectory_id: str,
    segment: dict[str, Any],
    segment_index: int,
    segment_count: int,
    instance_id: str,
    label: Any | None = None,
) -> dict[str, Any]:
    steps = segment["steps"]
    base_step = steps[-1]
    turn_ids = segment["turn_ids"]
    messages = base_step.messages_snapshot
    tools = base_step.tools

    tokens: list[int] = []
    step_logprobs = [step.concat_response_logprobs for step in steps]
    response_mask: list[int] = []
    full_versions: list[str] = []
    context_token_count = 0
    output_token_count = 0
    concat_logprobs_invalid = False
    concat_incremental_tokenization_failed = False

    for step in steps:
        tokens.extend(step.concat_token_ids)
        response_mask.extend(step.concat_response_mask)
        if record_token_versions:
            full_versions.extend(step.concat_versions)
        context_token_count += step.concat_context_token_count
        output_token_count += step.concat_output_token_count
        concat_logprobs_invalid = (
            concat_logprobs_invalid or step.concat_logprobs_invalid
        )
        concat_incremental_tokenization_failed = (
            concat_incremental_tokenization_failed
            or step.concat_incremental_tokenization_failed
        )

    extra_info = {
        "alignment_method": "tito",
        "token_build_mode": "tito",
        "segment_view": "lineage",
        "context_token_count": context_token_count,
        "context_delta_token_count": context_token_count,
        "output_token_count": output_token_count,
        "num_steps": len(steps),
        "num_turns": len(turn_ids),
        "turn_ids": turn_ids,
        "lineage_id": segment.get("lineage_id"),
        "lineage_index": segment.get("lineage_index"),
        "branch_from_step_id": segment.get("branch_from_step_id"),
        "step_ids": [step.step_id for step in steps],
        "timestamp": str(time.time()),
        "history_rewritten": session.history_rewritten,
        "segment_reason": segment["segment_reason"],
        "segment_reasons": segment["segment_reasons"],
        "trajectory_num_segments": segment_count,
        "request_metrics": [
            {
                "step_id": step.step_id,
                "request_e2e_latency_seconds": (
                    step.request_e2e_latency_seconds
                ),
                "request_queue_seconds": step.request_queue_seconds,
                "rebalancing_moved": step.rebalancing_moved,
            }
            for step in steps
        ],
    }
    if concat_logprobs_invalid:
        extra_info["tito_logprobs_invalid"] = True
    if concat_incremental_tokenization_failed:
        extra_info["tito_incremental_tokenization_failed"] = True
    if mask_nonlast_version_tokens:
        extra_info["mask_nonlast_version_tokens"] = True
    hook_metadata: dict[str, Any] = {}
    for step in steps:
        for key, value in step.tool_call_hook_metadata.items():
            hook_metadata.setdefault(key, []).append(value)
    if hook_metadata:
        extra_info["tool_call_hooks"] = hook_metadata

    response_logprobs = build_concatenated_logprobs(
        step_logprobs,
        [len(step.concat_token_ids) for step in steps],
        token_count=len(tokens),
    )
    if len(tokens) != len(response_mask):
        raise RuntimeError(
            "tito segment arrays are not aligned: "
            f"tokens={len(tokens)}, "
            f"full_loss_mask={len(response_mask)}"
        )
    if record_token_versions and len(full_versions) != len(tokens):
        raise RuntimeError(
            "tito segment arrays are not aligned: "
            f"tokens={len(tokens)}, "
            f"full_loss_mask={len(response_mask)}, "
            f"full_versions={len(full_versions)}"
        )

    record = {
        "uid": str(uuid.uuid4()),
        "trajectory_id": trajectory_id,
        "turn_id": turn_ids[-1],
        "instance_id": instance_id,
        "segment_index": segment_index,
        "segment_count": segment_count,
        "messages": messages,
        "tools": tools,
        "tokens": tokens,
        "full_logprobs": response_logprobs,
        "full_loss_mask": response_mask,
        "aligned_response_length": sum(response_mask),
        "label": label,
        "finish_reason": base_step.finish_reason,
        "extra_info": extra_info,
    }
    if record_token_versions:
        record["full_versions"] = full_versions

    routed_experts_field = _build_routed_experts_field(
        steps,
        token_count=len(tokens),
    )
    if routed_experts_field is not None:
        record["routed_experts_chunks"] = routed_experts_field

    return record
```

调用依据：server.py:2803 的 lineage_segments 遍历；材料来源见 StepRecord 类卡。logprob 辅助函数静态核对 dressage/transport/layouts.py:91–119，本轮不单独建卡。

[本轮形成过程](../../../../../../step-007-proxy-finalization-and-trajectory/04-flow.md#tito-segment-build)。

</details>
