# 大规模 RL 的环境供给：本仓库值得学什么

> 2026-11-04 用户已确认后续重点为 Kubernetes 沙箱工程。当前具体范围以[五项学习主线](tencent-k8s-learning-scope.md)为准；本页保留原有 RL 对照、12 组材料与讨论依据。

[项目入口与唯一进度](../README.md) · [岗位原文](../../../../slime_photo/code-reading/job-evidence/2026-10-28-user-provided-jd.md)

2026-11-03，按用户的三个问题做源码选题核对。当前 checkout 为 `37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1`，工作区干净；相较首次登记的 `400df364753adb9e36a61f93c506166856998590` 已更新。本次核心 controllers/extensions 无差异，examples 有新增和修改，尤其新增了 Harbor 示例说明。保留上次版本归属。

这是助手的源码分析与阅读建议，不是已读函数清单，不代表用户掌握，也没有运行 Kubernetes、训练或性能实验。

<a id="learning-scope"></a>

## 当前阅读口径：目标、材料与观察问题的对应

用户再次指出：

> 这里的这个内容和 我要看的12个一样吗?
> 还是说不一样?
> 请重新考虑一下 我到底需要的是什么?

本次修正：第 4 节的 12 组是仓库材料索引；第 6 节及此前聊天中的 rollout 独立性、Ready、取消、故障与回收，是阅读这些实现时的观察问题。两者有重叠但层级不同，不相加为新的必读清单。只讲后者也不完整，会遗漏用户明确提出的不同 Agent 与安全需求，并把部分应由训练框架处理的业务策略误当成这个仓库的学习交付。

按用户原始三项需求与“大规模 RL”背景，统一采用下表来判断材料的用途和深度。此后用户要求固定当前范围；2026-11-04 又回贴该讨论并要求打开 Step 00 scope。四项目标沿用，不再另增学习清单；各函数仍随实际阅读展开，材料出现于表中不表示已读。

| 学习目标 | 第 4 节材料对应 | 要学到什么程度 |
| --- | --- | --- |
| 预热怎样服务于训练批次 | 1、2 为主，5 按需 | 连接训练需求、备用池、领取与补充；能解释热命中和持续供给的条件 |
| 不同任务/环境怎样统一接入 | 3、10，结合 2 的 Task/回调 | 看清运行配置、任务初始化、交互与 reward 接口的分工；选一种非 coding 环境核对抽象边界 |
| 不同 Agent 怎样运行并受到隔离约束 | 4、9、11、12 | 对比 Agent 在沙箱内运行与仅把工具执行放进沙箱；看清 CLI/协议、凭据、网络和运行时隔离的责任。选代表实现，不逐个读所有 CLI |
| 上述能力怎样支撑持续、大规模 rollout | 2 为主，6、7、8 按问题进入 | 在主线中考察并发预算、领取一致性、取消清理、环境污染和持续吞吐；专门的准入/APF/CNI 优化由具体问题触发 |

用户当前请求是确定这个仓库对腾讯 Agent 强化学习框架岗位的学习增量。Slime 用于解释框架侧背景；尚未要求实现 Slime 与 Agent Sandbox 的实际代码集成。模型训练、组采样策略、样本过滤和奖励规则只说明接缝，不自动新增为本仓库必读主题。

下文保留此前源码依据与讨论；学习范围按本节统一理解。2026-11-04 经完整批次流程核对，用户确认首读 run_naive，见 [Step 000 scope](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/01-scope.md)；唯一进度继续维护在项目 README。

## 1. 目标：为训练持续提供合适、可用、可清理的环境

用户的新问题使阅读重心从“一个 Sandbox 怎样创建 Pod”转向“批量 rollout 怎样获得环境”。前者成为必要时回查的下层机制。

本仓库的增量主要在三个连接处：

1. **训练需求 → 预热计划**：哪些镜像、每种多少环境、什么时候预热、放在哪个集群？
2. **预热计划 → Kubernetes 供给**：怎样补足备用环境、领取时转移归属、观察可用状态、处理不足与失败？
3. **环境 → 任务执行**：不同任务怎样接入命令/文件或其他运行时接口，怎样收回资源并避免上一轮污染下一轮？

这直接关联 JD 职责 1/2/3/4/5，以及要求 3 的 Kubernetes、要求 5 的性能稳定性；但仓库里的环境基础设施不自动提供模型训练、完整轨迹和策略更新。Slime 已读内容继续作为训练侧背景。

## 2. 预热分两层看

### 2.1 Kubernetes 侧：维持一批尚未领取的 Sandbox

关系骨架（资源关系，非同步函数调用链）：

```text
SandboxTemplate --> SandboxWarmPool --> pool-owned Sandbox --> Pod
                           ^                 |
                           | refill          | adoption
                           |                 v
                    remaining reserve    SandboxClaim-owned Sandbox
```

- Template 保存环境蓝图；WarmPool 通过 `spec.sandboxTemplateRef.name` 引用它。
- WarmPool 的 `spec.replicas` 是池中备用 Sandbox 的目标数量；`status.readyReplicas` 才是观察到的 Ready 数量。
- WarmPool controller 创建的是 **Sandbox CR**；核心 Sandbox controller 再管理 Pod 等资源。
- Claim 通过 `spec.warmPoolRef.name` 请求环境。领取会移除池成员标签，将 Sandbox 的 controller owner 从 WarmPool 转给 Claim。池因此出现缺口并补充。
- 无可用候选时，Claim controller 可以走冷创建。不能把“请求了 warm pool”等同于必然热命中。
- 正常释放会删除 Claim 并走资源清理；默认不是把用过的容器放回干净备用池。

因此预热 100 个备用环境不等于整个集群最多 100 个环境：已经领取的环境与补充的备用环境可以并存。容量预算要同时看备用、正在执行、正在终止的资源。

源码入口：

| 问题 | 固定版本源码 |
| --- | --- |
| 本轮池协调的指挥官 | [SandboxWarmPoolReconciler.Reconcile:435](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L435) |
| 统计、补充、缩减备用数量 | [reconcilePool:491](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L491) |
| 从模板构造 Sandbox CR | [buildSandboxCR:1135](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L1135) |
| 领取与冷创建的分派 | [SandboxClaimReconciler.reconcileActive:580](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L580) |
| 找已有绑定或尝试池候选 | [getOrCreateSandbox:2230](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L2230) |
| 转移资源归属 | [completeAdoption:1478](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L1478) |

`reconcilePool` 中值得以后带问题研究的规模机制：把 terminating 资源计入创建预算；通过 expectations 等待 informer 观察到已发出的创建/删除，避免旧缓存导致重复扩容；按批次与速率补充；资源不足或 scheduling gate 未解除时避免反复删建。这些不是第一轮就要全部展开的前置。

### 2.2 训练侧：提前告诉池需要什么

`examples/agent-sandbox-rl` 已是一个 Python 编排包，不能仅因放在 examples 就视为几行演示。其范围包括：

- `Task(id, image, metadata)` 与任务数据源。
- `SandboxFleet` 的规划、预热、领取、释放及多集群放置。
- `naive`、`sliding`、`pipelined` 等预热策略。全量预热、限制同时驻留的镜像窗口、重叠下一窗口预热与本窗口执行，是不同取舍。
- `LookaheadWarmer.add(batch_id, counts)` / `finish(batch_id)`：调用方提供每批的 `image → 需求数量`，维护相应的池与副本数。它不自行预测训练器的下一批。
- `prepull` 缓存镜像与预先运行的 Sandbox 是不同层次；只有镜像缓存仍可能要等调度、容器启动和应用就绪。

可回查的短骨架：[run_naive:82](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82) 调用 `fleet.setup()`，然后交给执行器；默认 [process_parallel:34](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L34) 为每个任务做 `acquire → process_fn(task, handle) → release`。

[LookaheadWarmer.add:149](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/lookahead.py#L149) 经内部协调计算 create/scale/remove，调用 Fleet 的 `warm_image`、`set_pool_replicas`、`unwarm_image`。这是后续理解“这一批 rollout 尚在跑，提前准备下一批环境”的直接入口。

HPA/KEDA 则是按指标调整备用数量的另一种控制方式。训练器已知未来批次时可利用显式 lookahead；不能把指标驱动扩缩当作预知未来，也不应让多个写入者无协调地同时控制同一池的 replicas。

## 3. 不同环境与题目：已有抽象及边界

### 3.1 三种职责不要揉成一个 Sandbox

| 层次 | 本仓库已有接口 | 它没有自动替你完成的事 |
| --- | --- | --- |
| 环境运行条件 | `SandboxBlueprint` / `SandboxTemplate`：PodSpec、镜像、资源、存储；模板还有网络与注入策略 | 定义某道题的成功标准 |
| 环境申请与使用 | `SandboxClaim`、SDK、`SandboxHandle`、命令/文件接口 | 把任意浏览器、机器人或游戏动作翻译成运行时协议 |
| 任务/episode | Fleet 的 `Task` + `process_fn`；Gymnasium 的 `reset/step/close`、RewardFn、TerminationFn | 通用数据集语义、所有模态的观察空间、完整 RL 算法与训练轨迹 |

[Task:159](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/sources.py#L159) 的 metadata 对核心编排层是不透明的，由 callback/adapter 使用；它不会自动解析题目并准备 workspace。

[SandboxEnv.reset/step:102](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/clients/integrations/gymnasium/k8s_agent_sandbox_gymnasium/gymnasium_env.py#L102) 采用新 Claim 开始 episode，执行 shell 字符串动作，将 stdout/stderr 构成文本观察，再调用可替换的奖励/终止函数。浏览器截图、点击动作等需要额外适配，不能因为用了 Gymnasium 就视为通用环境已实现。

`clients/integrations/nemo-gym` 是另一种接法：按镜像映射到指定池，将执行和文件接口接到外部 NeMo Gym provider。其 README 明确指出 resources 来自模板、entrypoint 不支持按次覆盖；执行超时放弃 HTTP 请求也不必然停止容器内进程。这些合同是接入训练时要核查的实际边界。

### 3.2 兼顾题目差异和热命中

可采用的设计思路：按兼容的运行配置分池，稳定的工具/依赖/资源条件提前准备；领取后再通过文件与执行接口初始化题目。浏览器环境、Python 数据分析环境、代码仓库环境可以有不同模板。具体题目的 seed、输入数据与 reward 由任务层管理。

这个思路有两条源码约束：

1. Claim 指定 `spec.env` 或 `spec.volumeClaimTemplates` 会强制冷启动，而且模板注入策略可能直接拒绝这些覆盖。容器创建时的 env 与领取后给某次进程传入的 env 是不同事情。见 [Claim API](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/api/v1beta1/sandboxclaim_types.go) 与 [Template API](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/api/v1beta1/sandboxtemplate_types.go)。
2. 当前 Fleet 主要按 image 规划，Task 本身不包含任意独立资源策略。相同镜像但不同权限、CPU/内存或租户要求时，仍需明确分组、模板/配置或适配设计；不能把“同镜像”自动当作“同环境合同”。

复用也有边界：`agent-sandbox-rl` 的 `recycle=True` 是实验功能，当前 `GitRestoreReset` 面向 Git workspace，还涉及进程与临时文件清理；不能拿它证明任意环境都能完全 reset。默认新 Claim 与“复用已用过的同一沙箱”要分开理解。污染会影响 reward 的可比性。

<a id="adapter-roles"></a>

### 3.3 agent_sandbox_rl/adapters 中三个模块的职责

2026-11-04，用户选择先看 SWE-bench，并询问三个 adapter 是否差不多。它们都连接外部任务或工具与 Fleet，但适配的层次不同。

| 模块 | 主要输入与输出 | 负责的连接 |
| --- | --- | --- |
| swebench.py | 数据集行 → Task；已领取 handle → 探针文本 | SweBenchSource 加载任务；swebench_probe 提供轻量环境探测 |
| r2egym.py | 含完整题目 metadata 的 handle → R2E-Gym RepoEnv | 将已领取环境接入 R2E-Gym 的交互与评分接口，复用其任务逻辑 |
| openhands.py | Fleet/Task 或已领取 handle → OpenHands 工作区 | 对接 OpenHands 的工作区、执行通道和相关运行环境配置 |

1. 它们不是同一个接口的三个可直接互换的实现。
2. SWE-bench 数据加载与 R2E-Gym 环境适配可以组合：SweBenchSource(keep_row=True) 将完整行保存到 Task.metadata["ds"]，供后续 make_fleet_repo_env 使用。
3. swebench_probe 只执行 READY、Git/目录探针并返回文本，不包含解题 Agent 或完整的 SWE-bench 评测。
4. run_swebench_fleet.py 的实际 process_fn 是 _record(swebench_probe) 生成的 fn，它把探针文本与任务/环境标识一起装入结果字典。

固定源码依据：同一 37ced32 版本的 adapters/swebench.py:40、66、97，adapters/r2egym.py:314，adapters/openhands.py:318、353，以及 examples/run_swebench_fleet.py:92、116。当前具体阅读见 [swebench_probe 函数卡](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/swebench_probe.md)。

## 4. examples 与腾讯 JD：优先筛选 12 组

当前 `examples/` 直接子目录中有 **68 个包含 README.md 的目录**。这是目录统计，不是可运行性计数或岗位覆盖率；未逐个执行。下表是根据目录说明、关键配置与主线源码筛出的 12 组阅读材料，分组不等于 12 个正式 Step。

所有路径相对源码仓库根目录。

| 组 | 材料 | 对应问题 / JD | 投入建议 |
| --- | --- | --- | --- |
| 1 | `examples/warmpool-quickstart` | 模板、备用池、申请的资源合同；要求 3 | 最先看三种对象。所附 claim 带 PVC override，会冷启动，热路径示例应省去该覆盖并满足模板策略 |
| 2 | `examples/agent-sandbox-rl` | 批次、镜像、多集群、并发预算、清理；职责 1/4/5 | 核心增量；按问题选 Fleet、lookahead 和容量机制 |
| 3 | `examples/agent-sandbox-gymnasium` 及 `rllib`，`clients/integrations/gymnasium`、`nemo-gym` | episode 与环境接口、奖励/终止可替换；职责 2/3/5，加分项 2 | 先读一条接入路径。RLlib 示例是 CPU 文件任务，不是完整 LLM RL |
| 4 | `examples/ray-integration` | Ray rollout actor 如何把工具执行交给沙箱；职责 2/4、要求 3 | 重点看执行边界与回传，不重读模型循环 |
| 5 | `examples/hpa-swp-scaling`、`keda-scale-to-zero` | 随需求调整备用容量；职责 4、要求 3 | 后读。例子依赖 GKE 指标设施；缩到零后的首次请求不能保证热命中 |
| 6 | `examples/kueue-agent-sandbox` | 资源不足时的准入与配额；职责 4、要求 3 | 批量并发后再读；Kueue 负责准入，不代替训练调度 |
| 7 | `examples/apf-insulation` | API Server 争用中区分领取关键请求与后台补池；职责 4 | 出现控制面瓶颈时读；不是所有负载都能提速 |
| 8 | `examples/agent-sandbox-rl-network-policy` | 大量模板时网络策略与标签成本；职责 4、要求 3 | 后读；使用 Unmanaged 时要有外部策略，不能只关管理 |
| 9 | `examples/claude-code-sandbox`、`agentclientprotocol` | headless CLI、会话、执行协议；职责 2/3，加分项 1/2/4 | 复用已有 CLI 知识，只读 K8s/执行边界增量 |
| 10 | `examples/chrome-sandbox`、`playwright-sandbox`、`gemini-cu-sandbox` | 非纯 coding 的浏览器/Computer Use 环境；职责 2/3 | 用于看不同运行条件。Playwright README 仍以 Docker 路径为主，不视为完整 K8s RL 接入 |
| 11 | `examples/kata-gke-sandbox`、`warmpool-quickstart/secure-sandboxtemplate.yaml` | RuntimeClass、gVisor/Kata、网络/权限边界；要求 3、职责 4 | 选一种运行时验证；云特定配置不能直接当作腾讯环境配置 |
| 12 | `examples/containarium-execution-scoped-token` | 长寿命沙箱中的单次执行凭据与撤销；职责 2/4、要求 5 | 明确有跨执行凭据需求时读；它依赖外部凭据代理与 Cilium，不是默认内建保障 |

Claude 例子确实提供 SDK 驱动、Secret 注入及会话恢复；模板没有指定强隔离 RuntimeClass，不能因它是 Sandbox 就声称默认使用 gVisor。Secret 放进容器也不等于容器内进程看不到凭据。

本次在 `examples/` 和 `clients/integrations/` 文本检索未找到 Codex 专用实现。`clients/integrations/openai` 是 OpenAI Agents SDK 的 prototype，不能等同于 Codex CLI 适配；ACP 也要求目标 agent 实际支持相应协议。更换 CLI 仍需检查启动、鉴权、会话、输出和超时合同。没有据此断言无法运行 Codex。

另外两项保留为可选：

- `examples/podsnapshot-golden-warmpool`：GKE Pod Snapshot 扩展下，从预初始化的内存/文件系统快照准备环境。与普通预热和删除 Pod 的 Suspended 模式不同；不是原生 Kubernetes 通用快照保证。
- `examples/harbor-terminal-bench`：新 README 描述每 trial 使用 Claim，题目镜像与结果文件对接很相关。但它引用的 `clients/integrations/harbor` **在本次 checkout 不存在**，不能当作已核对可运行的集成，只列作待补证据。

## 5. 阅读推荐与停止位置

按照用户现在的目标，第一处建议改为 **`SandboxWarmPoolReconciler.Reconcile`**，通过它进入 `reconcilePool`，第一轮只问：“目标备用 3 个，当前只有 1 个时，谁发现差额、创建什么对象、把实际数量写到哪里？”保留“未领取的备用”与“已领取执行中”的区别。

后续候选按需求关系接续：池的补充 → Claim 的领取/归属/清理 → Fleet/Lookahead 的训练需求映射 → 一种环境接口 → 有证据的规模或隔离问题。若要先从 Python 应用端看整体，`run_naive` 是短的备选骨架。

2026-11-03 这次核对只保存方向调整与源码依据，没有自动建立 Step 000、函数卡片或认定上述模块已读完。2026-11-04 按用户后续请求建立了 [Step 000 scope](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/01-scope.md)；当前进度只维护在项目 README。

## 6. 用户进一步限定：围绕强化学习框架接入

用户追问还需考虑哪些学习内容，随后强调：

> 重点是这个强化学习框架对应上

因此后续按训练框架的实际交接选题。沿用已读 Slime 作为背景；下表是接入责任分析，不声称两个仓库已集成，也不另开通用 Kubernetes 运维课程。

| 强化学习框架中的问题 | 从 Agent Sandbox 学的机制 | 仍由训练框架或接入层负责 |
| --- | --- | --- |
| 一个任务应获得什么环境？ | Template/Claim、Fleet Task 的镜像映射、SDK 文件与执行接口 | 把 dataset/task/seed 映射到环境配置，准备题目初始状态；Sandbox CR 本身不解释题意 |
| 同一道题采样 G 条 rollout，环境怎样独立？ | 多个 Claim、新环境与实验性 recycle/reset 的区别 | 为每条 rollout 分配环境并保证可比较的初始条件；维护 group/rollout 身份，不能因同镜像就让并发 rollout 共享可变 workspace |
| 训练器什么时候可以开始交互？ | Sandbox/Claim Ready、运行时探测、命令与文件通道 | 验证题目初始化也已完成；基础设施 Ready 不等于任务语义已准备好 |
| 多轮 agent 怎样使用环境并被取消？ | SDK command executor、sandboxd 进程生命周期、连接后端 | 将工具调用映射到运行时；处理 rollout 超时/取消/重试。网络重试不自动提供命令 exactly-once；有副作用的命令不能一律重放 |
| 环境故障怎样影响训练样本？ | 分辨 Claim/Pod/网络/命令错误，取得输出与退出状态 | 区分“agent 答错”与“环境故障”；决定重试、过滤还是标记无效，维护组完整性，不能默认把基础设施故障当作低 reward |
| 连续批次怎样得到足够环境且最终释放？ | Lookahead/Fleet、池的补充、Claim 生命周期与清理 | 提供未来批次需求与并发预算；先取回评分所需产物再释放，处理 driver 崩溃与残留资源，验证补池速度是否跟得上持续消费 |

模型通道和环境通道也要分开：沿用此前 Slime 的 adapter/轨迹主线，沙箱接入需要让 agent 能访问相应模型代理，并使工具结果回到 rollout。Agent Sandbox 提供环境与执行机制，不因此接管 token/logprob、训练 mask、策略更新或 rollout 分组逻辑。

本次补充源码证据（同一 `37ced32` 版本）：

- `controllers/sandbox_controller.go::computeReadyCondition`：检查 Pod Running、Ready、IP 及按需 Service；没有判断题目数据或评分器是否已经准备好。
- `extensions/controllers/sandboxclaim_controller.go::adoptSandboxFromCandidates`：领取涉及 Claim 更新和 Sandbox 归属更新，处理版本冲突及中途状态恢复；资源领取一致性不等同于任务执行 exactly-once。
- `clients/python/agentic-sandbox-client/k8s_agent_sandbox/commands/command_executor.py::CommandExecutor.run`：区分请求等待的 timeout 与命令运行的 command_timeout；具体行为依赖运行时，旧版运行时可能忽略后者。
- `packages/sandboxd/pkg/server/process.go`：有流取消时清理进程组、执行超时与进程终止路径。不能把此前某个 NeMo Gym HTTP 适配的超时限制推广到所有后端。
- `examples/agent-sandbox-rl/agent_sandbox_rl/reaper.py`：有按 run 标签清理的工具，需要外部触发及正确识别存活任务，不是训练进程一死就自动执行。
- `docs/performance-tuning.md`：区分预先充满池的一次领取突发和持续领取同时补池；文档测量结果不能作为当前训练负载的吞吐保证。

第一阶段仍建议只接通 **任务 → 环境预热/领取 → 一次工具交互 → 输出交付 → 释放**。组采样、取消和环境失败是沿这条主线追加的问题。APF、池分片、多集群、快照等只在接入或实测瓶颈需要时深入；上一节的 12 组材料是候选库，不是必须通读的课程。

<details>
<summary>用户本次需求原文</summary>

> 我对于这里的需求更多的在与 我希望能够通过这个agent sandbox
> 看一下在大规模的强化学习训练当中
> 有什么需要在这个repo上学习的?
> 下面是几个对于这个repo的猜想和需求
> 1. 我需要进行强化学习训练,有些情况下我需要这里的sandbox能够通过预热的方法,来提前准备
> 并且希望是通过k8s的手段实现,我需要看哪些地方
> 2. 但是这里又不能够是单纯的只是coding的场景,我想要知道这里的有没有针对于不同环境和题目
> 对于这里的sandbox的比较好的抽象的构建?
> 3. 考虑到这里的claude和codex或者不同的内容,或者安全
> 这里的examples里面
> 有多少是可以和腾讯的job description对应上的呢?

</details>


<a id="kubernetes-priority-for-tencent"></a>

## 2026-11-04 · 转向 Kubernetes 控制器是否更贴合腾讯混元岗位

用户问：“以及这里的k8s的内容是否更加符合腾讯混元的这个岗位呢?”。依据仍为已保存的完整 JD，不据此推断招聘方实际使用本仓库，也不作为重新核实招聘状态。

结论：在已经阅读 Slime/Agent 链路和 Fleet 基本用法的背景下，把 Agent Sandbox 的后续精读投入放到 Kubernetes 侧，比继续深入同类 Python 预热编排更直接补足岗位要求。岗位整体仍是 Agent 框架研发，不能缩减成纯 Kubernetes 运维岗位。

| 已保存 JD 的明确内容 | Agent Sandbox 对应学习点 |
| --- | --- |
| 要求 3：熟悉 Kubernetes、容器化，具备集群开发、部署、排障或性能优化经验 | Sandbox 与 Pod/Service/PVC 的关系、控制器协调、状态与事件、真实部署和故障排查 |
| 职责 4：解决并发、资源、链路和行为一致性问题 | Claim 并发领取、归属转移、幂等、失败清理与缓存滞后造成的重复创建 |
| 职责 2：沉淀稳定可复用的框架组件 | 将环境生命周期封装为资源模型和接口，分开任务语义与底层资源操作 |
| 要求 5：模块化、测试、日志、性能与稳定性治理 | Reconcile 的错误分类、状态回写、重试与补池节奏、相关测试和诊断手段 |

建议优先保持三个连续问题：单个 Sandbox 怎样形成并管理运行环境；WarmPool 怎样维持备用数量；Claim 怎样领取和回收。APF、复杂多集群和底层网络实现仍按具体问题进入，不增加另一套全量 Kubernetes 课程。

源码阅读提供机制理解，不能单独代表 JD 所说的实际集群经验。后续应结合现有实践或一个小型部署/排障案例验证；例如能从资源状态和事件定位 Pod 未就绪的原因。当前讨论没有授权或执行新的集群部署，也没有把尚无运行证据的能力标为掌握。

任务级预取与 session 交接继续以 Dressage 作对照；模型、工具、轨迹和训练接入由既有 Agent/RL 主线承接。跨语言 Go 阅读属于 JD 加分项，但不因语言要求扩成 Go 全课程。
