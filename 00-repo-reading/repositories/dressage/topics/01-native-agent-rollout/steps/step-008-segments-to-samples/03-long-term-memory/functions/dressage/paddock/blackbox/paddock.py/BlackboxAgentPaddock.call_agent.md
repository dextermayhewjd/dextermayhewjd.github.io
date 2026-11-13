> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.call_agent.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# BlackboxAgentPaddock.call_agent

> Step 007 继承：来自 [Step 006 的 02-short-term-memory 记录](../../../../../../../step-006-agent-execution/02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.call_agent.md)；保留原话、来源与未知，继承不表示新增掌握。

[Step 006 scope · 第 1 项](../../../../../../../step-006-agent-execution/01-scope.md#reading-navigation) → **本函数** → BlackboxServerClient.call_agent → 返回 generate。

- 源码：[paddock.py:184–201](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L184)。
- 首次单独展开：Step 006，2026-11-07。
- 最近认识更新：2026-11-08，用户已概括为取得 state 环境访问资料，再通过 client.call_agent 使用；客户端提交与等待机制仍待阅读。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 已完成注册、前置命令和 Proxy 会话登记，现在把题目消息交给 Agent。
2. **具体内容**：确定已有 state，找到对应沙箱服务的入口，把会话标识、题目消息等交给客户端，等待并返回结果。
3. **建议构建的心智模型**：

   > 把题目消息交给指定沙箱里的 Agent 服务，等待并取回调用结果。

4. **调用处**，来自 generate:259：

   ```python
   call_payload = await maybe_await(
       paddock.call_agent(
           state,
           session_id=session_id,
           messages=_chat_messages_from_prompt(sample.prompt),
           metadata={"source": "dressage", **metadata},
       )
   )
   ```

先按三个动作看：

1. 使用前一步已有的环境与会话。
2. 把 sample.prompt 整理成消息交进来；这次才提交题目内容。
3. 等待返回，把结果保存在 call_payload 中。

前一步 register_agent 交入运行配置；这一步新增的关键材料是 messages，也就是本次要交给 Agent 的题目消息。

## 本场景的输入与输出：沿完整函数看交接

下面保留完整函数，只加注释。self 是已有的 BlackboxAgentPaddock；当前调用传入 SandboxState 对象，turn_id 未显式提供。

```python
async def call_agent(
    self,
    state: SandboxState | str,
    *,
    session_id: str,
    messages: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
    turn_id: str | None = None,
) -> dict[str, Any]:
    # 取得已保存的环境访问资料，不新建环境。
    state = self._resolve_state(state)
    # 找到沙箱内 Agent 服务的入口，交给客户端发送并等待。
    return await self._client.call_agent(
        self._endpoint_for_state(state, self._leases.get(state.trajectory_id)),
        trajectory_id=state.trajectory_id,  # 找回本次环境所用的关联标识。
        session_id=session_id,             # 当前执行会话。
        messages=messages,                 # 本次题目消息。
        metadata=metadata,                 # 随调用传入的附加资料。
        turn_id=turn_id,                    # 当前未提供，交给客户端处理。
    )
```

1. **交给谁：** endpoint 指向沙箱内的 BlackboxServer，不是外部 Dressage Proxy。
2. **执行在哪里发生：** 本函数只组织交接；客户端通过服务端触发 Agent 执行。
3. **交回什么：** 返回客户端的结果字典，generate 用 call_payload 接住。本函数没有创建 Sample，也没有在这里计算奖励。

客户端默认先异步提交，再查询到最终结果。因此外层 await 不会因为收到了“任务已接受”就自动返回成功结果。具体提交与查询是下一处阅读内容。

**下一处：** [BlackboxServerClient.call_agent 函数卡](../client.py/BlackboxServerClient.call_agent.md)。看清怎样构造请求和等待；返回后沿当前 return 回到 generate:267，再进入成功结果处理。

<details>
<summary>原话、尚不清楚与来源</summary>

## 我的直接表述（原话）

> 好的那么继续吧
> 我感觉我在差不多明白了
> 那么开始step吧

这表示接续前一步并开始本步，不能当成本函数机制已理解。

2026-11-08 的表述：

> 好的 那么目前来看一下这里的这个call agent吧
> 目前是拿到了state之后
> 也就是环境访问资料然后通过client callagent来使用
> 那么目前是否需要看一下这里的client call agent呢?

助手确认这个交接关系，并补充 state 会用于解析沙箱 endpoint；题目 messages 和会话信息一起交给客户端。下一处建议看 BlackboxServerClient.call_agent 的提交与等待流程。

## 尚不清楚

- 客户端怎样提交消息、生成 turn_id 并等待最终结果。
- 服务端怎样调用已有的 ClaudeCodeAdapter，以及结果如何变成 call_payload。
- agent_response 的实际取值规则，留到返回 generate 时查看。

## 来源与验证

- 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 当前场景来自 generate:259–267；函数主体来自 paddock.py:184–201；下游边界据 client.py:97–141 核对。
- [Step 006 形成过程](../../../../../../../step-006-agent-execution/04-flow.md#start-step006)。仅静态阅读，没有实际请求或执行结果。

</details>
