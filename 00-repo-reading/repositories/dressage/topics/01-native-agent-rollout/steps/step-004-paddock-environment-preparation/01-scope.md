# 01 · Dressage Step 004：环境需求怎样变成可使用的 state

> 编号调整：本目录由 Step 001 顺延为 Step 004。正文中的早期编号、原话及记忆快照保留历史语境；现行顺序见[编号与范围对照](../../../../step-numbering-2026-11-05.md)。

[本步入口](README.md) · [项目当前接续](../../../../README.md) · [Step 000 系统全景](../step-000-slime-bridge-and-interfaces/01-scope.md#whole-flow) · [本步阅读顺序](#reading-navigation)

## 1. 本步目标：环境需求怎样变成可使用的 state

承接 Step 003：未命中后的会话 ID 与 Paddock 操作对象已准备好。init 已在原步骤读过，本次只回顾输入到输出的交接：**已有 session_id、环境类型和环境参数，Paddock 怎样取得环境，并把访问资料 state 返回给 generate？**

1. **输入变成需求**：session_id、env_type、env_args 怎样组成 spec。
2. **需求换成环境资料**：provider 返回 lease，取得 endpoint，并按配置检查健康。
3. **资料交回上层**：保存 lease/state，返回 state 给 generate，再接到 register_agent。

本次能把这三项接起来即可，不重读全部辅助函数。具体 provider、类字段与取消处理按疑问回查；Agent 注册是下一处新内容，当前不展开。

## 2. 主读入口与必要背景

主读函数：[BlackboxAgentPaddock.init](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md)。沿用本步已有短期卡，不重新生成；早期讨论来源与编号历史保留。

入口场景是 generate 未领取到预热环境，进入 init 的正常路径；Paddock 对象与 provider 已由配置准备。原阅读已覆盖 provider 的共同约定，local_bwrap 仅作数据交接例子，本次不用重走其实现。Kubernetes 后端需要另外实现，没有实际运行。这里读的是 64 行的业务方法 init；35 行的 __init__ 只在需要辨认对象字段时回查。

| 进入本步时已有 | 本步先怎样理解 |
| --- | --- |
| session_id | Step 003 未命中分支更新后的执行身份；作为 init 的 traj_id 参数传入 |
| env_type、env_args | 环境需求；具体资源由配置的 provider 提供 |
| paddock | 持有 provider 和服务客户端的操作对象，不等同于实际沙箱 |
| state | init 将返回的访问资料；调用方随后用它注册 Agent |

## 3. 上层背景与本步阅读

<a id="whole-flow"></a>
<a id="step001-overview"></a>

### 3.1 承接上一轮的 generate 骨架：本步在环境准备处

> 上层导航：[Step 000 系统全景](../step-000-slime-bridge-and-interfaces/01-scope.md#whole-flow) → [Step 000 的 generate 展开](../step-000-slime-bridge-and-interfaces/01-scope.md#reading-navigation) → **Step 004：init 环境准备**。

1. **Step 003 已准备**：更新后的会话 ID，以及可调用 init 的 Paddock 对象。
2. **Step 004 本次回顾**：把环境参数交给 init，取得并保存环境资料，返回 state。
3. **Step 005 下一候选**：使用同一份 state 注册 Agent；本次只定位交接，不展开注册实现。

下面沿用上一轮 generate 的完整正常路径骨架，仅更换阅读标注。**3.1 中只标 Step 004 所处的范围，不再出现上一轮的内部阅读编号，也不展开 init 内部。**

```python
# 教学裁剪：预热未命中的正常路径。
session_id = ensure_blackbox_session_id(...)
instance_id = _instance_id(...)
env_args = paddock_env_args_from_metadata(...)
initialized = False
paddock = None
try:
    proxy_client = get_proxy_client()
    handle = await claim_prewarm(...)
    ...  # 进入未命中分支并更新会话 ID，前一步已说明。
    paddock = get_paddock_from_env(...)
    state = await maybe_await(paddock.init(...))    # Step 004：回顾环境初始化
    initialized = True

    await maybe_await(paddock.register_agent(...))
    await execute_blackbox_cmds_for_stage(...)     # 执行 Agent 运行前的命令
    register_session_context = getattr(proxy_client, "register_session_context", None)
    if callable(register_session_context):
        await maybe_await(register_session_context(...))

    call_payload = await maybe_await(paddock.call_agent(...))
    agent_response = agent_response_text(call_payload)

    await execute_blackbox_cmds_for_stage(...)
    await proxy_client.finalize_session(...)
    trajectory_payload = await proxy_client.read_trajectory(...)
    segments = trajectory_payload.get("data") or []
    result = multi_segment.expand_segments_to_samples(...)
    return result                                 # 执行 finally 后才真正返回
finally:
    if initialized and paddock is not None:
        schedule_terminate_paddock(...)
```

这是教学裁剪，保留所选正常路径与回收位置，省略参数、日志、失败包装和未完成会话的清理。Agent 的模型请求与 Proxy 记录仍发生在等待 call_agent 期间，跨进程细节可回到最外层全图查看。finally 安排后台回收，不保证远端清理已在函数返回前完成。

从这张图可以直接定位三件事：

1. init 的输入已经由 generate 准备好，本步进入的是环境未命中的路径。
2. init 返回 state；generate 随后将 initialized 设为 True，再进入 register_agent。
3. Agent 执行、轨迹读取、样本转换和退出安排仍在图中，但本轮不展开这些部分。

<a id="reading-navigation"></a>
<a id="current-excerpt"></a>
<a id="step001-reading"></a>

### 3.2 本次回顾顺序：沿已有 init 卡接回 state

**原步骤已按共同接口与正常路径收束，见[任务交接总结](05-task-flow.md)。本次先回顾下面的 1、2、3 三个主阶段；2.1–2.3 和类卡仅在有具体疑问时打开。** 不把已有材料重新变成必读清单，终点仍是 init 返回 state 给 generate。

**从这里才开始本步内部的 1、2、3。** 三个编号对应同一个 init 方法中的处理阶段，不是三个新函数，也不是三个新 Step。

```python
# 教学裁剪：正常初始化路径，省略异常处理。
env_args = {**(env_args or {}), **kwargs}           # [1] 整理环境需求
spec = SandboxSpec(...)

create_task = asyncio.create_task(                # [2] 取得环境
    self._provider.create(spec),                 # [2.1] provider 接口约定
    name=f"sandbox-create:{traj_id}",
)
lease = await asyncio.shield(create_task)
endpoint = lease.endpoints.get("blackbox")
if endpoint is None:
    endpoint = await self._provider.get_public_url(...)  # [2.2] 缺少入口时才调用
    lease.endpoints["blackbox"] = endpoint
endpoint = endpoint.normalized()             # [2.3] 整理入口并检查健康
if self._wait_health:
    await self._client.health(endpoint)

state = SandboxState(...)                        # [3] 保存并返回资料
# self 是当前 BlackboxAgentPaddock 实例；这两个实例字典由 __init__ 创建
self._leases[traj_id] = lease  # 只写入/更新本次 traj_id 的 lease，保留其他键
self._states[traj_id] = state  # 同一 traj_id 对应本次 state，可与其他轨迹并存
return state  # 交回本次结果；两个字典仍由这个 Paddock 对象持有
```

**对象归属**：一次 init 调用只处理一个 traj_id；同一个 BlackboxAgentPaddock 实例可被复用，多次 init 可以登记多个不同的 traj_id。这两个字典属于实例，不是所有实例共享的类变量。字段创建与复用依据见 [init 卡的记录归属说明](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#trajectory-indexes)。

同样是正常路径的教学骨架；两处异常清理被省略，缺少地址时回查 provider 的分支及健康检查条件仍保留。具体实参和完整语句在 init 函数卡中查看。

| 本步内部顺序 | 进入哪段源码 | 当前要理解的关系 | 结果交给哪里 |
| --- | --- | --- | --- |
| 1. 整理环境需求（回顾） | [init 71–85 行：卡片第 1 段](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#build-spec) | traj_id、env_type、env_args 怎样组成 spec，服务端口需求写在哪里 | spec 交给 provider.create |
| 2. 取得环境与服务入口（回顾） | [init 86–116 行：卡片第 2 段](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#acquire-environment) | lease 是什么、endpoint 从哪里来、何时检查健康 | 环境记录与服务地址交给 state 构造 |
| 2.1 create 的共同约定（按需） | [create 方法卡](02-short-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.create.md)；[接口总览](02-short-term-memory/classes/dressage/sandbox/provider.py/SandboxProvider.md)；[SandboxProvider 源码](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/sandbox/provider.py#L15) | 创建请求、资源记录、服务入口、就绪与失败清理怎样交接 | 回到 init 接收 lease，继续 endpoint 与 state |
| 2.2 get_public_url（按需回查条件分支） | [get_public_url 方法卡](02-short-term-memory/functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md) | 已有 lease、端口和服务名怎样交回 Endpoint；为何已有入口时跳过调用 | 回到 init 回填入口，再整理与检查健康 |
| 2.3 入口整理与健康检查（按需） | [init 114–116 行](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#normalize-and-health)；[health 函数卡](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.health.md) | normalized 不发请求；按开关访问 /health；正常结束才继续 | 回到第 3 段构造 state |
| 3. 保存资料并交付（回顾） | [init 117–151 行：卡片第 3 段](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#return-state) | 单次 init 返回一个 state；同一 Paddock 实例按 traj_id 保存多份 lease/state | state 返回 generate，随后用于注册 Agent |

第一段涉及的数据类型可在 [SandboxSpec](02-short-term-memory/classes/dressage/sandbox/types.py/SandboxSpec.md) 与 [SandboxServiceSpec](02-short-term-memory/classes/dressage/sandbox/types.py/SandboxServiceSpec.md) 两张类卡中回查。看清字段后返回 init 第 1 段；它们是本步的辅助入口，不新增阅读阶段。

2.1 与 2.2 是第 2 段内的 provider 接口阅读；2.3 回到调用方继续处理，均不代表新增 Step。[local_bwrap create](references/local-bwrap-create.md)已移到 references，只取数据交接，不追踪管理器和槽位池内部。

第二段涉及 [SandboxLease 与 endpoint](02-short-term-memory/classes/dressage/sandbox/types.py/SandboxLease.md)；第三段返回 [SandboxState](02-short-term-memory/classes/dressage/paddock/blackbox/common/state.py/SandboxState.md)。本轮关于 shield 的疑问见 [init 的取消分支](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md#shield-create-cancellation)，不改变三段主线。

**停止位置**：能把“环境需求 → 环境及服务入口 → state → generate”连起来，并区分 Paddock 操作对象、实际环境和返回的访问资料。代码中的每个调用不自动成为必读子函数。

**读完返回**：[generate 的环境取得段](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#environment-init)，接住 state 并设置 initialized=True；然后回到[注册段](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#agent-registration)。下一处新内容见 [Step 005：注册准备](../step-005-agent-registration/01-scope.md)，首读 BlackboxAgentPaddock.register_agent；不会因本次更新 scope 自动开始其源码阅读。

<details>
<summary>源码、继承与范围依据</summary>

- 采用用户确认的 [reference1](../step-000-slime-bridge-and-interfaces/references/reference1.md)。3.1 只标本步在父函数中的范围，3.2 的 1–3 是 init 内部阅读阶段，不是新增 Step。
- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。父函数 blackbox_dispatch.py:116–412；主读 init 位于 paddock/blackbox/paddock.py:64–151。
- [02 本步函数](02-short-term-memory/overview.md)使用 init 与直接调用方 generate；[03 前序快照](03-long-term-memory/overview.md)继承 Step 000 的 generate；init 归本步 02。两者均保留原话、认识时间和未知。
- [本步确认过程](04-flow.md#scope-adopted)。本轮建立正式阅读边界，未运行真实环境或训练；init 的具体理解反馈仍待后续记录。

</details>
