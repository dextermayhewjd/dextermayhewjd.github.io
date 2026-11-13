> 2026-11-07 采用编号代码骨架方案前的 scope 快照。当前版本见 [Step 005 scope](../../01-scope.md)。

# 01 · Dressage Step 005：已有环境怎样完成 Agent 注册准备

> 编号调整：本目录由原 Step 002 顺延。当前按用户要求重新阅读本步；前序学习历史保留。

[本步入口](../../README.md) · [项目进度](../../../../../../README.md) · [Step 004 总结](../../../step-004-paddock-environment-preparation/05-task-flow.md) · [当前起点](#reading-navigation)

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

> [Step 000 系统全景](../../../step-000-slime-bridge-and-interfaces/01-scope.md#whole-flow) → [generate 主线](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L116) → **Step 005：注册准备**。

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

### 3.2 调用链与面包屑导航

[generate 的调用处](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L232) → **[BlackboxAgentPaddock.register_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L153)（本轮入口）**。

主链如下，省略参数与轻量配置辅助调用。HTTP 标记表示跨服务请求，之后的入口不是客户端直接调用的 Python 方法。

```text
blackbox_dispatch.generate:232
  -> BlackboxAgentPaddock.register_agent
       -> BlackboxServerClient.register_agent
            == HTTP POST /v1/rollout/register ==>
                 register_rollout
                   -> BlackboxServer.register
```

| 入口 | 从哪里进入 | 读完返回哪里 |
| --- | --- | --- |
| **[BlackboxAgentPaddock.register_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L153)** | generate:232 的注册调用 | generate:242，接前置命令 |
| [BlackboxServerClient.register_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L60) | Paddock.register_agent:170 的 self._client 调用 | Paddock.register_agent 的 return |
| [register_rollout](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/api/rollout.py#L18) | POST /v1/rollout/register 的服务端路由 | HTTP 响应返回客户端 |
| [BlackboxServer.register](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L241) | register_rollout:22 的 server.register 调用 | register_rollout，再返回 HTTP 响应 |

**Paddock 内的按需回查入口**，不是另一套必读步骤：

| 辅助函数 | 所在调用点 | 返回后的位置 |
| --- | --- | --- |
| [_resolve_state](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L299) | Paddock.register_agent:165 | 166 行查找 lease |
| [_endpoint_for_state](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L311) | Paddock.register_agent:167 | 168 行及后续客户端调用 |

注册返回后的主线仍是：

1. [generate:242](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L242) → [execute_blackbox_cmds_for_stage](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/execute_hooks.py#L77) → 返回 generate:250。
2. 接口存在时，[generate:255](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L255) → [ProxyClient.register_session_context](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L95) → 返回 generate，停在 call_agent 之前。

此处只保留从哪里进入、下钻到哪里、怎样返回；参数、字段与行为解释随实际重读写入对应函数卡。当前短期卡仍为空，以上源码入口不表示已读懂，也不会自动恢复旧卡。

<details>
<summary>源码与历史边界</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，源码路径 /home/fredkeira/projects/Dressage。
- [前序累计记忆](../../03-long-term-memory/overview.md)保持原样；当前 [02](../../02-short-term-memory/overview.md)只保留空索引。
- [重读前的 scope 与短期卡](restart-from-callsite-2026-11-06/README.md)仅作历史回查，不自动恢复到当前 02。
- 没有运行真实 Agent、注册请求或训练。

</details>
