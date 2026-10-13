---
title: "S07 Skills：从最小示例学习技能编写"
weight: 70
description: "从 roll-dice 的最小完整文件开始，每次用一个具体问题、一次小改写和一组检查理解技能编写。"
---

先写出一份可以使用的 Skill，再学习从真实经验中提炼方法，判断哪些内容值得保留。主线以 [Agent Skills Home](https://agentskills.io/home)、[Quickstart](https://agentskills.io/skill-creation/quickstart) 和 [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices) 为依据，按小单元逐步展开。

## 当前学习单元

| 章节 | 这一节只解决什么 |
|---|---|
| [S07.1 Minimal Skill：写出一份最小完整技能]({{< relref "01-structure.md" >}}) | 用官网 roll-dice 例子认识名称、描述和正文；提供中英版本及一次调用 |
| [S07.2 Real Expertise：把有效做法写成可复用技能]({{< relref "02-real-expertise.md" >}}) | 从真实任务和项目资料中提炼方法，理解 SOP 怎样写成 Skill |
| [S07.3 Content Selection：哪些内容值得写进 Skill]({{< relref "03-content-selection.md" >}}) | 对照两份完整文件，判断哪些解释留给读者、哪些指令需要交给 Agent |
| [S07.4 Task Scope：一份 Skill 应该负责多大的任务]({{< relref "04-task-scope.md" >}}) | 从交付结果出发，对照范围过宽、过窄与合适的工作单元 |
| [S07.5 Calibrating Control：每一步需要多大自由度]({{< relref "05-control-calibration.md" >}}) | 按脆弱程度调整约束，给出默认方案，写成可复用流程 |
| [S07.6 有效指导的模式：按问题选择解决方案]({{< relref "06-instruction-patterns/_index.md" >}}) | 分六个独立页面，用问题、解决方案、最小示例和检查方式学习各模式 |
| [S07.7 References：怎样组织和引用配套资料]({{< relref "07-references.md" >}}) | 对照官方多文件示例，写清相对链接、资料用途、读取条件和检查方式 |

每个写作单元先提出具体问题，再用实际材料和完整文件解释；涉及改写时对照修改前后，最后给出检查方式。示意的预期与实际运行记录分别标注。

## 接下来怎样细分学习单元

官网的一个小标题可以拆成几个学习问题。每个小节以能完成一次判断或一次修改为尺度，尽量沿用同一个例子，检查这次改动带来了什么变化。

已展开的 [7.3 内容取舍]({{< relref "03-content-selection.md" >}}) 分成四步：

| 小节 | 只回答什么 | 这一小步做什么 |
|---|---|---|
| 7.3.1 | 为什么要对 Skill 正文做取舍？ | 理解正文进入上下文后，要与当前任务的其他信息一起使用 |
| 7.3.2 | 哪些信息必须告诉 Agent？ | 找出必须保留的执行要求、工具约定与理解缺口 |
| 7.3.3 | 哪些解释可以留在教程里？ | 对照两份完整的 roll-dice 文件，删去无关背景 |
| 7.3.4 | 删减后怎样确认任务仍能完成？ | 用相同请求检查执行记录和结果，决定是否补回信息 |

[7.4 任务范围]({{< relref "04-task-scope.md" >}}) 接着沿用 7.2 的小节编写示例：

| 小节 | 只回答什么 | 这一小步做什么 |
|---|---|---|
| 7.4.1 | 做到哪里算完成？ | 写清输入、交付结果与完成条件 |
| 7.4.2 | 哪些职责已经超出这个任务？ | 找出范围过宽的完整示例中额外加入的目标 |
| 7.4.3 | 哪些步骤不必单独拆成 Skill？ | 检查拆分是否割裂了一个共同的交付 |
| 7.4.4 | 怎样把边界写回文件？ | 收窄描述，明确范围与完成条件，再检查不同请求 |
| 7.4.5 | 怎样判断范围是否合适？ | 用交付、步骤关联、独立用途与复用性逐项检查 |
| 7.4.6 | 怎样验证描述是否匹配？ | 用应触发与不应触发的相近请求，记录实际加载情况 |
| 7.4.7 | 加载之后真的有帮助吗？ | 比较有无 Skill 的结果，以具体证据判断完成质量 |

每次只改变当前要观察的部分。一个主题学完后，再进入下一个主题；后续章节号与正文随实际学习进展确定。

## 先校准每一步的控制程度

[7.5 Calibrating Control]({{< relref "05-control-calibration.md" >}}) 衔接任务范围与执行机制：7.4 确定这份 Skill 负责什么，7.5 进一步判断每一步应该给 Agent 多大自由度。对应官网的 [Calibrating control](https://agentskills.io/skill-creation/best-practices#calibrating-control)。

原文强调按任务的脆弱程度调整指令的具体程度：允许多种正确做法时，说明目标和理由；操作依赖固定顺序或一致性时，把要求写具体。同一份 Skill 的不同部分也应分别判断。

| 学习小节 | 对应原文主题 | 本站写作任务中的例子 |
|---|---|---|
| 7.5.1 哪些操作要规定具体，哪些可以保留判断空间 | [Match specificity to fragility](https://agentskills.io/skill-creation/best-practices#match-specificity-to-fragility) | 解释顺序可按读者调整；必须满足的页面检查条件要明确 |
| 7.5.2 多种方法如何确定默认方案与切换条件 | [Provide defaults, not menus](https://agentskills.io/skill-creation/best-practices#provide-defaults-not-menus) | 默认复用项目已有检查命令，需要额外检查时再补充 |
| 7.5.3 如何把一次任务的做法提炼成可复用流程 | [Favor procedures over declarations](https://agentskills.io/skill-creation/best-practices#favor-procedures-over-declarations) | 根据本次资料选择最小示例，而不是要求每个小节都解释 d20 |

这三个例子是将官网原则应用到本站任务的教学说明。7.5 展示官网例子的中文译文，并用完整的 `write-learning-unit` 教学稿串起三个判断。

校准控制程度之后，再选择实现方式：目标和理由帮助 Agent 判断，默认值减少无谓选择，脚本执行需要一致的操作，验证器检查可测量的结果。指令写得严格，仍需区分它是否由实际运行机制执行。

## 7.6 有效指导的模式

7.5 决定每一步需要多大自由度。[7.6]({{< relref "06-instruction-patterns/_index.md" >}}) 按官网 [Patterns for effective instructions](https://agentskills.io/skill-creation/best-practices#patterns-for-effective-instructions) 拆成六个独立页面，每页围绕一个问题展开解决方案。

这一组有六种模式。先指出执行中的问题，再选择能改善它的做法；原文也强调，每份 Skill 按需要采用其中的模式。

| 学习小节 | 针对的问题 | 对应原文 |
|---|---|---|
| [7.6.1 记录容易踩的坑，纠正常见错误假设]({{< relref "06-instruction-patterns/01-gotchas.md" >}}) | Agent 按一般经验做出了不适合本项目的判断 | [Gotchas sections](https://agentskills.io/skill-creation/best-practices#gotchas-sections) |
| [7.6.2 用模板明确产物应有的结构]({{< relref "06-instruction-patterns/02-output-templates.md" >}}) | 同类任务的输出结构不稳定，容易缺项 | [Templates for output format](https://agentskills.io/skill-creation/best-practices#templates-for-output-format) |
| [7.6.3 用检查清单跟踪多步任务]({{< relref "06-instruction-patterns/03-checklists.md" >}}) | 步骤或依赖容易遗漏，完成状态不清楚 | [Checklists for multi-step workflows](https://agentskills.io/skill-creation/best-practices#checklists-for-multi-step-workflows) |
| [7.6.4 验证结果，失败后修正并重试]({{< relref "06-instruction-patterns/04-validation-loops.md" >}}) | 做完之后缺少检查，错误直接进入交付 | [Validation loops](https://agentskills.io/skill-creation/best-practices#validation-loops) |
| [7.6.5 执行前先验证计划]({{< relref "06-instruction-patterns/05-plan-validation.md" >}}) | 错误计划一旦执行，就会产生不必要的修改或副作用 | [Plan-validate-execute](https://agentskills.io/skill-creation/best-practices#plan-validate-execute) |
| [7.6.6 把重复操作封装成可复用脚本]({{< relref "06-instruction-patterns/06-scripts.md" >}}) | 每次任务都重新编写同一段解析、生成或检查逻辑 | [Bundling reusable scripts](https://agentskills.io/skill-creation/best-practices#bundling-reusable-scripts) |

六种模式可以相互配合。例如，易错点提醒字段别名，模板规定输出结构，清单跟踪步骤，验证器检查结果；批量操作先验证计划，重复的检查逻辑再提取为脚本。这个配合关系是教学组织方式，不是所有任务都必须执行的固定顺序。

每个页面都包含问题、解决方案、完整最小示例和检查方式。验证循环与脚本页面记录了隔离练习中的实际运行结果；计划验证明确区分官网流程示意与尚未提供的工具实现。脚本部分结合 [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts) 学习输入、输出、错误信息和调用方式。

需要区分：易错点、模板和清单帮助 Agent 遵循约定；可执行验证器检查它覆盖的条件；脚本封装固定逻辑。仅写下“验证通过后继续”仍需要 Agent 遵循，要强制执行检查与放行，就需要宿主程序落实控制。

[Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills) 用来比较整份 Skill 的效果；这里的模式帮助改进单次任务的处理过程，两者相互补充。

## 7.7 主文件与配套资料

[7.7 References]({{< relref "07-references.md" >}}) 从官网的 `SKILL.md`、`reference.md`、`examples.md` 多文件示例开始，区分正文、参考资料、模板与脚本，再用已有 `review-diff` 练习展示完整拆分。

这一单元依次解释文件放在哪里、相对链接怎样写、何时读取、哪些内容应留在主文件，以及怎样用实际读取记录检查结果。参考文件可以放在主文件旁边，也可以放进 `references/`；配套文件仍属于同一份 Skill。

## Best practices 有多少个学习点

按原文小标题统计，有 **15 个细分主题**；另有独立的 **Refine with real execution**。合起来是 **16 个学习点**。真实执行后的改进会贯穿每个单元，不必等全部主题读完才开始。

下面按学习任务组织这些主题。表内的问题可以各自形成一个小节，不要求一次完成一整组。“实际执行后改进”从最小 Skill 开始贯穿学习过程。

<details>
<summary>展开后续学习地图：按问题逐步拆分</summary>

| 学习阶段 | 按小节逐个回答的问题 | 对应原文 |
|---|---|---|
| 方法的来源 · 已展开 7.2 | 怎样从一次具体要求提炼复用规则？怎样从项目资料补充依据？ | Extract from a hands-on task；Synthesize from existing project artifacts |
| 正文的取舍 · 已细分 7.3.1–7.3.4 | 为什么要取舍？必须保留什么？哪些解释可以省去？删减后怎样验证？ | Add what the agent lacks, omit what it knows |
| 任务的范围 · 已细分 7.4.1–7.4.7 | 一个任务怎样才算完成？哪些步骤共同完成这个任务？何时范围过宽，何时拆得过碎？怎样用实际请求验证？ | Design coherent units；补充描述与结果评估指南 |
| 指令的详细程度 | 一步需要写多细？哪些解释有帮助，哪些细节会带来无关工作？ | Aim for moderate detail |
| 每一步的控制程度 · 已展开 7.5 | 哪些操作必须严格执行，哪些保留判断空间？多种方法如何选默认值？怎样把一次答案改成可复用过程？ | Calibrating control：Match specificity to fragility；Provide defaults, not menus；Favor procedures over declarations |
| 根据执行改进 · 贯穿各单元 | 怎样选择试用任务？执行记录暴露了什么问题？怎样记录具体易错点（7.6.1）？修改后怎样复查，并保留已有效的部分？ | Refine with real execution；Gotchas sections |
| 输出与多步工作的检查 · 已展开 7.6.2–7.6.5 | 怎样用模板固定输出？怎样用清单避免漏步？验证失败后怎样修正重试？哪些任务需要先验证计划再执行？ | Templates for output format；Checklists for multi-step workflows；Validation loops；Plan-validate-execute |
| 内容与重复操作的拆分 · 已展开 7.7、7.6.6 | 哪些信息每次都要读？哪些资料按条件读取？文件位置、相对链接与读取条件怎样配合？何时把重复操作提取为脚本？ | Structure large skills with progressive disclosure；File references；Bundling reusable scripts |

这些是可按需要采用的设计方法。真实任务决定哪些方法有帮助，并不要求一份 Skill 使用表中所有做法。

后续每个小节都用同样的学习过程：**看具体问题 → 找出原写法的不足 → 完成一次小修改 → 查看完整文件 → 用任务验证。** 验证既看最终产物，也看 Agent 怎样执行；成功和失败都能提供改进依据。

</details>

<span id="skills-map"></span>

## 机制参考

下列资料解释技能的发现、调用、上下文与 Agent Loop，使用此前的 `review-diff` 示例；可以在写作练习遇到运行机制问题时查阅。

<details>
<summary>查看发现、调用与系统接入的参考图和页面</summary>

{{< architecture src="images/skills-flow.svg" label="Skills 机制参考：技能包、可见目录、调用、正文交付和按需资源" caption="机制参考图：A–D 是内容从技能包进入上下文的过程，E 表示执行会话，F 表示按需资源。图是教学抽象，非 Claude Code 内部源码。" >}}

| 参考资料 | 解决的问题 |
|---|---|
| [S07.R Discovery：发现与加载位置]({{< relref "02-discovery.md" >}}) | 文件放在哪里，当前会话发现的是哪一份 |
| [S07.R Invocation：用户点名，或模型按描述选择]({{< relref "03-invocation.md" >}}) | 谁发起一次调用 |
| [S07.R Progressive Disclosure：区分磁盘、应用内存和模型上下文]({{< relref "04-context.md" >}}) | 各层内容何时可见 |
| [S07.R Rendering：模型读到的是处理后的正文]({{< relref "05-rendering.md" >}}) | 参数与动态内容怎样处理 |
| [S07.R Permissions and Hooks：区分指令、授权和执行拦截]({{< relref "06-permissions.md" >}}) | 执行边界与生命周期 |
| [S07.R Subagent：谁接收指令，主 Agent 是否等待]({{< relref "07-subagents.md" >}}) | 执行上下文怎样选择 |
| [S07.8 Evaluation：触发正确，还要真正完成任务]({{< relref "08-evaluation.md" >}}) | review-diff 的完整调用与验证案例 |
| [S07.9 Integration：把 Skills 接回 Agent Loop]({{< relref "09-agent-loop.md" >}}) | 目录与正文怎样进入原循环 |
| [S07.10 Appendix：一套完整的 Skills 示例]({{< relref "10-appendix.md" >}}) | review-diff 参考练习包 |

机制参考的官网核对日期与版本边界见各页。参考练习包与当前 roll-dice 写作练习分别使用，不要求先完成全部参考资料。

</details>
