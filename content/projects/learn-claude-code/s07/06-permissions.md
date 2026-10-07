---
title: "S07.6 Permissions and Hooks：区分指令、授权和执行拦截"
weight: 60
summary: "分清 allowed-tools、disallowed-tools 与权限策略，说明 Skill Hooks 的执行和持续时间。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

在 [Skills 独立总图]({{< relref "/projects/learn-claude-code/s07/_index.md" >}}#skills-map) 中，本节对应 **C / D / E 的调用与执行边界**。权限、Hook 和内容生命周期分别判断；不把“加载正文”当作取得全部授权。

本节的完整 Hook 脚本、文件位置与实验步骤见 [S07.10 完整示例附录]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}}#lab-project-claude-hooks-skill-hook-py)。

## 我想弄清楚的问题

在 Skill 里写“只做审查，不修改文件”，是否就能保证没有写操作？这是一条交给模型的工作要求。执行层还要分别处理工具是否可用、调用是否获准，以及是否被 Hook 拦截。

## allowed-tools 给的是临时预授权

本例可以写：

```yaml
allowed-tools: Read Grep Bash(git diff HEAD) Bash(git status --short)
```

它让列出的工具调用在本次 Skill 调用所在的 turn 中获得预授权。没有列出的工具仍可能存在，并继续走通常的权限流程；它不是“除此之外都不能用”的工具白名单。

`disallowed-tools` 则可以移除指定工具。例如：

```yaml
disallowed-tools: Write Edit
```

这样可以挡住对应工具，但如果 Bash 仍可用，模型依然可能通过命令修改文件。因此“禁止两种文件工具”也不能直接推导出“完全只读”。[依据：Skill 工具权限](https://code.claude.com/docs/en/skills#pre-approve-tools-for-a-skill)。

## 权限规则决定是否执行

Claude Code 的权限系统还会考虑调用内容、允许/询问/拒绝规则和当前权限模式。Skill 的临时授权不会让已有拒绝或询问规则消失。

我把这些判断理解为三层：

```text
Skill instruction -> Model proposes action
Tool availability -> Can this action be requested?
Permission / Hook -> May it actually execute?
```

这是一张理解用的关系图，不是内部函数调用顺序。若审查必须完全不写，应该根据实际可用工具设置执行约束，而不是仅靠正文“不要改”这一句。

[依据：Claude Code 权限配置](https://code.claude.com/docs/en/permissions)。

## Hook 可以在执行前给出明确决定

延续 S04：一个已配置的 `PreToolUse` Hook 可以读取工具请求，按规则决定拒绝。假设它识别出本轮不允许的写操作，可返回如下结构：

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "本次审查不允许此写操作"
  }
}
```

这是官网定义的返回格式。Hook 脚本自身要实现识别条件；这段 JSON 只是决定结果，单独放在 Skill 正文里不会自动变成执行拦截器。

实际使用时，需要在设置或 Skill 的 `hooks` frontmatter 中注册事件和处理程序。事件触发后，应用才会运行它。[依据：Hook 输入与决策](https://code.claude.com/docs/en/hooks#pretooluse-decision-control)。

## 三种状态持续多久

| 状态 | 当前官网描述的持续方式 |
|------|------------------------|
| 已注入的 Skill 正文 | 留在对话中，受上下文管理影响 |
| `allowed-tools` / `disallowed-tools` | 调用所在 turn，下一条用户消息后清除 |
| Skill frontmatter 注册的 Hook | 调用后继续作用于本次会话；可配置 `once` |

[Skill Hook 生命周期](https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents)尤其容易漏看：它可能在后面的 turn 仍触发，不应想当然地认为正文执行完就撤销。

因此排查行为时，应分别问“模型还有哪些指令”“哪些授权还在”“哪些 Hook 还注册着”。

## 我的理解

Skill 正文提供行动方法；工具配置和权限系统约束行动空间；Hook 在具体事件上执行附加检查。它们各自有执行入口和生命周期，不能用一个“Skill 已加载”概括全部状态。

[上一节]({{< relref "/projects/learn-claude-code/s07/05-rendering.md" >}}) · [下一节：Skill 和子 Agent]({{< relref "/projects/learn-claude-code/s07/07-subagents.md" >}})
