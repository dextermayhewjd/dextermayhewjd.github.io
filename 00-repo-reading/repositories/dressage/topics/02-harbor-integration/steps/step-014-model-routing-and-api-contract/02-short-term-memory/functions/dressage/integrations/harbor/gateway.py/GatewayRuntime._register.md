# GatewayRuntime._register

- 源码：[gateway.py:594–633](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L594)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独展开：Step 014，2026-11-14。
- 最近认识更新：2026-11-14，用户已概括创建 Proxy、绑定 Trial 资料的过程；返回 handle 与模型响应返回的区别仍待本轮澄清。

[_on_start 准备登记资料](../plugin.py/DressageHarborPlugin._on_start.md#trial-start-mainline) → [lease.register](GatewayLease.register.md#lease-register-mainline) → [runtime.call 调度](GatewayRuntime.call.md#runtime-call-mainline) → **当前 _register**。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：已有 Gateway，收到某次 Trial 的身份、token 与代理配置，需要为它建立请求处理入口。
2. **具体内容**：创建对应 Proxy，把绑定记录放进路由表，进入应用生命周期，再返回操作对象。
3. **建议构建的心智模型**：

   > 给这次 Trial 准备一个 Proxy，并记下“这个 token 应该找到它”。以后请求到达时按 token 查这张表。

4. **调用代码**（GatewayLease.register 经 runtime.call 委派）：

   ```python
   return await self._runtime.call(
       lambda: self._runtime._register(spec)
   )
   ```

## 本场景的输入与输出

`spec` 是 _on_start 准备的 RouteSpec，包含本次 Trial 身份、token 和上游配置。`self` 是已经运行的 GatewayRuntime。本函数新增 `_routes` 中的一条记录，正常返回 `AttemptHandle`，最终交回 _on_start 的 record.handle。

<a id="runtime-register-mainline"></a>

正常路径节选：容量、重复 token 检查与失败清理折叠保留。先关注创建 Proxy、保存路由表、交回操作对象三个动作。

```python
digest = _token_digest(spec.token)  # 用 token 的摘要作为查找键。
proxy = self._create_proxy(spec)    # 默认创建这次尝试对应的 RolloutLLMProxy。

lifespan_factory = getattr(
    getattr(proxy.app, "router", None), "lifespan_context", None
)
lifespan = lifespan_factory(proxy.app)
binding = _RouteBinding(
    spec=spec,                     # 保存 Trial 身份与代理配置。
    token_digest=digest,
    proxy=proxy,                   # 保存本次请求应交给的 Proxy 对象。
    lifespan=lifespan,
    semaphore=asyncio.Semaphore(
        self.config.gateway.limits.max_inflight_per_route
    ),
)
self._routes[digest] = binding      # 核心：在 Gateway 的路由表中保存这个对应关系。

await lifespan.__aenter__()         # 初始化 Proxy 应用的运行资源。
binding.state = AttemptState.READY
return AttemptHandle(self, binding) # 给调用方一个操作这条路由的对象。
```

`binding` 把 Trial 资料和 Proxy 放在一起；`handle` 供插件以后操作这条绑定。路由先为 READY，后续 AGENT_START 的 open_turn 再激活它。

**两种返回分开看**：当前登记函数返回的是 AttemptHandle，供 _on_start 保存；binding 留在 Gateway 路由表里。之后模型请求的 HTTP 响应沿本次请求自带的 send 返回 CLI，不依靠这里保存 Sandbox 回传地址。

### 这张表以后用在哪里

Gateway 收到请求时，会从请求头取 token，然后查刚才保存的表。以下仅定位消费位置，不在本轮展开 HTTP 处理函数：

```python
# _GatewayASGI._handle_http:886–887
digest = _token_digest(token)
binding = runtime._routes.get(digest)
# 验证与处理后，调用 binding.proxy.app(...) 处理该请求。
```

**钩子负责何时触发，当前函数负责建立什么关系。** 理解这里时，只需先知道 Harbor 的 START 会调用已经登记的 Dressage._on_start(event)；不用重读钩子存储、事件分发与跨循环调度内部。

<details>
<summary>完整函数：检查、应用生命周期与失败撤回</summary>

```python
async def _register(self, spec: RouteSpec) -> AttemptHandle:
    self._cleanup_tombstones()
    if len(self._routes) >= self.config.gateway.limits.max_active_routes:
        raise GatewayError("gateway max_active_routes limit reached")
    digest = _token_digest(spec.token)
    if digest in self._routes:
        raise RouteConflictError("route token is already active")
    if digest in self._tombstones:
        raise RouteConflictError("route token is tombstoned and cannot be reused")

    proxy = self._create_proxy(spec)
    lifespan_factory = getattr(
        getattr(proxy.app, "router", None), "lifespan_context", None
    )
    if not callable(lifespan_factory):
        raise GatewayError("RolloutLLMProxy.app does not expose a lifespan context")
    lifespan = lifespan_factory(proxy.app)
    binding = _RouteBinding(
        spec=spec,
        token_digest=digest,
        proxy=proxy,
        lifespan=lifespan,
        semaphore=asyncio.Semaphore(
            self.config.gateway.limits.max_inflight_per_route
        ),
    )
    self._routes[digest] = binding
    try:
        await lifespan.__aenter__()
    except BaseException as exc:
        self._routes.pop(digest, None)
        binding.state = AttemptState.BROKEN
        binding.broken_reason = (
            f"proxy lifespan startup failed: {type(exc).__name__}: {exc}"
        )
        if isinstance(exc, asyncio.CancelledError):
            raise
        raise GatewayError(binding.broken_reason) from exc
    binding.state = AttemptState.READY
    return AttemptHandle(self, binding)
```

应用生命周期初始化失败时，代码从 _routes 移除这条 binding 并记录 BROKEN。这里创建的是 Gateway 进程中的 Proxy 应用对象；进入 lifespan 不等于另外启动一个 HTTP 监听端口。

</details>

## 我的直接表述（原话）

用户要求回到实际登记与系统用途（节选）：

> 那么可以带着我看一下这里的这个register到底是在做什么吗?
> 我其实不是特别理解
> 我说的是这里的这个系统
> 这个gateway的这个系统到底是怎么设计的我感觉我不是特别理解

并追问：

> 或者你觉得我需要知道这个钩子系统到底是如何实现的吗?
> 还是说目前先知道这个emit的这个钩子系统能够让这个on start函数直接传输进去呢?
> 所以我需要了解的是
> 哪一个函数呢?

助手校准：登记回调时保存函数，发出事件时调用该函数并传入 event。当前先以这项约定接入业务，阅读 _register 建立路由表的动作；不将这些疑问记为已掌握。

本轮复述中的关键疑问（节选）：

> 然后通过这个routebind了之后把trial资料和proxy放在了一起
> 最后返还调用方这个binding?
> 也就是这里的这个请求之后应该返还到哪里?

助手校准：binding 保存到 _routes，返回调用方的是 AttemptHandle。runtime.call 的用途是切到网关所属事件循环执行，不能仅归因为“有 I/O”。HTTP 响应返回与登记函数返回是两条不同路径，完整复述见本轮 flow。

## 尚不清楚

- _create_proxy 怎样把 RouteSpec 绑定到具体代理、Proxy 怎样转发模型请求，后续按需进入。
- Gateway 的完整 HTTP 校验、改写与分派尚未逐段阅读。
- 事件注册、跨循环调度的实现细节保留原卡，当前不继续扩展。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对 _register:594–633、_RouteBinding:242 起、_default_proxy_factory:705–708 与 _handle_http:886–887、941。
- 当前 _create_proxy 使用默认 factory 时创建 RolloutLLMProxy；该 factory 可替换，不把默认路径描述成所有注入实现的唯一行为。
- 请求返回原 HTTP 请求的响应通道；路由表保存的是请求归属/处理对象，不是 Sandbox 回传地址。gateway.py:938–943 将当前请求的 send 包装后交给 proxy.app，_ActivitySend:1014–1018 最终调用原 send；rollout_llm_proxy.py:1250–1267 以 StreamingResponse 返回转换后的流式响应。
- 未实际执行路由登记、应用生命周期或请求分派。[本轮记录](../../../../../../04-flow.md#runtime-register-business-entry)。

</details>
