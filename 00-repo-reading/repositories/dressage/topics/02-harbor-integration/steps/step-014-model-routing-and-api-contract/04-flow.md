# Step 014 · 形成过程

<a id="step014-start"></a>

## 2026-11-13：从同一个 _prepare 进入 Agent 准备

用户在确认 Step 013 的技能上传用途后询问后续入口。助手说明：实际代码仍在 _prepare 内，with_default_user 之后调用 _setup_agent；笔记主题从环境能力转入 Agent 准备，属于 Step 014，但 Step 013 其他接口与验证仍保留待回查。

用户确认：

> 好的 那么看一下这里的这个step014吧

本轮入口固定为 Trial._setup_agent:1880–1894（Harbor v0.25.0，fdba28fc）。只解释 self.agent 与 self.agent_environment 的交接、准备期间的命令环境变量、等待超时及返回位置；具体 Agent.setup 内部尚未展开。沿用注释就地解释、完整外围处理折叠的函数卡形式。

按规则继承 Step 013 的 03 + 02，共 98 份同格式函数/类记录，状态、来源与未知保留；本步仅调取当前调用方 Trial._prepare 并新增 _setup_agent。未将卡片继承或本轮进入记为个人理解，也未进行安装、模型或沙箱运行。


<a id="base-installed-agent-setup-entry"></a>

## 2026-11-13：从 Trial 委派进入 Agent.setup 的实际实现

用户确认 Trial._setup_agent 调用 Agent.setup，并要求继续看具体准备。沿用 Step 012 的 claude-code 静态示例，核对本地 v0.25.0：ClaudeCode 继承 BaseInstalledAgent，没有重写 setup；实际来到 BaseInstalledAgent.setup，self 仍为 ClaudeCode 实例。

本轮只展开共同准备：环境内确保 /installed-agent、本地创建 setup 日志目录、调用 self.install、按需记录版本。安装内部作为下一层保留，未创建 install 卡。父子卡、scope 与进度同步；用户对委派关系的原话保存于 Trial._setup_agent 卡，不预填对新函数的理解。

## 2026-11-13：确认 setup 的基本安装准备职责

用户将当前 setup 概括为完成 Agent 最基本的安装。原话保存至 BaseInstalledAgent.setup 卡。助手确认这一用途理解，并区分 setup 组织准备与 install 执行具体安装；本轮没有继续展开 install，也不将职责理解视为安装细节已掌握。


<a id="run-agent-entry-restored-scope"></a>

## 2026-11-13：恢复 scope 并接入 _run_agent

用户要求继续 run agent，并说明误用 Ctrl+Z 撤销了 scope。检查发现 scope 回退到仅记录 Trial._setup_agent 的版本，BaseInstalledAgent.setup 的 1.1 项及相关交接缺失；本轮按此前记录恢复，再将当前入口更新为 SingleStepTrial._run_agent。

接续路径明确为 BaseInstalledAgent.setup → Trial._setup_agent → Trial._prepare → Trial.run → SingleStepTrial._run → SingleStepTrial._run_agent。调用方 Trial.run 与 SingleStepTrial._run 从 03 完整调取，仅回看当前交接。具体安装内部先保留未知，不因继续执行主线视为已读。

本轮只展开 _run_agent：传入本次结果对象、题目、超时、用户与 load 条件，委派 _run_agent_phase；最后同步 Agent 输出，再回到 _run 的日志上传。共用执行体和实际 Agent.run 是下一层，未提前建卡或声明掌握。scope 的 3.1 保持原有整体主线，3.2 恢复已读入口并接清本次返回/调用关系；所有阅读链接使用本地卡片。


## 2026-11-13：从 TrialConfig 恢复几个 run 的来路

用户忘记 run 从哪里启动，并记得之前有 TrialConfig。本轮仅恢复背景：TrialQueue._execute_trial_with_retries:201–203 用 Trial.create(trial_config) 创建对象、挂接 hooks，再 await trial.run()；当前普通任务使用 Trial.run → _prepare → SingleStepTrial._run → SingleStepTrial._run_agent。TrialConfig 是配置，不是执行入口；实际 Agent.run 尚在下游。

回查目标定位到已调取的 Trial.run 卡，只看 _prepare 返回后的 _run 调用，再通过 SingleStepTrial._run 回到主线 _run_agent。scope 标记临时回查，不重新展开队列、构造器或后续执行体，也未创建新卡。


## 2026-11-13：接回主线，区分 _run_agent 与 _run_agent_phase

用户确认 Trial.run 会进入具体 SingleStepTrial 的执行方法，并询问 run agent 是否就是 run agent phase、当前是否该看 try/finally。助手确认 self._run 的分派关系，同时区分两个真实函数：SingleStepTrial._run_agent 在 try 中 await Trial._run_agent_phase，except 记录两类执行失败，finally 尝试同步日志与 AgentContext。

当前只看清这层组织和输出交接，不预先展开 _run_agent_phase 或 _sync_agent_output 内部。scope 从临时回查位置恢复到 _run_agent；原话保存在当前函数卡。


<a id="run-agent-phase-entry"></a>

## 2026-11-13：进入共用 Agent 执行阶段

用户表示上一层差不多理解，确认看 _run_agent_phase。当前继续普通单步、无 user-agent、无 load/resume 的分支；新卡按建立执行记录、调用 Agent.run、执行段结束三部分组织。题目、环境、AgentContext 是本轮核心交接；完整的网络策略、用户、命令变量、日志、轨迹同步和其他分支折叠保留。

本轮通过 BaseAgent.run 的接口核对 context 是交给 Agent 填写执行信息的记录，返回值为 None；实际填哪些字段尚需看具体 Agent。当前不下潜其 run，也不把函数卡准备好视为学习者掌握整个阶段。


## 2026-11-13：区分 AGENT_START 通知与 run 执行

用户询问 _emit(AGENT_START) 在做什么，是否在传入 instruction/environment/context，并联想到 Gym。核对 Harbor v0.25.0：AGENT_START 是事件类型，_emit 构造带任务名、config、result、lock 的 TrialHookEvent，再依次 await 对应 hooks；三个执行参数是在后面的 run 调用中交给 Agent。

现有 Dressage 固定版本的 on_job_start 注册 _on_agent_start，对应回调在尝试 READY 时 open_turn、递增 turn_sequence 并设为 ACTIVE；只说明生命周期通知的接入用途，不声称此跨版本组合已经跑通。与 Gym 的相似仅是 Agent/Environment 分工，本框架的环境接口主要为 exec 和文件操作。

下一处建议定位到实际 ClaudeCode.run:2122–2233；本轮未展开其实现或创建函数卡，也不将推荐当作已确认阅读。


<a id="claude-code-run-entry"></a>

## 2026-11-13：进入 ClaudeCode.run 的 CLI 启动主干

用户确认“好的 那么我们来看一下这里的这个claude code run吧”。本轮沿普通运行分支，追踪同一份 instruction、environment、context：先准备认证/模型/会话目录和扩展注册，再通过 exec_as_agent 执行 shell 命令，题目由临时环境变量转入 shell 变量，经 printf/stdin 交给 Claude CLI；stream-json 输出合并标准错误后由 tee 写入环境日志。

本轮修正通用接口描述的具体落实：ClaudeCode.run 函数体没有直接写 context，with_prompt_template 仅渲染 instruction。外层 _sync_agent_output 取回日志后，_populate_agent_context 在记录为空时调用 ClaudeCode.populate_context_post_run，尝试解析轨迹并填写指标。这里只核对来源，不展开解析器，不将日志存在当作轨迹或指标已经成功生成。

当前函数卡以配置前置、实际 CLI 启动、返回交接三段组织，完整实现折叠保留；未创建认证、配置注册、exec_as_agent 或日志解析子卡，也未实际运行任何命令或模型请求。


## 2026-11-13：确认 ClaudeCode.run 的 CLI 包装职责

用户概括本函数基于 Claude CLI 组织命令，控制输出位置、格式等，并表示已了解这部分。完整原话保存至 ClaudeCode.run 卡。助手确认这是当前适配层的职责：拼接准备与启动命令，指定执行参数和输出配置；具体任务里的工具调用由运行起来的 Claude Code 执行。

当前只记录这层主干理解，不据此标记后端执行、日志解析、模型路由或整个 Step 014 已完成，也未自动开启下一函数。


## 2026-11-13：请求为什么经过 Gateway 与 RolloutLLMProxy

用户在理解 CLI 启动主干后，询问请求是否会自动从 HTTP 到 Gateway 再到 RolloutLLMProxy。本轮按固定源码回查：plugin.on_job_start 在 Job 执行前调用 _inject_agent_routing，把 Gateway 地址写入 Agent 配置的 ANTHROPIC_BASE_URL，并注入用于区分尝试的 token；后续尝试启动时登记 route/proxy，AGENT_START 打开 turn。

Gateway._handle_http 从请求头提取 token、定位 binding，重写请求后调用 binding.proxy.app；默认 proxy_factory 创建 RolloutLLMProxy。这是进程内 ASGI 分派，不是 Gateway 到另一个 RolloutLLMProxy HTTP 服务的网络跳转。配置缺失或路由未激活时，不会自动获得这条路径。

下一处建议先读 _inject_agent_routing，来源接到已读 _run_partition 的 plugin.on_job_start，再返回 CLI 的请求目的地；当前只完成定位与关系说明，尚未单独建候选函数卡。不同固定版本的组合未进行实际网络/模型验证。


## 2026-11-13：核对路由链已有笔记的位置

用户询问 Dressage 部分是否曾专门记录这段路由。检索现有记录后区分：原生路径在 Step 005 的 ClaudeCodeAdapter.initialize、Step 006 的 CLI 执行卡及 references/cli-output-and-model-api.md 中记录了 CLI 指向沙箱内 RolloutLLMProxy；当前 Harbor 路径的 Gateway 注入与进程内分派，在 Step 014 scope 和本轮 ClaudeCode.run 的“请求目的地从哪里来”段已有概览。

尚无 _inject_agent_routing、on_job_start 或 Gateway HTTP 分派的独立函数卡；研究文档/规划提及与本轮概览，不等于已经逐函数读过。下一处仍建议从路由注入开始，本轮未创建新卡或推进阅读。


## 2026-11-13：明确回查 Topic 01 的哪个步骤

用户澄清问的是 Topic 01 当时哪个 step 专门讲过。核对 scope 与函数卡：没有一整步专门展开“CLI 的每次模型请求如何经代理转发”。Step 005 的 ClaudeCodeAdapter.initialize 提到启动本地 RolloutLLMProxy；Step 006 的 _run_claude_turn 说明构建环境变量、ANTHROPIC_BASE_URL 指向已启动代理；Step 007 重点是执行后的会话收尾与轨迹整理/读取。Topic 01 不包含当前 Harbor Gateway 的路由注入与分派链。


## 2026-11-13：区分 Harbor Agent、原生 Adapter 与 Claude CLI

用户询问 Harbor 与 Dressage 是否各有 Agent，因而会是两个不同系统。核对当前创建/调用链：Dressage _run_partition 创建 Harbor Job 并挂接插件，Harbor Trial._init_agent 通过 AgentFactory 创建 self.agent；当前实际类为 Harbor ClaudeCode，而非 Topic 01 的 ClaudeCodeAdapter。

本轮把两条可选执行路线并列保存在主题 README：原生路径由 Paddock/BlackboxServer/Adapter 驱动 CLI；Harbor 集成路径由 Job/Trial/Harbor Agent 驱动 CLI。当前是一条协作流程，不为同一任务叠加执行两个 Agent。Dressage 继续承担集成、路由、轨迹与训练数据衔接，复用 RolloutLLMProxy 也不等于复用原生 Agent 的运行链。该解释尚待用户反馈，未推进下一函数。


<a id="inject-agent-routing-entry"></a>

## 2026-11-13：进入配置注入，核对收集范围

用户确认继续看如何在 Harbor 中实现路由，同时提出 base URL/proxy 预先定好后是否能在任何部署位置收集 Agent 全部上下文。助手限定：CLI 必须使用配置地址且网络可达，Proxy 处理的是经过它的模型请求与响应；未发送的本地状态、文件或绕过代理的请求不因此被收集。

本轮进入 Dressage 模块函数 _inject_agent_routing，保留父函数 on_job_start 中保存 token、注入配置、写回 trial_config.agent 的连续现场。Harbor v0.25.0 的 AgentFactory.create_agent_from_config 用 resolve_env_vars 解析变量引用，把结果以 extra_env 传给实例，后续执行阶段使用这些配置。当前只做固定版本的静态交接核对，未执行注册、网络或真实凭证操作。

新建当前函数卡并接入 scope/CLI 卡；注册表、路由登记、网关请求分派及完整工厂暂不另建卡。


## 2026-11-13：核对 on_job_start 曾经读到的深度

用户询问此前是否专门看过 job.run 前的 plugin.on_job_start。核对 Step 010 的 _run_partition 第 3 段和 Step 011 的 END 回调记录：已经看过 on_job_start → job.run → on_job_end 的调用顺序，并在 Step 011 为解释 END 事件看过 on_job_start 的回调注册片段。参考明确限定不通读整个函数；当前没有它的独立函数卡。

此前没有沿路由准备逐段展开 AgentConfig.env 的地址/token 注入。本轮 _inject_agent_routing 是对同一个运行前接入点的另一段职责作回查，不表示此前完全没见过 on_job_start，也不表示整个函数已读完。


<a id="on-job-start-expanded"></a>

## 2026-11-13：在 Step 014 补读 on_job_start 的路由准备主干

用户询问能否在 Step 014 展开 on_job_start。本轮按当前请求去向问题，把它补为同一步内的上层入口：取得待运行 TrialConfig 与 Gateway，为各配置准备 token/slot 并调用 _inject_agent_routing，最后登记 Trial 生命周期回调，返回 _run_partition 后才执行 job.run。

新卡采用三段真实交接代码与就地注释，完整检查、网络审计、身份和异常清理折叠保留；没有把所有内部 helper 变为新的必读项。scope 加入 3 on_job_start 与 3.1 注入子卡，不回退 Step 010，也不重开已经讨论的 Job 执行链。具体 route 创建和请求分派仍是后续边界。


## 2026-11-13：收拢准备阶段，建议追某次尝试的路由

用户概括 on_job_start 包含 config、URL、写入配置和回调登记，反馈内容杂、函数多，并表示大致理解 _inject_agent_routing。相关原话分存两张卡。助手将本轮成果收拢为地址、路由身份、回调登记，同时校准 BASE_URL 是地址值、token 是环境变量引用、hook 是函数对象，三者不是同一种引用。

下一处建议 DressageHarborPlugin._on_start:639：这是 Job 运行后由某个 Trial 的 START 事件触发的回调，与整份 Job 运行前调用的 on_job_start 不同。只需看真实 trial_id、已有 slot/token 怎样组成 RouteSpec 并经 lease.register 得到 handle；具体卡片尚未创建，不自动展开全部 Gateway helper。


<a id="trial-start-callback-entry"></a>

## 2026-11-13：建立 _on_start 卡并区分 Job 与 Trial 开始

用户询问刚才是否是一个 Job 开始、现在是否是 Trial 的某个步骤，并要求生成短期记忆。助手校准：on_job_start 在 Job 真正执行前准备配置；_on_start 对应整次 Trial 的 START 事件，位于 Trial.run 初始化结果之后、_prepare 之前，不是内部工作步骤或 AGENT_START。

本轮建立 DressageHarborPlugin._on_start 卡，跟踪 event 的 trial_name/trial_id、已有 slot/token、RouteSpec 和 register 返回的 handle；AttemptRecord 的附加字段、重复事件与旧 token 检查折叠保留。输出是插件状态更新，正常返回 None；回到 START 分发后 Trial 才继续准备。scope 与调用方导航同步，尚未展开 lease.register 或网关请求分派。


## 2026-11-13：纠正从配置回查直接跳到路由登记

用户指出：从 ClaudeCode.run 回看 on_job_start 与 _inject_agent_routing，是为了知道 harness 配置什么时候被改写，不明白为什么突然进入 _on_start。随后询问 _on_start 是否是为了了解 Gateway 在哪里创建、登记，以及它的用途。

助手校准三个问题：on_job_start 中 runtime.acquire 取得/启动 Gateway；_inject_agent_routing 改写 AgentConfig；_on_start 为已有 Gateway 登记某次 Trial 的 token/身份及对应 Proxy；请求到达后 _GatewayASGI._handle_http 才按 token 分派。此前把“接着了解路由登记”作为当然的下一步，没有明确阅读问题已经变化。

本轮将 scope 改为明确目的的导航：仅问 CLI 配置改写时，回查到 on_job_start/注入/写回配置即接回 ClaudeCode.run；继续问 token 如何对应 Trial 与 Proxy 时，再回查 _on_start。既有卡片与历史保留，不删除已建立材料，也不标记用户已掌握注册或网关内部。


## 2026-11-13：明确目的后继续 _on_start 卡片

用户在区分 Gateway 创建、配置改写、Trial 路由登记与请求分派后，确认“好的 那么开始看一下这个函数的short term memory吧”。本次沿已有 _on_start 卡片继续，目的固定为把 Trial 身份与已有路由凭证接起来，不再默认为配置回查的必然下钻。

当前先看四个输入动作：从 START 事件取 trial_name/trial_id、按 trial_name 找 on_job_start 保存的 slot、取得注册表、按 slot_id 取当前 token。这些是已有数据的接合，尚未进入 RouteSpec/register 的实现。scope 与唯一进度同步，保留前一轮纠正的历史。


## 2026-11-13：先明确钩子归属，再解释 register 与 handle

用户反馈在理解整体用途之前就看到 handle/register 和输入输出，无法判断是谁留出的钩子。助手核对 Harbor Job.on_trial_started、Trial._emit 与 Dressage GatewayLease.register/AttemptHandle.open_turn，先建立分工：Harbor 提供 START 的登记/触发机制，Dressage 注册 _on_start 回调；回调执行时向 Dressage 自己的 Gateway 登记本次 Trial 的路由。两种登记不同，返回的 AttemptHandle 是操作这条路由的对象，不是再次注册的回调。

本轮在 _on_start 卡的输入输出之前补入上述用途、双方归属和两种登记对照，并简化 register 行的注释。先解决整体职责，再沿具体数据继续，不将解释补齐记作用户已理解。


## 2026-11-13：接清事件链，确认下一候选为 GatewayLease.register

用户串起 Harbor 的 Trial 发出 START、进入 DressageHarborPlugin._on_start，再调用 lease.register，并询问是否接着看这个函数。助手确认主线并校准名词：Harbor 提供钩子机制，START 是事件；register 登记的是已有 Gateway 中本次 Trial 的路由，而不是创建/登记整个网关。

下一处建议按真实委派看 GatewayLease.register:389，再经 runtime.call 调度进入 GatewayRuntime._register:594；后者才包含实际 route/proxy 登记和 AttemptHandle 构造。本轮仅核对定位并保存推荐，未提前建卡或标为已读。


<a id="gateway-lease-register-entry"></a>

## 2026-11-13：进入 GatewayLease.register

用户确认看 GatewayLease.register。本轮为短函数建卡，输入从 _on_start 的 spec 与已有租约接入，职责限于释放检查、把 _register 操作交给 runtime.call、将 AttemptHandle 返回调用方。lambda 表达稍后执行的操作，runtime.call 负责在 Gateway 所属循环执行并交回结果；本轮没有展开其跨线程/取消机制。

scope 和父卡连接实际委派，下一候选保留 GatewayRuntime._register:594，尚未提前建卡。没有执行 Gateway、注册路由或操作模型。


<a id="gateway-runtime-call-entry"></a>

## 2026-11-13：补清 runtime.call 的执行位置与返回

用户表示不理解 lease.register 中的 runtime.call，询问是否需要查看。本轮建立 GatewayRuntime.call 卡，先解释 runtime 是管理网关线程/循环的对象，call 接收本次登记操作；同一循环直接 await，不同循环投递 submit，在网关循环创建 Task，完成后通过 Future 把结果传回调用方。

主干限于正常执行与返回，完整取消/异常/竞态保护折叠保留；与生命周期事件钩子登记区分，不自动扩展为完整异步课程或继续登记业务。_register 仍作为后续入口，未提前建卡或执行线程实验。


## 2026-11-14：恢复 on_start / lease.register 的阅读动机

用户表示忘记 on_start 的 lease.register，以及为什么开始读这一系列内容。本轮不重启整个 Job/Trial 阅读，也不继续异步内部；先恢复问题链：Claude CLI 请求发给谁 → on_job_start 注入地址/token；Gateway 如何对应到本次 Trial → START 回调 _on_start 登记路由；登记如何执行 → lease.register 委派 runtime.call。call 的线程/循环机制是这项登记的执行支撑，实际路由创建仍在未展开的 _register。

scope 3.2 补入问题来路，runtime.call 卡开头回链该位置；只记录当前需要提醒的背景，不把遗忘表述视为清零此前理解或把复习标为新增掌握。


## 2026-11-14：区分请求分派与响应返回

用户将登记理解为记住 Sandbox 的信息、知道消息应发还给谁。助手核对 Gateway._handle_http：从请求头取 token 查 binding，调用该 binding.proxy.app，并通过包裹原 send 的 _ActivitySend 返回响应。因此需要登记的是 token 对应的 Trial/Proxy 及会话关联；响应仍沿原 HTTP 请求连接返回，不另登记 Sandbox 回传地址。

澄清补入 _on_start 卡，未推进到网关函数的逐段阅读。


<a id="runtime-register-business-entry"></a>

## 2026-11-14：从事件与调度包装回到实际路由登记

用户表示仍不理解 Gateway 系统及 register 的用途，不确定是否要继续读钩子实现，并再次感到混乱。助手纠正此前连续下钻包装层造成业务动作不明显的问题：当前真正需要读的是 GatewayRuntime._register，先看创建 Proxy、建立 _RouteBinding、保存到 self._routes，以及返回 AttemptHandle。

新卡在输入输出之前交代用途，并用 _handle_http 的 token 查表位置说明这张表如何被后续请求消费。钩子只保留“登记时保存处理函数、发出 START 时调用它并传入 event”的约定；不再扩展事件或跨循环内部。调用包装卡保留并回链实际业务，当前不把未知机制一并标为已掌握，也没有运行网关。


## 2026-11-14：区分登记返回对象与模型响应通道

用户复述了回调登记、lease.register、runtime.call、创建 Proxy 与 binding 的主线，并追问绑定记录是否就是返回给调用方的对象，以及收到模型响应后怎样找到 Sandbox。原话：

> 我简单理解一下
> 首先呢是这里在on trial started
> 的时候把这个on start传输进去?
> 然后这个on start 当中呢
> 又有一个lease register的部分会登记这个spec
> 然后这里又会需要看一下这个gateway 的register到底在做什么
> 发现这里的这个runtime gateway是一个有io的部分
> 所以使用了runtime的call
> 然后需要通过runtime register spec的方式把这个登记操作交给runtime调度
> 然后在通过这个这个具体的这个创建默认的proxy什么的
> 然后通过这个routebind了之后把trial资料和proxy放在了一起
> 最后返还调用方这个binding?
> 也就是这里的这个请求之后应该返还到哪里?
> 是我的理解
> 那么还有什么是需要做的吗?
> 我的理解是这里的这个网关就是知道这个这个trial了之后
>
> 假设之前的sandbox向这个网关发送内容
> 网关之前就记录下来了这个sandbox
> 在收到请求之后是怎么知道在发送给sglang这类之后
> 然后把得到的消息反向传送给这里的这个sandbox的呢?

助手核对并区分：runtime.call 保证操作在网关所属事件循环执行；_register 将 binding 留在 _routes，返回的是 AttemptHandle。路由按 token 关联 Trial 与 Proxy，不以 Sandbox 回传地址作表项。每次 HTTP 请求有自己的响应出口 send，Gateway 将它交给对应 proxy.app，上游结果经协议转换后作为该请求的响应传回；流式结果也沿同一请求的响应流返回。不同上游跳转各有自己的请求/响应关系，不是一条跨越全部服务的连接。

本轮只用 gateway.py:938–943、_ActivitySend:1014–1018 和 RolloutLLMProxy 的 StreamingResponse 返回片段核对响应通道，没有展开全部 HTTP 处理；下一处候选为 _GatewayASGI._handle_http，尚未单独建卡。


## 2026-11-14：确认 Gateway 与响应处理的记录归属

用户询问这些内容是否应放在 Dressage，而非 Harbor 部分。助手确认：Harbor 的 Job/Trial 提供钩子与生命周期；Dressage 的 plugin.py 实现响应钩子的处理函数，gateway.py 实现路由登记、HTTP 分派与响应出口衔接。现有 Gateway 卡片已经位于 Step 014 的 functions/dressage/integrations/harbor/gateway.py；目录名 harbor 表示集成目标，不改变源码归属。

本轮只在 scope 标清源码切换。整条链继续保留在同一个集成步骤中，不搬动既有 Harbor 卡、不另开主题，也不提前建立尚未逐段阅读的 _handle_http 卡。


## 2026-11-14：按确认边界收窄 Step 014 的剩余函数

用户在讨论 Step 014 过重及 Topic 01 公共 Proxy 留白后表示“好的 那么按照这个方式 / 看一下step我们需要看什么short term function吧”。本轮据此收窄本步深入范围，保留整体图和已有卡片，剩余主读为 _on_agent_start 与 _GatewayASGI._handle_http，AttemptHandle.open_turn 作第一处的必要短回查。先读完激活再回到 CLI 发请求的位置，不把这两处写成 _register 的直接子调用。

原来准备放在本步的 RolloutLLMProxy 协议转换、Dressage Proxy 生成/StepRecord 记录和 SGLang 合同另列共享补读，暂不创建新步骤编号或未读函数卡；后续再接 Step 015。原 scope 归档保留，03 继承记录与旧步骤历史不改。本轮仅整理范围与入口，没有开始新的函数讲解或运行验证。


## 2026-11-14：同时保留旧导航与当前接续，按三部分组织

用户认可收窄后的骨架与导航，同时要求保留之前 3.2，并考虑用第一、第二、第三部分来组织。本轮恢复旧导航到正文：第一部分保留 Harbor Agent 准备与执行（原 1–2.2）；第二部分保留 Dressage 配置与路由登记（原 3–3.4）；第三部分保留当前待接的激活、HTTP 分派与返回（3.5–5）。每部分分别展示调用骨架和对应表，不把已有入口只藏在归档或一个总表中。

编号继续作为阅读路标；明确第二部分是对较早运行前准备的回查，三部分顺序不冒充程序执行先后。3.1 全景与 3.3 公共 Proxy 补读边界保持，尚未读的入口不提前建卡，当前下一处仍为 _on_agent_start。改排版前的 scope 另存历史快照，阅读状态没有推进。


<a id="third-part-agent-start"></a>

## 2026-11-14：开始第三部分，建立 _on_agent_start 卡

用户确认开始第三部分并要求建立函数卡。本轮只创建 DressageHarborPlugin._on_agent_start：从 Harbor _run_agent_phase 的 AGENT_START 事件进入，已有 _on_start 登记的 READY 路由与 handle；先确定 turn_id，调用 open_turn，递增轮次并将插件记录设为 ACTIVE，返回后才继续 Agent 执行。

完整短函数保留原语句，只加就地注释；区分插件 record.phase 与网关 binding.state，后者由 handle.open_turn 内部更新。open_turn 只核对效果，未单独建卡，也未展开公共 Proxy 的 turn 机制或重读 Runtime 调度。scope 的前两部分保留，第三部分 3.5 接入本地卡片；HTTP 主卡尚未展开。


## 2026-11-14：区分查记录、已绑定 Proxy 与 turn_id

用户概括通过 event 查看记录，认为 trial_id/turn_sequence 生成的 turn_id 可能用于找到 Proxy，并询问下一入口。核对 _record_for_event 与 AttemptHandle.open_turn 后，助手分清：event 的 (trial_name, trial_id) 用于查 self._attempts，record.handle 已持有 binding，binding 已持有 Proxy；turn_id 只是交给该 Proxy 的本轮标识。ACTIVE 是运行对象的状态更新，不等于轨迹持久化。

本轮按范围作 open_turn 的最小关系回查，未新建辅助卡或重开完整 Trial/调度链。下一主读建议 _GatewayASGI._handle_http，以真实 HTTP 请求中的 token 查 binding 和响应出口为问题，尚未开始该函数。


<a id="open-turn-short-read"></a>

## 2026-11-14：因追问补读 3.5.1，而非默认跳过

用户要求继续下一函数，并问为什么不继续 3.5.1。助手先说此前短核对过，随后明确校准：源码已核对和接口效果已说明，不等于已经带用户读完整函数。既然用户在此需要连接，本轮先为 AttemptHandle.open_turn 建立短卡并展开，暂不同时进入第 4 项 HTTP 主卡。

卡片保留完整短函数与就地注释，先接已有 handle/binding/Proxy，再看 turn_id 传递与网关 ACTIVE 状态，正常返回 _on_agent_start 后由插件更新轮次和 record.phase。Runtime 调度和公共 Proxy 内部继续暂缓；scope 将 3.5.1 标成当前短回查，主读范围没有扩成完整代理机制。


<a id="gateway-http-entry"></a>

## 2026-11-14：保留 operation 疑问，进入 HTTP 主卡

用户概括 open_turn 为已找到的 Proxy 打开本轮交互，追问为何另定义 operation，同时要求继续下一部分。助手补充：operation 将相关操作组合成 call 所需的无参可调用对象，并直接使用当前 self/turn_id；定义时不执行，runtime.call 安排执行并等待结果。具体线程机制仍作为未解问题保留，不因继续阅读标为掌握。

本轮进入第三部分第 4 项 _GatewayASGI._handle_http，来源明确为 CLI 的 HTTP 请求 → Web 服务器调用 _GatewayASGI.__call__ → 当前函数。卡片按查 token/路由、准备请求、委派并返回响应组织；当前带读先停在第一段，完整检查折叠，公共 Proxy 处理仍不展开。scope 保留前两部分与既有卡，后续未知继续留存。


## 2026-11-14：收拢 HTTP 服务的主干与阅读停止标准

用户觉得 HTTP 函数内容杂，不确定还要单独看什么，并尝试概括查路由、准备请求、发出请求和 idle/timeout。助手核对 _dispatch_with_idle_timeout 后，把本函数收拢为 token 查 binding、请求整形、进程内调用对应 Proxy.app、通过原 send 返回四步。真正向上游发送 HTTP 的工作属于公共 Proxy；本函数的 idle timeout 关注响应活动，不等同于 Agent 总执行超时。

本轮不新建 token、改写、缓冲接收、响应包装或容量控制卡；这些先按职责理解。路径/凭证/路由状态/大小/并发与超时属于服务保护，当前不平铺展开。后续只需接回已有执行结束位置，公共 Proxy 深入、结果解析与评测继续按既定边界安排；未宣称用户已完全理解或 Step 014 已完成。


## 2026-11-14：回到执行阶段的结束与返回位置

用户概括 _run_agent_phase 的开始事件、Agent 选择、环境变量、超时和结束回调，询问本步还有什么需要读。助手确认其正常编排主线，并校准环境变量是配置给命令使用；当前要回看的位置是整个 ClaudeCode.run 完成后的 finally，而不是从 AGENT_START 重读。一次模型 HTTP 响应返回后 CLI 仍可继续工作，不能直接跳成整段 Agent 已结束。

本轮在已有 phase 卡中补清 AGENT_END 的正常职责：Dressage._on_agent_end 委派 quiesce，等待本轮请求收尾并恢复 READY；不新建清理辅助卡。随后外层 _run_agent 的 finally 同步输出，再回 _run 的日志、产物、评测阶段。scope 第 5 项标明当前返回位置，接清后可收束首轮；公共 Proxy 补读与真实运行仍保留待办，未标记全步完成。


## 2026-11-14：确认从 CLI 启动处原位接入公共 Proxy 补读

用户最终确认公共 Proxy 补读直接进入 Topic 01 的既有 Step 006，而非新增 Step 018：从 send_message 的 Task 调用链接到 _run_claude_turn，在 CLI 启动后的原位跨 HTTP 接 Proxy。已同步本步 3.3 的跳转；公共处理函数仍待实际展开，本步原有接入边界及验证未知保留。
