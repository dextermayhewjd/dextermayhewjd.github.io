# 任务驱动的认知架构：步骤、模块与记忆分工

最新骨架方法讨论：[业务分块与关键实参的对照方案](discussion.md#step010-skeleton-data-handoffs-proposal)。本轮进一步区分减少代码行数与恢复数据交接，保留正式 scope，另存候选写法。

最新 scope 审阅：[Step 010 的真实调用骨架与分支层次](discussion.md#step010-core-skeleton-review)。原稿虽采用三段栏目，但配置、包装和多种返回路径同时进入主干；本轮按既有 skill 固定正常路径，保留连续代码与对应导航。

最新主题分组落实：[Slime 阅读主题与 step 的层次](slime-topic-grouping-proposal.md)。Step 000–009 已归入 Coding Agent RL 主题，以 generate 为入口、agent/ 与 swe.py 为支撑范围；原编号与记忆内容保留。

最新前后对比：[get_trajectory 两版的阅读用途](discussion.md#get-trajectory-before-after-review)。新版优先保持同一对象变化的连续性，完整数值与复杂分支保留为深入时的参考；本轮只评价，未再改稿。

最新函数卡落实：[get_trajectory 的单轮主线与分层对照](discussion.md#get-trajectory-card-reorder-applied)。保留原三段代码和历史内容，先读小树到样本的交接，再按需展开数值与复杂场景。

最新函数卡方案：[get_trajectory 的递进阅读顺序](discussion.md#get-trajectory-card-reorder-proposal)。保留现有三阶段源码与证据，将长数组及复杂分支移到基础主线之后；本轮只保存方案和真实反馈。

最新类卡排版：[字段、含义、已展开的用法同表展示](discussion.md#base-adapter-usage-column)。现有使用关系移到右侧列，减少上下查找；原话、未知与来源继续保留。

最新类卡精简：[BaseAdapter 先压缩查阅负担](discussion.md#base-adapter-card-slimming)。全部字段仍可见，每个字段只留一句含义和必要默认值；已讨论用法合并，原话、未知与历史保持可追溯。

最新类卡审阅：[工程准确性与认知负担](discussion.md#base-adapter-field-card-review)。保留全字段结构，优先补对象与状态的关系、当前场景和精确跳转；区分源码核对通过与学习效果验证。

最新类卡落实：[BaseAdapter 采用全字段总览与用法索引](discussion.md#class-field-memory-applied)。六部分结构已在当前类卡试用，完整列字段、按实际阅读补关系，保留个人原话和未知；通用 skill 尚未改写。

最新类卡方案：[字段先总览，用法随阅读增加](discussion.md#class-memory-field-overview-and-usage)。总览覆盖基类自身字段的内容与基本用途；具体使用只保留关系摘要和方法入口，个人表述与未知另存，尚未将方案写入通用 skill。

最新类卡讨论：[BaseAdapter 先补基本字段与职责地图](discussion.md#class-memory-object-map-proposal)。类卡描述对象持有的状态、协作对象和方法入口；方法卡描述一次调用的过程。当前提出扩充既有类卡的方案，尚未更改学习进度或模板。

最新记录分工：[closed、inflight 的定义归入 BaseAdapter 类卡](discussion.md#adapter-state-card-responsibility)。方法卡继续保留具体状态变化和执行交接；本轮完整原话已保存，版式的正面反馈与机制理解分别记录。

最新卡片落实：[shutdown_session 的跨循环图与三段源码](discussion.md#shutdown-state-cross-loop-applied)。已按用户确认重构当前卡片，保留状态结果、关键边界与完整历史；未改变源码、认识日期或通用 skill。

最新卡片审阅：[shutdown_session 的状态变化与跨循环表达](discussion.md#shutdown-state-cross-loop-review)。记录用户对篇幅和输入输出呈现的反馈；建议应用已有跨边界图示规则，并合并重复讲解，尚未改写卡片或通用 skill。

最新 scope 校准：[Step 004 第 3 部分接入新版源码](discussion.md#step-four-scope-core-refresh)。保留整体位置、三项输入和局部导航，归档旧稿；静态校准与用户的阅读状态分别记录。

最新格式落实：[Step 004 精简前两节并注明部分版本更新](discussion.md#step-four-scope-intro-bullets)。入口采用已有的 `18868a79` 核对，文末保留第 3 部分、函数卡片与 task flow 的旧版归属。

最新格式落实：[Step 003 的输入衔接精简](discussion.md#step-three-input-bridge-compaction)。3.2 围绕 `diff_text`、`md` 和评分入口展开，保留最小字典；辅助信息折叠，输入准备时机在正文说明。

最新格式落实：[Step 003 精简 scope 开头并折叠选读理由](discussion.md#step-three-scope-intro-bullets)。本步指挥官明确为 `_grade_scaleswe`，保留从 `run_evaluation` 分派进入的关系；版本说明集中到文末。

最新格式落实：[Step 002 沿用已确认的 scope 开头格式](discussion.md#step-two-scope-intro-bullets)。前两节各用三点说明目标与入口，版本说明移到文末；本步由 `_generate` 直接组织统计读取与补丁提取。

最新格式落实：[Step 001 的 scope 开头采用要点，版本说明移到文末](discussion.md#scope-intro-bullets-and-version-footer)。前两节分别保留目标、问题、范围与整体位置、局部入口、选择理由；其余步骤继续按后续反馈处理。

最新衔接讨论：[输入存在不等于已经讲清](discussion.md#scope-runtime-input-vs-prior-knowledge)。Step 003 先对照前两步实际涉及的内容，再补本步最小输入模型；源码来路与暂未展开部分分别处理，原 skill 和认可样例保留。

最新样例落实：[Step 001、Step 002 并列作为完整 scope reference](discussion.md#scope-two-approved-examples)。用户认可两份现有 scope；原正文保留，skill 分别提供主线阅读与回查输入来源的参考入口。

最新落实：[Step 001 的阅读图与执行总结](discussion.md#step-one-reading-map-applied)。scope 3.4 保留原 12 项表格并补充阅读图；task flow 按 `18868a79` 的执行关系和数据交接整理，旧版全文独立保存。函数卡片、长期记忆及通用 skill 未随之改写。

最新归属落实：[阅读路径图已移入 scope](discussion.md#reading-path-moved-to-scope)。用户确认后，图与函数导航已合并到 Step 002 的 scope 3.4；task flow 保留执行图并引用导航，实际阅读历史留在 04-flow，通用 skill 未修改。

此前格式落实：[Step 002 同时展示阅读路径与执行关系](discussion.md#task-flow-reading-path-applied)。最初将两图放在 task flow，随后按上面的归属确认将阅读图移入 scope，通用 skill 与其他步骤尚未修改。[原始讨论](discussion.md#task-flow-reading-path-review)保留方案由来。

最新职责讨论：[函数卡与跨函数机制分开](discussion.md#function-mechanism-note-boundary)。`collect_metrics` 保留本次调用的输入输出，统计的初始化与运行中更新移入机制 reference；用户已知 hook，当前聚焦本项目中的协作关系。未增加新的 memory 类型或改写 skill。

最新范围调整：[结果收集独立成步](discussion.md#agent-results-separate-step)。新 Step 002 按 `collect_metrics → git_diff` 看清每项输入、行为与输出，评测顺延为 Step 003；历史编号和快照保留其语境。

后续专题候选：[执行追踪基础设施](discussion.md#trace-infrastructure-topic)。保存用户对 `trace_span` 的独立阅读建议，沿一次 Coding Agent 任务理解记录、关联与导出；尚未开启新的 step。

最新确认：[Step 0–8 都要重新校准](discussion.md#slime-all-steps-recalibration)。已保存全体短期卡片盘点，并先校准 Step 0、归档其旧版；逐步正文校准与用户理解反馈分开，当前接续见唯一路线。

最新讨论：[Slime 更新后如何校准既有理解](discussion.md#slime-version-update-impact)。已完成旧版 `2f231865` 与当前 `18868a79` 的静态比较；建议保留各步职责与旧记忆，先校准整体入口，再按影响补读。具体迁移尚待用户选择。

最新落实：[Step 007 作为调用层级的新 reference](discussion.md#task-flow-hierarchy-reference)。已将认可的完整 task flow 单独保存；入口的直接部分、内部子调用和逐层返回应在主图中看清。Step 003 继续负责整体四部分结构，分支数量与深度按具体源码确定。

此前落实：[Step 003 作为 task flow 的主要 reference](discussion.md#task-flow-step-three-reference)。已建立 [repo-reading-task-flow](../../../.agents/skills/repo-reading-task-flow/SKILL.md)，单独保留完整样例并接入已有阅读技能；旧步骤与学习进度保持原状。

此前比较：[从 Step 1–5 提取 task flow 共同格式](discussion.md#task-flow-step-one-to-five-review)。建议保留开头整体总结、四部分正文与折叠来源，以 Step 3 为主样例，Step 4、5 补状态和生命周期变体；本次随后落实主要 reference，既有成稿保留。

此前要求：[task flow 由人形成总结，同时需要固定格式](discussion.md#task-flow-fixed-format)。已确认需要稳定格式；其后的四部分安排与图示选择已随主要 reference 写入 skill。

最新确认：[本步用到的旧函数也进入短期记忆](discussion.md#reactivate-prior-function-memory)。`02` 收录本步正在使用的新旧记录，`03` 保留累计快照；以 Step 7 的 `ensure_agent_user` 落实调取与直接导航，纯调取不改变认识时间。

最新试用：[确认建立 E2BSandbox 类卡片](discussion.md#e2b-class-card-created)。用户已确认沿用 Session 的方式，在 Step 005 中独立保存对象状态与操作入口；父函数引用类卡，进入、退出复用已有记录。成稿待反馈，通用 skill 未改。[此前分工建议](discussion.md#e2b-object-card-boundary)保留。

最新落实：[scope skill 增加局部导航分支](discussion.md#scope-local-navigation-branch)。用户已要求将分支写入现有 skill；新增“整体位置 → 局部骨架 → 阅读导航”的条件分支，并单独保存 [reference](../../../.agents/skills/repo-reading-scope/references/local-call-context.md)。整体概览与简单调用保留相应的精简方式，既有学习步骤未改写。

此前 scope 复核：[暂不填写函数卡片，仍需保留局部阅读地图](discussion.md#scope-map-without-function-cards)。Step 005 初稿遗漏本步局部骨架与导航，已按前几步的结构补齐；该轮只修改当前材料，随后由上述确认接续到 skill。

最新试用：[确认类卡片方向，以 Session 试用](discussion.md#session-class-card-trial)。用户已要求生成卡片；Step 004 的 `02/classes/` 现保存 [Session 类卡片](../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md)，原 reference 保留入口与语法依据。当前成稿待反馈，通用 skill 与旧快照未改写。

此前讨论：[源码中的类与 reference 怎样分工](discussion.md#class-memory-vs-reference)。用户指出 Session 是实际定义的 dataclass，不应仅因它不是函数就归为补充参考；由此提出区分类型定义、场景变量和补充材料的方案。

最新落实：[输入背景参照 Step 003 分开说明](discussion.md#split-input-references)。Step 4 的 base_sample、protocol、md、instance_id 各有独立 reference，session_id 复用已有说明；原合并页改为目录。此前[集中速查的讨论](discussion.md#shared-input-reference)保留为历史，本次未修改通用 skill。

此前建议：[scope skill 小幅修改，增加条件分支与示例](discussion.md#scope-skill-context-branch-proposal)。当时提出按对象或输入是否清楚选择展开方式；当前分支已落实，reference 采用启动沙箱为主例，并保留 Adapter 来源不清楚时的变体。

最新落实：[局部骨架接出对象来源和方法调用](discussion.md#scope-adapter-method-bridge)。Step 004 已按用户反馈，从 `generate` 中的服务状态与 Adapter 来源接到执行编号和 `open_session`；函数实现继续放在原卡片。使用已有 scope skill，本稿尚未作为新的通用 reference。

最新问题：[进入函数前，先恢复调用对象与参数的含义](discussion.md#function-entry-object-context)。用户指出 `open_session` 的 Adapter 与 session_id 背景仍不清楚；建议先看调用现场、最小来源，再进入函数体。当前只保存讨论，尚未将完整初始化加入范围或重排既有卡片。

最新范围纠正：[完整骨架定位与本步展开分开](discussion.md#scope-whole-skeleton-local-question)。Step 004 沿用 Step 001–003 的组织方式，继承完整骨架，仅展开用户明确的 `open_session`；相邻的沙箱和工作区准备保留为后续位置。此次纠正沿用既有 scope 规则，不要求所有 step 都只能含一个函数。

最新确认：[将 sid 与 inflight 分开解释](discussion.md#split-shared-state-explanations)。先建立执行编号的含义，再理解按编号登记请求；两份材料仍位于本步 references，函数卡片分别引用，旧链接保留为导航。此次确认只调整当前材料，未新增通用记忆类型或修改 skill。

最新问题：[sid 与 inflight 这样的共享状态怎样回查](discussion.md#shared-state-memory)。用户在理解函数步骤时仍不清楚所操作对象的含义；本轮在当前函数输入前补最小定义，并沿用 `references` 保存独立状态说明。尚未另立通用概念记忆类型或修改 skill。

最新讨论：[单张函数卡片需要讲清哪一层](discussion.md#trajectory-card-depth)。以 Step 3 的 `get_trajectory` 为例，区分函数自身的完整模型、被调用者的具体算法与跨函数的完整例子；沿用既有拆分规则，当前应用建议待反馈，尚未据此新建子卡或改写 skill。

最新纠正：[阅读路径与记录归属分开](discussion.md#aexit-function-record-ownership)。已独立展开的 `E2BSandbox.__aexit__` 按函数定义位置保存，`_grade_scaleswe` 只保留退出时机、结果交接和链接；这是应用既有规则的纠错，不是按函数长度新增拆分标准。

最新落实：[在 ensure_agent_user 输入旁说明协议](discussion.md#protocol-context-in-function-card)。新卡片保留单函数格式，协议作为参数背景，语言依据进入既有参考；`exec` 暂停在接口。此前[名称与收录边界讨论](discussion.md#sandbox-memory-entry-boundary)保留，提前准备的下游卡片继续标为待阅读。

最新调整：[补回 aenter 输入到输出的关键解释](discussion.md#aenter-balanced-explanation)。用户反馈上一版过于精简，本轮对照认可样例，补回具体中间数据、关键代码与分条说明；Sandbox 基础和完整语法讲解仍留在参考。此前的[精简记录](discussion.md#aenter-compact-model-implemented)与[分工依据](discussion.md#aenter-compact-model-boundaries)保留。

最新确认：[将 _run_turn 保存为锚点函数 reference](discussion.md#run-turn-anchor-reference)。用户已认可当前卡片，现已完整复制到短期记忆 skill 的[独立参考](../../../.agents/skills/repo-reading-short-term-memory/references/base-adapter-run-turn.md)，并在 [skill](../../../.agents/skills/repo-reading-short-term-memory/SKILL.md#锚点函数的组织方式)中记录适用条件、组织格式与职责边界；原步骤卡片和基础 `_translate` 样例保留。

此前格式统一：[将同类解释统一为分条形式](discussion.md#run-turn-uniform-explanations)。在[第二段已认可的版式](discussion.md#run-turn-explanation-bullets)基础上，同步第一、第三段为“代码块 → 分条逻辑说明 → 子函数跳转表”；折叠操作说明和职责边界也已分条。代码与表格内容保留，其他函数卡片及 scope、task flow 未改。

此前落实：[_run_turn 的函数模型与局部跳转](discussion.md#run-turn-function-model-implemented)。用户要求按[已明确的分工](discussion.md#function-model-before-task-summary)生成卡片；已保留原栏目重写整体输入输出和内部三段处理，各子函数链接交代进入理由与返回位置。scope 当时只增加函数卡片入口，task flow 主体保留；卡片随后经本次确认保存为锚点函数 reference。此前[收窄审阅范围](discussion.md#run-turn-review-focus)的约定继续保留；[早先审阅](discussion.md#run-turn-card-critical-review)中将函数内部流程全面交给 task flow 的建议不再作为改稿方向。

此前补充：[给出响应外观，并确定当前需要理解到哪里](discussion.md#respond-shape-and-reading-depth)。用户初步理解为将已有内容组织成可传输的响应，要求一个简短示意；已放在父卡的[字段对应表](discussion.md#respond-input-output-fields)之后，保留[此前的响应对象说明](discussion.md#respond-output-object)。[四张函数卡片的拆分](discussion.md#respond-split-implemented)保持，内部实现仍放在各自记录中，尚未升级为 skill reference。[本次分工依据](discussion.md#respond-tree-and-function-boundaries)与[此前内部实现补充](discussion.md#respond-internal-mechanism)继续保留。

最新格式纠正：[为什么短期函数记录偏离认可样例](discussion.md#short-term-template-drift)。当前成稿以 BaseAdapter._translate 为准；精简文字时保留栏目、任务场景和调用模式。

日期：2026-10-20。围绕“降低认知负载、复用已读代码的理解”，继续梳理阅读步骤、函数记录、短期与长期记忆，以及用户和助手的责任边界。

## 接续入口

- [当前 Coding Agent Step 1](../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/README.md)：保留 Harness 到 Adapter 的来路，当前逐段阅读 `_run_turn`；[Step 0](../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-000-coding-agent/README.md)只保留整体骨架。最新分工见[本次调整](discussion.md#step-zero-skeleton-step-one-run-turn)。
- [目录范围的最新纠正](discussion.md#keep-coding-agent-archive-initial-model)：保留 Coding Agent 与 Harness 到 Adapter 两步，只将旧 `initial-model` 移至[历史归档](../archived-steps/README.md)。
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

当前进入 [Step 1 的 `_run_turn` 逐段阅读](../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md)。Step 0 只保留整体骨架，原转换记录移入 Step 1 的 `02`，`03` 暂无前序函数继承。已有 Harness 和 HTTP 来路留作回查，不因这次调整推断用户已理解内部机制。

[每轮主题确认的最新规则](discussion.md#每轮-step-先确认主题)保存本次明确要求。

[最新的入口纠正](discussion.md#纠正起点从-coding-agent-任务开始)记录本轮修正；[此前转换示范](discussion.md#把职责方案做成完整步骤示范)与[1.3 和短期记忆的比较](discussion.md#比较讲解稿与短期记忆)保留历史依据。

[具体职责方案](responsibilities-proposal.md)保留为讨论历史，其中 overview 保存组合关系的建议已被纠正；其余未确认部分仍是草案。

[最新追问与方案说明](discussion.md#具体化职责划分任务模型与学习记录)保留本轮上下文；[此前的问题界定](discussion.md#再次明确讨论主线形成过程与分层职责)与[模块组合方案](discussion.md#澄清从零设计步骤及模块组合)继续作为讨论材料。[此前转向 main 的建议](discussion.md#如何继续读源码的初步建议)保留为讨论历史，用户已经指出它没有回答本轮的方法问题。
