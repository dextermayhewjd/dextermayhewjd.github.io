---
title: "S07.1 Minimal Skill：写出一份最小完整技能"
weight: 10
summary: "采用官网 Quickstart 的 roll-dice 示例，通过一次掷骰子认识 name、description 和正文指令。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

这一节采用 [Agent Skills Quickstart](https://agentskills.io/skill-creation/quickstart) 的 **roll-dice** 示例：让 Agent 使用随机数命令掷一次骰子。

先写一份完整的 `SKILL.md`，再认识其中的三个组成部分：`name`、`description` 和正文指令。

## 1. 先确定一个小任务

向 Agent 提出请求：

> Roll a d20.

`d20` 中的 `d` 表示骰子（die），`20` 表示它有 20 个面，通常标着 1～20。因此，`Roll a d20` 就是“掷一次 20 面骰子”，结果为 1～20 中的一个整数。同样，`d6` 表示常见的六面骰子，结果为 1～6。

我们希望 Agent 实际运行随机数命令，得到这次掷骰子的结果，再告诉我们。

## 2. 写出完整的 SKILL.md

官网 Quickstart 使用 **VS Code + GitHub Copilot 的 Agent 模式**。按该示例，在项目中创建：

```text
.agents/
└── skills/
    └── roll-dice/
        └── SKILL.md
```

文件内容如下：

````markdown
---
name: roll-dice
description: Roll dice using a random number generator. Use when asked to roll a die (d6, d20, etc.), roll dice, or generate a random dice roll.
---

To roll a die, use the following command that generates a random number from 1
to the given number of sides:

```bash
echo $((RANDOM % <sides> + 1))
```

```powershell
Get-Random -Minimum 1 -Maximum (<sides> + 1)
```

Replace `<sides>` with the number of sides on the die (e.g., 6 for a standard
die, 20 for a d20).
````

同一份 Skill 也可以写成中文。下面是对应的中文版本，保留相同的名称与命令；两种版本任选其一保存到 `SKILL.md` 即可。

````markdown
---
name: roll-dice
description: 使用随机数生成器掷骰子。当用户要求掷一次骰子（如六面骰 d6、二十面骰 d20）、掷骰子或生成随机掷骰结果时使用。
---

要掷一次骰子，请使用下面的命令，生成一个从 1 到指定面数之间的随机整数。

```bash
echo $((RANDOM % <sides> + 1))
```

```powershell
Get-Random -Minimum 1 -Maximum (<sides> + 1)
```

将 `<sides>` 替换为骰子的面数，例如普通六面骰使用 6，二十面骰 d20 使用 20。
````

这里的 `<sides>` 是占位符，表示骰子的面数。Agent 要根据请求把它替换为具体数字；Bash 和 PowerShell 是两种环境的写法，执行时选择当前环境对应的一种。

## 3. 分清这三部分

| 部分 | 本例写了什么 | 负责回答的问题 |
|---|---|---|
| `name` | `roll-dice` | 这份 Skill 叫什么？ |
| `description` | 用随机数掷骰子，以及哪些请求适合使用 | 当前任务适不适合用它？ |
| Markdown 正文 | 使用哪条命令，怎样替换骰子面数 | 使用之后具体怎么做？ |

开头两条 `---` 之间是 YAML 元信息，后面是 Markdown 正文。`name` 与所在的 `roll-dice` 文件夹同名。

`description` 帮助 Agent 判断是否采用这个 Skill；正文则在采用之后提供操作方法。正文中的代码块是交给 Agent 的说明，需要它通过终端工具执行。

## 4. 让 Agent 用一次

在 VS Code 打开项目，进入 Copilot Chat 的 Agent 模式。先输入 `/skills`，确认列表中出现 `roll-dice`，再提出：

> Roll a d20.

也可以用中文提出同一个请求：

> 帮我掷一次二十面骰子（d20）。

如果 Agent 使用 Bash，它应把命令中的 `<sides>` 替换成 `20`，实际执行：

```bash
echo $((RANDOM % 20 + 1))
```

观察它是否调用了终端工具，以及返回值是否在 1 到 20 之间。只在回复中说出一个数字，还不能说明它执行了 Skill 中的命令。

至此，一份最小完整 Skill 就串起来了：**名称标识技能，描述帮助选择，正文指导行动。**

来源：[Agent Skills Home](https://agentskills.io/home)、[Quickstart](https://agentskills.io/skill-creation/quickstart)。

[下一节：把有效做法写成可复用技能]({{< relref "/projects/learn-claude-code/s07/02-real-expertise.md" >}})
