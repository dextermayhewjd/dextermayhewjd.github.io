# 任务驱动的认知架构：步骤、模块与记忆分工

日期：2026-10-20。围绕“降低认知负载、复用已读代码的理解”，继续梳理阅读步骤、函数记录、短期与长期记忆，以及用户和助手的责任边界。

## 接续入口

- [当前 Coding Agent Step 1](../../../00-repo-reading/repositories/slime/steps/step-001-harness-to-adapter/README.md)：用户已明确追问从 Harness 到 Adapter 的连接；[Step 0](../../../00-repo-reading/repositories/slime/steps/step-000-coding-agent/README.md)保留前序核心骨架。
- [转换环节局部示范](../step-00-translate-structure-preview/README.md)：此前误标为 Step 0，保留为任务内部的参考。
- [职责划分建议](responsibilities-proposal.md)：将阅读导航、知识模型和学习记录映射到具体文件，并用同一个函数例子说明边界；当前为讨论草案。
- [完整讨论与研究依据](discussion.md)：保留用户表述、此前的职责讨论，以及本轮任务驱动架构的完整问答。
- [已认可的 common 函数记录样例](../../../.agents/skills/repo-reading-memory/references/base-adapter-translate.md)：本轮讨论的具体基础。
- [记忆格式总入口](../../../00-repo-reading/memory-format.md)：保留既有规范与历史讨论入口。
- [按两条指南重新设计阅读步骤](guide-based-redesign.md)：最新讨论稿，保留目录和函数记忆，调整步骤主线、记录分工与后续 skill 边界。
- [本步 scope 明确为三项](discussion.md#本步-scope-明确为三项)：用户确认以理解 Coding Agent 为目标，定位 `generate` 并提取核心骨架。
- [独立短期 memory skill](../../../.agents/skills/repo-reading-short-term-memory/SKILL.md)：本步函数记录与共用模型引用规则；[其余 skill 分工建议](skill-responsibilities-proposal.md)待逐项确认。
- [独立 scope skill](../../../.agents/skills/repo-reading-scope/SKILL.md)：阅读目标、指挥官函数与核心骨架；附详细剪枝方法和已确认 scope 样例。
- [独立阅读顺序 skill](../../../.agents/skills/repo-reading-order/SKILL.md)：已有骨架后的入口推荐；附用户原文、最小前置方法与 Harness 推荐实例。
- [怎样记录读懂实现的过程](../../../00-repo-reading/code-reading-guide.md#从函数作用继续读懂实现记录一次具体追踪)：用四项记录保存问题、代码证据、解释与下一处未知，并附实际地址传递样例。
- [当前 Step 还需要补什么](discussion.md#当前-step-还需要补什么)：先讨论本步任务、整体位置、交接与停止位置；当前为助手评估，尚未确定新的阅读范围。
- [起步时未知模块的导航图](discussion.md#起步时还不知道模块导航图怎样逐步建立)：用户认可缩进导航的形式；逐步增加节点和标记未知的做法仍是待讨论建议。
- [怎样判断先读哪个函数](discussion.md#怎样判断先读-run-还是消息转换)：先由助手定位接口与必要前置，再围绕当前问题提出函数和阅读深度的候选。
- [借鉴资深工程师的读法](discussion.md#借鉴资深工程师的函数阅读方式)：先建立输入输出、状态与正常路径模型，再按问题查看细节和测试；区分工程评审的完整责任与本步学习范围。
- [理解 Coding Agent 整体时优先看哪些函数](discussion.md#回到整体目标优先看哪些函数)：任务编排、CLI 启动、模型请求、结果评估与轨迹导出；整体导览与局部细读分开。

## 已明确的基础

1. `02` 保存本步单个函数的记录，`03` 保存此前累计的同格式函数记录；overview 只做索引。用户认可当前 common 函数记录作为格式基础，“形成过程”的去留仍在讨论。
2. 用户认可既有长期记忆继承机制：下一步的 `03` 合并前一步的 `03` 与 `02`，保留认识、未知和来源。
3. 设计目标是降低认知负载，并让后续阅读能提取、复用已有模块认识。
4. 用户要求将本轮讨论独立保存，并在仓库规则中加入接续阅读入口。
5. 用户澄清，本轮讨论的是从零构建“每一步怎样阅读、怎样记录和组合模块”的方法，使用 `_translate`、`_render_token_ids`、`call_sglang_generate` 作为具体例子；此前固定路线上的已讲内容不替代这次方法讨论。
6. 每个 step 先一起讨论要读哪个函数、围绕它弄清什么，以及短期 memory 的记录重点，由用户确认后再展开源码和建立函数记录；不要求预先给出答案，只确认 Coding Agent 方向也不代表已经选择 `generate`。
7. 当前 `_translate` 场景由 common 记录统一说明；Anthropic 文件直接引用它，保留实现定位与原始来源，不另写重复的输入输出和心智模型。
8. 本轮先独立短期 memory skill，其余职责只列分工建议；不一次建立全部候选 skill。
9. 随后用户进一步要求将当前 scope 读法独立为 `repo-reading-scope`，包括指挥官识别、五类过滤与 reference；长期继承和完整步骤编排未因此整体拆分。
10. 用户继续要求将先看核心动作、再回查前置的推荐方法独立为 `repo-reading-order`。推荐围绕当前问题，不固定所有任务都先看 Harness，也不将推荐记成已经开始下一步。

## 尚在讨论的方案

当前首先讨论“形成过程”相对短期记忆是否有独有用途。用户指出两者重复性很高，希望结合认知心理学、脑科学、教育学和资深工程师的视角，明确整个系统的分层与抽象。

任务主线与本步范围放在步骤层，帮助定位和控制展开深度。两层 memory 都保留单函数记录；过程与额外证据供需要时回查。此前“把整体关系保存在 memory overview”的建议已被用户纠正。

上述架构建议尚未逐项确认。函数记录是否取消独立的“形成过程”、哪些引用集中到来源区、步骤按问题怎样划界，以及双方具体分工，都保留为待讨论项。保存讨论不表示这些提案已写入 skill 或模板，也不增加源码学习的掌握状态。

## 下一次从哪里继续

当前进入[从 Harness 启动到 Adapter 收到请求](../../../00-repo-reading/repositories/slime/steps/step-001-harness-to-adapter/README.md)，先澄清启动、外部 CLI 与 HTTP 回连这一项关系。Step 0 保留当时快照，其转换记录已完整继承到 Step 1 的 `03`。后续是否继续展开地址配置、路由或请求处理，根据用户实际反馈共同确定。

[每轮主题确认的最新规则](discussion.md#每轮-step-先确认主题)保存本次明确要求。

[最新的入口纠正](discussion.md#纠正起点从-coding-agent-任务开始)记录本轮修正；[此前转换示范](discussion.md#把职责方案做成完整步骤示范)与[1.3 和短期记忆的比较](discussion.md#比较讲解稿与短期记忆)保留历史依据。

[具体职责方案](responsibilities-proposal.md)保留为讨论历史，其中 overview 保存组合关系的建议已被纠正；其余未确认部分仍是草案。

[最新追问与方案说明](discussion.md#具体化职责划分任务模型与学习记录)保留本轮上下文；[此前的问题界定](discussion.md#再次明确讨论主线形成过程与分层职责)与[模块组合方案](discussion.md#澄清从零设计步骤及模块组合)继续作为讨论材料。[此前转向 main 的建议](discussion.md#如何继续读源码的初步建议)保留为讨论历史，用户已经指出它没有回答本轮的方法问题。
