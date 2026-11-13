# blackbox_dispatch.generate

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../step-005-agent-registration/03-long-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

[本步 scope](../../../../../../../step-001-task-identity-and-parameters/01-scope.md#reading-navigation) · [当前采样配置片段](#sampling-seed) · [函数索引](../../../../../../../step-001-task-identity-and-parameters/02-short-term-memory/overview.md)

- 源码定位：[dressage/rollout/generate/blackbox_dispatch.py:116–412](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L116)，由助手静态核对。
- 首次接触：Step 000；2026-10-23 定位主流程，2026-11-05 用户明确要求建立本函数卡。
- 最近认识更新：2026-11-05，用户已复述环境取得、Agent 执行、轨迹读取与退出清理的主线，并明确清楚 Slime 的 generate_and_rm；对象身份及数据方向的精确区别仍待反馈。本轮保留原讲解结构，进入 init 回查环境来路。

- 本步调取：2026-11-06，从 [Step 000 原卡](../../../../../../../step-000-slime-bridge-and-interfaces/02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)保留整体职责、历史原话、未知与源码依据；本步只增加准备阶段的局部解释。原卡及其他步骤未修改。
- 本轮重点：generate:126–180；局部赋值和 sampling_seed 分支归在本卡，已有子函数只保留跳转。调取与整理不表示新的理解确认。

- Step 002 调取：2026-11-06，从前序完整记录回顾上层调用。当前只展开 get_proxy_client；下文 Step 001 的准备过程及认识时间保留其历史语境。
- [本步 scope](../../../../../../../step-002-proxy-client-and-prewarm-claim/01-scope.md#reading-navigation) · [当前客户端函数卡](../runtime.py/get_proxy_client.md)

- Step 003 调取：从前步累计模型保留整卡；当前按用户指定先读 [get_paddock_from_env](../runtime.py/get_paddock_from_env.md)，不重读后续执行/轨迹部分。

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

<a id="session-id-on-miss"></a>

### Step 003：预热未命中后，换用新初始化的会话标识（207–214）

**为什么这里再处理 ID**：最初的 session_id 用来领取预热记录。handle 为 None 后，接下来会另行初始化环境；这段让后续初始化与先前的预热尝试使用不同的会话标识。任务本身没换，instance_id 不在这里修改。

本段输入是已有的 session_id、sample、metadata 和前面从 metadata 读取的 deterministic_session_id；只在 handle is None 的分支执行。连续源码如下，去掉外层缩进：

```python
previous_session_id = session_id
if isinstance(deterministic_session_id, str):
    session_id = f"{previous_session_id}-miss"
    sample.session_id = session_id
else:
    sample.session_id = None
    session_id = ensure_blackbox_session_id(sample)
metadata["session_id"] = session_id
```

1. **确定性 ID**：原会话标识后追加 -miss，并同步到 sample.session_id。例如原来为 "bbs-task7-retry-2"，现在为 "bbs-task7-retry-2-miss"。
2. **普通 ID**：先把 sample.session_id 清空，再调用已读的 ensure_blackbox_session_id。因为没有确定性 ID 且旧属性已清空，函数才会生成新 UUID；不清空就会复用旧 ID。函数内部同时写回 sample.session_id。
3. **同步记录**：metadata["session_id"] 保存新值。此后局部变量、sample 属性与 metadata 中的会话标识一致，init、注册和轨迹操作继续使用新标识。

**离开本段**：接着取得 Paddock，将更新后的 session_id、metadata 中的 env_type 和已有 env_args 交给 paddock.init。get_paddock_from_env 只负责返回操作对象；实际初始化是随后单独调用的方法。

**预热没完成会不会误判 miss？** 不会仅因未完成就回退：记录在 start 时已经登记，claim 找到记录后等待已有 Task。新 ID 只区分真正回退后的新尝试，不代替旧环境清理。去重、正常调度顺序与晚到资源的处理边界见[预热进行中与 miss 的区别](../../../../../../../step-003-paddock-selection/references/prewarm-pending-versus-miss.md)。

这段不是重新寻找预热，也不是重新抽取题目。它只调整未命中后这次初始化所用的会话身份；命中预热时不会执行。

源码证据：blackbox_dispatch.py:207–228；已有测试 test_blackbox_dispatch_prewarm_miss_uses_new_session_id 与 test_blackbox_dispatch_uses_deterministic_retry_miss_and_sampling_seed 核对这两条路径。本轮只阅读测试断言，没有运行完整测试或环境。

### 函数内部怎样完成这次处理

下面六段对应同一个 generate 调用。本步展开第 1 段；第 2–6 段保留 Step 000 的整体背景并折叠。代码节选保持实际顺序，已有子函数链接本步卡片，片段不是独立运行入口。

#### 1. 本步：准备身份、环境参数与执行配置（126–180）

这一段的产物是局部变量和更新后的 metadata，不是 generate 的最终返回值；整个函数仍在后面返回训练样本。本段不创建沙箱、不执行命令、不调用模型。

##### 1.1 身份与环境参数（126–152）

先确保 sample.metadata 是字典，清除上一次的错误标记并初始化 execute_cmds 记录。下面连续摘录主要数据交接：

```python
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
```

1. 两个 ID 函数返回的值由 generate 写回 metadata。session_id 关联执行会话，instance_id 关联任务实例。
2. 规范化 blackbox_type。若任务显式提供类型或得到非默认类型，generate 将其装入 extra_env_args；这个条件属于调用者。
3. 环境参数函数从 metadata 筛选配置，并合入 extra_env_args，返回 env_args。下游环境初始化会使用它；预热命中时则采用 handle 中的参数。

| 子函数卡 | 返回后继续做什么 |
| --- | --- |
| [ensure_blackbox_session_id](../../prewarm/store.py/ensure_blackbox_session_id.md)、[instance_id](../../artifacts/samples.py/instance_id.md) | 写回 metadata 的两个 ID 字段 |
| [normalize_blackbox_type](../../../paddock/blackbox/common/defaults.py/normalize_blackbox_type.md) | 按条件准备 extra_env_args |
| [paddock_env_args_from_metadata](../runtime.py/paddock_env_args_from_metadata.md) | 接住 env_args，继续准备局部状态 |

<a id="local-state"></a>

##### 1.2 局部状态初值（153–159）

```python
paddock = None
state = None
initialized = False
proxy_client = None
context_owned = False
original_cancelled_error = None
agent_response = ""
```

1. paddock、state、proxy_client：尚未取得对应的操作对象、环境访问资料和客户端，先置为 None。
2. initialized、context_owned：分别记录环境初始化完成情况和本次调用是否承担 Proxy 会话上下文的清理责任，初始均为 False。
3. original_cancelled_error：留待记录取消异常。agent_response：留待保存 Agent 回答文本。

这里只给本次调用设初值，不创建对象。后续在实际赋值和清理处继续理解；当前不要求预先展开完整生命周期。

##### 1.3 准备命令计划与后端选项（160–168）

```python
try:
    execute_cmd_schedule = parse_blackbox_execute_cmds(
        metadata.get("blackbox_execute_cmds")
    )
    backend_options = _backend_options_for_register(
        args=args,
        metadata=metadata,
        blackbox_type=blackbox_type,
    )
    ...  # The same try continues with sampling configuration below.
```

1. execute_cmd_schedule 接住按 before_agent、after_agent 分类的命令计划，后续交给执行 hook。
2. backend_options 接住按 Agent 类型与本次覆盖项合并的选项，下面的种子分支还可能补充它，随后传给 register_agent。

| 子函数卡 | 返回后继续做什么 |
| --- | --- |
| [parse_blackbox_execute_cmds](../../../paddock/blackbox/execute_hooks.py/parse_blackbox_execute_cmds.md) | 保存计划，继续准备后端选项 |
| [_backend_options_for_register](_backend_options_for_register.md) | 接住选项，进入下面的种子分支 |

<a id="sampling-seed"></a>

##### 1.4 当前片段：补充采样配置（169–181）

**进入前**：已有 sampling_params、metadata 和上一函数返回的 backend_options。本段处在上面的同一个 try 内；为便于阅读，下面统一去掉 try 内缩进，连续源码没有省略分支。

```python
sampling_seed = sampling_params.get("sampling_seed")
if sampling_seed is not None:
    metadata["rollout_sampling_seed"] = int(sampling_seed)
    if isinstance(backend_options, dict):
        backend_options = dict(backend_options)
        proxy_options = backend_options.get("proxy")
        if not isinstance(proxy_options, dict):
            proxy_options = {}
        backend_options["proxy"] = {
            **proxy_options,
            "sampling_mode": "force",
            "sampling_seed_base": int(sampling_seed),
        }
```

1. **取种子**：读取 sampling_params 中的 sampling_seed。没有值或值为 None 时，整段跳过；0 也会进入处理。
2. **记到任务记录**：有值就转为整数，写入 metadata["rollout_sampling_seed"]。这里没有设置 Python 全局随机种子。
3. **补后端配置**：只有 backend_options 为字典时才继续。复制外层字典，取出 proxy 子配置；它不是字典则按空字典处理。
4. **保留其他选项并覆盖种子字段**：新 proxy 字典先展开原选项，再写 sampling_mode="force" 和 sampling_seed_base。因此这两个同名字段采用本段设置的值。

**执行前后示例**（教学构造，backend_options 仅列出相关字段）：

```python
# Before
sampling_params = {"sampling_seed": 42}
metadata = {"instance_id": "task-7"}
backend_options = {"proxy": {"default_temperature": 0.7}}

# After
metadata = {"instance_id": "task-7", "rollout_sampling_seed": 42}
backend_options = {
    "proxy": {
        "default_temperature": 0.7,
        "sampling_mode": "force",
        "sampling_seed_base": 42,
    }
}
```

metadata 被原地更新；backend_options 局部变量指向新字典，其 proxy 也换成新字典。原后端选项字典及其原 proxy 字典不会被这段原地修改。若 backend_options 不是字典，仅记录 metadata，不注入 proxy 选项。

**这里的 proxy 是什么**：backend_options["proxy"] 是配置字典，不是 get_proxy_client 返回的客户端。它经 Agent 注册交给 BlackboxServer 一侧的模型请求代理，影响转发给推理服务的请求参数。

| 字段 | 当前只需理解的含义 |
| --- | --- |
| default_temperature | 请求缺少 temperature 时补入的默认温度；前面示例的 0.7 是教学取值，不是统一固定默认值。默认配置可从 args.rollout_temperature 取得，任务配置可以覆盖 |
| sampling_mode="force" | 对已配置的采样覆盖项，采用代理的设置，即使请求已经提供相应值；它不表示将所有参数都强制重设 |
| sampling_seed_base | 种子基数；该代理用基数加内部请求序号形成 seed，而不是让每条请求都使用相同 seed |

本片段明确设置 mode 和种子基数，没有设置 sampling_temperature。因此原请求已有温度时，default_temperature 并不会仅因 force 模式而覆盖它。这里是 rollout 内模型推理请求的采样控制，不是训练优化器参数。

字段语义静态核对：blackbox_server/proxy/rollout_llm_proxy.py:537–558、blackbox_server/core/models.py 的 ProxyOptions；本轮只核对配置用途，没有展开代理实现或执行推理。

**离开片段**：后面执行 get_proxy_client（Step 002）。带种子的 backend_options 稍后交给 paddock.register_agent；force 和 seed_base 的字段语义见上方，完整请求处理留待 Proxy 阅读。本段不会发起模型请求，也不保证整条 Agent 轨迹完全可复现。

本步只到上述准备阶段。下面保留完整任务的已有模型，供需要时回查。

<details>
<summary>Step 000 已有背景：取得环境 → 注册和调用 Agent → 轨迹转换 → 清理</summary>

<a id="paddock-selection"></a>

**Step 003 当前交接**：handle 为 None 后，generate 先[更新 session_id](#session-id-on-miss)（本轮已补连续片段），再调用 [get_paddock_from_env](../runtime.py/get_paddock_from_env.md) 取得操作对象。返回之后，session_id、env_type、env_args 传入同一对象的 init；本轮停在调用 init 之前。下方历史背景保留完整环境取得过程供定位。

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

1. proxy_client 是访问 Proxy 服务的客户端，随后用于会话收尾和读取轨迹。本步从 [get_proxy_client](../runtime.py/get_proxy_client.md) 展开：返回后接着按 session_id 领取预热结果。
2. claim_prewarm 用 session_id 领取预热结果。命中时直接取得 paddock、state 和 env_args。
3. 本场景走 else：先更新会话标识，再取得 Paddock 对象，调用 init 得到 state。确定性会话标识会加上 `-miss`；其他情况清空后重新生成，后续调用都使用更新后的标识。
4. Paddock 是环境操作与交互协调对象；state 是初始化返回的访问状态，下一段注册 Agent 时还要带上它。
5. initialized=True 表示 init 已正常返回，供退出时判断是否安排回收。这里还没有执行题目。

| 需要回查时进入 | 读完返回哪里 |
| --- | --- |
| [get_paddock_from_env](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L165) | 回到 222 行，用取得的 paddock 调用 init |
| [BlackboxAgentPaddock.init：Step 004（原 001） 展开](../../../paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md) | 接住 state，继续下面的 register_agent |

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

</details>

## 我的直接表述（原话）

Step 002 本轮回填关系的表述：

> 那么这里的内容做的差不多了吗?
> 总结就是如果拿到了这个prewarm的handle了之后
> 就是通过这个handle来设置之前的一系列的内容是我的理解
> 那么之后呢?
> 我还需要做什么呢?

助手校准：这里是复用已有环境资料并设置初始化完成标记；命中后继续注册，未命中则进入后续身份更新与初始化路径。


本步新增（2026-11-06）：

> 我其实不是特别理解
> 这里的内容当前代表的是什么
> 但是之后应该是需要围绕这里看的是我的理解
> 那么我们现在需要看清一下这里的sampling seed吗 还是看什么呢?

用户随后要求：

> 好的那么补充一下本步的generate卡吧

以上分别是对局部状态的疑问和建卡授权，不表示已理解采样配置分支。下面保留 Step 000 的原始表述。


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

完整原话与助手逐项校准见[本次讨论参考](../../../../../../../step-000-slime-bridge-and-interfaces/references/generate-memory-revision-proposal.md#user-feedback)。用户随后表示原卡也挺好，重点是下一处读什么；本轮沿原卡进入 init，没有采用参考中的改版候选。上面的技术解释与用户已经表达的认识继续分开。

本轮补充表述与问题：

> 简单来说就是metadata里面继续加入rollout的samling seed
> 然后这里的proxy部分耕读的偶尔是proxy具体是什么样子的?
> 也就是default是什么 和rollout的inference 部分相关还有这里的sampling mode是什么?
> 那么这一步step算是结束了对吧

用户已表达 metadata 记录种子的理解；proxy 配置字段语义由助手核对补充，不视为用户已掌握代理机制。

Step 003 的本轮追问：

> 这里还是确定session id什么的 我还需要继续看吗?
> 我不是特别理解
> 如果你觉得需要看清楚那么就继续看

助手补充上述未命中 ID 更新片段；仍待用户对其作用表达理解确认。

## 尚不清楚

本步当前未知：局部状态变量的后续使用仍需结合实际调用理解；采样种子只展开配置写入，Proxy 的种子策略及实际可复现程度未验证。下面是 Step 000 调取时的未知快照，旧步骤编号沿用当时语境，不当作本步进度。


1. 用户已明确清楚 Slime 的 generate_and_rm；当前问题转为 Paddock、实际沙箱与 state 的关系。
2. init 怎样从 provider 取得环境，state 具体保存什么，已归入 Step 001 的[独立函数卡](../../../paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md)展开，理解反馈待记录。
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
- 本步记录与片段说明：[Step 001 过程](../../../../../../../step-001-task-identity-and-parameters/04-flow.md)。
- [Step 000 本次实际讨论](../../../../../../../step-000-slime-bridge-and-interfaces/04-flow.md#generate-first-function-card)。scope 继续保存完整主线与面包屑，03 暂无前序继承。
- 验证范围：静态调用和摘录核对；未启动沙箱、Agent、Proxy 或训练，没有真实输出数值。

</details>
