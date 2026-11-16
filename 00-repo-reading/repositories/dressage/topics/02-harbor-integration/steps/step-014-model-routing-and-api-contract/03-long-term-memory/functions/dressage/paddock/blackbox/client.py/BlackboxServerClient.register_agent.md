> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# BlackboxServerClient.register_agent

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 02-short-term-memory 记录](../../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

[Paddock.register_agent](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md) → **本函数：客户端发送** → HTTP /v1/rollout/register；回复后返回 Paddock。

- 源码：[client.py:60–95](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L60)。
- 首次接触：2026-11-06；旧卡已归档，本轮于 2026-11-07 从头重读。
- 最近认识更新：2026-11-07，用户已表述按 endpoint 发送并接收的理解；助手校准客户端/服务端身份及注册与探测的区别。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Paddock 已找到 endpoint，准备好身份和 Agent 配置，调用客户端把信息发出去。
2. **具体内容**：组装 payload，补可选字段，发送注册请求并等待回复，返回解析后的响应字典。
3. **建议构建的心智模型**：

   > 本函数是发送方：把 payload 中的注册配置发给 endpoint 指定的 BlackboxServer，要求对方完成 Agent 注册，并等待处理后的 response。它发起的是实际注册，不只是测试请求能否送达；具体处理在服务端，之后再读。

4. **调用位置**：Paddock.register_agent 的最后一个调用为 return await self._client.register_agent(...)；完整实参见[父函数卡](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md)，其中 self._client 就是当前这个客户端对象。

## 本场景的输入与输出

**输入**：endpoint（目标 URL 与请求头）、trajectory_id、instance_id、session_id、router_url、blackbox_type、backend_options、server_config。当前父函数未另指定时，router_api_path 为 /v1，system_prompt_file 为 None，sandbox_id 来自 state。

**输出**：response.json() 得到的注册响应字典，原样交回 Paddock；再上层的 generate 只等待调用正常结束，没有另存此字典。这里不会返回新 sandbox 或新 state。

### 完整函数（中文注释对应三个动作）

```python
async def register_agent(
    self,
    endpoint: SandboxEndpoint,
    *,
    trajectory_id: str,
    instance_id: str,
    session_id: str,
    router_url: str,
    blackbox_type: str,
    backend_options: Any,
    server_config: dict[str, Any],
    router_api_path: str = "/v1",
    system_prompt_file: str | None = None,
    sandbox_id: str | None = None,
) -> dict[str, Any]:
    # [1] 将传入的注册参数装成要发送的字典。
    payload = {
        "blackbox_type": blackbox_type,
        "router": router_url,  # 模型代理地址是正文中的配置，不是本次请求目标。
        "router_api_path": router_api_path,
        "bound_instance_id": instance_id,
        "bound_session_id": session_id,
        "backend_options": backend_options,
        "server_config": server_config,
    }
    # 两个可选字段：满足条件时才加入正文。
    if sandbox_id:
        payload["bound_sandbox_id"] = sandbox_id
    if system_prompt_file is not None:
        payload["system_prompt_file"] = system_prompt_file
    # [2] 向 endpoint.url 对应的沙箱服务发送 POST，并等待回复。
    response = await self._post_agent_with_retry(
        endpoint,
        "/v1/rollout/register",
        json=payload,  # HTTP 请求正文；发送时编码成 JSON。
        operation="register_agent",
        trajectory_id=trajectory_id,
    )
    # [3] response 是收到的回复，解析正文后交回 Paddock。
    return response.json()
```

### 当前只抓住这三点

1. payload 是 Python 字典形式的请求内容；JSON 中的 bound_session_id 来自传入的 session_id，没有在这里新建编号。
2. POST 目标由 endpoint.url 和 /v1/rollout/register 组成，携带 endpoint.headers。正文中的 router 是给对方的模型代理配置；trajectory_id 另交给请求辅助函数，不是此 payload 的字段。
3. await 等待回复；response.json() 解析收到的正文。请求重试策略和服务端初始化暂不在这里展开。

### 怎样从发送端找到接收端

跨 HTTP 的阅读依据是“请求方法 + URL 路径”，不是 Python 直接调用或文件名相似。

1. 本函数传给 _post_agent_with_retry 的 path 是 /v1/rollout/register。
2. [_post_agent_with_retry](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._post_agent_with_retry.md) 将 endpoint.url 与 path 拼接；[post_json_with_retry](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/common/http_retry.py#L55) 实际执行 client.post(...)，所以请求是 POST /v1/rollout/register。
3. 在服务端搜索同一路径，找到 [api/rollout.py:18](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/api/rollout.py#L18) 的 @router.post("/v1/rollout/register", ...)，其处理函数就是 register_rollout。
4. [app.py:117](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/app.py#L117) 用 app.include_router(rollout_router) 挂载这组路由，没有另加路径前缀；api/__init__.py 将 rollout.py 的 router 导出为 rollout_router。

因此下一入口是 register_rollout，它内部才直接调用 server.register(payload)。operation="register_agent" 不是路由选择依据。这里仅核对源码中的收发映射，没有实际发送网络请求。

## 我的直接表述（原话）

> 好的 那么按照这里的这个scope继续往下望看吧
> 我们是否需要看一下这里的这个client server 这里的这个register agent了呢?

本轮选择了下一个调用层，尚未对该层机制复述；之前的困惑保留在[旧卡归档](../../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/references/history/restart-from-callsite-2026-11-06/02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)。

本轮表述：

> 好的 我可以简单理解一下blackbox server这里类似于一个中转站
> 这里是通过输入了这个endpoint
> 看一下是否能够往这里的这个沙箱发送请求
> 然后这个请求是否能够被沙箱接收到是我的理解?

助手校准：当前看的 BlackboxServerClient 是发送方；BlackboxServer 是沙箱内接收并处理注册的服务。endpoint 指定接收地址，发送注册配置是为了让服务端完成注册，不是只做连通性探测；response 是处理回复。此校准尚待用户确认。

本轮关于跨 HTTP 跳转的提问：

> 有一个问题
> 我是怎么知道这里 self._post_agent_with_retry(
> 之后我就需要看这里的api rollout 呢?

助手已补充方法、路径、路由声明与挂载位置的对应依据，尚待用户反馈。

## 尚不清楚

- 请求内容、目标和回复的关系，等待本轮反馈。
- 请求到达后服务端实际做什么，下一层再展开。

<details>
<summary>来源与验证</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 请求 URL 与 headers 依据同文件 _post_agent_with_retry:330–353；本轮不进入重试策略。
- [本步过程](../../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/04-flow.md)。只核对源码，没有发送注册请求或启动服务。

</details>
