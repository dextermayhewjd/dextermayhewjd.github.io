# 02 · Step 6 的短期记忆

[本步范围](../01-scope.md) · [前序记忆](../03-long-term-memory/overview.md)

| 源码文件 | 记录 | 首次接触 | 最近认识更新与状态 |
| --- | --- | --- | --- |
| `examples/coding_agent_rl/generate.py` | [boot_agent_sandbox](functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md) | 整体骨架中定位；Step 6 开始独立记录 | 2026-10-24 用户概括创建、进入与退出职责；准备和交付的具体步骤由助手补清，未逐项确认。已按 18868a79 校准并做父函数替身验证，旧版理解保留 |
| `examples/coding_agent_rl/sunabako_sandbox.py` | [SunabakoSandbox.__init__](functions/examples/coding_agent_rl/sunabako_sandbox.py/SunabakoSandbox.__init__.md) | Step 6，2026-10-24 | 2026-10-24 用户概括准备字段与构造实例；执行环境另在进入时创建的边界已补清 |
| `examples/coding_agent_rl/sunabako_sandbox.py` | [SunabakoSandbox.__aenter__](functions/examples/coding_agent_rl/sunabako_sandbox.py/SunabakoSandbox.__aenter__.md) | Step 6，2026-10-24 | 2026-10-24 用户概括按 image 启动环境；配置到 SDK 的关系已补清，内部机制未展开 |
| `examples/coding_agent_rl/sunabako_sandbox.py` | [SunabakoSandbox.__aexit__](functions/examples/coding_agent_rl/sunabako_sandbox.py/SunabakoSandbox.__aexit__.md) | Step 6，2026-10-24 | 2026-10-24 用户概括先保存再退出；保存条件、范围及失败后仍回收待反馈，无真实回收验证 |
| `slime/agent/sandbox.py` | [E2BSandbox（类）](classes/slime/agent/sandbox.py/E2BSandbox.md) | Step 3 在进入与退出中接触；Step 6 开始独立类卡 | 2026-10-22 用户表示基本理解 cand 与 E2BSandbox，接续 CLI 安装；底层 SDK 仍有未知，未运行真实沙箱 |
| `slime/agent/harness/common.py` | [install_npm_cli：安装主记录](functions/slime/agent/harness/common.py/install_npm_cli.md) | Step 6 在安装入口中定位，2026-10-22 接续展开 | 保留 2026-10-22 的上传与安装理解；2026-10-24 核对 AST 未变并补当前调用，等待与完整恢复未展开 |
| `slime/agent/harness/claude_code.py` | [共用 install_npm_cli 记录](functions/slime/agent/harness/common.py/install_npm_cli.md)；[ClaudeCodeHarness.install_cli 定位](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md) | Step 6 先定位，2026-10-22 接续展开 | 保留参数适配与委托的认识；2026-10-24 补未设置 native 包时的 npm 分支与当前返回位置 |

形成过程：[Step 6 · 从 scope 进入函数记录](../04-flow.md#boot-agent-sandbox-function-card)。

后续追问：[Step 6 · 本地客户端与远端地址](../04-flow.md#sandbox-client-and-address)。

类卡确认与整理：[Step 6 · E2BSandbox 类卡片](../04-flow.md#e2b-class-card)。

安装入口：[Step 6 · 从沙箱对象进入 CLI 安装](../04-flow.md#install-cli-entry)。

安装交接：[Step 6 · 上传与远端安装](../04-flow.md#upload-and-remote-install)。

本轮版本校准见 [boot_agent_sandbox 更新记录](../04-flow.md#boot-card-refresh-18868a79)；新增方法见 [Sunabako 连读记录](../04-flow.md#sunabako-lifecycle-methods)；安装复用与总结见[本次收束](../04-flow.md#agent-sandbox-closure-18868a79)。安装旧例、E2B 记录与长期快照保留各自原版本。
