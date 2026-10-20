# 源码阅读与认知记录制度：讨论与待办

本目录承接原 `00-repo-reading/discussions/` 中的全部 14 份讨论、试用步骤和样例。正文及原始来源保留，路径变化涉及的链接已同步调整。

## 当前从哪里继续

先看[Step 0 · Coding Agent 阅读准备](../../00-repo-reading/repositories/slime/steps/step-000-coding-agent/README.md)，再接续[最新讨论入口](2026-10-20-task-driven-cognitive-architecture/README.md)。方向已确定为 Coding Agent，但下一轮具体问题与函数范围仍需用户确认；提前生成的 `generate` 记录已删除。

已确定需要函数级短期记忆。当前先判断“形成过程”相对短期记忆提供了哪些独有信息、哪些只是重复，再从认知心理学、脑科学、教育学和工程实践的视角讨论各层的职责与抽象。任务主线、函数间连接和长期组合属于这个设计问题的一部分，不先假定需要增加哪些文件或栏目。此前转回 `train.py::main()` 的建议没有回答这次方法问题，保留为历史讨论。

## 已明确的基础

- 每个 step 先一起讨论要读哪个函数、围绕它弄清什么，以及短期 memory 的记录重点，由用户确认后再展开源码和创建函数记录；助手可提出候选及理由，不用已有材料、旧路线或助手建议代替确认。
- 目标是降低认知负载，并让后续阅读能提取和复用已有认识。
- 需要函数级短期记忆；用户认可[当前 common 函数记录样例](../../.agents/skills/repo-reading-memory/references/base-adapter-translate.md)作为格式基础，其中“形成过程”的去留仍在讨论。
- `02` 与 `03` 的记录单位相同，都是单个函数；区别是本步与此前累计。任务主线在步骤层，overview 只做函数索引。
- Step 0 的函数记录放在 `02`，`03` 初始为空；进入下一步时，再把上一份 `03 + 02` 合并到新的 `03`。
- 用户认可长期记忆继承机制：下一步合并前一步的长期与短期记忆，保留内容、未知和来源。
- 本轮是在从零梳理阅读方法，已讲过的固定路线不代替这次制度设计。
- 已建立[独立短期 memory skill](../../.agents/skills/repo-reading-short-term-memory/SKILL.md)，负责本步单函数记录与共用模型引用；[其他 skill 的分工](2026-10-20-task-driven-cognitive-architecture/skill-responsibilities-proposal.md)先保留为建议。

## 制度待定项

- [ ] 检查“形成过程”与短期记忆的重复，判断哪些过程信息值得保留、供什么场合使用，以及是否需要独立保存。
- [ ] 区分内容的抽象层级、短期与长期的积累方式、认识变化的追溯职责，再确定它们怎样组织。
- [ ] 一个步骤怎样按具体问题划界，怎样确定本步起点、终点和停止条件。
- [ ] “本步任务与主线”怎样组织，是否与范围说明放在同一个入口。
- [x] 明确两层 memory 均按单函数记录；整体关系不另塞入短期或长期 overview。
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
| [当前 Coding Agent Step 0](../../00-repo-reading/repositories/slime/steps/step-000-coding-agent/README.md) | 已有转换记录与结构讨论；下一轮具体主题等待用户确认 |
| [转换环节的局部示范](step-00-translate-structure-preview/README.md) | 保留此前误标为 Step 0 的转换样例，供主线走到模型请求时回查 |
| [Step 01 试用步骤](step-01-translate-preview/README.md) | 当时的范围、短期与长期记录、实际讨论和详细参考 |
| [独立 common 样例](base-adapter-translate/BaseAdapter._translate.md) | 本轮逐项调整的函数记录版本 |

通用方法继续从 [00-repo-reading](../../00-repo-reading/README.md) 进入；各项目的实际阅读进度仍由各自既有入口维护。本目录集中保存制度讨论与待办，不另建一套源码阅读进度。
