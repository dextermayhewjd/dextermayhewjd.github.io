# create_app 内的 _chat_completions_pipeline

- 源码：[dressage/proxy/server.py:1939–2586](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L1939)，固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次展开：Step 006 公共 Proxy 补读，2026-11-15。
- 最近认识更新：用户对会话锁、轮次及整体流程仍有疑问；本次按要求一次补齐完整正常路径材料，不据此标为已掌握。

[chat_completions 接收请求](../../02-short-term-memory/functions/dressage/proxy/server.py/create_app.chat_completions.md#chat-completions-entry) → **当前流水线：生成、记录、组织响应** → 返回接收函数 → 本地 RolloutLLMProxy 转成 Anthropic 响应。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：外部 Dressage Proxy 已收到一份 OpenAI 格式请求，需要生成这次回复，并留下可供后续轨迹整理使用的交互记录。
2. **具体内容**：找会话与轮次，依据历史构建输入 token，调用模型，解析输出，写入 StepRecord，最后组织 OpenAI 响应。
3. **建议构建的心智模型**：

   > 一次生成有两个去向：给客户端的正文/工具调用，以及给轨迹系统的原始 token、概率和归属记录。这个函数把它们组织起来。

4. **调用背景**：上层传入同一个 request 和解析后的 body；[响应模式与心跳](../../02-short-term-memory/functions/dressage/proxy/server.py/create_app.chat_completions.md#response-modes)由外层配合处理。

   ```python
   # 流式且外层启用心跳时：
   task = asyncio.create_task(_chat_completions_pipeline(request, body))
   # 不启用心跳时直接 await 同一个函数；本卡只读 pipeline 内部的 stream=True 路径。
   ```

## 本场景的输入与输出

<a id="pipeline-overview"></a>

### 先固定一条完整路径

本卡选择：**stream=True、token_build_mode="tito"、本会话首条有效模型请求、显式 turn_id、正常生成成功**。输入有足够上下文空间，历史渲染与增量分词成功，生成期间没有抢占或版本冲突。这是阅读场景，不是一次真实运行的结果。

输入来自 `request` 的身份头与 `body` 的 messages/model/tools/生成参数。服务端的 tokenizer、SessionManager、生成控制器、解析器等已在 create_app 时准备好，本函数使用它们。

```text
OpenAI 请求：messages / tools / 参数 / 身份
  → 1. 找到 Session，确定 effective_turn_id
  → 2. 选择历史路径，得到 input_ids 和 sampling_params
  → 3. 请求模型，得到 router_response
  → 4. 解析正文、推理内容与工具调用
  → 5. 将原始 token、概率、消息与归属写成一步交互记录
  → 6. 返回 OpenAI SSE 响应，交回本地 Proxy
```

**正常输出有两部分**：会话中的 StepRecord，以及返回给上层的 StreamingResponse。此处还没有执行会话 finalize、拼接整条最终轨迹或生成训练 Sample。

| 阶段 | 主要产物 | 跳转 |
| --- | --- | --- |
| 1. 接住请求与归属 | session、effective_turn_id | [进入](#pipeline-input) |
| 2. 准备模型输入 | route、input_ids、sampling_params | [进入](#pipeline-prepare-input) |
| 3. 请求模型 | router_response | [进入](#pipeline-generate) |
| 4. 整理生成结果 | content、reasoning_content、tool_calls、full_messages | [进入](#pipeline-parse) |
| 5. 记录本次交互 | 原始 token/概率、快照、TITO 拼接材料、StepRecord | [进入](#pipeline-record) |
| 6. 组织并返回响应 | OpenAI 格式的 SSE 响应对象 | [进入](#pipeline-response) |

以下均为固定源码的正常路径摘录，保留真实名称与关键实参，不是可替换原函数的实现。省略的验证和失败分支在文末列出；第 2–5 段仍位于第 1 段取得的 session.request_lock 内，第 6 段在离开锁后组织响应。

<a id="pipeline-input"></a>

### 1. 接住请求，确定会话与轮次（1946–1979）

```python
messages: list[dict] = body.get("messages", [])  # 本次输入的消息历史。
model = body.get("model", "proxy-model")
stream = bool(body.get("stream", False))       # 当前选择 True。
tools = body.get("tools")
stream_options = body.get("stream_options")
if not isinstance(stream_options, dict):
    stream_options = {}
include_usage = stream_options.get("include_usage", True) is not False

session_id, instance_id, turn_id = _runtime_ids_from_request(request, body)
sandbox_id = _sandbox_id_from_request(request, body)
session, _ = session_manager.get_or_create_session(
    session_id, messages, instance_id=instance_id
)
session_id = session.session_id

async with session.request_lock:  # 同会话请求依次处理；这不是重复请求过滤器。
    instance_id = instance_id or session.instance_id
    effective_turn_id = session_manager.resolve_turn_id(
        session_id=session_id, requested_turn_id=turn_id
    )  # 校验并采用请求中的显式轮次，后续记录使用这个值。
    # 下方第 2–5 段继续位于这个锁内。
```

这里得到的是会话对象与归属，不是生成结果。get_or_create_session 当前按 ID 获取或创建会话；传入 messages 并不意味着已经写入 StepRecord。同一 turn 可以包含多次模型请求。

<a id="pipeline-prepare-input"></a>

### 2. 根据消息和历史准备模型输入（1981–2180）

```python
previous_step = session.latest_step
request_rollout_epoch = generation_controller.current_epoch
normalized_request_messages = mask_builder.normalize_template_messages(messages)
current_tools_hash = _tools_hash(tools, none_equals_empty=none_equals_empty_tools)
route = _select_route(
    session=session,
    normalized_request_messages=normalized_request_messages,
    tools=tools,
    tools_hash=current_tools_hash,
)  # 选择上下文历史路径，不是选择网络地址或 Gateway 路由。
```

本卡是首条有效请求，所以 previous_step 为 None；正常选择新历史路径，route.base_step_id 为 None，没有历史重写或工具变化造成的分段边界。原码据比较计算下面调用使用的 lineage_segment_boundary_before，本场景为 False。

```python
prompt_payload = _build_prompt_tokens(
    session=session,
    route=route,
    lineage_segment_boundary_before=lineage_segment_boundary_before,
    normalized_request_messages=normalized_request_messages,
    tools=tools,
)
input_ids = prompt_payload["input_ids"]
tito_incremental_tokenization_failed = bool(
    prompt_payload["tito_incremental_tokenization_failed"]
)
request_logprob_start_len = -1 if token_build_mode == "tito" else 0
prompt_tokens = len(input_ids)
sampling_params = _build_sampling_params(body, max_output_tokens, rollout_temperature)
configured_max_tokens = sampling_params.get("max_new_tokens")
max_tokens = int(configured_max_tokens or 0)

# 配置了动态预算和窗口上限时，限制本次生成量；本路径空间足够。
if dynamic_max_tokens and context_window is not None:
    remaining_context = context_window - prompt_tokens - 1
    sampling_params["max_new_tokens"] = (
        remaining_context
        if configured_max_tokens is None
        else min(int(configured_max_tokens), remaining_context)
    )
    max_tokens = int(sampling_params["max_new_tokens"])

expected_version = request.headers.get("X-Dressage-Expected-Version")
require_registered_context = request.headers.get("X-Dressage-Partial-Rollout") == "1"
```

这一段的主要交付物是 **input_ids + sampling_params**。route 还保留历史归属，prompt_payload 还带 TITO 的 context_delta_ids，供第 5 段记录；无需在这里把所有分词/分叉实现都读完。

<details>
<summary>同段还做了什么：历史边界、工具钩子与输入保护</summary>

- 原码在消息规范化后创建 tool_call_hook_metadata，并派发 after-tool-call hooks；元数据随后写入交互记录。钩子内部不在本卡展开。
- 比较 previous_step、当前消息和 tools，识别续接、重写与历史路径变化，生成 segment_reasons_before、segment_boundary_before、lineage_segment_reasons_before、lineage_segment_boundary_before 和 rewrite_reason。本卡首请求正常路径中原因列表为空、边界为 False、rewrite_reason 为 None。
- _select_route 正常结果可为 create/append/branch；本场景走 create，其余历史路径算法仅定位。渲染失败另有安全回退。
- 输入已占满窗口、生成预算不足、超过会话步数限制或版本/epoch 不满足要求时，函数会提前返回错误或抛出异常。本卡选择检查通过的路径。

</details>

<a id="pipeline-generate"></a>

### 3. 选择推理执行位置，请求一次生成（2182–2311）

先拿推理路由租约，再用其 worker_url 请求生成；这里的 routing_lease 与第 2 段的历史 route 是两种对象。

```python
# 选择本次请求使用的推理执行位置。
routing_lease = await engine_rebalancer.acquire(
    session_id=session_id,
    input_ids=input_ids,
    expected_version=expected_version,
    require_registered_context=require_registered_context,
)

# 将 token、采样参数和身份交给生成控制器。
router_response = await generation_controller.generate_preemptible(
    input_ids=input_ids,
    sampling_params=sampling_params,
    session_id=session_id,
    instance_id=instance_id,
    turn_id=effective_turn_id,
    routing_key=session_id,
    worker_url=routing_lease.worker_url,
    expected_version=expected_version,
    expected_epoch=(
        request_rollout_epoch
        if (not partial_rollout and session.steps)
        else None
    ),
    logprob_start_len=request_logprob_start_len,
    context_window=context_window,
)

# 成功后结算推理租约；不是在这里写入 StepRecord。
await _settle_routing_lease(
    engine_rebalancer.complete(
        routing_lease,
        committed_tokens=list(router_response.all_token_ids),
    )
)
```

router_response 带回文本、生成 token、logprob、版本等资料。实际调用层次是 generate_preemptible → _generate_with_optional_request_id → SGLangRouterClient.generate；本卡只把该生成调用作为一个完整交接，不展开控制器的抢占恢复。

<details>
<summary>生成失败的边界</summary>

生成异常时会尝试 engine_rebalancer.fail 结算租约，再传播错误。版本不匹配、过期、抢占、关闭和网络错误有相应 HTTP 错误转换；成功结算自身失败时记录警告，不因此丢弃已取得的生成结果。以上是正常路径之外的出口，不是还要追加的新生成阶段。

</details>

<a id="pipeline-parse"></a>

### 4. 同时准备对外内容和原始生成资料（2313–2389）

下面选无输出溢出的路径。原始 token/logprob 要保留；面向客户端的正文可以经过解析与清理。

```python
raw_text = router_response.text
response_token_ids = router_response.output_ids
response_logprobs = router_response.output_token_logprobs
response_versions = list(router_response.output_versions)

# 本路径没有 output_overflow；保留原码的结束原因选择。
context_overflow = router_response.meta_info.get("context_overflow")
output_overflow = (
    isinstance(context_overflow, dict) and context_window is not None
)
public_completion_tokens = _completion_usage_tokens(
    response_token_ids=response_token_ids,
    raw_text=raw_text,
)
finish_reason = (
    "length"
    if output_overflow or router_response.finish_reason == "length"
    else "stop"
)

# 把模型原始文本拆成推理内容、正文和工具调用。
reasoning_result = await proxy_reasoning_parser.parse(
    raw_text,
    routing_key=session_id,
)
reasoning_content = reasoning_result.reasoning_content
content, tool_calls = await proxy_tool_call_parser.parse(
    reasoning_result.text,
    tools,
    routing_key=session_id,
)
content = _strip_public_stop_markers(content)
if tool_calls:
    finish_reason = "tool_calls"

full_messages = messages + [
    _assistant_message(
        content,
        tool_calls,
        reasoning_content=reasoning_content,
    )
]
```

- **对外**：content、reasoning_content、tool_calls 与 finish_reason，用来组织客户端响应。返回 tool_calls 时这里整理调用描述，真正执行工具仍由 Agent 继续完成；原码还会派发已配置的 before-tool-call hooks。
- **对内**：response_token_ids、response_logprobs 和版本资料来自模型返回，不用清理后的正文重新分词来冒充原始生成 token。

<details>
<summary>版本资料如何接到记录</summary>

```python
response_version = (
    response_versions[-1]
    if response_versions
    else router_response.weight_version or "unknown"
)
if len(response_versions) != len(response_token_ids):
    response_versions = [str(response_version)] * len(response_token_ids)
request_version = response_version
if session.rollout_epoch is None:
    session.rollout_epoch = router_response.rollout_epoch
prompt_versions = [_INPUT_TOKEN_VERSION] * len(input_ids)
all_versions = prompt_versions + response_versions
```

中间还会校验当前轨迹能否接纳这些版本、partial rollout 跨度是否超限。本卡选择版本一致的正常路径。

</details>

<a id="pipeline-record"></a>

### 5. 准备 TITO 材料，写下这一次交互（2390–2531）

先区分“给客户端看的消息”与“记录下来供后续处理的数据”。本路径没有输出溢出，因此以下 recorded_* 保留模型正常返回的数据。

```python
recorded_response_token_ids = [] if output_overflow else response_token_ids
recorded_response_logprobs = [] if output_overflow else response_logprobs
recorded_response_versions = [] if output_overflow else response_versions
recorded_output_token_texts = (
    [] if output_overflow else list(router_response.output_token_texts)
)
recorded_all_token_ids = (
    list(input_ids)
    if output_overflow
    else list(router_response.all_token_ids)
)
recorded_all_logprobs = (
    list(router_response.input_token_logprobs_raw)
    if output_overflow
    else list(router_response.all_logprobs)
)
recorded_all_versions = (
    prompt_versions if output_overflow else all_versions
)
recorded_raw_text = "" if output_overflow else raw_text
normalized_full_messages = mask_builder.normalize_template_messages(
    full_messages
)

# 缓存消息渲染结果，供后续请求匹配历史。
snapshot_rendered = mask_builder.render_messages(
    normalized_full_messages,
    tools,
    add_generation_prompt=False,
    template_kwargs=tito_template_kwargs,
)
```

当前选择 TITO：快照 token 由本次输入与实际生成 token 拼接；concat_payload 记录本次的上下文增量和生成贡献，留给后续轨迹拼段。

```python
concat_payload: dict[str, Any] = {}
snapshot_token_ids = list(input_ids) + list(recorded_response_token_ids)
concat_payload = _build_concat_step_payload(
    context_delta_ids=prompt_payload["context_delta_ids"],
    response_token_ids=recorded_response_token_ids,
    response_logprobs=recorded_response_logprobs,
    response_versions=recorded_response_versions,
    context_version=str(request_version),
    concat_incremental_tokenization_failed=(
        tito_incremental_tokenization_failed
    ),
)
```

最后交给记录函数。下面只显示核心字段，完整实参在随后的折叠块中；省略字段并非真实调用不存在。

```python
await _record_step_atomically(
    session,
    session_id=session_id,
    turn_id=effective_turn_id,
    request_messages=messages,
    prompt_token_ids=input_ids,
    response_token_ids=recorded_response_token_ids,
    response_logprobs=recorded_response_logprobs,
    messages=full_messages,
    **concat_payload,
    step_id=session.next_step_id(),
    lineage_id=route.lineage_id,
    # 其余快照、版本、边界与诊断实参见下方完整调用。
)
```

这一步把本次输入、输出和归属交给会话记录层；**不是 finalize 整个会话，也不是在这里产出训练 Sample**。之后 Step 007 的收尾链才会整理已积累的多条记录。

<details>
<summary>其余记录资料与完整写入调用</summary>

没有要求 MoE 路由回放时不必深入这些张量处理；原码仍会规范化已有 routed-experts 数据并写入相应记录字段。

```python
previous_prefix_count = (
    0
    if route.type in {"create", "branch"}
    or lineage_segment_boundary_before
    else len(
        _lineage_tito_prefix_token_ids(
            session,
            route.lineage_id,
        )
    )
)
concat_token_count = len(concat_payload["concat_token_ids"])
if previous_prefix_count == 0:
    routed_experts_target_start = 0
    routed_experts_target_count = max(0, concat_token_count - 1)
else:
    routed_experts_target_start = previous_prefix_count - 1
    routed_experts_target_count = concat_token_count
response_routed_experts_chunks = canonicalize_routed_experts(
    router_response.routed_experts_chunks,
    target_start=routed_experts_target_start,
    target_count=routed_experts_target_count,
    expert_id_dtype=routed_experts_dtype,
)
router_response.routed_experts_chunks.clear()
```

```python
await _record_step_atomically(
    session,
    session_id=session_id,
    turn_id=effective_turn_id,
    request_messages=messages,
    normalized_request_messages=normalized_request_messages,
    prompt_token_ids=input_ids,
    prompt_token_logprobs=list(router_response.input_token_logprobs_raw),
    snapshot_token_ids=snapshot_token_ids,
    response_token_ids=recorded_response_token_ids,
    response_logprobs=recorded_response_logprobs,
    response_versions=recorded_response_versions,
    all_token_ids=recorded_all_token_ids,
    all_logprobs=recorded_all_logprobs,
    all_versions=recorded_all_versions,
    prompt_versions=prompt_versions,
    input_token_texts=list(router_response.input_token_texts),
    output_token_texts=recorded_output_token_texts,
    messages=full_messages,
    raw_response_text=recorded_raw_text,
    all_logprobs_invalid=router_response.all_logprobs_invalid,
    **concat_payload,
    response_routed_experts_chunks=response_routed_experts_chunks,
    tools=tools,
    segment_boundary_before=segment_boundary_before,
    rewrite_reason=rewrite_reason,
    segment_reason_before=(
        segment_reasons_before[0] if segment_reasons_before else None
    ),
    segment_reasons_before=segment_reasons_before,
    step_id=session.next_step_id(),
    lineage_id=route.lineage_id,
    lineage_index=session.lineages[route.lineage_id].index,
    route_type=route.type,
    route_base_step_id=route.base_step_id,
    normalized_messages_snapshot=normalized_full_messages,
    snapshot_rendered=snapshot_rendered,
    snapshot_rendered_len=len(snapshot_rendered),
    snapshot_tools_hash=current_tools_hash,
    lineage_segment_boundary_before=lineage_segment_boundary_before,
    lineage_segment_reasons_before=lineage_segment_reasons_before,
    finish_reason=finish_reason,
    request_version=str(request_version),
    response_version=str(response_version),
    tool_call_hook_metadata=tool_call_hook_metadata,
    request_e2e_latency_seconds=_optional_response_duration(
        router_response.meta_info.get("e2e_latency")
    ),
    request_queue_seconds=_optional_response_duration(
        router_response.meta_info.get("queue_time")
    ),
    rebalancing_moved=routing_lease.decision.moved,
)
```

</details>

<a id="pipeline-response"></a>

### 6. 离开会话锁，组织 OpenAI SSE 响应（2557–2573）

本卡固定 stream=True，所以走下面这条返回路径。此时生成和记录已完成；_pseudo_stream_chunks 把已有结果组织成事件流，不是从 SGLang 实时逐 token 接收。

```python
response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
return StreamingResponse(
    _pseudo_stream_chunks(
        response_id,
        model,
        content,
        reasoning_content,
        tool_calls,
        finish_reason,
        prompt_tokens,
        public_completion_tokens,
        include_usage,
    ),
    media_type="text/event-stream",
    headers=_SSE_RESPONSE_HEADERS,
)
```

StreamingResponse 返回 chat_completions，由外层直接交付或包在心跳流中继续交付；本地 RolloutLLMProxy 收到 OpenAI 响应后，再转为 Anthropic 响应给 CLI。返回响应对象不等于响应体已全部发送，外层心跳也可能在本函数生成完成前已经发出。

### 其他路径只在这里标边界

| 路径 | 与本卡选择的区别 |
| --- | --- |
| stream=False | 共用生成/记录，最后返回 JSONResponse；[入口卡的模式对照](../../02-short-term-memory/functions/dressage/proxy/server.py/create_app.chat_completions.md#response-modes)保留两种正常形式，本卡不并行展开此分支 |
| token_build_mode="snapshot" | 快照分词与记录方式不同；本卡固定 TITO，原码 2438–2444、2465–2470 可回查 |
| 后续请求、历史分叉、工具变化 | 第 2 段可能复用/分叉历史，并设置分段边界；本卡首请求路径不展开所有算法 |
| 输入溢出、输出溢出或版本/生成失败 | 可提前返回错误；输出溢出分支还会先记录输入相关资料再返回 413，不属于本卡成功路径 |
| 扩展钩子、MoE 路由回放、抢占续跑 | 保留发生位置与记录接口，不把每个实现都变成本轮必读 |

## 我的直接表述（原话）

<details>
<summary>已有问题与本次完整卡片要求</summary>

> 当前是rolloutllmproxy转换之后发送请求
> 那么之后呢?
> dressage接收到了这个请求
> 那么就是chat completions pipeline
> 那么现在需要看的是什么呢?
> chat completions的pipeline?

用户已定位到请求到达外部 Proxy 的阶段；本轮明确先经过 chat_completions 解析，再进入本函数。内部实现尚待逐段反馈。

本轮疑问：

> 为什么目前只有一个1的部分
> 我简单理解就是
> 首先获得请求头etc
> 然后考虑的是锁住这个session避免重复?
> 也就是需要处理实际使用的轮次? 还是什么呢?
> 我不是特别清楚
> 那么在往下我需要读取什么呢?

助手区分 session 并发串行化与去重、已有 turn 的校验与每次请求新建 turn；后续段落保留在同一张卡中，避免误以为函数只到第一段。

本次要求：

> 能否一起性生成完整呢?
> 然后我才需要知道这里到底是在做什么 这件事情

</details>

## 尚不清楚

- 用户对 session 锁、effective_turn_id 与整体处理目的仍需消化；材料完整不代表已经掌握。
- 历史路径与 TITO 增量构造、生成控制器、解析器、记录函数的内部算法尚未逐项深入，先按本卡的数据交接理解。
- 其他模式与失败分支不在本次完整正常路径内；没有真实网络、模型或 token 数值验证。

<details>
<summary>来源、完整源码与校验范围</summary>

- 本卡六段均核对固定提交的 server.py:1939–2586；token_build_mode="tito" 是 create_app 的默认值，本卡仍显式写明选择，避免与 snapshot 分支混用。
- 历史 route 来自 _select_route:1000；网络执行租约来自 engine_rebalancer.acquire，两者用途不同。输入转换为 _build_prompt_tokens:1665，TITO 拼接材料由 _build_concat_step_payload:1734 构造。
- get_or_create_session 按身份获取/创建，当前 messages 形参不参与初始化；resolve_turn_id 校验并维护轮次；session.request_lock 串行化同会话处理，不能当成去重。
- 正文保留业务主干和关键实参，完整源码可从页首固定版本链接回查；未把教学裁剪当成可替换实现，未执行模型或伪造输出。
- [补齐前的卡片](2026-11-15-pipeline-before-complete-walkthrough.md)保留此前文字、原话与未知；[本次形成过程](../../04-flow.md#pipeline-complete-card)。

</details>
