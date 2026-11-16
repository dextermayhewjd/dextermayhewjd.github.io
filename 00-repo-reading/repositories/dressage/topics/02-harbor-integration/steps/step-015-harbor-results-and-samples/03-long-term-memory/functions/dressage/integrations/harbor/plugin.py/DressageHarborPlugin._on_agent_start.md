# DressageHarborPlugin._on_agent_start

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_agent_start.md) 完整继承；不改变原认识时间或掌握状态。

- 源码：[plugin.py:694–705](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L694)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独展开：Step 014 第三部分，2026-11-14。
- 最近认识更新：2026-11-14，用户已关注 event 查记录与状态变化，但将 turn_id 理解为查找 Proxy；本轮校准查找关系，理解待反馈。

[Trial._run_agent_phase 发出 AGENT_START](../../../../harbor/trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-mainline) ⇒ **当前 _on_agent_start** → handle.open_turn → 回到执行阶段，再调用 [ClaudeCode.run](../../../../harbor/agents/installed/claude_code.py/ClaudeCode.run.md#claude-run-mainline)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Trial 已完成环境与 Agent 准备，即将开始 Agent 执行；Harbor 触发此前登记的 Dressage 回调。
2. **具体内容**：取回已登记的尝试，生成 turn_id，通过已有 handle 打开本轮交互，然后更新轮次和状态。
3. **建议构建的心智模型**：

   > 前面的 _on_start 已经建好请求路由；现在确定本轮交互的编号，并让这条路由开始接收请求。

4. **调用背景**（处理函数已在 [on_job_start](DressageHarborPlugin.on_job_start.md#job-start-hooks) 中登记；下面是 Harbor 执行阶段的节选）：

   ```python
   # Trial._run_agent_phase
   await self._emit(TrialEvent.AGENT_START)  # 调用已登记回调，当前进入 _on_agent_start。
   target.agent_result = AgentContext()     # 回调正常返回后，继续执行阶段的准备。
   # 后面才调用具体 Agent.run。
   ```

## 本场景的输入与输出

输入 event 用于找回同一次尝试的记录。已有 `record.trial_id`、`record.handle` 和 READY 路由；`turn_sequence` 初始为 0。正常返回 None，产生本轮 turn，并使对应路由和插件记录进入 ACTIVE。

<a id="agent-start-mainline"></a>

完整函数，仅添加就地注释：

```python
async def _on_agent_start(self, event: Any) -> None:
    record = self._require_record(event)  # 按事件里的 trial_name/trial_id 查已有记录。
    if record.phase is AttemptPhase.ACTIVE:
        return  # 已激活，重复通知直接返回。
    if record.phase is not AttemptPhase.READY or record.handle is None:
        raise RuntimeError(
            f"AGENT_START is invalid while attempt is {record.phase.value}"
        )
    turn_id = f"{record.trial_id}:{record.turn_sequence}"  # 生成本轮编号，不用它查找 Proxy。
    await record.handle.open_turn(turn_id)  # handle 已关联 Proxy，把本轮编号交给它并激活路由。
    record.turn_sequence += 1  # 为下一轮交互准备序号。
    record.phase = AttemptPhase.ACTIVE  # 插件侧同步标记正在执行。
```

当前的查找关系是 `event 的 (trial_name, trial_id) → record → record.handle → binding.proxy`。`turn_id` 是交给这个已关联 Proxy 的本轮编号；这里不按 turn_id 重新查找 Proxy。

`record.phase` 是插件保存的尝试状态；Gateway 的 `binding.state` 在 open_turn 内部变为 ACTIVE。这些是已有内存对象的状态变化，不等于本函数已将轨迹持久化。此前只短核对上述关系；本轮按追问进入 [AttemptHandle.open_turn](../gateway.py/AttemptHandle.open_turn.md#open-turn-mainline) 的短卡，调度机制仍不重复展开。

回调正常返回 [_run_agent_phase](../../../../harbor/trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-mainline)，该函数继续建立执行记录、设置运行条件，再调用 ClaudeCode.run。新建的 turn_id 用于关联这一轮执行中的模型请求，不是每发一次 HTTP 就在这里生成一个新编号。

## 我的直接表述（原话）

> 好的 那么开始这个第三部分这里的内容吧
> 看一下这里的这个函数卡片应该怎么建立吧

此前是本轮范围确认。本次追问：

> 这里其实就是
> 在进入的这个过程中
> 通过event的方式查看记录?
> 说实话我还是没有太理解这里的这个trial机制
> 但是我大概理解
> 但是在这个条件下
> 这里其实是在通过这个record里面的trial id和record turn sequence来
> turn id来找到这个proxy的?
> 也就是说这里其实精准的在这里也流下来了一个状态?
> anyway
> 那么我们继续吧
> 下一步需要看什么了呢?

助手校准：event 用于查已有尝试记录，handle 已关联 binding/Proxy；turn_id 标识本轮交互，不承担查找 Proxy 的职责。更新 ACTIVE 属于运行中的状态变化。

## 尚不清楚

- AttemptHandle.open_turn 已补为短卡；runtime.call 与公共 Proxy 内部仍按已有职责处理。
- 路由激活后，Gateway 怎样接收请求、查 binding 并返回响应，下一张主卡再读。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对 _on_agent_start:694–705、_require_record:894–899，以及 on_job_start:408 的注册位置。
- AttemptHandle.open_turn（gateway.py:292–306）通过已有 Runtime 调度，调用 binding.proxy.open_turn 后把 binding.state 设为 ACTIVE。RolloutLLMProxy.open_turn:118–122 创建本轮 _TurnScope；本轮不展开公共 Proxy 内部。
- AttemptRecord.turn_sequence 默认值为 0。Harbor v0.25.0 Trial._run_agent_phase:711–714 在 await AGENT_START 后才创建 AgentContext 与计时记录。
- 主体与字段含义只作静态核对，未执行 Agent、路由激活或模型请求；不同固定版本的运行兼容性仍待验证。
- [本轮记录](../../../../../../../step-014-model-routing-and-api-contract/04-flow.md#third-part-agent-start)。

</details>
