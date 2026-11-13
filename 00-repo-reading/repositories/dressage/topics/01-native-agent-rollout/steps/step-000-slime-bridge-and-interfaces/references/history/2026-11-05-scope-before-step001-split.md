# 01 · Dressage Step 000：一次黑盒任务怎样交回训练样本

[本步入口](../../README.md) · [项目进度](../../../../../../README.md) · [学习指南](../../../../../../references/design-on-slime.md#reading-guide) · [完整主线](#whole-flow) · [第一处阅读入口](#reading-navigation)

## 1. 阅读目标

**给定一份 sample，Dressage 怎样准备环境、调用 Agent、取得训练轨迹，并把它转换成 Sample 列表交回 Slime？**

1. 主攻 blackbox_dispatch.generate，先建立单次黑盒 rollout 的交接闭环。
2. 分清 Agent 的回答文本与 Proxy 保存的训练轨迹，两者来自同一次执行，但承担不同职责。
3. 读到能够定位输入、环境、调用、轨迹、样本和回收安排即可。TITO、各后端、奖励归一化与训练更新的内部机制留到后续。

## 2. 入口、场景与边界

**第一处打开 [generate 的短期函数卡](../../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)，对照 [blackbox_dispatch.generate，116–412 行](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L116)。** 它把输入任务、Paddock、Proxy 与样本转换接起来，是本次任务的编排入口。

本轮沿既有 scope 选定的正常路径：evaluation=False、claim_prewarm 未返回环境、Agent 调用正常完成、轨迹分段可用。先使用默认黑盒 Paddock 的接口；provider 由配置选择，暂不展开 E2B 或 local_bwrap 的内部实现。题目输入与所需服务配置已提供，沙箱由本次 init 取得，不假定进入 generate 时就已可用。

| 进入时需要知道 | 本步先理解到哪里 |
| --- | --- |
| sample | 一份待执行任务，携带 prompt、metadata 及相关字段；不是已经完成的训练轨迹 |
| args、sampling_params | 运行与采样设置，第一遍不逐项展开配置 |
| paddock | 提供环境生命周期和 Agent 交互操作的对象；通过 provider 取得环境，不把它等同于 Kubernetes 调度器 |
| state | paddock.init 返回的环境访问状态，随后交给 register_agent 和 call_agent |
| proxy_client | 访问模型请求代理的客户端；Proxy 负责转发与记录，地址由配置提供，不保证位于本机 |
| result | 正常路径返回的 list[Sample]；任务奖励与训练字段还有后续 hook 处理 |

本轮已从 generate 的整体阅读进入 [BlackboxAgentPaddock.init](2026-11-05-init-before-ownership-correction.md)，只看环境需求、provider 返回与 state 的正常交接；读完回到 generate 的 register_agent。原有完整主线和后续入口继续保留。

## 3. 整体位置与阅读导航

<a id="whole-flow"></a>

### 3.1 完整主线：Agent 执行期间产生轨迹，完成后交回样本

下面展示调用和跨进程交互，不是一段可执行源码。**[3] 在 [2] 等待 call_agent 期间发生；[5] 是 [2] 在 finally 中安排的后台清理。** 它们不是 generate 依次直接调用的普通子函数。

```text
[1] Slime rollout
      -> configured custom generate hook

[2] blackbox_dispatch.generate                 # Step 000 orchestrator
      -> proxy_client = get_proxy_client()
      -> claim_prewarm(...)                    # selected path: no handle
      -> paddock = get_paddock_from_env(...)
      -> state = await paddock.init(...)        # NOW: read init
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

两条结果通道先保持分开：

| 来源 | 返回到 generate 的内容 | 下一次交接 |
| --- | --- | --- |
| paddock.call_agent | call_payload → agent_response，回答文本 | 与 sample 一起参与样本构造和日志 |
| proxy_client.read_trajectory | trajectory_payload → segments，轨迹分段 | 交给 expand_segments_to_samples 生成训练样本 |

<a id="reading-navigation"></a>
<a id="current-excerpt"></a>

### 3.2 面包屑：从 generate 的调用位置进入，再返回 generate

Slime 的生成 hook → **[generate：主线入口](../../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)** → [paddock.init：当前](2026-11-05-init-before-ownership-correction.md) → 回到 generate → [paddock.call_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L184) → 回到 generate 读取轨迹 → [expand_segments_to_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/multi_segment.py#L118) → 回到 generate 安排清理并返回。

以下为选定正常路径的导航骨架，省略参数、预热未命中时的会话 ID 更新、日志、报告文件及失败包装。maybe_await 保留实际调用形状；前后命令没有配置时可为空。数字 1–5 对应下表的阅读位置，不等于 3.1 的程序阶段。

```python
# [1] generate: selected normal path, no prewarmed handle
initialized = False
paddock = None
try:
    proxy_client = get_proxy_client()
    paddock = get_paddock_from_env(...)
    state = await maybe_await(paddock.init(...))          # [2] 222-228
    initialized = True

    await maybe_await(paddock.register_agent(...))        # 232-241
    await execute_blackbox_cmds_for_stage(...)            # 242-249: before_agent
    register_session_context = getattr(proxy_client, "register_session_context", None)
    if callable(register_session_context):
        await maybe_await(register_session_context(...)) # 255

    call_payload = await maybe_await(paddock.call_agent(...))  # [3] 259-266
    agent_response = agent_response_text(call_payload)             # 285
    await execute_blackbox_cmds_for_stage(...)            # 293-300: after_agent

    await proxy_client.finalize_session(...)              # 301-303
    trajectory_payload = await proxy_client.read_trajectory(...)  # 305-309
    segments = trajectory_payload.get("data") or []
    result = multi_segment.expand_segments_to_samples(...) # [4] 324-331
    return result                                        # [1] 349, after finally
finally:
    if initialized and paddock is not None:
        schedule_terminate_paddock(...)                   # [5] 407-412
```

| 阅读位置与入口 | 本次要弄清什么 | 返回哪里继续 |
| --- | --- | --- |
| 1. [generate](../../02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)，主线入口 | 一份任务怎样连接环境、Agent、两条结果通道与回收安排 | 沿上述主体读完；返回值交给外层 Slime 生成流程 |
| 2. [BlackboxAgentPaddock.init](2026-11-05-init-before-ownership-correction.md)，当前展开正常路径 | 输入的环境需求怎样得到 state；不是直接给出最终任务结果 | 回到 generate:222，下一处是 233 行的 register_agent |
| 3. [BlackboxAgentPaddock.call_agent](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/paddock.py#L184)，先按接口看 | 发送任务并等待本次 Agent 调用完成；模型请求发生在等待期间 | 回到 generate:259，随后在 285 行提取回答文本 |
| 4. [expand_segments_to_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/multi_segment.py#L118)，先按接口看 | segments、sample 和回答怎样交给转换入口，返回值是什么 | 回到 generate:324，取得 result；接着到 349 行返回路径 |
| 5. [schedule_terminate_paddock](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/lifecycle.py#L175)，先按接口看 | 安排后台回收与等待回收完成有什么区别 | 返回 generate 的 finally，完成本次正常返回 |

首轮从第 1 个函数建立主线；用户已确认本轮进入第 2 个 init，查看环境取得与 state 返回。其余位置继续用于辨认交接，不因出现在图中就提前创建短期卡。后续推进时保留这些入口及返回位置，不用新函数的详解覆盖本节。

**停止位置**：能指认 sample 的来路、state 的用途、Agent 回答与轨迹的不同来源、result 的去向，以及 finally 的回收安排。预热命中、异常恢复、token 对齐、分段算法与训练权重语义保留为后续问题。

<details>
<summary>源码定位、选定分支与历史</summary>

- 固定 checkout：/home/fredkeira/projects/Dressage，3e3142fe8ea07e4504c3b20a936a4c201a3de44c；2026-11-05 再次核对，工作区干净。旧 /Users 路径保留在归档原稿中。
- generate:116–412；预热命中/未命中:185–229；正常执行和返回:232–349；完整 finally:389–412。
- 代理接口：[register_session_context](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L95)、[finalize_session](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L64)、[read_trajectory](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L115)。对象来路不清楚时回查 [get_paddock_from_env](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/runtime.py#L165)，读完返回 generate:221。
- 正常路径 finalize_session 后会清除 context_owned 标记，因此上面省略 finally 中的未完成会话上下文清理。失败或取消时该清理可能执行；完整源码保留，不把正常路径骨架当作全部实现。
- 当前公开 provider 是 e2b 和 local_bwrap；Paddock 是交互与生命周期协调层，不是 Docker/Kubernetes 调度器。代理地址按配置传入，不必然是本机服务。
- 本轮先校准 scope 与源码导航，随后按用户请求建立 generate 的首张函数卡；没有初始化环境、调用 Agent、请求模型或运行训练。本轮已按确认建立 init 子函数卡，其余子函数尚未建卡；03 暂无前序继承。
- [调整前的 scope](2026-11-05-scope-before-global-local-navigation.md)保留旧正文、路径和当时说明。
- 版式参考：[Agent Sandbox 的 Kubernetes scope](../../../../../../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-000-sandbox-reconcile/01-scope.md)。只借鉴目标、场景、完整主线和局部导航的分工，不导入该项目的主题编号或记忆继承规则。

</details>
