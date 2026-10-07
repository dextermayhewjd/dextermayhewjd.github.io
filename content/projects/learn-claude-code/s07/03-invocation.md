---
title: "S07.3 Invocation：用户点名，或模型按描述选择"
weight: 30
summary: "区分发现、菜单可见、模型可见和真正调用，解释两种调用控制字段。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

在 [Skills 独立总图]({{< relref "/projects/learn-claude-code/s07/_index.md" >}}#skills-map) 中，本节对应 **C 发起调用**。追踪用户和模型两种入口，随后交给同一正文准备阶段。

本节的手动专用配置变体、文件位置与实验步骤见 [S07.10 完整示例附录]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}}#lab-variants-manual-skill-md)。

## 我想弄清楚的问题

Skill 已经被发现，为什么有时自动调用，有时要我输入 `/review-diff`？需要分清三个阶段：被系统发现、可供某一方调用、真正进入调用流程。

## 两条调用路径

{{< architecture from="/projects/learn-claude-code/s07" src="images/skill-invocation.svg" label="放大独立总图的 C：用户点名与模型选择两种调用入口" caption="局部图 C：两种入口汇合在调用与装载边界。这里只展开谁发起、是否允许以及交给哪个会话；不会把整个 Agent Loop 再画一次。" >}}

用户可以明确点名：

```text
/review-diff
```

也可以提出任务：

```text
帮我检查这次未提交改动，重点找可能改变行为的缺陷。
```

第二条路径中，Claude 根据任务与 Skill 描述判断是否相关，再发起技能调用。描述帮助选择，但自然语言匹配会受措辞和当前上下文影响，不能保证所有相关请求都触发。

手动调用已经指定了 Skill，因此只能验证它能否运行；要判断自动选择是否可靠，必须另外使用自然语言任务测试。

## 描述要提供哪些信息

描述应该能回答“做什么、什么时候用”。例如：

```yaml
description: 检查当前 Git 仓库的未提交改动。用户要求审查 diff、排查改动风险或检查这次修改时使用。
```

这比“帮助写出高质量代码”更容易判断任务是否匹配。我的写作原则是把真正的使用场景放在前面，避免把所有相关关键词都堆进去；否则一个审查 Skill 可能连普通概念解释也抢着接管。

## 两个开关分别控制什么

下面每行都是一种独立配置：

| 配置 | 用户能用 `/name` | 模型能主动调用 | 描述默认进入模型目录 |
|------|------------------|----------------|----------------------|
| 默认 | 能 | 能 | 会 |
| `disable-model-invocation: true` | 能 | 不能 | 不会 |
| `user-invocable: false` | 不能 | 能 | 会 |

[官网调用控制](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill)说明了这些差异。一个字段控制模型发起，另一个控制用户命令入口；它们不是互相替代的同义词。

若把本例改为只由我启动，可以加：

```yaml
disable-model-invocation: true
```

这时期待它从“帮我检查改动”中自动触发，就与配置矛盾。

## 调用还要经过应用侧检查

模型认为相关并不等于应用一定允许启动。Skill 工具本身的权限规则、组织策略或技能可见性配置，都可能让请求被拒绝。失败发生在调用入口时，正文可能尚未被加载，不能据此判断正文写得不好。

因此排查顺序是：当前会话是否发现该 Skill → 当前调用者是否能调用 → 请求是否被允许 → 正文是否成功装载。

## 我的理解

目录描述让模型知道有哪些可选方法；自动匹配由模型判断，调用边界由应用配置处理。想要特定方法时，我可以直接点名；想检验它能否自己找对方法，就必须测试自动调用路径。

[上一节]({{< relref "/projects/learn-claude-code/s07/02-discovery.md" >}}) · [下一节：正文什么时候进入上下文]({{< relref "/projects/learn-claude-code/s07/04-context.md" >}})
