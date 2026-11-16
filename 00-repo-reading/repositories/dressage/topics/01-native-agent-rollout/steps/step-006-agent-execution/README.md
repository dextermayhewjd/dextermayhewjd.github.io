# Step 006 · 把题目交给 Agent，并取回执行结果

[项目进度](../../../../README.md) · [本步 scope](01-scope.md) · [前一步总结](../step-005-agent-registration/05-task-flow.md)

2026-11-07，用户在 Step 005 首轮收束后要求继续并开始下一步。本步沿已约定的旧 generate 收尾顺序，从 `paddock.call_agent` 进入。

## 本步问题

环境、Agent 注册和前置命令已经准备好。现在怎样把题目交给沙箱里的 Agent，等待执行结果，再返回 generate？

第一张函数卡是 [BlackboxAgentPaddock.call_agent](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.call_agent.md)。先看它将哪些已有资料交给客户端；服务端和实际 CLI 的内部执行按后续问题逐步进入，不提前建卡。

## 记录入口

1. [01-scope](01-scope.md)：整体位置、调用骨架、阅读入口和停止点。
2. [02 短期记录](02-short-term-memory/overview.md)：本步实际展开的函数。
3. [03 前序累计](03-long-term-memory/overview.md)：继承 Step 005 的 23 份长期记录与 9 份短期记录。
4. [04 形成过程](04-flow.md)：本步问题、说明和用户反馈。
5. [05 任务链路总结](05-task-flow.md)：提交回复、后台执行、查询结果和返回 generate 的完整交接。

## 按需补充

1. [CLI 输出与模型 API](../../../../references/cli-output-and-model-api.md)：stdout 里是什么、为什么与代理采集同时存在，以及不同问题该去哪里看。
2. [Python 怎样读取 CLI 的标准输出](references/python-stdout-pipe.md)：PIPE、逐行读取、decode 与 JSON 解析，附已运行的最小例子。

两份说明从 [_run_claude_turn 函数卡](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md)中拆出；函数卡继续保留执行顺序、关键代码和返回位置。

## 当前边界

选择 Claude Code、客户端默认 async 提交并等待结果的正常路径。本步停止在 generate 取得 call_payload、形成 agent_response 这一段；after_agent、轨迹导出和最终回收仍留在整体图中，后续接续。

本步已经开始不等于已经理解内部机制。当前仅静态核对，没有发送任务、启动 CLI 或执行模型调用。

2026-11-14 补读接续：从 [send_message 的 Task 调用](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md#launch-cli-task) 进入 [_run_claude_turn 的进程启动与模型请求段](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#model-request-during-cli)，承接 Step 014 留出的公共 Proxy 请求链。此为原位置的新增补读，原首轮状态与快照保留，未读处理函数尚未建卡。

2026-11-14 补读范围已展开到 [9.2a–9.2e 的去程与回程](01-scope.md#model-request-route)：本地 Proxy 发送 → 外部 Dressage Proxy 生成 → SGLang 调用 → 记录一步交互 → Anthropic 响应回 CLI。下一处仍只读发送入口，未预建其余函数卡；旧首轮状态与后续 Step 007/008 分工保留。
