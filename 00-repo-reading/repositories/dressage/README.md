# Dressage：按岗位目标逐步建立整体模型

[通用方法](../../README.md) · [工作流](../../workflow.md) · [学习指南](references/design-on-slime.md#reading-guide) · [岗位对照资料](job-and-repo-comparison.md)

阅读目标：为腾讯混元 Agent 强化学习框架岗位建立能力，围绕任务执行、模型与工具调用、上下文与轨迹、评测、训练数据交接及运行治理逐步阅读。官方文档作为资料索引；具体入口按当前问题、真实调用与必要前置选择。

2026-11-08 用户再次明确：主要目标是该岗位。Harbor 与 Agent Sandbox 接入是展示组件接缝、集群运行和失败治理能力的实践案例，不替代岗位学习主线。当前仍从 Step 007 继续轨迹、Sample 与清理；兼容性研究不自动改成优先完成集成或升级工程。

后续学习按[设计与源码学习指南](references/design-on-slime.md)推进：先走通一份黑盒任务，再围绕接口分工、轨迹数据、分段训练语义、长任务治理和失败处理五个方向深入。指南保留源码依据与停止标准，实际进度只在下节维护。

针对岗位的阅读终点建议见[读到哪里可以停止系统通读](references/design-on-slime.md#job-reading-stop)：单任务闭环、训练数据正确性、并发与失败治理三个验收层次，沿用上述五个方向；不表示已读或新增步骤。

最新适配研究见 [Dressage × Harbor × Agent Sandbox](references/agent-sandbox-harbor-integration-research.md)：核对两条真实执行路线、固定 Harbor 源码、K8s 预热及商业模型 API 的接缝，给出六个阅读单元和停止标准。此为接入方案研究，不表示已完成代码适配。

**后续阅读顺序**以各步最新 scope 为准（2026-11-12 按调用交接调整，登记在[阅读规划](references/integration-reading-plan.md#call-order-scopes-applied-20261112)）；原整体顺序见[接入阅读规划](references/integration-reading-plan.md)：旧 blackbox generate 主线收尾 → Dressage 的 Harbor 批量入口 → Harbor Trial → Environment 与 K8s 适配 → 模型与结果采集。规划负责顺序，研究报告负责技术依据；按本次要求已准备后续各步 scope，尚未生成未读函数卡。

2026-11-17 运行前提补充：**从 Slime 发起、无本地 GPU、调用国内厂商 LLM API，先观察 Agent 任务表现与评测结果，不做权重更新。** 框架组合判断、适配边界和候选推进顺序单独保存在[Slime 起点的 API 评测方案](implementation/minimax-harbor/README.md)。现已按用户要求建立独立实施单元；未启动新的阅读 step 或完成接入验证。

## 源码与当前接续

- 2026-11-17 改造基线确认：用户指定当前本地 Dressage，提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`，`main` 工作区干净；重新检查发现 origin 已变为 `git@github.com:dextermayhewjd/Dressage.git`。后续 API 适配以此为基线，详见[基线记录](implementation/minimax-harbor/README.md#baseline)。下方此前 remote 核对记录保留历史归属。

- 当前本机源码仓库：`/home/hongshi/projects/Dressage`（2026-11-16 核对，工作区干净，origin 为 `https://github.com/Accio-Lab/Dressage.git`）。历史路径 `/home/fredkeira/projects/Dressage` 与 `/Users/dextermayhew/projects/Dressage` 保留在旧记录中。
- 本轮核对提交：`3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- Harbor 版本对照（2026-11-11）：本机已有 `/home/fredkeira/projects/harbor`，HEAD `500af91374dcc43b59fac54cf90295646617b14d`；pyproject 标为 0.25.0，但比发布标签多 123 个提交。Dressage 已读调用方仍依据其锁定的 0.18.0；用户现已确认 Step 011 起直接读 Harbor v0.25.0 发布标签（fdba28fc），跨版本运行待验证；[来源与升级核对](references/agent-sandbox-harbor-compatibility.md#harbor-version-upgrade-20261111)另存，旧阅读记录保留版本归属。
- Harbor 当前本地源码（2026-11-16）：`/home/hongshi/projects/harbor`，HEAD 与 `v0.25.0` 标签均为 `fdba28fc411e47e8765420a1a063b4918fce3def`，工作区干净，origin 为 `https://github.com/harbor-framework/harbor.git`。后续沿用此路径；上条保留旧环境的版本对照历史。
- 当前接续：2026-11-17，[Step 016](topics/02-harbor-integration/steps/step-016-cancellation-and-retries/01-scope.md) 的单次外部取消、清理正常完成路径已完成本轮源码阅读：取消记录/CANCEL → 输出恢复 → finally/END → 脱敏/日志关闭 → 继续传播取消。用户已讨论并复述相关职责，不等于全部分支掌握；未验证真实资源释放。当前按用户要求回访 Step 013，先核对 BaseEnvironment 的沙箱接口及现成例子，见[接口对照](references/harbor-sandbox-interface-map.md)。Step 017 接入验证尚未开启；普通失败重试和复杂清理不新增为必读前置。
- 阅读深度反馈（2026-11-09）：用户表示逐函数下潜负担过重，同时希望保留 Step 010–017 来理解 Harbor 接入与评测框架整体。继续沿既有路线走通模块主线，按接口、资源和数据正确性决定下钻深度，不自动把每个 helper 变成必读卡；在生命周期和环境接口清楚后穿插最小实践，不等最后才验证。已读记录与编号保留，未实施边界见 [Step 010 形成过程](topics/02-harbor-integration/steps/step-010-harbor-rollout-entry/04-flow.md)。
- 阅读方式：先收尾原生 generate 的轨迹、样本和清理，再沿 Harbor 接入主题推进。深度依据[学习指南 4.3](references/design-on-slime.md#six-stage-reading-order)，不把每个辅助函数扩成独立专题。
- 当前学习内容在 Markdown 中预览；博客呈现另按用户明确要求处理。

## 实施任务入口

本次 Dressage 升级已确定只交付 `harbor==0.26.0`，0.25.0 的阅读和运行材料用作历史对照。升级判断和实验记录维护在本仓库的 `implementation/harbor-026-upgrade/`。从问题页看为什么改，从 PR 页看哪些改动一起评审。代码和回归测试在独立 Dressage 工作树 `compat/harbor-0.26` 实施。[调查索引](implementation/harbor-026-upgrade/README.md#investigations) · [PR-001 评审页](implementation/harbor-026-upgrade/prs/001-harbor-026-compatibility/README.md)

[MiniMax × Harbor 改造实践](implementation/minimax-harbor/README.md)：从已确认的 Dressage fork 版本出发，先完成 Slime 发起的无 GPU API 评测，再接 Agent Sandbox。实施进度只在该单元 README 维护；下方 topics 保留源码阅读历史与函数卡。

## 主题入口

| 主题 | 解决什么问题 | 步骤范围 |
| --- | --- | --- |
| [原生 Dressage 单任务闭环](topics/01-native-agent-rollout/README.md) | 任务、环境、Agent 执行、轨迹、Sample 与回收 | 原 Step 000–006 已整体归入；Step 007–009 已按各自确认范围首轮收束 |
| [Dressage × Harbor 接入与验证](topics/02-harbor-integration/README.md) | 任务与 Agent 适配、K8s 接缝、模型和结果采集、失败与验证 | Step 010–012 首轮收束；Step 013 保留待回查项；Step 014 已补读模型请求主线；Step 015 已开始；Step 016–017 仅 scope |
| [Agent Sandbox：Kubernetes 环境分支](topics/03-agent-sandbox/README.md) | Sandbox、Pod、状态、WarmPool、Claim 与访问隔离 | 本目录提供第三个导航入口，正文复用 Agent Sandbox 独立主题及其编号 |

3.1 保留本步在主题主线的位置；3.2 的图只表达执行关系，下方连续编号表表达阅读顺序。Step 016–017 目前只有 scope，不提前生成 02、03、04 或 05。目录迁移不改变原有认识和来源。

<a id="confirmed-reading-and-implementation-route"></a>

## 已确认的阅读与实施顺序（历史安排）

> 以下保留此前以 AgentLab 项目与 Step 017 为落点的安排。2026-11-17 用户已确认本轮改为在 Dressage fork 上实施，现行计划见 [implementation/minimax-harbor](implementation/minimax-harbor/README.md)；不将旧安排自动列为本次前置。

以腾讯混元 Agent 强化学习框架岗位为主目标，使用现有 slime_api_data_collecting 项目承接实践。三个 topic 是同一条学习与实施路线的组成部分，按下面的交接继续：

1. **Dressage Step 007–009：收尾原生任务闭环。** 从[会话收尾与轨迹取得](topics/01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/01-scope.md)开始，接 Sample 转换与退出清理。
2. **Dressage Step 010–012：理解批次入口、Trial 生命周期及任务/Agent 对象来源。** 从[Harbor 入口](topics/02-harbor-integration/steps/step-010-harbor-rollout-entry/01-scope.md)进入，接清 Trial 与输入对象；实际评测在 Step 015 的运行位置继续。
3. **Dressage Step 013 → Agent Sandbox → 返回 Step 013。** 先明确 [Environment 合同](topics/02-harbor-integration/steps/step-013-harbor-kubernetes-environment/01-scope.md)，再通过[第三个 topic](topics/03-agent-sandbox/README.md)，按既有进度核对状态、WarmPool、Claim 和执行访问。带着这些资源行为回到 Step 013，完成接口映射与最小冷创建验证。**不需要等整个 Harbor topic 结束才读 Agent Sandbox。**
4. **Dressage Step 014–016：接清 Agent 执行、模型请求、评测结果与失败处理。** 从[模型路由与 API 合同](topics/02-harbor-integration/steps/step-014-model-routing-and-api-contract/01-scope.md)继续，明确采集、评测结果、取消和重试的责任。
5. **Step 017：在现有项目中落实整合与验收。** [实施范围](topics/02-harbor-integration/steps/step-017-integration-validation/01-scope.md)包括固定任务、真实 Agent、模型请求、评分、结果汇总和回收，并补换 Agent、少量并发及一次失败/取消。保留旧 Runner 作为基线，逐项落实已经明确的适配；这里交付可运行结果，不自动追加一套新的理论阅读。

第三个 topic 只提供跨项目导航，K8s 正文与记忆仍唯一保存在 Agent Sandbox 项目，继续使用它自己的步骤编号。必要接口清楚后即可做局部验证，Step 017 用于整合与补齐证据；“scope 已准备”不表示阅读、实现或验证已经完成。

## 本次按问题对照

- [本地 AgentLab 与三件套路线的区别](references/agentlab-current-vs-harbor-dressage.md)：按当前 CLI 和源码区分已有编排、预热、K8s、评测能力，以及迁移会替换的职责和未接通的轨迹边界。

- [三个 topic 的评测体系完整性审查](references/evaluation-system-scope-audit.md)：判断现有范围能否支撑首版成品，区分学习覆盖、实现缺口和具体验收；与岗位能力审查分开。

- [topic 与每步 scope 的划分依据](references/topics-and-step-scopes-after-step006.md)：原生主线用 007–009 收尾，Harbor 接入按 010–017 规划，K8s 复用 Agent Sandbox 独立主题；对应 scope 已准备，未据此登记为已读。

- [Step 006 之后的岗位范围复核](references/post-step006-job-reading-review.md)：对齐最新确认的 JD 与接入规划；[现有 scope 覆盖审查](references/post-step006-job-reading-review.md#coverage-audit)指出上下文续接、分段奖励、故障/耗时观察、自动验证四处需明确的落点。审查是补强建议，不替代上面的唯一进度。

- [Dressage 学习指南与设计增量](references/design-on-slime.md)：基于锁定提交保存五个学习方向、首轮主线、两条结果通道和各轮阅读边界。

- [CLI 输出与模型 API：从哪里取得哪些信息](references/cli-output-and-model-api.md)：区分 Agent 程序输出与模型交互记录，并按问题定位启动、事件转换、代理采集和训练数据交接的源码入口。

- [与 Agent Sandbox 的预热和领取比较](../agent-sandbox/references/dressage-prewarm-comparison.md)：核对按 sample/session 预热、FIFO 派发与等待、provider 限制；这次比较不改变当前正式阅读步骤。

- [当前是否有 Kubernetes/单 Pod 配置](../agent-sandbox/references/dressage-prewarm-comparison.md#dressage-kubernetes-provider-boundary)：当前自有代码只提供 e2b/local_bwrap，Kubernetes 需要自行实现 SandboxProvider；Docker 运行环境与单任务 Pod 生命周期分开判断。

## 历史与证据边界

早期整理时，原 steps 目录曾已不存在。此前项目入口对 Step 1 的描述保存在[历史快照](topics/01-native-agent-rollout/steps/step-000-slime-bridge-and-interfaces/references/project-entry-before-step0.md)，不据此重建旧函数卡片或推断用户掌握状态。本次 topic 整理完整保留后来实际建立的 Step 000–006 记录；当前接续只在本页维护。

[认知阅读指南](cognitive-reading-guide.md)与岗位对照保留作既有参考；其中旧步骤安排不覆盖本轮确认的 scope。源码解释、个人理解和真实运行证据分别记录。

## 沙箱基础设施与岗位参考

- [沙箱基础设施、岗位职责与本地实践：原始讨论](implementation/references/sandbox-infra-discussion-original.md)：实施公共参考材料，不限定于 MiniMax 接入；保留用户提供的正文，尚未逐项核验。
