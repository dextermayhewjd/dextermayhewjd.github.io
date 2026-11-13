# 01 · Dressage Step 003：预热未命中后怎样准备 Paddock

[项目顺序与进度](../../../../README.md) · [上一阅读单元](../step-002-proxy-client-and-prewarm-claim/01-scope.md) · [下一阅读单元](../step-004-paddock-environment-preparation/01-scope.md) · [编号说明](../../../../step-numbering-2026-11-05.md)

本步按首轮范围收束：已说明未命中后的 ID 更新、Paddock 获取、工厂和缓存，以及传给 init 的参数。用户已反馈大致理解；完整调度、失败处理与真实运行不计为已掌握。下一处是 Step 004 的已读 init 回顾，不再增加本步子函数。

## 1. 本步目标

**claim_prewarm 没有交回环境时，怎样更新本次执行身份，并取得负责初始化环境的 Paddock 对象？**

本步只走未命中分支，结束在调用 init 之前；已经读过的环境创建与 state 返回在 Step 004 回顾，不重复展开。

## 2. 入口与场景

编排入口：[generate:204–221](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L204)。先沿当前分支看 ID 更新，再主读 [get_paddock_from_env:165](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L165)。

入口条件：handle is None；此前已有 sample、metadata、session_id、deterministic_session_id 和 env_args。本次 get_paddock_from_env 的 allow_whitebox_mode=False，未显式传 mode；白盒路径和所有自定义后端不作本轮通读。

| 本步区分 | 当前含义 |
| --- | --- |
| 更新后的 session_id | 接下来传给 init 及注册调用的会话身份；instance_id 并未因此重建 |
| Paddock 对象 | 实际创建或复用的 Python 实例，可以调用 init/register_agent 等方法；不是类名或配置草图，也不等于已经创建的沙箱 |
| init 的返回 state | 本步还未取得；下一步执行初始化后才返回 |

## 3. 上层位置与本步阅读

<a id="whole-flow"></a>

### 3.1 沿用 generate 主线：标出 Step 003 的范围

直接沿用 [Step 000 的 3.2 骨架](../step-000-slime-bridge-and-interfaces/01-scope.md#reading-navigation)，保持相同的主要调用和粒度，仅标出本步“未命中后的身份与对象准备”的位置。本步的 ID 更新与 Paddock 选择在 3.2 展开；结束位置是调用 init 之前。

```python
# Teaching skeleton: normal path, no prewarmed handle.
session_id = ensure_blackbox_session_id(...)       # task identity
instance_id = _instance_id(...)
env_args = paddock_env_args_from_metadata(...)
initialized = False
paddock = None
try:
    proxy_client = get_proxy_client()
    handle = await claim_prewarm(...)              # environment
    ...  # Step 003: renew session_id on the selected miss path.
    paddock = get_paddock_from_env(...)            # Step 003: obtain the Paddock object
    # End Step 003: initialization itself belongs to Step 004.
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

<a id="prewarm-before-local-reading"></a>

**阅读 3.2 前：预热记录从哪里来，什么时候需要重新初始化？**

1. **谁提前准备**：启用预热时，外层 rollout worker 通过 Scheduler 调用 PrewarmStore.start，提前安排 paddock.init；具体环境由 provider 创建或取得。
2. **Store 保存什么**：按 session_id 保存初始化 Task、Paddock 和环境参数。记录先建立，初始化可以仍在进行；它不是一张只存“已就绪环境”的表。
3. **generate 怎样接手**：使用同一会话 ID 调用 claim。有记录就等待已有 Task，成功后取得 handle，继续使用已有环境。
4. **回退怎样发生**：没有记录或初始化普通失败，claim 才返回 None；本步随后换用新 ID、取得 Paddock，再交给 init。旧预热的资源清理由对应生命周期流程负责。

| 领取时的情况 | 接下来做什么 |
| --- | --- |
| 有记录，初始化仍在进行 | 等待原 Task，不因为慢就另外创建 |
| 有记录，初始化已成功 | 取得 handle，继续注册 Agent |
| 无记录，或初始化发生普通异常 | 返回 None，进入 Step 003 的未命中分支 |

取消会传播异常，不属于上表的普通 miss。确定性 ID 加 -miss，普通 ID 则重新生成 UUID；**新 ID 用于区分尝试，-miss 本身不是清理指令，当前源码未发现按该后缀执行特殊清理的分支。**

整体位置见 [Step 000 的预热上游关系](../step-000-slime-bridge-and-interfaces/01-scope.md#prewarm-upstream)；具体记录与等待见 [Step 002 的 claim 卡](../step-002-proxy-client-and-prewarm-claim/02-short-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.claim.md)。失败、清理与身份区分的详细说明见[本步参考](references/prewarm-pending-versus-miss.md)。

> **待深入：Rollout worker 与预热调度。** 单条 rollout 的正常闭环走通后，再系统阅读“提前准备哪些任务、准备多少、怎样限制并发、取消与晚到资源怎样回收”。当前只建立启动、记录、领取和回退的关系；阅读时点见[学习指南](../../../../references/design-on-slime.md#rollout-worker-reading-time)。

<a id="reading-navigation"></a>
<a id="current-excerpt"></a>

### 3.2 本步内部顺序：更新身份，取得对象，接到 init

以下为未命中分支的节选，保留决定 ID 的实际判断，省略指标与日志。

```python
# Inside the handle-is-None branch:
previous_session_id = session_id                 # [1] renew attempt identity
if isinstance(deterministic_session_id, str):
    session_id = f"{previous_session_id}-miss"
    sample.session_id = session_id
else:
    sample.session_id = None
    session_id = ensure_blackbox_session_id(sample)
metadata["session_id"] = session_id

paddock = get_paddock_from_env(allow_whitebox_mode=False)  # [2] obtain Paddock
# [3] Stop here: the next call is paddock.init(...), already read in Step 004.
```

| 本步顺序 | 入口 | 读到哪里停 |
| --- | --- | --- |
| 1. 更新会话身份（已补片段） | [generate：未命中后更新 ID](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#session-id-on-miss) | 区分确定性 ID 加 -miss 与清空后重新取得 ID，确认 sample/metadata 写回与后续实参一致 |
| 2. 取得操作对象（已展开） | [get_paddock_from_env](02-short-term-memory/functions/dressage/rollout/generate/runtime.py/get_paddock_from_env.md) | 看清已有对象复用、模式/自定义类选择及工厂返回；不把构造 Paddock 当成创建沙箱 |
| 2.1 下钻工厂（已展开） | [create_paddock_from_env](02-short-term-memory/functions/dressage/paddock/factory.py/create_paddock_from_env.md) | 自定义类优先；否则按 blackbox/whitebox 创建实例。返回第 2 项，继续缓存和返回，不展开各类全部方法 |
| 3. 准备下一次交接（已说明） | [generate:221–228](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L221) | 更新后的 session_id、env_type、env_args 将交给同一个 Paddock 的 init；停止于调用边界 |

**停止位置**：已经取得 Paddock 对象，能说清将哪些参数交给 init；不能在此声称已经得到运行环境或 state。

**下一阅读位置**：[Step 004：环境初始化](../step-004-paddock-environment-preparation/01-scope.md)。这是原先已经读过的 Step 001，保留已有类卡、函数卡和收束状态，主要回顾这次交接。

<details>
<summary>源码与阅读边界</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，源码路径 /home/fredkeira/projects/Dressage。
- 本步编排范围：[blackbox_dispatch.generate:204–221](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L204)。
- 依据现行学习指南的[六段主线复核](../../../../references/design-on-slime.md#six-stage-reading-order)；本步只建立边界、源码入口和返回位置，不表示已读懂所有函数。
- 没有运行真实环境或训练；已为 get_paddock_from_env 与当前工厂函数建卡，调取已有 generate。原有记录只按编号顺延，详见编号对照。

</details>
