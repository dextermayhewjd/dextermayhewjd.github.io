# 01 · Dressage Step 014：准备并运行 Agent，接清运行中的模型请求

[主题入口](../../README.md) · [项目进度](../../../../README.md) · [前一范围](../step-013-harbor-kubernetes-environment/01-scope.md) · [后续结果范围](../step-015-harbor-results-and-samples/01-scope.md)

> 2026-11-14：按用户确认收窄深入范围。已讨论 Harbor Agent 执行与 Dressage 配置/路由登记；剩余主读为路由激活、Gateway 请求分派与响应出口。公共 Proxy 内部另列补读，不改旧步骤编号或完成状态。当前已进入第三部分的 HTTP 主卡，先看 token 查表；没有真实请求/模型/集群验证。

## 1. 阅读目标

**看清 Harbor 管理的 Agent 怎样接入 Dressage 的模型请求通道：配置地址与身份、登记并激活路由、把请求交给对应 Proxy，再沿本次请求返回响应。**

保留完整链路作定位，深入阅读停在 Gateway 与 RolloutLLMProxy 的交接。RolloutLLMProxy 的协议转换、Dressage Proxy 的生成/记录及 SGLang 合同属于两条路线共享的补读范围，不继续平铺加入本步。

## 2. 指挥官、已有背景与停止位置

1. **Harbor 执行背景已讨论**：Trial._setup_agent → BaseInstalledAgent.setup，以及 _run_agent → _run_agent_phase → ClaudeCode.run；现有卡片按需回看，不重新遍历安装、模板和所有 Agent 分支。
2. **Dressage 运行前准备已讨论**：on_job_start 注入 AgentConfig，_on_start 经租约/Runtime 建立 token 与 Trial/Proxy 的绑定；runtime.call 的线程细节暂缓。
3. **当前待接的主线**：准备结束后的 AGENT_START 激活本轮路由；CLI 发请求后，Gateway 按 token 查表、交给 Proxy，并保留响应出口。只沿普通 Claude Code 路径，无 user-agent、load/resume。
4. **首轮停止位置**：能说明 CLI 使用哪个地址、请求属于哪次尝试、Gateway 交给哪个 Proxy、响应怎样回到同一 HTTP 请求。Agent 执行结束后只接回既有收尾位置，日志/产物/评测交给 Step 015。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

沿用 Step 010、011 的整体主线，各步保持相同图形结构。**本步从环境就绪后继续 Agent.setup，再进入 Agent.run；模型请求发生在等待 Agent 执行的期间。本步深入范围停在 Gateway 对公共 Proxy 的接入边界；后面的协议转换、后端生成和 StepRecord 写入另列共享补读。** 具体入口与返回位置见 3.2；图中回调和 HTTP 均标明交互方式，不当作同一同步调用栈。

图内标注直接对应本步：**[本步]** 是当前展开位置，**[交给 Step …]** 是停止与交接位置；其余节点保留作整体背景。

```python
# 关系示意，不是可执行代码；标记的是本步观察位置。
Slime 的 rollout hook
  -> generate_rollout_harbor_sync                 # 训练入口；API-only 路线不必执行这里。
       -> _run_harbor_rollout -> _run_round -> _run_partition
            -> _CREATE_JOB(job_config)          # 创建 Job 时组成各次尝试的配置。
            -> plugin.on_job_start(job)  # [本步前置回查] 路由配置/回调在运行前登记，不是到这里才执行。
            -> Harbor Job.run
                 -> _run_trials_with_queue -> TrialQueue -> Trial.run  # 队列交接后进入一次尝试。
                      -> _prepare                # 环境与 Agent 准备。
                           -> Environment.start
                                -- 目标接缝 --> K8s 适配 -> Agent Sandbox -> Pod  # 待对齐/验证。
                           -> Agent.setup  # [本步] _setup_agent 调用已选 Agent.setup；安装入口仅短回顾。
                      -> _run
                           -> _run_agent  # [本步] _run_agent_phase 把 instruction/environment/context 交给 Agent.run。
                           -> _collect_artifacts  # [交给 Step 015] Agent 阶段结束后继续日志、产物和评测。
                           -> _run_verifier      # 使用题目的验证规则取得评分。
                      -> _finalize               # 清理环境并发出生命周期事件。
                           == END 事件 ==> plugin._on_end
                                            # 回调内部的轨迹处理留到实际接入时回查。
            <- JobResult
            -> plugin.on_job_end(...)           # 整份 Job 返回后的插件收尾。
            -> _bundle_samples                   # 训练路线的结果转换。
       <- Sample 组与 metrics
  <- RolloutFnTrainOutput

# Agent.run 期间的模型交互，不是等 Trial 结束才发请求：
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务  # [本步] 看 Gateway 接入与响应出口；公共 Proxy 内部另行补读。
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

<a id="routing-reading-purpose"></a>

本轮问题是 **Harbor Agent 怎样接入已有的模型请求通道**。本节分三部分，每部分各有调用骨架和函数导航；第一、第二部分保留已有阅读背景，当前从第三部分继续。

[第一部分：Agent 准备与执行](#reading-part-1) · [第二部分：配置与路由登记](#reading-part-2) · [第三部分：当前接续](#reading-part-3)

编号沿用原来的函数路标，不重新编号。**三部分是阅读组织顺序**：第二部分回查发生得更早的准备工作，真实触发与返回关系在各图中标明；不表示程序先完整跑完第一部分才运行第二部分。

<a id="reading-part-1"></a>

#### 第一部分：Harbor 的 Agent 准备与执行 · 保留已有背景

先恢复“怎样运行到 Claude CLI”。配置来源和 START 路由登记接第二部分；执行期间的激活和 HTTP 请求接第三部分。本段保留原 1–2.2 的入口，按需要回看。

```python
# 普通单步任务：install_only=False，user_agent=None。
Trial.run
  == START ==> plugin._on_start         # 第二部分：登记本次 Trial 的路由。
  -> Trial._prepare
       -> with_default_user(...)
            -> [1] Trial._setup_agent(...)
                 -> [1.1] BaseInstalledAgent.setup(...)
                      -> self.install(environment)  # 具体安装内部仍暂缓。
  <- _prepare 返回
  -> SingleStepTrial._run
       -> [2] SingleStepTrial._run_agent
            -> [2.1] Trial._run_agent_phase(...)
                 -> _emit(AGENT_START)  # 第三部分：激活本轮交互。
                 -> [2.2] ClaudeCode.run(...)
                      == HTTP ==> Gateway  # 第三部分：请求分派与响应出口。
                 -> _emit(AGENT_END)
            -> _sync_agent_output(...)
       -> _upload_agent_logs           # 后续日志、产物与评测交给 Step 015。
```

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 准备包装 · 已讨论 | [Trial._prepare](02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-agent-call) → [Trial._setup_agent](02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent.md#setup-agent-mainline) | 环境交给 Agent.setup，设置准备超时并记录信息 |
| 1.1. Agent 共同准备 · 用途已讨论 | [BaseInstalledAgent.setup](02-short-term-memory/functions/harbor/agents/installed/base.py/BaseInstalledAgent.setup.md#installed-agent-setup-mainline) | 准备目录、委派 install、按需记录版本；具体 install 内部暂缓 |
| 2 前置. 接回执行阶段 · 已回看 | [Trial.run 的 _run 调用](02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#run-call) → [SingleStepTrial._run 的第一项执行](02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) | 只接清 _prepare 返回后如何来到 _run_agent，不重读整段生命周期 |
| 2. 单步任务启动 Agent 执行 · 已讨论 | [SingleStepTrial._run_agent](02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run_agent.md#run-agent-mainline) | 看 instruction/target/timeout/user/load 的交接，正常返回后先同步输出，再继续 _run 的日志上传 |
| 2.1. 共用执行过程 · 主干已展示 | [Trial._run_agent_phase](02-short-term-memory/functions/harbor/trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-mainline) | 看开始记录、三个参数交接与结束回调；返回外层 _run_agent，同步输出 |
| 2.2. 具体 Agent 执行 · 主干已讨论 | [ClaudeCode.run](02-short-term-memory/functions/harbor/agents/installed/claude_code.py/ClaudeCode.run.md#claude-run-mainline) | 看题目如何进入 CLI、日志写到哪里；随后返回执行阶段与输出同步，模型请求路径另追 |

<a id="reading-part-2"></a>

#### 第二部分：Dressage 的配置与路由登记 · 保留已有回查

为了知道第一部分的 CLI 地址和路由从哪里来，回查 Job 运行前的配置，以及某次 Trial START 时的登记。这里保留原 3–3.4 的入口；GatewayRuntime.call 的调度细节仍按需，不恢复为默认必读。

```python
# 较早的运行前准备：修改 AgentConfig，并把事件处理函数交给 Harbor。
_run_partition
  -> [3] plugin.on_job_start(job)
       -> 取得 Gateway 租约与地址
       -> [3.1] _inject_agent_routing(...)  # 写入地址与 token 引用。
       -> 登记 Trial 生命周期回调
  <- 返回后才调用 job.run()

# Job 运行中的某次尝试：通过事件触发登记，不是上面函数继续直接调用。
Trial.run
  == START ==> [3.2] plugin._on_start(event)
       -> [3.3] GatewayLease.register(spec)
            -> [3.3.1] GatewayRuntime.call(...)
                 -- 在网关循环执行 --> [3.4] GatewayRuntime._register(spec)
                      -> _create_proxy(spec)
                      -> self._routes[digest] = binding
                      <- AttemptHandle，经前两层交回 record.handle
  -> Trial._prepare                    # 接回第一部分的准备阶段。
```

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 3. 运行前路由准备 · 用途已讨论 | [on_job_start](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin.on_job_start.md#job-start-mainline) | 取得网关、注入待运行配置、登记回调；返回后才调用 job.run |
| 3.1. 地址与 token 注入 · 按需回查 | [_inject_agent_routing](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/_inject_agent_routing.md#inject-routing-mainline) | 修改 AgentConfig，返回 on_job_start 的配置循环 |
| 3.2. token 与 Trial/Proxy 绑定 · 已接到登记调用 | [DressageHarborPlugin._on_start](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_start.md#trial-start-mainline) | 从 START 事件接真实 trial_id 与已有 token，登记路由并保存 handle；返回事件分发后进入 _prepare |
| 3.3. 租约上的路由登记 · 委派已展示 | [GatewayLease.register](02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayLease.register.md#lease-register-mainline) | 检查租约、委派 Runtime，再将 AttemptHandle 交回 _on_start |
| 3.3.1. 网关循环中的执行 · 机制回查 | [GatewayRuntime.call](02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayRuntime.call.md#runtime-call-mainline) | 看操作投递与结果返回，业务登记由 _register 完成；取消细节暂缓 |
| 3.4. Runtime 实际登记 · 已有卡片 | [GatewayRuntime._register](02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayRuntime._register.md#runtime-register-mainline) | 看 Proxy 与 Trial 资料怎样放入 _routes；返回 handle，供后续操作与请求查表 |

已有卡片保留原话和未解问题，不代表每个内部实现都已掌握。需要恢复背景时在这一部分回看，接清后返回第三部分。

<a id="reading-part-3"></a>

#### 第三部分：路由激活与请求分派 · 当前接续

承接前两部分已有的 Agent、Gateway、路由 binding 和 handle；下面保留此次收窄后的骨架、入口及停止位置。

<a id="current-reading"></a>

> **当前回到：[Trial._run_agent_phase 的结束段](02-short-term-memory/functions/harbor/trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-finish)**，对应第 5 项。只接清正常执行结束与返回，不重读 AGENT_START、Agent 选择和所有环境包装。
>
> **时机**：一次 HTTP 响应并不代表 Agent 已结束；等整个 ClaudeCode.run 正常返回，再记录 finished_at、触发 AGENT_END。结束回调只认本轮请求收尾的用途。
>
> **返回哪里**：外层 _run_agent 在 finally 同步输出，再回到 SingleStepTrial._run 的日志上传；详细日志、产物与评测由 Step 015 接续。
>
> **本步收束边界**：不再新增一批辅助函数。接清这段后可整理接入主线的首轮总结；公共 Proxy 补读和运行验证仍是明确的待办，不据此标为已经完成。

```python
# 正常执行顺序的关系示意；方括号编号与下表对应。
# 前置：START 已登记路由，Trial._prepare 已完成环境与 Agent 准备。
Trial._run_agent_phase
  -> _emit(AGENT_START)
       == 已登记回调 ==> [3.5] plugin._on_agent_start
            -> [3.5.1] record.handle.open_turn(...)  # 必要时短回查：设置 turn、激活路由。
       <- 回到执行阶段
  -> ClaudeCode.run
       == HTTP ==> _GatewayASGI.__call__ -> [4] _GatewayASGI._handle_http
            -> 按 token 找到 binding
            -> binding.proxy.app(...)  # 公共 Proxy：本步只认交接合同。
            <- 经本次请求的 send 返回响应，CLI 继续执行
  -> _emit(AGENT_END)                 # 只接回作用与返回位置。
  <- _run_agent 的 finally 同步输出
  <- SingleStepTrial._run            # 后面的日志、产物与评测交给 Step 015。
```

<a id="reading-sequence"></a>

| 优先级与入口 | 函数定位/已有卡片 | 本轮问题与停止位置 |
| --- | --- | --- |
| **3.5 主卡：激活本轮交互** | [DressageHarborPlugin._on_agent_start](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_agent_start.md#agent-start-mainline) | 从已有 record/handle 得到 turn_id，调用 open_turn 并进入 ACTIVE；返回 _run_agent_phase，随后才运行 Agent |
| **3.5.1 已展开的短回查** | [AttemptHandle.open_turn](02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/AttemptHandle.open_turn.md#open-turn-mainline) | 本轮补看完整短函数，接清已有 Proxy 与 turn_id、ACTIVE；返回 _on_agent_start，不重读 runtime.call |
| **4 主干已讨论：接收与分派 HTTP 请求** | [_GatewayASGI._handle_http](02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/_GatewayASGI._handle_http.md#gateway-http-route) | 请求头 token → 查 binding → 委派 proxy.app → 使用原请求 send 返回；检查/容量/超时先认用途 |
| **5 当前收束：接回已有执行主线** | [Trial._run_agent_phase 结束段](02-short-term-memory/functions/harbor/trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-finish) → [SingleStepTrial._run_agent](02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run_agent.md#run-agent-mainline) → [SingleStepTrial._run](02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) | 只回看结束回调与输出同步的交接，不新开一轮全生命周期阅读；详细结果处理在 Step 015 |

当前已建立 3.5、按需展开的 3.5.1 和第 4 项卡；现在回到第 5 项接清返回，不据此认定所有机制已掌握。其余未进入的辅助函数不提前建卡。上表两张主卡均属于 Dressage；当前不追加 Harbor 专属实现的默认必读项。

### 3.3 公共 Proxy 补读与本步边界

两条路线都复用 RolloutLLMProxy 和 Dressage Proxy。下列内容另列一个共享补读范围，补的是 Topic 01 在 Agent 执行与轨迹收尾之间暂缓的请求/记录链；不重写 Step 006/007 的历史状态。

| 后续共同问题 | 候选源码入口；当前不展开 |
| --- | --- |
| Claude 请求怎样转换并转发，响应怎样转换回来 | RolloutLLMProxy._handle_proxy 及选定的 Anthropic 响应分支 |
| 模型请求怎样生成并记录一步交互 | Dressage Proxy 的 chat_completions / _chat_completions_pipeline；仅追正常生成和记录交接 |
| 默认后端的输入输出合同是什么 | SGLangRouterClient.generate；messages 到 token 的衔接、返回值与记录归属 |

这一补读只追一条正常请求，不通读整个 Proxy。按 2026-11-14 用户确认，入口直接放在 [Topic 01 · Step 006 的原调用位置](../../../01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md#model-request-reading)：send_message → _run_claude_turn 的进程启动段 → 跨 HTTP 进入 Proxy；未读函数实际展开时再建卡，不新增 Step 018。接续为：本步接入边界收束 → Step 006 的公共 Proxy 补读 → Step 015 结果与评测。

**仍按需回查**：_safe、钩子容器、runtime.call 的跨线程/取消、全部网络策略和错误分支。取消/失败路径属于 Step 016；K8s 具体后端与环境合同遗留项仍在 Step 013/Agent Sandbox 专题。

**阅读与验证分开**：本步读通接入合同后可收束首轮阅读，但真实请求、trial/session 归属和响应的运行证据仍单列待办；不能据读过代码声称 Harbor 0.25 与当前 Dressage 已兼容运行。

<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用 v0.25.0 发布提交 fdba28fc411e47e8765420a1a063b4918fce3def；不混用领先该标签的本地 main。
- Dressage 使用 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，原依赖与运行时门禁仍约束 Harbor 0.18，组合运行尚未验证。
- [分为三部分前的 scope](references/history/2026-11-14-before-three-part-reading-navigation.md)保留当时排版；[本次收窄前的完整 scope](references/history/2026-11-14-before-narrowing-agent-routing-scope.md)保留原阅读清单与历史位置；[更早的整体结构](references/history/2026-11-12-before-call-order-scope.md)继续保留。
- Topic 01 曾明确暂缓模型 API 采集内部，见 [Step 007 形成过程](../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/04-flow.md)。后续补读不等于否定此前按范围完成的首轮阅读。
- 本次仅调整范围与导航；既有函数卡和 03 的 98 份继承记录保持，不提前创建未读卡。

</details>
