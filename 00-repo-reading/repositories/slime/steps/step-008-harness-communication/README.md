# Step 8 · Harness 启动 CLI 与等待返回

**目录编号调整**：本目录由原 Step 007 顺延而来；历史过程、函数来源和固定样例里的原编号保留当时语境，见[新旧编号对照](../../step-numbering-2026-10-23.md)。本次不改写原源码版本或学习结论。

[前一步：准备任务工作区](../step-007-prepare-workspace/README.md) · [下一步：Adapter 接收请求](../step-009-adapter-request-entry/README.md) · [当前阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

本步把准备好的沙箱与任务参数接到 `harness/common.py::BaseHarness.run`，读清账号与目录准备、上下文、CLI 配置、启动以及退出码返回。2026-10-23 按用户确认先收拢这一段，运行期间的 HTTP 接收问题由 Step 9 继续。

- [01 · 阅读范围](01-scope.md)：继承完整任务骨架，展开第 4 项的启动与等待。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：保留已读启动链，以及当时为接收入口追问调取的 `_run_turn`。
- [03 · 前序记忆](03-long-term-memory/overview.md)：进入本步时合并 Step 7 的 `03 + 02`，共 38 份记录，保持原快照。
- [04 · 问题与解释](04-flow.md)：原始问题、复述、校准及范围拆分的经过。
- [05 · 阅读后的任务总结](05-task-flow.md)：按 Step 004 的结构接住前序输入，串起执行交接，说明结果去向与后续边界。

当前场景仍为 Claude Code / Anthropic Adapter / E2B，源码绑定 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。用户已有启动阶段的整体复述；配置位置、ctx 去向及执行边界的校准保留其证据状态，详见 [flow](04-flow.md#launch-restatement-and-http-entry)。总结不表示所有下层机制均已掌握或真实运行。

原有[通信参考](references/run-communication-path.md)与[拆分前 scope](references/scope-before-step-008.md)保留历史。HTTP 接收的主动阅读入口统一接到 [Step 9 scope](../step-009-adapter-request-entry/01-scope.md)。
