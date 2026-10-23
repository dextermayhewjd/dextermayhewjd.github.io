# 02 · Step 8 的短期记忆

[本步范围](../01-scope.md) · [前序记忆](../03-long-term-memory/overview.md)

本目录收录本步正在使用的记录，包括新增卡片与从 `03` 调取的旧卡；“调取”不表示产生了新认识。

| 源码文件 | 记录 | 首次接触 | 最近认识更新与状态 |
| --- | --- | --- | --- |
| `slime/agent/harness/common.py` | [BaseHarness.run](functions/slime/agent/harness/common.py/BaseHarness.run.md) | Step 1 | 2026-10-23 已有启动链整体复述；本次校准配置位置和执行边界，HTTP 接收入口仍待接清 |
| `slime/agent/sandbox.py` | [ensure_agent_user](functions/slime/agent/sandbox.py/ensure_agent_user.md) | Step 3，2026-10-21 | 2026-10-23 从本步 `03` 调取；接上 `BaseHarness.run:97 → 98`。最近认识更新仍为 2026-10-22，保留原话与未知 |
| `slime/agent/harness/claude_code.py` | [ClaudeCodeHarness.launch_and_wait](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | Step 1 的上游定位；Step 8 首次独立建卡 | 2026-10-23 复述 cmd、配置与上下文；校准 58–70 行准备、71 行委派执行并等待 |
| `slime/agent/harness/common.py` | [HarnessContext（类）](classes/slime/agent/harness/common.py/HarnessContext.md) | Step 8，随 `run` 定位后单独展开 | 2026-10-23 概括为收拢上下文；补清本地 ctx 与远端配置、环境变量的区别 |
| `slime/agent/harness/claude_code.py` | [ClaudeCodeHarness.write_config](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) | Step 8，`run:103` | 2026-10-23 复述自动运行配置；写入位置为远端沙箱，配置文件与 CLI 程序代码的区别待反馈 |
| `slime/agent/harness/common.py` | [run_agent](functions/slime/agent/harness/common.py/run_agent.md) | Step 1 与 Step 8 的上游定位；2026-10-22 首次独立建卡 | 2026-10-23 串起目录、执行与等待阶段；下层机制保留在 exec_and_wait 卡片 |
| `slime/agent/sandbox.py` | [exec_and_wait](functions/slime/agent/sandbox.py/exec_and_wait.md) | Step 6 提及；Step 8 随 `run_agent` 首次独立建卡 | 2026-10-23 已列出脱机、防重、marker 与保活阶段；具体实现和清理边界未视为全部掌握 |
| `slime/agent/adapters/common.py` | [BaseAdapter._run_turn](functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | Step 1，2026-10-21 | 2026-10-23 从本步 `03` 调取，补清 Request/body 入口；后续转入 Step 9，保留本步调取历史与原未知 |

形成过程：[Step 8 · 原始通信问题](../../step-008-harness-communication/04-flow.md#run-cross-process-communication) · [独立成步的确认](../../step-008-harness-communication/04-flow.md#separate-communication-step)。
