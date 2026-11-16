# RolloutLLMProxy._build_app 内的 _proxy

- 源码：[rollout_llm_proxy.py:403–408](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/proxy/rollout_llm_proxy.py#L403)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次展开：Step 006 的公共 Proxy 补读，2026-11-14；原首轮历史保留。
- 最近认识更新：用户确认从 CLI 进程接到 Proxy；具体 HTTP 接收与委派尚待反馈。

[_run_claude_turn 启动 CLI](../../adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#model-request-during-cli) → 外部 CLI 发 HTTP 请求 ⇒ **当前 _proxy 接收** → [RolloutLLMProxy._handle_proxy](RolloutLLMProxy._handle_proxy.md#handle-proxy-map)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Claude CLI 按 ANTHROPIC_BASE_URL 请求已启动的本地 Proxy；本轮是 Topic 01 原生路线，不经过 Harbor 集成的 Gateway。
2. **具体内容**：FastAPI 根据路由找到这个接收函数，把请求和路径交给 _handle_proxy，再交回它产生的响应。
3. **建议构建的心智模型**：

   > 这是模型 HTTP 请求的入口，真正处理委派给 _handle_proxy。

4. **调用背景**：CLI 在外部进程中发请求，Web 框架调用这个路由函数；不是 _run_claude_turn 在 Python 中直接调用它。

## 本场景的输入与输出

例如 CLI 发出 `POST /v1/messages`，`request` 是这次 HTTP 请求对象，`path` 为 `v1/messages`。这里返回下游生成的 Response（也可能是 StreamingResponse），由 Web 框架经原 HTTP 请求返回 CLI。

<a id="proxy-http-entry"></a>

完整路由与处理函数：

```python
@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
async def _proxy(request: Request, path: str) -> Response:
    return await self._handle_proxy(request, path)
```

`_proxy` 定义在 _build_app 内，沿用该 Proxy 实例的 self；它只委派，不在这两行里完成协议转换或模型生成。下一处是 [_handle_proxy 函数卡](RolloutLLMProxy._handle_proxy.md#handle-proxy-map)，先从协议识别与请求转换读起。

响应先回到 CLI，CLI 可以继续工作；整次进程退出后，才回到 [_run_claude_turn 的结果整理](../../adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#return-result)。

## 我的直接表述（原话）

> 好的 那么就是这个create了这个subprocess exec之后的这个process对吧
> 也就是还有一个进程是需要我来理解一下到底是在做什么的
> 或者这个subporcess exec就是这个部分?
> 所以我们需要考虑一下开始看一下这里的这个rollout llm proxy的部分了?
> 这里没有gateway这类的东西对吗?
> 就是直接进入了rolloutllmproxy 了?

助手校准：create_subprocess_exec 已启动 Claude CLI，process 是 Python 管理该子进程的对象；原生路线直接请求本地 RolloutLLMProxy，Harbor Gateway 不在本次路径中。

## 尚不清楚

- _handle_proxy 怎样识别 Claude 请求、选择上游并处理响应，下一函数继续。
- Claude CLI 内部的具体 HTTP 客户端实现不在当前仓库，本轮保持外部程序边界。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对 _build_app 中路由定义和 _proxy；原生 Adapter 的 build_env:211 设置本地 ANTHROPIC_BASE_URL，_run_claude_turn:556 启动 CLI。
- Step 005 的 _start_proxy:609–648 已提供本地 Proxy 启动位置；此时只是消费已有服务，不再次启动它。
- Harbor 集成也复用此代理类，但本轮使用原生调用场景，不把两条部署路径混成同一条。
- 未启动进程或发送请求。[补读过程](../../../../../04-flow.md#native-proxy-http-entry)。

</details>
