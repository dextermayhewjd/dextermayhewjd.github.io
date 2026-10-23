# Step 7 · 准备任务工作区

**目录编号调整**：本目录由原 Step 006 顺延而来；历史过程、函数来源和固定样例里的原编号保留当时语境，见[新旧编号对照](../../step-numbering-2026-10-23.md)。本次不改写原源码版本或学习结论。

[前一步：启动执行沙箱](../step-006-agent-sandbox/README.md) · [当前阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

前一步已取得安装好 CLI 的沙箱对象 `sb`。本步围绕 `swe.prepare_workspace`，弄清现有工作目录如何接住任务配置与题目内容，交给后续 Agent 使用。

- [01 · 阅读范围](01-scope.md)：继承整体骨架，展开第 3 项工作区准备及返回位置。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：记录 `prepare_workspace`，并展开 `ensure_agent_user`、`apply_before_repo_set_cmd` 与 `apply_pre_commands`。
- [03 · 前序记忆](03-long-term-memory/overview.md)：完整合并 Step 6 的 `03 + 02`，共 35 份函数与类记录，包含引用入口。
- [04 · 问题与解释](04-flow.md)：保存本轮确认、初次讲解与后续反馈。
- [05 · 阅读后的任务总结](05-task-flow.md)：本步读通后再整理。

输入背景统一从 [md：工作区准备要使用的题目资料](references/metadata.md) 开始，包括 `grading`、两类准备配置、`problem_statement` 及字段来源；具体值对照[真实题目](references/scaleswe-auth0-example.md)。

用户后续提出的 Harness 启动与跨组件通信问题已独立为 [Step 8](../step-008-harness-communication/README.md)。本步保留工作区准备及其未收束项；通信说明与后续阅读放入新步骤，原始追问的迁移位置见 [flow](04-flow.md#run-cross-process-communication)。

源码沿用 `/home/hongshi/projects/slime` 的固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。建立记录与继承材料不表示用户已经理解本函数的全部实现。
