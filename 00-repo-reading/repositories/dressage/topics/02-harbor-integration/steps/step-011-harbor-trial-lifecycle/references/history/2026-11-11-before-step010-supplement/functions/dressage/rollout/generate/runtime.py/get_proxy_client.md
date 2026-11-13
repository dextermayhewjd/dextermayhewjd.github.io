> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/rollout/generate/runtime.py/get_proxy_client.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/rollout/generate/runtime.py/get_proxy_client.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/rollout/generate/runtime.py/get_proxy_client.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/rollout/generate/runtime.py/get_proxy_client.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# get_proxy_client

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/03-long-term-memory/functions/dressage/rollout/generate/runtime.py/get_proxy_client.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/03-long-term-memory/functions/dressage/rollout/generate/runtime.py/get_proxy_client.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

- 源码定位：[runtime.py:43](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L43)。
- 首次单独展开：Step 002，2026-11-06；此前仅在 generate 主线定位。
- 最近认识更新：Step 002，2026-11-06；用户提出每个 Paddock 的代理与会话登记理解，助手补充边界。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 完成任务身份与配置准备后，取得后续会话操作和轨迹读取所需的客户端。
2. **具体内容**：先检查模块缓存；没有客户端时，按需导入 ProxyClient，使用 proxy_url() 创建并缓存；已有则直接返回。
3. **建议构建的心智模型**：

   > 拿到一个访问 Dressage Proxy 的客户端。第一次创建，之后复用同一进程内此模块缓存的对象；这里不启动 Proxy 服务，也不发送请求。

4. **调用代码**（generate:182；参数准备已完成）：

   ```python
   proxy_client = get_proxy_client()
   ```

## 本场景的输入与输出

本函数没有显式参数，依赖模块缓存与地址配置。教学场景：_PROXY_CLIENT=None，ProxyClient=None，DRESSAGE_PROXY_URL="http://127.0.0.1:8000"。该地址仅为示意，不表示本机存在服务。

输出：一个 ProxyClient 对象，同时存入 _PROXY_CLIENT；类名保存在模块变量 ProxyClient。再次调用时，若缓存未重置，返回同一对象。不是每个 session_id 各创建一个客户端；多个进程各有自己的模块状态。

完整函数：

```python
def get_proxy_client() -> ProxyClientType:
    global _PROXY_CLIENT, ProxyClient
    if _PROXY_CLIENT is None:
        if ProxyClient is None:
            from dressage.proxy.proxy_client import ProxyClient as ProxyClientClass

            ProxyClient = ProxyClientClass

        _PROXY_CLIENT = ProxyClient(proxy_url())
    return _PROXY_CLIENT

```

1. **先查对象缓存**：_PROXY_CLIENT 初始为 None。已有对象时跳过整个创建分支。
2. **需要时取得类**：ProxyClient 初始是可注入的模块变量；为 None 时才导入真实类并保存。类与客户端对象是两项不同的缓存。
3. **创建客户端**：proxy_url() 优先取 DRESSAGE_PROXY_URL；否则用 PROXY_PUBLIC_HOST 或 master_addr()，配合 proxy_port() 组装地址。ProxyClient 构造过程保存地址并创建 httpx.AsyncClient，没有在此发出 HTTP 请求。
4. **返回给 generate**：局部变量 proxy_client 接住同一个对象，稍后用于会话登记、收尾、读取轨迹等操作。下一处是 claim_prewarm(session_id)，它不是该客户端的方法，两项操作分别取得服务访问工具与预热结果。

与上一阶段区分：backend_options["proxy"] 是模型请求代理的配置字典；这里得到的是访问 Dressage Proxy 服务的客户端对象。

### 客户端在整条流程里做什么

1. Dressage Proxy 服务处在模型请求链上，提供模型请求转发和轨迹收集等能力。
2. 当前 proxy_client 是 generate 访问该服务的 HTTP 客户端。在本路径中，它用于 register_session_context、finalize_session、read_trajectory 等会话与轨迹操作；轨迹来自服务端，不是客户端自己通过拿到对象就自动收集。
3. Agent 运行时的模型请求经 BlackboxServer 一侧的模型请求代理发往 Dressage Proxy；不能把该通路理解为每次都调用这里的局部 proxy_client 变量。
4. 紧随其后的 claim_prewarm 使用预热 store，独立于此 HTTP 客户端。客户端管理会话/取轨迹，handle 则交接预热环境资料。

### 补充：客户端、代理服务与会话登记

1. get_proxy_client 创建或复用的是 generate 一侧的出站 HTTP 客户端，不监听接收 Claude/Codex 请求的端口，也不是为每个 Paddock 创建一个代理。
2. Agent 发出的模型请求走 BlackboxServer 的模型请求代理，再到 Dressage Proxy。这里的客户端让 generate 访问 Dressage Proxy 的会话与轨迹接口。
3. register_session_context(session_id) 的请求正文只有会话编号，不上传对话 messages。当前版本服务端把它交给 engine_rebalancer：功能启用时，在 sessions 中为该编号建立 SessionRoutingState；未启用则不执行登记。
4. 因此这里的 context 是服务端的会话路由状态，不是完整聊天上下文。它放在 Dressage Proxy，是因为推理请求路由由该服务管理；后续实际消息随模型请求传入。路由和缓存调度的内部算法不在本步展开。

依据：proxy_client.py:95–105；proxy/server.py:2896–2904；proxy/rebalancing/scheduler.py:1999–2007。此调用位于 generate 后续注册阶段，不发生在 get_proxy_client 创建对象时。

## 我的直接表述（原话）

> 好的那么开始下一个step吧

上述为开启本步的授权。后续用户表述：

> 简单来说就是给这里的每一个paddock山一个proxy 让这里client端口能够接收这里的claude和codex传输出来的请求是我的理解
> 这是在这里的porxy_client 这里完成了初始化
> 但是为什么这里的上下文是在这里的dressage proxy这里完成登记上下文的我其实没有特别理解
> 不过继续吧
> 看一下下一个部分的内容吧

助手已在上方区分客户端与服务端、路由状态与聊天内容，尚未得到用户对校准内容的理解确认。

## 尚不清楚

- 客户端后续请求的具体协议与连接管理，本轮不展开。
- Proxy 服务在哪里启动，本函数不能回答。
- claim_prewarm 的交接已在本步对应卡片展开，尚待用户反馈。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本轮核对 HEAD 与源码干净工作区。
- runtime.py 的模块变量和 get_proxy_client；proxy/proxy_client.py:13 起的构造方法；config/config.py:69 起的 proxy_url。
- 静态源码核对，没有发出网络请求或启动服务。
- [本步过程](../../../../../../../../../../../01-native-agent-rollout/steps/step-002-proxy-client-and-prewarm-claim/04-flow.md)。

</details>
