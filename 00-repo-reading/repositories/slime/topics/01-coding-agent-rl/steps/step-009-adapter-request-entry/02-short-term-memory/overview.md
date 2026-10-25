# 02 · Step 9 的短期记忆

[本步范围](../01-scope.md) · [前序累计记忆](../03-long-term-memory/overview.md)

本步保留以下已读函数与类的记录。调取用于恢复当前交接，不改变首次接触或最近认识时间；接收侧新函数按实际阅读逐个加入。

2026-10-25 范围校准：下表的旧卡保留原版本。本轮按 [scope 的现行导航](../01-scope.md#adapter-entry-navigation)复用 Step 005 的服务、Step 008 的启动和 Step 001 的请求处理记录；本次没有改写两张旧卡或更新个人认识时间。

2026-10-25 本次调取：按用户要求，将 Step 008 的现行 `launch_and_wait` 卡片与 Step 005 的 `_AdapterService` 类卡完整放入本步 `02`；正文、图表与原话保留，只补来源并调整相对链接。

2026-10-25 服务端衔接：按已确认的流程说明方案，完整调入 Step 005 的 `run_app_in_thread` 卡片；保留原 Claude 场景与认识日期，新流程说明以 Codex 作为共同机制的例子。

| 源码文件 | 记录 | 首次接触 | 本步使用位置与状态 |
| --- | --- | --- | --- |
| `examples/coding_agent_rl/generate.py` | [_AdapterService 类卡](classes/examples/coding_agent_rl/generate.py/_AdapterService.md) | 2026-10-22 接触对象；2026-10-24 建类卡 | 从 Step 005 完整调入，回查共用依赖、Adapter 对象、访问地址与服务句柄 |
| `examples/coding_agent_rl/generate.py` | [_AdapterService.__init__](functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md) | Step 5，2026-10-22 | 回查 Adapter 应用与监听服务的来源；本次仅调取，监听细节待读 |
| `slime/agent/adapters/common.py` | [BaseAdapter._run_turn](functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | Step 1，2026-10-21 | 接住服务传入的 Request，重点补其来路；既有原话、未知与 Step 8 追问保留 |
| `slime/agent/harness/claude_code.py` | [ClaudeCodeHarness.launch_and_wait](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | Step 1 定位；2026-10-22 独立建卡 | 从 Step 008 调入现行完整卡片，本步回看 `env` 与 Adapter 地址传递，未重写正文 |
| `slime/agent/adapters/anthropic.py` | [AnthropicAdapter._register_routes](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._register_routes.md) | Step 009 定位；2026-10-25 集中回看 | 本步新建：登记 POST 路径与处理函数；请求触发机制尚待反馈 |
| `slime/agent/aiohttp_threaded.py` | [run_app_in_thread](functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md) | 前序定位；2026-10-24 展开启动交接 | 从 Step 005 完整调入，重点回看同一个 app 怎样交给 runner/site |

来源：[Step 9 范围确认](../04-flow.md#request-entry-scope) · [Step 8 的原始追问](../../step-008-harness-communication/04-flow.md#launch-restatement-and-http-entry)。
