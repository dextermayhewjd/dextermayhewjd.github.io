# Step 005 · 3.2 候选：连续代码骨架与面包屑导航

**状态：2026-11-07 经用户确认，已采用到当前 scope 的 3.2。** 当前短期目录继续保持清空后的状态，不恢复旧卡，也不预建新卡。

[当前 scope](../01-scope.md#reading-navigation) · [早期的“代码骨架＋编号表”版本](history/scope-before-server-registration-2026-11-06.md#reading-navigation)

## 调整原则

1. 恢复此前 3.2 的呈现方式：连续代码骨架、短注释、编号对应的源码导航。
2. 保留调用与返回的面包屑。表格只回答“进入哪个函数、从哪里进入、回来接哪里”，不把每行写成一项学习任务。
3. 3.1 完整主线不变。3.2 当前从 Paddock.register_agent 开始，Client 和服务端保留为后续下钻位置；详细参数、机制和个人理解进入实际重读后的函数卡。

以下分隔线内是建议替换进 scope 的正文。

---

### 3.2 本步调用骨架与阅读导航

[generate:232 的调用处](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L232) → **[BlackboxAgentPaddock.register_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L153)（当前入口 [1]）**。

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
| **1 · 当前** | [BlackboxAgentPaddock.register_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L153) | generate:232 的注册调用 | generate:242 的 [2] |
| 1.1 | [BlackboxServerClient.register_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/client.py#L60) | Paddock.register_agent:170 的 self._client 调用 | Paddock.register_agent 的 return |
| 1.2 | [register_rollout](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/api/rollout.py#L18) | HTTP /v1/rollout/register 路由 | HTTP 回复返回 [1.1] |
| 1.3 | [BlackboxServer.register](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L241) | register_rollout:22 的 server.register 调用 | register_rollout 接收响应 |
| 1.3.1 | [ClaudeCodeAdapter.initialize](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/adapters/claude_code.py#L291) | server.register 中的 adapter.initialize 调用；仅列 Claude Code 分支 | 回到 server.register 保存绑定并继续处理 |
| 2 | [execute_blackbox_cmds_for_stage](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/execute_hooks.py#L77) | generate:242，stage 为 before_agent | generate:250 |
| 3 | [ProxyClient.register_session_context](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L95) | generate:255，仅接口存在时调用 | generate，随后将进入 call_agent |

Paddock 内遇到具体卡点时，再从相应调用处回查 [_resolve_state](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L299) 或 [_endpoint_for_state](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L311)，看完返回原语句之后；它们不另构成强制阅读清单。

**返回方向**：具体初始化返回服务端；服务端响应通过 HTTP 回到客户端；客户端的字典结果返回 Paddock，再回到 generate 的 [2]。这里描述的是一条注册调用链，不是多次独立注册。

**当前边界**：先读 [1]，再按实际调用下钻 [1.1]，不跳过它们直接从 [1.3] 开始。服务端先选首次成功注册路径；重绑定、重试、安装部署等只在必要时回查。每次展开保留原调用位置，结束后回到主链。本步最终停在 call_agent 之前。

当前所有入口先链接固定版本源码；确认重读并建立新函数卡后，再把对应入口接到本步卡片。不会因图中出现函数名就提前建卡或标记掌握。

---

## 如果采用，实际只调整哪些内容

1. 替换当前 scope 的 3.2；3.1 的整体骨架不改。
2. 表格继续保留轻量的调用/返回定位，去掉详细讲解式的“每步要学会什么”。
3. 仍从 generate 的调用处定位到 Paddock.register_agent，保持从头重读的要求。
4. 02-short-term-memory 继续只有空索引；旧卡保留在历史归档，等待实际重读后逐张新建。

源码依据：Dressage 固定提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。上述 Python 片段是导航裁剪，不是完整可运行程序；HTTP 图用于标明进程边界，源码行号和符号已核对。本文件只提出展示方案，不推进阅读状态。
