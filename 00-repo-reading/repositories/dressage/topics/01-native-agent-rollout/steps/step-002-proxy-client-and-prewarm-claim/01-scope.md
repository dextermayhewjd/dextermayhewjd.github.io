# 01 · Dressage Step 002：客户端与预热结果怎样取得

[项目顺序与进度](../../../../README.md) · [上一阅读单元](../step-001-task-identity-and-parameters/01-scope.md) · [下一阅读单元](../step-003-paddock-selection/01-scope.md) · [编号说明](../../../../step-numbering-2026-11-05.md)

本步首轮范围已走完：客户端取得、预热记录来路、等待结果与 handle 回填已说明，用户已概括主要交接。前序记录在 03，本步函数在 02；完整调度与失败回收仍留待后续，不表示全部实现已掌握。已有 init 的阅读成果保留在 Step 004；这里补齐此前的来路，不清零旧认识。

## 1. 本步目标

**准备好任务身份之后，怎样取得 Proxy 客户端，并判断本次是否已经有对应的预热环境？**

本步把“领取结果”和“判断结果”一起看，保证知道接下来走哪条路径。预热调度器怎样预测或安排任务不在本步展开。

## 2. 入口与场景

编排入口：[generate:182–204](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L182)。先短读 [get_proxy_client](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L43)，再看 [claim_prewarm](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/store.py#L217) 的调用与返回。

输入已有 session_id、env_args 与局部标记。分别观察“返回 handle”和“返回 None”两个正常分支；不把函数名中的 claim 当成必然立即成功。

| 需要分清的对象 | 本步用途 |
| --- | --- |
| proxy_client | 访问 Dressage Proxy 的客户端对象，不是在这里启动 Proxy 服务 |
| handle | PrewarmHandle，携带已有 paddock、state、env_args；不要与 provider 返回的 SandboxLease 混为一谈 |
| None | 当前没有可交接的预热结果，需要走未命中后的初始化路径 |

## 3. 上层位置与本步阅读

<a id="whole-flow"></a>

### 3.1 沿用 generate 主线：标出 Step 002 的范围

1. **Step 001：准备运行材料。** 确定会话与任务身份，整理环境、Agent 和采样配置及前后置命令计划，并设置局部变量初值；尚未取得本次要使用的环境。具体函数见[前一步导航](../step-001-task-identity-and-parameters/01-scope.md#reading-navigation)。
2. **Step 002（当前）：取得客户端与预热结果。** 获取 Proxy 客户端，按 session_id 领取预热结果，再判断复用已有环境还是进入后续初始化。

**预热的上游位置**：外层异步 worker 可在派发 sample 前启动预热；本步的 generate 负责按会话 ID 领取。整体关系见 [Step 000 · 3.1 的预热上游补充](../step-000-slime-bridge-and-interfaces/01-scope.md#prewarm-upstream)，当前只回查来路，不展开完整调度策略。

直接沿用 [Step 000 的 3.2 骨架](../step-000-slime-bridge-and-interfaces/01-scope.md#reading-navigation)，保持相同的主要调用和粒度，标明前一步与本步的交接。这里用未命中路径定位整体流程；本步仍要辨认命中和未命中两种结果，具体分支及 handle 字段放在 3.2。

```python
# 教学裁剪：预热未命中的正常路径。
# Step 001：准备任务身份、配置与局部状态。
session_id = ensure_blackbox_session_id(...)       # 执行会话标识
instance_id = _instance_id(...)
env_args = paddock_env_args_from_metadata(...)
initialized = False
paddock = None
try:
    # Step 001：此处省略命令计划、后端选项和采样种子的准备。
    # Step 002 从这里开始。
    proxy_client = get_proxy_client()             # Step 002：取得 Proxy 客户端
    handle = await claim_prewarm(...)              # Step 002：领取预热结果
    # Step 002 到此结束；下面沿预热未命中路径继续。
    ...  # 进入未命中分支，更新 session_id。
    paddock = get_paddock_from_env(...)
    state = await maybe_await(paddock.init(...))
    initialized = True

    await maybe_await(paddock.register_agent(...))  # 注册 Agent
    await execute_blackbox_cmds_for_stage(...)     # 执行 Agent 运行前的命令
    register_session_context = getattr(proxy_client, "register_session_context", None)
    if callable(register_session_context):
        await maybe_await(register_session_context(...))

    call_payload = await maybe_await(paddock.call_agent(...))  # 调用 Agent 执行任务
    agent_response = agent_response_text(call_payload)

    await execute_blackbox_cmds_for_stage(...)     # 执行 Agent 运行后的命令
    await proxy_client.finalize_session(...)
    trajectory_payload = await proxy_client.read_trajectory(...)
    segments = trajectory_payload.get("data") or []
    result = multi_segment.expand_segments_to_samples(...)
    return result                                 # 执行 finally 后才真正返回
finally:
    if initialized and paddock is not None:
        schedule_terminate_paddock(...)            # 安排环境回收
```

这是预热未命中的正常路径示意，不是完整实现。预热命中时会复用已有 paddock/state；模型请求发生在等待 call_agent 期间；finally 安排的回收可能晚于函数返回完成。

<a id="reading-navigation"></a>
<a id="current-excerpt"></a>

### 3.2 本步内部顺序：先取客户端，再领结果并分支

```python
proxy_client = get_proxy_client()                 # [1] 取得客户端对象
...  # 读取预热请求标记并开始计时。
handle = await claim_prewarm(session_id)           # [2] 尝试领取预热结果
...  # 记录等待耗时。
if handle is not None:                           # [3] 使用领取结果
    paddock = handle.paddock
    state = handle.state
    env_args = handle.env_args
    initialized = True
    ...  # 记录命中指标和日志。
else:
    ...  # 未命中时进入 Step 003，本步不展开。
```

| 本步顺序 | 入口 | 读到哪里停 |
| --- | --- | --- |
| 1. 取得 ProxyClient（已展开） | [get_proxy_client](02-short-term-memory/functions/dressage/rollout/generate/runtime.py/get_proxy_client.md) | 看清首次创建与缓存复用、所用地址；不深入 HTTP 连接池或 Proxy 服务端 |
| 2. 领取预热结果（已展开） | [claim_prewarm](02-short-term-memory/functions/dressage/rollout/prewarm/store.py/claim_prewarm.md)；必要时看 [PrewarmStore.claim](02-short-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.claim.md) | 按 session_id 查找并转交结果；已有初始化任务可能仍需等待；没有结果时返回 None |
| 2.1 回查记录来路（已展开） | [PrewarmStore.start](02-short-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md) | 看清 _initialize 定义、create_task 与 task 字段写入；然后返回 claim 的 await record.task。这是阅读回查，运行时 start 发生在领取之前 |
| 3. 使用返回值（已收拢） | [generate:187–204](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L187)；[PrewarmHandle](02-short-term-memory/classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md) | 知道命中时取出哪些对象，为什么不再执行本次 init；未命中时进入下一阅读单元 |

**按需回查预热来路**：generate 只领取，预热由外层异步 worker 经 PrewarmScheduler 提前启动。为什么同一个 session_id 能查到记录，见 [claim 卡的上游交接说明](02-short-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.claim.md#prewarm-origin)；本步不展开完整预取调度策略。

**停止位置**：得到 ProxyClient，并能解释两条后续路径。claim 内部失败/取消先保留其结果与责任边界，预热任务如何批量创建、资源预算和调度策略以后再看。

1. 命中：已有 paddock/state，实际执行接到 [Step 005 注册准备](../step-005-agent-registration/01-scope.md)。
2. 未命中：进入 [Step 003 Paddock 准备](../step-003-paddock-selection/01-scope.md)，随后才调用 Step 004 的 init。

<details>
<summary>源码与阅读边界</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，源码路径 /home/fredkeira/projects/Dressage。
- 本步编排范围：[blackbox_dispatch.generate:182–204](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L182)。
- 依据现行学习指南的[六段主线复核](../../../../references/design-on-slime.md#six-stage-reading-order)；本步只建立边界、源码入口和返回位置，不表示已读懂所有函数。
- 没有运行真实环境或训练；仅为已展开的客户端取得、预热领取及 PrewarmHandle 创建记录。原有记录只按编号顺延，详见编号对照。

</details>
