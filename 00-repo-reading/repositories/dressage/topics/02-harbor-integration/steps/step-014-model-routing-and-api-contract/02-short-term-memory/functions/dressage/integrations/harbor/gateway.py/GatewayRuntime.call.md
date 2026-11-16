# GatewayRuntime.call

- 源码：[gateway.py:506–577](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L506)，Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独展开：Step 014，2026-11-13。
- 最近认识更新：用户追问 call 的具体职责，当前开始阅读，尚未复述内部机制。

[GatewayLease.register](GatewayLease.register.md#lease-register-mainline) → **当前 GatewayRuntime.call** → 执行传入的 operation → 结果交回 register。

**这次为什么看 call**：为了接清“当前 Trial 的模型请求路由怎样登记”，从 _on_start 的 lease.register 走到了这里。call 只负责执行位置与结果返回，路由业务仍在 _register；可先从 [scope 的问题来路](../../../../../../01-scope.md#routing-reading-purpose) 恢复背景。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：GatewayRuntime 管理自己的后台线程和事件循环；租约调用方可能处在另一个循环，需要把登记操作交过去执行。
2. **具体内容**：若已在网关循环，直接 await 操作；否则投递到网关循环，用 Future 把结果或错误传回。
3. **建议构建的心智模型**：

   > 调用方提出“登记这条路由”，网关循环负责执行，call 等待并交回结果。

4. **调用代码**（GatewayLease.register:392）：

   ```python
   return await self._runtime.call(
       lambda: self._runtime._register(spec)  # 本次传入的 operation。
   )
   ```

## 本场景的输入与输出

`runtime` 是 GatewayRuntime 对象，`call` 是项目定义的异步方法。输入 operation 是上面的无参函数；调用 `operation()` 得到 _register(spec) 的协程，再等待或安排它执行。正常返回该操作的结果，本次就是 AttemptHandle，最终存入 _on_start 的 record.handle。

<a id="runtime-call-mainline"></a>

### 1. 先确认该在哪里执行

```python
loop = self._loop  # 网关后台线程中已经运行的事件循环。
# 原码先检查这个循环是否仍在运行。
current_loop = asyncio.get_running_loop()
if current_loop is loop:
    return await operation()  # 已经在正确循环，直接执行并交回结果。
```

### 2. 不在同一循环：交过去执行，再等结果

下面是成功路径裁剪，省略取消、错误传递和状态竞态保护；完整实现折叠保留。

```python
result: concurrent.futures.Future[Any] = concurrent.futures.Future()

def submit() -> None:  # 这个回调将在网关循环里执行。
    task = loop.create_task(operation())  # 本例实际运行 _register(spec)。

    def completed(done: asyncio.Task[Any]) -> None:
        result.set_result(done.result())  # 将登记返回的 handle 放入结果对象。

    task.add_done_callback(completed)

loop.call_soon_threadsafe(submit)          # 把 submit 投递到网关循环。
return await asyncio.wrap_future(result)  # 调用方异步等结果，再交回 register。
```

这里安排的是本次操作执行，不是登记一个以后由 TrialEvent 触发的生命周期钩子。本轮先接清“在哪执行、结果怎样回来”，实际登记业务进入 [GatewayRuntime._register](GatewayRuntime._register.md#runtime-register-mainline)；调度失败与取消细节暂不展开。

<details>
<summary>完整函数：循环检查、错误传递、取消与竞态保护</summary>

```python
async def call(self, operation: Callable[[], Awaitable[Any]]) -> Any:
    loop = self._loop
    if loop is None or not loop.is_running():
        raise GatewayError("gateway owner loop is not running")
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:  # pragma: no cover - this is an async API
        current_loop = None
    if current_loop is loop:
        return await operation()

    result: concurrent.futures.Future[Any] = concurrent.futures.Future()
    cancel_requested = threading.Event()
    owner_task: list[asyncio.Task[Any] | None] = [None]

    def submit() -> None:
        if result.done() or cancel_requested.is_set():
            result.cancel()
            return
        try:
            task = loop.create_task(operation())
        except BaseException as exc:
            if not result.done():
                result.set_exception(exc)
            return
        owner_task[0] = task
        if cancel_requested.is_set():
            task.cancel()

        def completed(done: asyncio.Task[Any]) -> None:
            if result.done():
                # Retrieve the exception to avoid an owner-loop
                # "Task exception was never retrieved" warning.
                if not done.cancelled():
                    done.exception()
                return
            try:
                if done.cancelled():
                    result.cancel()
                else:
                    error = done.exception()
                    if error is not None:
                        result.set_exception(error)
                    else:
                        result.set_result(done.result())
            except concurrent.futures.InvalidStateError:
                # The caller can be cancelled between the done() check and
                # this cross-thread state transition.
                pass

        task.add_done_callback(completed)

    try:
        loop.call_soon_threadsafe(submit)
    except RuntimeError as exc:
        raise GatewayError("gateway owner loop stopped during dispatch") from exc
    try:
        return await asyncio.wrap_future(result)
    except asyncio.CancelledError:
        cancel_requested.set()
        result.cancel()

        def cancel_owner_task() -> None:
            task = owner_task[0]
            if task is not None and not task.done():
                task.cancel()

        try:
            loop.call_soon_threadsafe(cancel_owner_task)
        except RuntimeError:
            pass
        raise
```

</details>

## 我的直接表述（原话）

> 好的 这里就是一个lease的register
> 让这里的runtime call?
> 我其实不是很理解这里的runtime call具体是什么
> 我觉得是否需要查看一下呢?

本轮先解释 call 的执行与返回职责，未将问题记为已掌握跨线程调度。

## 尚不清楚

- GatewayRuntime._register 的路由/Proxy 创建与 handle 构造，仍是下一层业务。
- 跨循环的取消、Future 状态保护与线程同步的细节暂缓。

<details>
<summary>来源与验证</summary>

- 本地固定提交核对 call:506–577、GatewayLease.register:389–392。
- _start_blocking:710–728 创建后台线程；_thread_main:730–750 创建并运行 self._loop。这里只核对操作执行位置，不展开线程生命周期。
- concurrent.futures.Future 用于跨线程传递结果，asyncio.wrap_future 将它接入调用方的异步等待；代码节选仅覆盖成功路径，不能替换完整实现。
- 未运行线程、路由登记或取消实验。[本轮记录](../../../../../../04-flow.md#gateway-runtime-call-entry)。

</details>
