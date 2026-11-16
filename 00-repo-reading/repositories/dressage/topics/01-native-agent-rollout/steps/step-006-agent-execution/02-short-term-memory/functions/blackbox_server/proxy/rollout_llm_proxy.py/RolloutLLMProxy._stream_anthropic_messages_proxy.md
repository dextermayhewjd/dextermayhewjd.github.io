# RolloutLLMProxy._stream_anthropic_messages_proxy

- 源码：[rollout_llm_proxy.py:1167–1266](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/proxy/rollout_llm_proxy.py#L1167)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次展开：Step 006 公共 Proxy 补读，2026-11-15。
- 最近认识更新：开始阅读发送部分；尚无对本函数内部的个人复述。

[_handle_proxy 的流式分支](RolloutLLMProxy._handle_proxy.md#handle-proxy-forward) → **当前函数** → _send_stream_request → 跨 HTTP 进入 Dressage Proxy；之后回到本卡读响应转换。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_handle_proxy 已把 Claude 请求转为 OpenAI 格式，并确定本次请求的 stream=True。
2. **具体内容**：发送上游请求，检查响应，再将 OpenAI 响应流转成 Anthropic 事件流；流结束时关闭上游响应并结束请求标记。
3. **建议构建的心智模型**：

   > 去程发送已经转换好的请求，回程提供 Claude 能读取的事件流；本轮先看去程。

4. **调用代码**（_handle_proxy 的 Anthropic 流式分支）：

   ```python
   return await self._stream_anthropic_messages_proxy(
       upstream_url, body_bytes, headers, snapshot
   )
   ```

## 本场景的输入与输出

| 传入值 | 上一层已经准备好的内容 |
| --- | --- |
| url | 上游 Dressage Proxy 的 chat/completions 地址，由运行配置确定 |
| body | OpenAI Chat Completions 格式的 JSON 字节正文 |
| headers | 已整理的上游请求头，包含 session/instance/turn 等关联信息 |
| snapshot | 当前交互轮次的快照，用于错误与请求收尾；不作为另一个模型正文发送 |

正常返回 StreamingResponse，通过上层 HTTP 入口交回 CLI；错误路径可返回错误 Response。返回响应对象不表示已经把整个响应流发送完。

<a id="send-upstream"></a>

### 1. 发送已经准备好的请求 · 当前

发送段节选，异常时的请求标记清理见完整源码。

```python
assert self._client is not None  # Proxy 已有可用的 HTTP 客户端。
upstream_response = await self._send_stream_request(url, body, headers)
# 得到上游 HTTP 响应对象，响应体随后读取；并不表示模型已经生成完毕。
```

<a id="http-send-line"></a>

**真正发送 HTTP 的位置**在 _send_stream_request:1455–1456。这里直接摘出两句，先不展开其余辅助语句：

```python
request = self._client.build_request("POST", url, content=body, headers=request_headers)
return await self._client.send(request, stream=True)  # 向上面的 url 发出请求，取得流式响应对象。
```

调用链是 `_handle_proxy:605 → 本函数:1176 → _send_stream_request:1456`。此时上层 _handle_proxy 仍在等待转发函数，不是已经返回后才发请求。接着从这个发送点跨 HTTP 进入 [外部 Dressage Proxy.chat_completions](../../../dressage/proxy/server.py/create_app.chat_completions.md#chat-completions-entry)，再于回程继续下面的响应处理。

<a id="response-return"></a>

### 2. 上游响应回来后继续的位置 · 待回程阅读

| 位置 | 该段做什么 |
| --- | --- |
| 1182–1246 | 检查状态、读取初始响应内容，处理保活前缀和错误响应 |
| 1250–1266 | _forward 从上游读取并转换 Anthropic 事件，StreamingResponse 将其提供给 CLI；最后释放响应与请求标记 |

这两段保留为 scope 9.2e 的回程入口，本轮先不逐段展开。

<details>
<summary>完整函数：响应、错误转换与流清理</summary>

```python
async def _stream_anthropic_messages_proxy(
    self,
    url: str,
    body: bytes,
    headers: dict[str, str],
    snapshot: _TurnSnapshot | None,
) -> Response:
    assert self._client is not None
    try:
        upstream_response = await self._send_stream_request(url, body, headers)
    except BaseException:
        if snapshot is not None and snapshot.scope is not None:
            await self._mark_request_finished(snapshot.scope)
        raise

    if upstream_response.status_code >= 400:
        error_status: int | None = upstream_response.status_code
        error_body = await upstream_response.aread()
        first_bytes = b""
        byte_iter: AsyncIterator[bytes] | None = None
    else:
        error_status = None
        error_body = b""
        byte_iter = upstream_response.aiter_bytes()
        try:
            first_bytes, sniffed = await self._drain_keepalive_prelude(byte_iter)
        except BaseException:
            # The prelude awaits for the whole generation, so a disconnect
            # or cancellation here must still release the connection and
            # the request marker that _forward() would normally clean up.
            await upstream_response.aclose()
            if snapshot is not None and snapshot.scope is not None:
                await self._mark_request_finished(snapshot.scope)
            raise
        if sniffed is not None:
            error_status, error_body = sniffed

    if error_status is not None:
        self._log_upstream_error(
            url=url,
            status_code=error_status,
            response_headers=dict(upstream_response.headers),
            response_body=error_body,
            retried=False,
        )
        if snapshot is not None and snapshot.scope is not None:
            await self._record_context_overflow_error(
                snapshot.scope,
                status_code=error_status,
                response_body=error_body,
            )
            if await self._record_rollout_invalidated_error(
                snapshot.scope,
                status_code=error_status,
                response_body=error_body,
            ):
                await upstream_response.aclose()
                await self._mark_request_finished(snapshot.scope)
                return self._synthetic_anthropic_message_stream_response()
        await self._record_failed_upstream_error(
            snapshot,
            url=url,
            status_code=error_status,
            request_headers=headers,
            request_body=body,
            response_headers=dict(upstream_response.headers),
            response_body=error_body,
        )
        await upstream_response.aclose()
        if snapshot is not None and snapshot.scope is not None:
            await self._mark_request_finished(snapshot.scope)
        if 500 <= error_status < 600:
            return self._anthropic_non_retry_upstream_error_response(
                upstream_status_code=error_status,
                response_body=error_body,
            )
        return self._anthropic_error_response_from_bytes(
            status_code=error_status,
            response_body=error_body,
        )

    assert byte_iter is not None

    async def _forward():
        try:
            async for event in self._iter_anthropic_events_from_openai_stream(
                first_bytes,
                byte_iter,
            ):
                yield event
        finally:
            await upstream_response.aclose()
            if snapshot is not None and snapshot.scope is not None:
                await self._mark_request_finished(snapshot.scope)

    return StreamingResponse(
        _forward(),
        status_code=upstream_response.status_code,
        media_type="text/event-stream",
    )
```

</details>

## 我的直接表述（原话）

> 好的 那么现在看一下 下一个函数需要做什么吧

沿已确认的 9.2a 接续进入发送部分，尚无机制复述。

## 尚不清楚

- _send_stream_request 的实际发送和 HTTP 返回边界，下一处继续。
- 响应的保活、错误与事件转换在回程再读；不提前认定已经理解。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对完整函数与 _send_stream_request:1445–1456；后者用 HTTPX 的 send(..., stream=True)，所以返回响应对象与消费完响应体是不同阶段。
- 当前 stream=True 是选定的阅读分支，不是从 CLI stdout 的 stream-json 标志推断，也没有实际抓取模型请求。
- 未启动客户端或请求模型。[本次记录](../../../../../04-flow.md#stream-proxy-send-entry)。

</details>
