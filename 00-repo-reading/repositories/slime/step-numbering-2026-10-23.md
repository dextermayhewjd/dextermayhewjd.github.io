# 2026-10-23 · 新增结果收集步骤后的编号对照

[项目入口](README.md) · [当前接续](../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

用户要求把运行统计与补丁提取作为新的 Step 2，先读清各自发生的事情，再进入独立评测，并明确选择“整体顺延为 Step 003–009，修复导航并保留旧版内容与历史（推荐）”。当前步骤入口使用下表编号。

| 原编号与主题 | 当前编号与入口 |
| --- | --- |
| Step 000 · 整体骨架 | [Step 000 · 整体骨架](topics/01-coding-agent-rl/steps/step-000-coding-agent/README.md) |
| Step 001 · 模型请求 | [Step 001 · 模型请求](topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/README.md) |
| 本次新增 | [Step 002 · 运行统计与补丁提取](topics/01-coding-agent-rl/steps/step-002-agent-results/README.md) |
| Step 002 · 独立评测 | [Step 003 · 独立评测](topics/01-coding-agent-rl/steps/step-003-swe-evaluation/README.md) |
| Step 003 · 轨迹与样本 | [Step 004 · 轨迹与样本](topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/README.md) |
| Step 004 · 会话准备 | [Step 005 · 会话准备](topics/01-coding-agent-rl/steps/step-005-agent-preparation/README.md) |
| Step 005 · 执行沙箱 | [Step 006 · 执行沙箱](topics/01-coding-agent-rl/steps/step-006-agent-sandbox/README.md) |
| Step 006 · 工作区准备 | [Step 007 · 工作区准备](topics/01-coding-agent-rl/steps/step-007-prepare-workspace/README.md) |
| Step 007 · Harness 启动与等待 | [Step 008 · Harness 启动与等待](topics/01-coding-agent-rl/steps/step-008-harness-communication/README.md) |
| Step 008 · HTTP 接收入口 | [Step 009 · HTTP 接收入口](topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/README.md) |

## 历史记录怎样解释

- 当前项目索引、步骤 README、scope 与 overview 的导航编号已顺延；目录链接指向现位置。
- 历史 flow、task flow、函数卡片的首次接触与来源说明、用户原话，继续保留当时的 Step 编号。通过上表定位现目录，不把历史改写成当时已有新 Step 2。
- skill 中的“Step 003 主要 reference”和“Step 007 调用层级 reference”是固定样例的历史名称，文件名与正文保留；对应原始步骤现在分别位于 Step 004 与 Step 008。指向目录的链接已更新。
- 原 Step 002–008 的 `03` 仍是当时的累计快照，没有因插入新步骤批量重算。后续逐步校准时再合并当前前序记忆；新 Step 002 已完整继承本轮 Step 001 的 20 份记录。

编号变化只表示阅读安排调整，不改变源码版本、阅读事实或用户掌握状态。具体新增范围与原话见[本步记录](topics/01-coding-agent-rl/steps/step-002-agent-results/04-flow.md#scope-confirmation)。
