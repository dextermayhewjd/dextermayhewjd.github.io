# Slime 源码阅读路线：Research Agent 框架工程

本路线把模型调用、工具执行、任务与上下文、Trace、结果评测、并发恢复、集群资源和训练交接组织成连续的源码阅读单元。第一遍能说明每个部分具体做什么、需求应接在哪里；第二遍能追踪关键数据、失败分支和验证方法。

<a id="当前优先沿-generate-读完-41"></a>

## 当前接续

更新：2026-10-19，依据用户本轮明确反馈。这里是唯一的学习接续记录；下方章节合同、旧材料和源码索引不能覆盖它。

- **目标与条件：** 按用户提供的腾讯混元 Agent 强化学习框架工程师 JD 决定详略。本地无 GPU，以读明白和模型 API 辅助验证为主；前置与初始时间预算见[岗位对照](job-alignment.md#当前学习条件与投入安排)。
- **当前协作：** 用用户指定的 Action 2 页面推演工作流与 skill。助手先定位，由用户说自己的模块理解；只知道作用、尚不清楚实现时允许留白。用户已表达 `_translate` 返回对话历史与工具 schema、common 规定共同约定、两个 Adapter 提供具体实现，具体转换仍不清楚。助手详细讲解独立保留为参考。[Step 01](../../00-repo-reading/discussions/step-01-translate-preview/README.md) 的两个函数已采用[统一记忆格式](../../00-repo-reading/memory-format.md)；本步新认识放 `02`，`03` 暂无前序模型导入。通用模板现已同步，旧步骤保留原快照；格式规范不增加已完成或已掌握的学习范围。
- **认知记录入口：** 使用根目录的[通用工作流](../../00-repo-reading/workflow.md)，本项目保留 [000 初始模型](../../00-repo-reading/repositories/slime/steps/step-000-initial-model/README.md)作为起点记录。新步骤使用整体地图和镜像源码目录的逐函数记录，下一步 `03` 合并前一步的 `03` 与 `02`，新的 `02` 保存本步新认识。000 的旧目录保留，其技术模型仍待带读反馈，不是已掌握记录。
- **已读范围与记忆提醒：** 用户明确表示 `generate()` 的完整任务链已经走过，同时提醒走过不等于全部记住。保留已读事实；续读时先短回顾职责、输入输出与主线位置，根据具体问题补细节，不默认重讲全链，也不自行断言忘了哪些部分。
- **当前问题：** 从阅读目标建立“任务数据与配置 → 生成和评分 → 样本/批次 → 训练 → 权重返回”的基本框架，再逐步看清启动与职责交接；不从已读 `generate()` 倒推全景的起点。
- **固定下一步：** 从 [000 初始模型](../../00-repo-reading/repositories/slime/steps/step-000-initial-model/README.md)和 [00 全景 Walkthrough](http://localhost:1313/projects/slime/framework-walkthrough/)的基本框架进入 `train.py::main()`，回答“谁启动工作，第一次怎样进入循环”；实际展开时创建下一份步骤，继承完整记忆。后续沿服务准备、train 和 rollout 的真实交接推进；重遇 `generate()` 才按需短回顾。
- **本轮停止点：** 能把启动入口、资源/模型服务、批量调度、单份任务、训练数据消费者放在同一条调用与数据链上。后续深入扩展/评测、Trace/验证和并发/恢复；不因建立地图而平均展开所有训练和硬件细节。
- **资料用法：** 官方整体实验入门的 “The loop you are building” 用于概念对照；`agent.html` 用于查 Agent 接入点；本地 00 用于职责定位；实际调用以当前固定源码为证据。它们服务同一条阅读主线，不互相替代成新的课程顺序。
- **心智模型与正文：** 用户要求此方法适用于任意 repo，统一保存在根目录 `00-repo-reading/`。每步保留自己的基本理解、源码位置及新增或修正关系；连续技术解释维护在 [00 walkthrough](chapters/00-overview/walkthrough.md)，由 Hugo 直接渲染。步骤保存模型快照与引用，不手工复制另一份全文；当前状态只在本节维护。

### 阅读与验证记录

| 范围 | 阅读反馈 | 理解与运行证据 |
| --- | --- | --- |
| 00 全局职责与启动主线 | 用户当前要求补全全景及更上游入口，已开始讨论 | 理解程度尚无明确反馈，不要求先复述才能继续 |
| 01、02 中的 `generate()` 完整任务链 | 用户 2026-10-19 明确反馈已完整走过，并说明内容可能未全部记住、需要提醒 | 具体记忆缺口未逐项反馈；已读不等于全部分支验收，本轮没有真实 Agent、GPU 训练或集群运行证据 |
| 02 的轨迹分叉、改写与 token 对齐专题 | 入口保留为深入材料 | 没有整章或专题完成反馈，不自动续读这些内部细节 |
| 03–07 的独立深入单元 | 按当前主线与岗位优先级继续；本轮无逐单元完成反馈 | 不从 planned/ready 或测试材料存在推断已读、掌握或运行 |

用户明确反馈已读、卡住、跳过或改读另一层时，同轮更新本节的范围与下一步；章节 README/review 只链接本节。源码版本变化保留已读事实，另记需重新核对的接口差异。

### 当前源码与已有材料的版本边界

- 当前实测仓库：`/home/hongshi/projects/slime`，HEAD `2f2318653f6f794dddd321eff7c9d4b7b174643f`；已跟踪源码无改动，保留未跟踪的 `asyncio_concurrency_best_practices/`。历史 `/home/fredkeira/projects/slime` 在本机不存在。
- 本轮已按当前 HEAD 核对的入口：`train.py::main` 第 103 行、`create_rollout_manager` 第 293 行、`RolloutManager.generate` 第 303 行、`generate_and_rm` 第 289 行、Coding Agent `generate` 第 182 行、`BatchBuilder.convert` 第 237 行。新的讲解继续核对实际调用，不将此定位记录当作运行证明。
- 下方 26 项索引和原章节合同仍保留 `22a89f9` 的固定来源，4.1 图文还含 `8c17b67`；未逐项迁移，不批量替换提交链接。官方版本查询见[总入口](README.md#每次开始前确认源码与官方最新版本)。

## 4.1 单任务导览与回查入口

既有 **4.1 Agent Rollout Adapters and Harnesses** 导览以 `generate()` 的整次任务为主线，现有 01 任务执行与 02 模型/上下文单元共同说明其内部交接。以下材料保留供已读任务链回查，不作为当前必须重读的安排；26 项清单用于定位和扩展。 连续讲解见 [01 单元 walkthrough](chapters/01-task-execution/walkthrough.md)，回顾见 [review](chapters/01-task-execution/review.md)。 调用 Harness 前先读 [Pre-4：启动前准备](chapters/01-task-execution/pre-4-preparation.md)。目录放在 3.5 后、4 前，真实执行仍按准备、启动、模型请求、收尾推进。 Pre-4 已按 Adapter Service、任务信息、会话/默认采样、环境/CLI、工作区/题目逐项展开，并在末尾核对 run 的六个参数和隐含条件。 总览图先汇集五项准备及其成果，再接入 Harness.run。 章节完整存档见 [Pre-4 文件夹](../../slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/Pre-4.启动前准备/README.md)；内部导览可从 [Harness.run 主线](../../slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/4.Launch%20Agent/4.Harness.run调用与职责.md) 进入 [动作5环境能力](../../slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/5.Manage%20Sandbox/README.md)，读清后回到调用处继续。

推荐路径：准备任务、模型入口和会话 → 创建沙箱、准备工作区 → Harness 配置并启动 CLI → CLI 回连 Adapter → 消息转换、模型生成、响应与本轮轨迹 → CLI 继续或结束 → 回到 generate 收集 diff、独立评估、训练轨迹导出与清理。模型请求阶段是 CLI 运行中的嵌套循环，Sandbox 操作贯穿准备、运行与回收。

每步只需走通相关函数的输入、主要行为、输出/副作用与下一次交接；组件展开完就返回主线。先完成正常路径，再补超时、非零退出、空轨迹和失败清理。完成标准是能拿一份具体代码任务连续复述完整闭环，而不是逐行读完全部文件。

## 各 Action 的语境与文件范围

每章局部图后单独说明当前主线、本章职责与返回位置；主要源码文件和入口默认收起。统一划分见 [action-contexts.md](action-contexts.md)，具体文件/符号清单由 [action-contexts.json](action-contexts.json) 维护并生成网页。`generate()` 编排一次样本任务，2 → 3 → 3.5 展开一次模型请求，5、6 展开环境能力及长命令执行机制；它们是嵌套调用和职责划分，不是依编号依次运行的阶段。这里不另建阅读顺序或学习状态。

## 需求对照

[目标需求与阅读单元对照](job-alignment.md) 保存岗位来源、能力映射和待补实践。开始一个单元时选对应需求，再用“模块责任 → 扩展接缝 → 失败情景 → 验证证据”四问检查阅读是否对准目标。具体顺序和学习状态仍由本路线维护。

## 既有材料的固定来源（2026-10-10）

本节保留既有材料的历史来源；本机 checkout 和当前阅读接续以上方记录为准。历史段落中的“本轮”指 2026-10-10 的材料整理，不表示当前会话。

- 本地仓库根目录：`/home/fredkeira/projects/slime`；核心包：`/home/fredkeira/projects/slime/slime/`。`examples/`、`train.py`、`tests/`、`tools/`、`docker/` 也在范围内。
- 本轮核对版本：`22a89f96835969a47055a659c588f46151f8b07a`（本地 HEAD，2026-10-10）。固定源码链接指向这一提交，入口、行号与文件内容核对见 [source-map.json](source-map.json)。
- 已直接查询官方 THUDM/slime main：核对时为 `d06df4d77a1fbcf7bdc48e13071cf649e670133a`，比本地领先 1 次提交，仅改动 CPU CI 和回归测试。本轮保留本地快照；核对命令与状态见 [README](README.md#每次开始前确认源码与官方最新版本)，数据证据见 [upstream-check.json](upstream-check.json)。
- 仓库存在未跟踪的旧阅读记录；本路线保留它们。本轮范围内的源码文件与 Git blob 一致，未修改源码仓库。
- 现有 4.1 动作材料基于 `8c17b676cb57af1d17ee4402e91e9209af84b60b`；旧短课/复用路线使用 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。旧资料辅助定位，具体调用与行号以本轮固定源码为准。
- 新路线只在本 `code-reading/` 目录和网站“源码阅读顺序”页作为当前记录；源码仓库旧 `docs/repo-reading-route.md` 保留原目标与状态，不能混合计入本轮进度。
- 本轮为静态源码定位与路线材料，未运行 Agent、沙箱、模型服务、训练或 Kubernetes；没有用户掌握状态的推断。
- 历史检查报告 `historyTruncated=true`：本轮不做历史成长讲解，也不把最近提交窗口当作全仓历史。

## 快速浏览与深入的分工

从[当前接续](#当前接续)进入。先建立基本工作流，再按当前问题逐步展开；主线遇到已读的 4.1 任务组件时短回顾。进入新组件时先读问题、职责、少量入口和理解检查，函数太长时先列调用与数据交接。材料已展开的范围不等于用户已读、记住或掌握。

00–07 表达职责与依赖，投入重点按[岗位对照](job-alignment.md#当前学习条件与投入安排)调整。01、02 供已读任务链回查，03–05 优先补扩展、验证和稳定性，06、07 先定位资源与训练交接再按需深入。trace、explain、locate 表示目标阅读深度，不是已完成的学习状态。

| 顺序 | 单元 | slime_photo 对照 | 先能说明什么 | 前置 |
| --- | --- | --- | --- | --- |
| 00 | [全局职责与三种运行粒度](chapters/00-overview/README.md) | 1.1、4、7.1 | 先认识各模块做什么、在哪里运行，以及任务、请求、训练的包含关系。 | 无；从这里开始。 |
| 01 | [完整任务、Harness 与执行环境](chapters/01-task-execution/README.md) | 4.1 的动作 4、5、6、7；7.1 | 掌握任务执行的责任划分、环境接口、成功和失败的清理位置。 | 00；已知道任务、请求和训练的区别。 |
| 02 | [模型协议、上下文与训练轨迹](chapters/02-model-context/README.md) | 4.1 的动作 2、3、3.5；补读会话结束 | 掌握模型调用封装、工具消息处理、上下文变化和轨迹导出的接口。 | 01；已连接 CLI 配置、HTTP 路由与任务会话。 |
| 03 | [策略接入、数据生成与评测合同](chapters/03-strategy-evaluation/README.md) | 4.5、3.4、3.3、3.2、3.1；7.5/7.6/7.10 作为对照 | 掌握单样本生成、整批 rollout、评分、hook、过滤和评测配置的区别。 | 00–02；知道 Sample 与一次任务的返回边界。 |
| 04 | [Trace、结果分析、测试与复现](chapters/04-trace-validation/README.md) | 9、8.2、3.5；源码 tests/ 和复现文档 | 掌握 Trace 与日志的区别、结果分析、接口测试、实验配置和可复现性边界。 | 01–03；已能指出执行与评测的关键交接。 |
| 05 | [并发、任务数据、背压与恢复](chapters/05-concurrency-recovery/README.md) | 7.7、4.5、4.6；6.2 为独立服务对照 | 掌握 Asyncio 调度、并发预算、任务队列、传输、持久化、取消和恢复的职责。 | 03、04；知道组级输出合同与验证方式。 |
| 06 | [模型服务、Ray 资源与容器边界](chapters/06-serving-resources/README.md) | 4.3、4.4、2.1；Kubernetes 为独立实践 | 掌握运行位置、服务生命周期和资源治理，能定位 Kubernetes 需要补充的适配。 | 01、05；知道执行环境与并发预算的边界。 |
| 07 | [训练交接、策略版本与权重更新](chapters/07-training-handoff/README.md) | 4.2、5.1、7.8；7.9 与 SFT 作为第二遍 | 掌握生成与训练的工程合同、基本 RL/SFT 区别、checkpoint 与策略版本边界。 | 02、03、05、06；了解 Sample、结果传输与模型服务。 |

## 最终代码阅读清单

这是既有文件/函数索引，依附原有 00–07 单元；当前接续与学习状态只在[当前接续](#当前接续)维护。路径相对于 Slime 仓库根目录，源码链接保留 `22a89f96835969a47055a659c588f46151f8b07a` 的固定来源，不冒充当前 checkout。

**01–26 条目用于回查职责、输入输出、停止点与配套验证，接续位置以上方记录为准。** Trace 与契约测试从当前主线配合使用，配套测试先看 fixture/断言，不把源码阅读当作运行通过。

全局入口为 README 架构段与 `train.main`；4.1 连续导览提供单任务内部调用链，沿用 Claude/Anthropic 图文，Codex/OpenAI 保留为同一职责的实现对照。已经读过的调用链只按本轮问题回查，不作为必须重读的起步。

### 00 全局职责

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 01 · 样本数据合同 | [slime/utils/types.py · Sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/types.py#L107) | 只读主要字段到 SpecInfo 前：任务身份、prompt、tokens、reward、mask、logprob、状态和 Session。 | 先能说明一次任务、一次请求、一份训练样本的区别；完整序列化与所有方法后置。 | [tests/test_sample.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_sample.py#L1) |

### 01 完整任务与环境

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 02 · 一个任务的调用骨架 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | 读完 generate 的准备、Harness、diff、独立评分、训练/评测返回和 finally；boot 重试实现暂不展开。 | 解释 CLI 退出码与 reward 的区别；第二遍追超时、空轨迹和失败。 | [tests/test_agent/test_agent_rollout_cpu.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_agent_rollout_cpu.py#L1) |
| 03 · 可替换的 Agent 启动骨架 | [slime/agent/harness/common.py · BaseHarness.run](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L81)<br>[slime/agent/harness/common.py · run_agent](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L107) | 读 user/config/launch/wait 的交接；安装 Node/npm 的辅助函数先停住。 | 能指出新增 CLI 要实现的步骤；测试 fixture 和调用顺序断言随读。 | [tests/test_agent/test_harness.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_harness.py#L1) |
| 04 · 先选一种 CLI：Codex | [slime/agent/harness/codex.py · CodexHarness.write_config](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/codex.py#L56)<br>[slime/agent/harness/codex.py · CodexHarness.launch_and_wait](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/codex.py#L69) | 看配置模板、模型地址、session 与启动环境；到外部 CLI 边界停止。 | 能把 CLI 配置与 OpenAI Adapter 路由接起来；Claude 分支放在完整链读通后的实现对照。 | [tests/test_agent/test_harness.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_harness.py#L1) |
| 05 · 执行环境和长命令 | [slime/agent/sandbox.py · Sandbox](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L28)<br>[slime/agent/sandbox.py · exec_and_wait](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L82) | 读环境操作合同和等待函数；区分 detached spawn、退出标记、重复调用与等待预算。 | 第二遍展开 E2B RPC、超时和重放；Kubernetes 后端需另外实现与验证。 | [tests/test_agent/test_sandbox_exec_and_wait.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_sandbox_exec_and_wait.py#L1) |
| 06 · 任务产物与独立评分 | [examples/coding_agent_rl/swe.py · git_diff](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L230)<br>[examples/coding_agent_rl/swe.py · run_evaluation](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L239)<br>[examples/coding_agent_rl/swe.py · _grade_scaleswe](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L253) | 选 eval_cmd 评分分支，追 diff 如何在新的评估环境中应用；swepro/SWE-bench 的全部实现后置。 | 说明工作环境和评分环境分别由谁创建与清理；fake 测试不能证明真实 E2B/数据集评分。 | [tests/test_agent/test_agent_rollout_cpu.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_agent_rollout_cpu.py#L1) |

### 02 模型、上下文与轨迹

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 07 · 先选一种模型协议：OpenAI | [slime/agent/adapters/openai.py · OpenAIAdapter._register_routes](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/openai.py#L47)<br>[slime/agent/adapters/openai.py · OpenAIAdapter._translate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/openai.py#L53)<br>[slime/agent/adapters/openai.py · OpenAIAdapter._respond](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/openai.py#L69) | 用一份包含 tool_calls/tool 结果的请求，读路由、翻译和非流式响应；SSE 后置。 | 说明请求直接来自 CLI，协议名不是实际模型供应商；对照 Anthropic 时共享流程不用重读。 | [tests/test_agent/test_adapters.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_adapters.py#L1) |
| 08 · 一轮共享模型处理 | [slime/agent/adapters/common.py · BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L318)<br>[slime/agent/adapters/common.py · call_sglang_generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L442) | 读完两个函数，标出 sid/inflight/rid、模板 token、SGLang /generate、logprob、响应与记录。 | 当前实际顺序为 parse → respond → record_turn；第二遍再读取消与预算分支。 | [tests/test_agent/test_adapters.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_adapters.py#L1) |
| 09 · 输出和工具调用解析 | [slime/agent/parsing.py · parse_model_output](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L25)<br>[slime/agent/parsing.py · parse_tool_uses](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L59) | 读 reasoning/text/tool_uses/ill_formed 的返回形状；外部 parser 内部实现先停住。 | 分清解析工具调用与实际执行工具的责任；配套测试部分依赖 SGLang。 | [tests/test_agent/test_adapters.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_adapters.py#L1) |
| 10 · 上下文记录到训练 Sample | [slime/agent/trajectory.py · TurnRecord](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L29)<br>[slime/agent/trajectory.py · TrajectoryManager.record_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L283)<br>[slime/agent/trajectory.py · TrajectoryManager.get_trajectory](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L307)<br>[slime/agent/trajectory.py · _SampleBuilder.to_sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L234) | 只追一条正常工具多轮链，核对 tokens、mask、logprob 与 reward 的导出。 | 每个输出 Sample 当前赋完整 reward；第二遍选一种分叉/压缩/token drift，不通读全部消息树辅助实现。 | [tests/test_agent/test_trajectory_manager_branching.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_trajectory_manager_branching.py#L1) |
| 11 · 会话完成、导出与清理 | [slime/agent/adapters/common.py · BaseAdapter.finish_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L245)<br>[slime/agent/adapters/common.py · BaseAdapter.drop_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L278)<br>[slime/agent/adapters/common.py · BaseAdapter.shutdown_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L225) | 看在途请求等待、样本导出/解码与 cleanup-only；线程 drain 细节留到并发问题。 | 能区分本轮 HTTP 请求结束、Session 结束与任务结束。 | [tests/test_agent/test_agent_rollout_cpu.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_agent_rollout_cpu.py#L1) |

### 03 策略与评测接入

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 12 · 策略如何接回生成流水线 | [slime/rollout/sglang_rollout.py · generate_and_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L289)<br>[slime/rollout/sglang_rollout.py · generate_and_rm_group](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L384)<br>[slime/rollout/base_types.py · call_rollout_fn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/base_types.py#L28) | 定位 custom generate → hook → RM，组级并发/评分，以及整批 rollout 包装的不同返回合同。 | 说明单样本扩展和替换整批 rollout 的区别；queue identity 继承细节留到 22。 | [tests/plugin_contracts/test_plugin_generate_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_generate_contracts.py#L1)<br>[tests/plugin_contracts/test_plugin_rollout_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_rollout_contracts.py#L1) |
| 13 · 可替换评分器 | [slime/rollout/rm_hub/__init__.py · async_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/rm_hub/__init__.py#L55)<br>[slime/rollout/rm_hub/__init__.py · batched_async_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/rm_hub/__init__.py#L99) | 读分发顺序和单样本/批次函数签名；数学 grader 与远端重试后置。 | 能说明新增评分器与组级评分怎样接入。 | [tests/plugin_contracts/test_plugin_path_loading_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_path_loading_contracts.py#L1) |
| 14 · 样本处理与 hook | [slime/rollout/sample_hooks.py · apply_rollout_sample_hooks](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sample_hooks.py#L52)<br>[slime/rollout/sample_hooks.py · _apply_to_sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sample_hooks.py#L37) | 读 sync/async、Sample/None、嵌套形状和 rollout_id 上下文；批次过滤的确认过程后置。 | 能指出错误返回、样本扇出与身份保持需要哪些断言。 | [tests/test_rollout_sample_hooks.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_rollout_sample_hooks.py#L1) |
| 15 · 评测配置与实际消费 | [slime/utils/eval_config.py · EvalDatasetConfig](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/eval_config.py#L135)<br>[slime/utils/eval_config.py · build_eval_dataset_configs](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/eval_config.py#L265)<br>[slime/rollout/sglang_rollout.py · eval_rollout_single_dataset](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L616) | 配置后立即对照 runner：样本注入、sampling 和 rewards/truncated/samples 返回合同。 | 当前默认 runner 未消费 eval_task_timeout、early-stop、app_service 字段；配置合并测试不能证明运行时能力生效。 | [tests/test_eval_config.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_eval_config.py#L1) |
| 16 · 另一种策略：Multi-Agent | [examples/multi_agent/rollout_with_multi_agents.py · generate_with_multi_agents](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/multi_agent/rollout_with_multi_agents.py#L16)<br>[examples/multi_agent/agent_system.py · run_agent_system](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/multi_agent/agent_system.py#L198) | 画 solver → rewriter → selector 和早退，定位 _emit 如何统一兄弟样本 rollout_id。 | 对照 Coding Agent，确认通用接入合同；prompt、模型生成与奖励缩放细节第二遍再读。 | [tests/plugin_contracts/test_plugin_generate_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_generate_contracts.py#L1) |

### 04 Trace、验证与复现

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 17 · Trace 与真实埋点位置 | [slime/observability/trace_utils.py · bind_trace](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L238)<br>[slime/observability/trace_utils.py · trace_span](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L345)<br>[slime/observability/trace_utils.py · trace_function](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L451) | 先看身份、父子 span、耗时和错误，再回 sglang_rollout 的真实调用点；此步的思想也用于 02–16 的测试。 | 第二遍看 export/import 与重试关联；Coding Agent/CLI/环境/评分的端到端传播仍需补覆盖和验证。 | [tests/observability/test_trace_utils.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/observability/test_trace_utils.py#L1) |
| 18 · 结果分析与实验复现 | [tools/trace_timeline_viewer.py · _build_items_from_trace](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tools/trace_timeline_viewer.py#L245)<br>[tools/trace_timeline_viewer.py · _build_cache_data](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tools/trace_timeline_viewer.py#L572)<br>[tools/trace_timeline_viewer.py · main](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tools/trace_timeline_viewer.py#L2359)<br>[slime/observability/metric_utils.py · compute_pass_rate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/metric_utils.py#L14)<br>[docs/zh/advanced/reproducibility.md](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/docs/zh/advanced/reproducibility.md#L1) | 只读 Trace 到离线时间线的输入/缓存/入口，以及 pass@k 的分组假设；不通读 Viewer。 | 保存代码/模型/tokenizer/数据/采样/依赖/资源配置；固定 seed 不保证所有实现行为完全一致。 | [tests/observability/test_trace_utils.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/observability/test_trace_utils.py#L1) |

### 05 并发、队列与恢复

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 19 · 并发上限与请求节奏 | [slime/rollout/sglang_rollout.py · GenerateState.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L89)<br>[slime/utils/async_utils.py · AsyncPacer](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/async_utils.py#L8)<br>[slime/rollout/sglang_rollout.py · generate_rollout_async](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L476) | 先辨认 semaphore、pacer 和 FIRST_COMPLETED 收集/补任务；abort 与过滤分支第二遍追。 | 说明并发上限、启动节奏、线程事件循环和任务取消的不同职责。 | [tests/test_fully_async_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_fully_async_rollout.py#L1) |
| 20 · 持续生成：先看分支，再读本地池 | [slime/rollout/fully_async_rollout.py · _get_worker](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_rollout.py#L54)<br>[slime/rollout/fully_async_rollout.py · AsyncRolloutWorker._loop](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_rollout.py#L173)<br>[slime/rollout/fully_async_rollout.py · AsyncRolloutWorker.pause](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_rollout.py#L109) | 看本地 worker 的 active pool、完成队列、ABORTED 重入与暂停；reader_config 分支接下一步。 | 本地输出 queue 无界，背压由补任务条件承担；不能写成有界输出队列。 | [tests/test_fully_async_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_fully_async_rollout.py#L1) |
| 21 · 持久化模式：分布式生成池 | [slime/rollout/fully_async_distributed.py · DistributedRollout.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L474)<br>[slime/rollout/fully_async_distributed.py · RolloutScheduler._run](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L98)<br>[slime/rollout/fully_async_distributed.py · RolloutScheduler.generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L161)<br>[slime/rollout/fully_async_distributed.py · _GenerationActor._produce](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L319) | 从 _get_worker 的 reader_config 分支进入，辨认每节点 worker、局部 pool、输出队列与全局 demand/prefetch。 | 第二遍追 pause、worker 失败与结果恢复；只读本地 AsyncRolloutWorker 不覆盖这条主链。 | [tests/test_distributed_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_distributed_rollout.py#L1) |
| 22 · 任务租约、结果引用与确认 | [slime/data/queue_data_source.py · QueueReader.get_samples](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L1068)<br>[slime/data/queue_data_source.py · RolloutQueueController.take](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L488)<br>[slime/data/queue_data_source.py · RolloutQueueController.complete](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L563)<br>[slime/data/transport.py · pack_rollout_group](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/transport.py#L259)<br>[slime/data/transport.py · accept_raw_rollout](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/transport.py#L431) | 只追 task → lease → result_ref → receipt → accepted；QueueDataSource 主要是 reader/checkpoint 包装。 | 第二遍再读 heartbeat/add_samples、ready_batch/finish_batch 与 save/load；外部 straw/WAL 保证另行核对。 | [tests/test_distributed_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_distributed_rollout.py#L1)<br>[tests/test_straw_fully_async_recovery.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_straw_fully_async_recovery.py#L1) |

### 06 服务、资源与部署

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 23 · 服务和资源的真正拥有者 | [slime/ray/placement_group.py · create_placement_groups](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/placement_group.py#L123)<br>[slime/ray/serving.py · ServingCluster.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L38)<br>[slime/backends/sglang_utils/deployment.py · start_rollout_servers](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/deployment.py#L79)<br>[slime/backends/sglang_utils/external.py · discover_external_engines](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/external.py#L95) | 画 PG、router、Ray engine actor 和 HTTP 模型进程的运行位置，定位它们的创建者。 | 当前服务所有者在 ray/serving.py；第二遍读 engine_group/sglang_engine 与容器；Kubernetes 并行实践。 | [tests/test_placement_group.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_placement_group.py#L1)<br>[tests/test_external_sglang_engines.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_external_sglang_engines.py#L1) |
| 24 · 健康、恢复与退出策略 | [slime/ray/serving.py · ServingCluster.finish_rollout](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L280)<br>[slime/ray/serving.py · ServingCluster.recover_updatable_engines](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L256)<br>[slime/ray/serving.py · ServingCluster.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L294)<br>[slime/ray/rollout.py · RolloutManager.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L160)<br>[slime/utils/health_monitor.py · RolloutHealthMonitor.check_once](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/health_monitor.py#L126)<br>[slime/utils/cleanup.py · Cleanup](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/cleanup.py#L9) | 区分 rollout 结束、故障引擎退役、更新前恢复、训练失败保留 serving 和成功完整回收。 | RolloutManager 只清理自己拥有的资源；第二遍沿 health checks、engine recover/shutdown；部分测试启动 CPU Ray。 | [tests/test_rollout_manager_recovery.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_rollout_manager_recovery.py#L1) |

### 07 训练交接

| 顺序 | 阅读入口 | 第一遍读到这里 | 第二遍与边界 | 配套验证材料（先读） |
| --- | --- | --- | --- | --- |
| 25 · 生成数据怎样进入训练 | [train.py · main](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L103)<br>[train.py · train](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L13)<br>[slime/data/batch_builder.py · BatchBuilder.convert](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/batch_builder.py#L237)<br>[slime/backends/megatron_utils/actor.py · MegatronTrainRayActor._get_rollout_data](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L222)<br>[slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.train_actor](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L449) | 只追 tokens/mask/reward/rollout_log_probs 到 advantage 与 train；主循环第一遍可在全局地图中先扫角色。 | 第二遍选 compute_advantages_and_returns、policy_loss_function 或 sft_loss_function；不从 loss.py 开头逐行读。 | [tests/test_process_rollout_data.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_process_rollout_data.py#L1)<br>[tests/test_policy_loss.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_policy_loss.py#L1) |
| 26 · 数据完成、共同 checkpoint 与权重发布 | [slime/data/batch_builder.py · BatchBuilder.training_completed](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/batch_builder.py#L144)<br>[slime/data/checkpoint.py · save_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L39)<br>[slime/data/checkpoint.py · commit_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L77)<br>[slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.update_weights](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L628)<br>[slime/backends/megatron_utils/update_weight/__init__.py · create_weight_updater](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/update_weight/__init__.py#L10) | 接回 train 的 admission pause/update/resume，区分 accepted、training completed、checkpoint committed 与模型版本。 | 第二遍只按实际配置选一种权重 updater 与恢复路径；数值校正、全部传输后端和训练并行后置。 | [tests/test_rollout_straw_transport.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_rollout_straw_transport.py#L1)<br>[tests/test_megatron_checkpoint.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_megatron_checkpoint.py#L1)<br>[tests/test_update_weight_factory.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_update_weight_factory.py#L1) |

### 实现对照与后置范围

首条 CLI/协议链读通后，比较 ClaudeCodeHarness 的 write_config/launch_and_wait 与 AnthropicAdapter 的路由/_translate/_respond；共享处理与轨迹流程不用重读。

Search-R1、Tau-bench 和独立 Rollout Buffer 作为策略/环境/服务对照；模型结构、MLA、量化内核、NPU/GB10、全部 Megatron 并行实现和所有权重传输后端按实际需求后置。Kubernetes、外部 CLI 工具循环、端到端 Trace 和吞吐/恢复/训练实验需要独立实践，不能只靠阅读数量证明。

当前证据：文件、符号、行号与本地 Git blob 已静态核对；配套测试在本轮只作为阅读材料，未执行源码仓库的测试、模型服务、Ray、训练或 Kubernetes。

## 仓库覆盖与缺口

这里记录计划覆盖范围。源码入口经过静态核对，00 的职责地图与 01 的完整任务主线有展开讲解；01 也串联 02 的请求与轨迹职责，仍不表示所有分支或用户掌握状态已确认。

| 领域 | 主要代码/材料 | 对应单元 | 预期覆盖 | 后续或外部缺口 |
| --- | --- | --- | --- | --- |
| Agent 组件 | `slime/agent/`、`examples/coding_agent_rl/` | 01、02 | 启动、模型协议、环境、上下文、轨迹、任务与评分 | CLI 内部工具循环、任意外部模型客户端 |
| 策略与评测 | `slime/rollout/`、`utils/eval_config.py`、多轮示例 | 03 | custom generate、RM、hook、过滤、数据集、结果合同 | 其他环境/策略按问题选读；不是所有示例已审计 |
| Trace、测试与复现 | `slime/observability/`、`tools/`、`tests/`、CI 与复现文档 | 04 | Trace 合同、真实埋点覆盖检查、日志、指标、回放、契约与 fake 测试 | 端到端埋点、GPU/模型/集群实测与实验管理实践 |
| 数据、并发与恢复 | `slime/data/`、`fully_async_rollout.py`、`utils/cleanup.py` | 05、07 | 缓冲、队列、传输、取消、背压、恢复与共同 checkpoint | straw-queue、共享存储等外部实现和故障实验 |
| 模型服务与调度 | `backends/sglang_utils/`、`slime/ray/serving.py`、`slime/ray/rollout.py`、`utils/health_monitor.py` | 06、07 | 部署、发现、资源布局、健康、服务所有权与权重更新 | SGLang 服务内部、所有部署拓扑与容量调优 |
| 容器与 Kubernetes | `docker/`、`scripts/`、Sandbox 合同 | 06 + 独立实践 | 定位构建依赖，定义环境操作和集群适配边界 | 本版本未定位到原生 Kubernetes 沙箱后端或集群 controller；需实际集群经验 |
| 训练与算法 | `train.py`、`backends/megatron_utils/`、SFT/校正示例 | 07 | 数据消费、基本 SFT/RL、策略版本、checkpoint 与权重发布 | 并行训练细节、全部算法推导和数值实验 |
| 独立 Rollout Buffer 与其他插件 | `slime_plugins/rollout_buffer/`、模型插件 | 05 对照；其余后置 | 区分独立 HTTP buffer、TrajectoryManager、主链数据队列 | 模型结构/算子/平台插件的具体实现 |
| 项目维护与跨语言 | README、`docs/`、`.github/`、`scripts/`、`docker/` | 00 定位，04/06 按需 | 配置、测试入口、启动与发布材料职责 | TypeScript/Rust/Go 协作与 AI 工具经验需独立项目材料 |

这条路线支持理解需求到接口、数据、验证和运行边界的映射。实际部署、算法协作、性能治理和 owner 经验还需要任务实践与可观察结果，不能由阅读文件数量代替。

## 第 0 章 全局职责与三种运行粒度

**目录 ID：** `00-overview`
**产物状态：** ready
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 一次任务、一次模型请求和一次训练迭代，分别由哪些模块组织？

**前置：** 无；从这里开始。

**图文对照：** 1.1、4、7.1。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 训练与生成总入口 | [train.py · main](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L103) | locate | 只定位启动、资源准备和训练循环；训练算法留到 07。 |
| 任务数据合同 | [slime/utils/types.py · Sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/types.py#L107) | locate | 先辨认 prompt、reward、token、mask、状态和身份字段；字段转换在 02、03、07 展开。 |
| 分布式生成与评测入口 | [slime/ray/rollout.py · RolloutManager](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L36) | locate | 类的角色与 generate/eval 入口；资源治理留到 06。 |
| 一个代码任务的组装 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | locate | 只读调用骨架；执行和清理在 01 展开。 |

**章内顺序：**

1. 从本章 walkthrough 的基本工作流建立最小整体模型，先分清任务数据、生成评分、样本批次、训练和权重返回。
2. 以“谁启动并进入循环”为第一个展开问题，沿 train.main() 的真实交接定位服务准备与 train()；每步保留整体轮廓，第一遍不钻损失公式。
3. 到生成数据的交接再看 Sample 的主要字段；区分任务、请求和训练样本，具体字段按问题展开。
4. 主线进入具体 Agent 任务时，再定位 generate() 的 prepare → Harness → diff → evaluation → finish_session → finally；已读部分短提醒后返回调用方。

**验收问题：** 解释 agent/、rollout/、data/、ray/、backends/ 的职责，并指出工具循环、Kubernetes 和 tokenizer 实现的外部边界。

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 1 章 完整任务、Harness 与执行环境

**目录 ID：** `01-task-execution`
**产物状态：** ready
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 代码任务怎样启动 CLI、让 CLI 回连模型入口、收集补丁、独立评分并释放资源？

**前置：** 00；已知道任务、请求和训练的区别。

**图文对照：** 4.1 的动作 4、5、6、7；7.1。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 任务生命周期 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | trace | 分别追踪训练与 evaluation 分支；不是通用的独立任务平台。 |
| 调用方的模型入口准备 | [_AdapterService.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L138)（examples/coding_agent_rl/generate.py） | trace | 细读 tokenizer/解析配置、Adapter 内部状态、HTTP 线程、监听/回连地址和进程复用；返回调用方继续任务、Session、环境和题目准备。 |
| 启动骨架 | [slime/agent/harness/common.py · BaseHarness.run](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L81) | trace | 配置和 CLI 启动可替换；CLI 内部工具循环在外部软件包。 |
| 沙箱操作合同 | [slime/agent/sandbox.py · Sandbox](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L28) | trace | 当前实现为 E2B；Kubernetes 后端需独立实现和验证操作语义。 |
| 长命令等待 | [slime/agent/sandbox.py · exec_and_wait](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L82) | explain | 区分等待超时、进程退出和外层环境回收，不能假设返回超时就已杀死进程。 |
| 补丁的独立评估 | [examples/coding_agent_rl/swe.py · run_evaluation](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L239) | trace | 评分环境与 Agent 工作环境分开；继续定位 _grade_scaleswe/_grade_swebench。 |

**章内顺序：**

1. 先读 generate()，记录创建者、持有者、收集者和清理者。
2. 依次读 Harness.run、Sandbox 操作合同、exec_and_wait；再定位 Claude/Codex Harness 的模型地址和会话身份配置。
3. 补读 4.1 的动作 7 Make API Calls，接到 BaseAdapter._run_turn 的 HTTP 入口；模型处理留到 02。
4. 回到 swe.git_diff 和 run_evaluation，辨认工作环境退出后在新评估环境应用补丁并运行测试。
5. 沿超时、CLI 非零退出、空轨迹、评分失败和 finally 追踪结果与清理；用 tests/test_agent 中的 fake 测试理解可验证边界。

**验收问题：** 如果换 Agent CLI 或沙箱后端，分别修改哪层？CLI 的退出码为什么不等于任务 reward？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 2 章 模型协议、上下文与训练轨迹

**目录 ID：** `02-model-context`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** CLI 的模型请求如何进入共享流程，返回协议响应，并留下可用于训练的真实轨迹？

**前置：** 01；已连接 CLI 配置、HTTP 路由与任务会话。

**图文对照：** 4.1 的动作 2、3、3.5；补读会话结束。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 共享模型请求流程 | [slime/agent/adapters/common.py · BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L318) | trace | 协议转换、模板编码、模型生成、解析、响应与轨迹记录；具体协议见旁边 openai.py/anthropic.py。 |
| 实际模型调用 | [slime/agent/adapters/common.py · call_sglang_generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L442) | trace | 原生 SGLang /generate；协议兼容不表示已经支持任意云 API。 |
| 输出与工具解析 | [slime/agent/parsing.py · parse_model_output](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L25) | trace | 解析工具调用不等于执行工具；执行者是 CLI 或其他自定义 Agent。 |
| 会话轨迹与上下文分支 | [slime/agent/trajectory.py · TrajectoryManager](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L269) | trace | 第一遍看 record_turn/get_trajectory；token drift、分叉、mask 细节作为第二遍 explain 范围。 |
| 会话结束与训练样本导出 | [slime/agent/adapters/common.py · BaseAdapter.finish_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L245) | trace | 区分当前 HTTP 请求结束、会话关闭、Sample 导出和 cleanup-only drop_session。 |

**章内顺序：**

1. 取一份带工具的请求，沿 7 → 2 → 3 → 3.5 画输入输出。
2. 分别定位 OpenAI/Anthropic 路由、_translate、_respond；确认实际生成端是 SGLang。
3. 从 TurnRecord 到 record_turn，再到 finish_session/get_trajectory，核对 token、logprob、mask 与 reward 的来源。
4. 第二遍只选择一种上下文变化：追加工具结果、上下文压缩或分支；用 test_trajectory_manager_branching 理解行为。

**已确认的第二遍细分（2026-10-11）：** `generate()`／`_run_turn()` 主线之后，进入 [Trajectory Management 专题阅读入口](<../4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/Trajectory Management/README.md>)。每轮只展开一个机制：① `record_turn()` 的历史接续与分叉；② `_try_merge_assistant_rewrite()` 的改写合并；③ `get_trajectory()` 的 token 对齐、共享前缀去重和 Sample 导出。入口已建立，不表示用户已完成这些阅读单元。

**验收问题：** 一轮协议响应和一份训练 Sample 有什么关系？为什么仅保存最终文本无法还原生成时的全部训练信息？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 3 章 策略接入、数据生成与评测合同

**目录 ID：** `03-strategy-evaluation`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 新增 Agent 策略、评分器、数据集或样本处理逻辑时，应该接在哪个扩展点？

**前置：** 00–02；知道 Sample 与一次任务的返回边界。

**图文对照：** 4.5、3.4、3.3、3.2、3.1；7.5/7.6/7.10 作为对照。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 单样本生成与评分组合 | [slime/rollout/sglang_rollout.py · generate_and_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L289) | trace | custom generate、异步等待、样本 hook 和 group_rm 分支；自定义函数可能扇出多个 Sample。 |
| 整批 rollout 返回合同 | [slime/rollout/base_types.py · call_rollout_fn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/base_types.py#L28) | trace | 训练/评估输出不同；本版本支持数据引用，不能只记成 Python Sample 列表。 |
| 可替换评分器 | [slime/rollout/rm_hub/__init__.py · async_rm](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/rm_hub/__init__.py#L55) | trace | 按样本、全局路径或远端评分分发；分组评分另看 batched_async_rm。 |
| 评测数据与参数 | [slime/utils/eval_config.py · EvalDatasetConfig](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/eval_config.py#L135) | trace | 先核对 eval_rollout_single_dataset 实际消费字段和结果合同；类中 timeout/early-stop/app_service 字段不能直接当作默认 runner 已实现的行为。 |
| 样本处理扩展点 | [slime/rollout/sample_hooks.py · apply_rollout_sample_hooks](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sample_hooks.py#L52) | trace | 同步/异步 hook 与样本身份传递；动态过滤和批次 hook 有不同位置。 |

**章内顺序：**

1. 标出 --custom-generate-function-path、--custom-rm-path、--data-source-path 和 --rollout-function-path 的不同作用范围。
2. 追踪 generate_and_rm 的生成、Sample 上下文继承、hook、奖励和返回；看 generate_and_rm_group 的组级处理。
3. 读 EvalDatasetConfig 与 eval_rollout_single_dataset，画一次固定数据集评测的结果合同。
4. 选 Search-R1 或 multi_agent 的入口，与 Coding Agent 对照如何替换单样本生成；Tau-bench 作为后续环境适配例子。
5. 读 tests/plugin_contracts 与 test_rollout_sample_hooks，列出新策略需要维持的输入、输出、身份和错误约定。

**验收问题：** 新增搜索工具策略和新增评分方法分别改哪里？什么时候需要替换整个 rollout？过滤样本后身份与完成确认由谁处理？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 4 章 Trace、结果分析、测试与复现

**目录 ID：** `04-trace-validation`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 怎样把模型、工具、环境和评分的失败或延迟关联起来，并用测试与配置验证修改？

**前置：** 01–03；已能指出执行与评测的关键交接。

**图文对照：** 9、8.2、3.5；源码 tests/ 和复现文档。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 事件与 span 的组织 | [slime/observability/trace_utils.py · trace_span](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/trace_utils.py#L345) | trace | 自定义格式与跨边界 carrier；工具存在不表示所有示例已接好完整埋点。 |
| 实验日志与配置 | [slime/observability/logging_utils.py · configure_logger](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/logging_utils.py#L12) | locate | 继续读 init_tracking/finish_tracking；日志、指标与任务 Trace 分别定位。 |
| 正确率与结果统计 | [slime/observability/metric_utils.py · compute_pass_rate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/observability/metric_utils.py#L14) | trace | 按题目分组和评分假设影响 pass@k 的解释。 |
| 轨迹时间线查看器 | [tools/trace_timeline_viewer.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tools/trace_timeline_viewer.py#L1) | locate | 输入适配、span 展示、离线分析；不当作现成的全链路在线监控。 |
| 扩展接口行为测试 | [tests/plugin_contracts/test_plugin_generate_contracts.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/plugin_contracts/test_plugin_generate_contracts.py#L1) | locate | 先读 fixture 与断言；测试未经本轮执行，不标为通过。 |

**章内顺序：**

1. 从 trace_span/trace_event 到 export_trace/import_trace，画父子 span 与跨进程关联。
2. 取一个评分失败或模型请求变慢的情景，决定应该记录的身份、阶段、尝试次数、耗时和错误。
3. 选 test_adapters、test_sandbox_exec_and_wait、test_eval_config 和 plugin_contracts，说明它们实际验证什么。
4. 读 docs/zh/advanced/reproducibility.md，记录代码 SHA、模型/tokenizer、数据集、采样、依赖和资源配置；固定随机种子不等于所有后端完全一致。
5. 第二遍再实践一项 fake 驱动的失败注入；需要模型或集群的验证另行准备环境。

**验收问题：** 一次任务失败，日志、Trace、样本状态和评分结果各回答什么？复现实验需要保存哪些配置与产物？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 5 章 并发、任务数据、背压与恢复

**目录 ID：** `05-concurrency-recovery`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 怎样持续处理慢任务、控制积压，并在取消、重启和部分失败后保持结果与任务身份一致？

**前置：** 03、04；知道组级输出合同与验证方式。

**图文对照：** 7.7、4.5、4.6；6.2 为独立服务对照。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 持续运行的生成工作者 | [slime/rollout/fully_async_rollout.py · AsyncRolloutWorker](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_rollout.py#L78) | explain | 本地池的任务、完成队列与暂停；先读 _get_worker 分支，持久化 reader_config 模式还需 DistributedRollout。 |
| 批次生成与取消 | [slime/rollout/sglang_rollout.py · generate_rollout_async](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sglang_rollout.py#L476) | trace | 区分线程中的事件循环、进程/Ray 调度和服务端生成请求的取消。 |
| 持久化分布式生成 | [slime/rollout/fully_async_distributed.py · DistributedRollout.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L474) | trace | 从 _get_worker 的 reader_config 分支进入；每节点 worker、局部池、全局 demand/prefetch 与 worker 恢复。 |
| 任务领取与确认 | [slime/data/queue_data_source.py · QueueReader.get_samples](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L1068)、[slime/data/queue_data_source.py · RolloutQueueController.take](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L488)、[slime/data/queue_data_source.py · RolloutQueueController.complete](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L563) | trace | task、lease、result_ref 与 receipt；结果 accepted、训练 completed、checkpoint committed 分开理解。 |
| 任务数据源 | [slime/data/queue_data_source.py · QueueDataSource](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/queue_data_source.py#L1292) | trace | 这是 job-level reader/checkpoint 包装；具体租约与确认在 QueueReader/RolloutQueueController，外部 straw 语义另行核对。 |
| 结果打包与共享存储 | [slime/data/transport.py · pack_rollout_payload](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/transport.py#L350) | trace | Ray object-store 与 straw 数据引用两种路径；完成确认、接受批次和持久化 checkpoint 不等价。 |
| 共同清理预算 | [slime/utils/cleanup.py · Cleanup](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/cleanup.py#L9) | explain | 每项清理使用剩余时间；清理工具不是通用强制中断器。 |
| 恢复计划 | [slime/data/checkpoint.py · resolve_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L237) | locate | 先辨认数据进度与模型/优化器状态的共同恢复边界，再看恢复实现。 |

**章内顺序：**

1. 先看 GenerateState.semaphore、generation_pacer 与 _get_worker；再比较本地 AsyncRolloutWorker 和持久化 DistributedRollout 两条任务池，解释并发上限、启动节奏和各自的队列背压。
2. 追一个正常组、一个 ABORTED 组和一个超时请求；记录排队、重入、结果接受和资源释放。
3. 对照 data_source.py、QueueReader、RolloutQueueController 与 transport.py；区分 prompt buffer、租约、持久化结果、批次接受和训练消费确认。
4. 读 tests/test_fully_async_rollout.py 和恢复测试，提出慢任务、满队列、取消、服务重启与重复结果的行为验证。
5. 第二遍对照 slime_plugins/rollout_buffer/README.md：它是独立 HTTP Rollout Buffer 服务，不能与 trajectory.py 或主链数据队列混为一谈。

**验收问题：** 暂停生成和取消请求有什么区别？任务完成、结果已收集、训练已消费和 checkpoint 已提交有哪些不同？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 6 章 模型服务、Ray 资源与容器边界

**目录 ID：** `06-serving-resources`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 谁部署模型、分配资源、发现服务、检查健康、处理故障，并回收任务与推理资源？

**前置：** 01、05；知道执行环境与并发预算的边界。

**图文对照：** 4.3、4.4、2.1；Kubernetes 为独立实践。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 分布式资源布局 | [slime/ray/placement_group.py · create_placement_groups](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/placement_group.py#L123) | trace | Ray placement group 与 GPU 布局；不是 Kubernetes Pod 或集群调度器。 |
| 推理部署组装 | [slime/backends/sglang_utils/deployment.py · start_rollout_servers](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/deployment.py#L79) | trace | 配置、router、engine group 和服务进程；模型内部算子后置。 |
| 外部模型服务发现 | [slime/backends/sglang_utils/external.py · discover_external_engines](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/sglang_utils/external.py#L95) | trace | 外部 SGLang 引擎信息与控制接口，不等同于任意 Chat Completions API。 |
| 模型服务所有权 | [slime/ray/serving.py · ServingCluster.__init__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L38)、[slime/ray/serving.py · ServingCluster.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/serving.py#L294) | trace | 服务与队列可以跨训练尝试保留；失败、detach、正常成功退出的政策不同。 |
| 生成服务管理与清理 | [slime/ray/rollout.py · RolloutManager.dispose](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L160) | trace | 借用 ray/serving.py 中 ServingCluster 的模型服务，dispose 只清理自有资源；服务完整回收另由所有者负责。 |
| 容器构建参考 | [docker/Dockerfile](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/docker/Dockerfile#L1) | locate | 镜像、依赖与补丁；集群控制器、沙箱后端和网络存储仍需独立实践。 |

**章内顺序：**

1. 画运行位置：训练 actor、rollout worker、模型 HTTP 服务、Adapter、Agent CLI 与沙箱。
2. 追 placement group → deployment → engine/router → health/recovery → dispose 的职责交接。
3. 选择一个模型服务不可达或 CLI 无法回连 Adapter 的情景，定位地址、端口、会话、日志与清理者。
4. 另做 Kubernetes 实践：Pod 创建/就绪、资源限制、命令与文件操作、网络回连、日志与结果保存、取消和清理；该任务只是建议，尚未执行。

**验收问题：** Ray、Kubernetes、Sandbox 和模型服务各管理什么？要换 Kubernetes 沙箱，需要满足哪些操作与失败语义？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。

## 第 7 章 训练交接、策略版本与权重更新

**目录 ID：** `07-training-handoff`
**产物状态：** planned
**学习状态：** 统一见[当前接续](#当前接续)。

**问题：** 生成的轨迹怎样被训练消费，更新后的模型怎样继续服务下一轮任务，如何保留一致性？

**前置：** 02、03、05、06；了解 Sample、结果传输与模型服务。

**图文对照：** 4.2、5.1、7.8；7.9 与 SFT 作为第二遍。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 生成、训练、保存与更新主循环 | [train.py · train](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L13) | trace | 第一遍读职责与顺序；Megatron 张量并行和全部算法推导后置。 |
| 模型训练消费 | [slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.train_actor](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L449) | trace | 定位 reward、advantage、logprob、mask 的消费；不能假设所有字段在生成阶段已经算好。 |
| 权重发布 | [slime/backends/megatron_utils/actor.py · MegatronTrainRayActor.update_weights](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/backends/megatron_utils/actor.py#L628) | trace | 暂停/版本/内存或磁盘更新；与 GPU/模型服务生命周期共同理解。 |
| 共同 checkpoint | [slime/data/checkpoint.py · save_checkpoint](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/data/checkpoint.py#L39) | trace | 模型/优化器状态与数据进度共同恢复；仅完成一次训练不等于可恢复 checkpoint。 |
| SFT 样本生成 | [slime/rollout/sft_rollout.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/sft_rollout.py#L1) | locate | 审核后的轨迹可重新编码用于 SFT；需要概率信息的 RL 不能只用最终文本补齐。 |

**章内顺序：**

1. 画 train() 的生成 → 训练 → 数据完成确认 → checkpoint → 暂停与权重更新 → 继续生成。
2. 从 Sample 跟到 actor 的数据读取与 train_actor，说明 tokens、loss_mask、reward、rollout_log_probs 与 advantage 的用途和产生位置。
3. 追一个策略版本跨越生成与训练的情景，分清异步旧策略数据和 SGLang/Megatron 数值不一致两类问题。
4. 第二遍按具体算法读 loss.py 与 examples/train_infer_mismatch_helper/；权重传输细节再读 update_weight/ 与 delta-weight-sync 文档。

**验收问题：** 更换 Agent 策略为什么可能影响训练数据合同？哪些数据必须在生成时保留？异步生成与训练更新如何协调？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](#当前接续)。
