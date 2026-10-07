---
title: "S07.2 Discovery：放在哪里决定谁能用"
weight: 20
summary: "看清个人、项目、嵌套目录和插件 Skill 的发现方式，以及名称冲突的处理。"
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
---

在 [Skills 独立总图]({{< relref "/projects/learn-claude-code/s07/_index.md" >}}#skills-map) 中，本节对应 **B 可见目录**。这一节解释系统发现范围与调用者可见性；发现不等于调用。

本节的项目来源探针及发现实验、文件位置与实验步骤见 [S07.10 完整示例附录]({{< relref "/projects/learn-claude-code/s07/10-appendix.md" >}}#lab-project-claude-skills-origin-probe-skill-md)。

## 我想弄清楚的问题

写好 `SKILL.md` 后，Claude Code 怎样知道它存在？同一份 Skill 换个目录，能使用它的会话也可能改变。

## 先从项目级示例出发

我们的文件位于：

```text
my-repo/
└── .claude/
    └── skills/
        └── review-diff/
            └── SKILL.md
```

这是项目级 Skill，适合随源码提交并共享审查方法。放到个人目录则供这台机器的多个项目使用。

| 来源 | 代表位置 | 适合的用途 |
|------|----------|------------|
| 项目 | `.claude/skills/review-diff/SKILL.md` | 仓库内的约定 |
| 个人 | `~/.claude/skills/review-diff/SKILL.md` | 自己跨项目复用 |
| 嵌套项目目录 | `apps/web/.claude/skills/...` | 某个包的专用方法 |
| 插件 | 插件中的 `skills/` | 打包分发，带插件命名空间 |
| 组织管理 | 管理配置目录中的技能 | 团队统一配置 |

[官网加载位置说明](https://code.claude.com/docs/en/skills#choose-where-skills-load)还包含额外目录和账号同步等来源。这里抓住的关系是：**文件来源决定作用范围，发现后才有可调用的 Skill 条目。**

## 嵌套目录为什么可能晚一点出现

项目根部的 Skill 与子目录专用 Skill 可以分别维护。当前官网说明：会话启动时会搜索启动目录及其上层的项目配置；更深目录里的 Skill 会在处理该目录文件时被发现，也可通过添加目录提前加载。

因此，“文件已经在磁盘上”和“当前会话已经发现它”是两种状态。排查找不到 Skill 时，先检查会话所在位置，再检查配置来源，而不是马上修改描述。

[依据：monorepo 与子目录加载](https://code.claude.com/docs/en/skills#load-skills-in-monorepos-and-subdirectories)。

## 同名时哪个版本生效

假设个人目录和项目目录都有 `review-diff`。普通同名来源之间，当前 Claude Code 的优先级是组织管理高于个人、个人高于项目；插件通过命名空间保留独立名称。嵌套目录的同名 Skill 还可通过目录限定名称区分。

这解释了一个常见现象：改了仓库里的文件，调用时却得到另一套指令。调用名称相同，不代表来源相同。应核对实际加载的条目。[依据：同名解析](https://code.claude.com/docs/en/skills#resolve-skills-that-share-a-name)。

## 怎样观察发现结果

在 Claude Code 里查看：

```text
/skills
```

本地文件存在只是第一份证据；技能菜单里能找到条目，则说明当前会话已发现它。接下来还要看调用可见性和权限配置。

另外，云端会话不会自动读取你电脑上的个人目录。项目技能需要存在于云端克隆的仓库，账号同步和插件也有各自规则。这属于来源分发问题，不能用“本机能看到”推断“所有运行环境都能看到”。

## 我的理解

Skill 的发现相当于建立可用目录。路径、来源和命名规则决定目录里究竟是哪一份内容，后面的模型匹配只能在实际可见的条目上发生。

[上一节]({{< relref "/projects/learn-claude-code/s07/01-structure.md" >}}) · [下一节：谁决定调用]({{< relref "/projects/learn-claude-code/s07/03-invocation.md" >}})
