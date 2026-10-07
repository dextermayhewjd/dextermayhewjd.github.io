---
title: "S07.7 Subagent：谁接收指令，主 Agent 是否等待"
weight: 70
summary: "比较 inline、fork、后台和等待模式，并区分上下文隔离与工作目录隔离。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

在 [Skills 独立总图]({{< relref "/projects/learn-claude-code/s07/_index.md" >}}#skills-map) 中，本节对应 **E 目标执行上下文**。默认当前会话与可选 fork 分开看，再单独讨论等待或后台执行。

本节的预加载子 Agent 配置、文件位置与实验步骤见 [S07.10 完整示例附录]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}}#lab-variants-preload-review-worker-md)。

## 我想弄清楚的问题

加载 Skill 后，工作一定由主 Agent 做吗？如果 `context: fork` 启动了子 Agent，它知道之前聊了什么？主 Agent 会停下来等它吗？

这些问题需要分别看正文被交给谁、子 Agent 的起始上下文，以及调度方式。

## 默认 inline：正文进入当前对话

{{< architecture from="/projects/learn-claude-code/s07" src="images/skill-context-routing.svg" label="放大 E：Skill 正文交付到当前会话或可选 fork 子上下文" caption="先判断正文交给谁，再判断如何调度。fork 是可选分支；它不是每次 Skill 调用都必须经过的步骤。预加载 skills 则是本节末尾的另一种组合。" >}}

前面的最小 `review-diff` 没有配置 `context: fork`。正文进入当前对话，主 Agent 可以结合已有背景按 Skill 步骤审查。

因此它适合依赖当前讨论的任务。它也会占用当前对话的上下文，读取资料和工具结果同样留在这里。

## fork：把 Skill 作为子 Agent 的任务

一个独立的增强版本可以配置：

````markdown
---
name: review-diff
description: 独立审查当前仓库未提交改动。
context: fork
agent: general-purpose
background: false
---

检查当前 Git 仓库的未提交改动。
先确认文件范围，再检查 diff 和相关上下文。
输出文件位置、触发条件、影响及未覆盖范围。
只提交审查报告。
````

应用创建所选类型的子 Agent，把 Skill 内容作为任务交给它。该子 Agent 不会因为 `fork` 这个字段名就继承主聊天的全部历史。

如果我刚才口头说“只检查 API 层”，这份正文却没有范围，子 Agent 不能依赖那段父对话补齐。需要把范围明确写入 Skill 或传入参数。[依据：在子 Agent 中运行 Skill](https://code.claude.com/docs/en/skills#run-skills-in-a-subagent)。

## 等待，还是后台工作

按 **2026-10-01 官网**，从 Claude Code **v2.1.218** 起，fork Skill 默认可在后台执行；这里显式设置 `background: false`，才要求当前 turn 等它返回。

| 情况 | 主会话如何继续 |
|------|----------------|
| fork Skill，默认后台且环境支持 | 主会话可以继续，结果完成后送回 |
| `background: false` | 等结果返回 |
| `-p` / Agent SDK 等非交互情况 | 官网说明仍会等待 |

禁用后台任务、同一技能已有运行中的调用等情况也会影响等待方式。后台子 Agent 的可用工具还有额外限制，不能只根据一个字段推断所有环境的行为。

S06 本地教学版是普通同步函数调用；现代 Skill 的后台调度机制是这里额外增加的产品能力。

## 上下文隔离不自动复制工作区

`context: fork` 描述的是子 Agent 上下文。普通子 Agent 会从主会话的工作目录开始；单凭这个字段，不能认为文件操作也被隔离了。

若需要独立的 Git 工作树，Claude Code 的自定义子 Agent 支持另行配置 `isolation: worktree`。这是子 Agent 配置里的另一项能力，不是 Skill 的 `context` 字段自动附带的效果。

[依据：子 Agent 的工作目录与 isolation](https://code.claude.com/docs/en/sub-agents)。

## 另一种组合：子 Agent 预加载 Skill

也可以在自定义子 Agent 中写 `skills` 字段。下面是基于第一节 inline Skill 的独立组合：

```yaml
---
name: review-worker
description: 按统一审查方法检查委派的改动。
skills:
  - review-diff
---
根据委派消息确定审查范围，按预加载的方法输出报告。
```

这时 Skill 全文在子 Agent 启动时就进入它的上下文。它不必先通过目录描述决定加载这份方法；真正的任务范围仍由委派消息提供。

`skills` 指定预加载内容，不等于限制它只能使用这些技能。是否能继续调用其他 Skill，要看子 Agent 的可用工具与调用权限。手动调用专用的技能也不能任意预加载。[依据：子 Agent 预加载技能](https://code.claude.com/docs/en/sub-agents#preload-skills-into-subagents)。

## 我的理解

Skill 决定提供哪套指令，子 Agent 配置决定谁执行和有哪些工具，后台设置决定主会话是否等待。上下文、调度和文件工作区应分别检查；子 Agent 返回报告后，主 Agent 仍要依据证据判断结果是否足够。

[上一节]({{< relref "/projects/learn-claude-code/s07/06-permissions.md" >}}) · [下一节：怎样验证效果]({{< relref "/projects/learn-claude-code/s07/08-evaluation.md" >}})
