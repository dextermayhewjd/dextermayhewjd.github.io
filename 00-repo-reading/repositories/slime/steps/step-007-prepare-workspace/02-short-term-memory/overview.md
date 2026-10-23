# 02 · Step 7 的短期记忆

[本步范围](../01-scope.md) · [前序记忆](../03-long-term-memory/overview.md)

| 源码文件 | 记录 | 首次接触 | 最近认识更新与状态 |
| --- | --- | --- | --- |
| `examples/coding_agent_rl/swe.py` | [prepare_workspace](functions/examples/coding_agent_rl/swe.py/prepare_workspace.md) | Step 6 定位为下一处；Step 7，2026-10-22 开始记录 | 用户在两个准备入口讲解后反馈“大概明白了”，继续追问沙箱交接；已补充本地编排与远端效果的区别，末尾题目写入待继续，未运行真实沙箱 |
| `slime/agent/sandbox.py` | [ensure_agent_user](functions/slime/agent/sandbox.py/ensure_agent_user.md) | Step 3，2026-10-21 | 2026-10-22 在职责复述与账号/目录归属澄清后反馈“大概理解了”，继续返回父函数；具体 shell 与 SDK 实现未展开，原有复述保留 |
| `examples/coding_agent_rl/swe.py` | [apply_before_repo_set_cmd](functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md) | Step 7，2026-10-22 单独展开 | 用户在澄清后反馈“大概理解了”，概括按题目配置执行准备；当前先看 metadata / grading，未将 pre_commands 的类比计为实现已读 |
| `examples/coding_agent_rl/swe.py` | [apply_pre_commands](functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md) | Step 7，2026-10-22 单独展开 | 已用真实命令整理输入、脚本写入与执行的关系；用户反馈“大概明白了”，在父卡继续澄清整体交接，未运行远端命令 |

输入背景：[md 的内容、字段来源与用途](../references/metadata.md) · [auth0-python 真实题目](../references/scaleswe-auth0-example.md)，供相关函数共用；它们是数据参考，不另计为函数卡片。

形成过程：[进入工作区准备](../../step-007-prepare-workspace/04-flow.md#prepare-workspace-entry) · [展开用户与目录准备](../../step-007-prepare-workspace/04-flow.md#ensure-agent-user-entry) · [职责复述与澄清](../../step-007-prepare-workspace/04-flow.md#ensure-agent-user-restatement) · [理解反馈与返回主线](../../step-007-prepare-workspace/04-flow.md#workspace-initialization-next)。

本次展开：[将配置命令写成脚本并执行](../../step-007-prepare-workspace/04-flow.md#apply-before-repo-set-cmd-entry)。

后续澄清：[命令来源与题目前置准备的用途](../../step-007-prepare-workspace/04-flow.md#before-repo-set-purpose)。

后续反馈：[先看 metadata 与 grading 的配置结构](../../step-007-prepare-workspace/04-flow.md#grading-input-context)。

真实例子与职责澄清：[用真实题目补回准备函数的输入与输出](../../step-007-prepare-workspace/04-flow.md#real-task-preparation-example)。

本次展开：[准备命令怎样写入并执行](../../step-007-prepare-workspace/04-flow.md#apply-pre-commands-function-card)。

后续反馈：[准备效果留在哪里，接下来读什么](../../step-007-prepare-workspace/04-flow.md#preparation-effects-and-sandbox-handoff)。
