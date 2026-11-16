# create_app 内的 chat_completions

- 源码：[dressage/proxy/server.py:2588–2676](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L2588)，固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次展开：Step 006 公共 Proxy 补读，2026-11-15。
- 最近认识更新：当前开始读接收入口，尚无本函数的个人机制复述。

[本地 RolloutLLMProxy 的发送点](../../../blackbox_server/proxy/rollout_llm_proxy.py/RolloutLLMProxy._stream_anthropic_messages_proxy.md#http-send-line) == HTTP POST /v1/chat/completions ==> **当前外部 Dressage Proxy 接收入口** → _chat_completions_pipeline。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：本地 Proxy 已发出 OpenAI 格式的请求，外部 Dressage Proxy 现在接到它。
2. **具体内容**：验证访问、解析 JSON，将处理交给生成流水线；流式请求可在等待期间发送心跳，随后交付响应。
3. **建议构建的心智模型**：

   > 接住 HTTP 请求，把真正处理交给流水线；等待期间按需保持响应连接有活动。

4. **入口代码**：

   ```python
   @app.post("/v1/chat/completions")
   async def chat_completions(request: Request):
       # HTTP 框架把这次 POST 交到这里。
       ...
   ```

## 本场景的输入与输出

输入 request 中包含本地 Proxy 转换后的 OpenAI JSON 正文和关联请求头。返回流水线的响应，或带心跳的 StreamingResponse；响应交回本地 RolloutLLMProxy，再由它转换成 Anthropic 协议给 CLI。

<a id="chat-completions-entry"></a>

### 1. 接收正文 · 当前

```python
_check_auth(request)
body = await request.json()               # 读取已转换好的 OpenAI 格式 JSON。
stream = bool(body.get("stream", False))  # 读取本次请求是否要求流式响应。
```

<a id="response-modes"></a>

### 2. 两种响应模式、三种等待组合

`pipeline` 是生成处理函数，`stream` 是响应模式。当前入口收到的正文已经是 OpenAI Chat Completions 格式；下面比较的是同一协议下的两种响应模式，以及心跳配置造成的三种等待组合。

| 正常请求条件 | 等待处理的方式 | 最终正常响应 |
| --- | --- | --- |
| stream=False | 直接 await 同一个 pipeline | JSONResponse，一份完整结果 |
| stream=True，心跳间隔不大于 0 | 直接 await 同一个 pipeline | StreamingResponse，SSE 事件流 |
| stream=True，启用心跳 | 在 Task 中执行同一个 pipeline；若等待超过心跳间隔，则先按需发心跳 | 生成完成后转交 pipeline 的 SSE 响应流 |

表中的 JSON/SSE 内容由下游 pipeline 末尾组织；本函数决定怎样等待它，以及是否在等待期间包装心跳。

```python
# 非流式，或者流式但未启用心跳：直接等待同一个处理函数。
if not stream or stream_heartbeat_interval_seconds <= 0:
    return await _chat_completions_pipeline(request, body)

# 流式且启用心跳：让流水线执行，外层负责等待及心跳。
task = asyncio.create_task(_chat_completions_pipeline(request, body))
# 后续等待/心跳细节见折叠源码；不在入口函数里展开生成算法。
```

两种响应都经过“准备输入 → 模型生成 → 记录本次交互”。当前默认 /generate 路径先得到生成结果，pipeline 尾部再用 _pseudo_stream_chunks 组织 SSE；等待时的心跳不携带模型答案，不能当成 SGLang 正在逐 token 输出。此处只对比正常路径，具体逐段阅读继续选择 stream=True。

两条等待路径都交给 `_chat_completions_pipeline:1939`。当前进入 [_chat_completions_pipeline 函数卡](create_app._chat_completions_pipeline.md#pipeline-overview)，先看完整六段主线，再按需要回到具体段落；本轮不拆心跳 Task 或取消辅助函数。

<details>
<summary>完整函数：等待、心跳、响应与错误处理</summary>

```python
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Run the chat completion, keeping the upstream connection warm.

    ``/generate`` is not streaming, so a ``stream=true`` request would
    otherwise send nothing until generation finished and get cut by an idle
    gateway.  Heartbeat comment frames keep the Dressage -> blackbox hop
    alive while generation runs.

    Invariant relied upon downstream: because the response body is
    pseudo-streamed from an already-computed result, heartbeats and the
    terminal error event can only appear *before* the first real chunk.
    The blackbox proxy therefore only has to drain the heartbeat prelude and
    inspect a single frame.  Turning ``/generate`` into real token streaming
    would break that assumption and require full-stream error sniffing.
    """

    _check_auth(request)
    body = await request.json()
    stream = bool(body.get("stream", False))

    if not stream or stream_heartbeat_interval_seconds <= 0:
        return await _chat_completions_pipeline(request, body)

    # Keep the original HTTP status for anything that settles before the
    # first heartbeat commits the response.
    task = asyncio.create_task(_chat_completions_pipeline(request, body))
    task.add_done_callback(_consume_task_exception)
    try:
        done, _ = await asyncio.wait(
            {task},
            timeout=stream_heartbeat_interval_seconds,
        )
    except asyncio.CancelledError:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        raise
    if done:
        return task.result()

    async def _heartbeat_stream():
        try:
            while True:
                if task.done():
                    break
                yield _SSE_HEARTBEAT
                finished, _ = await asyncio.wait(
                    {task},
                    timeout=stream_heartbeat_interval_seconds,
                )
                if finished:
                    break
            try:
                result = task.result()
            except HTTPException as exc:
                yield _stream_error_chunk(exc.status_code, exc.detail)
                yield "data: [DONE]\n\n"
                return
            except Exception:
                logger.exception("chat completion failed during heartbeat streaming")
                yield _stream_error_chunk(
                    500,
                    {
                        "code": "internal_error",
                        "message": "Internal proxy error.",
                    },
                )
                yield "data: [DONE]\n\n"
                return
            if not 200 <= result.status_code < 300:
                yield _stream_error_chunk(
                    result.status_code, _response_json_payload(result)
                )
                yield "data: [DONE]\n\n"
                return
            assert isinstance(result, StreamingResponse)
            async for chunk in result.body_iterator:
                yield chunk
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                logger.info("chat completion client disconnected; cancelled generation")

    return StreamingResponse(
        _heartbeat_stream(),
        media_type="text/event-stream",
        headers=_SSE_RESPONSE_HEADERS,
    )
```

</details>

## 我的直接表述（原话）

> 好的 那么 我们知道这个的情况下 应该看什么了呢?
> 现在应该看这个proxy把这里的内容发送到了哪里?

当前先接上发送端与接收端，尚无对服务端内部机制的个人复述。

本轮概念追问：

> 这里有不是流水线的方式吗?
> 还是都是流水线?
> stream的方式?
> 我记得当时应该有两种?

助手校准：两种是非流式/流式响应；都使用同一个 pipeline，外层按 stream 与心跳配置选择等待方式。未据问题本身认定已经理解。

## 尚不清楚

- _chat_completions_pipeline 的输入准备、生成和单步记录，下一层继续。
- 心跳是等待期间的响应活动，不代表模型真实 token 已经流式产出；内部实现暂缓。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对本函数及其 POST 路由；本地 Proxy 的上游 URL 由 upstream_origin/router_api_path 配置。
- 当前默认 SGLang /generate 路径先完成生成，再组织模型响应；本入口的心跳可在生成等待期间发送。这里没有把心跳等同于模型输出。
- 只读源码，未发 HTTP 或调用模型。[本轮记录](../../../../../04-flow.md#external-proxy-chat-entry)。

</details>
