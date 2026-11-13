# Reference 1：上一轮的展开，成为下一轮的上层背景

> 2026-11-05 已按用户确认采用：[Step 000 scope](../01-scope.md) · [Step 004（原 001） scope](../../step-004-paddock-environment-preparation/01-scope.md)。下文保留当时的试读稿与“尚未建立”状态描述，作为方案历史。

2026-11-05，按用户最新建议另存的试读稿。**本轮只新增本文；原 reference、正式 scope 和函数卡保持不变，Step 001 尚未建立。**

[前一份 reference](scope-step-position-and-reading-order.md) · [现行 Step 000 scope](../01-scope.md) · [直接看新的 3.1](#step001-overview) · [直接看新的 3.2](#step001-reading)

这次建议的核心是：**Step 001 的 3.1 承接 Step 000 的 3.2 中的 generate 骨架，Step 001 的 3.2 再展开 init。** 最外层的系统全景保留在 Step 000，通过面包屑回看。

| 阅读位置 | 3.1：上层背景与本步范围 | 3.2：本步内部阅读顺序 |
| --- | --- | --- |
| Step 000 | 系统全景：Slime、Dressage、Agent、Proxy 与训练样本的关系 | 展开 generate 的整体交接 |
| Step 001，以下试读稿 | 承接 generate 的完整骨架，在 init 处标出 Step 001 | 展开 init 的需求整理、环境取得、状态交付 |

这里继承的是**调用骨架**。上一轮 3.2 中的内部序号、当前阅读标记和验收表，不直接复制成下一轮的内部序号；它们已经属于上一轮。新 3.1 只标本步范围，新 3.2 才使用本步内部的 1、2、3。

以下是采用这个方向后，**Step 001 的 scope 可以怎样写**。它是候选正文，不是已创建的新步骤。

---

## 1. 本步目标：环境需求怎样变成可使用的 state

上一轮已经从 generate 看过任务的完整交接。本轮只解决：**已有 session_id、环境类型和环境参数，Paddock 怎样取得环境，并把访问资料 state 返回给 generate？**

1. 看清环境需求怎样整理成 spec。
2. 看清 provider 返回的 lease 与服务地址怎样被使用。
3. 看清 state 保存什么，以及返回后怎样交给 register_agent。

读到能够说明这些交接就停止。本轮不要求看完 provider 的部署实现、Agent 的注册执行或 Proxy 的轨迹算法。

## 2. 主读入口与必要背景

主读函数：[BlackboxAgentPaddock.init](history/2026-11-05-init-before-ownership-correction.md)。现有卡片仍在 Step 000 中，此处直接引用，不通过候选稿提前迁移。

入口场景是 generate 未领取到预热环境，进入 init 的正常路径；Paddock 对象与 provider 已由配置准备。这里读的是 64 行的业务方法 init；35 行的 __init__ 只在需要辨认对象字段时回查。

| 进入本步时已有 | 本步先怎样理解 |
| --- | --- |
| session_id | 本次执行身份；作为 init 的 traj_id 参数传入 |
| env_type、env_args | 环境需求；具体资源由配置的 provider 提供 |
| paddock | 持有 provider 和服务客户端的操作对象，不等同于实际沙箱 |
| state | init 将返回的访问资料；调用方随后用它注册 Agent |

## 3. 上层背景与本步阅读

<a id="step001-overview"></a>

### 3.1 承接上一轮的 generate 骨架：本步在环境准备处

> 上层导航：[Step 000 系统全景](../01-scope.md#whole-flow) → [Step 000 的 generate 展开参考](scope-step-position-and-reading-order.md#step000-local) → **Step 001：init 环境准备**。

下面沿用上一轮 generate 的完整正常路径骨架，仅更换阅读标注。**3.1 中只标 Step 001 所处的范围，不再出现上一轮的内部阅读编号，也不展开 init 内部。**

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
    state = await maybe_await(paddock.init(...))    # Step 001: environment preparation
    initialized = True

    await maybe_await(paddock.register_agent(...))
    await execute_blackbox_cmds_for_stage(...)     # before_agent
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
    return result                                 # returned after finally
finally:
    if initialized and paddock is not None:
        schedule_terminate_paddock(...)
```

这是教学裁剪，保留所选正常路径与回收位置，省略参数、日志、失败包装和未完成会话的清理。Agent 的模型请求与 Proxy 记录仍发生在等待 call_agent 期间，跨进程细节可回到最外层全图查看。finally 安排后台回收，不保证远端清理已在函数返回前完成。

从这张图可以直接定位三件事：

1. init 的输入已经由 generate 准备好，本步进入的是环境未命中的路径。
2. init 返回 state；generate 随后将 initialized 设为 True，再进入 register_agent。
3. Agent 执行、轨迹读取、样本转换和退出安排仍在图中，但本轮不展开这些部分。

<a id="step001-reading"></a>

### 3.2 本步内部阅读顺序：展开 init

**从这里才开始本步内部的 1、2、3。** 三个编号对应同一个 init 方法中的处理阶段，不是三个新函数，也不是三个新 Step。

```python
# Teaching skeleton: normal initialization path; error handlers omitted.
env_args = {**(env_args or {}), **kwargs}           # [1] environment request
spec = SandboxSpec(...)

create_task = asyncio.create_task(                # [2] acquire environment
    self._provider.create(spec),
    name=f"sandbox-create:{traj_id}",
)
lease = await asyncio.shield(create_task)
endpoint = lease.endpoints.get("blackbox")
if endpoint is None:
    endpoint = await self._provider.get_public_url(...)
    lease.endpoints["blackbox"] = endpoint
endpoint = endpoint.normalized()
if self._wait_health:
    await self._client.health(endpoint)

state = SandboxState(...)                        # [3] record and return
self._leases[traj_id] = lease
self._states[traj_id] = state
return state
```

同样是正常路径的教学骨架；两处异常清理被省略，缺少地址时回查 provider 的分支及健康检查条件仍保留。具体实参和完整语句在 init 函数卡中查看。

| 本步内部顺序 | 进入哪段源码 | 当前要理解的关系 | 结果交给哪里 |
| --- | --- | --- | --- |
| 1. 整理环境需求 | [init 71–85 行：卡片第 1 段](history/2026-11-05-init-before-ownership-correction.md#build-spec) | traj_id、env_type、env_args 怎样组成 spec，服务端口需求写在哪里 | spec 交给 provider.create |
| 2. 取得环境与服务入口 | [init 86–116 行：卡片第 2 段](history/2026-11-05-init-before-ownership-correction.md#acquire-environment) | lease 是什么、endpoint 从哪里来、何时检查健康 | 环境记录与服务地址交给 state 构造 |
| 3. 保存资料并交付 | [init 117–151 行：卡片第 3 段](history/2026-11-05-init-before-ownership-correction.md#return-state) | state 与 Paddock 内部记录分别保留什么 | state 返回 generate，随后用于注册 Agent |

**停止位置**：能把“环境需求 → 环境及服务入口 → state → generate”连起来，并区分 Paddock 操作对象、实际环境和返回的访问资料。代码中的每个调用不自动成为必读子函数。

**读完返回**：[generate 的环境取得段](../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#environment-init)，接住 state 并设置 initialized=True；然后回到[注册段](../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#agent-registration)。注册内部是后续候选，不因本次返回导航而自动展开。

---

## 与上一份 reference 相比，具体变在哪里

1. 前稿让两步都以最外层系统全图作为 3.1；本稿让 Step 001 使用上一轮已经展开的 generate 作为直接背景。
2. 原来只有“generate:222 → init → state → register_agent”的几行返回提示，本稿用完整 generate 骨架替代它作为主要上下文；返回提示仍可保留在 3.2 末尾或函数卡中。
3. Step 000 的系统全景继续保留，通过顶部面包屑回看，不因进入下一层而删除。
4. 3.1 标本 Step 的范围；3.2 标本 Step 内部的阅读顺序。展开层级变化，二者职责不变。

这是一种按问题逐层展开的方式，并不要求每个后续 Step 都机械复制紧邻前一步的 3.2。如果后续改读同层的 register_agent，应回到 generate 作为上层背景；不会因为上一轮读了 init，就把 init 当成所有后续函数的上层。

## 目前保留什么，不做什么

1. 原 generate 卡、init 卡及其原话、来源均保留；本稿不修改它们。
2. 不创建 Step 001 的正式目录，不改变唯一学习进度。
3. 本稿只验证 scope 的承接方式；如果采用，再按已经确认的范围处理正式 scope 和记忆继承，保留真实的首次接触历史。

<details>
<summary>用户反馈、来源与核对方式</summary>

用户针对前稿的简短返回链提出：

> 我在想或许这里的step1的3.1就是step0的3.2呢?
> 这样子是否会好很多呢?

随后要求：

> 那么再生成一个reference1我看一下吧

本稿据此保留前稿 Step 000 的 3.2 正常路径代码，去掉本步内部的 [1]–[6] 标记，在 init 处添加 Step 001 范围标记；代码主体不变。init 的 3.2 沿用同一份三段骨架，不增加未讨论的新课程。

依据：[scope skill](../../../../../../../../.agents/skills/repo-reading-scope/SKILL.md)和[局部导航 reference](../../../../../../../../.agents/skills/repo-reading-scope/references/local-call-context.md)。本次采用用户指定的逐层承接方式，既有文件未被改写。

源码基准：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；generate 位于 dressage/rollout/generate/blackbox_dispatch.py:116–412；init 位于 dressage/paddock/blackbox/paddock.py:64–151。这里只核对静态骨架与链接，没有运行真实环境、Agent 或训练。

</details>
