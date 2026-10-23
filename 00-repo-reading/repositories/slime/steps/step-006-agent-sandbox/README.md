# Step 6 · 启动执行沙箱

**目录编号调整**：本目录由原 Step 005 顺延而来；历史过程、函数来源和固定样例里的原编号保留当时语境，见[新旧编号对照](../../step-numbering-2026-10-23.md)。本次不改写原源码版本或学习结论。

[前一步：登记会话配置](../step-005-agent-preparation/README.md) · [当前阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

本步围绕 `boot_agent_sandbox`，弄清：给定任务的镜像，怎样取得供 Agent 使用的执行沙箱 `sb`，并在使用结束后回收？本步的准备、交付与回收关系已收拢为 task flow；底层等待与故障恢复继续作为按需深入项，具体阅读状态见唯一路线。

## 从这里开始

- [01 · 阅读范围](01-scope.md)：整体骨架、本步局部骨架、阅读导航与停止位置。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：`boot_agent_sandbox` 的编排、`E2BSandbox` 的对象状态与操作入口，以及 `install_npm_cli` 的安装主记录；`ClaudeCodeHarness.install_cli` 保留为参数适配与委托的引用入口。
- [03 · 前序记忆](03-long-term-memory/overview.md)：继承 Step 5 的 `03 + 02`，共 30 份函数记录和 1 份类记录。
- [04 · 问题与解释](04-flow.md)：本轮的范围确认与后续真实讨论。
- [05 · 阅读后的任务总结](05-task-flow.md)：镜像进入、CLI 就绪、交出 sb、调用方使用与退出回收的完整交接。

源码沿用 `/home/hongshi/projects/slime` 的固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。任务主线的总结不代表所有内部机制均已掌握或已运行真实沙箱。
