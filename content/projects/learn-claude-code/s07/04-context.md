---
title: "S07.4 Progressive Disclosure：区分磁盘、应用内存和模型上下文"
weight: 40
summary: "跟踪描述、正文、参考文件的可见时间，解释加载后的保留、重复调用和压缩。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

在 [Skills 独立总图]({{< relref "/projects/learn-claude-code/s07/_index.md" >}}#skills-map) 中，本节对应 **D 正文交付 / F 按需资源**。只追踪内容何时进入模型上下文，暂不展开执行会话内部。

本节的按需读取的参考文件、文件位置与实验步骤见 [S07.10 完整示例附录]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}}#lab-project-claude-skills-review-diff-references-input-boundaries-md)。

## 我想弄清楚的问题

“按需加载”到底是在说晚一点读磁盘，还是晚一点把内容发给模型？我理解 Skills 时，最容易混淆的就是这两件事。

渐进式披露的重点是模型的上下文可见性。[Agent Skills 规范](https://agentskills.io/specification#progressive-disclosure)把它分成元信息、技能指令和配套资源三个层次。

## 用 review-diff 跟踪三层内容

{{< architecture from="/projects/learn-claude-code/s07" src="images/progressive-disclosure.svg" label="放大 D 与 F：名称描述、完整正文和按需资源分层进入上下文" caption="这里按模型可见内容分层：目录帮助选择，调用后获得正文，执行中再取所需资源。图中的三个层次不等于三次固定的磁盘读取。" >}}

| 阶段 | 模型得到什么 | 还没有默认得到什么 |
|------|--------------|--------------------|
| 可用目录 | 名称和用途描述 | 完整审查步骤 |
| 调用 Skill | `SKILL.md` 中的主流程 | 所有配套参考文件 |
| 任务需要更多细节 | 实际读取的参考内容，或脚本输出 | 没有取用的其他资料 |

`SKILL.md` 本身被调用时会完整装载。它不会因为包含多个标题就自动只加载其中一段；要让大块细节晚一点进入上下文，需要把它们放到单独文件，并在正文里说明什么时候取用。

## 配套资料怎样继续披露

扩展我们的目录：

```text
review-diff/
├── SKILL.md
├── references/
│   ├── input-boundaries.md
│   └── concurrency.md
└── scripts/
    └── inspect-diff.sh
```

在主文件中写清楚路由：

```markdown
## 需要时读取的资料

- 改动涉及空输入、类型转换或默认值时，读 references/input-boundaries.md。
- 改动涉及共享状态或异步执行时，读 references/concurrency.md。
```

两份资料不需要随每次调用全部进入上下文。Claude 要进一步了解输入边界时，再用文件工具读取第一份。脚本可以直接运行，模型通常看到的是执行结果；运行程序不会自动把全部源码当作参考文本注入。

第一份参考文件可以写得很具体：

```markdown
## 输入边界检查

- 空列表、空字符串、缺失字段分别会走哪条分支？
- 调用方约定的是返回默认值，还是明确报错？
- 如果默认值改变，哪些调用方会受到影响？

报告问题时，给出具体输入和导致错误的表达式。
先核对项目已有约定，不把偏好的编码风格当成行为缺陷。
```

这份文件扩展的是审查方法。主流程已经指定了取用条件，模型碰到相关改动时才需要它；目录名称本身不会自动触发读取。

我的设计重点是：目录描述负责发现，主文件负责主要步骤与资源入口，参考文件承载当前任务才需要的细节。

## 程序已经读过文件，不代表模型已看到

当前本地教学版的 `SkillLoader.scan()` 会把完整文件内容读入 `self.skills`。下面按源码保留关键字段：

```python
self.skills[name] = {
    "name": name,
    "description": description,
    "content": content,
}
```

但 `catalog()` 只取名称和描述；`load_skill` 才把完整文件作为工具结果回传到 `messages`。所以这份代码的“延迟”发生在模型上下文层，而非第一次读磁盘的时刻。它缓存并返回的是完整 `SKILL.md` 文件，包含 frontmatter；现代产品的正文处理另按官方说明理解。

对现代 Claude Code，我按官网确认的是“描述先可见、正文调用时装载”，不据此猜测内部每一次磁盘读取或缓存的时机。

## 加载之后会不会立刻消失

[官网内容生命周期](https://code.claude.com/docs/en/skills#skill-content-lifecycle)说明，装载后的正文作为消息保留在对话中，后续轮次继续参考。再次调用相同渲染内容会避免重复注入；参数或动态输出改变，则可能产生新内容。

自动压缩会按预算保留已调用技能，不能把它理解为所有正文永远完整保留。持续保留内容也有上下文成本，所以主文件仍应集中表达必要步骤。

正文留在上下文中，与调用时的临时工具授权是两种生命周期。下一节讨论内容如何渲染，第六节再区分这些权限。

## 我的理解

渐进式披露控制的是“模型现在需要看到多少”。Skill 被发现、程序缓存了正文、模型读到了正文，是三个不同状态；只有分清它们，才能解释为什么这种组织能节省上下文。

[上一节]({{< relref "/projects/learn-claude-code/s07/03-invocation.md" >}}) · [下一节：参数与动态信息]({{< relref "/projects/learn-claude-code/s07/05-rendering.md" >}})
