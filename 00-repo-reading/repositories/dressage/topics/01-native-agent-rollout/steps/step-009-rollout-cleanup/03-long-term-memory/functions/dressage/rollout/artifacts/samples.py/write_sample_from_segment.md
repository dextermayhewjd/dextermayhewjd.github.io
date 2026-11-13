> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../step-008-segments-to-samples/02-short-term-memory/functions/dressage/rollout/artifacts/samples.py/write_sample_from_segment.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

# write_sample_from_segment

- 源码：[artifacts/samples.py:291–418](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/artifacts/samples.py#L291)。
- 首次单独展开：Step 008，2026-11-08。
- 最近说明更新：2026-11-08；本轮用户已概括将轨迹适配为训练样本的主线；tokens/mask 的来源及单份填写与外层汇总的区别由助手校准，细节掌握不作推断。

[来自 expand_segments_to_samples](../../multi_segment.py/expand_segments_to_samples.md) → **填写当前副本** → 返回同一个 sample → 外层继续写 parent_traj_id、segment_index 和奖励字段。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：外层已为当前轨迹段 deepcopy 原任务模板，把这份 sample 副本和一个 segment 传进来。
2. **具体内容**：取得并按需截断轨迹数组，确定响应区间，写入 Sample 的训练字段；随后补文本、元数据、可选传输/专家路由资料与状态，返回同一个 sample。
3. **建议构建的心智模型**：

   > 把按整段保存的轨迹数据，转换成 Sample 的训练表示，同时补齐回答文本、来源和状态；原地修改并返回同一个副本。

   不在这里重新生成回答或采集 logprob，也不创建另一份模板副本。

4. **调用代码**：

   ```python
   sample = copy.deepcopy(template_sample)
   sample.rollout_id = rollout_id
   write_sample_from_segment(
       sample,
       args=args,
       segment=segment,
       all_segments=sorted_segments,
       session_id=sid,
       instance_id=iid,
       agent_response=agent_response,
   )
   ```

## 本场景的输入与输出

输入：可修改的 Sample 副本、当前段字典、全部段列表，以及配置 args、会话/任务标识和回答回退文本。all_segments 用于段数等元数据，不表示把所有段的 token 合到这个 sample。

输出：修改并返回传入的同一个 sample。外层没有接它的返回值，因为副本已经原地写好；最后由外层收集 Sample 列表。

<a id="mainline"></a>

### 先认清它负责的交接

```python
# 上一层负责复制模板、遍历每段。
sample = copy.deepcopy(template_sample)
write_sample_from_segment(sample, ...)  # 当前函数负责填写这份副本。
# 返回上一层后才补 parent_traj_id、segment_index、奖励并收集列表。
```

从工程实现看，这个函数是 **轨迹段格式到 Sample 格式的适配边界**。它不止改字段名字，还改变数组的表示方式。读完应能回答：哪些 token 被保留、响应区间从哪里开始、哪些位置算 loss、文本/来源/状态从哪里来。

### 整个函数的四段主干与阅读深度

| 顺序 | 源码位置 | 输入 → 本段产物 | 本轮怎样读 |
| --- | --- | --- | --- |
| 1. 准备一致的整段数组 | 301–323 | segment → tokens、mask、logprob、可选版本；应用长度和版本策略 | 理解校验和策略的作用；不逐行追完各辅助函数 |
| 2. 写入训练表示 | 325–350 | 整段数组 → 完整 tokens、响应区间长度、后缀 mask/logprob | 当前最核心，必须用同一例子对齐位置与长度 |
| 3. 写入可读文本与来源 | 352–382 | messages、身份与分段信息 → response、metadata | 必须接清文本和数组是两路数据，以及本段属于谁 |
| 4. 补可选数据，设置状态并返回 | 383–418 | 可选传输/专家数据、finish_reason → 附加字段、status、同一个 sample | 可选部分先按触发条件理解；状态依据和返回对象必须明确 |

不是每个 if 都要展开，但它如果改变训练数据的含义，就必须知道何时触发、改变了什么。下面先把正常路径连起来，再回看策略边界。

### 一份能接回源码的正常路径骨架

教学裁剪：选择无长度裁剪、无版本屏蔽、logprob 为内存列表、不使用专家路由回放的场景。配置不明时不能据此断言真实运行走这条路。省略的检查、元数据清理与可选分支均在下文定位，并在文末保留完整源码。

```python
# 1. 取得并检查整段数据；当前场景无需长度裁剪和版本屏蔽。
tokens, full_loss_mask, full_logprobs, full_versions = _segment_arrays(segment)
train_full_loss_mask = full_loss_mask

# 2. 找到响应区间，写入 Sample 的训练字段。
response_start = next(
    (idx for idx, value in enumerate(full_loss_mask) if value == 1),
    len(tokens),
)
response_length = len(tokens) - response_start
sample.tokens = tokens
sample.response_length = response_length
sample.loss_mask = train_full_loss_mask[response_start:]
sample.rollout_log_probs = full_logprobs[response_start:]  # 此处仅示意内存列表分支。
# 原代码随后校验后缀数组长度，避免位置错配。

# 3. 另行取得回答文本，并写入来源资料。
messages = segment.get("messages") or []
sample.response = _last_assistant_content(messages, fallback=agent_response)
sample.metadata["session_id"] = session_id
sample.metadata["instance_id"] = instance_id
sample.metadata["messages"] = messages
sample.metadata["proxy_extra_info"] = segment.get("extra_info") or {}
# 原代码在这里清理模板遗留的版本/partial 状态，再按本段信息重建。
sample.metadata["segment_count"] = len(all_segments)
sample.metadata["selected_segment_index"] = segment.get("segment_index", 0)
sample.metadata["all_segment_uids"] = [
    item.get("uid") for item in all_segments if item.get("uid") is not None
]
# 原代码在这里登记本地裁剪、传输引用与专家路由等可选资料。

# 4. 根据段的结束原因设置状态，返回同一个对象。
finish_reason = str(segment.get("finish_reason") or "stop")
set_status(sample, "TRUNCATED" if finish_reason == "length" else "COMPLETED")
return sample
```

<a id="write-training-arrays"></a>

### 第 2 段为什么是核心：整段数组变成响应后缀表示

下面是贯穿本卡的人工例子。无长度裁剪、无版本、未开启专家回放；数字只是 token ID 示意，文本例子不声称与这些人工 ID 对应真实 tokenizer 编码。

```python
# segment 中已有的整段数据：20、40 为模型输出，30 为后续上下文。
tokens =         [10,  11,   20,  30,   40]
full_loss_mask = [ 0,   0,    1,   0,    1]
full_logprobs =  [0.0, 0.0, -0.2, 0.0, -0.3]

# 第一个 1 在索引 2，因此响应区间是 [20, 30, 40]。
sample.tokens = [10, 11, 20, 30, 40]
sample.response_length = 3
sample.loss_mask = [1, 0, 1]
sample.rollout_log_probs = [-0.2, 0.0, -0.3]
```

1. tokens 保留整段，包括最初的输入上下文。不是只保留回答 token。
2. response_length 是从第一个输出位置到末尾的区间长度；其中可以夹着工具结果等上下文。
3. loss_mask 和内存形式的 rollout_log_probs 对齐这个后缀，因此两者长度都应等于 response_length。
4. mask 中 1 的数量才表示选中的输出位置数量。本例是 2，和 response_length=3 不同。
5. response_start 用原 full_loss_mask 定位；版本屏蔽可以改变 train_full_loss_mask，但不重新挪动响应起点。

<details>
<summary>为什么不能直接认为字段同名替换即可</summary>

segment.full_loss_mask/full_logprobs 是整段位置，sample.loss_mask/rollout_log_probs 是响应后缀位置。直接把整段 mask 或 logprob 原样交给 Sample，会与 response_length 的约定错位。

另外，前一步轨迹 record.aligned_response_length 是对原 mask 求和，当前函数没有把它直接作为 Sample.response_length。两者含义不同。

</details>

<a id="text-and-metadata"></a>

### 第 3 段要接清两件事：文本来源与任务归属


#### messages 会不会很长？前面的五个 ID 只是小示例

会。messages 可以包含多次模型交互的历史，工具输出也可能很长；前面的 [10,11,20,30,40] 只是演示切片的五个手工 token ID，不代表真实任务只有五个 token，更不是五条消息的编号。

当前 TITO 构建器取该段最后一个 StepRecord 的 messages_snapshot 作为 record["messages"]。记录时的 full_messages 是这次模型请求的 messages 加上新生成的 assistant 消息（proxy/server.py:2383）；因此在正常续接场景，它能包含此前历史。若发生上下文压缩或改写，则是当前可见历史，不能保证包含这次任务从头到尾所有原始消息。

例如一次 Agent 执行中有两次模型调用：第一次请求读取文件，工具返回文件内容，第二次模型据此回答。下面是消息形状的教学构造，省略 system 和工具定义，不对应前面人工 ID 的真实编码：

```python
messages = [
    {"role": "user", "content": "README 中的项目名是什么？"},
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": "call-1",
            "type": "function",
            "function": {"name": "read_file", "arguments": '{"path":"README.md"}'},
        }],
    },
    {"role": "tool", "tool_call_id": "call-1", "content": "# DemoProject"},
    {"role": "assistant", "content": "项目名是 DemoProject。"},
]
```

这里有两次模型生成，所以有两条 StepRecord；不代表有两个 Agent turn。若两条在同一 lineage 且没有分段边界，可以组合成一个 segment，再由本函数写成一个 Sample。消息条数、模型调用次数、轨迹段数与 Sample 数量是不同层级。

对应的 token 序列按区块理解即可（示意省略模板边界 token 的具体分配，不是可执行代码）：

```text
tokens: [input context] [assistant tool call] [tool result + context] [assistant answer]
mask:   [0 ... 0]       [1 ... 1]            [0 ... 0]                [1 ... 1]
```

从第一个 assistant 输出开始的后缀，同时包含工具调用、后续上下文和最终回答；response_length 是这个后缀的总长度，loss_mask 中的 0/1 区分位置。

回到当前函数，两个字段各自保存不同信息：

```python
sample.metadata["messages"] = messages  # 这段的消息快照，可能包含多轮历史。
sample.response = _last_assistant_content(messages, fallback=agent_response)
# 本例 response 为“项目名是 DemoProject。”，并非整段消息或整个训练后缀。
```

本函数即使按 token_cap 裁剪 tokens，也不会同步裁剪 messages 或重新生成 response 文本；不能用文本长度推断训练数组长度。

- **回答文本**：_last_assistant_content 从 messages 末尾向前找 role=assistant 且 content 非 None 的消息，返回 str(content)；找不到才用 agent_response。它不在这里解码 sample.tokens，所以不要假定文本恰好覆盖训练后缀，结构化 content 也可能被字符串化。
- **来源记录**：写入 session_id、instance_id、消息、Proxy 的 extra_info、段总数和当前段编号等。all_segments 只提供整体分段资料，不把其他段的 token 合入此 sample。
- **避免沿用模板旧状态**：先删除一组旧版本与 partial-rollout 相关键，再按当前段重建相关内容。无需背键名，但要知道模板副本的旧信息不能冒充当前段信息。

此处的 selected_segment_index/segment_count 和外层稍后写的 parent_traj_id/segment_index 不是同一处赋值。先看当前函数写什么，返回后再接外层职责。

<a id="status-and-return"></a>

### 第 4 段读到哪里停：状态来源与原地返回

先知道可选传输/专家回放字段的用途，详细表示按下表触发条件回查。最后沿 finish_reason → set_status → return sample 接清返回。

本函数状态只按 finish_reason 判断：等于 "length" 请求设置 TRUNCATED，否则请求设置 COMPLETED。**前面因 token_cap 裁剪数据，只会在这里写 metadata["truncated"]=True，不会自动使这个状态判断变成 TRUNCATED。** 这是源码中的两个独立维度，不额外推断它们等价。

返回的就是传入的 sample 副本。外层没有接 return 值也能继续使用已修改的对象，然后补轨迹归属、处理奖励并 out.append(sample)。本函数不计算奖励。

### 可选分支：现在要知道影响，何时再深入

| 分支与位置 | 影响 | 当前阅读边界 |
| --- | --- | --- |
| _segment_arrays:227；调用在 301 | 取出/规范化数据，要求 tokens 非空且数组长度对应 | 知道合同；暂不背错误分支 |
| token_cap:302–319 | 超过 max_tokens_per_gpu × 上下文并行大小时，截取前缀；内存数组同步裁剪 | 必须知道会影响数据；当前例子不触发，实际启用时复核裁剪后位置 |
| 版本屏蔽:321–323；来源重建:358–375 | 有版本且开启相应策略时，只保留最后输出版本的训练位置等 | 必须区分 full_loss_mask 与 train_full_loss_mask；辅助算法按需回查 |
| TransferQueue:334–337、383–404 | logprob 若是 layout，Sample 上暂写 None，布局放入 metadata 供后续取得 | 不是 logprob 丢失，也不是普通列表切片路径；当前不展开传输 |
| 专家路由:386–414 | 提供 MoE 路由回放数据；启用回放但缺少资料会报错 | 使用该功能才进一步展开 |

### 本函数读完的判据与返回位置

能说明“完整 tokens、响应区间、训练 mask/logprob 的对应”“文本与元数据来源”“两种截断含义和原地返回”，就已抓住正常路径主干；不要求逐个下钻所有 helper。

当前仍在这张卡内，先用数组例子对齐第 2 段，再顺序读第 3、4 段。最后返回 [expand_segments_to_samples](../../multi_segment.py/expand_segments_to_samples.md) 的 parent_traj_id/segment_index/reward 语句，而不是跳过外层直接回到 generate。

## 我的直接表述（原话）

> 好的 那么看一下这里的这二个write sample from segment吧

此前用户已表达从 segment 填入模板的理解；外层实际先复制模板，本函数改的是副本。当前尚无对 response_start 和切片含义的独立复述。

本轮反馈与请求：

> 这里的write sample from segment 还是蛮复杂的 你确定我只需要看这些就可以了吗?

> 请按照资深工程师的角度 来拆解和阅读这个函数吧
> 并且找到 我需要了解的主干

按此请求补齐整个函数的合同、主干和可选分支边界，不把助手对整体的梳理记为用户已经读懂全部实现。

本轮关于多轮记录的追问：

> 那么这里的message又特别长的吗?
> 我比较想要知道
> 因为这里只有一个10 11 20 30 40的部分 我在想有没有多轮轨迹交互的

助手补充正常两次模型调用、一次工具返回的消息形状，区分消息历史、StepRecord、segment、Sample 和最终 response；示例为构造，不写成用户已确认理解。

本轮对整体职责的概括：

> 好的 我差不多理解了
> 我觉得这里就是按照固定的形式
> 吧这里的内容切换成适合的samples的形式 我是这么理解的
> 转换成成tokens还有mask
> 最后汇集成为samples 可以用于训练

助手核对：将轨迹数据适配成训练用 Sample 的主线理解正确。tokens、mask、logprob 已存在于输入 segment；本函数整理、按需裁剪并映射这些数据到一份 Sample，不是首次把文本 tokenize。外层 expand_segments_to_samples 逐段调用，再把各份 Sample 汇集成列表。适配完成后交给后续流程消费，本函数本身不执行训练。

## 尚不清楚

- 全函数主干已梳理；数组、文本、来源和状态各段仍按用户后续反馈逐段接清，不预记全部掌握。
- 截断、版本屏蔽和 TransferQueue 等可选路径暂不深入。

<details>
<summary>完整源码与来源</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。本轮核对源文件及辅助函数，源码区间校正为 291–418；未修改 Dressage 源码。

本轮还抽取该函数及本地数组相关 helper，使用 SimpleNamespace 作为样本、模拟传输类型和状态赋值边界，验证无裁剪与 cap=4 两个构造例：无裁剪得到 response_length=3、mask=[1,0,1]；cap=4 得到 response_length=2、mask=[1,0]。两例均返回同一对象；finish_reason="stop" 时请求设置 COMPLETED，cap=4 同时有 metadata["truncated"]=True。这个局部验证不覆盖真实 Slime 状态枚举、TransferQueue、模型或训练。

来源入口：_last_assistant_content:100；_segment_arrays:227；_segment_token_cap:281；本地状态选择:416–418。

```python
def write_sample_from_segment(
    sample: Any,
    *,
    args: Any,
    segment: dict[str, Any],
    all_segments: list[dict[str, Any]],
    session_id: str,
    instance_id: str,
    agent_response: str,
) -> Any:
    tokens, full_loss_mask, full_logprobs, full_versions = _segment_arrays(segment)
    origin_tokens_len = len(tokens)
    token_cap = _segment_token_cap(args)
    truncated = token_cap is not None and origin_tokens_len > token_cap
    if truncated:
        tokens = tokens[:token_cap]
        full_loss_mask = full_loss_mask[:token_cap]
        if isinstance(full_logprobs, list):
            full_logprobs = full_logprobs[:token_cap]
        if full_versions is not None:
            full_versions = full_versions[:token_cap]
        logger.warning(
            "segment truncated for session_id=%s, instance_id=%s, segment_index=%s: %s > %s",
            session_id,
            instance_id,
            segment.get("segment_index", 0),
            origin_tokens_len,
            token_cap,
        )

    train_full_loss_mask = full_loss_mask
    if full_versions is not None and _segment_masks_nonlast_version_tokens(segment):
        train_full_loss_mask = _mask_nonlast_version_tokens(full_loss_mask, full_versions)

    response_start = next(
        (idx for idx, value in enumerate(full_loss_mask) if value == 1),
        len(tokens),
    )
    response_length = len(tokens) - response_start

    sample.tokens = tokens
    sample.response_length = response_length
    sample.loss_mask = train_full_loss_mask[response_start:]
    sample.rollout_log_probs = (
        None
        if isinstance(full_logprobs, TQFieldLayout)
        else full_logprobs[response_start:]
    )
    if len(sample.loss_mask) != response_length:
        raise ValueError(
            f"loss_mask length {len(sample.loss_mask)} != response_length {response_length}"
        )
    if (
        sample.rollout_log_probs is not None
        and len(sample.rollout_log_probs) != response_length
    ):
        raise ValueError(
            "rollout_log_probs length "
            f"{len(sample.rollout_log_probs)} != response_length {response_length}"
        )

    messages = segment.get("messages") or []
    sample.response = _last_assistant_content(messages, fallback=agent_response)
    sample.metadata["session_id"] = session_id
    sample.metadata["instance_id"] = instance_id
    sample.metadata["messages"] = messages
    sample.metadata["proxy_extra_info"] = segment.get("extra_info") or {}
    sample.metadata.pop("dressage_partial_rollout", None)
    sample.metadata.pop("dressage_async_group_id", None)
    sample.metadata.pop("response_versions", None)
    sample.metadata.pop("response_version_spans", None)
    sample.metadata.pop("dressage_start_token_version", None)
    sample.metadata.pop("dressage_end_token_version", None)
    sample.metadata.pop("full_versions", None)
    sample.metadata.pop("version_spans", None)
    if full_versions is not None:
        sample.metadata["full_versions"] = list(full_versions)
        sample.metadata["version_spans"] = _compress_version_spans(list(full_versions))
        version_bounds = _trainable_output_version_bounds(full_loss_mask, full_versions)
        if version_bounds is not None:
            start_token_version, end_token_version = version_bounds
            sample.metadata["dressage_start_token_version"] = start_token_version
            sample.metadata["dressage_end_token_version"] = end_token_version
        if _has_token_level_partial_rollout(full_loss_mask, full_versions):
            sample.metadata["dressage_partial_rollout"] = True
    sample.metadata["segment_count"] = len(all_segments)
    sample.metadata["selected_segment_index"] = segment.get("segment_index", 0)
    sample.metadata["all_segment_uids"] = [
        item.get("uid") for item in all_segments if item.get("uid") is not None
    ]
    if truncated:
        sample.metadata["truncated"] = True
    layouts: dict[str, dict[str, Any]] = {}
    if isinstance(full_logprobs, TQFieldLayout):
        layouts[full_logprobs.logical_field] = full_logprobs.to_dict()
    raw_routed_experts = segment.get("routed_experts_chunks")
    routed_experts_layout = (
        TQFieldLayout.from_dict(raw_routed_experts)
        if is_tq_field_layout_dict(raw_routed_experts)
        else None
    )
    if routed_experts_layout is not None:
        layouts[routed_experts_layout.logical_field] = (
            routed_experts_layout.to_dict()
        )
        routed_experts = None
    else:
        routed_experts = extract_routed_experts(
            segment,
            args,
            expected_token_count=len(tokens),
        )
    if layouts:
        sample.metadata[TQ_SAMPLE_REF_METADATA_KEY] = layouts
    if routed_experts is not None:
        sample.rollout_routed_experts = routed_experts
    elif (
        routed_experts_layout is None
        and getattr(args, "use_rollout_routing_replay", False)
    ):
        raise ValueError(
            "use_rollout_routing_replay is enabled but segment contains no routed_experts. "
            "Pass --use-rollout-routing-replay when starting the Dressage proxy."
        )

    finish_reason = str(segment.get("finish_reason") or "stop")
    set_status(sample, "TRUNCATED" if finish_reason == "length" else "COMPLETED")
    return sample

```

形成过程：[Step 008](../../../../../../../step-008-segments-to-samples/04-flow.md#write-sample-entry)。

</details>
