# Slime：按目标逐步建立整体模型

[通用方法](../../README.md) · [工作流](../../workflow.md)

用户的阅读目标是准备其提供的腾讯混元 Agent 强化学习框架工程师岗位。以理解框架为主，本地没有 GPU，希望用模型 API 辅助验证；按岗位责任取舍深度。完整目标和初始投入建议继续保存在[岗位对照](../../../slime_photo/code-reading/job-alignment.md)，不在这里复制一份。

本轮已确认阅读方向是 Coding Agent / Coding RL。Step 0 建立核心骨架，Step 1 读模型请求，Step 2 读独立评测，Step 3 读会话轨迹与奖励怎样交成样本，Step 4 回补 `open_session` 的会话配置登记。Step 5 已收拢执行沙箱的准备、交付与回收，Step 6 记录 `swe.prepare_workspace` 的任务工作区准备，Step 7 按用户确认独立研究 Harness 启动及沙箱、Adapter、SGLang 之间的通信。每个后续 step 仍先一起确认具体问题与函数范围；具体掌握与运行状态以唯一路线为准。

## 源码与唯一记录入口

- 已确认的本地源码：`/home/hongshi/projects/slime`；本轮固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。历史材料保留各自版本。
- 当前进度与下一步：[阅读路线的当前接续](../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。
- 连贯技术正文：[00 全景 walkthrough](../../../slime_photo/code-reading/chapters/00-overview/walkthrough.md)，其 [Hugo 页面](http://localhost:1313/projects/slime/framework-walkthrough/)从同一文件渲染。
- 模块与函数资料：[现有源码索引](../../../slime_photo/code-reading/code-reading-list.md)。00–07 和 4.1 是资料分组；本目录步骤是理解形成的先后，两者不混用。

## 步骤索引

| 步骤 | 本步核心问题 | 记录 |
| --- | --- | --- |
| 007 · 当前 | Harness 怎样启动 CLI，信息怎样在沙箱、Adapter 与 SGLang 之间往返？ | [步骤入口](steps/step-007-harness-communication/README.md) |
| 006 · 前序 | 已有沙箱怎样接住工作区配置与题目内容？ | [步骤入口](steps/step-006-prepare-workspace/README.md) |
| 005 · 前序 | 任务的镜像怎样变成供 Agent 使用的执行沙箱？ | [步骤入口](steps/step-005-agent-sandbox/README.md) |
| 004 · 前序 | open_session 怎样按 sid 登记本次执行的会话配置？ | [步骤入口](steps/step-004-agent-preparation/README.md) |
| 003 · 前序 | 会话轨迹如何结合奖励与基础样本，导出 Sample 列表？ | [步骤入口](steps/step-003-trajectory-to-samples/README.md) |
| 002 · 前序 | 代码改动如何在独立环境中被评测，并得到奖励？ | [步骤入口](steps/step-002-swe-evaluation/README.md) |
| 001 · 前序 | 从 Harness 定位到 Adapter 后，一次模型请求怎样被处理？ | [步骤入口](steps/step-001-harness-to-adapter/README.md) |
| 000 · 前序 | 理解 Coding Agent，定位指挥官函数并提取核心骨架 | [步骤入口](steps/step-000-coding-agent/README.md) |

旧 `initial-model` 已移出当前步骤目录，仅在[历史归档](../../../backlog/repo-reading/archived-steps/README.md)保留。Coding Agent 与 Harness 到 Adapter 两步作为前序继续保留，原目录纠正见[历史讨论](../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#keep-coding-agent-archive-initial-model)。

Step 0 的三项 scope 见[整体阅读范围](steps/step-000-coding-agent/01-scope.md)，两层 memory 暂无函数卡片。Step 1 的[当前阅读范围](steps/step-001-harness-to-adapter/01-scope.md)给出 `_run_turn` 的流程；`02` 保存移入的转换记录、新建的 `_run_turn` 记录与原有 Harness 记录，`03` 暂无前序函数可继承。助手讲解不等于用户已掌握全部实现。

Step 2 的 [scope](steps/step-002-swe-evaluation/01-scope.md)继承整体骨架后展开第 6 项评测；`02` 保存本步评分函数，`03` 完整继承 Step 1 的 17 份函数记录。原步骤和已认可的 skill reference 保留原文。

Step 3 的 [scope](steps/step-003-trajectory-to-samples/01-scope.md)接到第 7 项样本导出；`02` 从 `BaseAdapter.finish_session` 开始，`03` 合并 Step 2 的 `03 + 02`，共 24 份函数记录。[阅读后的任务总结](steps/step-003-trajectory-to-samples/05-task-flow.md)连接前序轨迹、评测奖励与样本导出，保留组装算法和外层清理的后续问题；不把总结等同于全部实现已读。

Step 4 的 [scope](steps/step-004-agent-preparation/01-scope.md)继承完整骨架，围绕第 1 项会话登记，回查 Adapter 对象与执行编号的来源；`03` 合并 Step 3 的 `03 + 02`，共 27 份函数记录，`02` 保存 `_AdapterService.__init__`、`_session_id` 与 `BaseAdapter.open_session` 三份函数卡片，以及 [Session 类卡片](steps/step-004-agent-preparation/02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md)。服务初始化卡片保留整体职责，当前只展开 Adapter 创建与保存；编号卡片解释实际读取的字段与三种返回规则；类卡片解释每次执行的配置对象。[task flow](steps/step-004-agent-preparation/05-task-flow.md)已收拢对象来源、编号与配置登记，并接回后续取用；保留题目信息与会话配置的边界澄清。环境与工作区准备仅在骨架中定位，作为后续候选。

Step 5 的 [scope](steps/step-005-agent-sandbox/01-scope.md)继承完整骨架，聚焦第 2 项启动执行沙箱；`02` 保存 [boot_agent_sandbox](steps/step-005-agent-sandbox/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md) 的准备、交付与退出回收模型，以及 [E2BSandbox 类卡片](steps/step-005-agent-sandbox/02-short-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)的状态、本地与远端关系和操作入口；安装过程统一见 [install_npm_cli 主记录](steps/step-005-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)，[ClaudeCodeHarness.install_cli](steps/step-005-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md)保留为参数适配与委托的引用入口。`03` 合并 Step 4 的 `03 + 02`，共 30 份函数记录与 1 份类记录。范围确认、类与函数的解释保存在本步 flow；[task flow](steps/step-005-agent-sandbox/05-task-flow.md)已收拢镜像输入、CLI 就绪、交出 sb、调用方使用与退出回收，底层等待和完整故障恢复留待按需深入。

Step 6 的 [scope](steps/step-006-prepare-workspace/01-scope.md)继承完整骨架并展开第 3 项工作区准备；`03` 完整合并 Step 5 的 35 份记录，`02` 保存 [prepare_workspace](steps/step-006-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md) 的整体交接、[ensure_agent_user](steps/step-006-prepare-workspace/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) 的用户与目录准备，以及 [apply_before_repo_set_cmd](steps/step-006-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md)、[apply_pre_commands](steps/step-006-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md) 的配置命令、脚本写入和执行。本步 task flow 待阅读后整理。

Step 7 的 [scope](steps/step-007-harness-communication/01-scope.md)保留整体七项骨架，展开第 4 项的本地启动与运行期间的三条通信路径。`03` 合并 Step 6 的 `03 + 02` 为 38 份记录，`02` 保存 `BaseHarness.run`、`ClaudeCodeHarness.write_config` 与 `ClaudeCodeHarness.launch_and_wait` 三张函数卡片，以及 [HarnessContext 类卡片](steps/step-007-harness-communication/02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)；[通信参考](steps/step-007-harness-communication/references/run-communication-path.md)由 Step 6 迁入，原始问题和归属纠正完整保留在新步骤 flow。新步骤建立不代表前序未收束内容或本步机制已掌握。

新步骤按 `01-scope.md`、`02-short-term-memory/`、`03-long-term-memory/`、`04-flow.md` 保存范围、本步新认识、前序累计模型与理解过程。两层记忆都镜像 Slime 源码目录，例如 `functions/slime/ray/rollout.py/RolloutManager.generate.md`；字段见[统一规范](../../memory-format.md)。下一步合并上一份 `03` 与 `02`，旧步骤保留当时的理解和目录。
