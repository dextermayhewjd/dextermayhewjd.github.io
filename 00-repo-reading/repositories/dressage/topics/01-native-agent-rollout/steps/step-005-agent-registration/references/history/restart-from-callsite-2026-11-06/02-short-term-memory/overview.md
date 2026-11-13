# Step 005 · 本步函数与数据记录

- [BlackboxAgentPaddock.register_agent](functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md)：当前主读，关注与 init、配置准备和 call_agent 的区别。
- [generate](functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)：完整调取上层主线，当前定位注册阶段。
- [SandboxState](classes/dressage/paddock/blackbox/common/state.py/SandboxState.md)：调取最新字段对照。
- [SandboxLease](classes/dressage/sandbox/types.py/SandboxLease.md)：注册时按轨迹找回原记录和入口。

原准备阶段记录保存在 [历史快照](../../before-registration-reading-2026-11-06/02-short-term-memory/overview.md)。新建卡片和调取不代表已经掌握；后续函数未提前建卡。
- [BlackboxServerClient.register_agent](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md)：当前展开请求正文、目标地址与响应交接。
