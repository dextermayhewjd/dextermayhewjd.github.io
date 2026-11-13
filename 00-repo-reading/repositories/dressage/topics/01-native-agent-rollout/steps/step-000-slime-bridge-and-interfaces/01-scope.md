# 01 · Dressage Step 000：一次黑盒任务怎样交回训练样本

[本步入口](README.md) · [项目进度](../../../../README.md) · [学习指南](../../../../references/design-on-slime.md#reading-guide) · [完整主线](#whole-flow) · [第一处阅读入口](#reading-navigation)

## 1. 阅读目标

**给定一份 sample，Dressage 怎样准备环境、调用 Agent、取得训练轨迹，并把它转换成 Sample 列表交回 Slime？**

1. 主攻 blackbox_dispatch.generate，先建立单次黑盒 rollout 的交接闭环。
2. 分清 Agent 的回答文本与 Proxy 保存的训练轨迹，两者来自同一次执行，但承担不同职责。
3. 读到能够定位输入、环境、调用、轨迹、样本和回收安排即可。TITO、各后端、奖励归一化与训练更新的内部机制留到后续。

## 2. 入口、场景与边界

**第一处打开 [generate 的短期函数卡](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)，对照 [blackbox_dispatch.generate，116–412 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L116)。** 它把输入任务、Paddock、Proxy 与样本转换接起来，是本次任务的编排入口。

本轮沿既有 scope 选定的正常路径：evaluation=False、claim_prewarm 未返回环境、Agent 调用正常完成、轨迹分段可用。先使用默认黑盒 Paddock 的接口；provider 由配置选择，暂不展开 E2B 或 local_bwrap 的内部实现。题目输入与所需服务配置已提供，沙箱由本次 init 取得，不假定进入 generate 时就已可用。

| 进入时需要知道 | 本步先理解到哪里 |
| --- | --- |
| sample | 一份待执行任务，携带 prompt、metadata 及相关字段；不是已经完成的训练轨迹 |
| args、sampling_params | 运行与采样设置，第一遍不逐项展开配置 |
| paddock | 提供环境生命周期和 Agent 交互操作的对象；通过 provider 取得环境，不把它等同于 Kubernetes 调度器 |
| state | paddock.init 返回的环境访问状态，随后交给 register_agent 和 call_agent |
| proxy_client | 访问模型请求代理的客户端；Proxy 负责转发与记录，地址由配置提供，不保证位于本机 |
| result | 正常路径返回的 list[Sample]；任务奖励与训练字段还有后续 hook 处理 |

本步保持 generate 的整体阅读深度。环境准备的具体机制进入 [Step 004（原 001）](../step-004-paddock-environment-preparation/01-scope.md)，不继续扩大本步范围。此前在本目录展开过的 init 记录已移入 references/history；正式短期记录归 Step 001。

## 3. 整体位置与阅读导航

<a id="whole-flow"></a>

### 3.1 完整主线：Agent 执行期间产生轨迹，完成后交回样本

下面展示调用和跨进程交互，不是一段可执行源码。**[3] 在 [2] 等待 call_agent 期间发生；[5] 是 [2] 在 finally 中安排的后台清理。** 它们不是 generate 依次直接调用的普通子函数。

```text
[1] Slime rollout
      -> configured custom generate hook

[2] blackbox_dispatch.generate                 # Step 000: overall handoff
      -> proxy_client = get_proxy_client()
      -> claim_prewarm(...)                    # selected path: no handle
      -> paddock = get_paddock_from_env(...)
      -> state = await paddock.init(...)
      -> await paddock.register_agent(...)
      -> before_agent commands                 # only if configured
      -> register session context with Proxy   # when supported
      -> call_payload = await paddock.call_agent(...)
           -- model requests during execution --> [3]
      -> agent_response = agent_response_text(call_payload)
      -> after_agent commands                  # only if configured
      -> await proxy_client.finalize_session(...)
      -> trajectory_payload = await proxy_client.read_trajectory(...)
      -> segments = trajectory_payload.get("data") or []
      -> result = multi_segment.expand_segments_to_samples(...)
      -> finally: schedule_terminate_paddock(...) --> [5]
      -> return result --> [4]

[3] Agent runtime + model service
      Agent -- HTTP --> BlackboxServer LLM proxy --> Dressage Proxy --> SGLang
      Agent <-- response -- BlackboxServer LLM proxy <-- Dressage Proxy <-- SGLang
      Dressage Proxy -> records token/trajectory data

[4] Slime receives list[Sample]
      -> downstream reward and train-data hooks
      -> training                              # later scope

[5] background lifecycle task
      -> terminate or release the environment
      -> may finish after generate has returned
```

1. **进入任务**：Slime 通过配置的生成入口交入 sample。
2. **组织一次黑盒执行**：generate 取得环境和会话状态，调用 Agent，再收集回答与轨迹并转换样本。
3. **执行期间的模型交互**：Agent 的模型请求经过代理到推理服务，训练所需记录在这一过程中产生；不用等 generate 返回才开始记录。
4. **交回训练链路**：正常返回 Sample 列表，奖励后处理与训练数据转换继续由后续配置的 hook 承接。
5. **安排环境回收**：finally 中安排后台清理；安排完成与远端环境已经释放是两个时刻。

**本步在 [2]，需要看清它与 [1]、[3]、[4]、[5] 的交接。** call_agent 返回表示这次 Agent 调用结束，不据此断定整个 Agent 进程或沙箱已经退出。

<a id="prewarm-upstream"></a>

**补充 [1] 的可选上游：谁在进入 generate 前启动预热？**

原图用 Slime rollout 概括了上游。启用预热的 Dressage 异步 worker 会先安排预热，再派发此前取得的任务组；下面补出这段关系，省略中间包装调用。初始化任务可以与其他 rollout 重叠，派发任务不要求它已经完成。

```text
Dressage async rollout worker
  |-- PrewarmScheduler.do_prefetch(...)
  |      -> start_prewarm(...) -> PrewarmStore.start(...)
  |          -> task: paddock.init(...)
  |          -> _records[session_id] = record
  |
  `-- PrewarmScheduler.pop_next_group(...) -> _run_group(...)
         -> Slime generation hooks -> blackbox_dispatch.generate(...)
             -> claim_prewarm(session_id) -> await record.task -> handle
```

1. **提前准备**：调度器取得未来的任务组，为 sample 确定会话 ID，启动环境初始化并登记记录。
2. **随后派发**：同一组 sample 进入生成流程，保留用于匹配的会话 ID。
3. **在 generate 中接手**：按该 ID 查记录，必要时等待初始化；没有记录则走原图中的未命中路径。

这是可选路径，不是每次 generate 调用都会先预热。当前标准调度器在 e2b 后端且预热开关开启时使用这条路径。**Step 000 这里只补整体位置；当前 Step 002 从领取端回查它，不新增调度器精读步骤。** 具体调用点与 ID 如何对上，见 [Step 002 的预热来源说明](../step-002-proxy-client-and-prewarm-claim/02-short-term-memory/functions/dressage/rollout/prewarm/store.py/PrewarmStore.claim.md#prewarm-origin)。

两条结果通道先保持分开：

| 来源 | 返回到 generate 的内容 | 下一次交接 |
| --- | --- | --- |
| paddock.call_agent | call_payload → agent_response，回答文本 | 与 sample 一起参与样本构造和日志 |
| proxy_client.read_trajectory | trajectory_payload → segments，轨迹分段 | 交给 expand_segments_to_samples 生成训练样本 |

<a id="reading-navigation"></a>
<a id="current-excerpt"></a>

### 3.2 本步内部阅读顺序：沿 generate 看完整交接

**本步问题**：任务进来后，环境、Agent、Proxy 与 Sample 转换怎样接起来？

**主读入口**：[blackbox_dispatch.generate](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)。下面 1–6 是本步内部阅读顺序，与原 generate 卡的六段对应；不是六个 Step，也不表示六个子函数已经精读。

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

<details>
<summary>源码、范围调整与历史</summary>

- Dressage 固定提交：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；generate:116–412。首轮正常路径仍为未命中预热环境、Agent 正常返回、轨迹分段可用。
- [已确认的 reference1](references/reference1.md)：Step 001 的 3.1 承接本页 3.2 的 generate 骨架，重新标注 Step 的范围；Step 001 的 3.2 才展开 init。
- [拆分前的完整 scope](references/history/2026-11-05-scope-before-step001-split.md)保留此前的导航、调用边界与来源。generate 原记录继续保留；init 内容完整保存于 Step 001 的 02，早期误放版本已移入历史参考。
- [更早的 scope](references/history/2026-11-05-scope-before-global-local-navigation.md)保留原始结构。
- 本次只是范围和记录组织调整，不代表全部机制已掌握；没有运行真实环境、Agent 或训练。

</details>
