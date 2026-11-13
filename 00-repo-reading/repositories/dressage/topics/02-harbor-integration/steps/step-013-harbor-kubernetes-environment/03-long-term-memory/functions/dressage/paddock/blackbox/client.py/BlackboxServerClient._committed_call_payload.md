> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# BlackboxServerClient._committed_call_payload

> Step 007 继承：来自 [Step 006 的 02-short-term-memory 记录](../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md)；保留原话、来源与未知，继承不表示新增掌握。

[Step 006 阅读导航](../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md#reading-sequence) → [_poll_turn 的成功分支](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md#committed-result) → **本函数：整理已经完成的调用结果** → 返回 _poll_turn。

## 函数定位

- 源码：[client.py:197–214](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L197)。
- 首次单独展开：Step 006，2026-11-08。
- 最近认识更新：2026-11-08，用户尝试将内容概括为 metadata 与确定的任务资料；助手补充分清调用标识、实际输出及用量，字段来源的理解尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_poll_turn 已解析查询回复，并确认 status 是 committed，调用结果已由服务端保存。
2. **具体内容**：从回复字典中选出调用标识、输出和用量等字段，加上提交阶段取得的重复提交标记，返回新的字典。这样异步查询得到的结果沿用原同步接口的返回结构。
3. **建议构建的心智模型**：

   > 把已经拿到的调用结果整理成上层需要的字典，再交回去。

4. **调用处**，位于 _poll_turn：

   ```python
   if status == _TURN_COMMITTED:
       return self._committed_call_payload(
           data, idempotent_replay=idempotent_replay
       )
   ```

## 本场景的输入与输出：直接看完整函数

data 是本次 GET 回复经 response.json() 得到的字典。idempotent_replay 来自此前的提交回复。下面仅增加中文注释；返回的整个字典就是本函数的输出。

这里的 data 是执行后的服务端回复，不是 generate 最初传入的 metadata 配置。会话与任务编号用于标识本次调用；outputs 保存实际输出，usage 保存用量，不能把整份结果都理解成预先确定的任务资料。

```python
@staticmethod
def _committed_call_payload(
    data: dict[str, Any],
    *,
    idempotent_replay: bool,
) -> dict[str, Any]:
    """Assemble a payload matching the legacy synchronous ``/messages`` body."""
    return {
        "request_id": data.get("request_id", ""),  # 请求标识，缺少时用空字符串。
        "session_id": data.get("session_id"),      # 当前会话。
        "instance_id": data.get("instance_id"),    # 任务实例。
        "turn_id": data.get("turn_id"),            # 本次 Agent 调用。
        "state": data.get("state"),                # 服务端会话状态。
        "idempotent_replay": idempotent_replay,     # 从提交阶段带来的重复提交标记。
        "outputs": data.get("outputs") or [],      # Agent 输出消息；缺少或为空时用空列表。
        "backend": data.get("backend"),            # 后端类型与后端会话等资料。
        "usage": data.get("usage"),                # 本次调用的用量资料。
    }
```

这里先记住三件事：

1. **只是选字段并整理字典。** 不发请求、不运行 Agent，也不把 outputs 自动提取成一段回答文字。
2. **不把所有查询字段原样返回。** 例如 status、error、时间戳没有放进结果字典；成功状态已经由外层检查。
3. **state 与 status 是不同字段。** state 是服务端会话状态，status 是本次调用状态；这里的 state 也不是前面 Paddock 返回的 SandboxState 环境访问资料。

## 返回哪里，本轮在哪里停

本函数返回字典后，_poll_turn 成功分支的 return 也随之结束。字典继续经客户端 call_agent、Paddock.call_agent 返回，最终由 generate 的 call_payload 接住。

本轮看清字段整理与返回关系即可；如何从 call_payload 得到 agent_response，留到返回 generate 时再看。

## 我的直接表述（原话）

> 好的 那么看一下这个函数的函数卡吧

这是建立函数卡的请求。

后续表述与追问：

> 好的 这里简单来说就是一系列的meta data里的内容对吧
> 一系列的确定性的任务?
> 还有什么需要我了解的部分吗?

助手校准：如果这里指会话、任务和调用编号，它们确实是返回资料的一部分；但这份字典也包含执行产生的 outputs 和 usage。函数只选择字段并组装字典，不生成任务，也不保证执行结果具有确定性。

## 尚不清楚

- 本轮的字段整理与返回关系，尚待用户反馈。
- generate 怎样从这个字典取得回答文本，后续沿 scope 接续。

<details>
<summary>来源与验证</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 当前函数与调用处：client.py:191–214。
- 查询字段依据：[TurnStatusResponse](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/models.py#L255) 与 [_build_turn_status_response](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L1042)，仅用于核对字段来源，未另建卡。
- [本次形成过程](../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/04-flow.md#committed-call-payload-reading)。仅静态核对，没有发送请求或运行 Agent。

</details>
