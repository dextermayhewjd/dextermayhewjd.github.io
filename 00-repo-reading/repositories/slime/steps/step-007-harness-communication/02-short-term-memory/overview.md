# 02 · Step 7 的短期记忆

[本步范围](../01-scope.md) · [前序记忆](../03-long-term-memory/overview.md)

| 源码文件 | 记录 | 首次接触 | 最近认识更新与状态 |
| --- | --- | --- | --- |
| `slime/agent/harness/common.py` | [BaseHarness.run](functions/slime/agent/harness/common.py/BaseHarness.run.md) | Step 1 | 保留旧问题与完整前序记录；Step 7 补齐启动场景与交接；局部复述见上下文和配置子卡，尚无完整机制复述 |
| `slime/agent/harness/claude_code.py` | [ClaudeCodeHarness.launch_and_wait](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | Step 1 的上游定位；Step 7 首次独立建卡 | 2026-10-22 用户明确进入本函数；已展开命令、完整环境字典及退出码交接，机制理解尚待反馈 |
| `slime/agent/harness/common.py` | [HarnessContext（类）](classes/slime/agent/harness/common.py/HarnessContext.md) | Step 7，随 `run` 定位后单独展开 | 2026-10-22 用户已概括三项运行信息；局部 `ctx` 与 Harness 属性的区别由助手补充，尚待反馈 |
| `slime/agent/harness/claude_code.py` | [ClaudeCodeHarness.write_config](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) | Step 7，`run:103` | 2026-10-22 用户概括配置准备与 `sb` 传输；已补齐两项状态、远端文件及后续启动的边界 |

形成过程：[Step 7 · 原始通信问题](../../step-007-harness-communication/04-flow.md#run-cross-process-communication) · [独立成步的确认](../../step-007-harness-communication/04-flow.md#separate-communication-step)。
