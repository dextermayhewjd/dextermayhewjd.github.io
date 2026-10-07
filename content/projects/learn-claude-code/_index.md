---
title: "Learn Claude Code"
description: "以新版 S01 到 S17 为主线，逐步记录我对 Agent 的理解，并保留独立的深入专题。"
weight: 10
ShowToc: true
---

## 这个项目记录什么

这里记录我在学习和拆解 Agent 过程中形成的理解。每个 S 章节都是一个独立栏目，先建立结构，再逐步补充内容、实验、问题和结论。

## 章节状态

主目录已对齐当前官方仓库的 S01–S17 顺序，源码基准为 `ce8f9f1`。S01–S09 保留已有笔记，其中部分教学对照仍来自旧版，版本范围在文章中说明；S10 Task System 已按新版重核。S07 的八个子章节继续保留。

S13 将团队、协议、自主认领与 Worktree 隔离组织为四个子主题；S15 主章解释运行时组装，S15.1 单独说明 System Prompt 的内容组成，Error Recovery 暂不展开。尚未学习的正文继续逐步填写。

章节名称统一为“编号 + 英文主题 + 一句中文解释”，例如 **S02 Tool Use：工具增加，循环不变**。左侧导航、下方章节卡片与文章标题使用同一名称。

## 旧编号怎样迁移

| 旧版博客主题 | 当前位置 |
|--------------|----------|
| S10 System Prompt | [S15.1 System Prompt]({{< relref "/projects/learn-claude-code/s15/system-prompt/" >}}) |
| S11 Error Recovery | [S15.2 Error Recovery]({{< relref "/projects/learn-claude-code/s15/error-recovery/" >}}) |
| S12 Task System | [S10 Task System]({{< relref "/projects/learn-claude-code/s10/" >}}) |
| S13 Background Tasks | [S11 Background Tasks]({{< relref "/projects/learn-claude-code/s11/" >}}) |
| S14 Cron Scheduler | [S12 Cron Scheduler]({{< relref "/projects/learn-claude-code/s12/" >}}) |
| S15 Agent Teams | [S13 Agent Teams]({{< relref "/projects/learn-claude-code/s13/" >}}) |
| S16 Team Protocols | [S13.2 Team Protocols]({{< relref "/projects/learn-claude-code/s13/02-team-protocols.md" >}}) |
| S17 Autonomous Agents | [S13.3 Task Claiming]({{< relref "/projects/learn-claude-code/s13/03-task-claiming.md" >}}) |
| S18 Worktree Isolation | [S13.4 Worktree Isolation]({{< relref "/projects/learn-claude-code/s13/04-worktree-isolation.md" >}}) |
| S19 MCP Tools | [S14 MCP Tools]({{< relref "/projects/learn-claude-code/s14/" >}}) |
| S20 Comprehensive Agent | [S15 Integrated Harness]({{< relref "/projects/learn-claude-code/s15/" >}}) |

新版 S16 Workflow Runtime 与 S17 Goal Loop 已补齐正文、源码对照与三张架构图。旧 S18–S20 地址会跳转到对应新页面；旧 S10–S17 地址已被新版同编号主题复用，请按上表查找原内容。

## 记录方式

每个章节围绕自己的理解逐步展开：

- 这一节要解决的问题
- 用架构图看清主流程与新增机制
- 分步解释概念，并给出对应代码
- 把步骤串成完整流程或伪代码
- 核对实现边界、实验结果和仍有疑问的地方
- 最后留下的一句话理解
