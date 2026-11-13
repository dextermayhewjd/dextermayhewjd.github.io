# Scope 分层参考：3.1 定位 Step，3.2 展开本步阅读顺序

2026-11-05，根据用户最新澄清整理。**分层原则来自已表达的偏好；下面的 Step 000 / Step 001 写法是供对照的建议稿。** 本轮只新增这份 reference，不改正式 scope、函数卡、目录或进度。Step 001 尚未建立。

[现行 scope](../01-scope.md) · [generate 卡](../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md) · [init 卡](history/2026-11-05-init-before-ownership-correction.md)

针对性试读：[3.1 全局标法](#global-position) → [Step 000 的 3.2](#step000-local) → [Step 001 的 3.2](#step001-local)。

## 这次明确的分工

| 层级 | 只需回答的主要问题 | 标注方式 |
| --- | --- | --- |
| Step | 这轮要解决什么问题，读到什么程度？ | Step 000、Step 001 是阅读单元编号 |
| 3.1 全局位置 | 这个 Step 位于整条任务流程的哪里，关注哪一部分？ | 在全局流程上标 Step 的范围，不写本步内部“第几个阅读动作” |
| 3.2 本步阅读顺序 | 本步先看哪里、再看哪里，每处弄清什么？ | 使用 1、2、3 等本步内编号，提供源码或函数卡入口及返回位置 |
| 短期函数卡 | 当前函数实际怎样处理数据和完成职责？ | 保存具体参数、连续源码、解释、个人表述与未知 |

**3.2 是 scope 的章节，不是另一个 topic。Step 编号与 3.2 的内部编号不一一对应。** 一个 Step 可以读一个主要函数，也可以围绕同一个问题串联多个函数；同一函数的几个处理阶段也可以构成本步的阅读顺序。

这次建议的两步边界：

| 阅读单元 | 问题 | 主读函数 | 停止位置 |
| --- | --- | --- | --- |
| Step 000：整体交接 | 一份任务怎样经过环境、Agent 和 Proxy，最终交回训练样本？ | blackbox_dispatch.generate | 能定位输入、主要调用、两路结果与回收安排；子函数先知接口 |
| Step 001：环境准备，候选 | 环境需求怎样变成后续可用的 state？ | BlackboxAgentPaddock.init | 能说明 provider 的输入输出、地址来路和 state 去向；暂不追 provider 内部实现 |

Step 000 保留完整 generate 说明供回查；阅读完成的标准不要求深入其中每个调用。把环境准备独立出来，是为了让下一轮的问题和边界明确，不是因为“换了函数就必须换 Step”。

<a id="global-position"></a>

## 两步共用的 3.1：完整流程上只标 Step 范围

下面沿用现有 3.1 的完整关系，包括 Agent 执行期间的模型请求、两路结果以及后台清理。为避免与本步内部编号混淆，用节点名称代替原图的全局数字索引。**这里没有“Step 001 的第 1/2/3 个动作”，也不标“当前读 init 的第几段”。**

图中的 Step 000 标在 generate 的整体编排范围，Step 001 标在其中环境准备的范围。这张对照图同时显示两个候选范围；正式每步 scope 可强调属于本步的标记，保留完整上下文。

```text
Slime rollout
  -> configured custom generate hook

blackbox_dispatch.generate                       # Step 000: overall handoff
  -> proxy_client = get_proxy_client()
  -> claim_prewarm(...)                           # selected path: no handle
  -> paddock = get_paddock_from_env(...)
  -> state = await paddock.init(...)              # Step 001: environment preparation
  -> await paddock.register_agent(...)
  -> before_agent commands                        # if configured
  -> register session context with Proxy          # when supported
  -> call_payload = await paddock.call_agent(...)
       -- model requests while awaiting --> Agent / model path
  -> agent_response = agent_response_text(call_payload)
  -> after_agent commands                         # if configured
  -> await proxy_client.finalize_session(...)
  -> trajectory_payload = await proxy_client.read_trajectory(...)
  -> segments = trajectory_payload.get("data") or []
  -> result = multi_segment.expand_segments_to_samples(...)
  -> finally: schedule_terminate_paddock(...) --> Background cleanup
  -> return result --> Slime downstream

Agent / model path
  Agent <-> BlackboxServer LLM proxy <-> Dressage Proxy <-> SGLang
  Dressage Proxy -> records trajectory data during execution

Slime downstream
  list[Sample] -> downstream reward / train-data hooks -> training

Background cleanup
  terminate or release the environment
  may finish after generate has returned
```

这是全局关系图，省略了参数和部分包装，并非可执行源码。Agent / model path 发生在等待 call_agent 期间；Background cleanup 是被安排的后台工作，不能理解为先清理完成再返回。

1. 在 Step 000 中，这张图帮助定位“本步看 generate 怎样完成整体交接”。
2. 在 Step 001 中，同一张图帮助定位“本步看其中取得环境并返回 state 的部分”。
3. Step 001 的内部实现不继续塞入这张图；spec、lease、endpoint、记录字典等阅读顺序进入该步的 3.2。

**位置相同不代表问题相同。** Step 000 了解 generate 的整体安排；Step 001 深入其中一处交接，两步仍处于同一条全局任务流程中。

<a id="step000-local"></a>

## Step 000 的 3.2 示例：沿 generate 看完整交接

**本步问题**：任务进来后，环境、Agent、Proxy 与 Sample 转换怎样接起来？

**主读入口**：[blackbox_dispatch.generate](../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)。下面 1–6 是本步内部阅读顺序，与原 generate 卡的六段对应；不是六个 Step，也不表示六个子函数已经精读。

```python
# Teaching skeleton: normal path, no prewarmed handle.
session_id = ensure_blackbox_session_id(...)       # [1] task identity
instance_id = _instance_id(...)
env_args = paddock_env_args_from_metadata(...)
initialized = False
paddock = None
try:
    proxy_client = get_proxy_client()
    handle = await claim_prewarm(...)              # [2] environment
    ...  # Select the miss branch and renew session_id.
    paddock = get_paddock_from_env(...)
    state = await maybe_await(paddock.init(...))
    initialized = True

    await maybe_await(paddock.register_agent(...))  # [3] registration
    await execute_blackbox_cmds_for_stage(...)     # before_agent
    register_session_context = getattr(proxy_client, "register_session_context", None)
    if callable(register_session_context):
        await maybe_await(register_session_context(...))

    call_payload = await maybe_await(paddock.call_agent(...))  # [4] execution
    agent_response = agent_response_text(call_payload)

    await execute_blackbox_cmds_for_stage(...)     # [5] after_agent
    await proxy_client.finalize_session(...)
    trajectory_payload = await proxy_client.read_trajectory(...)
    segments = trajectory_payload.get("data") or []
    result = multi_segment.expand_segments_to_samples(...)
    return result                                 # returned after finally
finally:
    if initialized and paddock is not None:
        schedule_terminate_paddock(...)            # [6] cleanup scheduling
```

这是导航骨架：参数按 scope 的写法省略，正常分支被提取；省略会话 ID 更新细节、日志、失败包装与未完成会话清理。完整实现和实际参数仍在函数卡与固定版本源码中。

| 本步内部顺序 | 看 generate 的哪一部分 | 本步理解到哪里即可 |
| --- | --- | --- |
| 1. 任务信息 | 126–180 行，身份与环境参数 | 知道 session_id、instance_id、env_args 来自哪里，分别交给谁 |
| 2. 环境取得 | 182–229 行，预热命中/未命中 | 知道两条路径最终提供 paddock 与 state；init 内部留给环境准备问题 |
| 3. 注册准备 | 232–255 行 | 知道环境、身份、Agent 类型和 Proxy 地址怎样交入注册，以及前置操作的位置 |
| 4. Agent 执行 | 256–291 行 | 知道任务消息交给 call_agent，call_payload 接住结果；模型请求发生在等待期间 |
| 5. 轨迹与样本 | 293–349 行 | 分清回答与轨迹，知道 segments 怎样交给转换入口、result 交回谁 |
| 6. 退出安排 | 389–412 行 | 知道何时安排回收，区分安排完成与实际释放完成 |

**本步停止条件**：能沿以上六个交接说明一次任务的去向，就具备从全景选择下一处深入问题的基础。预热算法、provider 创建、Agent 后端、轨迹分段算法都不因出现在图上而自动成为本步必读。

<a id="step001-local"></a>

## Step 001 的 3.2 示例：围绕 init 看环境怎样交付

**本步问题**：generate 已有 session_id、env_type、env_args，怎样得到后续注册和调用 Agent 所需的 state？

**主读入口**：[BlackboxAgentPaddock.init](history/2026-11-05-init-before-ownership-correction.md)。这是业务方法 init，不是 35 行的对象构造方法 __init__。现有卡片仍位于 Step 000，此处链接用于讨论后续归属，不表示已经迁移。

进入与返回位置：

```text
generate:222
  -> BlackboxAgentPaddock.init
  <- state
generate:229
  -> initialized = True
generate:233
  -> paddock.register_agent(state, ...)
```

本步局部骨架如下。1–3 是本步内的三个阅读阶段，与 init 卡的三段保持一致；下表说明各阶段的问题，具体语句在对应函数卡中展开。

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

| 本步内部顺序 | 对应源码与卡片 | 本处要看清什么 | 接下来到哪里 |
| --- | --- | --- | --- |
| 1. 整理需求 | 71–85 行；[卡片第 1 段](history/2026-11-05-init-before-ownership-correction.md#build-spec) | spec 怎样表达本次身份、环境参数和服务要求 | 把 spec 交给 provider.create |
| 2. 取得环境与入口 | 86–116 行；[卡片第 2 段](history/2026-11-05-init-before-ownership-correction.md#acquire-environment) | lease 与服务地址的来路，以及健康检查的条件 | 用环境记录和地址构造 state |
| 3. 保存并交付 | 117–151 行；[卡片第 3 段](history/2026-11-05-init-before-ownership-correction.md#return-state) | state 的字段、内部记录与返回对象的关系 | 回到 generate，继续 register_agent |

**本步停止条件**：能区分 Paddock、实际沙箱与访问资料 state，说明 spec 交给谁、地址来自哪里、返回后谁使用 state。provider 的具体部署实现、取消后的独立清理、register_agent 内部执行不在本轮展开。

这里有三个阅读阶段，但只有一个主读函数 init。SandboxSpec、SandboxState 是数据对象的构造；字典赋值是本函数的语句；都不另包装成源码中不存在的函数。

## try 块与阅读单元怎样对应

1. try 表示异常处理范围，可能包住多个业务阶段；它不决定一个 Step 的边界。
2. Step 000 沿正常路径交代每个主要动作的职责和交接，保证全流程能连起来。
3. Step 001 只深入环境准备问题；当前问题依赖的调用看接口或必要实现，其他调用保留位置。
4. 配置、赋值、检查与日志按所属阶段解释，不为每一行单独建立阅读步骤。
5. 异常与清理先保留会影响理解的边界，后续有具体问题时再展开，不默认为已学会。

## 与现有文件怎样衔接

1. 现行 generate 卡继续保留，本文不采用此前的精简候选。函数卡详尽程度与 Step 000 要求读到的深度分别说明。
2. 本文只展示 Step 001 的可能范围和局部写法，不建立正式步骤、不迁移现有 init 卡、不改学习进度。
3. 如果后续采用，先确定两步 scope 的边界，再按既有继承规则安置已读记录，保留首次接触、原话与来源。不能通过移动文件把已发生的 Step 000 接触历史抹掉。
4. 正式 scope 仍以各步文件为准；这份 reference 用于比较标注与阅读层级，不成为第二份实时进度表。

## 对照时重点看什么

1. 单看 3.1，是否能回答“这个 Step 在整条流程的哪里”？
2. 单看 3.2，是否能回答“本步主要读哪个函数，内部先读什么、后读什么”？
3. 从 3.2 打开函数卡后，是否知道读完带什么结果返回哪里？
4. 能否区分 Step 001 与它内部的第 1、2、3 个阅读阶段？

<details>
<summary>用户原话、依据与验证边界</summary>

用户澄清：

> 从3.1和3.2的角度确实3.2 在仔细讲述blackbox dispatchj generate的内容
> 但是3.1 不应该写内部具体是stepx的第几步
>
> 只有3.2这个层级才应该写
> 3.1只应该写这一步在哪里进行 step0还是step1
> 3.2是step内部的阅读顺序
> 是我的理解

随后要求：

> 先给出一份这里的建议的reference吧
> 我好针对性地看一下

依据：[scope skill](../../../../../../../../.agents/skills/repo-reading-scope/SKILL.md)及其[局部导航 reference](../../../../../../../../.agents/skills/repo-reading-scope/references/local-call-context.md)。本次按用户偏好把局部骨架、顺序与返回统一放在 3.2；不要求必须再添加 3.3。

源码沿用 Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。generate 的骨架来自 blackbox_dispatch.py:116–412；init 来自 paddock/blackbox/paddock.py:64–151。示例采用原范围内已核对的正常路径，不是实际运行记录。

本轮仅新增本文，未修改现有正文、步骤目录、函数卡、索引、长期记忆或源码。

</details>
