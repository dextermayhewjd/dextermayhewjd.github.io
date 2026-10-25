# Step 8 · Harness 启动 CLI 与等待返回

**目录编号调整**：本目录由原 Step 007 顺延而来；历史过程、函数来源和固定样例里的原编号保留当时语境，见[新旧编号对照](../../../../step-numbering-2026-10-23.md)。本次不改写原源码版本或学习结论。

[前一步：准备任务工作区](../step-007-prepare-workspace/README.md) · [下一步：Adapter 接收请求](../step-009-adapter-request-entry/README.md) · [当前阅读进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

本步把准备好的沙箱与任务参数接到 `harness/common.py::BaseHarness.run`，读清账号与目录准备、上下文、CLI 配置、启动以及退出码返回。2026-10-23 按用户确认先收拢这一段，运行期间的 HTTP 接收问题由 Step 9 继续。

**2026-10-24 当前材料**：[scope](01-scope.md)已对齐 `18868a79`，入口为 `_generate:287 → BaseHarness.run:81–104`；`launch_and_wait` 已复用 Step 002 新版卡片，并补充 PID 与压缩事件的协作说明。[更新前 scope](references/scope-at-2f231865.md)及[原启动卡片](references/launch-and-wait-before-current-reuse.md)完整保留，其余旧记录与继承快照按各自版本接续。

按用户反馈，当前启动卡片恢复整体大图作为主要入口，并将三段源码与图对应；PID 和压缩预算放在启动命令旁按需展开。[整理前版本](references/launch-and-wait-before-main-diagram-restoration.md)保留完整内容。

- [01 · 阅读范围](01-scope.md)：继承完整任务骨架，展开第 4 项的启动与等待。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：保留已读启动链，以及当时为接收入口追问调取的 `_run_turn`。
- [03 · 前序记忆](03-long-term-memory/overview.md)：保留原进入本步时合并 Step 7 的 `03 + 02` 快照，共 38 份记录；本次未刷新继承。
- [04 · 问题与解释](04-flow.md)：原始问题、复述、校准及范围拆分的经过。
- [05 · 阅读后的任务总结](05-task-flow.md)：已按当前版本接住前序输入，串起执行交接、结果回传与后续边界。

当前 scope、`launch_and_wait` 卡片和 task flow 使用 `/home/fredkeira/projects/slime` 的 `18868a79`；`exec_and_wait` 已局部更新完成文件读取与源码位置。本步其余旧卡和类记录保留各自历史场景，前序新卡按需复用；[旧 task flow](references/task-flow-at-2f231865.md)完整归档。已有整体复述和未知继续保留，具体收束依据见[本轮记录](04-flow.md#harness-execution-closure-20261025)，不等同于全部实现已掌握或真实运行。

原有[通信参考](references/run-communication-path.md)与[拆分前 scope](references/scope-before-step-008.md)保留历史。HTTP 接收的主动阅读入口统一接到 [Step 9 scope](../step-009-adapter-request-entry/01-scope.md)。
