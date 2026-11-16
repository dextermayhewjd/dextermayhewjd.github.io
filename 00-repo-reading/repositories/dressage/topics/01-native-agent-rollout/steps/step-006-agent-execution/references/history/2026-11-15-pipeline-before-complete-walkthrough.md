# create_app 内的 _chat_completions_pipeline

- 源码：[dressage/proxy/server.py:1939–2586](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L1939)，固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次展开：Step 006 公共 Proxy 补读，2026-11-15。
- 最近认识更新：2026-11-15，用户询问 session 锁是否用于去重、effective_turn_id 的含义与后续阶段；本轮校准，理解仍待反馈。

[chat_completions 接收并解析请求](../../02-short-term-memory/functions/dressage/proxy/server.py/create_app.chat_completions.md#chat-completions-entry) → **当前处理流水线** → 模型生成与单步记录 → 返回 OpenAI 格式响应。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：外部 Dressage Proxy 已收到本地 Proxy 转发的 OpenAI 请求，正文已解析成字典。
2. **具体内容**：识别会话与轮次，准备模型输入，调用生成，记录这一次交互并组织响应。
3. **建议构建的心智模型**：

   > 把一份模型请求变成生成结果和交互记录，再按请求的响应模式交回；本轮先看这份请求属于谁。

4. **调用背景**：由同一 create_app 内的 chat_completions 传入 request/body；是否在外层包装心跳见[响应模式对照](../../02-short-term-memory/functions/dressage/proxy/server.py/create_app.chat_completions.md#response-modes)。本函数内部继续选 stream=True 的正常成功路径。

   ```python
   # 外层需要心跳时安排该协程；不开启心跳时直接 await 同一个函数。
   task = asyncio.create_task(_chat_completions_pipeline(request, body))
   ```

## 本场景的输入与输出

`request` 保留 HTTP 请求头等信息；`body` 是已转换好的 OpenAI JSON 字典，包含 messages、model、tools 和 stream 等字段。session/instance/turn 的标识已由前面的本地 Proxy 带入请求头。

正常成功路径会把生成结果保存为本次会话的一步记录，并返回 OpenAI 格式响应；当前选 stream=True，最终为 StreamingResponse。之后由本地 RolloutLLMProxy 转换成 Anthropic 响应给 CLI。

| 本函数阶段 | 位置与本轮深度 |
| --- | --- |
| **1. 取请求内容、找到会话与 turn** | 1939–1979；已展示，当前校准锁与轮次 |
| **2. 准备本次生成的输入** | 1981 起；下一段先看 messages → 历史路径 → input_ids 的主干 |
| 3. 请求模型生成 | 2198 的 generate_preemptible 委派；后续按 scope 9.2c 进入正常生成调用 |
| 4. 处理结果、记录、组织响应 | 2479 的 _record_step_atomically，2557 起的响应构造；按 scope 9.2d 回来继续 |

<a id="pipeline-input"></a>

### 1. 取请求内容、找到会话与 turn · 当前

正常路径节选：暂略 usage 设置、会话已关闭的检查与异常转换；后续处理仍位于请求锁内。

```python
messages: list[dict] = body.get("messages", [])  # 本次提交的消息历史。
model = body.get("model", "proxy-model")
stream = bool(body.get("stream", False))       # 本轮按请求值 True 阅读。
tools = body.get("tools")

# 从请求头/正文取得归属，而不是在这里判断响应要送到哪个网络地址。
session_id, instance_id, turn_id = _runtime_ids_from_request(request, body)
sandbox_id = _sandbox_id_from_request(request, body)
session, _ = session_manager.get_or_create_session(
    session_id, messages, instance_id=instance_id
)

session_id = session.session_id
async with session.request_lock:  # 串行处理同一 session 的请求，避免并发读写历史。
    instance_id = instance_id or session.instance_id
    effective_turn_id = session_manager.resolve_turn_id(
        session_id=session_id, requested_turn_id=turn_id
    )  # 校验并取得本次采用的 turn；当前显式 turn_id 来自请求头。
    # 后面才继续历史路径、模型输入与生成；此处尚未调用模型。
```

到这里取得可继续使用的 `session` 与 `effective_turn_id`。**request_lock 是并发串行化，不是请求去重**：重复内容可以先后进入，锁本身不会判断内容相同并跳过。当前请求已带 turn_id，resolve_turn_id 会按会话规则校验并采用它；同一 turn 下可有多次模型请求，不是每次 HTTP 请求都新建一轮。

<a id="pipeline-prepare-input"></a>

### 2. 准备本次生成的输入 · 下一段

以下仍在同一个 session.request_lock 内，摘取正常处理主干。历史变化、工具回调和边界检查的具体分支暂略。

```python
previous_step = session.latest_step
normalized_request_messages = mask_builder.normalize_template_messages(messages)
current_tools_hash = _tools_hash(tools, none_equals_empty=none_equals_empty_tools)
route = _select_route(
    session=session,
    normalized_request_messages=normalized_request_messages,
    tools=tools,
    tools_hash=current_tools_hash,
)  # 这里选择的是会话历史路径，不是 Gateway 的网络路由。

# 原码再根据历史和工具变化，计算 lineage_segment_boundary_before。
prompt_payload = _build_prompt_tokens(
    session=session,
    route=route,
    lineage_segment_boundary_before=lineage_segment_boundary_before,
    normalized_request_messages=normalized_request_messages,
    tools=tools,
)
input_ids = prompt_payload["input_ids"]  # 后续实际交给模型的输入 token。
```

这段先回答“本次 messages 怎样结合已有历史，准备成模型输入”。先接清这些调用的输入输出，再决定是否需要下钻某一个；当前不展开全部历史分叉算法。

### 3. 请求模型生成 · 待展开

接到 2198 行的 generation_controller.generate_preemptible，以 input_ids 等资料请求生成，返回 router_response。具体正常调用链按 scope 9.2c 继续，当前尚未展开。

### 4. 处理结果、记录并组织响应 · 待展开

生成返回后处理文本与工具结果，2479 行进入 _record_step_atomically，2557 行之后组织响应。当前继续选 stream=True；记录与响应细节按 scope 9.2d 的回程展开。

## 我的直接表述（原话）

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

## 尚不清楚

- 第 2 段已列主干，messages 怎样结合历史路径成为 input_ids，接下来继续读；尚未据此标为理解全部输入构建。
- 生成调用、单步记录与响应组织仍待沿当前正常路径展开。
- 流式/非流式正常形式的共同点已在入口卡对照；本轮不同时深入另一响应分支或全部异常路径。

<details>
<summary>来源、完整实现与验证边界</summary>

- [完整流水线源码](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L1939)很长，本卡先保留整体阶段与当前输入段，不复制全文代替分段带读。
- _runtime_ids_from_request:571 优先从 X-Session-Id / X-Instance-Id / X-Turn-Id 等请求头取值，再用正文中的字段回退；sandbox ID 同样从头部或正文取得。另核对 SessionManager.resolve_turn_id 的显式/隐式轮次校验，当前只解释显式输入的正常路径，不另建辅助卡。get_or_create_session 的当前实现按身份获取或创建 Session，messages 参数尚未用于引导初始化。
- chat_completions:2589 负责 HTTP 接收与心跳包装；本函数负责请求的实际处理。当前默认 SGLang /generate 路径先取得生成结果，再由这里组织 SSE 响应，不能把心跳视为已生成的模型 token。
- 无模型、网络或实际会话运行；本卡建立不表示整个 648 行函数已读完。[本次记录](../../04-flow.md#chat-pipeline-input-entry)。

</details>
