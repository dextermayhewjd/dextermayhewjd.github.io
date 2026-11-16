> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/blackbox_server/api/sessions.py/send_message.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/blackbox_server/api/sessions.py/send_message.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/blackbox_server/api/sessions.py/send_message.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/blackbox_server/api/sessions.py/send_message.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/blackbox_server/api/sessions.py/send_message.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/blackbox_server/api/sessions.py/send_message.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/blackbox_server/api/sessions.py/send_message.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# api.sessions.send_message

> Step 007 继承：来自 [Step 006 的 02-short-term-memory 记录](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/blackbox_server/api/sessions.py/send_message.md)；保留原话、来源与未知，继承不表示新增掌握。

[Step 006 阅读导航](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md#reading-navigation) → [客户端发送请求](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._post_agent_with_retry.md) → **本函数：接收题目消息** → BlackboxServer.submit_turn。

## 函数定位

- 源码：[blackbox_server/api/sessions.py:22–48](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/api/sessions.py#L22)。
- 首次单独展开：Step 006，2026-11-08。
- 最近认识更新：用户要求建立本函数卡片；当前是助手的源码说明，尚无内部机制的独立复述。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：客户端向 `/v1/sessions/{session_id}/messages` 发送 POST。FastAPI 匹配这条路由，将请求交到本函数。
2. **具体内容**：取出已有的 BlackboxServer；当前 async 分支检查 turn_id，调用 submit_turn，再把提交记录组织成 HTTP 202 回复。
3. **建议构建的心智模型**：

   > 接收本次会话的题目消息，交给服务端安排执行，先回复“已接受这次提交”。

4. **触发本函数的请求**，来自客户端 call_agent（真实调用节选）：

   ```python
   submit_response = await self._post_agent_with_retry(
       endpoint,
       f"/v1/sessions/{session_id}/messages",
       json={
           "turn_id": turn_id,
           "mode": call_mode,
           "messages": messages,
           "metadata": metadata or {},
       },
       operation="call_agent",
       trajectory_id=trajectory_id,
   )
   ```

这里跨了一次 HTTP：客户端并没有直接调用这个 Python 函数。当前 call_mode 为默认的 async。

顺序是：

1. 接收路径中的 session_id 和正文中的题目消息。
2. 把它们交给已有的 server.submit_turn，取得本次提交的记录。
3. 回复 HTTP 202。客户端之后继续查询结果，Agent 的最终回答不在这次提交回复中。

## 本场景的输入与输出：沿完整函数看交接

下面保留完整函数，只添加注释。session_id 来自 URL；request 是 HTTP 请求对象；payload 是正文解析得到的 MessageRequest，包含 mode、turn_id、messages 等字段。

```python
@router.post("/v1/sessions/{session_id}/messages")  # 匹配客户端发来的 POST。
async def send_message(session_id: str, request: Request, payload: MessageRequest):
    # 取得应用启动时已有的服务对象，不在这里新建沙箱或 Agent。
    server = request.app.state.server
    if payload.mode == "async":  # 当前默认走这个分支。
        # 异步提交需要编号，客户端后续才能查询同一次调用。
        if payload.turn_id is None:
            raise ApiError(
                400,
                "request_error",
                "turn_id is required for async submissions.",
                details={"session_id": session_id},
            )
        # 统计当前在处理的 HTTP 请求；不会在这里等待 Agent 全部执行结束。
        async with server.request_scope():
            submission = await server.submit_turn(session_id, payload)

        # 把提交记录组织成回复，保留会话、调用编号和当前状态。
        response = TurnSubmitResponse(
            request_id=request.state.request_id,  # 当前 HTTP 请求编号。
            session_id=session_id,
            instance_id=submission.instance_id,
            turn_id=submission.turn_id,
            status=submission.status,
            idempotent_replay=submission.idempotent_replay,
        )
        # 返回“已接受/已识别这次提交”，不是返回最终答案。
        return JSONResponse(status_code=202, content=response.model_dump(mode="json"))

    # sync 模式走下面的等待路径；本轮先不展开。
    # 这个 server.send_message 是服务对象方法，与当前路由函数不同。
    async with server.request_scope():
        response = await server.send_message(session_id, payload)
    response.request_id = request.state.request_id
    return response
```

### 1. 先分清 request_scope 与 submit_turn

```python
async with server.request_scope():  # 管理这个请求处理区段的进入和离开。
    submission = await server.submit_turn(session_id, payload)  # 提交 Agent 任务。
```

执行顺序是：

1. 进入 request_scope，把正在处理的请求数加一。
2. 执行里面的 submit_turn，取得提交记录。
3. 离开 request_scope，在 finally 中把请求数减一；为零时发出“已无在途请求”的信号。

request_scope 的完整实现很短，作为理解外层包装的前置保留在这里：

```python
@asynccontextmanager
async def request_scope(self) -> AsyncIterator[None]:
    async with self._request_counter_lock:  # 只保护计数变更。
        self._active_requests += 1
        self._no_inflight_requests.clear()
    try:
        yield  # 这里执行调用方 async with 块里的 submit_turn。
    finally:
        async with self._request_counter_lock:
            self._active_requests -= 1
            if self._active_requests == 0:
                self._no_inflight_requests.set()
```

计数锁没有一直包住 Agent 的执行。这个计数用于服务关闭等请求管理，不能当作正在运行的 Agent 数量。submit_turn 返回后，后台任务可以继续运行，而本次请求处理区段已经退出。

来源：[BlackboxServer.request_scope:140](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L140)。本轮只作前置解释，不扩展为完整服务关闭流程。

### 2. submit_turn 返回什么

它返回一份提交记录，说明识别了哪个 turn、当前状态是什么、是否复用了已有提交。本轮先把它视为“安排执行后给出的记录”；真正的后台执行由下层负责。

`await server.submit_turn(...)` 等待的是这个提交过程，不是等待 Claude 完整解题。首次正常提交会安排后台任务；重复提交则可能复用已有记录，状态由 submission 提供。

### 3. HTTP 202 怎样回到客户端

1. 这里构造 JSONResponse，把 TurnSubmitResponse 编码成 JSON 正文。
2. 客户端的 HTTP 调用收到 `httpx.Response`，由 `_post_agent_with_retry` 交回 call_agent 的 submit_response。
3. call_agent 解析正文，然后进入 `_poll_turn` 查询最终结果。

因此，服务端的 JSONResponse 与客户端的 httpx.Response 是同一次 HTTP 交接两端的对象；都不能在当前 async 提交阶段直接理解成 Agent 答案。

### 4. 下一处看哪里

**下一处是 [BlackboxServer.submit_turn 函数卡](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.submit_turn.md)**，先看它怎样记录并安排这次调用，再回到本函数的 submission。当前 async 路径不进入下方的 server.send_message 同步分支。

本函数负责接收、委派和回复；此处还没有展开实际启动 Claude CLI 的实现。

<details>
<summary>原话、尚不清楚与来源</summary>

## 我的直接表述（原话）

> 好的那么请构建一下这里的这个api session.send message的部分的内容吧

这是本次建卡请求，不表示已经掌握服务端执行机制。

## 尚不清楚

- submit_turn 怎样维护调用记录、处理重复提交，以及安排后台任务。
- 后台任务怎样调用 Agent，客户端又怎样查询到最终结果。
- request_scope 在优雅关闭中的完整配合，仅按请求计数用途理解。

## 来源与验证

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 路由：api/sessions.py:22–48；请求计数：core/server.py:141–152；下游提交：core/server.py:413 起；客户端衔接：client.py:117–141。
- [Step 006 本次记录](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/04-flow.md#api-send-message-card)。本轮仅静态核对，没有发送真实 HTTP 请求、运行后台 Agent 或创建额外沙箱。

</details>
