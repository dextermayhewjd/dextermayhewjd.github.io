---
title: "S07.6.6 把重复操作封装成可复用脚本"
weight: 60
summary: "复用现有 Git 快照脚本，观察输入环境、实际输出和失败返回，区分脚本代码与调用指令。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

本节对应 [Bundling reusable scripts](https://agentskills.io/skill-creation/best-practices#bundling-reusable-scripts)，并参考 [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts)。

## 问题

每次审查改动，Agent 都要重新组织“确认仓库位置、查看状态、读取 diff、列出未跟踪文件”的命令组合。

如果这段逻辑每次都相同，重复生成会增加遗漏步骤、参数不同和维护多份代码的机会。

## 解决方案

将已经使用过、能检查的逻辑保留在脚本里。Skill 说明何时调用、在哪里运行，以及怎样使用结果。

简单的现有命令可以直接调用。反复组合的操作适合提取为脚本；不用为了拥有 `scripts/` 目录，把所有一句话命令都再包装一层。

## 最小示例

本站练习中已有 `scripts/inspect-diff.sh`。下面节选其代码，仅省略历史章节号注释：

```bash
#!/usr/bin/env bash
set -euo pipefail
git rev-parse --show-toplevel
git status --short
git diff HEAD
printf '\nUntracked paths (contents are not read automatically):\n'
git ls-files --others --exclude-standard
```

这段代码的输入环境是当前工作目录所属的 Git 仓库；输出包括仓库位置、状态、差异和未跟踪文件路径。它不自动读取未跟踪文件正文，也不输出“审查通过”的结论。

配套的完整最小教学 `SKILL.md`：

```markdown
---
name: review-diff
description: 用户要求审查当前 Git 仓库未提交改动、检查 diff 或查找回归时使用。
---

1. 在待审查的 Git 仓库中执行本技能目录内的 `scripts/inspect-diff.sh`。
2. 脚本失败时读取错误，先解决工作目录等前置条件。
3. 根据输出读取相关源码、测试和未跟踪文件正文。
4. 用证据报告问题及覆盖范围，不将快照输出当成审查结论。
```

生成本站练习后，可以在该练习仓库根目录执行真实路径：

```bash
bash .claude/skills/review-diff/scripts/inspect-diff.sh
```

文件位置与完整练习包见[机制参考附录]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}})。

## 怎样检查

2026-10-13 已在带有空输入回归的隔离仓库中执行该脚本：退出码为 `0`，输出包含 `src/normalize.py` 的差异以及 `untracked-note.txt` 路径。

在非 Git 目录中再次执行时，退出码为 `128`，实际错误为：

```text
fatal: not a git repository (or any of the parent directories): .git
```

因此可以明确区分“取得快照”和“前置条件不成立”。这两种脚本行为已验证，Agent 是否正确调用和使用结果仍需单独观察。

后续扩展脚本时，应继续明确参数、输出和错误含义。结构化结果适合程序继续处理；有用的错误信息帮助 Agent 决定下一步动作。

脚本存在于目录中不会自动执行。它要由工具或宿主程序实际调用，才会产生这里展示的输出。

[上一节：执行前验证计划]({{< relref "05-plan-validation.md" >}}) · [返回本章]({{< relref "_index.md" >}})
