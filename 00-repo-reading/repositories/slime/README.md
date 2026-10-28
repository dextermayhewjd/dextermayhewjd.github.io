# Slime：按主题推进源码阅读

[通用方法](../../README.md) · [工作流](../../workflow.md) · [当前进度与下一步](../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

阅读目标是对齐用户提供的腾讯混元 Agent 强化学习框架工程师岗位，以理解框架和实际交接为主。岗位要求与投入安排见[岗位对照](../../../slime_photo/code-reading/job-alignment.md)。

## 源码与记录入口

- 源码仓库：`/home/hongshi/projects/slime`；历史记录保留当时路径，现有校准材料使用 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，旧材料保留各自版本。
- 学习状态只维护在[唯一路线的当前接续](../../../slime_photo/code-reading/repo-reading-route.md#当前接续)，主题与步骤索引不另存一套进度。
- 后续方向统一按 [2026-10-28 阅读计划与约定](slime后续阅读顺序/current-goal-slime-reading-order.md#reading-agreement-20261028)接续；方案与选题依据见[后续阅读目录](slime后续阅读顺序/README.md)，实际进度只看唯一路线。

## 阅读主题

| 主题 | 核心问题与源码入口 | 记录入口 |
| --- | --- | --- |
| 01 · Coding Agent RL：generate 主线与 agent 组件 | 单题怎样运行、评测并交付样本；`coding_agent_rl/generate.py`、`swe.py` 与 `slime/agent/` | [主题入口与 Step 000–009](topics/01-coding-agent-rl/README.md) |
| 02 · Rollout 接入与奖励 | 单任务与组级生成、评分、持续调度、完成结果交付与自定义生成接口、训练数据转换；`generate_and_rm`、`generate_and_rm_group`、`AsyncRolloutWorker` | [主题入口与 Step 010–013、015–016](topics/02-rollout-reward/README.md) |
| 03 · Trace 与运行诊断 | 执行阶段怎样留下可关联的记录，怎样观察耗时和诊断问题；`trace_span` | [主题入口与 Step 014](topics/03-trace-diagnostics/README.md)，暂缓研究；状态见唯一路线 |
| 04 · 训练数据与更新 | Sample 怎样进入训练，权重怎样交回生成侧；`BatchBuilder`、`RolloutManager`、`train.py` | 规划项，实际展开时建立 |

主题按要解决的问题划分。同一主题可以涉及多个源码目录，同一个源码文件也可以在不同主题中按需阅读。

## 步骤与记忆怎样接续

- 步骤保存在 `topics/<主题>/steps/step-NNN-<问题>/`；Step 000–009 保留原编号，第二主题从 Step 010 继续，不因切换主题重新编号。
- 每步内部继续使用 scope、短期记忆、长期记忆、理解过程与 task flow。新增主题不增加一套主题级 memory，也不清空此前认识。
- 跨主题仍按“前一步 03 + 02 → 下一步 03”继承，完整保留来源、原话和未知；开始新步骤仍先确认具体问题与范围。
- 测试、Trace 与 Kubernetes 实践跟随相应任务展开；创建目录、迁移或整理文件不表示已经掌握或运行。

## 资料与历史

- [源码索引](../../../slime_photo/code-reading/code-reading-list.md)与[框架全景正文](../../../slime_photo/code-reading/chapters/00-overview/walkthrough.md)用于定位，不能代替具体主题的阅读边界。
- [源码版本影响](version-reviews/2026-10-23-2f231865-to-18868a79.md)、[卡片版本盘点](version-reviews/2026-10-23-step-card-audit.md)。
- [2026-10-23 步骤编号对照](step-numbering-2026-10-23.md)保留此前顺延历史。
- [主题迁移记录](version-reviews/2026-10-25-topic-migration.md)与[迁移前的完整项目入口](version-reviews/2026-10-25-project-entry-before-topics.md)。
