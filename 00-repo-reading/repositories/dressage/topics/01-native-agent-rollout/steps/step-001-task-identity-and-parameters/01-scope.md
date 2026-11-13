# 01 · Dressage Step 001：任务身份与参数怎样准备

[项目顺序与进度](../../../../README.md) · [上一阅读单元](../step-000-slime-bridge-and-interfaces/01-scope.md) · [下一阅读单元](../step-002-proxy-client-and-prewarm-claim/01-scope.md) · [编号说明](../../../../step-numbering-2026-11-05.md)

本步首轮阅读已收束：已读主要函数，并补齐类型传递、局部初值与采样配置的交接。表中的已展开只记录讲解范围，不表示全部实现已掌握或已运行验证；过程见[阅读记录](04-flow.md)。已有 init 的阅读成果保留在 Step 004；这里补齐此前的来路，不清零旧认识。

## 1. 本步目标

**generate 收到一份 sample 后，怎样得到本次执行的身份、环境参数和后续调用要用的配置？**

这一步对应 Step 000 第 1 段。重点是数据来路和去向，不是 UUID、配置系统或每个日志字段的实现。

## 2. 入口与场景

编排入口：[blackbox_dispatch.generate:126–180](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L126)。首个需要单独短读的函数是 [ensure_blackbox_session_id](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L22)，随后沿同一条数据准备路径继续。

输入是已有 sample、args、sampling_params，采用 evaluation=False 的训练生成场景。只假定 sample 已由上层交入，不假定已经有可用环境。

| 本步已有/准备的数据 | 当前需要辨认 |
| --- | --- |
| sample.metadata | 任务与环境配置的来路，也会写回部分本次执行记录 |
| session_id / instance_id | 执行会话与题目实例的身份，后续用来关联环境、Agent 和轨迹 |
| env_args / blackbox_type | 环境参数与 Agent 类型，不把类型选择等同于已经启动环境 |
| initialized / paddock 等局部变量 | 为之后的运行和清理准备初值，不属于 Paddock 的实例字典 |

## 3. 上层位置与本步阅读

<a id="whole-flow"></a>

### 3.1 沿用 generate 主线：标出 Step 001 的范围

直接沿用 [Step 000 的 3.2 骨架](../step-000-slime-bridge-and-interfaces/01-scope.md#reading-navigation)，保持相同的主要调用和粒度，仅标出本步“任务身份与参数准备”的位置。本步的 metadata、Agent 参数及后续配置细项在 3.2 展开，上层图只保留原骨架的定位粒度。

```python
# Teaching skeleton: normal path, no prewarmed handle.
session_id = ensure_blackbox_session_id(...)       # Step 001: identity and parameters
instance_id = _instance_id(...)
env_args = paddock_env_args_from_metadata(...)
initialized = False
paddock = None
try:
    # End Step 001: detailed parameter preparation is shown in 3.2.
    proxy_client = get_proxy_client()
    handle = await claim_prewarm(...)              # environment
    ...  # Select the miss branch and renew session_id.
    paddock = get_paddock_from_env(...)
    state = await maybe_await(paddock.init(...))
    initialized = True

    await maybe_await(paddock.register_agent(...))  # registration
    await execute_blackbox_cmds_for_stage(...)     # before_agent
    register_session_context = getattr(proxy_client, "register_session_context", None)
    if callable(register_session_context):
        await maybe_await(register_session_context(...))

    call_payload = await maybe_await(paddock.call_agent(...))  # execution
    agent_response = agent_response_text(call_payload)

    await execute_blackbox_cmds_for_stage(...)     # after_agent
    await proxy_client.finalize_session(...)
    trajectory_payload = await proxy_client.read_trajectory(...)
    segments = trajectory_payload.get("data") or []
    result = multi_segment.expand_segments_to_samples(...)
    return result                                 # returned after finally
finally:
    if initialized and paddock is not None:
        schedule_terminate_paddock(...)            # cleanup scheduling
```

这是预热未命中的正常路径示意，不是完整实现。预热命中时会复用已有 paddock/state；模型请求发生在等待 call_agent 期间；finally 安排的回收可能晚于函数返回完成。

<a id="reading-navigation"></a>
<a id="current-excerpt"></a>

### 3.2 本步内部顺序：从 sample 到待使用的运行材料

以下按源码顺序裁剪；为了追踪输入，身份与 metadata 操作保留少量实际参数，其余调用参数省略。

```python
metadata = getattr(sample, "metadata", None)
...  # Normalize metadata, clear errors, initialize execute_cmds.
deterministic_session_id = metadata.get("dressage_deterministic_session_id")
session_id = ensure_blackbox_session_id(sample)    # [1] identities
instance_id = _instance_id(sample)
metadata["session_id"] = session_id
metadata["instance_id"] = instance_id

blackbox_type = normalize_blackbox_type(...)       # [2] environment/Agent parameters
...  # Set extra_env_args when a blackbox_type override is needed.
env_args = paddock_env_args_from_metadata(...)

paddock = None                                    # [3] local lifecycle state
state = None
initialized = False
proxy_client = None
context_owned = False
original_cancelled_error = None
agent_response = ""

# At the beginning of the main try:
execute_cmd_schedule = parse_blackbox_execute_cmds(...)  # [4] later execution settings
backend_options = _backend_options_for_register(...)
...  # Optional sampling_seed handling.
# Stop before get_proxy_client().
```

| 本步顺序与阅读位置 | 对应上方骨架阶段 | 读什么 | 读到哪里停 |
| --- | --- | --- | --- |
| 1. 会话 ID（已展开） | [1] identities | [ensure_blackbox_session_id](02-short-term-memory/functions/dressage/rollout/prewarm/store.py/ensure_blackbox_session_id.md) | 看清 ID 的优先来源、复用或生成，以及写回 sample.session_id |
| 2. 任务实例 ID（已展开） | [1] identities | [instance_id，调用别名 _instance_id](02-short-term-memory/functions/dressage/rollout/artifacts/samples.py/instance_id.md) | 看清 metadata.instance_id、group_index、UUID 的取值顺序，以及它与 session_id 的用途区别 |
| 3. 返回 generate（已说明交接） | [1] identities | [generate:140–141](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L140) | 看清两个返回值怎样写入 metadata，收拢身份准备这一段 |
| 4. 环境与 Agent 参数（已展开） | [2] | [normalize_blackbox_type](02-short-term-memory/functions/dressage/paddock/blackbox/common/defaults.py/normalize_blackbox_type.md)；[generate:142–152](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L142)；[paddock_env_args_from_metadata](02-short-term-memory/functions/dressage/rollout/generate/runtime.py/paddock_env_args_from_metadata.md) | 知道 env_args 怎样从 metadata 取出，blackbox_type 为什么参与当前环境参数 |
| 5. 局部状态初值（已补职责说明） | [3] | [generate：局部状态初值](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#local-state) | 分清占位对象、初始化完成标记和上下文归属标记；不为赋值单独建步骤 |
| 6. 后续调用的配置（已展开） | [4] | [generate:161–180](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L161) | [命令计划](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/parse_blackbox_execute_cmds.md)供执行 hook 使用，[后端选项](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/_backend_options_for_register.md)供注册使用；[采样种子片段](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#sampling-seed)属于 generate，不是独立函数 |

**继续前的概念对照**：

1. **session_id**：标识哪一次执行会话，用来关联该次运行的请求与轨迹。
2. **instance_id**：标识哪个任务实例；它不是沙箱资源编号。
3. **sandbox_id**：标识实际的沙箱资源，由 provider 返回，当前参数准备阶段还没有取得。
4. **env_args**：描述环境配置，包括镜像、超时、命令和附加参数；此处整理配置，尚未创建环境。

同一道题执行两次，可以具有相同的 instance_id、不同的 session_id，并使用不同的沙箱；具体关联依赖上游提供的标识。本轮先读第 6 项，再补第 5 项的职责说明；原代码执行顺序保持不变。

**停止位置**：进入 get_proxy_client 之前，能列出本次身份、环境参数、运行配置和几个生命周期标记。它们是运行材料，不是已经创建好的沙箱或 Agent。

**下一阅读位置**：[Step 002：客户端与预热领取](../step-002-proxy-client-and-prewarm-claim/01-scope.md)。

<details>
<summary>源码与阅读边界</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，源码路径 /home/fredkeira/projects/Dressage。
- 本步编排范围：[blackbox_dispatch.generate:126–180](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L126)。
- 依据现行学习指南的[六段主线复核](../../../../references/design-on-slime.md#six-stage-reading-order)；本步只建立边界、源码入口和返回位置，不表示已读懂所有函数。
- 没有运行真实环境或训练；本步函数卡见[索引](02-short-term-memory/overview.md)；类型规范化按用户要求独立成卡；局部赋值保留必要说明。原有记录只按编号顺延，详见编号对照。

</details>
