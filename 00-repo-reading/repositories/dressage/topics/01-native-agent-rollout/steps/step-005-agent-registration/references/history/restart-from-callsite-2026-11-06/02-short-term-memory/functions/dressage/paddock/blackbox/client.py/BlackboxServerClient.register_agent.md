# BlackboxServerClient.register_agent

[Paddock 的注册调用](../paddock.py/BlackboxAgentPaddock.register_agent.md) → **本函数：组织并发送 HTTP 请求** → BlackboxServer；响应原路返回。

- 源码：[client.py:60–95](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L60)。
- 首次单独展开：Step 005，2026-11-06；此前只定位请求路径。
- 最近认识更新：用户明确要求先读客户端并建卡；尚无对本函数机制的直接表述。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Paddock 已从 state/lease 找到环境入口，并准备好身份、Agent 类型和配置，将它们交给本函数。
2. **具体内容**：将参数组装为 payload，按条件添加两个可选字段，通过请求辅助函数发送 POST，返回响应 JSON。
3. **建议构建的心智模型**：

   > 向已经存在的沙箱服务发送一条配置消息：“这次用哪个 Agent、属于哪个会话、模型请求发往哪里，请按这些信息准备好。”
   >
   > 1. payload 是这条消息的内容：一个 Python 字典。
   > 2. endpoint 是消息的接收地址：环境中的 BlackboxServer。
   > 3. json=payload 让 HTTP 客户端把字典作为 JSON 请求正文发送；等待后把服务端回复解析成字典返回。
   >
   > 这里发送的是配置消息，题目的 messages 在后面的 call_agent 才提交。

4. **调用代码**（Paddock.register_agent，连续摘录）：

   ```python
   return await self._client.register_agent(
       endpoint,
       trajectory_id=state.trajectory_id,
       instance_id=instance_id,
       session_id=session_id,
       router_url=router,
       blackbox_type=blackbox_type,
       backend_options=merge_backend_options(blackbox_type, backend_options),
       server_config=_server_config_for_provider(self._provider.name, blackbox_type),
       router_api_path=router_api_path,
       system_prompt_file=system_prompt_file,
       sandbox_id=state.sandbox_id,
   )
   ```

## 本场景的输入与输出

教学场景：沿用已取得 sandbox-42 的环境，endpoint.url="https://sandbox-42.example"、endpoint.headers={}；trajectory_id/session_id="run-a"、instance_id="question-1"、blackbox_type="claude_code"。router_url="http://proxy.example:8800"。backend_options 和 server_config 是上层已经准备好的字典，不在本函数重新生成。router_api_path="/v1"，system_prompt_file=None。

**发送到哪里**：POST https://sandbox-42.example/v1/rollout/register，携带 endpoint.headers。router_url 是正文中的配置，不是本次 POST 的目标。

### payload 到底是什么

客户端的局部变量不能直接被另一个进程中的服务端读取，所以要把参数装成一条网络消息。payload 只是这份待发送数据的变量名，不是函数、Agent 或环境对象。

下面只展示本场景 payload 中的三个字段，其他字段见表格及完整函数：

```python
payload = {
    "blackbox_type": "claude_code",
    "bound_session_id": "run-a",
    "router": "http://proxy.example:8800",
}
```

它表达：“为 run-a 使用 Claude Code，后续模型请求转到指定的 Proxy 地址”。整个注册消息仍发送给 sandbox-42 的 BlackboxServer，不能把正文里的 router 当成这次注册请求的目的地。

### bound_session_id 不是连接检测，也不是新生成的 ID

1. 客户端把上层传来的 session_id 原样放到 payload["bound_session_id"]，例如 "run-a"。bound 表示本次 Agent 运行配置绑定这个会话。
2. 服务端保存绑定并准备对应会话；后续提交任务时检查 session_id 是否匹配，错误编号会触发 bound_session_mismatch，而不是转给别的会话。
3. image 是创建环境时使用的镜像/模板配置；endpoint 是已运行 BlackboxServer 的服务地址。这里向 endpoint 发注册请求，不向镜像仓库发送。
4. 这是一问一答的 HTTP 注册调用，不是在这里新建一个特殊的长期双向通道；也不是前面的 GET /health 探测。成功回复说明注册处理成功，不表示 Agent 已完成题目。

依据：服务端 core/server.py 的 _validate_register_binding、_require_bound_session_match、_ensure_bound_session_initialized。本轮只回查字段用途，不展开整套会话协议。

| 输入参数 | 请求 JSON 中的字段 |
| --- | --- |
| blackbox_type | blackbox_type |
| router_url、router_api_path | router、router_api_path |
| instance_id、session_id | bound_instance_id、bound_session_id |
| backend_options、server_config | 同名字段，直接使用传入字典 |
| sandbox_id="sandbox-42" | bound_sandbox_id；仅 sandbox_id 为真值时加入 |
| system_prompt_file=None | 本例不加入；非 None 时加入同名字段 |

trajectory_id 不作为字段放进这份 payload，而是传给请求辅助函数；endpoint 用来决定 URL 和请求头。

**返回什么**：服务端响应解析后的字典。正常注册响应包含 request_id、status、binding、capabilities、config 等；本轮没有真实请求，不虚构具体返回值。Paddock 将它原样交回 generate，generate 当前只等待注册完成，不保存这个字典。

### 完整函数

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
    payload = {
        "blackbox_type": blackbox_type,
        "router": router_url,
        "router_api_path": router_api_path,
        "bound_instance_id": instance_id,
        "bound_session_id": session_id,
        "backend_options": backend_options,
        "server_config": server_config,
    }
    if sandbox_id:
        payload["bound_sandbox_id"] = sandbox_id
    if system_prompt_file is not None:
        payload["system_prompt_file"] = system_prompt_file
    response = await self._post_agent_with_retry(
        endpoint,
        "/v1/rollout/register",
        json=payload,
        operation="register_agent",
        trajectory_id=trajectory_id,
    )
    return response.json()
```

### 只看三个动作

1. **组装正文**：把本次 Agent、身份和代理配置放入 payload；有值时补入环境 ID 与系统提示文件。
2. **发送并等待**：_post_agent_with_retry 拼接 endpoint.url 与 /v1/rollout/register，携带 headers 发送请求。此处先把重试当作已提供的能力，不展开内部策略。
3. **返回回复**：response.json() 交回注册响应。这里没有构造题目的 messages，也不执行 provider.create。

**下一处候选**：服务端入口为 blackbox_server/api/rollout.py 的 register_rollout，再委托 core/server.py 的 BlackboxServer.register。要看“请求收到后到底做什么”，从服务端首次注册的正常路径进入；本轮只把交接定位清楚。

## 我的直接表述（原话）

> 好的 那么简单看一下这里的这个函数吧
> 创建关于这个函数的函数卡片吧

这是阅读与建卡授权。随后用户追问：

> 你能简单告诉我这里到底有什么我必须要知道的内容吗?
> 我也不是特别懂这里的payload又是什么呢?
> 这里是在做什么我是真的没有看清楚
> 心智模型应该是什么呢?

助手改从跨进程传递参数的具体消息解释 payload、endpoint 和 response；用户仍未确认理解。

本轮对通信和绑定字段的提问：

> 这里我可以理解为
> 这里是一种类似于双向通道的东西吗?
> 因为这里的image在构建的过程
> 应该是有类似于image在哪里这个抽象的对吗?
> 那么这里的这个boud session id我是真的不是特别理解
>
> 这里是为了检测看一下这个发向agent的这个这个请求是否能够成功?

助手已区分请求/回复、镜像与运行服务地址，以及会话绑定与健康探测；尚待用户理解反馈。

## 尚不清楚

- 服务端怎样配置、初始化具体 Agent，是下一处阅读问题。
- 客户端重试、超时与异常分类的细节，本轮不展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- client.py:60–95；请求拼接与 headers 见 _post_agent_with_retry:330–353；服务端路由见 api/rollout.py:18–25，响应字段见 core/models.py 的 RegisterResponse。
- [本步过程](../../../../../../../../../04-flow.md)。所有域名、ID 是教学示意，未发起请求或运行 Agent。

</details>
