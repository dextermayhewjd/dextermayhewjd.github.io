# AttemptHandle.open_turn

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/AttemptHandle.open_turn.md) 完整继承；不改变原认识时间或掌握状态。

- 源码：[gateway.py:292–306](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L292)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独展开：Step 014 第三部分 3.5.1，2026-11-14；此前仅短核对接口效果，没有单独带读完整函数。
- 最近认识更新：2026-11-14，用户已概括给已有 Proxy 打开本轮交互；内层 operation 的必要性尚有疑问，本轮补充说明后按要求继续主线。

[_on_agent_start](../plugin.py/DressageHarborPlugin._on_agent_start.md#agent-start-mainline) → **当前 record.handle.open_turn(turn_id)** → 返回 _on_agent_start，更新轮次和插件状态。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：调用方已生成 turn_id，当前 handle 已绑定本次 Trial 的 Proxy，路由为 READY。
2. **具体内容**：检查绑定状态，让 Proxy 接入本轮 turn，再把 Gateway 侧路由标为 ACTIVE。
3. **建议构建的心智模型**：

   > 给已经找到的 Proxy 设置本轮交互，让已有路由开始接收请求。

4. **调用代码**（_on_agent_start:703–705）：

   ```python
   await record.handle.open_turn(turn_id)  # 当前进入；不返回新的 handle。
   record.turn_sequence += 1              # 返回后由插件更新下一轮序号。
   record.phase = AttemptPhase.ACTIVE      # 插件记录也更新为 ACTIVE。
   ```

## 本场景的输入与输出

`self` 就是现有 record.handle，内部已有 `_binding`；`turn_id` 来自上一层，当前没有传 backend_session_id，采用默认 None。正常返回 None，Proxy 保存本轮标识，Gateway 的 binding.state 进入 ACTIVE。

<a id="open-turn-mainline"></a>

完整短函数，只补就地注释：

```python
async def open_turn(
    self, turn_id: str, backend_session_id: str | None = None
) -> None:
    async def operation() -> None:  # 先定义要交给网关循环执行的一组操作。
        binding = self._binding  # handle 已持有路由绑定，不按 turn_id 重新查找。
        if binding.state != AttemptState.READY:
            raise RouteStateError(
                f"cannot open turn for {self.trial_id}: route is {binding.state.value}"
            )
        # 让已关联的 Proxy 记录本轮交互标识。
        await binding.proxy.open_turn(
            turn_id, backend_session_id=backend_session_id
        )
        binding.state = AttemptState.ACTIVE  # 网关路由进入可接收请求的状态。

    await self._runtime.call(operation)  # 在网关所属循环执行上述操作。
```

`operation` 把检查、设置 turn 和更新状态放成一个可调用的操作。它定义在函数内，可直接使用这次的 self、turn_id、backend_session_id；定义时还没执行，下面的 runtime.call(operation) 才调用并等待它。这样符合 call 接收无参操作的接口，本轮不继续展开线程细节。

这里的 `binding.state` 属于 Gateway；返回后，调用方才更新插件的 `record.phase`。`runtime.call` 复用已读职责，不再次展开线程/取消机制。Proxy 内部怎样管理整轮模型请求留在公共补读，本轮只确认它接收 turn_id。

读完回到 [_on_agent_start](../plugin.py/DressageHarborPlugin._on_agent_start.md#agent-start-mainline) 的 await 之后，随后回调结束，Harbor 才继续 Agent 执行；下一张主卡仍是 Gateway 的 HTTP 接收与分派。

## 我的直接表述（原话）

> 好的 那么现在看一下下一个部分的这个函数把
> 但是为什么不再继续这里的这个3.5.1了呢?

助手校准：此前只按最小需要说明了 handle → binding.proxy 的关系，没有完整带读本函数。用户追问后，本轮明确补看 3.5.1，不将助手源码核对当成用户已经读完。

本轮理解与疑问：

> 我可以简单理解为
> 这里其实就是给已经找到的这个proxy开始交互
> 然后在本轮打开交互但是下面的这个网关所属循环执行这里我其实没有看懂也就是runtime call operation为啥要在函数里面单独再放一个这个operation呢?
> 我不是特别理解
> 但是躬耕就是上面说的这个operation
> 那么请继续看一下下一个部分吧

用户已概括 open_turn 的用途；operation 的调度关系仍保留为未完全理解，不据继续阅读标为掌握。

## 尚不清楚

- Proxy 内部的 _TurnScope 与请求计数机制仍暂缓。
- 内层 operation 与所属循环的调度关系仍可回访；用户当前选择继续主线。
- 路由 ACTIVE 后的 HTTP 分派，已进入 [_GatewayASGI._handle_http](_GatewayASGI._handle_http.md#gateway-http-mainline)。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对 AttemptHandle.__init__:262–264 与 open_turn:292–306；调用方为 plugin.py:703。
- RolloutLLMProxy.open_turn:118–122 创建本轮 _TurnScope，属于本轮只认输入效果的下游；未另建公共 Proxy 卡。
- 本次仅静态读源码，没有实际激活路由、创建任务或请求模型。
- [本轮记录](../../../../../../../step-014-model-routing-and-api-contract/04-flow.md#open-turn-short-read)。

</details>
