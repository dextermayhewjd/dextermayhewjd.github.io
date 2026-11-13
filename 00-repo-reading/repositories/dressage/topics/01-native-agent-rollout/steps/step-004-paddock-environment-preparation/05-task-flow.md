# 05 · 环境需求怎样交成可继续使用的 state

> Paddock.init 接收本次执行标识与环境需求，构造 spec，交给 provider 取得 lease；取得服务入口并按配置检查健康后，保存环境记录、返回 state，让 generate 可以继续注册 Agent。

[本步 scope](01-scope.md) · [本步记录](02-short-term-memory/overview.md) · [本次收束](04-flow.md#step001-closure) · [项目当前接续](../../../../README.md)

## 1. 本步在任务中的位置

Step 000 建立了 generate 的整体交接。本步只展开其中预热未命中后的环境准备：调用方已有 session_id、环境类型和 env_args，从 generate:222 调用 Paddock.init，得到 state 后继续 register_agent。

本步关注共同接口与正常路径。provider 可以创建新环境，也可以从已有资源中领取；当前没有实现或部署 Kubernetes 后端。具体 local_bwrap 代码保留为参考，不属于本步必须逐层读完的内容。

## 2. 已读部分怎样完成交接

以下是职责与数据交接图，编号对应 scope 的三个主要阶段；省略参数细节和异常分支，完整代码在函数卡中。

```text
blackbox_dispatch.generate:222
  -> BlackboxAgentPaddock.init
     |
     +- 1. environment request                    71-85
     |     -> merge env_args
     |     -> spec = SandboxSpec(...)
     |          services: SandboxServiceSpec(...)
     |
     +- 2. acquire environment and endpoint        86-116
     |     -> create_task = asyncio.create_task(...)
     |          runs: provider.create(spec)
     |     -> lease = await asyncio.shield(create_task)
     |     -> endpoint = lease.endpoints.get("blackbox")
     |          if missing:
     |            endpoint = await provider.get_public_url(...)
     |            lease.endpoints["blackbox"] = endpoint
     |     -> endpoint = endpoint.normalized()
     |     -> if _wait_health: await client.health(endpoint)
     |
     +- 3. save and return state                   117-151
           -> state = SandboxState(...)
           -> self._leases[traj_id] = lease
           -> self._states[traj_id] = state
           -> return state
  <- state
  -> initialized = True                           229
  -> paddock.register_agent(state, ...)            233; next handoff
```

1. **需求整理**：spec 描述要什么环境，内部服务描述说明要访问什么服务；创建这些 Python 对象本身没有创建运行环境。
2. **环境与访问入口**：provider.create 的正常返回值是 lease；已有 endpoint 就复用，缺少时才补取。normalized 只整理数据，health 才发 HTTP 请求。
3. **交付给上层**：Paddock 保存 lease 与 state，返回 state；provider 的环境记录与 Paddock 对外的访问状态各有用途。

对应函数：[init](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md) · [provider.create](02-short-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.create.md) · [get_public_url](02-short-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md) · [health](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.health.md)。

数据类型：[SandboxSpec](02-short-term-memory/classes/dressage/sandbox/types.py/SandboxSpec.md) · [SandboxServiceSpec](02-short-term-memory/classes/dressage/sandbox/types.py/SandboxServiceSpec.md) · [SandboxLease 与 Endpoint](02-short-term-memory/classes/dressage/sandbox/types.py/SandboxLease.md) · [SandboxState](02-short-term-memory/classes/dressage/paddock/blackbox/common/state.py/SandboxState.md)。

## 3. 本步结果是什么，交给谁

用户用“从 provider 拿到 handle，环境准备好了”概括这一层，方向正确；源码中把它分成两次交付：

| 交付 | 实际对象 | 后续使用方 |
| --- | --- | --- |
| provider → Paddock.init | SandboxLease：环境身份、能力、服务入口与后端资料 | init 取得 endpoint，并保存 lease 以支持后续操作与回收 |
| Paddock.init → generate | SandboxState：本次归属、服务 URL、环境标识与摘要 | generate 继续调用 register_agent、随后才执行 Agent |

init 最后的三个动作是：

```python
self._leases[traj_id] = lease
self._states[traj_id] = state
return state
```

正常返回意味着本次初始化路径已经完成。若启用了健康检查，还表示这次 /health HTTP 调用无异常结束；关闭检查时不能附加这一结论。它不自动证明题目全部初始化完成、Agent 已执行或结果正确。

环境是在本步取得的，不要求每次都全新创建。生命周期也没有在返回 state 时结束，后续仍要使用并最终释放它。

## 4. 本步收束与后续衔接

用户在补清实例索引与 state 后，已[确认 init 看完](04-flow.md#step001-reading-complete)。按既定“共同接口、正常交接”的深度，本步完成阅读并收束。用户已表达对环境取得的总体认识；lease 与 state 的精确交付区别由助手在本次补齐，不将其记成用户已经逐项复述。

以下内容保留未知，不为了结束本步继续扩张阅读范围：

1. Kubernetes 或其他后端的实际部署、调度、网络和完整失败恢复。
2. 具体实现支持哪些可选参数，以及所有取消、重复调用和资源释放边界。
3. Agent 注册与执行、模型交互、轨迹和训练样本处理。

接回原主线后，下一处候选是 [BlackboxAgentPaddock.register_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L153)：已有 state，怎样把 Agent 类型、任务身份和 Proxy 地址配置到环境中。当前仅标出下一交接，没有创建下一步或函数卡。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- [init:64-151](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L64)；[调用方:222-241](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L222)。
- [health:49-58](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L49)；共同接口 sandbox/provider.py；数据类型 sandbox/types.py 与 paddock/blackbox/common/state.py。
- 本次原话、理解边界与修正见 [04-flow](04-flow.md#step001-closure)。总结由助手按已发生的阅读整理，不替用户宣称所有机制已掌握。
- 此前有隔离的取消交接实验，使用模拟 provider，无真实沙箱；本次只核对源码与记录，没有执行部署、健康请求或训练。

</details>
