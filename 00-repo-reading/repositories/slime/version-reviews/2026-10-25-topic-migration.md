# 2026-10-25 · Slime 步骤按主题迁移

用户确认采用“仓库 → 主题 → 步骤”的组织方式。当前已建立 [Coding Agent RL 主题](../topics/01-coding-agent-rl/README.md)，其余主题仅在项目入口中作为规划列出。

## 迁移范围

- 原位置：`00-repo-reading/repositories/slime/steps/`。
- 新位置：`00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/`。
- Step 000–009 共 10 个步骤，473 个文件（457 个 Markdown、16 个 JSON）。
- 原编号、内部目录、原话、未知、源码版本及记忆内容保留；修改文件链接与四处 JSON 记录路径以适应新位置。
- 项目入口改为主题导航；迁移前完整入口保存在[历史快照](2026-10-25-project-entry-before-topics.md)。

## 接续规则

- 下一实际步骤继续用 Step 010，不在主题内重新从 000 编号。
- 跨主题仍继承前一步的 03 + 02，不新增主题级 memory，不将迁移记为掌握。
- 主题 README 维护范围与索引，当前进度仍只在[原唯一路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。

## 验证

- 已对照迁移前备份检查全部 473 个文件。457 份 Markdown 的正文、原话、未知和版本信息保持一致，仅重算链接目标；16 份 JSON 保留数据，仅其中一份的四个文档路径随目录更新。
- 迁移阶段共重算 1,187 处链接，包括 10 份 skill 文档的引用；一份 skill reference 中原先层级不正确的五个链接也已定位并修正。
- 检查 6,268 处本地引用，无新增缺失链接，活动链接不再指向旧 steps 根目录。既有的外部环境资源路径与模板示例按原来源保留。
- `git diff --check` 通过。
- `python3 -m unittest discover -s tests -p 'test_slime_chapters.py'`：20 项通过；该检查使用 Hugo 0.166.0 构建并校验现有 Slime 页面、导航、源码引用及保留材料。
- 仅建立 `topics/01-coding-agent-rl/`，未预建后续主题或 Step 010；迁移不改变此前的学习与真实运行状态。
