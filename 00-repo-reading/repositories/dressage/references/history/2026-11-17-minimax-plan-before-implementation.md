> 历史快照：2026-11-17 迁入 implementation 前的完整讨论方案；不再维护当前进度。现行入口见 [实施单元](../../implementation/minimax-harbor/README.md)。

# 从 Slime 出发，通过远端 LLM API 跑通 Agent 评测

2026-11-17：保存本轮框架组合判断，并按用户补充的运行条件修订。本文是目标与接缝记录，不代表已经实现或验证；实际阅读进度仍见[项目入口](../../README.md)。

## 已确认的改造基线

2026-11-17，用户明确以当前本地版本继续。本轮重新检查结果：

- 源码目录：`/home/hongshi/projects/Dressage`。
- 固定提交：`3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 提交标题：`docs(readme): update news for step balance`。
- 当前分支：`main`；工作区干净。
- 当前 `origin`：`git@github.com:dextermayhewjd/Dressage.git`（本地 remote 已指向用户仓库；本轮未联网验证远端状态）。
- `git describe`：`v0.1.0-84-g3e3142f`，不是恰好处于 v0.1.0 标签。
- 本提交声明的 Harbor 依赖：`harbor==0.18.0`；此前阅读的 Harbor v0.25.0 不自动成为已验证运行依赖。

该记录更新下文较早“origin 指向官方仓库、尚未建立用户 fork”的当时状态。后续以此提交做对照基线，不自动升级；本轮仅检查和记录，没有修改框架源码、切换分支或安装依赖。

## 1. 用户确定的前提

用户要求单独保存上一轮判断，同时明确：

> 我只会需要一开始从slime这个框架出发
> 但是我没有实际的gpu
> 但是这个发出信号的部分是发往具体的llm api的国内的厂商
> 这样子我可以用来理解
> 一个模型的具体表现？

据此，本轮目标是：**以 Slime 为发起入口，通过国内厂商的远端 LLM API 执行 Agent 任务，收集过程与评测结果；本地不部署模型，不进行模型权重更新。** 厂商现已确定为 MiniMax；模型、账户对应的 API 地址、接口协议与具体运行入口尚未选定。

这修订了上一轮“先从 Harbor 跑通、随后接回 Slime”的建议：Slime 应从首版就在入口位置；训练更新仍是未来有条件时的扩展，不是本轮验收要求。

### 实现方式补充：局部修改 Dressage，沿用 Harbor 路线

用户进一步明确：

> 我需要在harbor的这条路线上跑通的同时
> 我需要小幅度入侵 只是修改部分的代码？ 这样子的话 最后对比起来会很方便？

据此，目标不是在外面另搭一套执行框架，而是**以当前 Dressage 为基线，在已有 Harbor 路线上做集中、可对照的局部修改**，接入远端模型 API。Slime 仍是首版发起入口；Harbor 的 Job/Trial、Agent、Verifier 和生命周期尽量继续复用。

“小幅度”是控制改动范围的目标，不是已确认的修改行数。当前候选接缝分成三处：

| 接缝 | 拟改变什么 | 保留什么 |
| --- | --- | --- |
| 模型请求 | 在 Dressage 合适的请求边界增加厂商 API 后端与明确的选择配置；落点待核对 | 原有 SGLang 后端，避免直接改坏原路径 |
| 结果整理 | 支持 API 实际提供的回答、工具调用、用量与评测记录；显式处理缺少的训练字段 | Trial 身份、奖励、产物与结果关联；原训练路径的数据约束 |
| 启动 | 核对从 Slime 发起时如何不创建训练模型和本地推理服务 | 从 Slime 发起和接回结果的总体关系 |

不能先假设只替换 `SGLangRouterClient` 就够：当前 `GenerationController` 的结果也包含 token ID、logprob 和版本信息。如果厂商返回消息/工具调用，适配可能需要从更上层的消息边界接入。应先核对最短调用链，再确定改哪几个文件。

为方便对照，建议固定上游提交，把 API 后端、启动适配、K8s 环境适配分成独立改动；保存运行配置与统一的任务/评分标识。这样能分别回答“代码改了哪里”和“同样任务的结果变了什么”。无 GPU 时，可以静态对照原实现，但不能声称已经完成原 SGLang 路线与新 API 路线的运行 A/B 验证。

本轮仅确认实现方向并记录上述建议，尚未修改 Dressage、Harbor 或 Slime 源码。

## 2. 保留的框架组合判断

三个框架的主要职责不同，可以沿现有集成关系组合，不必重写三套执行框架。

| 组件 | 本轮希望复用的职责 | 需要核对或适配的边界 |
| --- | --- | --- |
| Slime | 作为任务发起、rollout/评测与结果交接的起点 | 找到或适配不启动训练模型、本地推理服务的运行入口 |
| Dressage | 已有 Harbor 接入、会话关联、模型请求与轨迹整理 | 将所需请求路径接到厂商 API；评测记录与训练专用数据要求分开 |
| Harbor | Job/Trial、Agent、题目环境、Verifier、执行与清理 | 版本兼容、任务与 Agent 配置、环境实现 |
| Agent Sandbox / Kubernetes | 提供 Agent 执行代码、命令与测试的环境 | Harbor Environment 接入、资源与生命周期；预热后续验证 |
| 国内厂商 LLM API | 远端执行模型推理 | 消息、工具调用、认证、超时、限流与返回格式 |

**模型运行的地方与 Agent 执行工具的地方分开。** 无本地 GPU 不妨碍远端推理；沙箱仍需要 CPU、内存、容器与网络等资源，具体题目还可能有额外要求。

## 3. 目标链路：不是现成可运行声明

```text
Slime 发起一次 rollout / 评测任务
    │  待核对：无本地 GPU 的启动路径
    ▼
Dressage 的 Harbor 集成
    ▼
Harbor Job / Trial
    ├─ Agent 的模型请求
    │      └─ 模型接口适配 → 国内厂商 LLM API
    │                         └─ 返回回答或工具调用
    ├─ Agent 执行工具
    │      └─ Environment → Agent Sandbox / Kubernetes
    └─ Verifier 对任务结果评分
           ▼
整理回答、工具轨迹、产物、奖励与运行指标
           ▼
返回 Slime 发起端，保存本次评测结果

本轮到此结束：不执行训练，不更新或同步模型权重。
```

模型接口适配的具体落点仍需源码核对。保留 Dressage 的职责和已有集成，不意味着原来的整条 SGLang Proxy 路径能原样复用。

## 4. 为什么不能只换一个模型地址

当前静态源码揭示两处需要先检查的接缝：

1. Slime `train.py` 的 `train()` 在 eval-only 分支之前已经调用 `create_training_models()`、`actor_model.update_weights()`。因此，不能仅凭“只评测”就断言现有训练入口不需要模型/GPU；实际无 GPU 入口需要进一步核对和验证。
2. Dressage `SGLangRouterClient.generate()` 使用 `input_ids`、`return_logprob` 等字段，发送到 `/generate`。厂商 API 的协议与返回信息尚未选定，不能把修改 URL 等同于完成适配。

另有已知版本接缝：Dressage 当前声明 `harbor==0.18.0`，已读 Harbor 为 v0.25.0。实现前须明确采用的版本组合并验证。

评测不应强行填造训练字段。若 API 不提供真实 token ID、逐 token logprob 或可核对的权重版本，就明确记录缺失；不能用重新分词或补零声称恢复了原始训练轨迹。也不能据一次 API 调用认定能够更新厂商模型的权重。

## 5. 这样能够理解什么“模型表现”

可以观察**某个模型在固定 Agent、提示、工具、环境与题目条件下的任务表现**：是否完成任务、Verifier 分数、工具使用过程、失败原因，以及调用次数、延迟和 API 实际报告的用量。

这不是脱离框架的模型能力测量。比较模型时应尽量固定题目集、Agent/harness、提示、工具、采样配置、预算与环境，保存模型标识和评测时间，并区分模型答错、工具失败、API 失败和沙箱故障。一次跑通只证明链路可用，不能据此断言模型整体更强。

小例子（目标示意，非运行结果）：同一道修复代码题，模型 API 返回编辑/执行工具调用，Agent 在沙箱中修改文件并运行测试；Verifier 判定是否通过。最终既看到通过与否，也能回查模型提出了什么、工具实际做了什么、失败发生在哪一层。

## 6. 据此前提收敛后续工作

### 用户最新明确的实施顺序

用户进一步归纳：已经走过 Dressage 的 Harbor 路线，希望只对这条路径上需要模型 API 的地方作最小修改，改动成功后再切换 Agent Sandbox。

据此，分两阶段验证：

1. **先接通厂商模型 API。** 从 Slime 发起，沿已有 Dressage–Harbor 路线，集中处理实际经过的模型调用边界、必要的结果字段与无 GPU 启动依赖。环境先沿用一个可运行且不依赖本地 GPU 的后端；具体后端尚待确定，不能因源码已有就认为本机可用。验收为一个任务完成模型调用、工具执行、Verifier 评分和结果返回。
2. **再切换 Agent Sandbox。** 保持第一阶段的模型配置、Agent、题目和评分规则，改环境后端并验证文件、命令、日志产物与清理。冷创建跑通后再接预热池。

这里的“需要 API 的地方”限定为模型请求及其必要的数据适配；不把沙箱、文件传输、Ray 等接口一并替换。若多个上层调用共享一个模型请求出口，优先修改共同出口，不逐个调用点重复改造。准确落点与改动量仍待源码核对。

此顺序更新此前笼统的接入建议；没有重新开始全仓阅读，也没有宣布任一阶段已运行成功。

以下为候选推进顺序，不自动开启新 step 或创建未读函数卡：

1. **先确认 Slime 无 GPU 的发起路径与模型 API 接缝。** 明确哪些启动依赖必须绕开或适配，评测输出需要满足什么合同。
2. **跑通一个任务。** 一个固定模型、一个 Agent、一个题目与 Verifier；通过 API 得到模型输出并形成可追溯的评分结果。
3. **接入 Kubernetes 环境并验证生命周期。** 覆盖创建、执行、文件交接、正常结束与取消清理，再讨论小规模并发和预热。

面向岗位，本轮交付应能展示：接口适配、异步任务执行、模型/工具交接、评测、可追溯结果，以及实际完成后的容器/K8s 运行与排障证据。训练交接的源码理解保留，但不把未做的 GPU 训练写成实践成果。

## 7. 预热核对：Harbor 主流程不预取，不等于后端不能预热

2026-11-17 用户追问“Harbor 这条路没有任何预热”的原因。静态核对本地 Harbor v0.25.0（fdba28fc，工作区干净）后，应修正这个绝对判断：

- `Trial._start_agent_environment`（trial.py:1853）等待 `agent_environment.start(...)`，本层不决定环境是冷创建还是从池中领取。
- `E2BEnvironment.start`（environments/e2b.py:256）检查/创建模板，再调用 `_create_sandbox`，后者调用 `AsyncSandbox.create`。模板复用不等于 Harbor 提前为未来 Trial 创建运行中的实例；单看 SDK 调用也不能推断 E2B 服务内部完全没有优化。
- `ACKEnvironment.start`（environments/ack.py:1355）已有 `use_sandbox_claim` 分支，调用 `_start_with_sandboxclaim` 从 SandboxSet 取得预热实例。此后端使用 `agents.kruise.io`，不是本轮目标 kubernetes-sigs/agent-sandbox 的直接适配实现，也未验证与 Dressage 锁定的 Harbor 0.18.0 兼容。
- Dressage 的 `start_prewarm/claim_prewarm` 实际调用位于原生 prewarm scheduler 和 `rollout/generate/blackbox_dispatch.py`；在 `integrations/harbor` 未找到该调用。这证明当前原生预取链没有直接复用到 Harbor，不证明 Harbor 所有后端没有预热。

**从代码职责作出的解释**：原生 Dressage 提前初始化 Paddock 会话，并把该句柄交给自己的 dispatch；Harbor 则创建自己的 Environment 对象并拥有启动/停止周期。二者没有现成句柄交接，就不能自动共享那份预热资源。没有查到作者关于未复用原因的明确说明，不能把这一架构解释当作作者动机。

本轮适合读到这里停止：看清 `Environment.start` 可以封装冷创建或热领取。无需为了 API 第一阶段迁移 Dressage 原生预热池。进入 Agent Sandbox 阶段时，再设计 start 的 Claim 领取、环境匹配、就绪与 stop 的所有权清理，并核对池耗尽时的行为。

下一项候选工作是沿已读模型链定位可替换边界（消息进入 → SGLang token 请求 → 结果消费者），列出最小修改清单，同时检查 Slime 无 GPU 启动路径；不重读全部 Harbor，不因这个建议创建未读函数卡。

### 模型适配的首次源码定位（2026-11-17）

用户要求沿 `GenerationController.generate_preemptible` 定位。当前固定 Dressage 提交下：

| 位置 | 静态观察 | 对适配的意义 |
| --- | --- | --- |
| server.py:1939，pipeline 入口 | 读取 body 中 messages、model、tools 等 | 这里还保留对话协议层信息 |
| server.py:2087 / 2198 | 从 prompt_payload 取 input_ids，交给 generate_preemptible | 进入控制器前已转换为模型 token 输入 |
| generation_controller.py:159 / 244 | 接收 input_ids、sampling_params，调用 _generate_with_optional_request_id | 不是通用 messages 客户端接口 |
| generation_controller.py:675 | 委派 self._sglang_client.generate | 参数兼容包装，没有恢复 messages/tools |
| sglang_client.py:176 / 208 | 将 input_ids 等提交到 /generate | 实际 SGLang HTTP 出口 |
| generation_controller.py:293 / 315 / 341 | 读取输入 logprob、检查要求的版本、收集 output_ids 等 | 返回值不只是回答文本；版本检查是否强制取决于参数与分支 |
| server.py:2479 | _record_step_atomically 收到 token、logprob、版本等字段 | 只替换发送端仍需处理后续记录合同 |

初步判断：针对以 messages/tools 为输入的厂商 API，应优先评估 pipeline 的对话消息边界，而不是直接将 token 请求换一个 URL。这不是已经确定在 1939 行插入分支的实现方案；初始化、会话、响应和记录的依赖尚需完整核对。当前下一观察点是 pipeline 的“消息 → prompt_payload/input_ids → generate_preemptible”交接；暂停恢复内部不扩为必读。

### 是否已有可直接复用的 API 接口（2026-11-17 静态核对）

结论分三层：已有原始消息入口；已有 SGLang 客户端注入点；在本次检查的 Harbor→Proxy 正常路径中，未发现已完成的通用厂商 messages 后端切换。

- `server.py:1939` 的 pipeline 从 body 取 messages/model/tools；`server.py:2079` 附近调用 `_build_prompt_tokens`，2087 取 input_ids。`_build_prompt_tokens`（1662 附近）可调用 `_full_prompt_token_ids`，后者使用 `mask_builder.tokenize_messages`。这是明确的消息到 token 交接位置，但更早的路由选择也依赖模板，不能仅在 2087 前插入一次 HTTP 请求就认为适配完成。
- `create_app`（server.py:725）允许注入 `sglang_client`，891 行设默认客户端，随后交给 GenerationController。这是已有的依赖注入点，但合同仍是 token 输入和 SGLangResponse，不等于通用聊天 API 后端。
- `GatewayRuntime._create_proxy`（gateway.py:670 附近）传入 `upstream_origin`、`upstream_headers`、`router_api_path` 等。说明转发目标可配置；尚不能据此认定将目标直接指向厂商即可保留 Dressage 会话/轨迹导出与 ArtifactStore 的完整合同。

因此可复用已有消息与转发边界，新增适配实现仍需核对响应和记录路径。下一个优先观察点保持 pipeline 的消息输入及 token 准备，不开始重写控制器，也不承诺只改一行 URL。

### 将阅读转为 fork 上的改造：基线与首批清单

2026-11-17 用户提出：基于 Dressage 的 fork 继续，记录实际需要修改哪些地方。当前本机已有 `/home/hongshi/projects/Dressage`，origin 为 `https://github.com/Accio-Lab/Dressage.git`，HEAD 为 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`，工作区干净；这份 checkout 目前指向上游，不是已建立的用户 fork。本轮未创建远端 fork，也未修改 Git remote。

建议以这份已读版本作为第一轮基线，创建个人 fork 后保留 upstream 并在独立分支开发。fork 的默认分支可能比本地已读提交更新，因此实现分支应明确从上述提交出发；是否升级另作决定。

首批工作清单（候选位置，不代表每个文件都必须改）：

| 工作项 | 已定位的代码 | 首轮判断标准 |
| --- | --- | --- |
| 消息型模型后端 | `dressage/proxy/server.py`，必要时新增独立客户端模块 | messages/tools 能交给厂商，回答及工具调用能交回 Agent；保留原 SGLang 路径 |
| 响应与记录合同 | pipeline 的解析/记录段、`dressage/integrations/harbor/artifacts.py` | 不伪造 token/logprob，已有 finalize/read/commit 生命周期能够完成 |
| 无 GPU 发起入口 | Slime `train.py`、Dressage 的 Harbor rollout 入口与启动配置 | 从 Slime 发起任务，不加载本地训练或推理模型；不能预设只改 Dressage 就能达成 |
| 最小验证 | 已有测试与新增针对接缝的测试、一个运行配置 | 先模拟响应核对合同，再用真实 API 跑一个任务并保存评分与轨迹 |
| 第二阶段环境替换 | Harbor Environment 适配、Agent Sandbox 配置 | 第一阶段通过后再改环境；冷创建与清理先通过，再验证预热 |

改动日志按“原行为 → 为什么改 → 修改位置 → 验证结果”记录。学习用函数卡继续保存到本学习仓库；实施日志和可执行测试应随未来 fork 的代码维护，当前不先生成重复材料。厂商与模型尚未选定，具体消息、工具、流式和认证兼容性待核对。

### 厂商确定为 MiniMax

2026-11-17 用户明确“使用的是minimax的api”。本轮已核对 MiniMax 官方国际站的 [OpenAI 兼容接口](https://platform.minimax.io/docs/api-reference/text-openai-api)与 [Anthropic 兼容接口](https://platform.minimax.io/docs/api-reference/text-anthropic-api)：均提供消息与工具调用相关能力，但有参数兼容限制；多轮工具交互应保留官方要求的完整助手响应。国内文档对应页面本轮抓取超时，不能据国际站示例替用户确定国内账户地址或可用模型。

就现有 Dressage 链路，优先评估在已有 OpenAI 消息边界接 MiniMax 的兼容接口，减少额外协议变化；Anthropic 兼容能力作为另一种候选。不能因 CLI 可以直连 MiniMax 就认为满足本轮保留 Dressage/Harbor 路线与结果收集的目标。具体模型名与账户提供的 Base URL 待用户给出，无需在聊天提供 API Key。本轮只查官方文档，未发起模型调用。

### 执行方案澄清：无需先下载任意模型（2026-11-17）

用户询问是否应先下载一个本地模型再逐步替换。助手建议不下载任意模型：本轮推理由 MiniMax 提供。本地权重、tokenizer/模板与远端 API 是不同依赖；`server.py:881–883` 确有 tokenizer 加载，TITO 另有模型/模板约束，但这不能通过任意 tokenizer 代替目标模型来正确解决。拟新增的消息 API 路径应隔离这些 SGLang/token 依赖，不把随意分词生成的数据冒充 MiniMax 实际 token。

建议按可独立验证的小步执行，而不是先复刻完整 GPU 训练环境：

1. 固定 Dressage 源码与 Harbor 依赖基线，在用户 fork 的独立分支维护改动。先梳理启动/导入依赖，保留原 SGLang 路径；现有 GPU 原路径不标为已运行。
2. 最小 MiniMax 客户端：确认账户 Base URL、模型和认证配置；先验证一次文本请求，再验证一次工具调用及工具结果回传。调用需要用户可用凭证；本轮未执行。
3. 明确并实现从 Slime 发起的无 GPU 执行路径。确认不创建训练模型、不启动 SGLang、不执行权重同步；先用明确标为模拟的响应测调度/返回合同，随后接 MiniMax 客户端。此入口是否需要独立脚本或配置分支仍待核对，不把独立测试脚本冒称完整 Slime 路径。
4. 沿 Dressage–Harbor 正常链路跑一个 CPU 任务：保留 Gateway、Trial 身份、工具执行、Verifier 和清理；适配模型响应及非训练结果记录。验收从 Slime 发起，到结果返回、日志产物保存与环境清理。环境先选本机实际可用的一种后端，尚未承诺现成可运行。
5. 保持模型、任务和评分配置，换成 Agent Sandbox 环境。先冷创建与清理，后小池预热和并发验证。

每一步只提交已验证的变化，记录“修改目的、文件、验证证据、剩余限制”。模拟响应只验证工程合同，MiniMax 实际请求才能提供模型表现证据；不需要为了第一步而下载无关模型，也不把 CPU-only 顶层入口等同于关闭一个训练开关。

## 8. 依据与尚未验证的内容

- Dressage `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`：`docs/harbor.md`、`pyproject.toml`、`dressage/proxy/sglang_client.py`、`examples/harbor/run_harbor_training_qwen3.5_4b.sh`。已有 Harbor 集成及 Slime 训练入口；SGLang 请求协议是静态源码事实。
- 同版本 `dressage/proxy/generation_controller.py`：`GenerationChunk` / `PreemptibleGenerateResult` 含 token、logprob 与版本字段，说明 API 适配边界不能只按 HTTP 地址推断。
- Slime `18868a79b0b083a093798a94ed0f8cb4f71b9c14`：`train.py` 的启动、模型初始化与评测分支。
- [沙箱接口地图](../harbor-sandbox-interface-map.md)和[沙箱供给与预热](../sandbox-supply-prewarm-and-kubernetes.md)：环境接入与预热问题继续复用，不重启整套阅读。
- 厂商 API 能力、可用模型、实际无 GPU 入口、依赖安装、Harbor 版本组合、Agent Sandbox 适配均未完成运行验证。本轮未发起付费 API 请求、部署或训练。
- 本次讨论与前一次判断的修订关系见 [Step 013 过程记录](../../topics/02-harbor-integration/steps/step-013-harbor-kubernetes-environment/04-flow.md#slime-api-evaluation-20261117)。
