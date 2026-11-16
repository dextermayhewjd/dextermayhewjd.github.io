# RolloutLLMProxy._handle_proxy

- 源码：[rollout_llm_proxy.py:421–654](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/proxy/rollout_llm_proxy.py#L421)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次展开：Step 006 公共 Proxy 补读，2026-11-14；原首轮记录保留。
- 最近认识更新：2026-11-14，用户已明确概括 Anthropic JSON 字段转换为 OpenAI 格式、整理 header，再转发给 Dressage Proxy；具体字段映射与下游内部仍待按需展开。

[_proxy HTTP 接收入口](RolloutLLMProxy._build_app._proxy.md#proxy-http-entry) → **当前 _handle_proxy** → 对应协议的转发/响应方法 → 返回 _proxy，由 Web 框架响应 CLI。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Claude CLI 已向本地 Proxy 发出模型请求；当前沿有效的 Anthropic Messages 请求阅读。
2. **具体内容**：将 Claude 的 Anthropic 请求转换成 OpenAI Chat Completions 请求，交给配置的上游 Dressage Proxy，并按 Anthropic 协议组织返回。
3. **建议构建的心智模型**：

   > 当前函数位于 Claude CLI 与 Dressage Proxy 之间，负责这一段的协议适配。

   <a id="handle-proxy-map"></a>

   请求方向（当前阅读的 Dressage 链路）：

   ```text
   Claude CLI
     ↓ Anthropic Messages 请求
   RolloutLLMProxy._handle_proxy（当前）
     ↓ OpenAI Chat Completions 请求
   Dressage Proxy（直接上游）
     ↓ input_ids + sampling_params，调用 /generate
   SGLang（模型后端）
   ```

   这里的 messages 转换主要调整字段与协议格式，并管理 turn/session 归属；模型推理、token 化和完整上下文管理不都在这个函数里。**当前转成 OpenAI 请求；下游 Dressage Proxy 再准备 SGLang 的 token 请求。**

   响应沿反方向交回：Dressage Proxy 整理 OpenAI 样式响应，本 Proxy 再转成 Anthropic 响应给 Claude CLI。协议名称描述格式；实际目标服务由配置的 URL 决定。

4. **调用代码**（_build_app 内的 _proxy:407–408）：

   ```python
   async def _proxy(request: Request, path: str) -> Response:
       return await self._handle_proxy(request, path)
   ```

## 本场景的输入与输出

输入为一次 `POST /v1/messages` 的 request 与 path，正文是有效 JSON 对象。当前 Proxy 已绑定 session/instance，Adapter 已打开本轮 turn；上游地址也已在初始化时配置。返回 Response 或 StreamingResponse，经 HTTP 回到 CLI；不直接返回 AdapterResponse 或训练 Sample。

下面按同一 Anthropic 场景分三段，保留实际变量和调用。其他协议、日志、策略细节与失败处理见折叠源码；两种响应模式按请求体的 stream 字段分支，不能从 CLI 的 stdout 格式 stream-json 推断它。

<a id="handle-proxy-mainline"></a>
<a id="handle-proxy-protocol"></a>

### 1. 识别 Claude 请求，选择上游并转换格式

选定 Anthropic 分支的节选，初始化和 JSON 失败处理暂略：

```python
is_chat = self._is_chat_completion(request.method, path)
is_anthropic = self._is_anthropic_messages(request.method, path)  # 本例 POST /v1/messages 命中。
is_responses = self._is_openai_responses(request.method, path)
is_model_request = is_chat or is_anthropic or is_responses
upstream_url = (
    self._openai_chat_completions_upstream_url()  # 本链路中是 Dressage Proxy 的 chat/completions 地址。
    if is_anthropic or is_responses
    else self._join_upstream(path, request.url.query)
)

body_bytes = await request.body()
parsed_body = json.loads(body_bytes)
# 当前有效 JSON + Anthropic 分支：
original_anthropic_request = dict(parsed_body)
body_json = self._anthropic_messages_to_openai_chat_completion(
    original_anthropic_request
)  # 转换 JSON 协议字段；本行不执行模型推理。
original_stream = bool(original_anthropic_request.get("stream", False))
is_streaming = original_stream
```

`upstream_url` 的实际值由 upstream_origin/router_api_path 拼出；本场景指向上图的直接上游 Dressage Proxy。

<a id="handle-proxy-identity"></a>

### 2. 接上当前 turn，整理上游正文和请求头

```python
snapshot = await self._enter_chat_request() if is_model_request else None
turn_id = snapshot.turn_id if snapshot else None  # 接上已经打开的交互轮次。
# 原码检查步数上限；正常继续时可按配置调整 model/采样参数，并整理 stream_options。
original_request = original_anthropic_request  # 当前协议分支的原始正文。
if body_json != original_request:
    body_bytes = json.dumps(body_json, ensure_ascii=False).encode("utf-8")

headers = self._build_upstream_headers(
    request.headers,
    is_chat=is_model_request,
    is_anthropic=is_anthropic,
    turn_id=turn_id,
)  # 带上绑定的 session/instance 与本轮 turn 等上游归属信息。
```

原码还保存请求/工具摘要；这里先认请求归属和转发材料。模型交互如何写入上游 Session/StepRecord，后续接到 Dressage Proxy 时再读。

<a id="handle-proxy-forward"></a>

### 3. 选择转发方法，取得适合 Claude 的响应

**接下来按 scope 的 [9.2a–9.2e](../../../../../01-scope.md#model-request-route) 读**：先从下面流式分支进入 [_stream_anthropic_messages_proxy](RolloutLLMProxy._stream_anthropic_messages_proxy.md#send-upstream)，走到 HTTP 发送点，再跨到 Dressage Proxy 的生成/记录路径，最后回来读响应转换。当前选 stream=True，不同时展开普通响应分支。

```python
if is_anthropic and is_streaming:
    return await self._stream_anthropic_messages_proxy(
        upstream_url, body_bytes, headers, snapshot
    )  # 返回流式响应对象，流数据由其生成器继续提供。

if is_anthropic:
    return await self._plain_anthropic_messages_proxy(
        request.method, upstream_url, body_bytes, headers, snapshot
    )  # 普通响应路径。
```

这里第 605 行的 `return await self._stream_anthropic_messages_proxy(...)` 会先执行转发；经其第 1176 行调用 _send_stream_request，在第 1456 行 [client.send 真正发出 HTTP](RolloutLLMProxy._stream_anthropic_messages_proxy.md#http-send-line)。上层 _handle_proxy 此时尚未返回。

返回上层 _proxy 后，由 Web 框架把响应发回原请求的 CLI。一次模型响应结束后，CLI 可能继续调用工具/模型；整次 CLI 结束才接回 [_run_claude_turn 的结果整理](../../adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#return-result)。

| 后续按需进入的真实函数 | 返回当前函数的位置 |
| --- | --- |
| _anthropic_messages_to_openai_chat_completion | 第 1 段 body_json 接住转换后的字典；内部字段转换未展开 |
| _enter_chat_request / _build_upstream_headers | 第 2 段接住 snapshot/headers，继续准备转发材料；内部暂缓 |
| [_stream_anthropic_messages_proxy](RolloutLLMProxy._stream_anthropic_messages_proxy.md#send-upstream) / _plain_anthropic_messages_proxy（未展开） | 第 3 段得到 Response，再原样返回 _proxy；具体发送与响应转换后续按选定分支读 |

本轮仅建立本函数主干；只有实际进入的流式转发函数已建卡，其余辅助函数不预建，也不一次深入全部协议和策略。

<details>
<summary>完整函数：其他协议、策略、日志与失败处理</summary>

```python
async def _handle_proxy(self, request: Request, path: str) -> Response:
    is_chat = self._is_chat_completion(request.method, path)
    is_anthropic = self._is_anthropic_messages(request.method, path)
    is_responses = self._is_openai_responses(request.method, path)
    is_model_request = is_chat or is_anthropic or is_responses
    upstream_url = (
        self._openai_chat_completions_upstream_url()
        if is_anthropic or is_responses
        else self._join_upstream(path, request.url.query)
    )

    body_bytes = await request.body()
    body_json: dict[str, Any] | None = None
    is_streaming = False
    original_stream = False
    original_chat_request: dict[str, Any] | None = None
    original_anthropic_request: dict[str, Any] | None = None
    original_responses_request: dict[str, Any] | None = None
    parsed_body: Any = None

    if body_bytes:
        try:
            parsed_body = json.loads(body_bytes)
        except json.JSONDecodeError:
            pass

    if isinstance(parsed_body, dict):
        if is_chat:
            original_chat_request = dict(parsed_body)
            body_json = dict(parsed_body)
            original_stream = bool(original_chat_request.get("stream", False))
            is_streaming = original_stream
        elif is_anthropic:
            original_anthropic_request = dict(parsed_body)
            body_json = self._anthropic_messages_to_openai_chat_completion(original_anthropic_request)
            original_stream = bool(original_anthropic_request.get("stream", False))
            is_streaming = original_stream
        elif is_responses:
            original_responses_request = dict(parsed_body)
            body_json = self._openai_responses_to_chat_completion(original_responses_request)
            original_stream = bool(original_responses_request.get("stream", False))
            is_streaming = original_stream
        else:
            body_json = parsed_body
    elif is_model_request and parsed_body is not None:
        LOGGER.warning(
            "[PROXY REQUEST] Model request payload is %s, forwarding without proxy mutation",
            type(parsed_body).__name__,
        )

    LOGGER.debug(
        "[PROXY REQUEST] %s /%s -> %s (is_chat=%s, is_anthropic=%s, is_responses=%s, stream=%s)",
        request.method,
        path,
        upstream_url,
        is_chat,
        is_anthropic,
        is_responses,
        original_stream,
    )
    LOGGER.debug("[PROXY REQUEST] Body content: %s", self._preview_bytes(body_bytes, limit=1000))
    LOGGER.debug("[PROXY REQUEST] Body size: %d bytes", len(body_bytes) if body_bytes else 0)
    LOGGER.debug("[PROXY REQUEST] Path: /%s, Upstream: %s", path, upstream_url)

    snapshot = await self._enter_chat_request() if is_model_request else None
    turn_id = snapshot.turn_id if snapshot else None
    if snapshot is not None and snapshot.max_steps_exceeded:
        await self._record_max_steps_error(snapshot)
        return self._max_steps_exceeded_response(
            snapshot,
            response_format="anthropic" if is_anthropic else "openai",
        )

    if is_model_request and body_json is not None:
        tools = body_json.get("tools")
        LOGGER.debug(
            "[PROXY REQUEST] Top-level request keys: %s",
            sorted(body_json.keys()),
        )
        LOGGER.debug(
            "[PROXY REQUEST] model=%s, msg_count=%d, original_stream=%s, has_stream_options=%s, tool_count=%d",
            body_json.get("model"),
            len(body_json.get("messages", [])),
            original_stream,
            "stream_options" in body_json,
            len(tools) if isinstance(tools, list) else 0,
        )

        if is_anthropic:
            original_request = original_anthropic_request
            request_kind = "anthropic_messages"
        elif is_responses:
            original_request = original_responses_request
            request_kind = "openai_responses"
        else:
            original_request = original_chat_request
            request_kind = "openai_chat_completions"
        if snapshot is not None:
            self._write_model_request_tool_summary(
                snapshot=snapshot,
                request_kind=request_kind,
                original_body=original_request,
                converted_body=body_json,
            )

        # Anthropic Messages and OpenAI Responses have already been
        # normalized to an OpenAI chat body at this point.  Apply the
        # training model policy to every supported model protocol, not
        # only requests that arrived at /chat/completions.
        if (
            is_model_request
            and self.model_override is not None
            and "model" in body_json
        ):
            body_json["model"] = self.model_override

        if self.sampling_mode is not None:
            for key, value in (
                ("temperature", self.sampling_temperature),
                ("top_p", self.sampling_top_p),
            ):
                if value is not None and (
                    self.sampling_mode == "force" or body_json.get(key) is None
                ):
                    body_json[key] = value
            if self.sampling_seed_base is not None and (
                self.sampling_mode == "force" or body_json.get("seed") is None
            ):
                body_json["seed"] = (
                    self.sampling_seed_base + self._sampling_request_sequence
                )
            self._sampling_request_sequence += 1

        if (
            body_json.get("temperature") is None
            and self.default_temperature is not None
        ):
            body_json["temperature"] = self.default_temperature

        if body_json.get("stream", False):
            stream_options = body_json.get("stream_options")
            if not isinstance(stream_options, dict):
                stream_options = {}
            else:
                stream_options = dict(stream_options)
            stream_options["include_usage"] = True
            body_json["stream_options"] = stream_options
        elif "stream_options" in body_json:
            removed_stream_options = body_json.pop("stream_options")
            LOGGER.debug(
                "[PROXY REQUEST] Removed stream_options because upstream stream=false: %s",
                json.dumps(removed_stream_options, ensure_ascii=False),
            )

        LOGGER.debug(
            "[PROXY REQUEST] Final upstream stream=%s, has_stream_options=%s",
            body_json.get("stream"),
            "stream_options" in body_json,
        )

        if body_json != original_request:
            body_bytes = json.dumps(body_json, ensure_ascii=False).encode("utf-8")
            LOGGER.debug("[PROXY REQUEST] Final body size: %d bytes", len(body_bytes))
            LOGGER.debug(
                "[PROXY REQUEST] Final body preview: %s",
                self._preview_bytes(body_bytes, limit=500),
            )

    headers = self._build_upstream_headers(
        request.headers,
        is_chat=is_model_request,
        is_anthropic=is_anthropic,
        turn_id=turn_id,
    )
    LOGGER.debug("[PROXY REQUEST] Forwarding with headers: %s", list(headers.keys()))
    if is_model_request:
        LOGGER.debug(
            "[PROXY REQUEST] Sticky header %s=%s",
            self.sticky_header_name,
            headers.get(self.sticky_header_name),
        )

    if is_anthropic and is_streaming:
        LOGGER.debug("[PROXY REQUEST] Using Anthropic streaming proxy")
        return await self._stream_anthropic_messages_proxy(
            upstream_url,
            body_bytes,
            headers,
            snapshot,
        )
    if is_chat and is_streaming:
        LOGGER.debug("[PROXY REQUEST] Using streaming proxy")
        return await self._stream_proxy(
            upstream_url,
            body_bytes,
            headers,
            snapshot,
        )
    if is_responses and is_streaming:
        LOGGER.debug("[PROXY REQUEST] Using OpenAI Responses streaming proxy")
        return await self._stream_openai_responses_proxy(
            upstream_url,
            body_bytes,
            headers,
            snapshot,
            original_responses_request or {},
        )
    if is_anthropic:
        LOGGER.debug("[PROXY REQUEST] Using Anthropic plain proxy")
        return await self._plain_anthropic_messages_proxy(
            request.method,
            upstream_url,
            body_bytes,
            headers,
            snapshot,
        )
    if is_responses:
        LOGGER.debug("[PROXY REQUEST] Using OpenAI Responses plain proxy")
        return await self._plain_openai_responses_proxy(
            request.method,
            upstream_url,
            body_bytes,
            headers,
            snapshot,
            original_responses_request or {},
        )
    LOGGER.debug("[PROXY REQUEST] Using plain proxy")
    return await self._plain_proxy(
        request.method,
        upstream_url,
        body_bytes,
        headers,
        snapshot,
    )
```

</details>

## 我的直接表述（原话）

> 好的也就是这里的这个proxy的服务器
> 然后接收到了这个请求
> 然后就是_handle proxy对吧
> 那么请建立对应的函数卡片吧

用户已接清接收入口到处理函数的委派；本函数内部尚待逐段反馈。

本轮追问：

> 也就是说我可以理解为在这里有很多处理这里的上下文?
> 把这里的messages的格式转化为一个可以用来 理解这里到底是在做什么的方式?
> 有点类似于slime中处理很多请求的方式?
> 然后这里作为一种中转
> 转化为上游可以接收的形式
> 值得是sglang这种可以接受的形式对吗?
> 我其实不是特别理解了?
>
> 这里是单纯的转发给上游发给谁呢?
> 最后需要整理成为anthropic的形式我是的理解的

助手校准：当前适配的是 Anthropic 与 OpenAI Chat Completions 协议；本链路的直接上游是配置的 Dressage Proxy，再由它走 SGLang token 接口。回到 CLI 的响应需要恢复 Anthropic 形式；具体转换字段仍未深入。

用户认可协议方向图，并追问呈现原因（节选）：

> 放在这个short term function当中呢?
> 或者说我觉得需要考虑一下这里的这个内容
> 有没有更加好的呈现方式呢?
> 虽然我举得已经很好了
> 但我为什么会有当前的这种误解呢一开始
> 请找到原因

本轮将请求图移到代码之前的心智模型处，并将入口链接指向它；没有据此标记用户已掌握全部协议转换。

本轮主干复述：

> 好的 我简单理解一下就是这里的内容更多的在与把这里的anthropic的内容从json对象转化字段变成为openai的格式?同时整理一下header
> 然后转发给dressage的proxy?

这一概括与当前路径一致：转换的是 JSON 协议字段结构，整理头部并带上会话/turn 归属，再通过转发方法请求上游 Dressage Proxy；未据此认定已掌握全部字段转换或响应分支。

## 尚不清楚

- Anthropic 到 OpenAI 的字段转换、实际 HTTP 发送和响应转换，后续按当前分支展开。
- snapshot/turn 的具体管理与上游 StepRecord 写入还未完整衔接。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对完整 _handle_proxy:421–654、接收入口 _proxy:407–408，以及 _openai_chat_completions_upstream_url:663–666、_build_upstream_headers:668–726。直接上游来自 Adapter._start_proxy 使用的 router_base_url；SGLangRouterClient.generate:176–216 则发送 input_ids/sampling_params 到 /generate，本轮只核对接口区别。
- 上游头包含绑定的 X-Session-Id、X-Instance-Id，以及有值时的 X-Turn-Id；模型覆盖、采样和 max_steps 会影响行为，裁剪不表示这些逻辑不存在。
- 当前入口来自 Topic 01 的原生 CLI 路径；Harbor 集成复用相同代理代码，后续解释在这里维护一份。
- 未构造真实请求或运行模型，stream 的取值仍由实际请求决定。[本轮记录](../../../../../04-flow.md#handle-proxy-card-entry)。

</details>
