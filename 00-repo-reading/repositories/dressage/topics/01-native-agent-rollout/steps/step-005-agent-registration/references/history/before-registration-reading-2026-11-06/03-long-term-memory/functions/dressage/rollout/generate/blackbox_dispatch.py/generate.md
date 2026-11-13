# blackbox_dispatch.generate

[本步 scope 与完整主线](../../../../../../../../../../step-004-paddock-environment-preparation/01-scope.md#whole-flow) · [阅读导航](../../../../../../../../../../step-004-paddock-environment-preparation/01-scope.md#reading-navigation) · [函数索引](../../../../../overview.md)

- 源码定位：[dressage/rollout/generate/blackbox_dispatch.py:116–412](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L116)，由助手静态核对。
- 首次接触：Step 000；2026-10-23 定位主流程，2026-11-05 用户明确要求建立本函数卡。
- 最近认识更新：2026-11-05，用户已复述环境取得、Agent 执行、轨迹读取与退出清理的主线，并明确清楚 Slime 的 generate_and_rm；对象身份及数据方向的精确区别仍待反馈。本轮保留原讲解结构，进入 init 回查环境来路。

- 继承自：[Step 000 原始函数记录](../../../../../../../../../../step-000-slime-bridge-and-interfaces/02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)。2026-11-05 完整继承；原话、首次接触、最近认识更新和未知保持原记录，以下“本轮”保留其历史语境。

- 本步调取：[Step 001 前序快照](generate.md)。init 为本步主读，generate 为直接调用方回查；调取不新增个人认识。

- 继承入 Step 002：来自 [Step 004（原 001） 的完整记录](../../../../../../../../../../step-004-paddock-environment-preparation/02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)，合并前序 03 + 02；原话、认识时间与未知保留，以下“本轮”沿用原记录语境。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据固定版本源码整理，作为本轮理解参考。

1. **使用场合**：Slime 要为一份 sample 执行自定义生成时，通过配置加载这个函数。它接入的是一次黑盒 Agent 任务；Agent 内部可以有多轮模型与工具交互。

2. **具体内容**：根据 sample 的任务信息取得环境，注册并调用 Agent，从调用结果提取回答，再从 Proxy 收集训练轨迹，将轨迹分段转换成 Sample 列表交回 Slime。退出时安排环境回收；预热、失败和取消有各自分支。

3. **建议构建的心智模型**：

   > 把 generate 看作“一份任务进入，训练样本交出”的编排入口。
   >
   > 1. Paddock 提供环境及调用 Agent 的操作。
   > 2. Agent 执行任务；执行期间的模型请求经过 Proxy 留下轨迹。
   > 3. generate 分别收回答文本和轨迹，再调用转换函数生成 Sample。
   > 4. Sample 交回 Slime，环境回收交给后台生命周期任务。
   >
   > 本轮先看清这些交接。具体 Agent 如何解题、Proxy 如何记录 token、Sample 如何参与训练，分别由后续组件承担。

4. **调用代码**：Slime 留出的是可配置的调用位置；这里的 generate 就是放入该位置的函数。

   Dressage 的配置入口：

   ```bash
   --custom-generate-function-path \
     dressage.rollout.generate.blackbox_dispatch.generate
   ```

   Slime 的 generate_and_rm 中，实际分派代码如下。只摘录分派部分，保留原变量名；版本采用 Dressage 锁定的 Slime 提交。

   ```python
   custom_func_path = getattr(sample, "generate_function_path", None) or args.custom_generate_function_path

   if custom_func_path is not None:
       custom_generate_func = load_function(custom_func_path)
       # if signature has evaluation, pass evaluation
       if "evaluation" in inspect.signature(custom_generate_func).parameters:
           sample = await custom_generate_func(args, sample, sampling_params, evaluation=evaluation)
       else:
           sample = await custom_generate_func(args, sample, sampling_params)
   else:
       sample = await generate(args, sample, sampling_params)
   ```

   1. 本场景配置路径指向 blackbox_dispatch.generate，加载后由 custom_generate_func 调用。
   2. 它声明了 evaluation 参数，因此会走传入 evaluation 的分支。
   3. 最后 else 中的 generate 是 Slime 自带的默认路径。配置 Dressage 后，不需要先执行这条默认路径再进入 Dressage。
   4. 返回值重新赋给 Slime 的 sample 变量；这个变量此时也可以是 Sample 列表。

## 本场景的输入与输出

沿用 scope 的正常路径：evaluation=False，没有领取到预热 handle，Agent 调用正常完成，Proxy 返回可转换的非空轨迹分段。provider 由配置选择，不假定一定创建 Kubernetes Pod。以下为静态源码说明，未运行任务，未取得实际 session ID、回答或 token 数值。

**输入**：

| 参数 | 本场景携带什么 | 在函数中交给哪里 |
| --- | --- | --- |
| sample | prompt、metadata，以及 index、label 等相关任务字段 | prompt 交给 Agent；metadata 提供环境与后端设置；原 sample 作为分段样本的模板 |
| args | 本次运行设置 | 用于准备 backend_options，并交给样本转换函数 |
| sampling_params | 采样参数字典 | 本函数显式读取 sampling_seed（如果提供），用于后端代理配置；其他字段不在这里逐项展开 |
| evaluation | 本场景为 False | True 会在主 try 之前抛出 ValueError；本函数不承接评估模式 |

**输出与状态变化**：

| 结果 | 本场景的内容 | 去向 |
| --- | --- | --- |
| 返回值 result | list[Sample]；转换函数按轨迹分段构造样本，携带 token、mask、logprob 及归属信息等训练材料 | 返回到 Slime 的自定义生成调用处，后续再进行评分、奖励处理与训练数据交接 |
| 输入 sample 的状态 | metadata 会被清理和更新；本次选定的预热未命中路径还会更新 session_id | 供当前执行、样本构造和失败追踪使用 |
| 环境生命周期 | 正常取得环境后，finally 安排后台终止或释放 | 安排完成时，远端资源可能尚未释放 |

**两条结果不能合并理解**：

1. call_payload → agent_response：Agent 给出的回答文本。
2. trajectory_payload → segments → result：Proxy 保存的轨迹经过转换后成为训练样本。

例如一次任务产生两段有效轨迹，转换入口可返回两个 Sample；它们仍属于同一条原始任务轨迹。这里的“两个”是说明返回形状的假设，不是一次运行结果，也不能直接当成两次独立答题。

### 函数内部怎样完成这次处理

下面六段对应同一个 generate 调用。代码按原执行顺序节选，省略处用 `...` 标记；统一减少外层缩进，保留所示调用的实参。各段不是独立可运行程序。第一遍沿本页读交接，子函数只保留源码入口，尚不另建卡片。

#### 1. 从 sample 取出会话、任务与环境配置（126–180）

```python
metadata = getattr(sample, "metadata", None)
if not isinstance(metadata, dict):
    metadata = {}
    sample.metadata = metadata
...  # Clear previous error markers and initialize execute_cmds.
deterministic_session_id = metadata.get("dressage_deterministic_session_id")
session_id = ensure_blackbox_session_id(sample)
instance_id = _instance_id(sample)
metadata["session_id"] = session_id
metadata["instance_id"] = instance_id
blackbox_type = normalize_blackbox_type(
    metadata.get("blackbox_type") or DEFAULT_BLACKBOX_TYPE
)

extra_env_args = None
if "blackbox_type" in metadata or blackbox_type != DEFAULT_BLACKBOX_TYPE:
    extra_env_args = {"blackbox_type": blackbox_type}
env_args = paddock_env_args_from_metadata(
    metadata,
    extra_env_args=extra_env_args,
)
...  # Initialize lifecycle flags; enter the main try.
```

1. metadata 是本次任务携带的配置与记录字典，函数会直接更新它。
2. session_id 用来贯穿环境、Agent 会话和 Proxy 轨迹；instance_id 用来标识题目实例。两者不要混成同一个标识。
3. env_args 从 metadata 整理而来，下一段交给环境初始化。这一段还没有取得环境。
4. 主 try 开始后还会解析前后置命令、准备 backend_options，并在提供 sampling_seed 时补入代理配置。首轮只保留这些数据接下来用于注册和执行的关系。

| 需要回查时进入 | 读完返回哪里 |
| --- | --- |
| [paddock_env_args_from_metadata](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L203) | 带着 env_args 回到下面的 paddock.init 调用 |

<a id="environment-init"></a>

#### 2. 领取预热环境；本场景未命中，再调用 init（182–229）

```python
proxy_client = get_proxy_client()
...  # Read prewarm_requested and start wait-time measurement.
handle = await claim_prewarm(session_id)
...  # Measure prewarm_wait.
if handle is not None:
    paddock = handle.paddock
    state = handle.state
    env_args = handle.env_args
    initialized = True
    ...  # Hit metrics and logs.
else:
    ...  # Miss metrics; renew session_id and update sample/metadata.
    paddock = get_paddock_from_env(allow_whitebox_mode=False)
    state = await maybe_await(
        paddock.init(
            session_id,
            metadata.get("env_type"),
            env_args,
        )
    )
    initialized = True
```

1. proxy_client 是访问 Proxy 服务的客户端，随后用于会话收尾和读取轨迹。
2. claim_prewarm 用 session_id 领取预热结果。命中时直接取得 paddock、state 和 env_args。
3. 本场景走 else：先更新会话标识，再取得 Paddock 对象，调用 init 得到 state。确定性会话标识会加上 `-miss`；其他情况清空后重新生成，后续调用都使用更新后的标识。
4. Paddock 是环境操作与交互协调对象；state 是初始化返回的访问状态，下一段注册 Agent 时还要带上它。
5. initialized=True 表示 init 已正常返回，供退出时判断是否安排回收。这里还没有执行题目。

| 需要回查时进入 | 读完返回哪里 |
| --- | --- |
| [get_paddock_from_env](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L165) | 回到 222 行，用取得的 paddock 调用 init |
| [BlackboxAgentPaddock.init：本轮进入](../../../paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md) | 接住 state，继续下面的 register_agent |

<a id="agent-registration"></a>

#### 3. 为环境配置 Agent，并登记执行所需的会话（232–255）

```python
await maybe_await(
    paddock.register_agent(
        state,
        instance_id=instance_id,
        session_id=session_id,
        router_url=proxy_url(),
        blackbox_type=blackbox_type,
        backend_options=backend_options,
    )
)
await execute_blackbox_cmds_for_stage(
    paddock,
    state,
    metadata,
    schedule=execute_cmd_schedule,
    session_id=session_id,
    stage="before_agent",
)
register_session_context = getattr(
    proxy_client, "register_session_context", None
)
if callable(register_session_context):
    context_owned = True
    await maybe_await(register_session_context(session_id))
```

1. register_agent 接收前一段的 state，同时带入题目、会话、Agent 类型、后端设置和 Proxy 地址，为随后调用 Agent 准备会话。
2. before_agent 命令属于可配置的前置操作，没有配置时可以为空；实际解题调用在下一段。
3. Proxy 客户端支持 register_session_context 时，先设置 context_owned，再登记会话。这个标志使退出路径能够清理尚未正常收尾的上下文。
4. 到这里，环境状态、Agent 会话和代理上下文已经接好，下一步才把 sample.prompt 交入 Agent。

| 需要回查时进入 | 读完返回哪里 |
| --- | --- |
| [BlackboxAgentPaddock.register_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L153) | 回到前置命令及 Proxy 会话登记，随后进入 call_agent |

#### 4. 调用 Agent，等待本次执行，取得回答文本（256–291）

```python
call_payload: Any = None
call_succeeded = False
try:
    call_payload = await maybe_await(
        paddock.call_agent(
            state,
            session_id=session_id,
            messages=_chat_messages_from_prompt(sample.prompt),
            metadata={"source": "dressage", **metadata},
        )
    )
    call_succeeded = True
except Exception as exc:
    ...  # Harvest selected early-stop cases or raise the failure.

if call_succeeded:
    agent_response = agent_response_text(call_payload)
    ...  # Check for failure encoded in the returned payload.
```

1. sample.prompt 整理为 messages，连同 state、session_id 和 metadata 交给 call_agent。
2. await 等待本次 Agent 调用完成。Agent 的多轮模型与工具交互发生在这段等待期间，generate 不在本页逐轮组织这些动作。
3. Agent 发出的模型请求经过代理；Proxy 在执行期间记录轨迹。下图只是职责边界，不是额外的源码调用列表。

   ```text
   ╔════════════════════════════════════════════════════╗
   ║ generate: await paddock.call_agent(...)             ║
   ║           -> call_payload -> agent_response         ║
   ╚════════════════════════════════════════════════════╝
          | delegated execution while awaiting
          v
   Agent <-> BlackboxServer LLM proxy <-> Dressage Proxy <-> SGLang
                                              |
                                              v
                                        trajectory data
   ```

4. 正常返回后，agent_response_text 从 call_payload 提取回答。此时尚未读取 Proxy 中的训练轨迹。
5. call_agent 返回说明这次调用结束，不等同于整个 Agent 进程退出或环境已释放。

| 需要回查时进入 | 读完返回哪里 |
| --- | --- |
| [BlackboxAgentPaddock.call_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L184) | 回到 259 行接住 call_payload，继续提取回答和下面的轨迹收集 |

#### 5. 收尾会话，读取轨迹，再转换并交回 Sample（293–349）

```python
await execute_blackbox_cmds_for_stage(
    paddock,
    state,
    metadata,
    schedule=execute_cmd_schedule,
    session_id=session_id,
    stage="after_agent",
)
await proxy_client.finalize_session(
    session_id, instance_id=instance_id, label=getattr(sample, "label", None)
)
context_owned = False
trajectory_payload = await proxy_client.read_trajectory(
    trajectory_id=session_id,
    instance_id=instance_id,
    drain=True,
)
...  # Write optional trajectory artifacts; log write failures.
segments = trajectory_payload.get("data") or []
base_metadata_for_logs = dict(metadata)
result = multi_segment.expand_segments_to_samples(
    sample,
    segments,
    args=args,
    agent_response=agent_response,
    session_id=session_id,
    instance_id=instance_id,
)
...  # Write optional sample artifacts; log write failures.
return result
```

1. 先执行 after_agent 后置命令；它和第 3 段的前置命令位于 Agent 调用两侧。
2. finalize_session 请求 Proxy 收尾本会话。成功后将 context_owned=False，正常退出时无需再丢弃未完成的上下文。
3. read_trajectory 按本次 session_id 与 instance_id 读取轨迹；本次调用保留 drain=True。
4. 从 trajectory_payload 的 data 字段取出 segments。这一份数据来自 Proxy，不是把回答文本直接当成轨迹。
5. expand_segments_to_samples 接收原 sample、segments 和 agent_response 等信息，得到 result。分段样本会保留共同的原轨迹归属；本轮只读输入输出，分段算法与奖励广播留待后续。
6. return result 走正常返回路径；Python 会先执行下面的 finally，然后才把结果交回 Slime。Slime 仍可能为需要 reward 的样本调用评分路径；不是到这里就完成训练更新。

| 需要回查时进入 | 读完返回哪里 |
| --- | --- |
| [ProxyClient.finalize_session](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L64) / [read_trajectory](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L115) | 回到 305 行接住 trajectory_payload，提取 segments |
| [expand_segments_to_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/multi_segment.py#L118) | 回到 324 行接住 result，沿返回路径进入 finally |

#### 6. 退出时安排环境回收（389–412）

```python
finally:
    ...  # Preserve the active cancellation error.
    try:
        if context_owned:
            try:
                await _discard_session_context(
                    proxy_client,
                    session_id=session_id,
                    metadata=metadata,
                )
            except asyncio.CancelledError:
                if original_cancelled_error is None:
                    raise
    finally:
        if initialized and paddock is not None:
            schedule_terminate_paddock(
                paddock,
                session_id=session_id,
                env_args=env_args,
            )
```

1. 本场景 finalize_session 已成功，context_owned=False，因此跳过上下文丢弃操作。
2. 初始化已成功且 paddock 存在，调用 schedule_terminate_paddock 安排后台清理。
3. 本函数没有在这里 await 远端环境清理完成；返回 Sample 和资源实际释放可以发生在不同时刻。
4. 读完回到 Slime 的 custom_generate_func 调用处，接住 Sample 列表，再继续外层处理。

| 需要回查时进入 | 读完返回哪里 |
| --- | --- |
| [schedule_terminate_paddock](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L175) | 返回 generate 的 finally，随后完成本次返回 |

<details>
<summary>其他路径的边界：先知道返回形状，不展开恢复机制</summary>

1. 预热命中：使用 handle 中已有的环境状态，跳过本次 init，随后接回 register_agent。
2. 某些 Agent 提前停止：代码允许继续收集已有轨迹，不能把所有 call_agent 异常都理解成马上丢弃样本。
3. 主 try 捕获的普通失败：记录失败，调用 mark_aborted_no_grad，将状态设为 ABORTED，返回单个 sample。因此整个函数并非所有路径都返回列表。
4. 取消：记录并重新抛出 CancelledError，同时进入 finally。取消不是一个正常返回的奖励或回答。
5. 空 segments：转换函数会抛出 ValueError，进入普通失败路径；本页选择的是有可用分段的正常场景。
6. 初始化尚未正常返回时 initialized 可能仍为 False；不能只凭本函数 finally 推断底层没有清理，Paddock/provider 还有自己的取消处理。

</details>

## 我的直接表述（原话）

2026-11-05，用户确认首读入口并请求建卡：

> 好的那么我第一个需要看的函数是哪一个呢?
> 先看一下这里的slime留出来的钩子也就是这里的generate
> 然后需要看一下这里的blackbox dispatch 对吗?
> 那么先生成一下
> 这里的这个blackbox_dispatch.py
> 的generate的short term memory吗

这段是首次的阅读顺序问题与建卡请求。随后用户已给出主线复述，以下保留节选：

> 我清楚slime的generate and rm

> 这里通过session id还有instance id能够获得到这里的轨迹结果是我的理解

> 最后在推出的时候再考虑推出这里的环境部分的内容
> 因为创建的sandbox的内容就不再需要被使用了?
> 所以需要终结是我的理解

完整原话与助手逐项校准见[本次讨论参考](../../../../../../../../../../step-000-slime-bridge-and-interfaces/references/generate-memory-revision-proposal.md#user-feedback)。用户随后表示原卡也挺好，重点是下一处读什么；本轮沿原卡进入 init，没有采用参考中的改版候选。上面的技术解释与用户已经表达的认识继续分开。

## 尚不清楚

1. 用户已明确清楚 Slime 的 generate_and_rm；当前问题转为 Paddock、实际沙箱与 state 的关系。
2. init 怎样从 provider 取得环境，state 具体保存什么，本轮开始在[独立函数卡](../../../paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md)展开，理解反馈待记录。
3. register_agent 与 call_agent 如何调用具体后端，尚未展开。
4. Proxy 如何记录每次模型请求、形成 segments，尚未展开。
5. 分段样本的奖励、mask 和训练权重如何保持原任务含义，以及失败重试与取消清理的完整机制，留作后续问题。

<details>
<summary>来源、验证与阅读记录</summary>

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；本机路径 /home/fredkeira/projects/Dressage。2026-11-05 核对 HEAD 与干净工作区。
- 主函数：blackbox_dispatch.py:116–412。环境路径:182–229；注册和调用:232–291；轨迹与正常返回:293–349；失败和 finally:350–412。
- 配置依据：[docs/rollout.md:373](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/rollout.md#L373)。
- 调用者依据：[Slime generate_and_rm](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/rollout/sglang_rollout.py#L224)。采用 Dressage 锁定的 Slime aaf5c2092b01219fa0d5c2d323741d409086ca32；子模块未初始化，从本机另一 Slime 仓库的 Git 对象库只读取得该版本，不用其较新工作区替代。
- 正常返回形状与空轨迹边界：multi_segment.py:118–196。后续奖励和训练转换仅定位接口，没有在本卡展开。
- 版式沿用 BaseAdapter._translate 的栏目与 BaseAdapter._run_turn 的连续阶段、紧邻解释及返回导航；只创建当前 generate 的卡片。
- [Step 000 本次实际讨论](../../../../../../../../../../step-000-slime-bridge-and-interfaces/04-flow.md#generate-first-function-card)。该链接保留 Step 000 的形成过程；Step 001 的 03 保存前序快照，02 用于本步接续。
- 验证范围：静态调用和摘录核对；未启动沙箱、Agent、Proxy 或训练，没有真实输出数值。

</details>
