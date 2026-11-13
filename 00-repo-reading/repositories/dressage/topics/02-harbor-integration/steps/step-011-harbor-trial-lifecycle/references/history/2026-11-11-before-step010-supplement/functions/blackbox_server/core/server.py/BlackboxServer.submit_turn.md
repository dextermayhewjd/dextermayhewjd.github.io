> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.submit_turn.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.submit_turn.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.submit_turn.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.submit_turn.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# BlackboxServer.submit_turn

> Step 007 继承：来自 [Step 006 的 02-short-term-memory 记录](../../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.submit_turn.md)；保留原话、来源与未知，继承不表示新增掌握。

[Step 006 阅读导航](../../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md#reading-navigation) → [api.sessions.send_message](../../api/sessions.py/send_message.md) → **本函数：登记调用并安排后台执行** → 返回 submission。

## 函数定位

- 源码：[core/server.py:413–532](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L413)。
- 首次单独展开：Step 006，2026-11-08。
- 最近认识更新：2026-11-08，用户已概括提交前读取会话、锁和调用编号以协调提交，随后用“开关”理解 Event，并表示可以继续；Task 调度与 Event 等待的说明及小验证保留在下方。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：HTTP 路由收到题目消息，在 request_scope 中调用本函数。
2. **具体内容**：检查会话与提交是否可用，识别重复调用；首次提交时保存记录、创建后台 Task，返回提交信息。
3. **建议构建的心智模型**：

   > 确认这次 Agent 调用可以提交，把它登记下来并安排后台执行，再返回提交记录。

4. **调用代码**，来自 api.sessions.send_message：

   ```python
   async with server.request_scope():  # 统计当前请求的进入和离开。
       submission = await server.submit_turn(session_id, payload)
   # 离开上面的区段后，路由才把 submission 组织成 HTTP 202 回复。
   ```

这里的 request 参数就是路由传入的 payload（MessageRequest），不是 HTTP Request 对象。request.messages 是题目消息，request.turn_id 是这次调用编号。

## 本场景的输入与输出：先看首次正常提交

先用一次题目请求理解它：客户端已经说“请让 Agent 处理这段题目”。submit_turn 接住这份请求，检查能否接收，记录题目并安排后台处理，再告诉调用方“这次提交的编号和状态是什么”。它返回的不是题目的答案。

这里会出现四份不同的东西：

1. **TurnRecord**：留在服务端，记住题目、调用编号和当前状态。
2. **asyncio.Task**：留在服务端，让 _run_turn 在后台推进 Agent 执行。
3. **asyncio.Event**：给查询这次调用的人一个通知，告诉它可以结束等待、再读取状态和结果。
4. **TurnSubmission**：返回给路由，随后组成 HTTP 202 回复，告诉客户端本次提交已被接收。

当前假设注册已完成、会话可用、没有相同 turn，也没有另一个正在执行的 turn。下面是正常路径节选，省略检查和异常包装；完整函数保留在文末。

### 1. 找到会话，检查能不能提交

1. 确认服务已 Ready，消息格式与绑定的 session_id 符合要求。
2. 取得注册阶段已经保存的 session 及它的锁。
3. 在会话锁内检查状态、次数、重复编号和其他正在执行的调用。

核心的数据来路是：

```python
bound_session_id = self._require_bound_session_match(session_id)
session = await self._session_store.get(bound_session_id)
session_lock = await self._session_store.get_lock(bound_session_id)

# 以下编号与指纹处理位于原函数的会话锁内。
effective_turn_id = self._resolve_turn_id(session, request.turn_id)
request_fingerprint = message_request_fingerprint(request.messages)
existing = session.turn_ledger.get(effective_turn_id)
```

这里的会话锁用于同一会话的提交协调，不是外层 request_scope 的请求计数锁。

### 2. 登记这次调用，创建后台 Task

```python
now = utcnow()
session.turn_ledger[effective_turn_id] = TurnRecord(
    turn_id=effective_turn_id,
    request_fingerprint=request_fingerprint,
    status=TurnStatus.QUEUED,             # 当前先记为排队/已提交。
    request_messages=request.messages,   # 保存本次题目消息。
    created_at=now,
    updated_at=now,
)
# 给本次调用保留一个完成通知对象。
self._turn_events[(bound_session_id, effective_turn_id)] = asyncio.Event()
# 交给事件循环调度，不需要等以后有人 await task 才开始。
task = asyncio.create_task(
    self._run_turn(bound_session_id, effective_turn_id, request)
)
self._active_turn_tasks[bound_session_id] = task  # 保存 Task，供后续管理。
```

本函数安排的是 `_run_turn`。真正调用 Agent 适配器发生在该后台协程中；不是返回 HTTP 202 之后，客户端才重新发出一条启动命令。

### 2.1 Task、Event 与调用记录为什么分开

| 对象 | 负责什么 | 本仓库怎样使用 |
| --- | --- | --- |
| `asyncio.Task` | 后台执行的句柄，供查询是否结束、请求取消等操作使用 | `_active_turn_tasks[session_id]` 保存正在执行的任务；取消接口可以找到它并调用 task.cancel() |
| `asyncio.Event` | 通知等待者停止等待，再去读取当前结果 | `_turn_events[(session_id, turn_id)]` 对应一次调用；查询接口等待它，执行或取消逻辑设置它 |
| `TurnRecord` | 保存业务状态、题目消息、结果或错误 | `session.turn_ledger[turn_id]` 是查询实际结果的位置；Event 本身不保存答案 |

**create_task 会安排运行；await task 是等待它结束。** 事件循环调度到这个 Task 时，后台函数就可以继续执行，不需要等另一个地方显式 await task 才启动。

### 2.2 为什么查询结果时不直接等执行 Task

设想 Agent 还在解题，而一次 HTTP 查询最多只想等待一段时间。查询超时应当返回当前状态，让客户端之后继续查询；不应该因此把 Agent 一起取消。

当前 [get_turn](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L737) 等的是 Event：

```python
# get_turn 的实际等待片段：超时只结束本次通知等待。
with contextlib.suppress(asyncio.TimeoutError):
    await asyncio.wait_for(event.wait(), timeout=clamped)
# 后面再次读取 turn_ledger 中的 record，组织当前状态和结果。
```

执行端 [_run_turn](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L704) 在 finally 中设置 Event，并按当前任务身份清理 `_active_turn_tasks`。显式取消时，另一处代码会对真正的执行 Task 调用 cancel。

1. **Task 负责执行和执行生命周期。** 保存它是为了能管理这次运行，不是用它保存题目答案。
2. **Event 负责通知。** 多个查询可以等同一个通知；一次查询超时或取消不会经这个等待直接取消执行 Task。
3. **Record 负责结果。** 被唤醒后还要检查状态，Event 被设置不表示一定成功，也可能对应失败或取消。

这不是 Python 强制必须使用两个对象；也可以设计基于 Task 的等待，但要另行处理超时/取消的传播。本实现通过 Event 把查询等待和执行控制分开。本轮读懂这个分工即可，不必继续展开完整状态机。

**Event 可以先理解为一个“带等待能力的开关”。** 初始是关闭状态；调用 event.wait() 的协程等着；event.set() 将其打开，等待者便可以继续，之后的 wait() 也能直接通过。它不是启动或暂停执行 Task 的开关，也不存放题目答案。本例用它表示“可以结束等待，再检查调用记录”。

### 3. 返回提交记录

```python
return TurnSubmission(
    turn_id=effective_turn_id,
    status=TurnStatus.QUEUED,
    idempotent_replay=False,              # 本次新建，未复用旧提交。
    instance_id=self._response_instance_id(),
)
```

路由将这份记录赋给 submission，再构建 HTTP 202 回复。记录说明“提交了哪次调用”，不含 Agent 最终答案；客户端后续按同一个 turn_id 查询执行结果。

### 必须保留的重复与冲突边界

1. **相同 turn_id、相同消息指纹**：返回已有调用的记录，不再创建一个后台 Task。
2. **相同 turn_id、不同消息指纹**：报冲突，不能把另一个请求当作原调用。
3. **不同 turn_id，但当前会话已有活跃调用**：报冲突，不能在同一个会话里同时提交另一个活跃 turn。

上述判断均由实际代码完成，不能只凭客户端复用 turn_id 就假定去重已生效。

## 返回与下一处

- 返回：[api.sessions.send_message](../../api/sessions.py/send_message.md) 的 submission，继续组织 HTTP 回复。
- 后台方向：[_run_turn 函数卡](BlackboxServer._run_turn.md)，负责调用 Agent 适配器、更新结果并发出通知；现按用户请求进入这一层。
- 外层 request_scope 只统计这个提交处理区段。退出后，请求计数可能下降，但后台 Agent 仍可能正在运行。

<details>
<summary>完整源码（固定版本，未裁剪）</summary>

```python
async def submit_turn(self, session_id: str, request: MessageRequest) -> TurnSubmission:
    """Accept (or idempotently replay) a turn and start background execution.

    Runs the short admission critical section under ``session_lock`` and then
    releases the lock, spawning ``_run_turn`` for the actual backend call.
    """

    self._ensure_state_ready_for_messages()
    await self._wait_if_paused()
    self._validate_identifier("session_id", session_id)
    if request.turn_id is not None:
        self._validate_identifier("turn_id", request.turn_id)
    capabilities = self._require_capabilities()
    self._validate_message_request(request.messages, capabilities)

    assert self._binding_context is not None
    assert self._adapter is not None

    bound_session_id = self._require_bound_session_match(session_id)
    if bound_session_id is None:
        raise ApiError(
            500,
            "internal_error",
            "Rollout binding is missing bound_session_id.",
        )
    session = await self._session_store.get(bound_session_id)
    session_lock = await self._session_store.get_lock(bound_session_id)
    if session is None or session_lock is None:
        raise ApiError(
            500,
            "internal_error",
            "Bound session was not initialized.",
            details={"session_id": bound_session_id},
        )

    async with session_lock:
        if session.state == SessionState.ABORTED:
            raise ApiError(
                409,
                "conflict",
                "Session has been aborted and cannot accept new turns.",
                details={"session_id": session_id, "state": session.state},
            )
        if session.state == SessionState.DESYNCED:
            raise ApiError(
                409,
                "conflict",
                "Session is desynced and cannot accept new turns.",
                details={"session_id": session_id, "state": session.state},
            )
        if session.turn_count >= self._effective_config.max_turns:
            raise ApiError(
                429,
                "too_many_requests",
                "Session reached the max committed turn limit.",
                details={"session_id": session_id, "max_turns": self._effective_config.max_turns},
            )

        effective_turn_id = self._resolve_turn_id(session, request.turn_id)
        request_fingerprint = message_request_fingerprint(request.messages)
        existing = session.turn_ledger.get(effective_turn_id)
        if existing is not None:
            if existing.request_fingerprint != request_fingerprint:
                raise ApiError(
                    409,
                    "conflict",
                    "Same turn_id was already used with a different request body.",
                    details={"session_id": session_id, "turn_id": effective_turn_id},
                )
            # Same turn_id + same fingerprint: idempotent replay of the
            # existing record regardless of its state.  COMMITTED replays the
            # result, QUEUED/INFLIGHT re-attach to the same execution, and the
            # remaining terminal states are returned as-is for the client to
            # decide the next step.
            return TurnSubmission(
                turn_id=effective_turn_id,
                status=existing.status,
                idempotent_replay=True,
                instance_id=self._response_instance_id(),
            )

        # Distinct turn_id while another turn is still active: at most one
        # active turn per session.
        active_turn_id = self._active_turn_id(session)
        if active_turn_id is not None:
            raise ApiError(
                409,
                "conflict",
                "Session already has an active turn in progress.",
                details={
                    "session_id": session_id,
                    "turn_id": effective_turn_id,
                    "active_turn_id": active_turn_id,
                },
            )

        if not await self._adapter_health_with_retry("before_send_message"):
            await self._mark_backend_error("adapter_healthcheck_failed")
            raise ApiError(503, "service_unavailable", "Backend is unavailable.")

        now = utcnow()
        session.turn_ledger[effective_turn_id] = TurnRecord(
            turn_id=effective_turn_id,
            request_fingerprint=request_fingerprint,
            status=TurnStatus.QUEUED,
            request_messages=request.messages,
            created_at=now,
            updated_at=now,
        )
        self._turn_events[(bound_session_id, effective_turn_id)] = asyncio.Event()
        task = asyncio.create_task(
            self._run_turn(bound_session_id, effective_turn_id, request)
        )
        self._active_turn_tasks[bound_session_id] = task
        return TurnSubmission(
            turn_id=effective_turn_id,
            status=TurnStatus.QUEUED,
            idempotent_replay=False,
            instance_id=self._response_instance_id(),
        )
```

</details>

<details>
<summary>原话、尚不清楚与来源</summary>

## 我的直接表述（原话）

> 好的 那么看一下这里的这个server request scope的内容吧
> 也就是你说的这个await server submit turn这里的内容吧

助手先区分请求计数包装与任务提交主体，再按首次正常提交展开；该说明不代表用户已经掌握两者的区别。

用户继续反馈：

> 好的那么能否和我解释游戏ia这里的submit turn到底做了什么呢?
> 我不是特别理解

本轮用“记录题目、安排后台处理、返回提交记录”解释整体作用，并区分服务端的 TurnRecord、后台 Task 和返回的 TurnSubmission；尚待用户反馈。

随后用户表述：

> 好的 那么我差不多理解了
> 这里更多的内容是需要判断这里的agent调用可以提交对吗?
> 需要通过session store什么的获取一系列的信息和lock
> 然后来考虑一下这里的effective turn id啊什么的内容
> 避免同一个绘画的提交不协调
>
> 然后调用的时候在后台保存一个玩车能够统治的的对象
> 然后通过这个task的方式来完成这里的对于这个task的记录?
>
> 这里具体的机制你觉得我需要理解吗?
> 我其实不知道为什么保留一个event ?
> 我是知道创造一个task这里时会后续await的时候进行的
> 但是turn event和tasks为什么需要分开我其实不是特别理解

助手确认提交协调这一部分，纠正 Task 不需要等待后续 await 才开始；用执行句柄、通知对象和业务记录三个职责解释存储分工。用户对补充说明尚未给出确认。

用户进一步澄清：

> 不是不是 我需要理解的是task和event
> 我理解task只是提交了
> 并不一定是现在执行
> 后续可以通过await task来得到这个结果
>
> 单项式event我其实不是特别清楚到底是干嘛的
> 这个我觉得需要考虑清楚?
> 这里类似于一个 开关吗?
> 我的简单理解就是这里的这个这里通过这个类似的开关?
>
> 这是我对于这里的理解?
> 也就是
> 好的我觉得可以继续下去了?

助手确认 create_task 是安排运行、不保证在当前语句立刻开始，await task 可以等待并取得协程返回值；Event 的“开关”比喻可用，进一步限定为等待者的通行标志，而非 Task 的执行开关。当前函数 _run_turn 的业务结果另存 TurnRecord。可以按这一层理解继续，下一候选为 _run_turn，不要求先深入 Event 底层实现。

## 尚不清楚

- `_run_turn` 如何调用适配器、更新执行状态与结果。
- Event 通知、查询超时与执行 Task 的分工本轮已从使用点补充，用户理解尚待反馈。
- 完整的关闭、取消、限流与健康检查分支，本轮不逐一展开。

## 来源与验证

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 主体：core/server.py:413–532；请求计数：同文件 140–151；后台入口：577；HTTP 调用点：api/sessions.py:33–43。
- [Step 006 本次记录](../../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/04-flow.md#request-scope-and-submit-turn)。业务源码仅静态核对，未运行 Dressage 的 submit_turn、调用 Agent 或发出 HTTP 请求；下面的小验证仅使用 Python 标准库。
- 2026-11-08 补充标准库小验证：后台协程先设置 started，再等待手动放行；不 await 执行 Task 也能观察它已启动。等待 finished Event 超时后，执行 Task 仍未完成且未取消；放行后收到通知并从独立 record 读取结果。仅运行本地 asyncio 示例，没有运行 Dressage 或沙箱，也不以计时快慢证明调度顺序。

</details>
