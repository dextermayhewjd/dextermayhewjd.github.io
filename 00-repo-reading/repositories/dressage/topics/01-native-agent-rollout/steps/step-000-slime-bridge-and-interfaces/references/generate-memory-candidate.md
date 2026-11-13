# blackbox_dispatch.generate · 短期记忆候选稿

候选 B，供试读，尚未替换正式卡片。[改进方案](generate-memory-revision-proposal.md) · [现行完整卡](../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md) · [scope 完整主线](../01-scope.md#whole-flow)

- 源码定位：[blackbox_dispatch.py:116–412](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L116)，助手静态核对。
- 首次接触：Step 000；2026-10-23 定位主流程，2026-11-05 建立首张函数卡。
- 最近认识更新：2026-11-05，用户已复述任务信息、环境取得、Agent 执行、轨迹交回与退出清理；对象身份和返回方向的精确区别仍待反馈。这里只提出记录方式，正式状态未改。

## LLM 整理：使用场合、具体内容与心智模型

以下是助手按源码整理的解释，与下方用户原话分开。

1. **使用场合**：Slime 将一份待执行的 sample 交给这个自定义生成函数。

2. **具体内容**：组织环境取得、Agent 执行和轨迹收集；将轨迹转换成 Sample，退出时安排环境回收。

3. **建议构建的心智模型**：

   > generate 负责一次任务的交接：把任务交给可用环境中的 Agent，再将本次执行留下的轨迹转换成 Slime 能接收的样本。它同时保留本次环境的回收责任。

4. **调用代码**：本场景 custom_func_path 已配置为 dressage.rollout.generate.blackbox_dispatch.generate。下面两行节选自 Slime 的分派分支，省略中间的签名判断；本函数支持 evaluation 参数。

   ```python
   custom_generate_func = load_function(custom_func_path)
   ...  # Branch for callables accepting evaluation.
   sample = await custom_generate_func(args, sample, sampling_params, evaluation=evaluation)
   ```

## 本场景的输入与输出

当前场景：evaluation=False；未领取到预热 handle；Agent 调用正常完成；Proxy 返回可转换的非空轨迹分段。环境由配置的 provider 提供。以下是静态说明，未取得实际回答、token 或运行标识。

| 进入本函数的参数 | 本轮用途 |
| --- | --- |
| sample | prompt 提供任务消息，metadata 提供身份与环境设置；原 sample 还作为输出样本的模板 |
| args | 后端注册与样本转换所需的运行设置 |
| sampling_params | 此处显式使用可选的 sampling_seed 配置；其余不逐项展开 |
| evaluation=False | 选择训练生成场景；True 会在主 try 之前报错 |

| 离开本函数时 | 去向与边界 |
| --- | --- |
| 正常返回 result，即 list[Sample] | 交回 Slime，继续评分及后续训练数据处理；不是只返回一句回答 |
| 更新过的 sample.metadata/session_id | 保存本次执行的身份及相关记录 |
| 已安排环境清理 | 后台清理可能晚于函数返回完成 |

### 函数内部的六个交接

以下是同一次调用的正常路径节选。保留真实变量与所示调用的实参；统一减少外层缩进，`...` 标记省略，不能拼成完整可运行程序。完整检查、日志、失败包装和配置展开仍可从[现行详细卡](../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)回查；采用此稿时，该链接需改指归档原稿。

<a id="phase-1"></a>

#### 1. 任务信息 → 执行身份与环境参数（126–180）

```python
metadata = getattr(sample, "metadata", None)
...  # Normalize metadata and clear previous error markers.
session_id = ensure_blackbox_session_id(sample)
instance_id = _instance_id(sample)
metadata["session_id"] = session_id
metadata["instance_id"] = instance_id
...  # Resolve blackbox_type and extra_env_args.
env_args = paddock_env_args_from_metadata(
    metadata,
    extra_env_args=extra_env_args,
)
```

1. session_id 标识本次执行会话，instance_id 标识题目实例；它们从 sample 相关信息取得或生成，不能理解成由 image 创建出来的环境。
2. env_args 描述环境需求，稍后交给 init。本阶段还会准备后端选项、前后置命令及清理标记，先知道它们服务于下面的调用即可。

**接下来**：拿 session_id 领取预热结果；没有可用结果时，拿 env_args 初始化环境。

<a id="phase-2"></a>

#### 2. 环境需求 → 可用环境的 state（182–229）

```python
proxy_client = get_proxy_client()
...  # Prewarm metrics.
handle = await claim_prewarm(session_id)
...  # Wait-time measurement.
if handle is not None:
    paddock = handle.paddock
    state = handle.state
    env_args = handle.env_args
    initialized = True
    ...  # Hit metrics and logs.
else:
    ...  # Renew session_id and update sample/metadata after a miss.
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

1. proxy_client 供本函数访问 Dressage Proxy 服务。取得客户端本身不改变 Agent 的请求地址。
2. 命中时使用 handle 中的现成环境状态；本场景未命中，更新会话标识后调用 init，接住 state。
3. Paddock 是操作环境的协调对象，sandbox 是实际环境，state 保存本次访问资料，如 sandbox_url、sandbox_id 和 trajectory_id。两条环境分支最后都回到下面的注册调用。

**按需进入**：[BlackboxAgentPaddock.init](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L64)。读完带着 state 返回[第 3 段](#phase-3)；目前只有源码入口，尚无子函数卡。

<a id="phase-3"></a>

#### 3. state 与后端配置 → 可调用的 Agent 会话（232–255）

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
...  # before_agent commands, then Proxy session-context registration.
```

1. register_agent 使用 state 定位环境，带入题目与会话身份、Agent 类型和后端选项。router_url 将 Proxy 地址交入注册过程，参与配置模型请求路径。
2. 随后执行配置的 before_agent 命令。
3. Proxy 客户端支持时，再登记会话上下文。准备完成后，进入 call_agent 交付任务消息。

**按需进入**：[register_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L153)。读完返回前置操作和会话登记，再到[第 4 段](#phase-4)。本卡保留先后次序，辅助操作的完整代码留作回查。

<a id="phase-4"></a>

#### 4. 任务消息 → Agent 调用结果（256–291）

```python
call_payload = await maybe_await(
    paddock.call_agent(
        state,
        session_id=session_id,
        messages=_chat_messages_from_prompt(sample.prompt),
        metadata={"source": "dressage", **metadata},
    )
)
...  # Selected successful-call branch; failure handling omitted.
agent_response = agent_response_text(call_payload)
```

1. call_agent 接收从 prompt 整理出的 messages，发起调用；call_payload 是等待结束后接住的返回值。随后从中提取 agent_response。
2. Agent 的多轮模型与工具交互发生在这段等待期间。模型请求经过 BlackboxServer 的 LLM proxy 和 Dressage Proxy，Proxy 同时留下轨迹；调用关系见 [scope 全图](../01-scope.md#whole-flow)。
3. 返回表示本次 Agent 调用结束。此时还需要读取轨迹，也还没有完成沙箱释放。

**按需进入**：[call_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L184)。接住 call_payload 后回到本段提取回答，再到[第 5 段](#phase-5)。

<a id="phase-5"></a>

#### 5. Proxy 轨迹与回答 → Sample 列表（293–349）

```python
...  # Execute the configured after_agent commands first.
await proxy_client.finalize_session(
    session_id, instance_id=instance_id, label=getattr(sample, "label", None)
)
context_owned = False
trajectory_payload = await proxy_client.read_trajectory(
    trajectory_id=session_id,
    instance_id=instance_id,
    drain=True,
)
...  # Trajectory artifact logging.
segments = trajectory_payload.get("data") or []
...  # Preserve metadata for sample logs.
result = multi_segment.expand_segments_to_samples(
    sample,
    segments,
    args=args,
    agent_response=agent_response,
    session_id=session_id,
    instance_id=instance_id,
)
...  # Sample artifact logging.
return result
```

1. Agent 调用后先运行 after_agent 命令，再让 Proxy 收尾会话；成功后清除 context_owned 标记。
2. read_trajectory 用本次身份向 Proxy 服务读取记录，返回 trajectory_payload；从 data 字段取出 segments。轨迹保存在服务一侧，ProxyClient 封装读取请求。
3. expand_segments_to_samples 接收 sample、segments 和回答等信息，返回 Sample 列表。一份回答与一份训练轨迹是两路结果，不能相互替代。
4. result 将交回 Slime；Python 在真正返回前，先执行[第 6 段 finally](#phase-6)。

| 按需进入 | 返回本段后做什么 |
| --- | --- |
| [ProxyClient.read_trajectory](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L115) | 接住 trajectory_payload，提取 segments |
| [expand_segments_to_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/multi_segment.py#L118) | 接住 result，进入返回与回收路径 |

<a id="phase-6"></a>

#### 6. 本次环境使用结束 → 安排回收（389–412）

```python
finally:
    ...  # Preserve cancellation; discard unfinished context when needed.
    ...  # The following block is inside the cleanup's nested finally.
    if initialized and paddock is not None:
        schedule_terminate_paddock(
            paddock,
            session_id=session_id,
            env_args=env_args,
        )
```

1. 当前正常路径已经取得环境、收尾会话并取回结果，退出时安排环境终止或释放。原源码用嵌套 finally 保证上下文清理出错时仍能尝试安排环境清理，片段只展示最终交接。
2. schedule_terminate_paddock 安排后台任务；本函数返回时，远端清理可能仍在进行。这里完成后，结果才交回 Slime 的调用处。

**按需进入**：[schedule_terminate_paddock](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L175)。读完返回 generate 的退出路径。

<details>
<summary>本轮只保留的其他路径边界</summary>

1. 预热命中时跳过本次 init，继续注册与执行。
2. 某些 Agent 提前停止仍允许收集已有轨迹，具体判断尚未展开。
3. 主 try 中的普通失败可返回标记为 ABORTED、无梯度的单个 sample；整个函数并非所有路径都返回列表。
4. 取消继续抛出 CancelledError，同时处理退出清理；init 未正常返回时，还需结合 provider 的清理路径判断资源归属。
5. 空 segments 会使转换入口报错；本页选择非空有效分段。

</details>

## 我的直接表述（原话）

2026-11-05，用户明确已有基础：

> 我清楚slime的generate and rm

同轮复述节选，保留原措辞：

> 然后才是这里的看一下是否能够获得这里的prewarm的sandbox
> 如果不恩能够够就获取一个这样子的sandbox也就是这里的paddock?

> 这里通过session id还有instance id能够获得到这里的轨迹结果是我的理解

> 最后在推出的时候再考虑推出这里的环境部分的内容
> 因为创建的sandbox的内容就不再需要被使用了?
> 所以需要终结是我的理解

完整复述与材料反馈保存在[本次讨论原话](generate-memory-revision-proposal.md#user-feedback)，包括关于 image、ProxyClient 和 call_payload 的表述。最初的建卡请求仍保存在[原函数卡](../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)。采用时需保留这些来源，不用助手纠正后的措辞替换原话。

## 尚不清楚

1. Paddock、sandbox、state，以及执行身份与环境配置的区别，已有源码说明，理解反馈待记录。
2. ProxyClient 与 Proxy 服务、call_agent 与 call_payload 的精确分工，已有澄清，尚未据此展开对应函数。
3. init 的环境取得过程、Agent 后端执行、Proxy 记录轨迹和分段样本转换的内部机制，仍按后续问题选择。
4. 失败重试、取消与资源清理的完整配合尚未展开。

<details>
<summary>来源、验证与详细材料</summary>

- Dressage 源码固定为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，路径 /home/fredkeira/projects/Dressage。
- Slime 调用处使用 Dressage 锁定的 aaf5c2092b01219fa0d5c2d323741d409086ca32：[generate_and_rm](https://github.com/THUDM/slime/blob/aaf5c2092b01219fa0d5c2d323741d409086ca32/slime/rollout/sglang_rollout.py#L224)。当前调用代码节选自同一分派分支，不是新增包装。
- 环境身份依据：rollout/prewarm/store.py:22 的 ensure_blackbox_session_id、rollout/artifacts/samples.py:42 的 instance_id；state 字段见 paddock/blackbox/common/state.py:10。
- [Step 000 原始建卡讨论](../04-flow.md#generate-first-function-card)；本次复述暂保存在[候选方案](generate-memory-revision-proposal.md#user-feedback)，正式 flow 未改。
- 详细源码与旧说明仍在[现行完整卡](../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)。这些链接只服务当前对照；以后正式采用时，先归档旧卡并将链接改指历史参考。
- 只做静态核对，不代表实际运行或掌握。当前文件是试读候选，不是新增正式函数卡或进度记录。

</details>
