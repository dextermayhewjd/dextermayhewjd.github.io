# 01 · Dressage Step 014：准备并运行 Agent，接清运行中的模型请求

[主题入口](../../../../README.md) · [项目进度](../../../../../../README.md) · [前一范围](../../../step-013-harbor-kubernetes-environment/01-scope.md) · [下一范围](../../../step-015-harbor-results-and-samples/01-scope.md)

> 状态：2026-11-13 用户确认开始本步。已讨论 Trial._setup_agent 与 BaseInstalledAgent.setup，ClaudeCode.run 主干也已讨论，当前澄清配置改写与 Trial 路由登记的阅读边界，_on_start 保留按需回查；具体 install、命令执行后端与网关分派仍未展开。Harbor 依据 v0.25.0 发布版；Step 013 未读接口与适配验证仍保留，没有运行任务、安装、模型或集群验证。

## 1. 阅读目标

**沿 _setup_agent → _run_agent 看选定 Agent 怎样使用环境，再追一条模型请求，对齐路由、尝试身份和响应。**

## 2. 指挥官、入口条件与边界

1. **主线入口**：接 Step 013 后的 [Trial._setup_agent:1880](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/trial.py#L1880)，再回到 SingleStepTrial._run 的 [_run_agent:74](https://github.com/harbor-framework/harbor/blob/fdba28fc411e47e8765420a1a063b4918fce3def/src/harbor/trial/single_step.py#L74)。已读安装关系只短回顾，不通读安装脚本。
2. **已有输入**：选定 Agent、可用环境、题目 instruction；只沿一个 Agent/协议、普通 run（非 resume/load、无 user-agent bridge）阅读。
3. **前置回查**：on_job_start 在 Job 运行前配置路由；START 在 _prepare 前登记尝试；AGENT_START 在 Agent.run 前打开本轮模型交互。各自按原时机回查，不把这些准备统一画成环境启动后的新调用。
4. **停止位置**：能指出 Agent 的实际执行入口、请求目的地、trial/session 对应和响应来源；返回 SingleStepTrial._run 的日志与产物阶段。商用 API 适配只在选用它且确有缺口时深入，不预设必须重建 Proxy。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 Harbor 接入主线中的位置

沿用 Step 010、011 的整体主线，各步保持相同图形结构。**本步从环境就绪后继续 Agent.setup，再进入 Agent.run；模型请求发生在等待 Agent 执行的期间。路由登记只作为必要前置回查。** 具体入口与返回位置见 3.2；图中回调和 HTTP 均标明交互方式，不当作同一同步调用栈。

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
Agent == HTTP ==> Gateway -> Dressage Proxy -> 模型服务  # [本步] 等待 Agent 执行期间追一条请求与响应。
# 只做 API 评估时，调用方也可以从 Harbor Job 进入，不启动 Slime 训练。
```

<a id="reading-navigation"></a>

### 3.2 本步骨架与阅读顺序

下面是普通单步任务的教学裁剪。按编号进入当前局部，弄清交接后回到真实调用方；前置回查、能力对照和验证不会冒写成一条连续执行栈。

<a id="routing-reading-purpose"></a>

**为什么读到这里**：本轮主问题是“Harbor 启动的 Claude CLI，其模型请求怎样进入 Dressage，并对应到正确的 Trial？”阅读中的问题依次是：

- 请求发给谁？回查 on_job_start / _inject_agent_routing，找到 BASE_URL 和 token 配置。
- Gateway 怎样知道 token 属于哪次尝试？回查 Trial START 触发的 _on_start，登记该 Trial 的请求路由。
- 登记操作怎样执行？从 lease.register 进入 runtime.call；这里负责调度，实际登记业务仍在 _register。

2026-11-14 当前先恢复上述目的与位置，不继续展开异步细节或新函数。

<a id="current-reading"></a>

> **当前函数：[GatewayRuntime._register](../../02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayRuntime._register.md#runtime-register-mainline)**。回到实际登记业务，先不继续钩子或跨循环调度细节。
>
> **当前源码归属：Dressage**。plugin.py / gateway.py 位于 dressage/integrations/harbor，目录名 harbor 表示接入目标；它们不是 Harbor 框架源码。对应卡片保存在 functions/dressage/...，此前 Trial/Agent 的卡片则在 functions/harbor/...。
>
> **为什么到这里**：已有 Gateway 地址还不够；网关还需保存“这个 token 对应本次 Trial 的哪个 Proxy”。_on_start 提供 spec，前面的 lease.register / runtime.call 将登记工作交到这里。
>
> **本轮看什么**：创建 Proxy → 构造 binding → self._routes[digest] = binding → 返回 AttemptHandle。再用 HTTP 入口的查表位置确认它的用途，不展开全部请求处理。
>
> **钩子暂时知道多少**：Harbor 在 START 时调用已登记的 Dressage._on_start(event) 即可；这里不是重新把函数传给 emit。
>
> **当前澄清**：登记返回的是 AttemptHandle，binding 留在路由表；模型响应通过原 HTTP 请求的 send 返回 CLI。若继续看请求如何到达和返回，下一处建议 _GatewayASGI._handle_http:864，尚未单独建卡。

导航随实际问题更新；下面的后续行保留职责和源码位置，尚无本步卡片时不预建，也不直接跳往网络源码。


```python
# 正常路径的准备与返回：仍是同一次 Trial。
Trial.run
  == START ==> [3.2] plugin._on_start  # 接清身份与已有 token 后委派登记。
  -> Trial._prepare
       -> with_default_user(...)
            -> [1] Trial._setup_agent(...)
                 -> [1.1] BaseInstalledAgent.setup(...)  # 已读：共同安装准备。
                      -> self.install(environment)       # 具体安装内部暂缓。
            <- 返回 _prepare，完成资料记录。
  <- _prepare 返回
  -> SingleStepTrial._run              # install_only=False，进入执行阶段。
       -> [2] SingleStepTrial._run_agent  # 已接清：交出题目与本次结果对象。
            -> [2.1] Trial._run_agent_phase(...)  # 组织执行并调用 Agent.run。
                 -> AGENT_START 回调
                 -> [2.2] await ClaudeCode.run(...)  # 当前：在环境里启动 CLI。
                      # 等待期间，Agent 发起模型请求。
                      == HTTP ==> Gateway --进程内分派--> RolloutLLMProxy.app -> Dressage Proxy -> 模型后端
                 -> AGENT_END 回调
            -> _sync_agent_output(...)
       -> _upload_agent_logs          # Agent 阶段返回，日志/产物交给 Step 015。

# 这些准备发生得更早，只在解释地址和身份时回查：
[3] plugin.on_job_start  # 已讨论用途：取得网关、修改配置、登记回调。
  -> [3.1] _inject_agent_routing(...)  # 复用已有子卡。
# 上方同一个 START 回调中的登记路径：
[3.2] plugin._on_start -> [3.3] GatewayLease.register
  -> [3.3.1] runtime.call(...) 调度 [3.4] GatewayRuntime._register
  -> GatewayRuntime._create_proxy(...)
```

<a id="reading-sequence"></a>

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. 准备包装 · 已讨论 | [Trial._prepare](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-agent-call) → [Trial._setup_agent](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent.md#setup-agent-mainline) | 环境交给 Agent.setup，设置准备超时并记录信息 |
| 1.1. Agent 共同准备 · 用途已讨论 | [BaseInstalledAgent.setup](../../02-short-term-memory/functions/harbor/agents/installed/base.py/BaseInstalledAgent.setup.md#installed-agent-setup-mainline) | 准备目录、委派 install、按需记录版本；具体 install 内部暂缓 |
| 2 前置. 接回执行阶段 · 已回看 | [Trial.run 的 _run 调用](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial.run.md#run-call) → [SingleStepTrial._run 的第一项执行](../../02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) | 只接清 _prepare 返回后如何来到 _run_agent，不重读整段生命周期 |
| 2. 单步任务启动 Agent 执行 · 已讨论 | [SingleStepTrial._run_agent](../../02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run_agent.md#run-agent-mainline) | 看 instruction/target/timeout/user/load 的交接，正常返回后先同步输出，再继续 _run 的日志上传 |
| 2.1. 共用执行过程 · 主干已展示 | [Trial._run_agent_phase](../../02-short-term-memory/functions/harbor/trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-mainline) | 看开始记录、三个参数交接与结束回调；返回外层 _run_agent，同步输出 |
| 2.2. 具体 Agent 执行 · 主干已讨论 | [ClaudeCode.run](../../02-short-term-memory/functions/harbor/agents/installed/claude_code.py/ClaudeCode.run.md#claude-run-mainline) | 看题目如何进入 CLI、日志写到哪里；随后返回执行阶段与输出同步，模型请求路径另追 |
| 3. 运行前路由准备 · 用途已讨论 | [on_job_start](../../02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin.on_job_start.md#job-start-mainline) | 取得网关、注入待运行配置、登记回调；返回后才调用 job.run |
| 3.1. 地址与 token 注入 · 按需回查 | [_inject_agent_routing](../../02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/_inject_agent_routing.md#inject-routing-mainline) | 修改 AgentConfig，返回 on_job_start 的配置循环 |
| 3.2. token 与 Trial/Proxy 绑定 · 已接到登记调用 | [DressageHarborPlugin._on_start](../../02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_start.md#trial-start-mainline) | 从 START 事件接真实 trial_id 与已有 token，登记路由并保存 handle；返回事件分发后进入 _prepare |
| 3.3. 租约上的路由登记 · 委派已展示 | [GatewayLease.register](../../02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayLease.register.md#lease-register-mainline) | 检查租约、委派 Runtime，再将 AttemptHandle 交回 _on_start |
| 3.3.1. 网关循环中的执行 · 机制回查 | [GatewayRuntime.call](../../02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayRuntime.call.md#runtime-call-mainline) | 看操作投递与结果返回，业务登记由 _register 完成；取消细节暂缓 |
| 3.4. Runtime 实际登记 · 当前 | [GatewayRuntime._register](../../02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayRuntime._register.md#runtime-register-mainline) | 看 Proxy 与 Trial 资料怎样放入 _routes；返回 handle，供后续操作与请求查表 |
| 4. 后端合同与一次响应 · 待进入 | SGLangRouterClient.generate:176，尚无本步卡 | 核对选用后端的协议与返回；未运行的内容只作静态分析 |
| 5. 返回执行主线 · 待进入 | Trial._run_agent_phase:781 → [SingleStepTrial._run](../../02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run.md#single-step-run-mainline) | AGENT_END 后返回并同步输出，再接日志/产物，进入 Step 015 |


**按需前置的停止位置**：本轮在 on_job_start 看清网关、配置与回调三个交接；完整审计、_safe 包装和各回调内部不一并展开。Step 011 的回调连接记录仍可复用。

**实施前要核对，但不另开一轮通读**：Pod 是否能访问所配置地址；所选模型后端是否提供所需协议；Dressage 的版本门禁是否已适配。默认 SGLang token 接口不是普通商业 messages API；模型请求成功也不保证存在可训练轨迹。已有商业 API 工厂仅在确实选用时对照。

**本步局部验证**：一条真实请求和响应、对应的 trial/session、Agent 执行出口。会话 finalize/read 的完整控制交接在 Step 015 用同一次尝试继续，未取得的 token/logprob 如实留缺口。

**读后接续**：回到 SingleStepTrial._run 的日志、产物和 Verifier 调用，进入 [Step 015](../../../step-015-harbor-results-and-samples/01-scope.md)；不把模型请求画成 Agent 返回后的串行下一步。

<details>
<summary>源码版本、历史与验证边界</summary>

- Harbor 使用发布提交 fdba28fc411e47e8765420a1a063b4918fce3def（v0.25.0），本轮按本地 git show 定位相关符号；本地 main 与发布标签有差异，不混用。
- Dressage 源码仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c，依赖和运行时门禁仍限定 Harbor 0.18。本文建立接口阅读路线，不表示已经完成升级；具体适配与验证见既有兼容性记录。
- 既有 Agent Sandbox 与 slime_api_data_collecting 的能力按原记录和当前实际分支核对；已有代码、接口声明与真实运行证据分别登记。
- [调整前 scope](2026-11-12-before-call-order-scope.md)完整保留。本步已进入 ClaudeCode.run；具体 install、后端执行与日志解析仍未逐段读，不因出现在骨架中标为掌握。

</details>
