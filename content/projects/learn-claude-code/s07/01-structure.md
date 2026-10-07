---
title: "S07.1 Skill Structure：先看一个最小例子"
weight: 10
summary: "区分元信息、工作指令和配套资源，建立一个可理解的 review-diff 示例。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

在 [Skills 独立总图]({{< relref "/projects/learn-claude-code/s07/_index.md" >}}#skills-map) 中，本节对应 **A 技能包**。先区分元信息、正文与资源，暂不展开 Agent Loop。

本节的主 SKILL.md、文件位置与实验步骤见 [S07.10 完整示例附录]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}}#lab-project-claude-skills-review-diff-skill-md)。

## 我想弄清楚的问题

目录里放一份 Markdown，为什么就能叫 Skill？关键在于 Agent 应用能发现这份内容、知道何时使用它，并在调用时把指令交给模型。

我们先写一个 `review-diff`。它的任务很具体：检查当前仓库的未提交改动，报告可能影响行为的缺陷。

## 最小目录和完整正文

文件放在项目中：

```text
.claude/skills/review-diff/SKILL.md
```

内容可以是：

````markdown
---
name: review-diff
description: 检查当前 Git 仓库的未提交改动。用户要求审查 diff、排查改动风险或检查这次修改时使用。
---

## 工作步骤

1. 查看 git status --short，确认改动范围。
2. 查看 git diff HEAD，再读必要的上下文。
3. 检查输入边界、错误处理和行为变化。
4. 每个问题写清楚文件位置、触发条件和后果。
5. 只提交审查报告；没有足够证据时说明不确定性。

## 输出格式

先列问题，再说明检查范围。没有发现问题时明确写出。
````

这是原创示例，不是官网内置审查 Skill 的副本。`git diff HEAD` 展示已跟踪文件相对 HEAD 的改动；新建但未跟踪的文件需要根据 `git status` 另外检查。

## 三部分分别是谁处理的

| 部分 | 作用 |
|------|------|
| YAML frontmatter | Agent 应用解析名称、描述及调用配置 |
| Markdown 正文 | 加载后交给模型，指导它怎样完成任务 |
| 参考文件、脚本和素材 | 按任务需要进一步读取、执行或使用 |

正文中的“查看 diff”是交给模型的行动指令。模型仍要请求 Bash 或文件工具，由 Harness 执行；加载 Skill 不会把正文里的每一句话当程序运行。

更确定的操作可以写成脚本，由模型调用；带 `!` 的动态命令则属于应用的预处理，后面会单独讲。

## 开放标准和 Claude Code 扩展

[Agent Skills 规范](https://agentskills.io/specification#skillmd-format)定义了 `SKILL.md`、元信息和资源组织。Claude Code 使用这个基本形态，并添加自己的字段。

例如 `disable-model-invocation` 和 `context` 是 Claude Code 的调用与执行配置。把 Skill 移到另一个 Agent 产品时，应查看对方支持的字段；文件格式相似并不意味着运行行为完全相同。

本例明确写 `name`、`description`，让名称与用途容易判断。Claude Code 对缺省字段有自己的回退规则，[官网 frontmatter 参考](https://code.claude.com/docs/en/skills#frontmatter-reference)也不同于标准对必需字段的规定。

## 我的理解

Skill 的可复用性来自“发现信息 + 工作指令 + 配套资源”的组织。它把审查方法装成一个能被调用的包，真正的审查仍由模型和工具共同完成。

[下一节：Skill 怎么被发现]({{< relref "/projects/learn-claude-code/s07/02-discovery.md" >}})
