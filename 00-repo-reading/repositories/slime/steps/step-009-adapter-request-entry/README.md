# Step 9 · CLI 的 HTTP 请求怎样进入 Adapter

**目录编号调整**：本目录由原 Step 008 顺延而来；历史过程、函数来源和固定样例里的原编号保留当时语境，见[新旧编号对照](../../step-numbering-2026-10-23.md)。本次不改写原源码版本或学习结论。

[前一步：启动 CLI 与等待返回](../step-008-harness-communication/05-task-flow.md) · [当前阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

Step 8 已把启动材料接到远端 CLI，并整理了等待与退出码返回。用户仍不清楚：CLI 发出请求后，谁接收它、怎样找到 `_run_turn`，函数里的 `body` 又从哪里来。本步专门补这段交接。

**运行位置**：本步发生在 `HARNESS_CLS().run(...)` 等待 CLI 的过程中；步骤编号表示阅读顺序。

- [01 · 阅读范围](01-scope.md)：完整骨架、服务准备与请求处理两条局部路径，以及首个观察点。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：先调取 `_AdapterService.__init__` 与 `_run_turn` 两张完整旧卡，供直接回看；接收侧新函数逐处阅读后记录。
- [03 · 前序累计记忆](03-long-term-memory/overview.md)：合并 Step 8 的 `03 + 02`，共 43 份函数与类记录；保留原话、未知和各自来源。
- [04 · 问题与解释](04-flow.md)：原始缺口、范围确认及后续理解修正。
- [05 · 阅读后的任务总结](05-task-flow.md)：本步阅读之后再收拢。
- [通信路径参考](references/run-communication-path.md#adapter-request-entry)：承接前一步已有的监听、路由与请求解析说明。

从 `adapters/anthropic.py:48–50` 的 `AnthropicAdapter._register_routes` 开始，先看清 `POST /v1/messages` 与处理函数的对应；再按 scope 回查服务如何开始监听，接回 `_run_turn:325` 的 JSON 读取。主读 Claude Code / Anthropic 路径，OpenAI 路径仅对照入口。
