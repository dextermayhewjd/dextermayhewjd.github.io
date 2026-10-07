---
title: "S07 Skills：从发现到执行的完整流程"
weight: 70
description: "先理解 Skills 自身，再逐部分拆解，完整走一次 review-diff，最后接回 Agent Loop。"
---

**版本范围：** 本专题以 Agent Skills 标准与现代 Claude Code 的公开文档为依据。流程图是我的教学抽象，伪代码用来解释接口，不代表 Claude Code 的内部源码。主线先采用项目级、默认 inline 的 `review-diff`；可选配置分别展开。总图与接入说明的官网核对日期：**2026-10-04**；扩展配置的具体条件见各节来源与版本说明。

## 这次先看 Skills 自己

S06 从工具入口展开了一段子循环。Skills 涉及的范围更广：内容组织、发现、调用、装载和执行上下文都有各自的问题。先把这些边界认清，再放回完整系统，比较容易看出每一步到底改变了什么。

本组仍用 `review-diff` 贯穿：检查仓库的未提交改动，给出有证据的风险报告。它是笔记中的讲解示例，尚未安装到本仓库。

阅读顺序是：**独立总图 → 局部拆解 → 走完一个例子 → 接回 Agent Loop。**

<span id="skills-map"></span>

## Skills 独立总图

{{< architecture src="images/skills-flow.svg" label="Skills 独立机制：技能包、可见目录、调用、正文交付和按需资源" caption="先只看 Skills。A–D 是内容从技能包走向上下文的主线；E 暂时把执行会话当作外部接口；F 表示执行时继续取用的资源。虚线可选扩展分别讲解，完整 Agent Loop 最后在 S07.9 接回。" >}}

这是一张机制地图。紫色标出本节讨论的 Skills 机制，蓝色是已有执行会话，灰色是内容存放处；不是产品版本之间的源码差异图。

| 图中位置 | 先回答的问题 | 去哪里展开 |
|---|---|---|
| A 技能包 | 哪部分是元信息，哪部分是工作指令，哪些文件只是配套资源？ | S07.1 |
| B 可见目录 | 系统发现了什么，当前调用者能看到什么？ | S07.2 |
| C 发起调用 | 用户点名与模型自行选择怎样汇合？ | S07.3 |
| D 准备与交付 | 正文什么时候可见，参数和动态信息如何处理？ | S07.4、S07.5 |
| D / E 的执行边界 | 权限、Hook 和目标上下文分别影响什么？ | S07.6、S07.7 |
| F 按需资源 | 哪些资料需要继续读取，哪些脚本需要执行？ | S07.4、S07.5 |
| 一次完整调用 | 是否选对方法，又是否完成任务？ | S07.8 |
| 整体系统 | 上述接口最终接在 Agent Loop 的哪里？ | S07.9 |

目录描述先供选择，正文在调用时装载，配套资源按需使用，这是理解渐进披露的起点。[Agent Skills 标准](https://agentskills.io/specification#progressive-disclosure)

## 第一遍只走默认路径

先使用最小的 `review-diff`：用户或模型发起调用，正文进入当前对话，模型按照审查步骤使用已有工具。动态命令、额外权限配置和 fork 都不是这个最小例子的前提。

这条主线要分清四个动作：

1. **发现**：应用知道这个 Skill 存在。
2. **调用**：决定这一次要使用它。
3. **交付内容**：相应指令进入模型可见上下文。
4. **依据指令行动**：模型继续请求工具，取得证据并形成报告。

文件存在不等于已经调用；加载正文也不等于完成任务。默认 inline 和可选 fork 的交付目标不同，后者到 S07.7 再展开。[Claude Code 的调用与上下文说明](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill)

## 九节主线与完整示例附录

| 层次 | 章节 | 核心问题 |
|---|---|---|
| 核心主线 | [S07.1 Skill Structure：先看一个最小例子]({{< relref "/projects/learn-claude-code/s07/01-structure.md" >}}) | 一份 Skill 包含什么？ |
| 核心主线 | [S07.2 Discovery：放在哪里决定谁能用]({{< relref "/projects/learn-claude-code/s07/02-discovery.md" >}}) | 怎样发现、怎样决定可见范围？ |
| 核心主线 | [S07.3 Invocation：用户点名，或模型按描述选择]({{< relref "/projects/learn-claude-code/s07/03-invocation.md" >}}) | 一次调用从哪里发起？ |
| 核心主线 | [S07.4 Progressive Disclosure：区分磁盘、应用内存和模型上下文]({{< relref "/projects/learn-claude-code/s07/04-context.md" >}}) | 模型何时看见哪一层内容？ |
| 可选扩展 | [S07.5 Rendering：模型读到的是处理后的正文]({{< relref "/projects/learn-claude-code/s07/05-rendering.md" >}}) | 如何加入参数与动态信息？ |
| 可选扩展 | [S07.6 Permissions and Hooks：区分指令、授权和执行拦截]({{< relref "/projects/learn-claude-code/s07/06-permissions.md" >}}) | 执行边界与生命周期怎样区分？ |
| 可选扩展 | [S07.7 Subagent：谁接收指令，主 Agent 是否等待]({{< relref "/projects/learn-claude-code/s07/07-subagents.md" >}}) | 切换执行上下文会改变什么？ |
| 完整案例与验证 | [S07.8 Evaluation：触发正确，还要真正完成任务]({{< relref "/projects/learn-claude-code/s07/08-evaluation.md" >}}) | 沿一次调用追踪内容与结果，怎样检查效果？ |
| 接回系统 | [S07.9 Integration：把 Skills 接回 Agent Loop]({{< relref "/projects/learn-claude-code/s07/09-agent-loop.md" >}}) | 回顾 S06，再把 Skills 接入点放回总图与伪代码。 |
| 完整示例附录 | [S07.10 Appendix：一套完整的 Skills 示例]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}}) | 可下载工程、完整文件内容、配置变体、实验步骤，以及每份文件对应的章节与注意点。 |

各节开头标明自己在独立总图中的位置。调用、渐进披露、上下文分支配局部图；目录范围、权限生命周期和评估用表格或代码说明，不为每节强行重复三张全局图。

## 三类内容分别看

| 内容 | 本专题怎样使用 |
|---|---|
| 开放标准 | 解释技能包、元信息与分层内容组织 |
| Claude Code 的公开行为 | 解释产品中的调用、渲染、权限和子 Agent 配置 |
| 教学代码与伪代码 | 用可追踪的处理步骤理解上述接口，明确其简化范围 |

当前本地 `s07_skill_loading/code.py` 用 `SkillLoader`、`catalog()` 和 `load_skill` 演示目录与完整内容分开进入上下文。它不是全部现代 Skills 功能的实现，也没有带入 S06 的 `task`。这个独立脚本的工具集合，不能用来推断现代产品是否支持 Skill 与子 Agent 组合。

末尾的系统接入图沿用已学过的 Agent 骨架，标明本章增加的机制；它不是把不同产品与不同示例文件当作同一个仓库版本做差异比较。
