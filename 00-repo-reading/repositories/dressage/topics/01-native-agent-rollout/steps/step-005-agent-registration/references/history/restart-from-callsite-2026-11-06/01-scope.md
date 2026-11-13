# 01 · Dressage Step 005：已有环境怎样完成 Agent 注册准备

> 编号调整：本目录由 Step 002 顺延为 Step 005。正文中的早期编号、原话及记忆快照保留历史语境；现行顺序见[编号与范围对照](../../../../../../../step-numbering-2026-11-05.md)。

[本步入口](../../../README.md) · [项目当前接续](../../../../../../../README.md) · [Step 004（原 001） 总结](../../../../step-004-paddock-environment-preparation/05-task-flow.md) · [本步阅读顺序](#reading-navigation)

## 1. 本步目标

**已经有可访问的环境，怎样把 Agent、任务身份和模型代理配置交给 BlackboxServer，并接上执行前的准备？**

本步对应 Step 000 第 3 段“注册准备”。沿已有 Paddock/客户端入口，当前转向 BlackboxServer 的首次注册和 Claude Code 初始化；前置命令和 Proxy 会话登记随后接回，停止在 call_agent 真正执行任务之前。

1. 看清 state 怎样定位同一环境的 endpoint。
2. 看清注册请求送达后，实际准备哪些目录、配置、代理服务与会话记录。
3. 分清 BlackboxServer 的 Agent 注册与 Dressage Proxy 的会话登记，接回 generate 的执行前位置。

## 2. 入口、已有输入与边界

**已有来路：[BlackboxAgentPaddock.register_agent](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md) → 客户端。当前下一入口是 [BlackboxServer.register](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L241)，按 3.2 的首次成功注册路径阅读。** 本步的编排段仍在 blackbox_dispatch.generate:232–255；后面的前置命令和 Proxy 登记是 generate 中的同级调用，不属于 Paddock.register_agent 的内部。

场景承接 Step 004：init 已正常返回 SandboxState，Paddock 的 _leases/_states 中保留本次记录。采用正常注册路径；没有实际启动服务或发出请求。create、健康检查及具体环境后端只作前序背景，不重新展开。

| 进入时已有的内容 | 来源与本步用途 |
| --- | --- |
| [state](02-short-term-memory/classes/dressage/paddock/blackbox/common/state.py/SandboxState.md) | init 返回的访问资料，提供轨迹归属、环境标识和服务 URL |
| paddock 及其记录 | 沿用同一个 BlackboxAgentPaddock 实例，可按 trajectory_id 找回 lease；不是每次注册再创建环境 |
| instance_id、session_id | generate 先前从 sample 整理出的题目和执行会话标识；本步关注传给谁 |
| blackbox_type、backend_options | generate 先前选择和整理的 Agent 后端配置；细项按需要回查 |
| router_url=proxy_url() | 模型请求代理的地址；与访问 BlackboxServer 的环境 endpoint 分开理解 |
| execute_cmd_schedule、proxy_client | generate 已准备的前置命令计划和 Proxy 客户端，供后两项配套调用使用 |

## 3. 上层背景与本步阅读

<a id="whole-flow"></a>

### 3.1 回到 generate：本步位于注册与执行前准备

> [Step 000 系统全景](../../../../step-000-slime-bridge-and-interfaces/01-scope.md#whole-flow) → [generate 主线](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md) → **Step 005：注册准备**。

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

### 3.2 本步内部阅读顺序：请求送达 → 服务端准备 → 返回调用方

**当前要解决的问题：注册请求到达以后，服务端实际新增了什么，凭什么可以继续接收题目？**

固定场景：已有可访问的 BlackboxServer，Claude Code 程序已由部署提供；这次是 blackbox_type="claude_code" 的首次成功注册。这里不安装 Agent，不混读 Codex/OpenCode 的初始化，也不展开重绑定、重试或失败恢复。

**下一处主读：[BlackboxServer.register](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L241)。** Paddock 与客户端两层保留为来路；先看服务端主干，到 adapter.initialize 时进入 ClaudeCodeAdapter.initialize，再带着实际结果返回。

下面是同一次注册的调用与阅读路径，HTTP 箭头表示跨服务请求；编号属于本步内部，不是新增 Step。

```text
[1] BlackboxAgentPaddock.register_agent
  -> [1.1] BlackboxServerClient.register_agent
       == HTTP POST /v1/rollout/register ==>
          register_rollout
            -> [1.2] BlackboxServer.register
                 -> [1.2.1] ClaudeCodeAdapter.initialize
                 <- runtime directories / proxy / settings ready
            <- register response
       <== HTTP response ==
  <- response dict
[1.3] return to generate
[2]   execute_blackbox_cmds_for_stage
[3]   register_session_context (when supported)
      -> stop before call_agent
```

1. **请求送达（1、1.1）**：确定环境入口，把本次身份和 Agent 配置发过去；这部分已有卡，按需回顾即可。
2. **服务端准备（1.2、1.2.1，当前重点）**：选出适配器，准备本次运行资料；以实际目录、代理服务、配置文件及会话记录的变化为观察点。
3. **返回主线（1.3、2、3）**：注册响应原路返回，然后执行前置命令、登记 Proxy 会话上下文；题目消息在后面的 call_agent 才提交。

| 本步位置 | 阅读入口 | 本轮需要看见的变化 | 返回哪里 |
| --- | --- | --- | --- |
| 1. Paddock 注册（来路） | [已有函数卡](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md) | 从 state 找 lease/endpoint，把身份和配置交给客户端 | 客户端注册方法 |
| 1.1 HTTP 请求（来路） | [已有客户端卡](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)；[接收路由](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/api/rollout.py#L18) | 参数成为 JSON 正文，POST 由路由交给 server.register | 进入服务端主干 |
| **1.2 服务端注册（下一处）** | [BlackboxServer.register:241](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L241) | 选择适配器、形成绑定资料；等待初始化；建立绑定会话并设为 READY | 注册响应通过路由交回客户端 |
| 1.2.1 具体初始化（从上行下钻） | [ClaudeCodeAdapter.initialize:291](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L291) | 运行目录、模型请求代理和 settings.json 被准备好；检查 Claude 可执行文件可用 | 回到 server.register 保存绑定、准备会话 |
| 1.3 响应回到 generate | [generate:232–241](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L232) | 调用方等待成功，不另接响应变量；此时尚未提交题目 messages | 下一行前置命令 |
| 2. 前置命令（后续） | [execute_blackbox_cmds_for_stage](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/execute_hooks.py#L77) | 执行配置中的 before_agent 命令，没有命令时为空 | generate:250 |
| 3. Proxy 会话登记（后续） | [ProxyClient.register_session_context](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L95) | 向 Dressage Proxy 登记会话；与 BlackboxServer 的 Agent 注册分开 | 停在 call_agent 前 |

<details>
<summary>按需回看：Paddock.register_agent 的局部骨架</summary>

```python
state = self._resolve_state(...)
lease = self._leases.get(state.trajectory_id)
endpoint = self._endpoint_for_state(...)
router = _validate_public_proxy_url(...)
blackbox_type = normalize_blackbox_type(...)
return await self._client.register_agent(...)
```

这里 self 是 Paddock，self._client 是 BlackboxServerClient。endpoint 是当前注册请求的目标；router 是传过去的模型代理地址。

</details>

返回 generate 后仍沿以下原顺序继续，保留实际条件；参数按 scope 约定省略：

```python
await maybe_await(paddock.register_agent(...))        # [1] 等待注册完成
await execute_blackbox_cmds_for_stage(...)           # [2] 执行前置命令
register_session_context = getattr(
    proxy_client, "register_session_context", None
)
if callable(register_session_context):
    context_owned = True
    await maybe_await(register_session_context(...)) # [3] 登记 Proxy 会话
# 本步停在 call_agent 之前。
```

**停止位置**：能沿一次首次成功注册说明“请求送到哪里 → 服务端与适配器实际准备了什么 → 回复后上层做什么”。不以记住全部参数为完成标准。Claude Code 真正处理题目的子进程在后续消息执行路径启动，当前只定位边界。

**暂不展开**：重复注册/重绑定规则、完整重试与取消恢复、其他 Agent 初始化、模型请求和轨迹算法。服务端与适配器的新卡在实际逐段阅读时再建立，源码入口不代表已经读懂。

<details>
<summary>来源、参数来路与记录范围</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本机 /home/fredkeira/projects/Dressage，核对时源码工作区干净。
- 编排来源：[generate:232–255](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L232)；身份和配置来路：138–179 行；state 来路：222–229 行。
- 本次增加服务端 register 与 ClaudeCodeAdapter.initialize 的正常路径；[调整前 scope](../scope-before-server-registration-2026-11-06.md)保留旧阅读边界。
- 主读与配套调用的固定源码入口见表格。骨架是教学裁剪，不是可独立执行的完整程序。
- [03](../../../03-long-term-memory/overview.md)接续 Step 001–004 的累计记录，共 23 张函数/类卡；旧的十张准备快照另行归档；[02](02-short-term-memory/overview.md)已调入 generate、SandboxState 与 SandboxLease，新增当前注册函数卡；其余未读调用不预建卡。
- [本步确认与建立](../../../04-flow.md#step002-created)。没有运行 Agent、网络注册或训练，不将 scope 建立记为理解完成。

</details>
