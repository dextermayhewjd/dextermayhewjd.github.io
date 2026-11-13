# 05 · 任务链路：完成 Agent 注册与执行前准备

> 接住已经取得的沙箱和运行参数，完成 Agent 注册，执行配置好的前置命令，再向 Dressage Proxy 登记会话。正常走完后，generate 可以进入后面的 call_agent，把题目交给 Agent。

[本步 scope](01-scope.md) · [函数卡片](02-short-term-memory/overview.md) · [形成过程](04-flow.md#step005-first-pass-closure) · [项目进度](../../../../README.md)

## 1. 本步在整个任务中的位置

前一步已经通过 Paddock.init 取得环境，保存 lease，并把 state 交回 generate。本步沿用这些对象和此前整理的 session_id、instance_id、Agent 类型、后端选项及命令计划。

当前场景是 Claude Code 的首次正常注册，程序已由运行环境提供。本步不安装 Claude，也还没有通过 call_agent 提交题目。

本步在 generate 中只有三个主要动作：

1. `paddock.register_agent`：完成这次 Agent 运行的注册准备。
2. `execute_blackbox_cmds_for_stage`：执行 before_agent 命令。
3. `proxy_client.register_session_context`：向外部 Proxy 登记会话。

**停止位置：generate:255 的登记调用正常返回之后，进入 call_agent 之前。**

## 2. 已读部分怎样完成交接

下面保留调用层级。HTTP 箭头表示请求跨到服务端，不是客户端内部直接调用服务端 Python 函数。下层返回后，回到原调用者继续。

```python
blackbox_dispatch.generate  # 本步只看 Agent 执行前的准备
  |
  +-- [1] paddock.register_agent  # 找到已有沙箱，提交本次 Agent 配置
  |     -> client.register_agent  # 把配置组装成注册请求
  |        -> _post_agent_with_retry
  |        == HTTP POST /v1/rollout/register ==>  # 请求发往沙箱中的服务
  |           register_rollout  # 接收请求，交给服务对象处理
  |             -> BlackboxServer.register  # 选择适配器，组织注册准备
  |                  -> ClaudeCodeAdapter.initialize  # 准备目录、设置和本地模型代理
  |                  <- None  # 准备结果已留在对象和文件中
  |                  -> save binding / session; set READY  # 保存会话，允许后续提交任务
  |                  <- RegisterResponse, False  # False 表示本次未直接复用旧注册
  |        <== HTTP response ==
  |     <- response dict  # 返回 generate，继续第 2 项
  |
  +-- [2] execute_blackbox_cmds_for_stage(stage="before_agent")  # 执行配置好的前置命令
  |     -> for each command:  # 一条结束后再执行下一条；没有命令就跳过
  |          [2.1] _execute_blackbox_cmd  # 处理这一条命令的执行与结果
  |            -> paddock.execute_cmd -> sandbox command service  # 交给已有沙箱执行
  |            <- command result  # 取回输出、退出码和超时状态
  |            -> append metadata record; check required failure  # 先记录；必需命令失败则中止
  |     <- None  # 前置命令阶段结束，返回 generate
  |
  +-- [3] register_session_context = getattr(proxy_client, ...)  # 取得会话登记方法
        if callable:  # 存在可调用的方法才继续
          -> context_owned = True  # 标记后续需要处理登记的清理
          -> ProxyClient.register_session_context(session_id)  # 向外部 Proxy 登记本次会话
             == HTTP POST /v1/session/context ==> Dressage Proxy  # 发送会话 ID
             <== response dict ==  # 等待登记请求完成
        -> stop here in Step 005  # 本步结束，尚未提交题目

next: paddock.call_agent(...)  # 下一步才把题目交给 Agent，超出本步范围
```

### 2.1 完成 Agent 注册

1. Paddock 根据 state 找到沙箱服务的 endpoint，整理 Agent 类型、配置以及外部模型代理地址。
2. 客户端把这些资料发送给沙箱里的 BlackboxServer。
3. BlackboxServer 选择 ClaudeCodeAdapter，构建 BindingContext，等待 initialize 完成目录、配置文件和本地模型代理的准备。
4. initialize 返回后，BlackboxServer 保存绑定、能力和生效配置，建立或取得对应会话，设置 READY，返回注册响应。
5. 响应逐层回到 generate。generate 没有保存这个返回字典，而是继续执行前置命令。

这里的两个地址有不同用途：endpoint 是注册请求发往的沙箱服务；router_url 是告诉 Agent 后续模型请求应使用的外部 Dressage Proxy 地址。

这里的 READY 表示注册准备完成。返回值中的 False 表示本次没有直接复用旧的相同注册，不表示失败。

回查：[Paddock.register_agent](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md) → [客户端注册](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md) → [HTTP 发送](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._post_agent_with_retry.md) → [接收路由](02-short-term-memory/functions/blackbox_server/api/rollout.py/register_rollout.md) → [服务端注册](02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.register.md#after-initialize) → [Claude 初始化](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.initialize.md)。

### 2.2 执行配置好的前置命令

> 执行你事先配置好的命令，例如创建目录、准备文件、检查环境。然后读取输出、退出码和超时状态，决定是否继续。

1. 外层从命令计划中取出 before_agent 阶段的命令，没有配置就直接继续。
2. 每条命令交给 _execute_blackbox_cmd，再通过 Paddock 的命令接口在已有沙箱内执行。
3. 执行结果或异常追加到 metadata 中。必须成功的命令失败时抛出异常；可选命令失败可以记录后继续。
4. 一条结束后才执行下一条；全部结束后返回 generate。

命令由配置指定，不是 Claude/Codex 在这里根据题目自主作出的决定。创建目录等只是例子，也不是每次固定执行的动作。

回查：[按阶段执行](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md) → [一条命令的执行、记录和判断](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md)。

### 2.3 向外部 Dressage Proxy 登记会话

> 向 Dressage Proxy 登记本次会话，供后续请求管理使用；请求失败时会报错。

调用处的顺序是：

1. 取得 Proxy 客户端的会话登记方法。
2. 设置 context_owned，让后续清理逻辑知道需要处理这份登记。
3. 传入当前 session_id，等待登记请求完成。

客户端把 session_id 发到外部 Proxy 的 `/v1/session/context`。这里没有上传题目或聊天历史。代理侧启用相关路由管理时会保留会话路由记录；未启用时可以直接返回成功。

这次请求来自 generate 所在的一侧。它失败时能定位到登记环节，但不能单凭这次失败断定一定是 Proxy 服务本身出了问题；成功也不等于验证了沙箱到 Proxy 的网络路径。

回查：[ProxyClient.register_session_context](02-short-term-memory/functions/dressage/proxy/proxy_client.py/ProxyClient.register_session_context.md)。

## 3. 本步留下什么，交给谁使用

本步没有产生题目答案或新的 Sample，主要留下运行准备与记录。

| 留下的内容 | 后续用途 |
| --- | --- |
| BlackboxServer 的 Agent 适配器、绑定、会话与 READY 状态 | 接收后面的题目消息并执行 Agent |
| 沙箱中已执行的前置操作，以及 metadata 中的命令记录 | 给任务提供配置要求的初始条件，并保留执行依据 |
| Proxy 侧会话登记，以及 generate 的 context_owned 标记 | 后续请求管理；异常退出时确定清理责任 |

Paddock 和 state 继续沿用。接下来 generate 才会把 sample.prompt 整理成 messages，传给 `paddock.call_agent`。

## 4. 本步收束与下一处

用户表示“差不多理解了”，本步的注册、命令执行和 Proxy 登记已按 scope 覆盖，**可以结束 Step 005 的首轮阅读并保存这份总结**。

1. 本次收束的是执行前准备，不是整个 blackbox generate。
2. 注册重试、完整重绑定、命令服务端进程实现、代理再平衡算法仍保留为按需回查内容；不要求读完它们才进入后续主线。
3. 下一处候选是 `paddock.call_agent`：看题目怎样交给 Agent、怎样等待并取回结果。它属于后续执行范围，本次不提前创建新步骤或函数卡。
4. 后续仍沿已确认的[接入阅读规划](../../../../references/integration-reading-plan.md)：先收束原生 generate 的主线，再进入 Dressage 与 Harbor 的接入路线。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定提交：Dressage `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 外层位置：[blackbox_dispatch.generate:232](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L232)。
- 注册结果：[BlackboxServer.register:301](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/core/server.py#L301)。
- 前置命令：[execute_hooks.py:77](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/execute_hooks.py#L77)。
- Proxy 登记：[proxy_client.py:95](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L95)，服务端及路由管理的出处见对应函数卡。
- 下一调用位置：[generate:259](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L259)，只用于定位后续范围。
- 本页依据本步 scope、实际函数卡及 [04-flow](04-flow.md) 中的追问和修正整理。两段心智模型采用用户认可的简洁表达；不能据此推断所有内部细节均已掌握。
- 本轮核对属于静态源码阅读，没有执行真实 HTTP 请求、沙箱命令、模型调用或训练。

</details>
