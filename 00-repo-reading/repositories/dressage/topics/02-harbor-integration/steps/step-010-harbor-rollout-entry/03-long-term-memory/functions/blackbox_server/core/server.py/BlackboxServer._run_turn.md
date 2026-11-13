> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# BlackboxServer._run_turn

> Step 007 继承：来自 [Step 006 的 02-short-term-memory 记录](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md)；保留原话、来源与未知，继承不表示新增掌握。

[Step 006 阅读导航](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md#reading-navigation) → [submit_turn 安排后台任务](BlackboxServer.submit_turn.md) → **本函数：执行已提交的调用** → 保存结果，通知等待者。

## 函数定位

- 源码：[core/server.py:577–710](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L577)。
- 首次单独展开：Step 006，2026-11-08。
- 最近认识更新：2026-11-08，用户尝试概括第 3 段的锁、记录查找与活跃任务移除；助手补充各次查找取得的对象及保存、通知、清理之间的区别，尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：submit_turn 已记录题目、准备 Event，并创建运行本函数的后台 Task。
2. **具体内容**：将调用标记为执行中，把题目交给已注册的 Agent 适配器；保存结果或错误，最后设置 Event 并移除自己的活跃 Task 登记。它不只是记录运行，而是负责推进这次执行和收尾。
3. **建议构建的心智模型**：

   > 在后台执行这次 Agent 调用，保存执行结果，再通知等待者来查看。

4. **从哪里启动**，来自 submit_turn:523：

   ```python
   task = asyncio.create_task(
       self._run_turn(bound_session_id, effective_turn_id, request)
   )
   self._active_turn_tasks[bound_session_id] = task
   ```

顺序是：

1. submit_turn 把本函数安排进事件循环。
2. 本函数在后台推进 Agent 调用；客户端可以查询同一次 turn 的状态。
3. 本函数把结果写入记录，而不是把答案作为 Task 返回值交回 submit_turn。

## 本场景的输入与输出：沿正常路径读三段

输入沿用已有的 session_id、turn_id 和 MessageRequest。request.messages 是题目消息，self._adapter 是注册阶段已经准备好的适配器；本例为 ClaudeCodeAdapter。

**本函数正常返回 None。** 结果保存在会话记录中，Event 只负责通知。以下片段按真实执行顺序摘取；完整函数和失败分支在文末保留。

### 1. 找到调用记录，标记为执行中（585–596）

```python
session = await self._session_store.get(session_id)
session_lock = await self._session_store.get_lock(session_id)
# 原函数从这里进入外层 try；finally 会处理通知和 Task 登记清理。
if session is None or session_lock is None:
    return

async with session_lock:
    record = session.turn_ledger.get(turn_id)
    if record is None or record.status != TurnStatus.QUEUED:
        return  # 只接手仍处于 QUEUED 的本次调用。
    record.status = TurnStatus.INFLIGHT  # 从已提交，变成正在执行。
    record.updated_at = utcnow()
```

这里继续使用 submit_turn 建立的 TurnRecord，没有重新创建一个业务任务。离开这个 with 后会话锁已释放，不会持有它等待整次 Agent 执行。

### 2. 把题目交给 Agent 适配器，等待结果（598–611）

第 1 段把已有记录从 QUEUED 改为 INFLIGHT；这里把题目交给具体 Agent。此前从这里进入适配器；回看时只需对上末尾的 adapter_response 和 outcome，再进入第 3 段。

<a id="receive-adapter-result"></a>

**从适配器返回时的阅读入口：** 下面 await 正常完成后，adapter_response 接住 send_message 返回的对象，outcome 暂存这份成功结果。随后跳到第 3 段的成功分支，先不逐项阅读中间的异常分类。

```python
turn_context = TurnContext(
    turn_id=turn_id,                                  # 本次调用的编号。
    request_fingerprint=record.request_fingerprint,   # 本次请求的识别资料。
    metadata=request.metadata,
    deadline_seconds=self._effective_config.backend_timeout,
)

# 正常成功路径；原函数会另外处理取消、超时和后端异常。
adapter_response = await self._wait_for_backend_call_excluding_pause(
    self._adapter.send_message(session, turn_context, request.messages),
    timeout=self._effective_config.backend_timeout,
)
outcome = ("commit", adapter_response, None)  # 暂存成功结果，准备写入记录。
```

1. TurnContext 把本次调用的编号、附加资料和执行预算交给适配器。
2. `self._adapter.send_message(...)` 生成执行协程，由外层等待辅助函数调度并等待；该辅助函数还处理暂停与超时预算，本轮先按接口理解。
3. 适配器负责具体 Agent 的执行，成功后交回 adapter_response。当前 _run_turn 本身没有直接启动 CLI 子进程。

这里的 send_message 是注册时选中的 Agent 适配器方法，不是此前 HTTP 路由的同名函数。当前场景对应 ClaudeCodeAdapter.send_message。外层 `_wait_for_backend_call_excluding_pause` 管调度等待与预算，内层适配器管 Agent 执行；想追踪具体 Agent 行为时，下一处优先进入适配器，等待外壳先保留职责与返回关系。

这个对象来自 Step 005：register 中 `create_adapter(request.blackbox_type)` 在本例返回 ClaudeCodeAdapter，随后保存为 `self._adapter`。因此上面的方法调用会进入 claude_code.py；[对象来路与 self 的变化](../../adapters/claude_code.py/ClaudeCodeAdapter.send_message.md)已补在子卡开头。

<a id="save-result-and-notify"></a>

### 3. 保存结果，再设置 Event 通知等待者（675–710）

下面是成功提交分支节选：

```python
async with session_lock:
    record = session.turn_ledger.get(turn_id)
    if record is None or record.status != TurnStatus.INFLIGHT:
        return  # 期间若已被取消/中止，不再把它覆盖为成功。
    if outcome[0] == "commit":
        adapter_response = outcome[1]
        session.backend_session_id = adapter_response.backend_session_id
        session.conversation_history.extend(request.messages)
        session.conversation_history.extend(adapter_response.outputs)
        session.trace_events.extend(adapter_response.trace_events)
        session.turn_count += 1
        session.updated_at = utcnow()
        record.status = TurnStatus.COMMITTED  # 本次结果已提交。
        record.response = adapter_response   # 真正的结果保存在这里。
        record.updated_at = utcnow()
```

随后进入外层 finally。以下是 finally 的完整内容：

```python
event = self._turn_events.get((session_id, turn_id))
if event is not None:
    event.set()  # 打开通知开关，让等待者继续检查记录。
current = asyncio.current_task()
if self._active_turn_tasks.get(session_id) is current:
    self._active_turn_tasks.pop(session_id, None)  # 只移除自己的活跃登记。
```

1. **锁内取记录并保存结果。** session_id 和 turn_id 已经存在；session.turn_ledger.get(turn_id) 取得本次调用的 TurnRecord。成功分支更新会话历史，将 AdapterResponse 存入 record.response，并标记 COMMITTED。这里不是生成新的 session_id；保存的 backend_session_id 来自适配器返回值。
2. **锁外取得 Event 并发出通知。** self._turn_events.get((session_id, turn_id)) 找到本次调用的通知对象，event.set() 唤醒等待者。Event 不携带答案，也不表示一定成功；失败或取消路径也会走到通知。
3. **最后移除自己的活跃登记。** asyncio.current_task() 取得正在执行本函数的 Task；先用 get(session_id) 确认表中仍是它，再 pop 移除该项，避免误删后续任务的登记。本次 TurnRecord 和结果仍保留；pop 不是取消 Task 或销毁沙箱。

这正好接回上一段的分工：**Task 管执行，Event 管通知，TurnRecord 保存状态和结果。** 查询端通过 get_turn 读取记录，再由客户端的 _poll_turn 把结果交回 call_agent。

## 按需回查与返回位置

| 入口 | 什么时候看、看完接回哪里 |
| --- | --- |
| [_wait_for_backend_call_excluding_pause:161](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L161) | 想了解执行协程怎样被调度、暂停时如何计算预算，再展开；返回 adapter_response |
| [ClaudeCodeAdapter.send_message 函数卡](../../adapters/claude_code.py/ClaudeCodeAdapter.send_message.md) | 回查 AdapterResponse 的来路；看完接回本函数第 2 段末尾和第 3 段 |
| [BlackboxServer.get_turn:712](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L712) | 想了解客户端如何取得已保存的结果，再回到查询路径 |

本函数是后台入口，不会再沿普通调用栈把答案直接返回已结束的 submit_turn。执行结果通过共享记录和查询接口交付。以上入口先保留导航，不提前建卡。

<details>
<summary>失败路径：本轮先保留的边界</summary>

1. 执行等待被取消时，调用 _finalize_interrupted_turn_locked 更新本次记录，然后返回；finally 仍会通知等待者。
2. 超时、上下文超限、步数超限及后端异常等被整理成失败 outcome，再交给 _handle_unknown_turn 更新相应状态；不写入成功结果。
3. Agent 返回期间若记录已被取消/中止，不会再覆盖为 COMMITTED。
4. 通知与 Task 登记清理不是销毁整个沙箱；沙箱最终释放属于 generate 的外层生命周期。

完整恢复、关闭及异常归类本轮不逐项展开。

</details>

<details>
<summary>完整源码（固定版本，未裁剪）</summary>

```python
async def _run_turn(
    self,
    session_id: str,
    turn_id: str,
    request: MessageRequest,
) -> None:
    """Background execution of a submitted turn (does not hold session_lock)."""

    session = await self._session_store.get(session_id)
    session_lock = await self._session_store.get_lock(session_id)
    try:
        if session is None or session_lock is None:
            return

        async with session_lock:
            record = session.turn_ledger.get(turn_id)
            if record is None or record.status != TurnStatus.QUEUED:
                return
            record.status = TurnStatus.INFLIGHT
            record.updated_at = utcnow()

        turn_context = TurnContext(
            turn_id=turn_id,
            request_fingerprint=record.request_fingerprint,
            metadata=request.metadata,
            deadline_seconds=self._effective_config.backend_timeout,
        )

        outcome: tuple[str, Any, dict[str, Any] | None]
        try:
            adapter_response = await self._wait_for_backend_call_excluding_pause(
                self._adapter.send_message(session, turn_context, request.messages),
                timeout=self._effective_config.backend_timeout,
            )
            outcome = ("commit", adapter_response, None)
        except asyncio.CancelledError:
            async with session_lock:
                self._finalize_interrupted_turn_locked(session, turn_id)
            return
        except asyncio.TimeoutError:
            outcome = (
                "unknown",
                None,
                {
                    "error": "backend_timeout",
                    "message": "Backend call exceeded backend_timeout.",
                    "http_status": 504,
                },
            )
        except BackendContextOverflowError as exc:
            outcome = (
                "unknown",
                None,
                {
                    "error": "context_overflow",
                    "message": str(exc),
                    "http_status": 413,
                    "extra_details": exc.details(),
                },
            )
        except BackendMaxStepsExceededError as exc:
            outcome = (
                "unknown",
                None,
                {
                    "error": "max_steps_exceeded",
                    "message": str(exc),
                    "http_status": 429,
                    "extra_details": exc.details(),
                },
            )
        except (BackendTransportError, BackendProtocolError, BackendProcessError) as exc:
            outcome = (
                "unknown",
                None,
                {
                    "error": "backend_error",
                    "message": f"Backend request failed: {exc}",
                    "http_status": 502,
                    "process_error": isinstance(exc, BackendProcessError),
                },
            )
        except Exception as exc:
            LOGGER.exception(
                "unexpected error while running turn %s for session %s",
                turn_id,
                session_id,
            )
            outcome = (
                "unknown",
                None,
                {
                    "error": "internal_error",
                    "message": f"Unexpected backend failure: {exc}",
                    "http_status": 500,
                },
            )

        async with session_lock:
            record = session.turn_ledger.get(turn_id)
            if record is None or record.status != TurnStatus.INFLIGHT:
                # Turn was aborted/cancelled concurrently; do not commit.
                return
            if outcome[0] == "commit":
                adapter_response = outcome[1]
                session.backend_session_id = adapter_response.backend_session_id
                session.conversation_history.extend(request.messages)
                session.conversation_history.extend(adapter_response.outputs)
                session.trace_events.extend(adapter_response.trace_events)
                session.turn_count += 1
                session.updated_at = utcnow()
                record.status = TurnStatus.COMMITTED
                record.response = adapter_response
                record.updated_at = utcnow()
            else:
                error_kwargs = dict(outcome[2] or {})
                process_error = bool(error_kwargs.pop("process_error", False))
                await self._handle_unknown_turn(
                    session=session,
                    turn_id=turn_id,
                    error=error_kwargs["error"],
                    message=error_kwargs["message"],
                    http_status=error_kwargs.get("http_status"),
                    extra_details=error_kwargs.get("extra_details"),
                )
                if process_error:
                    await self._mark_backend_error("backend_process_error")
    finally:
        event = self._turn_events.get((session_id, turn_id))
        if event is not None:
            event.set()
        current = asyncio.current_task()
        if self._active_turn_tasks.get(session_id) is current:
            self._active_turn_tasks.pop(session_id, None)
```

</details>

<details>
<summary>原话、尚不清楚与来源</summary>

## 我的直接表述（原话）

> 好的那么轻开一个run turn的函数卡片吧

这是本次建卡请求，不表示已掌握后台执行和结果提交的全部机制。

用户随后表述并追问：

> 好的 那么我现在可以简单理解为
> 之前的submit是尝试运行记录了这个task
> 同时通过这个run turn来记录下这个运行
> 然后呢?
> 我不是特别清楚下一步是需要做什么了?
> 或者再度这里的这个run turn的过程中需要看什么?

助手校准：submit_turn 登记并安排后台工作；_run_turn 实际推进适配器调用，随后保存结果和通知。当前重点先放在第 2 段的执行交接，不把该函数仅理解为运行记录器；下一下钻候选是当前具体适配器的 send_message，暂不创建新卡。

2026-11-08，第 3 段的表述与追问：

> 难道不是在这里的run turn之后 看一下这里的这个3吗?
> 也就是这里的在这个session lock之后拿到做了当前的这个session id
> 然后通过设计get然后从self active turn tasks 这里pop出去?
> 是我的理解?

助手确认当前正是本函数第 3 段，并区分三个对象：锁内按 turn_id 查 TurnRecord，锁外按 (session_id, turn_id) 查 Event，最后按 session_id 查活跃 Task 并核对身份后移除。该说明补在第 3 段代码下方；原有编号和阅读位置不变。

## 尚不清楚

- 适配器怎样启动 CLI、收集输出和处理模型/工具交互。
- 暂停与超时辅助函数的完整行为。
- 查询端如何从记录生成回复，以及取消和结果提交竞争时的所有分支。

## 来源与验证

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 主体：core/server.py:577–710；启动处：同文件 523–526；返回读取：get_turn 与 _build_turn_status_response。
- [Step 006 本次记录](../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/04-flow.md#run-turn-card)。本次只核对源码和卡片，没有运行 Dressage 后台任务、Agent 或模型请求。

</details>
