# _GatewayASGI._handle_http

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/_GatewayASGI._handle_http.md) 完整继承；不改变原认识时间或掌握状态。

- 源码：[gateway.py:864–949](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L864)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独展开：Step 014 第三部分第 4 项，2026-11-14。
- 最近认识更新：2026-11-14，用户尝试概括查路由、准备请求、转交和超时；本轮校准进程内 Proxy 委派与响应 idle timeout，理解仍待反馈。

[ClaudeCode.run 启动 CLI](../../../../harbor/agents/installed/claude_code.py/ClaudeCode.run.md#claude-run-mainline) → CLI 发 HTTP 请求 ⇒ 网关的 _GatewayASGI.__call__ → **当前 _handle_http** → 对应 Proxy.app → 原请求的响应出口。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：已登记并激活路由，Claude CLI 的一次模型请求现在到达 Gateway。
2. **具体内容**：从请求头识别路由，按配置处理请求内容与头部，交给对应 Proxy，并沿原请求返回响应。
3. **建议构建的心智模型**：

   > 之前建立的 token → Proxy 表，现在被真实请求查用；每个请求继续携带自己的响应出口。

4. **调用代码**（_GatewayASGI.__call__:862，HTTP 分支）：

   ```python
   await self._handle_http(
       scope,    # Web 服务器给出的本次请求信息：方法、路径、请求头等。
       receive,  # 读取本次请求体的函数。
       send,     # 向这个请求的发起方发送响应的函数。
   )
   ```

## 本场景的输入与输出

沿用 Claude CLI 的普通模型请求，token 已配置并有对应 ACTIVE 路由。这里已经跨过 HTTP 边界：输入由 Web 服务器交入，不是 _on_agent_start 直接调用本函数。正常返回 None，HTTP 响应内容经 send 发出。

<a id="gateway-http-mainline"></a>
<a id="gateway-http-route"></a>

### 1. 从请求头找到已有路由 · 当前先读

正常请求节选：协议路径、token 缺失/冲突、未知与过期路由检查在完整源码中保留；这里先看凭证有效且路由已登记的情况。

```python
runtime = self._runtime
headers = list(scope.get("headers", []))
token, conflict = _extract_route_token(headers)  # 从请求头读取路由 token。
digest = _token_digest(token)
binding = runtime._routes.get(digest)            # 查前面 _register 建好的表。

if binding.state != AttemptState.ACTIVE:
    await _send_json(send, 409, {"error": "route_not_active"})
    return  # 对应前一步：路由还没有激活，就不能继续处理请求。
```

<a id="gateway-http-forward"></a>

### 2. 准备交给 Proxy 的请求

下面接住已有 binding；并发容量与请求体大小的失败分支暂略。

```python
body = await _read_body(
    receive, runtime.config.gateway.limits.request_body_max_bytes
)
request_sequence = binding.request_sequence
binding.request_sequence += 1
rewritten_body = _rewrite_payload(body, binding.spec, request_sequence)  # 按配置处理模型/采样参数。
rewritten_scope = dict(scope)
rewritten_scope["headers"] = _rewrite_agent_headers(
    headers, len(rewritten_body)  # 移除 Agent 凭证头，更新请求体长度。
)
delegated_receive = _BufferedReceive(rewritten_body, receive)  # 让 Proxy 读到处理后的请求体。
tracked_send = _ActivitySend(send)                           # 保留本次请求的响应出口。
```

### 3. 在进程内调用 Proxy，响应回到 CLI

```python
await _dispatch_with_idle_timeout(
    binding.proxy.app(rewritten_scope, delegated_receive, tracked_send),
    tracked_send,
    timeout=runtime.config.gateway.limits.sse_idle_timeout_sec,  # 等待响应活动的空闲上限。
)
```

这是进程内的 ASGI 委派。Proxy 返回的响应消息经 tracked_send 调用原 send，回到正在等待这一请求的 CLI；本函数不另保存 Sandbox 回传地址。原实现最后在 finally 归还本次请求占用的并发名额。

一次 HTTP 响应返回后，CLI 还可以继续工具调用或发下一次模型请求；只有 Agent 执行结束，才接回外层 ClaudeCode.run。公共 Proxy 内部的协议转换与上游生成按既定补读范围另看。

**本轮只需接清四步**：按 token 查 binding → 整理请求 → 进程内委派 Proxy.app → 经原 send 返回响应。idle timeout 监测“多久没有响应活动”，不是整个 Agent 的总执行时限；长时间无响应活动会中断这次代理处理。路径/凭证/状态/大小/容量检查先认保护用途，不再逐个下钻辅助函数。

请求整形先记住：body 可按配置调整模型和采样参数，headers 会清理 Agent 凭证并更新长度；协议转换与真正的上游 HTTP 请求由公共 Proxy 负责。

<details>
<summary>完整函数：路径、身份、状态、大小、容量与超时检查</summary>

```python
async def _handle_http(
    self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend
) -> None:
    runtime = self._runtime
    runtime._cleanup_tombstones()
    method = str(scope.get("method", "GET")).upper()
    path = str(scope.get("path", "/")).rstrip("/") or "/"
    allowed = (method, path) in _MODEL_PATHS
    if method == "GET" and path == "/v1/models":
        allowed = runtime.config.security.allow_model_listing
    if not allowed:
        await _send_json(send, 404, {"error": "not_found"})
        return

    headers = list(scope.get("headers", []))
    token, conflict = _extract_route_token(headers)
    if conflict:
        await _send_json(send, 400, {"error": "conflicting_route_tokens"})
        return
    if token is None:
        await _send_json(send, 401, {"error": "missing_route_token"})
        return
    digest = _token_digest(token)
    binding = runtime._routes.get(digest)
    if binding is None:
        if digest in runtime._tombstones:
            await _send_json(send, 410, {"error": "route_closed"})
        else:
            await _send_json(send, 401, {"error": "unknown_route_token"})
        return
    if (
        time.monotonic() - binding.created_at
        >= runtime.config.gateway.limits.route_ttl_sec
    ):
        await runtime._close_binding(binding, tombstone=True)
        await _send_json(send, 410, {"error": "route_expired"})
        return
    if binding.state == AttemptState.BROKEN:
        await _send_json(send, 503, {"error": "route_broken"})
        return
    if binding.state == AttemptState.CLOSED:
        await _send_json(send, 410, {"error": "route_closed"})
        return
    if binding.state != AttemptState.ACTIVE:
        await _send_json(send, 409, {"error": "route_not_active"})
        return

    header_size = sum(len(name) + len(value) for name, value in headers)
    if header_size > runtime.config.gateway.limits.request_header_max_bytes:
        await _send_json(send, 431, {"error": "request_headers_too_large"})
        return

    acquired = await self._acquire_capacity(binding)
    if not acquired:
        await _send_json(send, 503, {"error": "gateway_busy"})
        return
    try:
        if binding.state != AttemptState.ACTIVE:
            await _send_json(send, 409, {"error": "route_not_active"})
            return
        body = await _read_body(
            receive, runtime.config.gateway.limits.request_body_max_bytes
        )
        if body is None:
            await _send_json(send, 413, {"error": "request_body_too_large"})
            return
        request_sequence = binding.request_sequence
        binding.request_sequence += 1
        rewritten_body = _rewrite_payload(body, binding.spec, request_sequence)
        rewritten_scope = dict(scope)
        rewritten_scope["headers"] = _rewrite_agent_headers(
            headers, len(rewritten_body)
        )
        delegated_receive = _BufferedReceive(rewritten_body, receive)
        tracked_send = _ActivitySend(send)
        try:
            await _dispatch_with_idle_timeout(
                binding.proxy.app(rewritten_scope, delegated_receive, tracked_send),
                tracked_send,
                timeout=runtime.config.gateway.limits.sse_idle_timeout_sec,
            )
        except asyncio.TimeoutError:
            if not tracked_send.response_started:
                await _send_json(send, 504, {"error": "upstream_idle_timeout"})
    finally:
        self._release_capacity(binding)
```

</details>

## 我的直接表述（原话）

用户在询问 operation 后选择继续（节选）：

> 那么请继续看一下下一个部分吧

本轮追问与概括：

> 好的 除了这个部分之外
> 我们还有什么需要单独看的吗?
> 我其实不是特别明白了
> 感觉这一部分其实还是挺杂的
> 什么都有的感觉
> 感觉比slime复杂很多
> 以至于其实我不是特别清楚这个http服务到底是在做什么
> 简单来说是先找到当前这个路由
> 然后准备好这个http请求具体是什么
> 然后在把这个请求发出去?
> 可以接受一定的idle和timeout?
> 还有什么是我需要看和注意的吗?

助手校准：主干归纳基本对应源码；“发出去”在本函数是进程内调用对应 Proxy.app，外部上游请求属于 Proxy。响应沿原 send 返回，idle timeout 关注响应活动；辅助检查暂不增加为独立必读卡。

## 尚不清楚

- token 提取、请求改写和 receive/send 包装先认职责，不逐个建立辅助卡；当前对四步主干的理解仍待反馈。
- 公共 RolloutLLMProxy 如何转换协议与请求后端，留到共享补读。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对 _GatewayASGI.__call__:856–862 与 _handle_http:864–949。
- _extract_route_token:1107 读取支持的凭证头，并检查多个值是否冲突；_rewrite_payload:1073 按配置覆盖模型、采样参数和 seed；_rewrite_agent_headers:1127 去掉凭证及原长度/传输编码头，再写入新长度。本轮只核对用途。
- _ActivitySend:1014–1018 最终 await 原 send(message)，并记录响应活动；这是原请求的响应通道。_dispatch_with_idle_timeout:1021 起等待处理任务完成或新的响应活动，超时会取消代理处理任务；调用方仅在响应尚未开始时尝试返回 504。
- 当前为静态正常路径阅读，未发真实请求或验证后端连通性；源码片段不能替换完整实现。
- [本轮记录](../../../../../../../step-014-model-routing-and-api-contract/04-flow.md#gateway-http-entry)。

</details>
