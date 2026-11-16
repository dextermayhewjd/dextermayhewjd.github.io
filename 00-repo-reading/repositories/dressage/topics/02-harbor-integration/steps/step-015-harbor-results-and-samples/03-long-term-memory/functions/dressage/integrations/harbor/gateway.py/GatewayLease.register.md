# GatewayLease.register

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayLease.register.md) 完整继承；不改变原认识时间或掌握状态。

- 源码：[gateway.py:389–392](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L389)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独展开：Step 014，2026-11-13。
- 最近认识更新：本轮开始阅读，尚无本函数内部的个人复述。

[_on_start 的登记调用](../plugin.py/DressageHarborPlugin._on_start.md#trial-start-mainline) → **当前 GatewayLease.register** → [GatewayRuntime.call](GatewayRuntime.call.md#runtime-call-mainline) 调度 GatewayRuntime._register → 返回 AttemptHandle。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：_on_start 已准备好本次 Trial 的路由资料 spec，要通过已有租约提交登记。
2. **具体内容**：检查租约是否释放，将登记操作交给 Runtime 执行，原样交回结果。
3. **建议构建的心智模型**：

   > 租约提供登记入口，Runtime 负责实际登记。

4. **调用代码**（_on_start:691–692）：

   ```python
   record.handle = await self._lease.register(spec)  # 当前进入，等待操作对象返回。
   record.phase = AttemptPhase.READY                # 返回后由调用方更新状态。
   ```

## 本场景的输入与输出

`self` 是 on_job_start 通过 runtime.acquire 取得的 GatewayLease，持有 Runtime 的引用；`spec` 是上一层准备的 RouteSpec，带有本次尝试身份、token 和路由配置。正常返回 `AttemptHandle`，由 `_on_start` 存到 `record.handle`。

<a id="lease-register-mainline"></a>

完整函数，仅调整换行、补充注释：

```python
async def register(self, spec: RouteSpec) -> AttemptHandle:
    if self._released:
        raise GatewayError("gateway lease is already released")

    return await self._runtime.call(
        lambda: self._runtime._register(spec)  # 把这次登记操作交给 Runtime 调度。
    )
```

`lambda` 将“执行 _register(spec)”这个操作交给本次 `runtime.call`；后者在 Gateway 所属事件循环执行它，并等待结果。当前进入 [GatewayRuntime.call](GatewayRuntime.call.md#runtime-call-mainline) 看执行位置与结果返回；实际登记业务现从 [GatewayRuntime._register](GatewayRuntime._register.md#runtime-register-mainline) 继续。

返回 [_on_start](../plugin.py/DressageHarborPlugin._on_start.md#trial-start-mainline) 后，调用方保存 handle、标记 READY，再返回 Trial 的 START 事件分发。

## 我的直接表述（原话）

> 好的 那么看一下这里的这个gatewaylease register吧

本轮确认入口，尚无对实现的个人复述。

## 尚不清楚

- GatewayRuntime._register 如何创建 Proxy、保存路由并返回 handle，下一层再看。
- runtime.call 的正常调度已进入子卡；取消和异常传递细节仍暂缓。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对 GatewayLease.__init__:368–371、register:389–392，以及调用方 plugin.py:691–692。
- GatewayRuntime.call:506–577 在同一所属循环时直接等待 operation()，否则把操作调度到所属循环再取回结果；本轮只核对这层职责，不把其线程/取消实现列为已读。
- 实际登记入口为 GatewayRuntime._register:594–633；本函数没有自己构造新的 AttemptHandle，而是返回下游结果。
- 仅静态阅读，没有启动线程、创建路由或运行模型。[本轮记录](../../../../../../../step-014-model-routing-and-api-contract/04-flow.md#gateway-lease-register-entry)。

</details>
