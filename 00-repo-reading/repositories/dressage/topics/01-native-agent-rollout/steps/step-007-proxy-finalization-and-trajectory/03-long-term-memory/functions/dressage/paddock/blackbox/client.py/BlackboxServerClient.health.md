# BlackboxServerClient.health

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../step-006-agent-execution/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.health.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../step-005-agent-registration/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.health.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

[Step 004（原 001） · 2.3](../../../../../../../step-004-paddock-environment-preparation/01-scope.md#reading-navigation) → [init 健康检查处](../paddock.py/BlackboxAgentPaddock.init.md#normalize-and-health) → **health** → 返回 init 构造 state。

- 源码：[dressage/paddock/blackbox/client.py:49–58](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L49)。
- 首次接触：Step 001，从 init 的可选健康检查调用进入。
- 最近认识更新：2026-11-05，用户将其初步理解为“访问后再构造 state”，要求简短记录；等待、HTTP 检查和失败去向由助手补充。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：init 已取得 endpoint，且 _wait_health=True。
2. **具体内容**：带请求头访问该服务的 /health，等待响应，检查 HTTP 状态，返回响应内容。
3. **建议构建的心智模型**：

   > 对已知的服务入口做一次 HTTP 健康请求。正常结束后 init 才继续构造 state；失败则抛异常，交给 init 清理已取得的环境。

4. **调用代码**，位于 Paddock.init：

   ```python
   if self._wait_health:
       await self._client.health(endpoint)
   ```

   调用方的 self._client 是 BlackboxServerClient；下面函数内部的 self._client 是它持有的 httpx.AsyncClient。

## 本场景的输入与输出

| 内容 | 本场景含义 |
| --- | --- |
| 输入 endpoint | 已有的服务 URL 和 headers；不是创建沙箱的请求 |
| 请求 | GET 到 endpoint.url 去掉尾部斜杠后的 /health 路径，携带 endpoint.headers |
| 正常返回 | 响应解析后的 JSON；不能解析为 JSON 时返回文字摘要字典。init 不使用返回内容，只等待调用正常结束 |
| 失败 | 网络或 HTTP 错误向外抛出；init 不继续正常构造 state，而是进入异常清理 |

完整短函数：

```python
async def health(self, endpoint: SandboxEndpoint) -> dict[str, Any]:
    response = await self._client.get(
        f"{endpoint.url.rstrip('/')}/health",
        headers=endpoint.headers,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"ok": True, "text": response.text}
```

1. await 等待请求完成，不是只发出请求就继续。
2. raise_for_status 检查 HTTP 状态；代码没有额外校验 JSON 中的 ok 等业务字段，也没有轮询重试。
3. 成功后回到 [init 的 state 构造段](../paddock.py/BlackboxAgentPaddock.init.md#return-state)。_wait_health=False 时，调用方直接跳过本方法。

## 我的直接表述（原话）

用户先问（节选）：

> 还是只需要记住
> 这里会发送一个访问?
> 然后然后再构造这个state

随后要求：

> 那么简单把这个放在一个short term memory里面吧

完整过程见[本步记录](../../../../../../../step-004-paddock-environment-preparation/04-flow.md#health-short-memory)；不把建卡请求记为全部机制已掌握。

## 尚不清楚

- 用户对“等待成功才继续、失败进入清理”的理解待反馈；服务端 /health 的业务判定及 HTTP 客户端内部不在本轮展开。

<details>
<summary>来源与验证范围</summary>

- 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；调用及异常处理位于 paddock/blackbox/paddock.py:114–147。
- 仅静态核对，没有发出实际 HTTP 请求。健康请求成功不代表完整 Agent 任务或训练流程已经验证。

</details>
