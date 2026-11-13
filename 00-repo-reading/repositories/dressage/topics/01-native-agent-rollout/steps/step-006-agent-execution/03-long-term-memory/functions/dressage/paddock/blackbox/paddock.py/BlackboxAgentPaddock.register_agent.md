# BlackboxAgentPaddock.register_agent

> Step 006 继承：来自 [Step 005 的 02-short-term-memory 记录](../../../../../../../step-005-agent-registration/02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

[generate:232 调用处](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L232) → **本函数** → [BlackboxServerClient.register_agent](../client.py/BlackboxServerClient.register_agent.md)。

- 源码：[paddock.py:153–182](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L153)。
- 首次接触：2026-11-06，旧卡已按用户要求移入历史；本轮于 2026-11-07 从头重读。
- 最近认识更新：本轮尚无用户机制复述；此卡是重新核对的代码说明，不恢复旧卡的掌握假设。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 已取得环境和 state，接下来调用这个 Paddock 方法发起注册。
2. **具体内容**：从 state 找到环境入口，整理注册参数，交给 BlackboxServerClient；把客户端回复返回上层。
3. **建议构建的心智模型**：

   > 先确定“向哪个已有环境发请求”，再把入口和注册信息交给客户端。本轮先看找到入口这一段，后续怎样发送、服务端怎样处理，沿调用链再读。

4. **调用代码**（generate 中的真实调用）：

   ```python
   await maybe_await(
       paddock.register_agent(
           state,
           instance_id=instance_id,
           session_id=session_id,
           router_url=proxy_url(),
           blackbox_type=blackbox_type,
           backend_options=backend_options,
       )
   )
   ```

## 本场景的输入与输出

**整个函数的输入**：已有 state、任务/会话 ID、Agent 类型、后端选项与代理地址。本次未传的 router_api_path 默认 /v1，system_prompt_file 默认 None。self 是持有环境记录及 BlackboxServerClient 的 Paddock 实例。

**整个函数的输出**：客户端返回的注册响应字典；generate 只等待此调用正常完成，随后进入前置命令。本函数不返回新的 state，也不再次调用 provider.create。

### 完整函数：当前先看 [1]

执行语句来自源码，仅添加中文阅读注释。[2] 已补充地址方向的说明，Agent 类型整理及 [3] 客户端内部仍保留后续位置。

```python
async def register_agent(
    self,
    state: SandboxState | str,
    *,
    instance_id: str,
    session_id: str,
    router_url: str | None = None,
    blackbox_type: str = DEFAULT_BLACKBOX_TYPE,
    backend_options: Any = None,
    router_api_path: str = "/v1",
    system_prompt_file: str | None = None,
) -> dict[str, Any]:
    # [1] 当前展开：从 state 找到环境入口。
    state = self._resolve_state(state)
    lease = self._leases.get(state.trajectory_id)
    # endpoint.url：当前 sandbox 内的 BlackboxServer 地址，注册请求发给它。
    endpoint = self._endpoint_for_state(state, lease)
    # [2] 选择模型代理的上游地址，并整理 Agent 类型。
    # router_url：调用方这次指定的 Dressage Proxy 地址；它不是 sandbox 地址。
    # self._proxy_public_url：Paddock 构造时保存的默认 Proxy 地址。
    # 优先用 router_url，未传或为空时才用默认值；public 表示应从沙箱可访问。
    # 此处只检查 URL 格式等条件，不创建代理，也不发请求验证连通性。
    router = _validate_public_proxy_url(router_url or self._proxy_public_url)
    blackbox_type = normalize_blackbox_type(blackbox_type)
    # [3] 后续位置：把入口与注册参数交给客户端，返回它的回复。
    return await self._client.register_agent(
        endpoint,
        trajectory_id=state.trajectory_id,
        instance_id=instance_id,
        session_id=session_id,
        # 作为注册正文中的配置传给 sandbox，告诉它后续模型请求的上游地址。
        router_url=router,
        blackbox_type=blackbox_type,
        backend_options=merge_backend_options(blackbox_type, backend_options),
        server_config=_server_config_for_provider(self._provider.name, blackbox_type),
        router_api_path=router_api_path,
        system_prompt_file=system_prompt_file,
        sandbox_id=state.sandbox_id,
    )
```

<a id="resolve-endpoint"></a>

### [1] 找到请求入口（165–167 行）

1. 解析 state，按 trajectory_id 找回 Paddock 保存的 lease。
2. 优先取 lease 的 blackbox endpoint；没有时，用 state.sandbox_url 和空 headers 构造入口。

按需查看 [_resolve_state](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L299)、[_endpoint_for_state](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L311)；取得 endpoint 后回到 168 行。

<a id="two-url-directions"></a>

### [2] 选出模型代理地址（168 行）

1. **endpoint.url**：注册请求发往的沙箱服务地址。
2. **router**：优先用传入的 router_url，否则用构造时保存的 self._proxy_public_url。它指向 Dressage Proxy，作为配置告诉沙箱“后续模型请求去哪里”。

此处只检查地址格式等条件，不发送网络请求；随后继续整理 Agent 类型并交给客户端。

## 我的直接表述（原话）

本轮明确请求：

> 那么请生成一下这里的这个paddock register agent部分的代码说明吧

这是重读后建卡请求，尚无对本轮三行代码的机制复述。之前的困惑与表述保留在[旧卡归档](../../../../../../../step-005-agent-registration/references/history/restart-from-callsite-2026-11-06/02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md)和过程记录，不预填为已经理解。

本轮追问：

> 这里关于proxy的部分我其实一直没有明白
> 这个url是用来访问具体的某一个sandbox位置的吗?
> 还是说用来访问其他内容的?
> 我一直不是特别理解

助手对照 endpoint.url 与 router_url 的请求方向，尚未收到用户理解确认。

## 尚不清楚

- 本轮需要先确认从 state 找回 lease/endpoint 的关系。
- 后续参数怎样组成客户端请求、服务端收到后怎样配置 Agent，仍按 scope 逐层展开。

<details>
<summary>来源与验证</summary>

- 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮核对源码工作区干净。
- 主方法及 _resolve_state、_endpoint_for_state 来自同一个 paddock.py；调用方为 generate:232–241。
- [分段说明与示例的精简前记录](../../../../../../../step-005-agent-registration/references/history/paddock-register-explanations-before-trim-2026-11-07.md)。
- [本步过程](../../../../../../../step-005-agent-registration/04-flow.md)。仅静态核对，没有创建环境或发送注册请求。

</details>
