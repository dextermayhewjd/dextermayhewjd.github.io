# 02 · Step 7 的短期记忆

[本步范围](../01-scope.md) · [前序记忆](../03-long-term-memory/overview.md)

| 源码文件 | 记录 | 首次接触 | 最近认识更新与状态 |
| --- | --- | --- | --- |
| `examples/coding_agent_rl/swe.py` | [prepare_workspace](functions/examples/coding_agent_rl/swe.py/prepare_workspace.md) | Step 6 定位为下一处；Step 7，2026-10-22 开始记录 | 2026-10-24 用户反馈差不多理解，追问第二段版本变化；已区分不变的分派逻辑、脚本路径变化和末尾 baseline 返回，内部细节未逐项确认，无真实运行 |
| `examples/coding_agent_rl/swe.py` | [_repository_tree](functions/examples/coding_agent_rl/swe.py/_repository_tree.md) | Step 2，2026-10-23 作为依赖定位；Step 7，2026-10-24 独立建卡 | 2026-10-24 用户识别快照职责，继续追问 current、run_turn 与索引／树的数量关系；调用链与快照稳定性已核对，机制理解尚待反馈 |
| `slime/agent/sandbox.py` | [ensure_agent_user](functions/slime/agent/sandbox.py/ensure_agent_user.md) | Step 3，2026-10-21 | 2026-10-24 用户复述账号、Git 配置与交给 sb 的职责；已补系统账号、按需创建和等待执行的语义，内部机制保留未知 |
| `examples/coding_agent_rl/swe.py` | [apply_before_repo_set_cmd](functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md) | Step 7，2026-10-22 单独展开 | 2026-10-24 用户概括通过脚本初始化工作区；已补准备命令与安装动作的范围区别，独立教学例子及旧认识保留 |
| `examples/coding_agent_rl/swe.py` | [apply_pre_commands](functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md) | Step 7，2026-10-22 单独展开 | 保留 2026-10-22 的初步理解；2026-10-24 更新 /tmp 脚本路径、当前调用场景和返回位置，完整原命令保留 |

输入背景：[md 的内容、字段来源与用途](../references/metadata.md) · [auth0-python 真实题目](../references/scaleswe-auth0-example.md)，供相关函数共用；它们是数据参考，不另计为函数卡片。

形成过程：[进入工作区准备](../04-flow.md#prepare-workspace-entry) · [展开用户与目录准备](../04-flow.md#ensure-agent-user-entry) · [职责复述与澄清](../04-flow.md#ensure-agent-user-restatement) · [理解反馈与返回主线](../04-flow.md#workspace-initialization-next)。

本次展开：[将配置命令写成脚本并执行](../04-flow.md#apply-before-repo-set-cmd-entry)。

后续澄清：[命令来源与题目前置准备的用途](../04-flow.md#before-repo-set-purpose)。

后续反馈：[先看 metadata 与 grading 的配置结构](../04-flow.md#grading-input-context)。

真实例子与职责澄清：[用真实题目补回准备函数的输入与输出](../04-flow.md#real-task-preparation-example)。

本次展开：[准备命令怎样写入并执行](../04-flow.md#apply-pre-commands-function-card)。

后续反馈：[准备效果留在哪里，接下来读什么](../04-flow.md#preparation-effects-and-sandbox-handoff)。

当前版本校准：[按实际变化更新本步短期记录](../04-flow.md#prepare-workspace-short-term-refresh)。
