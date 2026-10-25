> 2026-10-25 主题迁移前的完整项目入口。正文作为历史快照保留，仅重算文件链接；当前入口见 [Slime README](../README.md)。

---

# Slime：按目标逐步建立整体模型

[通用方法](../../../README.md) · [工作流](../../../workflow.md)

用户的阅读目标是准备其提供的腾讯混元 Agent 强化学习框架工程师岗位。以理解框架为主，本地没有 GPU，希望用模型 API 辅助验证；按岗位责任取舍深度。完整目标和初始投入建议继续保存在[岗位对照](../../../../slime_photo/code-reading/job-alignment.md)，不在这里复制一份。

本轮已确认阅读方向是 Coding Agent / Coding RL。Step 0 建立核心骨架，Step 1 读模型请求，新增 Step 2 单独读运行统计与补丁提取，Step 3 读独立评测，Step 4 读会话轨迹与奖励怎样交成样本，Step 5 回补 `open_session` 的会话配置登记。Step 6 已收拢执行沙箱的准备、交付与回收，Step 7 记录 `swe.prepare_workspace` 的任务工作区准备，Step 8 收拢 Harness 启动与等待，Step 9 按用户确认单独补清 CLI 的 HTTP 请求怎样进入 Adapter。每个后续 step 仍先一起确认具体问题与函数范围；具体掌握与运行状态以唯一路线为准。

2026-10-23 插入新 Step 2 后，原 Step 002–008 已顺延为 Step 003–009。历史原话、过程和固定 skill reference 保留当时编号，见[新旧编号对照](../step-numbering-2026-10-23.md)；后续步骤的原记忆快照暂不批量重算。

## 源码与唯一记录入口

- 当前可用的本地源码：`/home/fredkeira/projects/slime`；2026-10-24 核对 HEAD 仍为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。历史路径 `/home/hongshi/projects/slime` 在本机不可用；2026-10-23 的官方 main 核对仍保留原时点依据。Step 0、Step 1 scope 已按新版校准并保存旧稿；Step 1 已校准 `_translate`、`_render_token_ids`、`call_sglang_generate`、`parse_model_output`、`_build_reply`、`_respond`、`TrajectoryManager.record_turn`，新增 `_session_prompt_ids`、`trace_span` 卡片，Step 1 的 [task flow](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/05-task-flow.md)也已同步新版，旧稿完整归档；Step 3 的 [scope](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/01-scope.md)已同步新版入口与阅读导航；Step 3 的 [task flow](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/05-task-flow.md)及本轮七张函数卡片已同步新版，旧稿保留；Step 4 的 [scope](../topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/01-scope.md)、三张主流程卡片与 task flow 已校准到样本列表返回，旧稿归档；内层细节后续回访，Step 5 已校准服务初始化并补入 endpoint、后台 HTTP 启动及服务类卡，前序继承更新为 30 份；编号、会话登记与 Session 字段也已校准，task flow 按用户后置字段细节的边界收拢；Step 6–9 的 scope 与 task flow 也已按各步范围更新，旧卡与累计快照继续保留各自版本归属；[版本影响](2026-10-23-2f231865-to-18868a79.md)与[卡片盘点](2026-10-23-step-card-audit.md)单独保存。
- 当前进度与下一步：[阅读路线的当前接续](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。
- 后续选读与 Dressage 对照规划：[Slime 后续阅读顺序](../slime后续阅读顺序/README.md) · [切入 Dressage：提炼抽象层级与评测方式](../slime后续阅读顺序/dressage-abstraction-and-evaluation-route.md) · [混元岗位对齐与评测抽象分析](../slime后续阅读顺序/hunyuan-jd-and-eval-abstraction-analysis.md)。
- 连贯技术正文：[00 全景 walkthrough](../../../../slime_photo/code-reading/chapters/00-overview/walkthrough.md)，其 [Hugo 页面](http://localhost:1313/projects/slime/framework-walkthrough/)从同一文件渲染。
- 模块与函数资料：[现有源码索引](../../../../slime_photo/code-reading/code-reading-list.md)。00–07 和 4.1 是资料分组；本目录步骤是理解形成的先后，两者不混用。

## 步骤索引

| 步骤 | 本步核心问题 | 记录 |
| --- | --- | --- |
| 009 · HTTP 请求接入 | CLI 的 HTTP 请求怎样被监听、路由并交给 _run_turn？ | [步骤入口](../topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/README.md) |
| 008 · 前序 | Harness 怎样启动 CLI，并等待退出码返回？ | [步骤入口](../topics/01-coding-agent-rl/steps/step-008-harness-communication/README.md) |
| 007 · 前序 | 已有沙箱怎样接住工作区配置与题目内容？ | [步骤入口](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/README.md) |
| 006 · 前序 | 任务的镜像怎样变成供 Agent 使用的执行沙箱？ | [步骤入口](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/README.md) |
| 005 · 前序 | open_session 怎样按 sid 登记本次执行的会话配置？ | [步骤入口](../topics/01-coding-agent-rl/steps/step-005-agent-preparation/README.md) |
| 004 · 前序 | 会话轨迹如何结合奖励与基础样本，导出 Sample 列表？ | [步骤入口](../topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/README.md) |
| 003 · 前序 | 代码改动如何在独立环境中被评测，并得到奖励？ | [步骤入口](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/README.md) |
| 002 · 结果收集 | CLI 结束后，怎样取回运行统计与代码补丁？ | [步骤入口](../topics/01-coding-agent-rl/steps/step-002-agent-results/README.md) |
| 001 · 前序 | 从 Harness 定位到 Adapter 后，一次模型请求怎样被处理？ | [步骤入口](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/README.md) |
| 000 · 新版校准起点 | 理解 Coding Agent，定位指挥官函数并提取核心骨架 | [步骤入口](../topics/01-coding-agent-rl/steps/step-000-coding-agent/README.md) |

旧 `initial-model` 已移出当前步骤目录，仅在[历史归档](../../../../backlog/repo-reading/archived-steps/README.md)保留。Coding Agent 与 Harness 到 Adapter 两步作为前序继续保留，原目录纠正见[历史讨论](../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#keep-coding-agent-archive-initial-model)。

Step 0 的三项 scope 见[整体阅读范围](../topics/01-coding-agent-rl/steps/step-000-coding-agent/01-scope.md)，两层 memory 暂无函数卡片。Step 1 的[当前阅读范围](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md)给出 `_run_turn` 的流程；`02` 保存移入的转换记录、新建的 `_run_turn` 记录与原有 Harness 记录，`03` 暂无前序函数可继承。助手讲解不等于用户已掌握全部实现。

Step 2 的 [scope](../topics/01-coding-agent-rl/steps/step-002-agent-results/01-scope.md)按 `collect_metrics → git_diff` 组织结果收集，明确两份输出与后续消费者；`03` 完整继承 Step 1 当前的 20 份记录，`02` 随逐个函数的实际阅读建立。第一处入口是 `ClaudeCodeHarness.collect_metrics`。

Step 3 的 [scope](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/01-scope.md)继承整体骨架后展开第 6 项评测；`02` 保存本步评分函数，`03` 保留原步骤建立时继承自 Step 1 的 17 份函数记录。新增 Step 2 的记忆待进入评测校准时再合并，已认可的 skill reference 保留原文。

Step 4 的 [scope](../topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/01-scope.md)接到第 7 项样本导出；`02` 从 `BaseAdapter.finish_session` 开始，`03` 合并 Step 3 的 `03 + 02`，共 24 份函数记录。[阅读后的任务总结](../topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/05-task-flow.md)连接前序轨迹、评测奖励与样本导出，保留组装算法和外层清理的后续问题；不把总结等同于全部实现已读。

Step 5 的 [scope](../topics/01-coding-agent-rl/steps/step-005-agent-preparation/01-scope.md)继承完整骨架，围绕第 1 项会话登记，回查 Adapter 对象与执行编号的来源；`03` 合并 Step 4 的 `03 + 02`，共 30 份函数与类记录，`02` 当前保存五份函数卡片和两份类卡片，覆盖服务初始化、端点、后台启动、编号与会话登记；[Session 类卡片](../topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md)已补齐新版五项字段。服务初始化卡片已按新版拆清共用准备与 endpoint 委派，新增服务类卡及 endpoint、run_app_in_thread 的交接记录；编号卡片解释实际读取的字段与三种返回规则；类卡片解释每次执行的配置对象。[task flow](../topics/01-coding-agent-rl/steps/step-005-agent-preparation/05-task-flow.md)已按 `18868a79` 收拢服务准备、编号与登记，主线在 `store[sid]` 建立处结束，Session 字段细节后置；保留题目信息与会话配置的边界澄清。环境与工作区准备仅在骨架中定位，作为后续候选。

Step 6 的 [scope](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/01-scope.md)继承完整骨架，聚焦第 2 项启动执行沙箱；`02` 保存 [boot_agent_sandbox](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md) 的准备、交付与退出回收模型，以及 [E2BSandbox 类卡片](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md)的状态、本地与远端关系和操作入口；安装过程统一见 [install_npm_cli 主记录](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md)，[ClaudeCodeHarness.install_cli](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md)保留为参数适配与委托的引用入口。`03` 合并 Step 5 的 `03 + 02`，共 30 份函数记录与 1 份类记录。范围确认、类与函数的解释保存在本步 flow；[task flow](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/05-task-flow.md)已收拢镜像输入、CLI 就绪、交出 sb、调用方使用与退出回收，底层等待和完整故障恢复留待按需深入。

Step 7 的 [scope](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/01-scope.md)继承完整骨架并展开第 3 项工作区准备；`03` 保留原进入本步时合并的 35 份记录。`02` 保存 [prepare_workspace](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md) 的整体交接、[ensure_agent_user](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) 的用户与目录准备、[apply_before_repo_set_cmd](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md) 与 [apply_pre_commands](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md) 的配置命令，以及 [_repository_tree](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_repository_tree.md) 的快照生成。[task flow](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/05-task-flow.md)已按 `18868a79` 汇总工作区准备、题目写入与 `baseline` 返回；实现上的待深入问题仍保留在各卡片中。

Step 8 的 [scope](../topics/01-coding-agent-rl/steps/step-008-harness-communication/01-scope.md)保留整体七项骨架，收拢第 4 项的 CLI 启动与等待；[task flow](../topics/01-coding-agent-rl/steps/step-008-harness-communication/05-task-flow.md)已按 `18868a79` 串起运行前提、配置、命令与环境、后台执行和结果回传，旧总结完整归档。`03` 保留进入本步时的 38 份记录，`02` 保留 8 份已读或调取的函数与类记录。原有通信问题、参考和拆分前 scope 继续保存，具体理解与未知见唯一路线及函数原话。

Step 9 的 [scope](../topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/01-scope.md)专门接清 CLI 运行期间的 HTTP 接收入口：服务准备、路由绑定、`request → body`，再接回既有模型处理链。`03` 保留进入本步时的 43 份记录；`02` 包含调入的启动与服务记录、服务类卡以及路由函数卡。[task flow](../topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/05-task-flow.md)已整理正常请求与响应交接；[整组步骤的覆盖核对](../topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/04-flow.md#coding-agent-coverage-check)区分单题正常主线、外层生命周期收尾及尚未系统展开的训练闭环。本步编号表示阅读顺序，接收请求发生在 Step 8 等待 CLI 期间。


新步骤按 `01-scope.md`、`02-short-term-memory/`、`03-long-term-memory/`、`04-flow.md` 保存范围、本步新认识、前序累计模型与理解过程。两层记忆都镜像 Slime 源码目录，例如 `functions/slime/ray/rollout.py/RolloutManager.generate.md`；字段见[统一规范](../../../memory-format.md)。下一步合并上一份 `03` 与 `02`，旧步骤保留当时的理解和目录。
