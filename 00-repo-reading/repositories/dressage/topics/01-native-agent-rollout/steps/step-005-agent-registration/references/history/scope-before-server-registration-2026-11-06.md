> 2026-11-06：加入服务端首次注册阅读前的范围快照；不代表当前阅读入口。

# 01 · Dressage Step 005：已有环境怎样完成 Agent 注册准备

> 编号调整：本目录由 Step 002 顺延为 Step 005。正文中的早期编号、原话及记忆快照保留历史语境；现行顺序见[编号与范围对照](../../../../../../step-numbering-2026-11-05.md)。

[本步入口](../../README.md) · [项目当前接续](../../../../../../README.md) · [Step 004（原 001） 总结](../../../step-004-paddock-environment-preparation/05-task-flow.md) · [本步阅读顺序](#reading-navigation)

## 1. 本步目标

**已经有可访问的环境，怎样把 Agent、任务身份和模型代理配置交给 BlackboxServer，并接上执行前的准备？**

本步对应 Step 000 第 3 段“注册准备”。主读 Paddock.register_agent；前置命令和 Proxy 会话登记先看用途与先后，停止在 call_agent 真正执行任务之前。

1. 看清 state 怎样定位同一环境的 endpoint。
2. 看清注册请求带入什么身份与配置、发给哪个服务。
3. 分清 BlackboxServer 的 Agent 注册与 Dressage Proxy 的会话登记，接回 generate 的执行前位置。

## 2. 入口、已有输入与边界

**首读入口：[BlackboxAgentPaddock.register_agent，153–182 行](restart-from-callsite-2026-11-06/02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md)。** 本步的编排段仍在 blackbox_dispatch.generate:232–255；后面的前置命令和 Proxy 登记是 generate 中的同级调用，不属于 Paddock.register_agent 的内部。

场景承接 Step 004：init 已正常返回 SandboxState，Paddock 的 _leases/_states 中保留本次记录。采用正常注册路径；没有实际启动服务或发出请求。create、健康检查及具体环境后端只作前序背景，不重新展开。

| 进入时已有的内容 | 来源与本步用途 |
| --- | --- |
| [state](restart-from-callsite-2026-11-06/02-short-term-memory/classes/dressage/paddock/blackbox/common/state.py/SandboxState.md) | init 返回的访问资料，提供轨迹归属、环境标识和服务 URL |
| paddock 及其记录 | 沿用同一个 BlackboxAgentPaddock 实例，可按 trajectory_id 找回 lease；不是每次注册再创建环境 |
| instance_id、session_id | generate 先前从 sample 整理出的题目和执行会话标识；本步关注传给谁 |
| blackbox_type、backend_options | generate 先前选择和整理的 Agent 后端配置；细项按需要回查 |
| router_url=proxy_url() | 模型请求代理的地址；与访问 BlackboxServer 的环境 endpoint 分开理解 |
| execute_cmd_schedule、proxy_client | generate 已准备的前置命令计划和 Proxy 客户端，供后两项配套调用使用 |

## 3. 上层背景与本步阅读

<a id="whole-flow"></a>

### 3.1 回到 generate：本步位于注册与执行前准备

> [Step 000 系统全景](../../../step-000-slime-bridge-and-interfaces/01-scope.md#whole-flow) → [generate 主线](restart-from-callsite-2026-11-06/02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md) → **Step 005：注册准备**。

本步与 init 是 generate 中的同级环节，因此继续使用 generate 作上层背景，而不把上一轮 init 内部的流程当作注册的父流程。下面继承同一份正常路径骨架，只标 Step 范围；本步内部编号从 3.2 开始。

```python
# Teaching skeleton: normal path, no prewarmed handle.
session_id = ensure_blackbox_session_id(...)
instance_id = _instance_id(...)
env_args = paddock_env_args_from_metadata(...)
initialized = False
paddock = None
try:
    proxy_client = get_proxy_client()
    handle = await claim_prewarm(...)
    ...  # Select the miss branch and renew session_id.
    paddock = get_paddock_from_env(...)
    state = await maybe_await(paddock.init(...))    # Step 004: environment preparation
    initialized = True

    # Step 005: Agent registration and pre-call preparation
    await maybe_await(paddock.register_agent(...))
    await execute_blackbox_cmds_for_stage(...)     # before_agent
    register_session_context = getattr(proxy_client, "register_session_context", None)
    if callable(register_session_context):
        await maybe_await(register_session_context(...))

    # End Step 005: call_agent belongs to the next execution scope
    call_payload = await maybe_await(paddock.call_agent(...))
    agent_response = agent_response_text(call_payload)

    await execute_blackbox_cmds_for_stage(...)
    await proxy_client.finalize_session(...)
    trajectory_payload = await proxy_client.read_trajectory(...)
    segments = trajectory_payload.get("data") or []
    result = multi_segment.expand_segments_to_samples(...)
    return result                                 # returned after finally
finally:
    if initialized and paddock is not None:
        schedule_terminate_paddock(...)
```

教学裁剪省略参数、会话标志及部分错误处理。Agent 运行期间的模型请求和后续回收仍在整体流程中，但不属于本步的注册准备。完整行为返回各自源码核对。

<a id="reading-navigation"></a>
<a id="current-excerpt"></a>

### 3.2 本步内部阅读顺序：先注册，再完成配套准备

**当前展开第 1 项 Paddock.register_agent。** 已建立独立函数卡；前置命令与 Proxy 登记仍按后续顺序推进。

下列代码来自 generate:232–255 的正常路径；参数按 scope 约定省略，关键会话标志保留：

```python
await maybe_await(paddock.register_agent(...))      # [1] register Agent with BlackboxServer
await execute_blackbox_cmds_for_stage(...)         # [2] before_agent commands
register_session_context = getattr(
    proxy_client, "register_session_context", None
)
if callable(register_session_context):
    context_owned = True
    await maybe_await(register_session_context(...))  # [3] register context with Proxy
# Stop before call_payload = await maybe_await(paddock.call_agent(...)).
```

第 1 项需要先辨认的局部骨架，来自 Paddock.register_agent:165–182：

```python
state = self._resolve_state(...)
lease = self._leases.get(state.trajectory_id)
endpoint = self._endpoint_for_state(...)
router = _validate_public_proxy_url(...)
blackbox_type = normalize_blackbox_type(...)
return await self._client.register_agent(...)
```

这里的 self 是 Paddock，self._client 是 BlackboxServerClient。endpoint 用来访问环境中的 BlackboxServer；router 是传给注册过程的模型代理地址。两者承担不同方向的通信。

| 本步顺序 | 阅读入口 | 本轮要弄清什么 | 读完返回哪里 |
| --- | --- | --- | --- |
| **1. Agent 注册：首读** | [Paddock.register_agent](restart-from-callsite-2026-11-06/02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md) | state 怎样接回 lease/endpoint；任务身份、Agent 类型和代理地址怎样交给客户端 | 返回 generate:232；调用方不绑定响应字典，随后执行 before_agent 命令 |
| 1.1 注册请求：当前 | [BlackboxServerClient.register_agent](restart-from-callsite-2026-11-06/02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md) | 客户端怎样组装请求并发向 BlackboxServer 的 /v1/rollout/register | 响应沿 Paddock.register_agent 返回；不展开全部重试或服务端后端实现 |
| 2. 前置命令：先按接口看 | [execute_blackbox_cmds_for_stage](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/execute_hooks.py#L77) | stage=before_agent 的命令在 Agent 调用前执行；没有配置时可为空 | 返回 generate:250，进入 Proxy 会话登记 |
| 3. Proxy 会话登记：先按接口看 | [ProxyClient.register_session_context](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L95) | 与第 1 项是不同服务上的登记；只在客户端提供该方法时调用，context_owned 供后续清理使用 | 返回 generate:255，接下来才进入 call_agent |

**本步结束时应能说明**：环境没有被再次创建，注册请求通过环境入口交给 BlackboxServer；可选前置命令随后执行；Proxy 会话上下文在调用 Agent 前登记。注册准备完成不等于 Agent 已经执行题目。

**停止位置**：generate:255 之后、call_agent 之前。具体 Agent 后端怎么运行、服务端完整注册实现、模型请求和轨迹收集留到后续问题；不因这里出现名称就预建函数卡。

<details>
<summary>来源、参数来路与记录范围</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本机 /home/fredkeira/projects/Dressage，核对时源码工作区干净。
- 编排来源：[generate:232–255](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L232)；身份和配置来路：138–179 行；state 来路：222–229 行。
- 主读与配套调用的固定源码入口见表格。骨架是教学裁剪，不是可独立执行的完整程序。
- [03](../../03-long-term-memory/overview.md)接续 Step 001–004 的累计记录，共 23 张函数/类卡；旧的十张准备快照另行归档；[02](restart-from-callsite-2026-11-06/02-short-term-memory/overview.md)已调入 generate、SandboxState 与 SandboxLease，新增当前注册函数卡；其余未读调用不预建卡。
- [本步确认与建立](../../04-flow.md#step002-created)。没有运行 Agent、网络注册或训练，不将 scope 建立记为理解完成。

</details>
