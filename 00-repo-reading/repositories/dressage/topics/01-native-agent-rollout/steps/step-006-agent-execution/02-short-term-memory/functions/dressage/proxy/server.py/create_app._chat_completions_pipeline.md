# create_app 内的 _chat_completions_pipeline

- 源码：[dressage/proxy/server.py:1939–2586](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L1939)，固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次展开：Step 006 公共 Proxy 补读，2026-11-15。
- 最近认识更新：2026-11-15，用户已表述解析结果、保存交互、离开会话锁并返回响应的主线；一次模型请求与完整轮次的区别由助手补充，内部机制仍按需回查。

[chat_completions 接收请求](create_app.chat_completions.md#chat-completions-entry) → **当前流水线：生成、记录、组织响应** → 返回接收函数 → 本地 RolloutLLMProxy 转成 Anthropic 响应。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：外部 Dressage Proxy 已收到一份 OpenAI 格式请求，需要生成这次回复，并留下可供后续轨迹整理使用的交互记录。
2. **具体内容**：找会话与轮次，依据历史构建输入 token，调用模型，解析输出，写入 StepRecord，最后组织 OpenAI 响应。
3. **建议构建的心智模型**：

   > 一次生成有两个去向：给客户端的正文/工具调用，以及给轨迹系统的原始 token、概率和归属记录。这个函数把它们组织起来。

4. **调用背景**：上层传入同一个 request 和解析后的 body；[响应模式与心跳](create_app.chat_completions.md#response-modes)由外层配合处理。

   ```python
   # 流式且外层启用心跳时：
   task = asyncio.create_task(_chat_completions_pipeline(request, body))
   # 不启用心跳时直接 await 同一个函数；本卡只读 pipeline 内部的 stream=True 路径。
   ```

## 本场景的输入与输出

<a id="pipeline-overview"></a>

### 先固定一条完整路径

本卡沿 **stream=True、TITO、会话首条有效请求、显式 turn_id** 的正常成功路径阅读；假定输入空间足够、无抢占或版本冲突。以下是源码阅读场景，未实际运行模型。

**输入**：request 中的身份，以及 body 中的 messages、model、tools 和生成参数；所用服务端组件已由 create_app 准备好。

**正常输出有两部分**：会话中的 StepRecord，以及返回给上层的 StreamingResponse。此处还没有执行会话 finalize、拼接整条最终轨迹或生成训练 Sample。

| 阶段 | 主要产物 | 跳转 |
| --- | --- | --- |
| 1. 接住请求与归属 | session、effective_turn_id | [进入](#pipeline-input) |
| 2. 准备模型输入 | route、input_ids、sampling_params | [进入](#pipeline-prepare-input) |
| 3. 请求模型 | router_response | [进入](#pipeline-generate) |
| 4. 整理生成结果 | content、reasoning_content、tool_calls、full_messages | [进入](#pipeline-parse) |
| 5. 记录本次交互 | 原始 token/概率、快照、TITO 拼接材料、StepRecord | [进入](#pipeline-record) |
| 6. 组织并返回响应 | OpenAI 格式的 SSE 响应对象 | [进入](#pipeline-response) |

以下为**源码裁剪**：保留主要调用和关键实参，省略处用注释标明，不是可直接运行的替代实现。第 2–5 段都在第 1 段的锁内；为便于阅读不重复缩进。[完整参数与辅助处理](../../../../../references/history/2026-11-15-pipeline-complete-before-compaction.md#pipeline-input)可按需回查。

<a id="pipeline-input"></a>

### 1. 确定请求属于哪个会话、哪一轮（1946–1979）

**本段要解决的问题**：这次请求属于谁的历史、哪一轮交互？先确定归属，后面才能使用正确的历史并把结果记到对应轮次；同会话请求也要依次更新这些状态。

```python
messages = body.get("messages", [])
tools = body.get("tools")
# 同处读取 model、stream 和 usage 选项。
session_id, instance_id, turn_id = _runtime_ids_from_request(request, body)
session, _ = session_manager.get_or_create_session(
    session_id, messages, instance_id=instance_id
)
session_id = session.session_id

async with session.request_lock:  # 同会话请求串行处理，不是去重。
    instance_id = instance_id or session.instance_id
    effective_turn_id = session_manager.resolve_turn_id(
        session_id=session_id, requested_turn_id=turn_id
    )  # 校验并采用显式 turn_id；同一 turn 可以有多次模型请求。
    # 第 2–5 段接着在此执行。
```

<a id="pipeline-prepare-input"></a>

### 2. 将消息历史变成模型输入（1981–2180）

**本段要解决的问题**：模型需要 token 和采样参数，收到的却是 messages：怎样结合会话历史，准备这次真正送给模型的输入？

```python
normalized_request_messages = mask_builder.normalize_template_messages(messages)
route = _select_route(
    session=session,
    normalized_request_messages=normalized_request_messages,
    # 省略 tools 及其 hash 实参。
)  # 选择上下文历史路径；首请求创建新路径，不是选择网络地址。

prompt_payload = _build_prompt_tokens(  # 独立函数卡：create_app._build_prompt_tokens.md（scope 9.2b.1）；消息 → token
    session=session,
    route=route,
    normalized_request_messages=normalized_request_messages,
    tools=tools,
    # 省略历史分段边界实参；本场景无分段。
)
input_ids = prompt_payload["input_ids"]
sampling_params = _build_sampling_params(body, max_output_tokens, rollout_temperature)
# 原码随后按剩余上下文空间调整生成预算，并检查版本等条件。
```

交给下一段的是 **input_ids + sampling_params**；prompt_payload 还保留上下文增量，供第 5 段记录。

**当前回查**：[进入 _build_prompt_tokens 函数卡](create_app._build_prompt_tokens.md)，沿首请求分支定位文字转 token 的实际调用。读完返回本段，带着 `input_ids` 继续第 3 段。

<a id="pipeline-generate"></a>

### 3. 把输入交给模型，接回生成结果（2182–2311）

**本段要解决的问题**：输入已经准备好，应交给哪个推理执行位置，怎样拿回生成结果并结算本次租约？

```python
routing_lease = await engine_rebalancer.acquire(
    session_id=session_id, input_ids=input_ids,
    # 省略版本及已登记上下文要求。
)  # 这次选择推理执行位置，与上段的历史 route 不同。

router_response = await generation_controller.generate_preemptible(
    input_ids=input_ids,
    sampling_params=sampling_params,
    session_id=session_id,
    instance_id=instance_id,
    turn_id=effective_turn_id,
    worker_url=routing_lease.worker_url,
    # 省略 routing_key、版本、epoch、logprob 和窗口参数。
)
await _settle_routing_lease(
    engine_rebalancer.complete(
        routing_lease, committed_tokens=list(router_response.all_token_ids)
    )
)  # 生成成功后结算租约。
```

router_response 带回文本、token、logprob 等。[进入 generate_preemptible：正常生成的四段交接](../generation_controller.py/GenerationController.generate_preemptible.md#generation-mainline)，读完回到这里结算租约；控制器经客户端发送 /generate。

<a id="pipeline-parse"></a>

### 4. 从模型结果中解析正文和工具调用（2313–2389）

**本段要解决的问题**：模型返回的是原始生成结果，客户端需要的是正文、推理内容和工具调用：怎样整理回复，同时保留记录所需的原始 token 和概率？

```python
raw_text = router_response.text  # 第 3 段已拿到结果；这里取出生成文本，不再请求生成
response_token_ids = router_response.output_ids  # 生成内容的 token IDs，不是 request/session ID
response_logprobs = router_response.output_token_logprobs  # 生成 token 的对数概率，供后续记录
# 同处整理版本、token 用量与结束原因，原始 token/logprob 留给记录。

reasoning_result = await proxy_reasoning_parser.parse(raw_text, routing_key=session_id)
# 从生成文本中分离推理内容；这里解析的是文本，不是 token IDs 或 logprob。
reasoning_content = reasoning_result.reasoning_content  # 单独保留推理内容
content, tool_calls = await proxy_tool_call_parser.parse(
    reasoning_result.text, tools, routing_key=session_id  # 从剩余文本解析正文与工具调用描述
)
content = _strip_public_stop_markers(content)  # 清理对外正文中的停止标记
if tool_calls:
    finish_reason = "tool_calls"  # 这里只整理调用描述，工具由 Agent 执行。

full_messages = messages + [  # 原对话追加这次 assistant 回复，得到更新后的消息列表
    _assistant_message(content, tool_calls, reasoning_content=reasoning_content)
]
```

现在得到两份材料：**解析后的内容用于回复客户端，原始 token 和概率用于记录**。第 4 段只做整理；第 5 段保存记录，第 6 段才组织并返回响应。切换为厂商 API 时，需要核对其是否已提供结构化正文和工具调用，不能默认继续照搬原始文本解析路径。

<a id="pipeline-record"></a>

### 5. 保存这一次交互（2390–2531）

**本段要解决的问题**：除了回复客户端，还要为后续请求和轨迹整理保留这次生成的数据：怎样把输入、输出及其归属保存成一步交互记录？

```python
# 原码先准备 recorded_*；无输出溢出时保留第 4 段的原始生成资料。
# 同时准备消息快照与版本字段，供下面两个调用使用。
snapshot_token_ids = list(input_ids) + list(recorded_response_token_ids)
concat_payload = _build_concat_step_payload(
    context_delta_ids=prompt_payload["context_delta_ids"],
    response_token_ids=recorded_response_token_ids,
    response_logprobs=recorded_response_logprobs,
    # 省略版本与增量分词状态实参。
)  # TITO：保存本次新增的上下文与生成贡献，供后续拼接轨迹。

await _record_step_atomically(
    session,
    session_id=session_id,
    turn_id=effective_turn_id,
    prompt_token_ids=input_ids,
    response_token_ids=recorded_response_token_ids,
    response_logprobs=recorded_response_logprobs,
    messages=full_messages,
    **concat_payload,
    step_id=session.next_step_id(),
    lineage_id=route.lineage_id,
    # 省略请求消息、快照、版本、边界与诊断实参。
)
```

会话里新增一个 StepRecord；整条轨迹和训练 Sample 留给后续收尾链整理。

<a id="pipeline-response"></a>

### 6. 离开会话锁，返回响应（2557–2573）

**本段要解决的问题**：生成和记录已经完成，怎样把整理好的回复按客户端要求的流式协议交回去？

```python
response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
return StreamingResponse(
    _pseudo_stream_chunks(
        response_id, model, content, reasoning_content, tool_calls,
        finish_reason, prompt_tokens, public_completion_tokens, include_usage,
    ),
    media_type="text/event-stream",
    headers=_SSE_RESPONSE_HEADERS,
)  # 将已经生成的结果组织成 SSE，不是后端实时逐 token 生成。
```

返回 chat_completions，由 HTTP 响应交回本地 RolloutLLMProxy，再转为 Anthropic 响应给 CLI。返回响应对象时，响应体不一定已全部发送。

<details>
<summary>其他分支与辅助处理：本轮先知道边界</summary>

- stream=False 共用生成和记录，最后返回 JSONResponse；[入口卡](create_app.chat_completions.md#response-modes)对照响应模式及外层心跳。
- snapshot 模式使用另一套快照分词方式；后续请求还可能续接或分叉历史。本卡固定首请求、TITO 成功路径。
- 原码还处理工具钩子、版本检查、MoE 资料对齐及失败时的租约结算。输出溢出时可先记录输入资料再返回 413。
- [完整稿](../../../../../references/history/2026-11-15-pipeline-complete-before-compaction.md#pipeline-overview)保留这些处理的位置、详细实参与源码依据；不要求此时逐项下钻。

</details>

## 我的直接表述（原话）

2026-11-17 第 4 段追问：

> 简单来说是在这里拿到对应的response的对吗？
> 是我的理解
> 还有对应的id和log probs？
> 最后在parser回去？

助手校准：response 在第 3 段已返回；第 4 段提取文本、生成 token IDs 和 logprob，parser 处理文本并提取正文/推理/工具调用，实际响应在第 6 段返回。

2026-11-17 当前问题（不表示已掌握转换实现）：

> 主要是哪里从文字被tokenizer 变成token的是需要了解的对吗？


最新表述：

> 后续其实就是从模型结果中解析正文和工具调用
> 然后是保存这一次交互然后是离开会话锁然后返回相应
> 是我的理解

助手校准：本次记录对应一次模型请求；同一 turn 可有多次模型请求，不能据此认为整轮 Agent 任务已结束。

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

本次版式反馈：

> 能否考虑稍微简化一点点呢?
> 作为一个认知学专家和资深程序员
> 你会考虑如何修改这个函数的short term memroy呢?

</details>

## 尚不清楚

- 用户已串起后半段主线；session 锁、effective_turn_id 和历史分支的内部机制仍未逐项验证掌握。
- 历史路径与 TITO 增量构造、生成控制器、解析器、记录函数的内部算法尚未逐项深入，先按本卡的数据交接理解。
- 其他模式与失败分支不在本次完整正常路径内；没有真实网络、模型或 token 数值验证。

<details>
<summary>来源、完整源码与校验范围</summary>

- 本卡六段均核对固定提交的 server.py:1939–2586；token_build_mode="tito" 是 create_app 的默认值，本卡仍显式写明选择，避免与 snapshot 分支混用。
- 历史 route 来自 _select_route:1000；网络执行租约来自 engine_rebalancer.acquire，两者用途不同。输入转换为 _build_prompt_tokens:1665，TITO 拼接材料由 _build_concat_step_payload:1734 构造。
- get_or_create_session 按身份获取/创建，当前 messages 形参不参与初始化；resolve_turn_id 校验并维护轮次；session.request_lock 串行化同会话处理，不能当成去重。
- 正文保留业务主干和关键实参，完整源码可从页首固定版本链接回查；未把教学裁剪当成可替换实现，未执行模型或伪造输出。
- [补齐前的卡片](../../../../../references/history/2026-11-15-pipeline-before-complete-walkthrough.md)保留此前文字、原话与未知；[本次形成过程](../../../../../04-flow.md#pipeline-complete-card)。

</details>
