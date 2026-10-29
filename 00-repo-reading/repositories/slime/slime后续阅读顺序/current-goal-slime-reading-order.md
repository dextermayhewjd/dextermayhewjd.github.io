# Slime 后续阅读计划与约定

<a id="reading-agreement-20261028"></a>

## 2026-10-29：结合已有基础后的剩余范围

用户已要求综合 Agent、异步、强化学习与 Slime 记录确定剩余范围。**当前剩余 Slime 工作收为两段核心阅读加一项验证**：A 完成已开启 Step 017 的训练闭环；B 复用已读 worker，补中断回队及背压的业务语义；C 复用已有接入和评测链做一个小改动与复跑验证。详细源码、证据和停止条件以 [综合审查](2026-10-29-existing-foundation-and-remaining-scope.md)为准。

Learn Claude Code、原生异步课程和 CS285 已有基础不重复建设；Kubernetes 已有 kubectl 与简单部署经验，补排障案例而非从零重学。Trace 继续暂缓。下方四阶段保留为原路线，A/B/C 是在当前进度上的剩余工作，不表示重读全部阶段。

## 2026-10-28：现行计划

用户要求：

> 那么重新敲定一下这里的下面的计划以及约定的阅读方向吧

本节统一此前讨论后的阅读方向、顺序与边界。依据是[用户提供的完整岗位说明](../../../../slime_photo/code-reading/job-evidence/2026-10-28-user-provided-jd.md)和已发生的阅读；下方旧候选与修正完整保留为历史。**计划不另维护实时进度**，实际开始、暂缓、理解反馈与运行状态只看[唯一路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。

目标是能接入和维护 Agent 组件，验证运行与评估行为，并理解生成数据与训练的交接。选择代码时依据“岗位的具体工作 → 当前缺口 → 最小可验证问题”；用户贴出的新文件、PR 或函数先判断其关联和优先级，再决定是否进入主线。

2026-10-29 深度约束：用户再次要求严格按 JD，不增加隐含要求。当前以 Agent 框架工程为主轴，RL 作为满足“至少一类训练流程”要求的路线；Step 017 只连接数据、任务完成与权重更新。具体必需能力及停止条件见 [岗位边界](../../../../slime_photo/code-reading/job-alignment.md#jd-required-depth-20261029)。本次不改变已有阅读顺序，也不把 Trace 暂缓、Kubernetes 或未执行的接入验证从能力缺口中删除。

### 1. 复用已有阅读基础

| 已读范围 | 后续怎样使用 |
| --- | --- |
| 主题 01：Coding Agent 的 generate、模型请求、沙箱、评估、轨迹导出 | 作为一个真实 Agent 实现和组件分工的参考；遇到明确缺口才回查对应段落。 |
| Step 010–011：generate_and_rm、奖励分派、generate_and_rm_group | 复用生成接口、评分责任和组级组织的认识。 |
| Step 012–013：worker loop、完成回调、group handoff 与过滤收集 | 复用正常任务调度和结果交付；保留此前未展开的异常、取消和清理边界。 |

已有阅读不等于所有分支已理解，也不等于完成了独立实现或真实运行。Step 014 的 Trace 仍按用户要求暂缓，已有卡片、例子、证据与未知保留。

### 2. 接下来按这个顺序推进

下表是阅读阶段顺序；已具体划分为 Step 015 的生成接口接入与 Step 016 的训练数据转换，其余阶段在实际进入时按问题切分，不预创建目录。

| 顺序 | 具体问题与源码入口 | 本阶段的停止标准 |
| --- | --- | --- |
| **① Step 015：自定义 generate 的接口约定与接入验证** | 复用 [generate_and_rm](/home/hongshi/projects/slime/slime/rollout/sglang_rollout.py:289) 的调用位置，对照 [Coding Agent generate](/home/hongshi/projects/slime/examples/coding_agent_rl/generate.py:225)，选读 [生成接口契约测试](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:148)。问题是：自己接入一个实现时，接收什么、返回什么、承担什么职责，怎样检查接入正确？ | 能说明输入、返回数据、状态和评分责任的边界；用一个最小接入或改动验证正常返回及一个约定错误/失败情形，并说明验证未覆盖什么。已有调用主线仅作回顾。 |
| **② [Step 016：Sample 怎样成为训练数据](../topics/02-rollout-reward/steps/step-016-sample-to-train-data/README.md)** | 以 [BatchBuilder.convert](/home/hongshi/projects/slime/slime/data/batch_builder.py:256) 为核心，按需回查奖励后处理。 | 用同一条样本解释 tokens、response_length、loss_mask、reward、rollout_log_probs 的用途与转换结果；说清原始奖励与后处理结果、哪些 token 参与训练、字段怎样对齐。 |
| **③ 生成与训练怎样闭环** | 以 [train](/home/hongshi/projects/slime/train.py:13) 为主线，通过 [RolloutManager._generate](/home/hongshi/projects/slime/slime/ray/rollout.py:335) 接回样本转换。 | 连贯说明生成结果怎样交给训练、何时通知完成与更新生成侧权重、评估放在哪里。理解异步数据与权重版本的关系，区分运行完成与持久 checkpoint；不展开 loss、优化器和通信内部。 |
| **④ 已读运行链怎样处理失败和回收资源** | 回到 [AsyncRolloutWorker._loop](/home/hongshi/projects/slime/slime/rollout/fully_async_rollout.py:178)、[_make_done_cb](/home/hongshi/projects/slime/slime/rollout/fully_async_rollout.py:246) 的有关分支，配 [test_fully_async_rollout.py](/home/hongshi/projects/slime/tests/test_fully_async_rollout.py) 中对应的单个场景。 | 实际进入时选定一个失败或取消案例，追清错误/结果去向、在途任务与资源如何收尾、后续工作能否继续，并用测试或受控实验核对。不把全部分布式恢复都展开。 |

这样排序是先把已读组件用于一次接入，再接通其产物到训练的正常主线，最后沿已有运行链补关键失败行为。若前一阶段出现阻塞当前任务的错误，可以就地处理该错误，不必等待第④阶段。

2026-10-28 局部调整：用户明确不需要继续讲解或测试 generate 的可等待要求，取消 async def / def 教学反例。该演示不作为进入第②阶段的前置；未运行的接入验证仍按实践缺口保留，不计为已通过。其余阅读顺序不变，下一具体 step 仍在范围确认后建立。

### 3. 下一步的具体范围已经明确

**Step 015 放在主题 02，围绕“怎样按框架约定写一个自定义 generate，并验证接入”展开。** [步骤入口](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/README.md)已建立；本节只保存既定范围，实际阅读与运行状态继续由唯一路线维护。

阅读推进为：

1. 回到 generate_and_rm 中选函数、传参、等待与接收返回值的局部；其余已读控制流程保留为背景。
2. 对照一个真实的 Coding Agent generate，整理实现承担的职责及 Sample / Sample 列表怎样交回；内部模型、工具和沙箱流程按已有记录回查。
3. 读一个匹配的契约测试，用一个最小调用观察真实输入、返回和副作用，明确测试覆盖与遗漏。现有测试断言只是部分验证，须与真实调用及下游数据要求核对。

scope 保存整体位置、上述阅读编号、关键源码入口和停止处。短期记忆重点保存调用约定、具体实现的输入输出以及本次实际验证；简单配套逻辑留在所属函数卡，不把每个 helper 拆成独立步骤。CPU 小例、模拟依赖与完整 Agent/模型运行必须分开标注，不能用前者宣称后者成功。

### 4. 同步保留的实践与暂缓项

- **评估与实验复跑**：结合前面的最小接入及已读 run_evaluation，固定任务/产物、模型与代码版本、采样配置、环境及评分规则，保存结果并复跑比较；不重读所有 grader，不把队列恢复当作完整实验复现。
- **Kubernetes / 容器**：独立安排实践，不必等待源码全部读完。围绕同一个最小服务或 worker 完成部署，并定位一次资源、连接或重启问题，留下操作、观察和修复依据。
- **Trace**：继续暂缓，恢复时以一次慢任务或失败任务的定位为目标，从真实使用和留下的记录进入；不自动回到 trace_utils 内部逐层展开。
- **按需选读**：QueueReader/straw、完整分布式恢复、WAL/pack/GC、训练 loss/优化器/通信内部，以及额外框架与跨语言源码。只有具体问题需要时才提升优先级。

这些实践用于形成接入、测试、诊断和迭代的证据；阅读完成、材料生成与岗位能力已验证分别记录。

### 5. 后续带读共同遵循的约定

1. **按问题选代码。** 每步说明为什么来到这里、调用方是谁、输入输出是什么、读到哪里停。新材料先归为当前必需、后续候选或可选参考，不因刚被贴出就改变主线。
2. **先有完整位置，再做局部展开。** scope 用普通代码块保留整体骨架与本步位置；阅读导航标 1、2、3 和关键行号。每次只展开当前要理解的一段，沿调用最多下钻两层，其他机制保留明确的黑箱边界。
3. **真实实现为主，测试帮助观察与验证。** 根据问题可先看一个小测试建立输入输出预期，但不将整份测试文件、fixture 或测试框架内部变成默认必读。
4. **复用已读，展示数据变化。** 已读函数先短提醒职责与输入输出；新增理解围绕一个连续例子和前后状态展开，避免重复逐行翻译或罗列全部字段。
5. **记录各司其职。** scope 管本步主线和导航；02 保存本步函数认识、必要例子及真实反馈；03 从上一实际步骤的 03 + 02 继承；04 保存追问、证据与修正。暂缓项也保留来源和未知，不虚构掌握状态。
6. **方向稳定，变更有依据。** Step 015 的问题与边界按本次计划接续，不重复确认已确定部分。后续若出现需要改变核心范围的新问题，先说明它与岗位或当前阻塞的关系，再确定调整；不默默扩大成整仓阅读。

源码入口核对本地 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，工作区无变更；旧材料继续保留各自版本。本次只整理计划、约定与导航，不修改 Slime 源码、不更新 Hugo、不运行插件或训练。

---

<details>
<summary>此前候选、优先级修正与历史路线（保留原文，不作为现行计划）</summary>

# 当前目标推进的slime阅读顺序

2026-10-28 能力范围见下方[完整 JD 复核](#full-jd-review-20261028)，下一入口见[岗位优先级纠正](#step015-jd-priority-correction)：队列保留为选读，优先考虑生成扩展的接入与验证。[straw 队列调度与混元岗位](straw-queue-jd-assessment-2026-10-28.md)保留该实现案例的具体边界。Trace 的暂缓状态与新步骤确认以[唯一路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准。

<a id="full-jd-review-20261028"></a>

## 2026-10-28：按完整职责复核，明确阅读与实践的检验目标

用户重新提供了[五条职责、六条要求及四条加分项](../../../../slime_photo/code-reading/job-evidence/2026-10-28-user-provided-jd.md)，要求仔细核对。以下是助手基于该文本与本地 Slime `18868a79` 的建议，不代表用户已经确认下一步或掌握这些内容。

此前“两块重点与一块概览”可作近期入口清单，但不能单独代表完整岗位准备。职责 1–3 的共同重点是把 Agent 研究流程做成可复用的组件，并支持策略、评估与实验接入；职责 4 要求运行治理，职责 5 要求理解这些组件与训练的交接。需要修正的是检验目标：已读调用流程还要能用于组件替换；评估还要能复跑和比较；训练交接还要说明关键数据的含义。无需因此平均深读整个框架。

| 必须保留的内容 | 具体代码与已有基础 | 下一步需要形成的解释或证据 |
| --- | --- | --- |
| Agent 组件边界：对应职责 2、3，要求 2、5 | 复用已读 Coding Agent 主线；按缺口回查 [BaseHarness](/home/hongshi/projects/slime/slime/agent/harness/common.py:57)、[BaseAdapter](/home/hongshi/projects/slime/slime/agent/adapters/common.py:190)、[Session](/home/hongshi/projects/slime/slime/agent/adapters/common.py:46)、[TrajectoryManager](/home/hongshi/projects/slime/slime/agent/trajectory.py:367) | 说清任务启动、模型协议、上下文、工具执行、轨迹各归谁负责。能指出替换一个 Agent 或模型接入组件时，哪些接口和状态必须保持一致。已读记录用于定点回查，不重读全部 helper。 |
| 策略、评估接入与实验复跑：对应职责 1、3，要求 4–6 | [generate](/home/hongshi/projects/slime/examples/coding_agent_rl/generate.py:225)、[run_evaluation](/home/hongshi/projects/slime/examples/coding_agent_rl/swe.py:290)，配套 [生成契约测试](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:148)或[评分契约测试](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_path_loading_contracts.py:342) | 做一个小接入：签名、输入输出、失败含义、正常与失败测试。用固定任务及产物，记录模型/代码版本、采样配置、环境和评分协议，复跑评估并比较结果。`run_evaluation` 用干净评估环境验证 diff；完整实验复现还需要上述配置与产物记录。区分 Agent 任务评分与训练期间的独立评估入口。 |
| 并发、资源与行为一致性：对应职责 4，要求 1、5 | 已读本地 AsyncRolloutWorker 正常链；可选实现案例 [QueueReader](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1002) 的 get_samples / get_samples_async / add_samples，配[跨 reader 续跑](/home/hongshi/projects/slime/tests/test_distributed_rollout.py:337)与[归还回复丢失](/home/hongshi/projects/slime/tests/test_distributed_rollout.py:390)测试 | 能把任务积压、阻塞、容量与清理对应到具体状态，并验证一个失败场景。可先在已读 worker 上补关键失败路径；若选择队列案例，再解释 A 归还 partial、B 领取续跑和旧 lease 的处理。性能结论要有观察或测量，不要求通读 WAL、pack、GC 或完整分布式恢复。 |
| RL 数据与训练交接：对应职责 5、要求 4 | [BatchBuilder.convert](/home/hongshi/projects/slime/slime/data/batch_builder.py:256)连接 [RolloutManager._generate](/home/hongshi/projects/slime/slime/ray/rollout.py:335)与 [train](/home/hongshi/projects/slime/train.py:13) | 用一条真实结构的 Sample 跟踪 tokens、response_length、loss_mask、reward、rollout_log_probs：哪些 token 参与学习、奖励和生成时概率起什么作用、字段如何对齐。再解释生成→训练→更新生成侧权重→评估，以及权重版本差异为何影响异步数据。需要理解用途，不要求通读 loss、优化器或并行通信实现。 |

表中源码是本机定位链接，行号提示以 `18868a79` 为准。前三项可由同一个小需求贯穿：接入一个策略或评估变化，观察并发与失败行为，补测试并记录结果；不必分别造三个项目。岗位要求 6 的沟通与 owner 意识通过需求澄清、取舍、验证与迭代记录体现。

### 单独保留、不可被其他模块替代的部分

- **Trace/日志**：Step 014 继续暂缓。以后以定位一次慢任务或失败任务为目标补齐，不再以拆完 trace_utils 的内部 helper 为目标。
- **Kubernetes/容器**：要求 3 明确要求实际集群经验。用上述同一个最小服务或 worker 做部署、资源/连接/重启排障；Ray 和 straw 源码不能替代这项实践。
- **实验复现的层次**：先做到配置与产物可追溯、评估可复跑、差异可解释。队列持久化、断点恢复和随机训练逐位一致各有额外条件，不能相互等同，也不将全部底层恢复实现列为本轮前置。
- **加分项**：AI 编程工具、Coding Agent 与现有知识库建设可结合实际成果说明；跨语言协作由具体改动触发，不扩为 TypeScript/Rust/Go 全仓阅读任务。

### 建议接续

按岗位职责和当前缺口，优先建议完成一次生成扩展的接入与接口验证，复用已读 generate_and_rm 与 Coding Agent 主线；训练交接和已读 worker 的关键失败路径仍保留。QueueReader 的跨 worker 交接是按实际问题触发的选读案例，不能仅因用户贴出相关 diff 就升级为下一必读。Trace 按用户决定恢复，Kubernetes 实践不必等所有源码读完。

这是建议与实际讨论的保存：没有开启新 step，没有运行插件、评估、故障实验或训练，没有新增掌握判断。下方旧方案完整保留为修正前快照。

<a id="step015-jd-priority-correction"></a>

### 2026-10-28：区分岗位能力、实现案例与下一步优先级

用户追问：

> 确定要读的内容是这个吗？
> 需要看这里的test distributed rolllout还是这里的queue data source 解决或者对应的内容是哪一块呢？
> 主要的是你确定这是这个岗位要求的内容吗？ 还是只是因为我把这个内容paste了在上面呢？

助手修正：此前队列选题确实顺着用户贴出的 diff 推进；其与岗位存在关联，但仅凭关联不足以把它排成岗位导向的下一步。JD 要求并发、资源与行为一致性治理，未指定持久队列、lease、straw 或跨 worker continuation 为必读实现。没有该 diff 时，按已读基础与尚未验证的缺口，应优先考虑职责 2、3 直接提出的组件接入与验证。

两个文件的职责明确区分：`slime/data/queue_data_source.py` 是运行时的持久任务领取/归还实现；`tests/test_distributed_rollout.py` 中的指定测试提供输入与预期行为，用来核对实现，不是另一个运行时组件，也不需要通读整份测试文件。先看该测试只是一种帮助理解案例的读法，不能决定整个选题优先级。

**新的优先候选问题：一个自定义 Agent 生成函数，怎样满足 Slime 的调用与返回约定，并验证接入正确？** 复用 [generate_and_rm](/home/hongshi/projects/slime/slime/rollout/sglang_rollout.py:289) 的已读调用位置，对照真实 [coding_agent_rl.generate](/home/hongshi/projects/slime/examples/coding_agent_rl/generate.py:225)，最后选读 [生成扩展契约测试](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:148)。[本地官方文档](/home/hongshi/projects/slime/docs/en/get_started/customization.md:517)将这些测试定位为自定义接口的 CPU 验证方式。

本候选的新增内容是实际输入输出、调用者预期、测试覆盖范围与未覆盖的失败行为；已读分派流程只做回顾。现有测试断言是验证样例，不等于完整生产合同，必须对照真实调用和实现。目标是完成一个最小接入并说明验证依据，不重新遍历所有 generate/helper 或 rm_type。具体范围仍待用户确认，尚未创建 Step 015、修改插件或运行测试。

<a id="generate-integration-versus-repeat-reading"></a>

#### 已读流程与“自己接入一个 generate”的区别

用户回顾已读 `generate_and_rm`、`AsyncRolloutWorker._loop` 和 group handoff，并询问下一步是否就是了解一个 generate 应该怎样写。

核对 [主题 01](../topics/01-coding-agent-rl/README.md) 与 [主题 02](../topics/02-rollout-reward/README.md) 后，需要保留完整历史：用户此前也读过 Coding Agent 的 `generate → _generate`、模型请求、沙箱、评估与轨迹导出；不能将当前基础说成“只读了 generate_and_rm”。已有记录反映阅读与明确反馈，不能直接推出所有边界已掌握或已经具备独立实现能力。

助手澄清：用户对下一候选目标的概括基本一致——弄清自己接入一个 generate 时应该怎样实现并验证。新增视角是把已读的具体实现整理为可迁移的接口要求：框架传入什么、插件承担什么、交回的数据和状态需要满足什么、哪些调度和结果处理继续由框架负责，以及怎样检查正常与失败行为。以一个最小接入或改动验证这些要求即可，不重新通读 Agent 全链，也不先重造完整 Agent 框架。

该候选主要对应职责 2、3 与要求 5、6。完整岗位准备仍包括：在已读运行链上补关键失败/取消与资源清理；按用户意愿恢复 Trace 诊断；补 Sample 到训练数据及权重更新的交接；做容器/Kubernetes 部署排障。评估配置、产物记录和复跑可结合小接入一起验证。它们保留原有范围，不因这次澄清另加新模块。

本轮仅澄清已读内容与候选目标；用户是在核对理解，尚未表达已经能够独立编写插件，未据此创建新步骤或新增掌握判断。

<a id="step015-queue-handoff-proposal"></a>

### 此前 Step 015 队列候选：保留为选读，已撤回下一步首选排序

用户原话：

> 那么是否需要开启新的step呢？
> 重点是需要清楚开启的step具体解决的内容是什么这件事情

当时建议单开 Step 015，接回主题 02 的 Rollout 调度问题。用户随后要求核对选题是否受粘贴内容影响，现已按上方纠正撤回首选排序；以下保留该案例的原范围，供按需回访。Step 014 的 Trace 继续暂缓，尚未创建新的步骤目录或函数卡。

**唯一核心问题：一个已准备好、可归还的 partial group，怎样从 worker A 交回共享队列，再由 worker B 领取？** 这补足此前 worker 从数据源取 group、把未完成结果交回数据源时留下的接口黑箱；本次选定 straw 的 QueueReader 路径。

```text
共享队列
  → worker A 领取 group
  → 得到可归还的 partial group       # 本步将其作为输入前提
  → A 保存并归还
  → 共享队列可再次分配
  → worker B 领取该 group 的保存内容
```

这是跨时刻的数据交接示意，不是单个函数的调用栈。上层真实位置为 `_GenerationActor._produce` / `_generate_group` 的取组调用，以及 `_rebuffer` → `_flush_rebuffers` 的归还调用；这里只定位它们与 QueueReader 的连接，不展开整个分布式 worker。具体 Agent 是否继续旧 token、重启会话或恢复外部进程，不由本步的队列交接直接保证。

| 阅读顺序 | 入口 | 这部分要解决什么 |
| --- | --- | --- |
| 1. 先看交接实例 | [test_returned_partial_is_available_to_another_reader](/home/hongshi/projects/slime/tests/test_distributed_rollout.py:337) | 测试构造了哪些 partial 数据，B 领取后要求保留什么、改变什么；先有可观察目标。 |
| 2. 看领取 | [QueueReader.get_samples](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1050)；[get_samples_async](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1102)只补调用方式 | 领取请求怎样取得 group 和 lease，怎样载入 Sample 并登记本次领取。异步包装先理解为将阻塞读取交给 reader 线程。 |
| 3. 看归还，再回到 B 领取 | [QueueReader.add_samples](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1106)，按需短看 [RolloutQueueController.return_groups](/home/hongshi/projects/slime/slime/data/queue_data_source.py:388) | 仅走有效 partial、尚未 accepted 的归还分支：保存输入、归还任务、移除 A 的领取记录；再用同一个 get_samples 解释 B 为什么能取得它。 |

**最小前置**：只区分 group/Sample（工作内容）、队列任务（调度记录）、lease（本次领取凭证）；不先通读数据源构造、Ray 启动或全部队列字段。

**短期记忆准备保留**：领取与归还两个主要函数的输入、输出/副作用，以及同一个 group 在“A 领取后→归还后→B 领取后”的变化。重点跟踪样本标识、保存的生成内容、领取凭证与本地登记；`get_samples_async` 只需最短的配套说明。scope 保存整体位置、编号与源码入口，不把每个辅助调用拆成新卡。

**停止位置**：能依据源码和该测试解释“哪些内容保留、谁现在可以处理、A 为什么不再持有原领取”，本步就可以收束。该测试只验证保存内容可由另一 reader 取回，不声称真实模型已续跑成功。本轮只静态核对了源码与测试，尚未执行测试。

**后置问题**：worker 崩溃、lease 超时/续租、回复丢失、优先级/staleness 排序、accepted delivery、checkpoint、WAL/pack/GC，以及上层怎样生成可归还的 Agent 结果。若当前 partial 分支需要一次下钻，就停在队列接口的输入输出，不进入存储引擎。

<a id="remaining-code-scope-20261028"></a>

## 2026-10-28 修正前快照：两块重点与一块概览

本节保留当时建议；完整岗位范围及检验深度以[上方完整 JD 复核](#full-jd-review-20261028)为准。

用户原话：

> 为了对齐 腾讯的岗位 我还需要看哪些代码呢？

按用户提供的六条任职要求与当前阅读记录整理。Coding Agent 单任务链路、generate_and_rm / group、评分接口、AsyncRolloutWorker 的正常调度和完成交付已有阅读记录，后续有具体缺口再回查；不能因此将全部失败分支或所有机制记为掌握。Step 014 的 Trace 保持暂缓。

下列三项是剩余阅读建议，尚未创建新 step；第 3 项只补训练数据与控制交接的概览，不与前两项投入相同深度。源码均核对本地固定版本 18868a79，不能当成远端 main 的当前行号。

| 建议顺序与深度 | 具体代码 | 读到哪里停，以及怎样验证 |
| --- | --- | --- |
| 1. 重点：任务领取、归还与故障处理 | [QueueReader.get_samples / get_samples_async / add_samples](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1050)；遇到 lease 问题再读 [_heartbeat_loop](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1029) 与 [close](/home/hongshi/projects/slime/slime/data/queue_data_source.py:1268) | 先解释 worker A 归还 partial 后，worker B 如何接着处理，以及旧 lease 怎样结束。配 [跨 reader 续跑测试](/home/hongshi/projects/slime/tests/test_distributed_rollout.py:337) 和 [归还回复丢失测试](/home/hongshi/projects/slime/tests/test_distributed_rollout.py:390)。再选择一个失效/取消场景，不通读持久队列与存储引擎。对应 JD 1、2、5。 |
| 2. 重点：扩展接口与契约测试 | [自定义生成契约测试](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:148)；或 [自定义评分契约测试](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_path_loading_contracts.py:342)，回接已读生成/评分接口 | 选一个最小生成或评分扩展，说明签名、返回数据及调用者预期，并为实际改动补正常与失败情形验证。现有测试检查签名、类型/形状等条件，不能据此断言覆盖所有异常。目标是能完成接入并说明如何验证，对应 JD 1、2、5、6。 |
| 3. 概览：训练数据与主循环交接 | [BatchBuilder.convert](/home/hongshi/projects/slime/slime/data/batch_builder.py:256) → [RolloutManager._generate](/home/hongshi/projects/slime/slime/ray/rollout.py:335) → [train.py::train](/home/hongshi/projects/slime/train.py:13)，按调用关系回接 | 用一个 Sample 看 tokens/reward/logprob/mask 如何进入训练字段，再看生成 → 训练 → 通知完成 → 更新生成侧权重。区分奖励后处理与再调用奖励模型、运行完成与持久 checkpoint。只看正常主干，loss、优化器、模型并行和权重同步内部暂不展开。补足 JD 4 的框架背景。 |

第一项的上层分布式执行者是 [_GenerationActor](/home/hongshi/projects/slime/slime/rollout/fully_async_distributed.py:256)，只定位 reader 创建与异步取组的调用，保持和已读本地 AsyncRolloutWorker 的边界。详细范围继续见 [straw 选题评估](straw-queue-jd-assessment-2026-10-28.md)。

### 单独保留的能力缺口

- Trace 暂缓是学习顺序调整，不从岗位要求中删除日志与诊断。以后围绕一次慢/失败任务观察已有记录，不要求重新逐层拆所有 trace helper。
- Kubernetes/容器仍需实际部署与排障。可参考 [docker/Dockerfile](/home/hongshi/projects/slime/docker/Dockerfile) 的环境组织，但不把完整 GPU 镜像构建或整个 serving 模块作为开始实践的前置。选择已有最小服务/worker，保留一次资源、连接或重启问题的处理证据。
- Python 与工程能力需要实际修改、测试和解释取舍。第 1 项故障实验与第 2 项小扩展可承担这部分练习；读完源码不直接等于岗位能力已验证。AI 工具和跨语言加分项按真实任务积累，不另加整套 Rust/Go/TypeScript 源码课程。

当前建议顺序是队列生命周期 → 小扩展与测试 → 训练交接概览。Trace 保持暂缓，下一具体 step 仍待用户确认；本轮只有静态源码与测试入口核对，没有执行测试、插件或训练。

## 此前路线快照

历史路线目标（2026-10-25）：对齐腾讯混元 Agent 强化学习框架工程师岗位，在已读完 Coding Agent 单题正常主线的基础上，继续学习**框架接入 → 评分扩展 → 批量调度 → 训练交接**。

[返回目录](README.md) · [岗位对应与评估依据](hunyuan-jd-reading-order-assessment-2026-10-25.md)

2026-10-26 补充：下文保留 10 月 25 日的路线快照。近期新增深入保持结果交付、Trace、接口验证；完整范围还包括已读 Agent 主链、训练/评估背景及 Kubernetes 实践，训练内部与完整分布式实现仍按需。详见[范围与检验标准](../../../../slime_photo/code-reading/job-alignment.md#jd-minimum-sufficient-scope-20261026)，当前已读位置只以[唯一路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准。

## 建议阅读顺序

| 顺序 | 模块与入口 | 读到能说明什么为止 |
| --- | --- | --- |
| 1. 框架怎样调用 Agent | [slime/rollout/sglang_rollout.py：generate_and_rm](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L289-L380) | 自定义 generate 怎样装载、调用；Sample 或列表怎样交回；已有 reward 时怎样处理 |
| 2. 评分逻辑怎样接入 | [slime/rollout/rm_hub/__init__.py：async_rm、batched_async_rm](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/rm_hub/__init__.py#L55-L110) | 单条与批量评分如何调用，自定义评分器接在哪里；先读接口，再选一个实现 |
| 3. 多条轨迹怎样组织 | [slime/rollout/sglang_rollout.py：generate_and_rm_group](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L388)，按需回查 GenerateState | 同一道题的多次采样如何并发、汇总和整组评分；并发限制与取消怎样影响结果 |
| 4. 持续生成怎样调度 | [slime/rollout/fully_async_rollout.py：AsyncRolloutWorker](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L82) | 沿 _loop、_make_done_cb、get_completed_groups 看任务生产、完成队列、背压与结果消费 |
| 5. Sample 怎样成为训练输入 | [slime/data/batch_builder.py：BatchBuilder.convert](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/batch_builder.py#L256)，连接 [RolloutManager._generate](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L335) | tokens、reward、logprob、mask 如何交成训练数据，哪些字段必须保持一致 |
| 6. 生成与训练怎样闭环 | [train.py：train](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/train.py#L13) | 生成结果怎样交给训练，训练后怎样更新生成侧权重；先看控制与数据交接 |

- **1、2 对应策略与评测接入**，最能承接已经读过的 Coding Agent。
- **3、4 对应并发、资源与稳定性治理**。示例默认 straw 使用分布式 fully-async；第 4 项的本地 worker 用来建立基础模型，之后还需对照 DistributedRollout，不能直接等同于默认执行体。
- **5、6 对应训练视角与工程交接**。具体损失、并行通信和优化器内部按需后置。

## 2026-10-25 的首个候选入口（历史快照）

先读 `generate_and_rm`，围绕三个问题：**谁调用我们的 Agent？返回值要满足什么？奖励由谁负责？**

```text
generate_and_rm
  → 选择 custom_generate_function_path
  → 调用已读的 coding_agent_rl.generate
  → 接住 Sample / Sample 列表
  → 判断是否还需要评分
```

## 贯穿主线的配套

- **测试与 Trace**：从第 1 项配套现有 `tests/plugin_contracts/`；到并发部分，选一个超时或取消案例，验证结果并定位问题。
- **Kubernetes**：从第 3、4 项同步实践。在已有简单部署经验上，重点补资源限制、服务连接和故障恢复。
- **Dressage**：遇到具体接口或评测抽象问题时做定点对照。

记录于 2026-10-25，源码基准为 Slime `18868a79`。本页保存选读路线，实际开始位置仍以[唯一路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准。

</details>
