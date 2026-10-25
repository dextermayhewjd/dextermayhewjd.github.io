# Step 7 · 准备任务工作区

**目录编号调整**：本目录由原 Step 006 顺延而来；历史过程、函数来源和固定样例里的原编号保留当时语境，见[新旧编号对照](../../../../step-numbering-2026-10-23.md)。本次不改写原源码版本或学习结论。

[前一步：启动执行沙箱](../step-006-agent-sandbox/README.md) · [当前阅读进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

前一步已取得安装好 CLI 的沙箱对象 `sb`。本步围绕 `swe.prepare_workspace`，弄清现有工作目录如何接住任务配置与题目内容，交给后续 Agent 使用。

**2026-10-24 当前材料**：[scope](01-scope.md)与 [prepare_workspace 父卡](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md)已对齐 `18868a79`，入口为 `_generate:285 → prepare_workspace:187–209`。三张辅助卡也已按实际变化更新，父卡和 scope 直接链接本步记录；题目写入与 `baseline` 交接继续保存在父卡。旧 scope、父卡和三张辅助卡均完整归档，输入参考尚未逐项校准。

本步新增的 [_repository_tree](02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_repository_tree.md)记录与[任务总结](05-task-flow.md)现已接入，汇总准备效果、初始快照与调用方的交接。Git 内部和并发等待深入问题继续保留，当前阅读状态以唯一路线为准。

- [01 · 阅读范围](01-scope.md)：继承整体骨架，定位第 3 项工作区准备、题目写入与 `baseline` 返回。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：记录 `prepare_workspace`，并展开 `ensure_agent_user`、`apply_before_repo_set_cmd`、`apply_pre_commands` 与生成快照的 `_repository_tree`。
- [03 · 前序记忆](03-long-term-memory/overview.md)：保留原进入本步时合并 Step 6 的 `03 + 02` 快照，共 35 份函数与类记录；本次未刷新继承。
- [04 · 问题与解释](04-flow.md)：保存本轮确认、初次讲解与后续反馈。
- [05 · 阅读后的任务总结](05-task-flow.md)：接住已有沙箱、按配置准备工作区、写题目并交回 `baseline`。

输入背景统一从 [md：工作区准备要使用的题目资料](references/metadata.md) 开始，包括 `grading`、两类准备配置、`problem_statement` 及字段来源；具体值对照[真实题目](references/scaleswe-auth0-example.md)。

用户后续提出的 Harness 启动与跨组件通信问题已独立为 [Step 8](../step-008-harness-communication/README.md)。本步保留工作区准备的总结与待深入问题；通信说明与后续阅读放入相应步骤，原始追问的迁移位置见 [flow](04-flow.md#run-cross-process-communication)。

当前 scope 与五张函数卡使用 `/home/fredkeira/projects/slime` 的 `18868a79` 定位；独立教学场景、输入参考、历史稿与继承快照保留各自来源。旧资料中的 `None` 返回、脚本路径和行号属于原版本；源码讲解与个人理解反馈分别记录。
