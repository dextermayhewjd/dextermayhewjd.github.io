# Slime：按目标逐步建立整体模型

[通用方法](../../README.md) · [工作流](../../workflow.md)

用户的阅读目标是准备其提供的腾讯混元 Agent 强化学习框架工程师岗位。以理解框架为主，本地没有 GPU，希望用模型 API 辅助验证；按岗位责任取舍深度。完整目标和初始投入建议继续保存在[岗位对照](../../../slime_photo/code-reading/job-alignment.md)，不在这里复制一份。

本轮已确认阅读方向是 Coding Agent / Coding RL。Step 0 建立核心骨架，Step 1 读模型请求，新增 Step 2 单独读运行统计与补丁提取，Step 3 读独立评测，Step 4 读会话轨迹与奖励怎样交成样本，Step 5 回补 `open_session` 的会话配置登记。Step 6 已收拢执行沙箱的准备、交付与回收，Step 7 记录 `swe.prepare_workspace` 的任务工作区准备，Step 8 收拢 Harness 启动与等待，Step 9 按用户确认单独补清 CLI 的 HTTP 请求怎样进入 Adapter。每个后续 step 仍先一起确认具体问题与函数范围；具体掌握与运行状态以唯一路线为准。

2026-10-23 插入新 Step 2 后，原 Step 002–008 已顺延为 Step 003–009。历史原话、过程和固定 skill reference 保留当时编号，见[新旧编号对照](step-numbering-2026-10-23.md)；后续步骤的原记忆快照暂不批量重算。

## 源码与唯一记录入口

- 已确认的本地源码：`/home/hongshi/projects/slime`；2026-10-23 实测 checkout 与官方 main 为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。Step 0、Step 1 scope 已按新版校准并保存旧稿；Step 1 已校准 `_translate`、`_render_token_ids`、`call_sglang_generate`、`parse_model_output`、`_build_reply`、`_respond`、`TrajectoryManager.record_turn`，新增 `_session_prompt_ids`、`trace_span` 卡片，Step 1 的 [task flow](steps/step-001-harness-to-adapter/05-task-flow.md)也已同步新版，旧稿完整归档；Step 3 的 [scope](steps/step-003-swe-evaluation/01-scope.md)已同步新版入口与阅读导航；Step 3 的 [task flow](steps/step-003-swe-evaluation/05-task-flow.md)及本轮七张函数卡片已同步新版，旧稿保留；其余函数卡片与 Step 4–9 的记录继续保留各自版本，待逐项校准；[版本影响](version-reviews/2026-10-23-2f231865-to-18868a79.md)与[卡片盘点](version-reviews/2026-10-23-step-card-audit.md)单独保存。
- 当前进度与下一步：[阅读路线的当前接续](../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。
- 连贯技术正文：[00 全景 walkthrough](../../../slime_photo/code-reading/chapters/00-overview/walkthrough.md)，其 [Hugo 页面](http://localhost:1313/projects/slime/framework-walkthrough/)从同一文件渲染。
- 模块与函数资料：[现有源码索引](../../../slime_photo/code-reading/code-reading-list.md)。00–07 和 4.1 是资料分组；本目录步骤是理解形成的先后，两者不混用。

## 步骤索引

| 步骤 | 本步核心问题 | 记录 |
| --- | --- | --- |
| 009 · 已建接收范围，待校准 | CLI 的 HTTP 请求怎样被监听、路由并交给 _run_turn？ | [步骤入口](steps/step-009-adapter-request-entry/README.md) |
| 008 · 前序 | Harness 怎样启动 CLI，并等待退出码返回？ | [步骤入口](steps/step-008-harness-communication/README.md) |
| 007 · 前序 | 已有沙箱怎样接住工作区配置与题目内容？ | [步骤入口](steps/step-007-prepare-workspace/README.md) |
| 006 · 前序 | 任务的镜像怎样变成供 Agent 使用的执行沙箱？ | [步骤入口](steps/step-006-agent-sandbox/README.md) |
| 005 · 前序 | open_session 怎样按 sid 登记本次执行的会话配置？ | [步骤入口](steps/step-005-agent-preparation/README.md) |
| 004 · 前序 | 会话轨迹如何结合奖励与基础样本，导出 Sample 列表？ | [步骤入口](steps/step-004-trajectory-to-samples/README.md) |
| 003 · 前序 | 代码改动如何在独立环境中被评测，并得到奖励？ | [步骤入口](steps/step-003-swe-evaluation/README.md) |
| 002 · 新增范围 | CLI 结束后，怎样取回运行统计与代码补丁？ | [步骤入口](steps/step-002-agent-results/README.md) |
| 001 · 前序 | 从 Harness 定位到 Adapter 后，一次模型请求怎样被处理？ | [步骤入口](steps/step-001-harness-to-adapter/README.md) |
| 000 · 新版校准起点 | 理解 Coding Agent，定位指挥官函数并提取核心骨架 | [步骤入口](steps/step-000-coding-agent/README.md) |

旧 `initial-model` 已移出当前步骤目录，仅在[历史归档](../../../backlog/repo-reading/archived-steps/README.md)保留。Coding Agent 与 Harness 到 Adapter 两步作为前序继续保留，原目录纠正见[历史讨论](../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#keep-coding-agent-archive-initial-model)。

Step 0 的三项 scope 见[整体阅读范围](steps/step-000-coding-agent/01-scope.md)，两层 memory 暂无函数卡片。Step 1 的[当前阅读范围](steps/step-001-harness-to-adapter/01-scope.md)给出 `_run_turn` 的流程；`02` 保存移入的转换记录、新建的 `_run_turn` 记录与原有 Harness 记录，`03` 暂无前序函数可继承。助手讲解不等于用户已掌握全部实现。

Step 2 的 [scope](steps/step-002-agent-results/01-scope.md)按 `collect_metrics → git_diff` 组织结果收集，明确两份输出与后续消费者；`03` 完整继承 Step 1 当前的 20 份记录，`02` 随逐个函数的实际阅读建立。第一处入口是 `ClaudeCodeHarness.collect_metrics`。

Step 3 的 [scope](steps/step-003-swe-evaluation/01-scope.md)继承整体骨架后展开第 6 项评测；`02` 保存本步评分函数，`03` 保留原步骤建立时继承自 Step 1 的 17 份函数记录。新增 Step 2 的记忆待进入评测校准时再合并，已认可的 skill reference 保留原文。

Step 4 的 [scope](steps/step-004-trajectory-to-samples/01-scope.md)接到第 7 项样本导出；`02` 从 `BaseAdapter.finish_session` 开始，`03` 合并 Step 3 的 `03 + 02`，共 24 份函数记录。[阅读后的任务总结](steps/step-004-trajectory-to-samples/05-task-flow.md)连接前序轨迹、评测奖励与样本导出，保留组装算法和外层清理的后续问题；不把总结等同于全部实现已读。

Step 5 的 [scope](steps/step-005-agent-preparation/01-scope.md)继承完整骨架，围绕第 1 项会话登记，回查 Adapter 对象与执行编号的来源；`03` 合并 Step 4 的 `03 + 02`，共 27 份函数记录，`02` 保存 `_AdapterService.__init__`、`_session_id` 与 `BaseAdapter.open_session` 三份函数卡片，以及 [Session 类卡片](steps/step-005-agent-preparation/02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md)。服务初始化卡片保留整体职责，当前只展开 Adapter 创建与保存；编号卡片解释实际读取的字段与三种返回规则；类卡片解释每次执行的配置对象。[task flow](steps/step-005-agent-preparation/05-task-flow.md)已收拢对象来源、编号与配置登记，并接回后续取用；保留题目信息与会话配置的边界澄清。环境与工作区准备仅在骨架中定位，作为后续候选。

Step 6 的 [scope](steps/step-006-agent-sandbox/01-scope.md)继承完整骨架，聚焦第 2 项启动执行沙箱；`02` 保存 [boot_agent_sandbox](steps/step-006-agent-sandbox/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md) 的准备、交付与退出回收模型，以及 [E2BSandbox 类卡片](steps/step-006-agent-sandbox/02-short-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)的状态、本地与远端关系和操作入口；安装过程统一见 [install_npm_cli 主记录](steps/step-006-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)，[ClaudeCodeHarness.install_cli](steps/step-006-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md)保留为参数适配与委托的引用入口。`03` 合并 Step 5 的 `03 + 02`，共 30 份函数记录与 1 份类记录。范围确认、类与函数的解释保存在本步 flow；[task flow](steps/step-006-agent-sandbox/05-task-flow.md)已收拢镜像输入、CLI 就绪、交出 sb、调用方使用与退出回收，底层等待和完整故障恢复留待按需深入。

Step 7 的 [scope](steps/step-007-prepare-workspace/01-scope.md)继承完整骨架并展开第 3 项工作区准备；`03` 完整合并 Step 6 的 35 份记录，`02` 保存 [prepare_workspace](steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md) 的整体交接、[ensure_agent_user](steps/step-007-prepare-workspace/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) 的用户与目录准备，以及 [apply_before_repo_set_cmd](steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md)、[apply_pre_commands](steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md) 的配置命令、脚本写入和执行。本步 task flow 待阅读后整理。

Step 8 的 [scope](steps/step-008-harness-communication/01-scope.md)保留整体七项骨架，收拢第 4 项的 CLI 启动与等待；[task flow](steps/step-008-harness-communication/05-task-flow.md)串起运行前提、远端配置、命令与环境、退出码返回。`03` 保留进入本步时的 38 份记录，`02` 保留 8 份已读或调取的函数与类记录。原有通信问题、参考和拆分前 scope 继续保存。

Step 9 的 [scope](steps/step-009-adapter-request-entry/01-scope.md)专门接清 CLI 运行期间的 HTTP 接收入口：服务准备、路由绑定、`request → body`，再接回既有模型处理链。`03` 合并 Step 8 的 `03 + 02` 为 43 份记录，`02` 先调取 `_AdapterService.__init__` 与 `_run_turn` 供本步直接回看；新函数逐处阅读后记录。本步编号表示阅读顺序，接收请求发生在 Step 8 等待 CLI 期间。


新步骤按 `01-scope.md`、`02-short-term-memory/`、`03-long-term-memory/`、`04-flow.md` 保存范围、本步新认识、前序累计模型与理解过程。两层记忆都镜像 Slime 源码目录，例如 `functions/slime/ray/rollout.py/RolloutManager.generate.md`；字段见[统一规范](../../memory-format.md)。下一步合并上一份 `03` 与 `02`，旧步骤保留当时的理解和目录。
