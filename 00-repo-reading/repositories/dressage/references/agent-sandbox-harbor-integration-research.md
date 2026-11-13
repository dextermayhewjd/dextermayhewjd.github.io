# Dressage、Agent Sandbox 与 Harbor：适配边界与阅读路线

[学习指南](design-on-slime.md) · [Dressage 当前进度](../README.md) · [已有 Provider 接口资料](sandbox-provider-guide.md)

**日常阅读按已确认的[接入阅读规划](integration-reading-plan.md)推进。** 本文保留研究依据、路线比较与兼容性缺口；后续确认的“先给旧 generate 收尾”及整体顺序以规划为准，不从本页的候选入口重新推导另一套路线。

研究日期：2026-11-07。用户要求 deep research：希望复用 Dressage 的能力，启动 Kubernetes 沙箱，支持不同任务和 Agent，并接入 Agent Sandbox 与 Harbor；不希望为了局部优化而脱离原框架、重复实现调度和执行体系。

2026-11-08 补充核对：[Harbor 锁定版本已有 GKE、ACK、OpenShift 后端](harbor-kubernetes-backends.md)。下文“需要 K8s 环境适配”指目标 kubernetes-sigs/agent-sandbox 的特定接口与版本接缝，不能理解为 Harbor 没有 K8s 能力。实施前应先评估现有后端，不能预设必须从零写环境实现。

同日进一步的[当前版本兼容性核对](agent-sandbox-harbor-compatibility.md)验证了示例适配目录缺失，以及 Dressage 版本保护对 Harbor 0.25.0 的拒绝；当前组合尚不能按示例直接运行。

同日又按现有项目的真实 CLI 做了[AgentLab 对照](agentlab-current-vs-harbor-dressage.md)：当前入口已自行编排预热、K8s、Harness 和 Verifier，不能描述成只有一个 API 替换点。默认白盒 API 路线与可选 Slime API 生成替换工厂也应分别判断，默认 CLI 未注入轨迹 Adapter。

本文是源码核对后的设计与阅读建议，不是已实施方案。没有启动集群、调用付费模型或修改三个项目的源码；也没有创建新的正式 step 或函数卡。

## 1. 结论：保留 Dressage 的真实 Harbor 路线，以环境接口连接 Kubernetes

**若“使用 Harbor 的任务、现成 Agent 与评测器”是目标的一部分，建议以 Harbor Job/Trial 为该路径唯一的任务编排者，复用 Dressage 已有 Harbor 插件，在 Harbor 的 Environment 边界接入 Agent Sandbox。**

这不是脱离 Dressage：它自带的 `run_harbor_rollout_qwen3.5_4b.sh` 最后就是 `harbor run --plugin dressage`。原生 `AsyncRolloutWorker → blackbox_dispatch.generate → Paddock → BlackboxServer` 是同仓库内另一条路线，不是 Harbor 集成必须再经过的一层。

可以复用两条路线的设计知识，但不能直接叠加它们的任务所有权。一次 Harbor Trial 不应该同时由本地 RolloutRunner 再创建环境、启动另一个 Agent、评分和重试。

```text
项目的实验配置与任务来源
  -> Harbor Job.create / Job.run
       -> DressageHarborPlugin 挂接生命周期与模型路由
       -> Harbor TrialQueue：并发、尝试与重试
            -> Trial.run
                 -> Environment.start
                      -> K8s 环境适配（需要补齐）
                           -> Agent Sandbox / Claim -> Sandbox -> Pod
                 -> 已有 Harbor Agent.setup / install
                 -> Agent.run
                      -> Dressage Gateway -> 模型与采集后端（API 兼容性待验证）
                 -> Verifier.verify
                 -> 环境停止、写 TrialResult、发出 END
                      -> Dressage 插件收尾、关联轨迹与评分
```

图中“需要补齐”和“待验证”是实际缺口，不能据图把它们当作已有实现。对 API-only 项目，默认 Dressage Proxy 的兼容性尤其不能省略。

### 为什么选择这条路线

| 组合方式 | 能直接保留什么 | 为当前目标付出的额外代价 |
| --- | --- | --- |
| Dressage 原生 rollout + 新 K8s Provider | 原生 Paddock、BlackboxServer、预热 store | 仍须启用/验证 K8s 预热；若再接完整 Harbor Trial，需要转换环境所有权、执行与评分协议 |
| Harbor + Dressage 已有插件 + K8s Environment | 已有 Harbor 任务/Agent/Verifier/重试，以及 Dressage 的路由和产物挂接 | 补 K8s 环境合同、版本与 API 模型合同；原生 session 预热改由 K8s 备用池承担。**本研究推荐** |
| 现有 agentlab runner + K8s + 导入 Harbor 任务 | 当前运行器与预热实现 | 只能复用部分 Harbor 资料，仍维护本地 Agent/评测调度；不等于复用 Harbor 的完整生命周期 |

如果“接入 Harbor”仅表示读取其题目文件，第一或第三条也可成立；本研究按用户同时复用任务执行和评测能力的目标推荐第二条。这个条件需要在实施 scope 中明确。

<a id="generate-vs-trial"></a>

### generate、Harbor Trial 与 Sample 怎样结合

用户追问 generate 是否主要给 Slime 生成 Sample，以及这些抽象怎样连在一起。需要区分两个真实入口：

| 入口 | 被怎样调用 | 承担的工作 |
| --- | --- | --- |
| `blackbox_dispatch.generate` | Slime 的 `--custom-generate-function-path`，接收单个 sample 等参数 | 经 Paddock/BlackboxServer 执行一次任务，读取轨迹并构造 Sample；不只是最后做格式转换 |
| `generate_rollout_harbor_sync` | Slime 的 `--rollout-function-path`，接收 rollout_id/data_buffer 等参数 | 组织一批 Harbor Trial，取得结果与轨迹，转换为 Sample 组，返回 `RolloutFnTrainOutput` |

当前 Harbor 路线不需要调用第一个入口。若目标先是 API 模型评估与 K8s 平台，可以由项目调用 Harbor Job，获得 TrialResult 和采集产物；不需要先引入第二个 Slime 批量入口。要把结果正式交给 Slime 训练时，再展开它及其数据合同。

用户进一步追问“Slime 一开始不是就留下一个 generate 吗”。这里缺失的是两个扩展粒度：Slime 的 `--custom-generate-function-path` 只替换原 rollout 内的一条任务生成；`--rollout-function-path` 替换整批 rollout 的组织与交付。二者都属于 Slime 已有扩展点。若要原样复用 Dressage 的 Harbor 实现，配置后者和 HarborDataSource，不是在前者里面再塞一个不兼容签名的批量函数。自写单条 generate 包装 Harbor Trial 理论上可行，但会新增环境/回调/采集/失败交接代码，不能称为直接复用已有完整路线。

阅读时先在上层保留：`Slime → generate_rollout_harbor_sync → _run_harbor_rollout → _run_partition → Harbor Job/Trial`，完成后经 `_bundle_samples` 和 `RolloutFnTrainOutput` 返回 Slime。这只为第 1 单元补足调用方定位，不另新增一个必须通读的训练专题。当前 API 采集项目是否运行这一训练入口，仍受后文的模型与轨迹合同约束。

真实训练桥接见 [启动参数](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_training_qwen3.5_4b.sh#L66)。`generate_rollout_harbor_sync` 的内部 `_run_partition` 先运行以下代码，再读取插件结果并调用 `_bundle_samples`；不能把 generate 画成任务结束后才调用的纯转换器：

```python
# _run_partition 的实际调用顺序，plugin 和 job 此前已创建。
await plugin.on_job_start(job)
result = await job.run()
await plugin.on_job_end(result)
```

抽象按职责连接：Harbor Task 描述题目/环境要求/验证规则；Agent 描述执行策略或 CLI；Trial 是某 Agent 做某题的一次尝试；Environment 为这次尝试提供运行能力并映射到 Agent Sandbox；Dressage 插件把模型请求和轨迹关联到尝试；Sample 是交给 Slime 的数据载体，一次 Trial 因分段可以产生多个 Sample。Task、Trial、环境资源和 Sample 不能互当别名。

本轮读法：旧 `blackbox_dispatch.generate` 保留职责和背景，不再继续逐层精读以接入 Harbor。先走通 Trial 与环境/Agent/Verifier；需要 Slime 消费时才看 [Harbor 批量入口](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L1257) 和 [_bundle_samples](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L624)。

### 旧 blackbox generate 怎样收尾，避免阅读断裂

用户继续要求同时看清 Slime、Dressage、Harbor 与 K8s 环境的关系，并询问旧 generate 是否还需结尾。这里把 Harbor/harbour 按同一 Agent 评测框架理解，环境沿用此前指定的 Agent Sandbox。

建议给旧 generate 做一次**主线收束**，与继续深挖全部黑盒实现区分：只补清 call_agent 的结果、after_agent、finalize/read_trajectory、segments 转 Sample、finally 安排回收五个交接。异常分支至少知道取消继续抛出、普通故障可被标为 ABORTED；不把后台清理的安排等同于资源已经删除。当前没有因此将 Step 005 或旧 generate 全部标记为已完成。

| 原生 generate 中的职责 | Harbor 整合路线中对应的承担者 |
| --- | --- |
| Paddock.init 取得环境 | Harbor Environment.start，通过 K8s 适配使用 Agent Sandbox |
| register_agent / call_agent | Harbor 所选 Agent 的 setup/install/run |
| 会话收尾与轨迹读取 | Dressage Harbor 插件与 Proxy/采集接口 |
| segments 转 Sample | 需要交给 Slime 时，由 Dressage Harbor rollout 桥接及 _bundle_samples 完成 |
| 结束与清理 | Harbor Trial/Environment 管环境，Dressage 插件管模型路由及采集资源 |

整体不是只读 Harbor：Slime↔Dressage 的输入输出短读，Dressage↔Harbor 的生命周期和采集重点读，Harbor↔Agent Sandbox 的环境合同重点读。原生 generate 收束后，先在 generate_rollout_harbor_sync 定位外层调用方，再进入 Harbor Trial.run；这是第 1 阅读单元里的连续导航，不另建两套路线。API-only 项目的模型合同仍按 3.3 节处理，不能仅凭图示认定已经兼容 Slime 训练。

## 2. 版本与证据范围

| 来源 | 本次核对版本 | 核对方式 |
| --- | --- | --- |
| Dressage | `3e3142fe8ea07e4504c3b20a936a4c201a3de44c` | 本地源码，工作区干净 |
| Agent Sandbox | `37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1` | 本地源码，工作区干净 |
| slime_api_data_collecting | `151db30d1f4533773948695f4033ebe4353521d8` | 本地 `src/agentlab` 源码，工作区干净；不以残留 `src/apilab` 文档代替现状 |
| Harbor | `0.18.0`，Git tag 指向 `527d50deb63a5d279e8c20593c18a2cbc7f61f9e` | 下载官方 PyPI wheel、核验 SHA256、只解包读取；GitHub tag API 核对提交 |
| 官方在线文档 | 研究当日页面 | 用于确认公开入口及已发布示例；不将当前文档新增接口混入 0.18.0 合同 |

Harbor wheel SHA256：`e436f04fca35bb3705be603b8c123d0472418d10120cfd7e5ba8dc902e56bc32`。临时源码位于 `/tmp/dressage-adaptation-research/harbor-0.18.0/harbor/`，下文使用固定提交的永久链接。没有安装 Harbor 或执行包内代码。

[机器可核对的证据清单](agent-sandbox-harbor-integration-evidence.json)记录 27 个关键文件的哈希、Harbor 的 9 个抽象方法及未取得集成包的查询结果；这是来源核验，不是行为测试通过记录。

### 一个阻止直接拼接示例的版本问题

1. Dressage 的 [pyproject.toml](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/pyproject.toml#L21)锁定 `harbor==0.18.0`；[compat.py](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L37)做版本检查，并依赖任务解析及待运行 Trial 的具体组织。
2. Agent Sandbox 的 [Harbor 示例](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/harbor-terminal-bench/README.md#L84)要求 `harbor>=0.25`，引用 `clients/integrations/harbor`。
3. 该目录不在当前 Agent Sandbox 工作树或 HEAD 文件树中。研究当日查询官方 GitHub 的同一路径及 PyPI `k8s-agent-sandbox-harbor` 均返回 404；公开文档存在，不等于本次已获得可复用的包。

**本次建议先按 Harbor 0.18.0 设计接口，保留 Dressage 的既有兼容范围。** 不能把示例中的类名当作已经可导入的依赖。若之后取得面向新 Harbor 的环境实现，应单独验证/升级 Dressage compat 与生命周期合同；不要仅放宽版本号就宣布兼容。

## 3. 三个关键判断

### 3.1 Harbor 已解决“选哪个 Agent、在哪里安装”的一部分问题

固定版本源码的真实链路是：

1. [Job._init_trial_configs](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/job.py#L363)按 `attempt × task × agent` 生成 TrialConfig。不同 Agent/模型组合由配置表达，不要求每道题另写 generate。
2. [Trial.run / _prepare](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L345)先准备环境，再调用所选 Agent 的 setup。
3. [BaseInstalledAgent.setup](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/agents/installed/base.py#L497)调用 `self.install(environment)`。
4. [ClaudeCode.install](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/agents/installed/claude_code.py#L166)与 [Codex.install](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/agents/installed/codex.py#L107)检查已有程序和版本，满足条件则复用，否则执行各自安装。

所以“任务基础镜像 + 按所选 Agent 准备程序”有现成实现可读，不必把所有 CLI 预装进每份任务镜像。是否允许在线安装、依赖是否兼容、镜像中是否提供包管理器等仍由部署条件决定。可以预制含单个 Agent 的衍生镜像来减少 setup 成本，但这属于部署优化，不是重写 Agent 循环。

这与先前读到的 Dressage 原生 `ClaudeCodeAdapter.initialize` 不矛盾：后者只配置并检查现有程序，Harbor 则在自己的 Agent.setup/install 中处理安装；二者属于不同执行路线。

### 3.2 两种预热不是同一个合同

| 机制 | 提前准备的对象 | 消费方式 | 本次如何使用 |
| --- | --- | --- | --- |
| Dressage 原生 PrewarmScheduler / Store | 为具体 sample/session 发起 Paddock.init，保存 Task 与 state | blackbox_dispatch 根据 session_id 领取，未完成会等待 | 读一遍上游/领取关系作为对照；不直接插入 Harbor Trial |
| Agent Sandbox WarmPool / Claim | 某种模板下的备用 Sandbox | Environment.start 创建 Claim，取得对应资源 | 建议作为 Harbor 路线首个预热实现 |
| 现有 agentlab PrewarmStore | 沙箱 + recipe.setup + harness.prepare_fn 的结果 | ready 队列派发或按 task_id 领取 | 已存在；迁移前明确哪些行为需要保留，不再叠加第三套调度 |

Dressage 的 [prewarm_enabled](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/prewarm/config.py#L11)目前仅对 E2B 开启；预热创建的是 Paddock 状态，不是 Harbor Environment。其原生 worker 的结果合同也依赖 Slime sample group。把它搬来驱动 Harbor 还需要处理环境交接和两套生命周期，不能称作“只接一个 Provider”。

WarmPool 若要隐藏首次启动耗时，必须在 Trial 领取前创建并达到期望备用数。若直到 Environment.start 才首次创建池，第一批仍可能等待冷启动。初版先验证冷路径，再给少量明确模板提前设置备用数；不要为全部题目镜像无限驻留资源。

池中环境 Ready 不等于题目初始化和 Agent.setup 完成。后两者先保留在 Harbor Trial 中。领取过的环境也不能未经重置就视为可供下一题使用的干净环境。

### 3.3 API 模型是另一处真实适配，不会被 Harbor 自动解决

Dressage 的默认链路为 `Harbor Agent → Gateway → Dressage Proxy → SGLang`：

1. 插件 [_inject_agent_routing](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1031)设置 Agent 的模型访问地址和按尝试关联的令牌。
2. [GatewayRuntime._create_proxy](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L666)使用 RolloutLLMProxy；它与黑盒服务代码有复用，但这条路线没有再启动一个 BlackboxServer 管 Harbor Agent。
3. [ProxyClient](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/proxy_client.py#L42)除了模型请求，还需要 `/session/finalize`、`/trajectory/read` 等接口。
4. [SGLangRouterClient.generate](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/sglang_client.py#L176)接收 token IDs，调用 SGLang `/generate`，不是普通商业模型的 messages API。

现有 agentlab 的 `make_call_api_generate` 是 Slime 模块函数替换点，并非上述 HTTP/轨迹合同的直接实现。它当前有重编码 token 和零占位 logprob 的路径，不能被标记成模型真实 on-policy 证据。

因此 **API-only 条件下，原样复用 Dressage 整条采集链仍需一项独立兼容性验证**。关闭 `require_trainable_tokens` 不会让插件停止调用会话收尾和轨迹读取。可以先用 Harbor 原生结果与 ATIF 验证任务/沙箱路径，但这只是阶段性验证，不代表完成 Dressage 采集接入。后续在协议接缝实现商业 API 适配时，必须明确返回真实信息、缺失信息和不支持的训练能力。

## 4. 应该读哪些：六个有停止位置的阅读单元

这是接入问题的阅读顺序，不是六个已创建的 step。每单元只沿一条正常路径下钻，再补本单元一个必要失败分支。各层的完整函数清单和所有配置不成为前置。

| 顺序 | 主读入口与最小回查 | 要形成的结果／停止位置 |
| --- | --- | --- |
| 1. 真实总流程与 Dressage 的位置 | Dressage 启动脚本最后的 `harbor run --plugin dressage`；Harbor `attach_job_plugin`；**Trial.run**；Dressage `on_job_start` 只看路由和回调挂接 | 画出创建、Agent、Verifier、END 的执行顺序，标出 Dressage 回调。能说明原生 blackbox_dispatch 不在此链中就停 |
| 2. 环境创建与操作接缝 | **Trial._prepare → _setup_agent_environment**；EnvironmentFactory.create_environment_from_config；BaseEnvironment 的 start/stop/exec/文件接口；现有 UpstreamK8sSandbox | 写出字段和行为映射，完成一个环境创建/执行/销毁的适配草案；暂不写另一套控制器 |
| 3. 不同任务与 Agent | **Job._init_trial_configs**、TaskConfig；BaseInstalledAgent.setup；选 ClaudeCode.install/run 一条，再比 Codex 差异；**Verifier.verify** | 把一题变成 instruction、environment、tests/verifier；知道更换 Agent 只改哪个配置。非 shell 任务额外工具协议按需适配 |
| 4. K8s 预热与领取 | 当前 Agent Sandbox 的 updateStatus 收束后，进入 **WarmPool.Reconcile → reconcilePool**、Claim 的 getOrCreateSandbox/归属交接 | 能让两个并发 Trial 领取不同环境，解释备用数、热命中、冷创建和清理；不研究所有规模优化 |
| 5. 模型与轨迹接缝 | **DressageHarborPlugin._inject_agent_routing**、Gateway 的路由建立；ProxyClient 与默认 SGLangRouterClient；对照现有 API 后端 | 明确 API-only 缺少哪些协议/数据。先通过一次请求与一次收尾的合同验证，不承诺“换 URL 即完成” |
| 6. 结果、取消与重试 | **Trial._finalize**、TrialQueue._execute_trial_with_retries；Dressage `_on_cancel → _on_end → _finalize_attempt → HarborArtifactStore.commit_attempt` | 关联 Trial/attempt/session；区别失败与零分；验证一次取消不泄漏环境、不重复提交结果。走通后停止继续通读 |

**第一处真正展开的编排函数建议是 Harbor `Trial.run`。** 先用 Dressage 启动脚本与插件注册证明它属于当前整合路线，再读这个短主干。`on_job_start` 解释“Dressage 怎样接进来”，`Trial.run` 解释“任务怎样实际走完”；两者相邻阅读，避免只看插件而丢失主流程。

### 可直接打开的固定版本入口

- Dressage [运行入口脚本](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/examples/harbor/run_harbor_rollout_qwen3.5_4b.sh#L109)、[on_job_start](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L261)。
- Harbor [attach_job_plugin](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/cli/job_plugins.py#L24)、[Trial.run / _prepare / _finalize](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/trial.py#L345)、[SingleStepTrial._run](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/single_step.py#L38)。
- Harbor [EnvironmentFactory](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/factory.py#L297)、[BaseEnvironment](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/environments/base.py#L892)、[任务环境配置](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/models/task/config.py#L416)。
- Harbor [Verifier.verify](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/verifier/verifier.py#L138)、[TrialQueue 重试与并发](https://github.com/harbor-framework/harbor/blob/527d50deb63a5d279e8c20593c18a2cbc7f61f9e/src/harbor/trial/queue.py#L194)。
- Agent Sandbox [WarmPool](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxwarmpool_controller.go#L435)、[Claim](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/extensions/controllers/sandboxclaim_controller.go#L2230)。已读 Pod/Ready/status 记录继续复用，不从零重读。
- 当前项目 [UpstreamK8sSandbox](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/sandboxes/k8s/adapter.py:100)、[直接创建实现](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/sandboxes/k8s/direct.py:167)、[API 后端](/home/fredkeira/projects/slime_api_data_collecting/src/agentlab/models/api_backend.py:201)。

## 5. 需要修改什么，哪些先不动

### 环境接缝：新增或取得 Harbor Environment 适配

优先包住已有 K8s 操作，不重写 Sandbox controller。按锁定的 Harbor 0.18.0 对齐：

| Harbor 侧 | 现有能力／需要补齐 |
| --- | --- |
| `start(force_build)` | 取得指定任务镜像或 Claim；首版限定预构建 Linux 单容器镜像，明确不支持构建请求时的行为 |
| `stop(delete)` | 对应当前环境的取消和删除；`delete=False` 不能照常无条件删资源 |
| `exec(command,cwd,env,timeout_sec,user)` | 映射退出码/输出；调用 `_merge_env`、`_resolve_user` 的语义；区分网络等待和进程超时 |
| 单文件与目录 upload/download | 当前只读写文件不够；Harbor 的 Agent 安装、测试上传和日志下载会使用目录接口 |
| image、resources、workdir、network | 从 task/Trial 配置生成资源需求，尊重显式覆盖并拒绝不支持能力；不能仅按题目名称猜测环境 |

现有 SDK 分支 `adapter.py:208` 只调用 `commands.run(cmd)`，会丢弃上层传入的 env/timeout，也未兑现 user 语义。此处需要先修正或显式拒绝不支持的调用。Direct 分支与 SDK 分支分别验证；不能由 mock Provider 测试通过推断真实 SDK 合同通过。

### 任务接缝：转换题目，不重复实现 Harbor 的 Agent 循环

- 题目描述进入 `instruction.md`。
- 预构建镜像、工作目录和资源进入 task.toml 的环境配置。
- 测试、判分脚本和奖励文件按 Harbor Verifier 合同组织；保留原任务的判定含义。
- 默认只选一个任务格式和一个 Agent 打通；再用同一题更换 Codex 验证复用。
- 现有 TaskRecipe 中特殊工具服务、模拟用户或初始化行为不能仅靠文件改名迁移；按是否已有 Harbor 对应任务/Agent 决定最小适配。

### 编排与采集接缝：只保留一个 Trial 所有者

- Harbor 路线用 Harbor Job/Trial 管该次执行；现有 RolloutRunner 保留为旧路径对照，不包在 Harbor Trial 外再跑一次。
- 复用 Dressage Harbor 插件的前提是满足其 Gateway/Proxy/产物合同。API 模型适配与 K8s 环境适配分开验收。
- 现有报告、API 调用账本和上下文证据保留，通过 Trial/attempt/session 对应，而不是只复制一个最终 reward。
- 原生 Dressage worker、Paddock 和黑盒适配器暂作已有背景；只有决定采用原生路线时才实现 Dressage SandboxProvider。Harbor 路线的环境接缝是 BaseEnvironment，不必先再实现一套同名 Provider。

## 6. 从阅读到适配的验收顺序

这不是本次已执行的测试列表，而是后续实施时的停止标准：

1. **一题 + Oracle + 冷创建**：先验证任务文件、环境、Verifier 和删除，不消耗模型调用来排查基础设施。
2. **一题 + Claude + API 采集**：确认所选 Agent 的安装/配置、真实模型请求、结果与失败记录。API 采集合同未通过就不宣称整合完成。
3. **同一题 + Codex**：证明换 Agent 不重写任务和平台；必要协议差异留在已有 Agent/模型适配层。
4. **同模板少量并发 + 预热**：先准备池，观察独立 Claim、备用补充、真实等待时间；不能凭配置有 pool 名就判为热命中。
5. **创建中取消、执行超时和一次重试**：确认各 attempt 归属、取消后不留下不可追踪资源、失败不伪装成正常零分、结果提交不重复。

全部通过后，已达到当前“起沙箱、换任务/Agent、接入 Harbor 与复用 Dressage 适用组件”的第一阶段目标。多集群、所有 Agent、完整训练与复杂动态预测不是这次适配的前置。

## 7. 对此前建议的修正与未知

1. 只建议下一步看原生 worker，缺少了“完整使用 Harbor 时谁拥有 Trial”的判断；本研究把它降为对照材料。
2. 只建议看插件 on_job_start，又容易缺少实际执行主干；现在将它与 Harbor Trial.run 放在同一个总流程单元。
3. 之前关于缺少 Harbor→Agent Sandbox 成品接入的说法，本次补充为可复查事实：有公开示例，但当前固定 checkout 缺实现，且示例版本与 Dressage 不同；不是认定整个生态永久没有相关实现。
4. 没有跑真实任务、付费 API、Kubernetes 或多卡训练；未证明性能收益、强隔离或全部任务兼容。
5. 尚未决定商业 API 侧最终采用哪个具体注入位置，也未证明现有采集结果能直接进入 Dressage 产物合同。需要读完第 5 单元并做小验证后决定，不能预先承诺只改一个函数。

## 8. 在线资料入口

- [Harbor 0.18.0 官方发行](https://github.com/harbor-framework/harbor/releases/tag/v0.18.0)、[PyPI 版本元信息](https://pypi.org/pypi/harbor/0.18.0/json)。
- [Harbor 概念](https://docs.harborframework.com/core-concepts/index)、[自定义环境](https://docs.harborframework.com/sandboxes/custom-sandboxes)、[插件](https://docs.harborframework.com/plugins/custom-plugins)。这些是当前在线版本，实际方法以锁定源码为准。
- [Agent Sandbox 的 Harbor 示例页面](https://agent-sandbox.sigs.k8s.io/docs/use-cases/examples/harbor-terminal-bench/)。本报告没有把示例的运行数字当成本次实测结果。
- [Dressage Harbor 集成](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/docs/harbor.md)。
