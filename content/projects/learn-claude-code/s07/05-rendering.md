---
title: "S07.5 Rendering：模型读到的是处理后的正文"
weight: 50
summary: "用实际调用说明参数替换、技能目录变量和动态命令注入，区分预处理与模型行动。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

在 [Skills 独立总图]({{< relref "/projects/learn-claude-code/s07/_index.md" >}}#skills-map) 中，本节对应 **D 准备正文中的可选处理**。从最小正文逐步加入参数和动态内容，不把它们当作每个 Skill 的必经步骤。

本节的随 Skill 分发的脚本、文件位置与实验步骤见 [S07.10 完整示例附录]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}}#lab-project-claude-skills-review-diff-scripts-inspect-diff-sh)。

## 我想弄清楚的问题

调用 `/review-diff` 后，模型读到的一定是原始文件吗？正文可以包含参数位置和动态命令，因此需要先理解“文件模板 → 渲染结果 → 模型上下文”的过程。

## 用参数指定审查重点

给 Skill 加入提示和参数位置：

````markdown
---
name: review-diff
description: 检查当前仓库未提交改动中的行为缺陷。
argument-hint: "[focus]"
---

审查重点：$ARGUMENTS

先查看当前改动，再读取相关上下文，最后按证据报告问题。
````

调用：

```text
/review-diff 空输入和错误处理
```

模型得到的对应段落会变成：

```text
审查重点：空输入和错误处理
```

`$ARGUMENTS` 承载参数文本；`argument-hint` 帮用户知道应该填什么，本身不是参数类型校验器。位置参数也可以用 `$0`、`$1` 等访问。参数替换不是 Shell 执行，也不会自动把“空输入”转换成某个检查函数。

[依据：参数传递与字符串替换](https://code.claude.com/docs/en/skills#pass-arguments-to-skills)。

## 动态命令在模型读取正文前运行

如果希望审查时总能带上当时已跟踪文件的改动，可以用一个独立的增强版本：

````markdown
---
name: review-diff
description: 检查当前仓库未提交改动中的行为缺陷。
allowed-tools: Bash(git diff HEAD)
---

## 当前已跟踪文件的改动

!`git diff HEAD`

## 任务

根据上面的 diff 和必要的文件上下文，报告有证据的问题。
````

Claude Code 先执行命令，把输出插入正文，再将处理后的内容交给模型。与第一节“正文要求模型自己调用 Bash”相比，这里的命令发生在 Skill 内容预处理阶段。

```text
Original SKILL.md -> Run injected command -> Insert stdout -> Send rendered content
```

这段 diff 只反映命令运行时的状态。后面又改了文件，旧输出不会自动变成最新内容；需要重新取数。未跟踪文件也要额外处理，不能因为拿到了 diff 就宣称检查过全部工作区。

## 命令失败时，正文可能没有进入上下文

动态命令受权限和运行环境约束。常规情况下命令未获允许或执行失败，会使这次技能渲染失败；官网另有 auto 模式和部分命令退出码的特殊处理。

这意味着“Skill 没有给出报告”可能是注入阶段失败，模型还没读到工作步骤。应该查看权限或命令错误，而不是先改审查方法。

账号同步 Skill、Cowork、云端和终端的动态命令处理也有区别；这里的示例针对本地项目 Skill，不把这段语法当成所有环境都必然执行的承诺。[依据：动态注入及失败规则](https://code.claude.com/docs/en/skills#inject-dynamic-context)。

## 资料路径和脚本路径

现代 Claude Code 可以用 `${CLAUDE_SKILL_DIR}` 定位 Skill 所在目录。例如正文指示：

```markdown
需要收集改动信息时，运行：
bash "${CLAUDE_SKILL_DIR}/scripts/inspect-diff.sh"
```

路径替换后，模型仍需要请求工具运行这条普通指令。只有写成动态注入语法时，才会进入前面的预处理路径。Skill 中的 `scripts/` 目录也不会因为被发现就自动运行。

本例的 `scripts/inspect-diff.sh` 可以是一个简单的收集程序：

```bash
#!/usr/bin/env bash
set -euo pipefail
git status --short
git diff --stat HEAD
git diff HEAD
```

它在当前工作目录对应的仓库中运行，返回状态和 diff，供模型继续审查。它只列出未跟踪文件的路径，不会自动读取那些文件的内容；后续取证仍属于模型的工作。

## 我的理解

现代 Skill 的正文可以是模板。Harness 负责替换参数、准备动态数据，模型再基于处理后的指令工作；预处理命令和模型后来发起的工具调用，要分开追踪。

[上一节]({{< relref "/projects/learn-claude-code/s07/04-context.md" >}}) · [下一节：权限和 Hooks]({{< relref "/projects/learn-claude-code/s07/06-permissions.md" >}})
