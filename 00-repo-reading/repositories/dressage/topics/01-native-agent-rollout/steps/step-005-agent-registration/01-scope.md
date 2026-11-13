# 01 · Dressage Step 005：已有环境怎样完成 Agent 注册准备

> 编号调整：本目录由原 Step 002 顺延。当前按用户要求重新阅读本步；前序学习历史保留。

> 2026-11-07：本步已按此范围完成首轮阅读收束，[task flow](05-task-flow.md)连接三个阶段；下方保留原阅读路径和最后停靠位置，实时接续以项目入口为准。

[本步入口](README.md) · [项目进度](../../../../README.md) · [Step 004 总结](../step-004-paddock-environment-preparation/05-task-flow.md) · [当前起点](#reading-navigation)

## 1. 本步目标

**环境已经取得后，为什么还要调用 register_agent，这次调用如何让服务端完成 Agent 运行准备？**

本步仍属于 generate 的注册准备段。旧短期卡已清空，不把 Paddock 和 Client 层当成已理解；先从调用现场建立输入、接收者与后续用途，再逐层进入实现。

## 2. 当前入口与边界

**先打开 generate:232–241 的注册调用，再进入 BlackboxAgentPaddock.register_agent。** 本轮不直接从 BlackboxServer.register 开始。

固定一个教学场景：init 已返回 state，已有可访问的 BlackboxServer，采用 Claude Code 首次注册。Agent 程序由运行环境提供是场景前提；安装位置保留为后续按需回查，不混入每个参数的解释。

先前的 state、lease、Paddock 只是可回顾背景，不要求读者一次记住所有字段。当前先回答：谁发起调用、手里已有何物、交给谁、调用结束后往哪里走。

## 3. 上层背景与本步阅读

<a id="whole-flow"></a>

### 3.1 回到 generate：本步位于注册与执行前准备

> [Step 000 系统全景](../step-000-slime-bridge-and-interfaces/01-scope.md#whole-flow) → [generate 主线](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L116) → **Step 005：注册准备**。

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

### 3.2 本步调用骨架与阅读导航

**本次接续（2026-11-07）：** 从 [1.3.1] initialize 返回 [1.3] register 的[保存与响应](02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.register.md#after-initialize)，再回到 generate 看 [2] 前置命令和 [3] Proxy 会话登记。本轮已补这两处卡片，仍停在 call_agent 之前；首次说明不等于本步已掌握或完成。

本次从 [2.1 _execute_blackbox_cmd](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md) 返回 [2] 的命令循环，再回到 generate。**最后停靠 [3] ProxyClient.register_session_context**，对应 generate:250–255 的调用处；[2.1] 内部的 paddock.execute_cmd 仍按接口交接理解。

[generate:232 的调用处](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L232) → **[BlackboxAgentPaddock.register_agent](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md)（本轮起点 [1]）**。

先在下面的 generate 片段定位 [1]，再进入 Paddock 方法。编号用于把调用位置与下方入口对应起来，不代表这些函数已经读过。

**本步在 generate 中的连续片段：**

```python
# 教学裁剪：保留注册及其后的实际调用顺序，省略参数。
await maybe_await(paddock.register_agent(...))       # [1] Agent 注册
await execute_blackbox_cmds_for_stage(...)          # [2] 执行前置命令
register_session_context = getattr(
    proxy_client, "register_session_context", None
)
if callable(register_session_context):
    context_owned = True
    await maybe_await(register_session_context(...)) # [3] Proxy 会话登记
# 本步停在后面的 call_agent 之前。
```

**从 [1] 进入 Paddock.register_agent：**

```python
# Paddock.register_agent:165–182，参数省略；self 是 Paddock 对象。
state = self._resolve_state(...)
lease = self._leases.get(state.trajectory_id)
endpoint = self._endpoint_for_state(...)
router = _validate_public_proxy_url(...)
blackbox_type = normalize_blackbox_type(...)
return await self._client.register_agent(...)       # [1.1] 交给客户端
```

此处 self._client 是 BlackboxServerClient。客户端发出的请求跨 HTTP 到达服务端；这段关系用调用图表示，不把服务端伪装成客户端内部的普通 Python 调用。具体 Agent 下钻固定以 Claude Code 为例。

```text
[1] BlackboxAgentPaddock.register_agent
  -> [1.1] BlackboxServerClient.register_agent
       -> [1.1.1] BlackboxServerClient._post_agent_with_retry
       == HTTP POST /v1/rollout/register ==>
          [1.2] register_rollout
            -> [1.3] BlackboxServer.register
                 -> [1.3.1] ClaudeCodeAdapter.initialize
                 <-
            <-
       <== HTTP response ==
  <- response dict
  -> generate continues at [2]
```

**编号对应的函数入口与返回位置：**

| 编号 | 源码入口 | 从哪里进入 | 返回后接哪里 |
| --- | --- | --- | --- |
| 1 | [BlackboxAgentPaddock.register_agent](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md) | generate:232 的注册调用 | generate:242 的 [2] |
| 1.1 | [BlackboxServerClient.register_agent](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md) | Paddock.register_agent:170 的 self._client 调用 | Paddock.register_agent 的 return |
| 1.1.1 | [BlackboxServerClient._post_agent_with_retry](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._post_agent_with_retry.md) | 客户端 register_agent:88 | 返回 HTTP 响应，由 register_agent:95 解析 |
| 1.2 | [register_rollout](02-short-term-memory/functions/blackbox_server/api/rollout.py/register_rollout.md) | HTTP /v1/rollout/register 路由 | HTTP 回复返回 [1.1] |
| 1.3 | [BlackboxServer.register](02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.register.md) | register_rollout:22 的 server.register 调用 | register_rollout 接收响应 |
| 1.3.1 | [ClaudeCodeAdapter.initialize](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.initialize.md) | server.register 中的 adapter.initialize 调用；仅列 Claude Code 分支 | 回到 server.register 保存绑定并继续处理 |
| 2 | [execute_blackbox_cmds_for_stage](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md) | generate:242，stage 为 before_agent | generate:250 |
| 2.1 | [_execute_blackbox_cmd](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md) | [2] 的 for 循环，传入其中一条 command | 返回 [2]，继续下一条命令 |
| **3 · 本步停止位置** | [ProxyClient.register_session_context](02-short-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.register_session_context.md) | generate:255，仅接口存在时调用 | generate，随后将进入 call_agent |

Paddock 内遇到具体卡点时，再从相应调用处回查 [_resolve_state](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L299) 或 [_endpoint_for_state](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L311)，看完返回原语句之后；它们不另构成强制阅读清单。

**返回方向**：具体初始化返回服务端；服务端响应通过 HTTP 回到客户端；客户端的字典结果返回 Paddock，再回到 generate 的 [2]。这里描述的是一条注册调用链，不是多次独立注册。

**当前边界**：上方保留从 [1] 开始的完整调用链；本次从 initialize 返回后接续 [2]、[3]。服务端仍选首次成功注册路径；重绑定、重试、安装部署等只在必要时回查。每次展开保留原调用位置，结束后回到主链。本步最终停在 call_agent 之前。

当前 [1]、[1.1]、[1.1.1]、[1.2]、[1.3]、[1.3.1]、[2]、[2.1]、[3] 已链接实际接触后建立的函数卡；其余辅助入口仍链接固定版本源码。不会因图中出现函数名就提前建卡或标记掌握。

<details>
<summary>源码与历史边界</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，源码路径 /home/fredkeira/projects/Dressage。
- [前序累计记忆](03-long-term-memory/overview.md)保持原样；当前 [02](02-short-term-memory/overview.md)仅收录本轮重读后新建的卡片，不自动恢复旧卡。
- [重读前的 scope 与短期卡](references/history/restart-from-callsite-2026-11-06/README.md)仅作历史回查，不自动恢复到当前 02。
- 没有运行真实 Agent、注册请求或训练。

</details>
