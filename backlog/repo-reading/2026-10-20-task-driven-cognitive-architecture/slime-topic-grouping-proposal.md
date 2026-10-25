# Slime 阅读记录：主题分组方案

记录日期：2026-10-25。用户已确认本方案；Step 000–009 已迁入第一个主题，编号与记忆继承规则保留。实施范围见[迁移记录](../../../00-repo-reading/repositories/slime/version-reviews/2026-10-25-topic-migration.md)。

[返回制度讨论](README.md) · [Slime 阅读入口](../../../00-repo-reading/repositories/slime/README.md) · [当前模块阅读顺序](../../../00-repo-reading/repositories/slime/slime后续阅读顺序/current-goal-slime-reading-order.md)

## 1. 主题放在 step 上一层

建议采用“仓库 → 阅读主题 → 既有 step → 函数/类记录”的层次。主题说明正在解决哪一类框架问题；step 保留每次阅读形成认识的实际顺序；源码路径说明依据在哪里。

这三种信息分别表达。一个阅读主题可以跨多个源码目录，同一个源码文件也可以在后续不同主题中被再次使用。

## 2. Step 000–009 归入第一个主题

建议名称：**Coding Agent RL：generate 主线与 agent 组件**。

- **核心问题**：一道代码任务怎样获得运行环境、驱动 Agent、调用模型、产生补丁、获得评分并交出 Sample。
- **主入口**：`examples/coding_agent_rl/generate.py::generate → _generate`。
- **主要支撑实现**：`slime/agent/` 下的 Harness、Adapter、Sandbox 与轨迹管理。
- **任务实现**：`examples/coding_agent_rl/swe.py`、沙箱适配等。
- **步骤范围**：现有 Step 000–009，保留原编号、内容、来源和明确未知。正常主线已覆盖不等于整个 `slime/agent/` 都已读完；外层失败/最终清理等既有待回查项继续保留。

`generate` 与 `agent/` 适合作为主题入口页中的“主入口”和“相关目录”，不必把现有步骤再拆成两个独立主题。例如 Step 005 的服务准备同时涉及两处代码，拆开会打断同一条对象交接。

## 3. 后续主题按问题划分

| 拟议主题 | 主要代码入口 | 对应问题 |
| --- | --- | --- |
| 01 · Coding Agent RL | coding_agent_rl/generate.py、swe.py、slime/agent/ | 单题执行、评测与样本产出 |
| 02 · Rollout 接入与奖励 | sglang_rollout.generate_and_rm、rm_hub | 自定义生成与评分怎样接入框架，结果契约是什么 |
| 03 · 批量生成与调度 | generate_and_rm_group、fully_async_rollout | 多轨迹、持续生成、队列、取消与结果完整性 |
| 04 · 训练数据与更新 | BatchBuilder、RolloutManager、train.py | Sample 怎样进入训练，训练与生成权重怎样衔接 |

主题 02–04 是对既有后续模块计划的分组，实际开始时再建立。测试、Trace 与 Kubernetes 实践按正在解决的问题关联到相应主题。

## 4. 目录与编号建议

下面是目标结构。当前已建立第一个主题并迁入既有步骤；02–04 仍是规划，实际展开时再创建：

```text
repositories/slime/
├─ README.md
└─ topics/
   ├─ 01-coding-agent-rl/
   │  ├─ README.md
   │  └─ steps/
   │     ├─ step-000-coding-agent/
   │     ├─ step-001-harness-to-adapter/
   │     ├─ ...
   │     └─ step-009-adapter-request-entry/
   ├─ 02-rollout-reward/
   ├─ 03-rollout-scheduling/
   └─ 04-training-handoff/
```

- step 内的 `01-scope`、`02`、`03`、`04-flow`、`05-task-flow` 保持既有职责。
- 旧 Step 000–009 不改号；下一次实际展开的步骤继续用 Step 010。主题编号与步骤编号各有用途。
- 主题 README 只放核心问题、主入口、相关源码目录和所属步骤索引；当前进度仍只维护在 `repo-reading-route.md`。
- 主题不是新的记忆层。跨主题继续沿用已确认的 `上一 step 的 03 + 02 → 下一 step 的 03`；完整来源与未知不因换主题而清空。

## 5. 已采用的迁移边界

现有 Step 000–009 整体迁入 `topics/01-coding-agent-rl/steps/`，共 473 个文件。目录变化只增加父级分组，学习正文、原话、未知、认识日期与源码版本保留；链接、项目入口及读取路径的规则一起校正。

项目 README 改为主题导航，第一个主题的 README 保存问题、源码范围和步骤索引。下一步仍从 Step 010 继续；迁移不等于新主题已开始，也不表示已有未解问题已掌握。

<details>
<summary>用户的原始问题</summary>

用户随后确认：

> 好的那么就按照这个方式来构建吧

最初的问题：

> 那么在继续之前考虑一下 当前的step是否需要拆分一下?
> 也就是作为一系列主题?
> 比如当前的step0到9是和coding agent rl相关的?
>
> 那么是否考虑一下变成为按照主题的分离呢?
> 之前可以变成为coding agent rl/generate(主要阅读函数) + agnet(folder)

</details>
