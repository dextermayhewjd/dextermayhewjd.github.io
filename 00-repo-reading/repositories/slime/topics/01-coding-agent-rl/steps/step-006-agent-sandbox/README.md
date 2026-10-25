# Step 6 · 启动执行沙箱

**目录编号调整**：本目录由原 Step 005 顺延而来；历史过程、函数来源和固定样例里的原编号保留当时语境，见[新旧编号对照](../../../../step-numbering-2026-10-23.md)。本次不改写原源码版本或学习结论。

[前一步：登记会话配置](../step-005-agent-preparation/README.md) · [当前阅读进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

**2026-10-24 版本校准与总结**：[当前 scope](01-scope.md)和 [task flow](05-task-flow.md)已按 `18868a79` 接清准备、交付和回收。[boot_agent_sandbox 主卡](02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md)及三张 Sunabako 方法卡已接入[阅读导航](01-scope.md#reading-path)，原有 npm 安装记录补充了当前调用与实现未变的核对。[旧 scope](references/scope-at-2f231865.md)与[旧 task flow](references/task-flow-at-2f231865.md)完整保留；E2B、安装旧例和长期继承保持各自历史来源。

本步围绕 `boot_agent_sandbox`，弄清：给定任务的镜像，怎样取得供 Agent 使用的执行沙箱 `sb`，并在使用结束后回收？当前 task flow 已收拢这条交接；底层等待与故障恢复继续作为按需深入项，具体阅读状态见唯一路线。

## 从这里开始

- [01 · 阅读范围](01-scope.md)：整体骨架、本步局部骨架、阅读导航与停止位置。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：`boot_agent_sandbox` 的编排、Sunabako 的初始化／进入／退出、旧 E2B 对象记录，以及 `install_npm_cli` 的安装主记录；`ClaudeCodeHarness.install_cli` 保留为参数适配与委托的引用入口。
- [03 · 前序记忆](03-long-term-memory/overview.md)：继承 Step 5 的 `03 + 02`，共 30 份函数记录和 1 份类记录。
- [04 · 问题与解释](04-flow.md)：本轮的范围确认与后续真实讨论。
- [05 · 阅读后的任务总结](05-task-flow.md)：镜像进入、CLI 就绪、交出 sb、调用方使用与退出回收的完整交接。

当前 scope、task flow、boot_agent_sandbox 主卡与三张 Sunabako 方法卡使用 `/home/fredkeira/projects/slime` 的 `18868a79`；安装卡已补当前调用，但完整旧例与其余旧卡继续保留历史 checkout `/home/hongshi/projects/slime` 的 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 证据。源码校准与学习反馈分别记录，总结不代表全部机制已掌握或已运行真实沙箱。
