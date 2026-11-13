# process_parallel：长任务、完成边界与结果含义

[返回函数卡](reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/process_parallel.md#long-agent-lifetime) · [原始讨论](../04-flow.md#long-agent-lifetime)

源码版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。本页区分静态源码结论、本地受控实验和未验证的真实 Agent 行为。

## 1. ThreadPoolExecutor 等的究竟是什么

1. ex.submit(_one, task) 提交整个 _one，返回一个外层 Future。
2. 工作线程执行 fleet.acquire(task)，取得环境。
3. 工作线程调用 process_fn(task, handle)。这个同步调用可以执行很久；调用返回或抛错之前，线程仍停留在该任务中。
4. 回调退出后，_one 进入 finally，调用 fleet.release(handle)。
5. _one 整体退出后，外层 Future 才完成。正常路径中，as_completed 此时才交出它。
6. fut.result() 取得已经完成的 _one 的返回值，或重新抛出它的异常；它不是发起 Agent 执行的操作。

因此，持续很久的同步 Agent 回调可以放在这里运行，但会占用一个工作线程和所持环境。其他任务可以完成并写入 results；这个函数仍要等整批完成后才返回列表。

## 2. 回调的返回不自动等于 Agent 成功

| process_fn 的行为 | 当前执行器怎样处理 |
| --- | --- |
| 等待 Agent 到达约定结束点，返回结果记录 | _one 释放环境后，外层 Future 返回该记录 |
| 抛出 Exception | _one 尝试释放环境；外层收集处把异常放入对应结果位置 |
| 返回失败、超时或未完成的状态字典 | 作为普通返回值保存；本层不解释这些业务状态 |
| 只发起后台任务，立即返回任务 ID | 本层认为 Python 回调已返回，随即释放环境，不会根据 ID 继续轮询 |
| 返回另一个尚未完成的 concurrent.futures.Future | 把它当普通值返回，不递归等待其完成，随后仍释放环境 |

如果回调已经算出结果，但 finally 中的释放抛错，_one 仍可能以异常结束；不能把所有异常都直接解释为 Agent 答错。

当前接口的重要约定是：process_fn 要覆盖本次任务所需的执行、等待和结果收集生命周期。若其内部采用远端异步提交，就应在返回前完成所需等待与收集，或采用明确管理该异步生命周期的其他接口。

## 3. 仓库中的真实接入形态

OpenHands 示例的调用链是：

```text
process_parallel
  -> _one(task)
     -> process_fn(task, handle)
        -> _conversation(task, workspace)
           -> conversation.run()
           -> return execution_status
     -> fleet.release(handle)
```

实际回调由 examples/run_openhands_fleet.py 的 _rollout 返回。其 _conversation 在 conversation.run() 返回后才读取状态：

```python
conversation.send_message(_env("PROMPT", DEFAULT_PROMPT))
conversation.run()
return {"id": task.id, "mode": "conversation",
        "status": str(conversation.state.execution_status)}
```

这里的返回值已经包含业务状态，而不是执行器自动生成一个“成功”。具体何时返回、怎样理解 execution_status，需要接着核对所用 SDK 和回调；本次没有运行真实 Agent。

固定源码：[OpenHands 回调与 conversation:130](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/examples/run_openhands_fleet.py#L130)。

## 4. 这一层尚未承担的管理职责

1. process_parallel 本身没有为完整 Agent 回调设置 deadline；as_completed 和 fut.result 在此都未传 timeout。回调一直不结束，整批调用就可能一直等。
2. ready_timeout 与 claim_timeout 针对环境准备或领取，不等于整个 Agent 运行时限。
3. 本函数不提供增量结果流、自动重试、检查点恢复或按业务状态判定 reward。
4. 对 Future 的等待超时不等于终止正在运行的线程或远端进程。需要取消时，执行回调与远端环境还要有相应协议。
5. 本页分析的是同步 process_parallel。仓库另有 AsyncSandboxFleet._call，会识别协程函数及返回的 awaitable 并等待；不能把 async def 直接交给当前同步路径，并假定它会自动 await。

这些限制只针对本层，不表示仓库其他层没有超时、资源保护或诊断机制。具体能力应沿当前使用路径核对。

固定源码：[同步执行器:34](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L34)、[异步调用适配:230](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/async_fleet.py#L230)。

## 5. 本次受控验证

2026-11-04，从固定源码用 AST 原样提取 process_parallel 执行；替换 fleet 的领取、释放及观察对象，保留真实 ThreadPoolExecutor 与 Future。使用 threading.Event 控制一个回调何时返回，不访问集群。

1. 同时提交 long 和 short 两条任务。long 被 Event 阻塞，short 正常返回。
2. short 释放后，观察到 batch_done=False，released=["short"]。long 尚未释放。
3. 允许 long 返回后，整批结果顺序为 [long 的结果, short 的结果]，释放顺序为 ["short", "long"]。
4. 另让一个回调直接返回未完成的 Future。观察到执行器返回同一个 Future，其 done() 仍为 False，而该任务的环境已经被释放。

该实验验证 Python 层的等待、返回与释放关系，不验证真实 Agent 的完成判定、超时实现或 Kubernetes 的故障行为。
