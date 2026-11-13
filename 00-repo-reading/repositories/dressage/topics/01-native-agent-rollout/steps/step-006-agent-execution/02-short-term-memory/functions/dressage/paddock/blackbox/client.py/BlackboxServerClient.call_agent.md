# BlackboxServerClient.call_agent

[Step 006 阅读导航](../../../../../../01-scope.md#reading-navigation) → [Paddock.call_agent](../paddock.py/BlackboxAgentPaddock.call_agent.md) → **本函数：提交并等待 Agent 调用** → 返回 Paddock，再回到 generate。

## 函数定位

- 源码：[client.py:97–141](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L97)。
- 首次单独展开：Step 006，2026-11-08。
- 最近认识更新：2026-11-08，用户已概括为向沙箱发送题目信息，并追问沙箱内如何执行；提交与最终完成的细节仍按下文保留。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Paddock 已找到沙箱服务的 endpoint，把题目 messages、会话 ID 和附加资料交给这个客户端。
2. **具体内容**：准备本次调用的 turn_id，提交消息；默认 async 模式下继续等待服务端执行完成，再返回结果字典。
3. **建议构建的心智模型**：

   > 给这次 Agent 调用一个编号，把题目发送到沙箱服务，等待最终结果后返回。

4. **调用处**，来自 Paddock.call_agent：

   ```python
   return await self._client.call_agent(
       self._endpoint_for_state(state, self._leases.get(state.trajectory_id)),
       trajectory_id=state.trajectory_id,
       session_id=session_id,
       messages=messages,
       metadata=metadata,
       turn_id=turn_id,
   )
   ```

先按三个动作看：

1. 准备 turn_id，标识这一次提交；已有编号就沿用，没有才生成。
2. 将消息提交到该 session 的 messages 接口。
3. 等待最终结果，交回 Paddock，再由 generate 的 call_payload 接住。

## 本场景的输入与输出：沿完整函数看提交和等待

本轮沿用 Claude Code 已注册的正常场景：endpoint 指向沙箱内 BlackboxServer，messages 来自题目，turn_id 未显式提供，环境变量未覆盖默认的 async 模式。这里的 self 是 BlackboxServerClient，不是 Paddock。

以下保留完整函数，只添加中文注释；输入怎样使用、结果怎样返回直接放在对应语句旁。

```python
async def call_agent(
    self,
    endpoint: SandboxEndpoint,
    *,
    trajectory_id: str,
    session_id: str,
    messages: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
    turn_id: str | None = None,
) -> dict[str, Any]:
    """Submit an agent turn asynchronously and poll until it settles.

    A stable ``turn_id`` is generated once (when the caller does not supply
    one) and reused across the whole submit retry cycle, making the submit
    POST idempotent: a retried submit re-attaches to the same server-side
    turn instead of starting a second execution.
    """
    # [1] 为这次提交准备编号；下面的提交重试继续使用同一个编号。
    if turn_id is None:
        turn_id = f"turn-{uuid4().hex}"
    call_mode = self._resolve_call_mode()  # 当前默认得到 "async"。

    # [2] 向沙箱内 BlackboxServer 提交题目消息。
    submit_response = await self._post_agent_with_retry(
        endpoint,
        f"/v1/sessions/{session_id}/messages",
        json={
            "turn_id": turn_id,            # 本次 Agent 调用的编号。
            "mode": call_mode,            # 决定提交后怎样等待结果。
            "messages": messages,         # 真正提交的题目消息。
            "metadata": metadata or {},
        },
        operation="call_agent",           # 提供给请求辅助层的操作名称。
        trajectory_id=trajectory_id,
    )
    if call_mode == "sync":
        # sync 模式：服务端让这次 HTTP 请求等待到执行结束。
        # 当前选择的 async 路径不进入这个分支。
        return submit_response.json()

    # [3] async 模式：提交回复不是最终答案，还要查询这次调用的结果。
    submit_data = submit_response.json()
    idempotent_replay = bool(submit_data.get("idempotent_replay", False))
    return await self._poll_turn(
        endpoint,
        trajectory_id=trajectory_id,
        session_id=session_id,
        turn_id=turn_id,                    # 查询同一个会话下的同一次调用。
        idempotent_replay=idempotent_replay,
    )  # 等到最终结果后，才将字典交回上层；失败可能抛异常。
```

### 1. turn_id 标识哪件事

session_id 对应已有会话，turn_id 对应该会话中这一次提交的 Agent 调用。一次 Agent 调用内部可能多次请求模型，不能把 turn_id 直接理解为每次模型推理请求的编号。

同一次提交的重试保留相同 turn_id，供服务端识别重复请求。重新调用本函数且仍未提供 turn_id，则会生成新的编号；它不是全局自动识别所有重复任务的机制。

### 2. 提交回复和最终结果有什么区别

1. 默认 async 模式下，服务端返回 HTTP 202，表示它接受了这次提交；Agent 可能还在运行。
2. [_poll_turn](BlackboxServerClient._poll_turn.md) 继续按 session_id 与 turn_id 查询。未完成时等待，成功提交结果时返回字典，终止失败状态则报错。
3. Paddock 原样返回这个字典，generate 将它保存为 call_payload；不是把最初的 202 回复当作答案。

**从服务端后台链读回来时，接在 submit_data = submit_response.json()。** _post_agent_with_retry 收到提交的 HTTP 响应就返回；后台 _run_turn 的完成不是它的等待条件。此前深入服务端是为了理解结果怎样产生，读完后切回本函数，再进入 _poll_turn 看结果怎样被领取。

因此，这里的 **async 不表示调用方发出任务就立即结束**。外层仍然在 await 本函数，等待的是最终调用结果。

正常返回字典中可以包含 outputs、backend、usage、会话与调用标识等字段，具体由下层结果构造。它还不是奖励或训练 Sample；如何从中得到 agent_response 属于返回 generate 后的下一段。

### 3. 接下来从哪里继续

| 位置 | 先读什么、在哪里停 |
| --- | --- |
| [_post_agent_with_retry 函数卡](BlackboxServerClient._post_agent_with_retry.md) | 当前先进入这一直接调用：对齐 messages 路径、正文及 HTTP 响应，再找服务端接收路由 |
| [api.sessions.send_message 函数卡](../../../../blackbox_server/api/sessions.py/send_message.md) | 想看服务端为何返回 202 时，进入匹配路由，定位 submit_turn 即可 |
| [_poll_turn 函数卡](BlackboxServerClient._poll_turn.md) | 已沿服务端执行链返回，本轮从这里看查询、等待与状态判断；完成后返回本函数 |
| [返回 Paddock.call_agent](../paddock.py/BlackboxAgentPaddock.call_agent.md) | 沿 return 返回 generate:267，继续成功结果处理 |

当前先读清本函数的三个动作，不提前为表中所有下游函数建卡。

<details>
<summary>原话、尚不清楚与来源</summary>

## 我的直接表述（原话）

> 好的那么现在生成一下这个blackboxserver client call agent部分的short term memory吧

这是建立卡片的请求，不代表内部机制已掌握。此前对 Paddock 的理解保留在上层卡片。

后续表述：

> 好的 我差不多了理解了
> 这里就是向这里的这个沙箱发送题目星系
> 但是沙箱本省是怎么执行的呢?
> 这里我需要看什么呢?

助手将“题目星系”按上下文理解为题目信息。下一处沿请求路径定位 api.sessions.send_message，再由 submit_turn 安排服务端后台执行；实际 CLI 进程由具体 Agent 适配器启动。当前只给出方向，没有把服务端内部登记为已读。

## 尚不清楚

- 服务端怎样识别同一个 turn_id，如何启动后台 Agent 执行。
- `_poll_turn` 怎样区分运行中、成功与失败，如何处理超时。
- call_payload 的具体字段怎样形成后续 agent_response。

## 来源与验证

- 固定源码：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 本函数：client.py:97–141；默认模式：同文件的 _DEFAULT_CALL_MODE；最终字典：_poll_turn / _committed_call_payload；202 回复：api/sessions.py 的 send_message。
- [Step 006 本次记录](../../../../../../04-flow.md#client-call-agent-card)。本次仅核对源码和卡片，没有实际提交题目、轮询服务或运行 Agent。

</details>
