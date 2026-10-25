# 源码阅读与认知记录制度：讨论与待办

本目录承接原 `00-repo-reading/discussions/` 中的全部 14 份讨论、试用步骤和样例。正文及原始来源保留，路径变化涉及的链接已同步调整。

## 当前从哪里继续

最新骨架方法讨论：[Step 010 按业务结果分块并保留关键实参](2026-10-20-task-driven-cognitive-architecture/discussion.md#step010-skeleton-data-handoffs-proposal)。用户反馈精简后仍缺少一层；已回查原有 skill 并保存候选骨架，正式 scope 暂未采用。

最新 scope 审阅：[Step 010 先固定路径，再提取真实调用骨架](2026-10-20-task-driven-cognitive-architecture/discussion.md#step010-core-skeleton-review)。用户反馈原稿看不清主干；本轮按既有 skill 精简为生成选择、等待、后处理、补奖励与返回，其他分支折叠，旧稿归档。

最新主题分组落实：[Slime 采用“主题 → 既有 step”层次](2026-10-20-task-driven-cognitive-architecture/slime-topic-grouping-proposal.md)。用户确认后，Step 000–009 已整体迁入 Coding Agent RL 主题，主入口与源码目录分别标注；编号、记忆继承和唯一路线保留，后续主题实际展开时再建。

最新前后对比：[新版 get_trajectory 更适合作为当前主读入口](2026-10-20-task-driven-cognitive-architecture/discussion.md#get-trajectory-before-after-review)。助手依据对象连续性和信息层次作出判断；完整数值与复杂情景继续按需查阅，尚不把该判断当成学习效果的实测。

最新函数卡落实：[get_trajectory 按单轮例子重排](2026-10-20-task-driven-cognitive-architecture/discussion.md#get-trajectory-card-reorder-applied)。整体交接先可见，三段源码紧接变量变化；完整数值、复杂对照和历史折叠保留，旧稿归档。

最新函数卡方案：[get_trajectory 保留三段主线，调整材料先后](2026-10-20-task-driven-cognitive-architecture/discussion.md#get-trajectory-card-reorder-proposal)。用户反馈对象前置大概理解，认可现有内容质量并要求先看方案；建议沿原单轮例子逐段读，完整数值、分叉与压缩作为后续对照，尚未重排正文。

最新类卡排版：[已展开的用法放在含义右侧](2026-10-20-task-driven-cognitive-architecture/discussion.md#base-adapter-usage-column)。字段定义与使用入口合为同一行，移除独立用法表；“—”只表示本卡尚未归纳，不作为未学习的判断。

最新类卡精简：[保留全字段，压缩重复说明与用法表](2026-10-20-task-driven-cognitive-architecture/discussion.md#base-adapter-card-slimming)。按用户要求先瘦身，字段表改为两列，原话和来源折叠；完整旧稿另存，当前核心疑问仍保留。

最新类卡审阅：[BaseAdapter 的工程准确性与学习可用性](2026-10-20-task-driven-cognitive-architecture/discussion.md#base-adapter-field-card-review)。完整字段总览可以保留；建议补充同一 sid 的状态关系、当前运行场景与精确方法跳转，学习效果需结合实际试读判断。本轮未改类卡正文。

最新类卡落实：[BaseAdapter 全字段总览与渐进用法索引](2026-10-20-task-driven-cognitive-architecture/discussion.md#class-field-memory-applied)。已按用户确认建立 13 个实例字段和 4 个类级配置的浅层总览，实际用法先保留已讨论部分，原话与未知独立记录。

最新类卡方案：[全字段浅层总览，按实际阅读补用法](2026-10-20-task-driven-cognitive-architecture/discussion.md#class-memory-field-overview-and-usage)。用户提出先“点亮”全部字段，再逐次记录使用关系；已核对 BaseAdapter 的字段规模，建议类卡采用独立的字段与用法结构，待试用。

最新类卡讨论：[先建立 BaseAdapter 的基本对象地图](2026-10-20-task-driven-cognitive-architecture/discussion.md#class-memory-object-map-proposal)。区分类与方法的记录对象、短期与长期的形成步骤；建议先接清核心状态、协作对象和方法职责，再继续当前方法，类卡扩充方案尚未实施。

最新记录分工：[BaseAdapter 类卡保存字段定义，方法卡保存具体操作](2026-10-20-task-driven-cognitive-architecture/discussion.md#adapter-state-card-responsibility)。按用户建议在 Step 004 短期记忆中归并 `closed`、`inflight`，并将此前完整复述写入 shutdown_session 的原话区。

最新卡片落实：[shutdown_session 按状态变化与跨循环交接重构](2026-10-20-task-driven-cognitive-architecture/discussion.md#shutdown-state-cross-loop-applied)。主图区分两个循环与函数职责，三段源码与图对应；完整示例、历史复述和扩展未知折叠保留。用户已反馈呈现更清楚，具体机制仍按实际疑问接续。

最新卡片审阅：[shutdown_session 应突出状态变化与跨循环收尾](2026-10-20-task-driven-cognitive-architecture/discussion.md#shutdown-state-cross-loop-review)。用户明确反馈卡片偏长、纯输入输出表达不合适；已找到短期记忆 skill 的跨边界图示与分阶段规则，具体精简仍为本卡的待采用方案。

最新 scope 校准：[Step 004 的整体骨架、输入衔接与局部导航](2026-10-20-task-driven-cognitive-architecture/discussion.md#step-four-scope-core-refresh)。第 3 部分按新版源码整理为三个小节，旧 scope 归档；函数卡片与 task flow 仍待逐项校准。

最新格式落实：[Step 004 的 scope 前两节采用要点并接入新版定位](2026-10-20-task-driven-cognitive-architecture/discussion.md#step-four-scope-intro-bullets)。版本说明置于文末，明确前两节采用 `18868a79` 的入口核对，第 3 部分及函数记录仍待校准。

最新格式落实：[Step 003 的 3.2 收拢为两份输入与一次交接](2026-10-20-task-driven-cognitive-architecture/discussion.md#step-three-input-bridge-compaction)。保留最小 `md` 示例，补清输入准备的时间关系；辅助参数、源码来路和未展开边界合入折叠区。

最新格式落实：[Step 003 的 scope 按同一标准精简](2026-10-20-task-driven-cognitive-architecture/discussion.md#step-three-scope-intro-bullets)。前两节采用要点，保留评分分派与局部编排的区别；完整选读理由默认折叠，版本说明移到文末。

最新格式落实：[Step 002 沿用 Step 001 的要点格式](2026-10-20-task-driven-cognitive-architecture/discussion.md#step-two-scope-intro-bullets)。用户确认具体改稿后，已精简前两节并将版本说明移到文末；本步指挥官按实际编排保留为 `_generate`。

最新格式落实：[Step 001 的 scope 开头改为要点，版本说明移到文末](2026-10-20-task-driven-cognitive-architecture/discussion.md#scope-intro-bullets-and-version-footer)。用户确认先精简“阅读目标”和“指挥官函数”，参考 Step 005–008 的说明密度；本轮只在 Step 001 落实，后续步骤按反馈逐步处理。

最新衔接讨论：[运行时输入与前序认识需要区分](2026-10-20-task-driven-cognitive-architecture/discussion.md#scope-runtime-input-vs-prior-knowledge)。Step 003 的输入来路原先预设过多，已改为先接前两步的内容，再补最小任务字典；暂未涉及的构造保持明确未知。

最新样例落实：[Step 001 与 Step 002 都作为已认可的完整 scope](2026-10-20-task-driven-cognitive-architecture/discussion.md#scope-two-approved-examples)。两份原正文保留，分别完整收录到 skill reference；后续按问题参考主线阅读与输入来源回查的组织方式。

最新落实：[Step 001 的阅读图与执行总结分开维护](2026-10-20-task-driven-cognitive-architecture/discussion.md#step-one-reading-map-applied)。scope 3.4 已在原 12 项导航前补图，task flow 按 `18868a79` 校准执行与交接；旧版全文归档，函数卡片和长期记忆保留。

最新归属落实：[阅读路径图移入 scope](2026-10-20-task-driven-cognitive-architecture/discussion.md#reading-path-moved-to-scope)。用户已确认，图与函数导航现位于 Step 002 的 scope 3.4；task flow 保留执行与结果总结，并从旧入口链接到新位置，04-flow 保存实际形成过程。

此前格式落实：[Step 002 增加阅读路径图，保留执行图](2026-10-20-task-driven-cognitive-architecture/discussion.md#task-flow-reading-path-applied)。用户已确认将“为什么回查、如何返回主线”独立成图，与真实调用关系分别展示；随后按上面的归属确认移入 scope，通用 skill 与其他步骤尚未修改。

最新职责讨论：[函数卡只连接跨函数机制](2026-10-20-task-driven-cognitive-architecture/discussion.md#function-mechanism-note-boundary)。围绕当前输入输出理解函数；统计如何产生与更新集中保存在机制 reference。已在 Step 002 做局部修正，更多机制记录的通用规则仍作为建议。

最新范围调整：[运行统计与补丁提取单独成为新 Step 002](2026-10-20-task-driven-cognitive-architecture/discussion.md#agent-results-separate-step)。用户希望先看清两个调用各自发生什么，评测保持独立；原 Step 002–008 顺延，历史编号与快照的解释见[对照表](../../00-repo-reading/repositories/slime/step-numbering-2026-10-23.md)。

后续专题候选：[Coding Agent 的执行追踪基础设施](2026-10-20-task-driven-cognitive-architecture/discussion.md#trace-infrastructure-topic)。用户提出日后单独阅读 `trace_span`，接入已有 Trace 与验证专题；具体接续以项目唯一路线为准。

最新确认：[Slime 每个 step 都要按新版重新校准](2026-10-20-task-driven-cognitive-architecture/discussion.md#slime-all-steps-recalibration)。覆盖 Step 0–8，核对入口、输入输出、配置与调用关系；已先整理 Step 0，旧版与未迁移的函数记忆保留。

最新落实：[将 Step 007 的调用层级图保存为新 reference](2026-10-20-task-driven-cognitive-architecture/discussion.md#task-flow-hierarchy-reference)。嵌套调用先展示入口的直接部分，再在每个分支下展开子调用、作用与返回；Step 003 继续作为整体四部分结构的主样例。

此前落实：[以 Step 003 为主要 reference 建立 task-flow skill](2026-10-20-task-driven-cognitive-architecture/discussion.md#task-flow-step-three-reference)。已保存完整样例并接入阅读入口，固定位置、交接、结果和收束四部分；本次进一步明确调用层级图的用法。

此前比较：[参考 Step 1–5 的 task flow 格式](2026-10-20-task-driven-cognitive-architecture/discussion.md#task-flow-step-one-to-five-review)。已有成稿形成了“整体总结、位置、交接、结果、收束、来源”的共同结构；当时尚未确定主要 reference，现由上述确认接续。

此前要求：[task flow 需要固定格式](2026-10-20-task-driven-cognitive-architecture/discussion.md#task-flow-fixed-format)。人的总结与稳定格式同时需要；现已按上述样例落实。

最新确认：[本步用到的旧函数也进入短期记忆](2026-10-20-task-driven-cognitive-architecture/discussion.md#reactivate-prior-function-memory)。即使没有新认识，也可从 `03` 调取完整卡片到 `02`，由本步入口直接链接；原快照、来源与认识时间保留。已用 Step 7 的 `ensure_agent_user` 落实并同步现有规则。

最新试用：[确认建立 E2BSandbox 类卡片](2026-10-20-task-driven-cognitive-architecture/discussion.md#e2b-class-card-created)。用户已确认在 Step 005 中独立保存对象状态与操作入口，父函数通过链接复用，已有方法卡保留。成稿待反馈，通用 skill 尚未修改。

此前试用：[确认类卡片方向，以 Session 试用](2026-10-20-task-driven-cognitive-architecture/discussion.md#session-class-card-trial)。Session 的主体说明进入 Step 004 的 `02/classes/`，原 reference 保留导航与语法依据。

当前保留 [Step 0 · Coding Agent 核心骨架](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-000-coding-agent/README.md)与 [Step 1 · Harness 到 Adapter](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/README.md)，旧 `initial-model` 保留在[历史归档](archived-steps/README.md)。最新分工是 Step 0 只看骨架，转换记录归入 Step 1，并从 `_run_turn` 开始逐段读实现；见[本次讨论](2026-10-20-task-driven-cognitive-architecture/discussion.md#step-zero-skeleton-step-one-run-turn)。具体阅读接续仍以[唯一路线](../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准。

已确定需要函数级短期记忆。当前先判断“形成过程”相对短期记忆提供了哪些独有信息、哪些只是重复，再从认知心理学、脑科学、教育学和工程实践的视角讨论各层的职责与抽象。任务主线、函数间连接和长期组合属于这个设计问题的一部分，不先假定需要增加哪些文件或栏目。此前转回 `train.py::main()` 的建议没有回答这次方法问题，保留为历史讨论。

## 已明确的基础

- 每个 step 先一起讨论要读哪个函数、围绕它弄清什么，以及短期 memory 的记录重点，由用户确认后再展开源码和创建函数记录；助手可提出候选及理由，不用已有材料、旧路线或助手建议代替确认。
- 目标是降低认知负载，并让后续阅读能提取和复用已有认识。
- 需要函数级短期记忆；用户认可[当前 common 函数记录样例](../../.agents/skills/repo-reading-memory/references/base-adapter-translate.md)作为格式基础，其中“形成过程”的去留仍在讨论。
- `02` 与 `03` 区别是本步与此前累计，原有单函数记录继续保留。2026-10-22 确认扩展到独立阅读的类，先以 Session 类卡片试用；任务主线仍在步骤层，overview 只做记录索引。
- Step 0 的函数记录放在 `02`，`03` 初始为空；进入下一步时，再把上一份 `03 + 02` 合并到新的 `03`。
- 用户认可长期记忆继承机制：下一步合并前一步的长期与短期记忆，保留内容、未知和来源。
- 本轮是在从零梳理阅读方法，已讲过的固定路线不代替这次制度设计。
- 已建立[独立短期 memory skill](../../.agents/skills/repo-reading-short-term-memory/SKILL.md)，负责本步单函数记录与共用模型引用；[其他 skill 的分工](2026-10-20-task-driven-cognitive-architecture/skill-responsibilities-proposal.md)先保留为建议。

## 制度待定项

- [x] 确认将独立阅读的类纳入正式记忆，以 Session 建立首张类卡；保留与函数卡、场景说明和补充 reference 的分工。
- [ ] 根据 Session 类卡的实际阅读反馈，确认详略并同步通用 skill、模板与继承说明。
- [ ] 检查“形成过程”与短期记忆的重复，判断哪些过程信息值得保留、供什么场合使用，以及是否需要独立保存。
- [ ] 区分内容的抽象层级、短期与长期的积累方式、认识变化的追溯职责，再确定它们怎样组织。
- [ ] 一个步骤怎样按具体问题划界，怎样确定本步起点、终点和停止条件。
- [ ] “本步任务与主线”怎样组织，是否与范围说明放在同一个入口。
- [x] 初始确认两层 memory 均按单函数记录；后续类卡扩展见上项，整体关系仍不另塞入短期或长期 overview。
- [ ] 用户与助手各自负责什么，怎样在不增加额外负担的情况下核对理解。
- [ ] 上述分工确认后，怎样统一 skill、模板和实际步骤；旧步骤如何保留历史状态。
- [x] 先独立短期 memory skill，写入“共同记录已覆盖时直接引用”的规则，并接入原有入口。

以上是待共同决定的事项。归档与保存不表示这些提案已经成为新的执行规则。

## 待执行事项

- [ ] 将已确认的 reference 回填到 [Step 01 的 common 函数记录](step-01-translate-preview/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md)，并修正 [overview](step-01-translate-preview/02-short-term-memory/overview.md) 的一处旧锚点。

用户要求覆盖前先说明方案；此前已提供方案，但尚未获得执行确认。本轮只迁移存放位置和链接，没有用 reference 覆盖原 Step 01 内容。执行时需按归档后的新路径重新核对来源、目标和相对链接。

## 全部讨论与试用材料

| 材料 | 保存的内容 |
| --- | --- |
| [2026-10-19 步骤目录与格式讨论](2026-10-19-step-folder-format.md) | 步骤边界、函数记录、两层记忆、scope 与 flow 分工及历次反馈 |
| [2026-10-19 Skill 重构推演](2026-10-19-skill-refactor-round-01.md) | 用真实转换场景推演记录方法 |
| [2026-10-19 Skill 验证记录](2026-10-19-memory-skill-validation.md) | 既有验证及其边界 |
| [2026-10-20 任务驱动的认知架构](2026-10-20-task-driven-cognitive-architecture/README.md) | 本轮完整问答、认知科学依据、最新澄清与组合方案 |
| [Coding Agent Step 0](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-000-coding-agent/README.md) | 核心骨架与结构讨论，不收录函数分析 |
| [Harness 到 Adapter Step 1](../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/README.md) | `_run_turn` 逐段阅读、转换记录，以及原 Harness 来路与讨论 |
| [旧 initial-model 归档](archived-steps/README.md) | 此前从框架启动切入的方案，已移出当前步骤目录 |
| [转换环节的局部示范](step-00-translate-structure-preview/README.md) | 保留此前误标为 Step 0 的转换样例，供主线走到模型请求时回查 |
| [Step 01 试用步骤](step-01-translate-preview/README.md) | 当时的范围、短期与长期记录、实际讨论和详细参考 |
| [独立 common 样例](base-adapter-translate/BaseAdapter._translate.md) | 本轮逐项调整的函数记录版本 |

通用方法继续从 [00-repo-reading](../../00-repo-reading/README.md) 进入；各项目的实际阅读进度仍由各自既有入口维护。本目录集中保存制度讨论与待办，不另建一套源码阅读进度。
