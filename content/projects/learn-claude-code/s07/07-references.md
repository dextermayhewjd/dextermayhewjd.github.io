---
title: "S07.7 References：怎样组织和引用配套资料"
weight: 70
summary: "从官方多文件例子出发，区分主文件与配套资料，写清相对链接、读取条件，并检查按需读取是否发生。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

当一份 Skill 需要更多说明时，可以把主流程留在 `SKILL.md`，把详细资料拆到其他文件，再从主文件说明何时读取。它们仍然共同组成一份 Skill。

本节以 [Agent Skills 的文件引用规范](https://agentskills.io/specification#file-references)、[渐进式披露建议](https://agentskills.io/skill-creation/best-practices#structure-large-skills-with-progressive-disclosure)和 [Claude Code 的 Add supporting files](https://code.claude.com/docs/en/skills#add-supporting-files) 为依据。先看官方写法，再将它应用到本站已有的审查练习。

## 7.7.1 从官方例子认识主文件与配套文件

下面是 Claude Code 官方目录示例的中文说明，文件名和位置保留原样：

```text
my-skill/
├── SKILL.md       # 必需：概述与导航
├── reference.md   # 详细 API 文档，需要时读取
├── examples.md    # 使用示例，需要时读取
└── scripts/
    └── helper.py  # 工具脚本，调用执行
```

与它配套的正文片段是：

```markdown
## 补充资料

- 完整 API 细节见 [reference.md](reference.md)。
- 使用示例见 [examples.md](examples.md)。
```

这里需要区分三个层次：`SKILL.md` 告诉 Agent 如何完成任务，以及去哪里取用细节；`reference.md` 和 `examples.md` 提供具体内容；脚本提供可调用的代码。文件放进目录后，还需要主文件给出使用说明。

参考资料可以包含技术细节、领域规则、输入输出示例或某个场景的完整处理步骤，不限于百科式的背景知识。拆分的目的是让当前任务需要的内容进入上下文。

## 7.7.2 文件应该放在哪里，引用应该怎样写

**参考文件不必放在名为 `references/` 的目录中。** 上面的官方例子将它们放在主文件旁边；Agent Skills 规范则展示了 `references/REFERENCE.md`。两种组织都可以使用，路径要与实际位置一致。

规范中的引用示例，翻译后是：

```markdown
详细说明见[参考指南](references/REFERENCE.md)。
```

其中 `[参考指南]` 是链接文字，`(references/REFERENCE.md)` 是目标路径。这个路径以技能根目录为基准；在这个例子里，就是 `SKILL.md` 所在目录。

| 文件实际位置 | 从 `SKILL.md` 写出的链接 |
| --- | --- |
| 与主文件同目录的 `reference.md` | `[API 说明](reference.md)` |
| 子目录中的 `references/input-boundaries.md` | `[输入边界说明](references/input-boundaries.md)` |

规范建议从 `SKILL.md` 直接引用需要的资料，避免深层引用链。例如，直接指向 `references/input-boundaries.md`，比先读一个索引、再读另一个索引、最后才找到内容更清楚。“引用一层”不表示禁止使用子目录，规范自己的例子就包含 `references/`。

正文没有固定模板；这两处官网也没有声明纯文本路径无效。因此，原来的“读 references/input-boundaries.md”不是规范语法错误。本站教学统一采用**有说明的 Markdown 相对链接**，与官方示例一致，也方便检查文件指向。

## 7.7.3 怎样说明文件内容和读取条件

只有链接，Agent 知道去哪里；加上资料用途和可判断的条件，Agent 才更容易知道何时需要它。

官网最佳实践对比了“详情见 references/”与“API 返回非 200 状态码时，读取 references/api-errors.md”。前者没有指出具体文件，也没有给出读取条件。

将这个原则用于已有的审查例子，可以写成：

```markdown
## 需要时读取的资料

- 改动涉及空输入、缺失字段、默认值或类型边界时，
  阅读[输入边界审查](references/input-boundaries.md)，核对输入与函数约定。
- 改动涉及共享状态、异步任务或并发时，
  阅读[共享状态审查](references/concurrency.md)，检查读取和写回的交错顺序。
```

这里同时交代了**读取条件、资料用途和文件位置**。它保留了原例中的条件判断，并把路径改成明确的相对链接；读取后仍回到当前审查任务。

文件存在、出现在目录列表中，或者被写成链接，都不代表它已经进入模型上下文。实际读取仍需 Agent 使用可用的文件工具，或由客户端提供对应的加载机制。参见[配套资源的按需加载](https://agentskills.io/client-implementation/adding-skills-support#listing-bundled-resources)。

## 7.7.4 哪些内容适合拆出去，还有哪些配套部分

先按任务需要判断内容，再选放置位置：

| 当前内容的用途 | 合适的位置 |
| --- | --- |
| 每次都需要的任务范围、主步骤和关键约束 | `SKILL.md` |
| 特定情况下才需要的详细规则、说明或示例 | 配套参考文件，可放在 `references/` |
| 要套用、复制或填充的模板、图片等素材 | 通常放在 `assets/` |
| 需要实际运行的解析、生成或验证代码 | 通常放在 `scripts/` |

这些目录是[规范推荐的组织惯例](https://agentskills.io/specification#optional-directories)，可以按需要增加其他文件或目录，不要求每份 Skill 都具备全部目录。文件内容也可能有交集：文档中的格式示例可以随说明放在参考文件中，单独复用的报告模板可以放在 `assets/`。

不要把必须提前知道的规则随意移走。例如，“`git diff HEAD` 不包含未跟踪文件的正文”会影响一开始怎样确定审查范围，适合保留在主文件。若先漏掉文件，Agent 可能根本意识不到需要再查这条规则。[官网 Gotchas 建议](https://agentskills.io/skill-creation/best-practices#gotchas-sections)也强调了这种情况。

即使主文件还很短，也可以按任务条件拆出低频细节；如果整段内容没有帮助，则应考虑删除，而不是搬进另一个文件。正文保持精简与参考资料按需读取，需要一起考虑。

## 7.7.5 看一份完整的最小拆分

下面从本站已有 `review-diff` 练习裁剪出三份文件。主文件只保留审查与参考读取，省去原练习的参数、动态命令和权限配置；引用改为 Markdown 相对链接。两份参考文件保留实际内容，仅省去历史章节注释。

```text
review-diff/
├── SKILL.md
└── references/
    ├── input-boundaries.md
    └── concurrency.md
```

**主文件：`SKILL.md`**

```markdown
---
name: review-diff
description: 用户要求审查当前 Git 仓库未提交改动、检查 diff 或查找回归时使用。
---

## 审查流程

1. 用 `git status --short` 和 `git diff HEAD` 确认改动范围。
   `git diff HEAD` 不包含未跟踪文件的正文，相关内容需要另外读取。
2. 阅读相关源码和测试，按下面的条件选择参考资料。
3. 输出问题的位置、触发条件、影响和证据，并说明未覆盖范围。
   只做审查，不修改文件；证据不足时不要声称已经确认缺陷。

## 需要时读取的资料

- 涉及空输入、缺失字段、默认值或类型边界时，
  阅读[输入边界审查](references/input-boundaries.md)。
- 涉及共享状态、异步任务或并发时，
  阅读[共享状态审查](references/concurrency.md)。
```

**配套文件一：`references/input-boundaries.md`**

```markdown
# 输入边界审查

- 先核对函数约定，再选择边界输入；不要把个人风格当作缺陷。
- 本练习 normalize_first([]) 的约定是返回空字符串。
- 指出具体表达式、触发输入和可观察后果。
- 运行测试只验证当前样例，不等于全部输入正确。
```

**配套文件二：`references/concurrency.md`**

```markdown
# 共享状态审查

- 标出读取旧值、让出执行权、写回新值的位置。
- 检查两个请求是否可能基于同一旧值各自写回。
- 以一个具体交错顺序和测试解释结果，避免泛称“线程不安全”。
- 本练习要求两次 increment 完成后 count 增加二。
```

这两份资料中的函数与约定属于本站练习，迁移到其他项目时需要重新核对。完整原始练习与文件入口见[配套附录]({{< relref "10-appendix.md" >}}#lab-project-claude-skills-review-diff-references-input-boundaries-md)。

这里仍然只有一份 `review-diff` Skill。阅读配套文件是在展开同一份技能的细节；启用另一份具有自己名称、描述和入口的 Skill，才涉及多份技能的组合。

## 7.7.6 怎样检查拆分和引用是否有效

先检查文件关系：从 `SKILL.md` 所在目录解析链接，确认文件存在、名称与大小写正确、内容与链接说明一致。网页能把教学代码显示出来，并不代表代码中指向的文件已经验证或被 Agent 读取。

再观察实际任务。下面是针对本例的待执行检查用例：

| 任务情况 | 预期读取的参考资料 |
| --- | --- |
| 检查空列表或默认值行为 | `input-boundaries.md` |
| 检查两个异步调用更新计数的行为 | `concurrency.md` |
| 同时包含输入边界与共享状态改动 | 两份都需要 |
| 只涉及文档拼写，且无上述行为变化 | 不要求读取这两份 |

检查不止看“读取成功”，还要看资料有没有被用于判断：是否按真实函数约定选择输入，是否给出了具体交错顺序。文件缺失或无法访问时，应报告缺少的资料，不应声称已经完成该项核对。

这些是教学检查方法，尚未报告模型执行成绩。要检查实际行为，需要保留文件读取记录、审查依据和最终输出；不能把相对链接本身当作执行保证。

[上一节：有效指导的模式]({{< relref "06-instruction-patterns/_index.md" >}}) · [机制参考：内容何时进入上下文]({{< relref "04-context.md" >}})
