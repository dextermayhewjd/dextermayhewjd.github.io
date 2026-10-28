# AnthropicAdapter._register_routes

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../../step-010-generate-and-rm/03-long-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._register_routes.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 02-short-term-memory 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._register_routes.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 源码定位：[anthropic.py:48–50](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L48-L50)。
- 首次接触：Step 009 范围定位；2026-10-25 沿请求入口集中回看。
- 最近认识更新：2026-10-25，用户转贴并明确认可“类构造 → 基类初始化 → 子类路由登记”的解释，表示这条链已经理清；这是对现有解释的认可，不记为独立复述或全部路由机制掌握。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：创建 AnthropicAdapter 时，继承的 `BaseAdapter.__init__` 已建立 HTTP 应用，现在调用本方法登记协议路由。
2. **具体内容**：给 `app` 登记两条 POST 路径及其处理函数，返回 `None`；请求实际到达后，由 aiohttp 调用对应处理器。
3. **建议构建的心智模型**：

   > 给 HTTP 应用登记“请求方法 + 路径 → 处理函数”的对应关系。

4. **调用代码**：从 [generate.py:187–195](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L187-L195) 的类构造调用进入；当前场景 `agent_name="claude_code"`：

   ```python
   # _AdapterService.endpoint，构造参数在这里省略
   _, adapter_cls = _AGENTS[agent_name]  # 得到 AnthropicAdapter
   adapter = adapter_cls(...)          # 在这句内部完成初始化与路由登记
   ```

   `AnthropicAdapter` 没有自己的 `__init__`，因此复用 `BaseAdapter.__init__`。执行基类中的代码时，`self` 仍是正在创建的 AnthropicAdapter 实例。基类先创建 `self.app`，再在 `240` 行调用：

   ```python
   self._register_routes(self.app)
   ```

   这个方法按 `self` 的实际类型找到 `AnthropicAdapter._register_routes`，进入下方的两行登记代码。完成后返回构造调用；`generate.py:200` 才继续执行 `run_app_in_thread(adapter.app, ...)`。

登记好的 `app` 怎样与监听服务连接，以及请求到达后怎样找到处理器，集中见 [HTTP 请求分派说明](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/references/http-request-dispatch.md)。该页以 Codex 路径举例；本卡保留 Anthropic 的两条路由。

## 本场景的输入与输出

**输入**：当前 AnthropicAdapter 对象与它已经创建的 `app`。以下为方法完整主体：

```python
app.router.add_post("/v1/messages", self._run_turn)
app.router.add_post("/v1/messages/count_tokens", _count_tokens)
```

**输出**：函数返回 `None`；`app` 中增加以下路由。这里只核对静态登记关系，没有启动真实服务。

| 请求方法与路径 | 对应处理函数 |
| --- | --- |
| `POST /v1/messages` | `self._run_turn`，继承自 BaseAdapter |
| `POST /v1/messages/count_tokens` | `_count_tokens` |

本步只沿第一条请求路径。`self._run_turn` 在这里作为处理函数传入；等 Claude Code 请求 `<adapter_url>/v1/messages`，aiohttp 才将请求交给它。随后 `_run_turn:394` 的 `await request.json()` 读取正文，接回[已读模型处理卡片](../../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)。

**发送端怎样确定路径**：Harness 将基础地址放入 `ANTHROPIC_BASE_URL`，Claude Code 的 Messages 客户端按接口约定发送请求；本函数负责登记接收规则。当前 Codex 配对使用另一条 `/v1/responses` 路径，见[归档中保留的发送端与完整 URL](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/references/archive/scope-v1.md#client-request-target)。这里没有展开外部 CLI 的内部 HTTP 调用。

## 我的直接表述（原话）

2026-10-25，当前问题：

> 也就是说这里在init的时候有一个adapter
> 还有这里的url
> 但是这里是否还需要看一下这里的add router呢?

这段表述确定了希望补清的交接；路由登记和后续调用的区别尚待反馈。

2026-10-25，进一步提出发送端缺口：

> 但是也有一个问题cli部分发来的请求都是/v1/messages吗?
> 这是在哪里调用的呢?
> 我知道他会发请求
> 也就是从codex或者claude中发送的请求
> 但是到底发到哪一个网络请求的部分这里是否需要单独说清楚呢?

2026-10-25，用户对前一轮说明反馈大概明白后，回查构造入口：

> 好的我大概明白了
> 那么下一个问题 变成了
> 这里的的adapter init的时候是在哪里register了这个部分
> 因为我目前完全没有在generate中看出来这个register的部分是在哪一个部分被写上去的这件事情

随后用户转贴前轮解释并明确认可：

> 好的那么这样子我算是理清楚了
>
> 我觉得这里讲述的十分正确和详细

所认可的完整解释与关于 scope、教学顺序的追问保存在[本轮确认记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/04-flow.md#constructor-explanation-approved-and-scope-plan)。

## 尚不清楚

- aiohttp 的内部匹配实现和 `_count_tokens` 暂不展开。
- 外部 CLI 的具体 HTTP 发送函数尚未追踪；当前补充基于 Slime 的启动配置、接收路由与官方接口约定。

<details>
<summary>来源与验证边界</summary>

- 源码绑定 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[调用位置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L238-L240)与[请求正文读取](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L387-L395)。
- [本轮问题与说明](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/04-flow.md#route-registration-reading)；[本步面包屑](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/01-scope.md#breadcrumb-adapter-entry)。
- [发送端路径澄清](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/04-flow.md#client-request-url-origin)保留 Claude/Codex 的版本边界与官方文档依据。
- 静态源码核对，没有发起真实 HTTP 请求或运行 CLI、模型服务。

</details>
