# 02 · Step 8 的短期记忆

[本步范围](../01-scope.md) · [前序记忆](../03-long-term-memory/overview.md)

本目录收录本步正在使用的记录，包括新增卡片与从 `03` 调取的旧卡；“调取”不表示产生了新认识。

| 源码文件 | 记录 | 首次接触 | 最近认识更新与状态 |
| --- | --- | --- | --- |
| `slime/agent/harness/common.py` | [BaseHarness.run](functions/slime/agent/harness/common.py/BaseHarness.run.md) | Step 1 | 2026-10-23 已有启动链整体复述；本次校准配置位置和执行边界，HTTP 接收入口仍待接清 |
| `slime/agent/sandbox.py` | [ensure_agent_user](functions/slime/agent/sandbox.py/ensure_agent_user.md) | Step 3，2026-10-21 | 2026-10-23 从本步 `03` 调取；接上 `BaseHarness.run:97 → 98`。最近认识更新仍为 2026-10-22，保留原话与未知 |
| `slime/agent/harness/claude_code.py` | [ClaudeCodeHarness.launch_and_wait](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | Step 1 的上游定位；Step 8 首次独立建卡 | 2026-10-24 用户选定“组装启动材料 → 补充运行控制 → 委派并等待”的模型；整体主图与源码保留，具体机制仍待反馈 |
| `slime/agent/harness/common.py` | [HarnessContext（类）](classes/slime/agent/harness/common.py/HarnessContext.md) | Step 8，随 `run` 定位后单独展开 | 2026-10-23 概括为收拢上下文；补清本地 ctx 与远端配置、环境变量的区别 |
| `slime/agent/harness/claude_code.py` | [ClaudeCodeHarness.write_config](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) | Step 8，`run:103` | 2026-10-23 复述自动运行配置；写入位置为远端沙箱，配置文件与 CLI 程序代码的区别待反馈 |
| `slime/agent/harness/common.py` | [run_agent](functions/slime/agent/harness/common.py/run_agent.md) | Step 1 与 Step 8 的上游定位；2026-10-22 首次独立建卡 | 2026-10-23 串起目录、执行与等待阶段；下层机制保留在 exec_and_wait 卡片 |
| `slime/agent/sandbox.py` | [exec_and_wait](functions/slime/agent/sandbox.py/exec_and_wait.md) | Step 6 提及；Step 8 随 `run_agent` 首次独立建卡 | 2026-10-25 用户反馈大致理解三阶段，已补后台运行与主机等待的关系；read_file 版本已校准，具体清理与实现仍保留边界 |
| `slime/agent/adapters/common.py` | [BaseAdapter._run_turn](functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | Step 1，2026-10-21 | 2026-10-23 从本步 `03` 调取，补清 Request/body 入口；后续转入 Step 9，保留本步调取历史与原未知 |

形成过程：[Step 8 · 原始通信问题](../04-flow.md#run-cross-process-communication) · [独立成步的确认](../04-flow.md#separate-communication-step)。
