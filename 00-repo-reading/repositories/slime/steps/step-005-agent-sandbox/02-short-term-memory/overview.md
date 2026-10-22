# 02 · Step 5 的短期记忆

[本步范围](../01-scope.md) · [前序记忆](../03-long-term-memory/overview.md)

| 源码文件 | 记录 | 首次接触 | 最近认识更新与状态 |
| --- | --- | --- | --- |
| `examples/coding_agent_rl/generate.py` | [boot_agent_sandbox](functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md) | 整体骨架中定位；Step 5 开始独立记录 | 2026-10-22 用户表示基本完成本函数的理解；准备、交付与回收已收拢为 task flow，底层机制保留未知；已有局部验证，未运行真实沙箱 |
| `slime/agent/sandbox.py` | [E2BSandbox（类）](classes/slime/agent/sandbox.py/E2BSandbox.md) | Step 2 在进入与退出中接触；Step 5 开始独立类卡 | 2026-10-22 用户表示基本理解 cand 与 E2BSandbox，接续 CLI 安装；底层 SDK 仍有未知，未运行真实沙箱 |
| `slime/agent/harness/common.py` | [install_npm_cli：安装主记录](functions/slime/agent/harness/common.py/install_npm_cli.md) | Step 5 在安装入口中定位，2026-10-22 接续展开 | 用户已复述上传、远端安装与 for 的控制作用；包处理差别及重试范围已补说明，等待与完整恢复机制未展开 |
| `slime/agent/harness/claude_code.py` | [共用 install_npm_cli 记录](functions/slime/agent/harness/common.py/install_npm_cli.md)；[ClaudeCodeHarness.install_cli 定位](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md) | Step 5 先定位，2026-10-22 接续展开 | 参数适配与委托入口；完整场景和实现说明集中在 common 卡片 |

形成过程：[Step 5 · 从 scope 进入函数记录](../04-flow.md#boot-agent-sandbox-function-card)。

后续追问：[Step 5 · 本地客户端与远端地址](../04-flow.md#sandbox-client-and-address)。

类卡确认与整理：[Step 5 · E2BSandbox 类卡片](../04-flow.md#e2b-class-card)。

安装入口：[Step 5 · 从沙箱对象进入 CLI 安装](../04-flow.md#install-cli-entry)。

安装交接：[Step 5 · 上传与远端安装](../04-flow.md#upload-and-remote-install)。
