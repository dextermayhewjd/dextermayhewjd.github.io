> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# ClaudeCodeAdapter.send_message

> Step 007 继承：来自 [Step 006 的 02-short-term-memory 记录](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md)；保留原话、来源与未知，继承不表示新增掌握。

[Step 006 scope](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md#reading-navigation) → [BlackboxServer._run_turn](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md) → **本函数：组织一次 Claude 调用** → _run_claude_turn → 返回 AdapterResponse。

## 函数定位

- 源码：[claude_code.py:323–410](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L323)。
- 首次单独展开：Step 006，2026-11-08。
- 最近认识更新：2026-11-08，用户已概括为确定对话、把要执行的内容交给 Claude、等待结果；助手补充新建/续接会话及本次 CLI 运行的返回边界。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：服务端后台 _run_turn 已经拿到题目，将本次调用交给注册时选中的 ClaudeCodeAdapter。
2. **具体内容**：取出用户消息，确定新建还是续接 Claude 会话，标记代理请求归属，组织 CLI 运行并返回整理好的结果。
3. **建议构建的心智模型**：

   > 确定新建还是续接 Claude 会话，把题目交给已经准备好的 Claude CLI，等待本次运行完成，整理结果后交回服务端。

4. **调用处**，来自 BlackboxServer._run_turn：

   ```python
   adapter_response = await self._wait_for_backend_call_excluding_pause(
       self._adapter.send_message(session, turn_context, request.messages),
       timeout=self._effective_config.backend_timeout,
   )
   ```

此处 _run_turn 的 self 是 BlackboxServer；下面函数内的 self 是 ClaudeCodeAdapter。这里的 send_message 也不是前面接收 HTTP 的 api.sessions.send_message 路由函数。

### 为什么会进入 claude_code.py

1. Step 005 注册时，BlackboxServer.register 调用 `create_adapter(request.blackbox_type)`。当前示例选择 claude_code，工厂返回 ClaudeCodeAdapter 实例。
2. register 执行 `self._adapter = adapter`，把这个实例保存在 BlackboxServer 对象上，并调用它的 initialize。
3. 现在 BlackboxServer._run_turn 调用 `self._adapter.send_message(...)`，因此进入这个实例所属类的 ClaudeCodeAdapter.send_message，源码就在 claude_code.py。
4. 进入本函数后，self 已是 ClaudeCodeAdapter；继续调用 `self._run_claude_turn(...)`，仍在同一个适配器对象中。

这里没有重新选择 Agent，也不是按文件名自动跳转。若注册时选择 codex，工厂会返回 CodexAdapter，同一处 self._adapter.send_message 就会进入 Codex 的实现。

来源：[create_adapter](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/factory.py#L15) · [注册时保存适配器](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L301)。

## 本场景的输入与输出：按四个动作阅读

输入是已有会话资料、这次 turn 的资料和题目消息。当前正常路径只允许一条非空的 user 消息。正常输出是 AdapterResponse；它会交给 _run_turn 写入调用记录，不是直接返回 Slime Sample。

下面是原函数的正常路径节选。检查与失败分支的完整源码保留在文末；各片段不能当作彼此独立的完整函数运行。

### 1. 取出这次题目

```python
message = new_messages[0]  # 此前已检查只有一条消息。
# 随后检查 message.role 是 user，message.content 非空。
```

本次真正交给 CLI 的题目文本是 message.content。健康、消息数量和格式检查先按入口条件理解，不要求逐个进入辅助函数。

### 2. 准备 Claude 会话和本次请求归属

```python
had_backend_session = session_context.backend_session_id is not None
backend_session_id = (
    session_context.backend_session_id or self._stable_backend_session_id()
)
session_state = ClaudeCodeSessionState(
    backend_session_id=backend_session_id,
    resume=had_backend_session,  # 有已有 Claude 会话则准备续接。
)

if self._proxy is not None:
    await self._proxy.open_turn(
        turn_context.turn_id, backend_session_id=backend_session_id
    )
```

1. backend_session_id 用于 Claude 后端会话；不把它与外部 session_id、当前 turn_id 当作同一字段。
2. resume 表明本次是否续接已有 Claude 会话。
3. self._proxy 是 initialize 时已经准备的本地 RolloutLLMProxy。open_turn 标记当前调用归属，不是在这里重新启动外部 Dressage Proxy。

<a id="receive-cli-result"></a>

### 3. 启动并等待本次 CLI 运行——当前回看结果接收处

这里的阅读分界在第 3 段内部，按我们实际走过的路径理解：

1. 此前先整体说明 send_message 的各段职责；第 1、2 段负责取题目和准备会话，并不表示其中每个辅助函数都已深入阅读。
2. 随后从第 3 段上半部分的 self._run_claude_turn 调用进入子函数，展开了 CLI 启动、stdout 收集和结果返回。
3. 现在回到第 3 段下半部分：正常路径中，等待器将 Task 的结果交给 outputs、trace_events、usage，再继续第 4 段。

```python
# 此前的下钻位置：进入 _run_claude_turn，阅读 CLI 怎样运行。
task = asyncio.create_task(
    self._run_claude_turn(
        user_text=message.content,
        turn_context=turn_context,
        session_state=session_state,
    )
)

# 当前回到这一行：等待 Task，并在正常路径中接住三项结果。
# 等待器还处理代理报告的步数限制；本轮先不进入其内部。
outputs, trace_events, usage = await self._await_backend_task_or_proxy_max_steps(
    task,
    session_context=session_context,
    proxy=self._proxy,
)
```

当前只需对上“下层返回三项结果 → 这一行接住 → 第 4 段使用”。无需为了读这一行重新展开等待器的内部实现。上面的先后是阅读顺序；实际运行时，Task 的执行与这里的等待是配合进行的。

<a id="finish-and-return"></a>

### 4. 等代理请求收尾，返回结果并清除本次绑定

上一段 await 正常返回后，outputs、trace_events、usage 已经取得。现在继续同一个 send_message，先看下面 drain_turn 的用途，再看这三项结果怎样放进 AdapterResponse；本轮先不进入代理与等待器的内部实现。

```python
if self._proxy is not None:
    await self._proxy.drain_turn(
        timeout=self._remaining_timeout(
                deadline, operation="wait for rollout proxy drain"
        )
    )
    await self._raise_if_proxy_context_overflow()
    await self._raise_if_proxy_rollout_invalidated()

session_context.backend_session_id = backend_session_id
success = True
return AdapterResponse(
    outputs=outputs,
    trace_events=trace_events,
    usage=usage,
    backend_session_id=backend_session_id,
)
```

1. drain_turn 等待本次在途代理请求收尾，并检查代理报告的失败。
2. 保存 Claude 会话编号，供后续调用续接。
3. 返回 outputs、trace_events、usage 与后端会话编号，交给 _run_turn 保存。
4. return 真正交回之前仍会执行 finally：再次处理代理请求收尾，随后 clear_turn 清除本次代理绑定。不是在这里销毁整个沙箱。

这些 CLI 输出整理结果，与之后从 Dressage Proxy 读取的训练轨迹不是同一份返回值；此处不继续展开训练数据转换。

## 接下来只需要看哪里

**当前从 [_run_claude_turn](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md) 返回本函数第 3 段，再接第 4 段。**

1. 接住 outputs、trace_events、usage。
2. 等待本次代理请求收尾，检查失败，保存后端会话编号。
3. 组成 AdapterResponse；finally 完成代理收尾并清除当前 turn 绑定后，才真正交回 [BlackboxServer._run_turn](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md)。

读完这里，再回到 _run_turn 看结果怎样保存。客户端 _poll_turn 放在这条返回路径之后阅读；已经生成其卡片不代表这段交接可以省略。后端会话 ID 算法、两个等待器与代理内部实现继续按需回查。

<details>
<summary>完整源码（固定版本，未裁剪）</summary>

```python
async def send_message(
    self,
    session_context: SessionContext,
    turn_context: TurnContext,
    new_messages: list[Message],
) -> AdapterResponse:
    deadline = asyncio.get_running_loop().time() + turn_context.deadline_seconds
    if not await self.health():
        raise BackendProcessError("claude_code backend is not healthy.")
    if len(new_messages) != 1:
        raise BackendProtocolError(
            "claude_code adapter expects exactly one input message."
        )
    message = new_messages[0]
    if message.role != "user":
        raise BackendProtocolError(
            "claude_code adapter only accepts a user message."
        )
    if message.content is None or not message.content.strip():
        raise BackendProtocolError(
            "claude_code adapter requires non-empty user content."
        )

    had_backend_session = session_context.backend_session_id is not None
    backend_session_id = (
        session_context.backend_session_id or self._stable_backend_session_id()
    )
    session_state = ClaudeCodeSessionState(
        backend_session_id=backend_session_id,
        resume=had_backend_session,
    )

    if self._proxy is not None:
        await self._proxy.open_turn(
            turn_context.turn_id, backend_session_id=backend_session_id
        )

    success = False
    try:
        task = asyncio.create_task(
            self._run_claude_turn(
                user_text=message.content,
                turn_context=turn_context,
                session_state=session_state,
            )
        )
        try:
            (
                outputs,
                trace_events,
                usage,
            ) = await self._await_backend_task_or_proxy_max_steps(
                task,
                session_context=session_context,
                proxy=self._proxy,
            )
        except BackendTransportError as exc:
            await self._raise_if_proxy_context_overflow()
            await self._raise_if_proxy_rollout_invalidated()
            await self._raise_with_proxy_failed_upstream(exc)
        if self._proxy is not None:
            await self._proxy.drain_turn(
                timeout=self._remaining_timeout(
                    deadline, operation="wait for rollout proxy drain"
                )
            )
            await self._raise_if_proxy_context_overflow()
            await self._raise_if_proxy_rollout_invalidated()
        session_context.backend_session_id = backend_session_id
        success = True
        return AdapterResponse(
            outputs=outputs,
            trace_events=trace_events,
            usage=usage,
            backend_session_id=backend_session_id,
        )
    finally:
        if self._proxy is not None:
            drain_timeout = None if success else 2.0
            try:
                await self._proxy.drain_turn(timeout=drain_timeout)
            except asyncio.TimeoutError:
                LOGGER.warning(
                    "Timed out draining rollout proxy requests for turn %s",
                    turn_context.turn_id,
                )
            finally:
                await self._proxy.clear_turn()
```

</details>

<details>
<summary>原话、尚不清楚与来源</summary>

## 我的直接表述（原话）

> 好的 那么继续吧
> 看一下这里到底是在做什么?
> 或者 你觉得 我目前需要看哪些内容呢?

这表示沿上一轮推荐的适配器方向继续，不代表已经理解本函数或 CLI 的内部机制。

后续表述：

> 好的 我简单理解就是确定是什么对话
> 然后把这个claude硬性的内容给claude
> 然后等待结果?
> 大抵是这个样子我可以这么理解吗?
>
> 那么现在再看一下吧
> 还有什么需要我理解的吗?

助手按上下文将其理解为“确定会话，交入题目及执行资料，等待结果”。主线可如此概括；会话选择还包括新建/续接，等待的是这次 CLI 运行而不只是一轮模型回复。代理 open_turn/drain_turn/clear_turn 的作用先保留为归属与收尾，不要求立即深入。下一处仍为 _run_claude_turn 的实际进程启动。

2026-11-08 返回段追问（原话）：

> 是这里的adapter response就直接把这些内容返回了对吗?
> 看一下scope的部分吧
> 目前是这些就结束了吗?

助手核对：return 创建并返回包含三项执行结果与后端会话编号的 AdapterResponse 对象；正常完成 finally 后，服务端 _run_turn 接住它。本函数这一层可以收拢，Step 006 还需接清服务端保存结果、客户端查询与 generate 的结果整理。此处不表示用户已确认掌握上述全部交接。

## 尚不清楚

- CLI 参数、环境变量和工作目录的具体值及如何启动进程。
- Claude 的输出事件如何转换成 AdapterResponse 的组成部分。
- 等待器与代理失败检查的完整协作，后续按需展开。

## 来源与验证

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 本函数：adapters/claude_code.py:323–410；下游执行入口：528–607；调用方：core/server.py:607–611。
- [Step 006 本次记录](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/04-flow.md#claude-send-message-reading)。仅静态核对，没有启动 CLI 或执行模型调用。

</details>
