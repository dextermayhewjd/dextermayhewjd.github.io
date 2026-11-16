> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# BlackboxServerClient._poll_turn

> Step 007 继承：来自 [Step 006 的 02-short-term-memory 记录](../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md)；保留原话、来源与未知，继承不表示新增掌握。

[Step 006 阅读导航](../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md#reading-navigation) → [客户端 call_agent](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.call_agent.md) → **本函数：等待并取回已有调用的结果** → 返回 call_agent。

## 函数定位

- 源码：[client.py:159–195](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L159)。
- 首次单独展开：Step 006，2026-11-08。
- 最近认识更新：尚无本函数的独立复述；本轮按用户确认建立源码说明。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：客户端 call_agent 已提交题目，并收到 async 模式的提交回复。服务端可能仍在执行，需要继续查询结果。
2. **具体内容**：按会话和调用编号向 BlackboxServer 查询状态，未完成则继续查询，完成则返回结果，失败则抛异常。
3. **建议构建的心智模型**：

   > 查询已经提交的这次 Agent 调用，等它结束，把结果带回来。

4. **调用处**，来自客户端 call_agent 的提交回复之后：

   ```python
   return await self._poll_turn(
       endpoint,
       trajectory_id=trajectory_id,
       session_id=session_id,
       turn_id=turn_id,
       idempotent_replay=idempotent_replay,
   )
   ```

刚才读的 _run_claude_turn 在沙箱内执行 CLI。现在回到调用沙箱服务的客户端；查询可以与服务端执行同时进行，并不需要等 CLI 退出才开始。

## 本场景的输入与输出：沿完整函数看三处

输入沿用提交时的沙箱入口、会话 ID 和调用 ID。成功时返回调用结果字典，交回 call_agent，再经 Paddock 返回 generate 的 call_payload。下面保留完整函数，只添加中文注释。

```python
async def _poll_turn(
    self,
    endpoint: SandboxEndpoint,  # 沙箱内 BlackboxServer 的 URL 和请求 headers。
    *,
    trajectory_id: str,         # 传给请求辅助层，用于关联请求记录。
    session_id: str,            # 查哪个会话。
    turn_id: str,               # 查该会话中的哪次 Agent 调用。
    idempotent_replay: bool,    # 提交回复中的重复提交标记，带入最终结果。
) -> dict[str, Any]:
    # [1] 准备等待配置和查询地址，沿用已经提交的调用编号。
    poll_wait = _env_float(
        "DRESSAGE_BLACKBOX_AGENT_POLL_WAIT_SEC", 30.0, min_value=0.0
    )
    total_timeout = _env_float(
        "DRESSAGE_BLACKBOX_AGENT_POLL_TOTAL_TIMEOUT_SEC", 0.0, min_value=0.0
    )
    deadline = time.monotonic() + total_timeout if total_timeout > 0 else None
    url = f"{endpoint.url.rstrip('/')}/v1/sessions/{session_id}/turns/{turn_id}"
    while True:
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError(
                f"blackbox turn poll exceeded total timeout for "
                f"session_id={session_id} turn_id={turn_id}"
            )

        # [2] 发 GET 查询；wait 告诉服务端本次可以等待多久再回复。
        response = await self._get_turn_with_retry(
            url,
            params={"wait": poll_wait},
            operation="poll_turn",
            trajectory_id=trajectory_id,
            headers=endpoint.headers,
        )
        data = response.json()
        status = str(data.get("status") or "")

        # [3] 按状态决定：返回结果、报错，或继续下一次查询。
        if status == _TURN_COMMITTED:
            return self._committed_call_payload(data, idempotent_replay=idempotent_replay)
        if status in _TURN_ERROR_STATES:
            self._raise_turn_error(data, url)
        # queued / inflight (or unknown transient) -> keep polling.
        # 注意：具体的字符串 "unknown" 属于上面的失败状态，已经报错。
```

### 1. 地址决定查询哪一次执行

endpoint 指向沙箱内 BlackboxServer；session_id 与 turn_id 选中已有的调用记录。本函数发送 GET 查询，不会重新提交题目或再启动一次 Claude。

### 2. 发出查询，等待这次 HTTP 回复

这里进入 [_get_turn_with_retry 函数卡](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._get_turn_with_retry.md)，看查询怎样交给公共 HTTP 层。该方法正常返回后，从下面的正文解析继续。

默认传 wait=30。服务端若发现调用还在进行，可以等完成通知或等待到期再回复；调用提前完成时可以提前回复。客户端 await 的是这次 HTTP 查询，不是远端 Python Task；wait 也不是客户端固定睡眠间隔。

这接回前面见过的 Event：服务端 _run_turn 保存结果后设置完成通知，服务端 get_turn 可以等待该通知；客户端通过 HTTP 取得状态与结果。Event 本身没有跨网络传过来。

<a id="parse-query-response"></a>

查询返回后，回到这里读取正文与状态，再进入第 3 段判断：

```python
data = response.json()
status = str(data.get("status") or "")
```

<a id="committed-result"></a>

### 3. 状态决定下一步动作

| 服务端返回的 status | 本函数做什么 |
| --- | --- |
| queued / inflight | 尚未结束，进入下一轮查询 |
| committed | 结果已保存，整理结果字典并 return |
| failed / unknown / cancelled | 终止失败状态，抛出异常 |

成功分支进入 [_committed_call_payload 函数卡](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md)；它整理好结果字典后，这里的 return 直接结束 _poll_turn。

当前实现对其他未识别的状态也继续循环；它们与具体失败状态字符串 unknown 要分开。这里的 status 是本次 Agent 调用的状态，不是 Pod 的运行状态。

## 返回哪里，本轮在哪里停

<a id="return-call-payload"></a>

成功返回 call_agent，再返回 Paddock 与 generate。本轮看清“同一次调用 → 查询状态 → 等待或取回结果”即可。下一处是回到 generate，看 agent_response_text 怎样使用 call_payload。

<details>
<summary>按需回查：结果字段、超时与服务端入口</summary>

1. **结果字典**由 _committed_call_payload 整理，包含以下字段；这只是字段名清单，不是本次运行结果：

   ```python
   request_id, session_id, instance_id, turn_id, state
   idempotent_replay, outputs, backend, usage
   ```

   outputs 是返回消息；backend 与 usage 保留后端和用量资料。提交时取得的 idempotent_replay 在这里附回结果。服务端查询的 status 用于分支判断，不会由该辅助函数原样放入返回字典。

2. **总时限**默认 0，表示本函数不设置轮询总截止时间。设置正数后，每轮查询前检查 deadline；它不是用硬超时中断正在进行的 HTTP 请求，因此不保证恰在截止时刻结束。请求失败还可能由辅助层抛异常。

3. **下层入口**只作为本次解释的源码依据，不要求继续逐个深入：

   | 要核对什么 | 源码入口 |
   | --- | --- |
   | GET 请求与重试 | [_get_turn_with_retry 函数卡](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._get_turn_with_retry.md) |
   | 返回字典与失败异常 | [_committed_call_payload 函数卡](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md) · [_raise_turn_error:217](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L217) |
   | 谁接收这条查询 | [api.sessions.get_turn:55](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/api/sessions.py#L55) |
   | 服务端如何等待 Event | [BlackboxServer.get_turn:712](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L712) |

</details>

## 我的直接表述（原话）

> 好的那么看一下下一个你觉得我应该读的short term function吧

这是承接上一轮 _poll_turn 推荐的阅读请求，尚无对本函数机制的独立复述。

补清服务端返回链和阅读顺序后，用户明确接续：

> 那么现在看一下这里的这个poll turn吧

本轮复用已有卡片，从客户端提交后的查询位置进入；这次请求不代表已经掌握轮询内部机制。

## 尚不清楚

- 本轮的查询、等待和结果交接说明，尚待用户反馈。
- HTTP 重试、各类失败恢复和服务端完整状态查询逻辑，保留为按需回查。

<details>
<summary>来源与验证</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本次核对源码工作区干净。
- 完整函数仅添加注释，未删除分支；状态常量来自 client.py:23–25。
- 已核对调用者、GET 辅助层、匹配路由和服务端 Event 等待位置。仅静态核对，没有向沙箱发请求、运行 Agent 或验证真实等待时长。
- [Step 006 本次形成过程](../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/04-flow.md#poll-turn-reading)。

</details>
