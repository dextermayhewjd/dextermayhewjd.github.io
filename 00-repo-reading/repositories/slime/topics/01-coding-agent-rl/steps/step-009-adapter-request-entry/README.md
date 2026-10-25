# Step 9 · 沙箱中的 CLI 怎样经 Adapter 请求 SGLang

**目录编号调整**：本目录由原 Step 008 顺延而来；历史过程、函数来源和固定样例里的原编号保留当时语境，见[新旧编号对照](../../../../step-numbering-2026-10-23.md)。本次不改写原源码版本或学习结论。

[前一步：启动 CLI 与等待返回](../step-008-harness-communication/05-task-flow.md) · [当前阅读进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

Step 8 已把启动材料接到沙箱中的 CLI，并整理了等待与执行结果返回。本步围绕用户提出的“沙箱执行时怎样把请求送到 SGLang”，接清 **CLI → HTTP → Adapter → HTTP → SGLang → 回复**，同时补齐路由、`request` 与 `body` 的来路。

**运行位置**：本步发生在 `_generate` 等待 `harness.run(...)` 的过程中；步骤编号表示阅读顺序。

- [01 · 正式阅读范围](01-scope.md)：已采用用户确认的第三版，结合清晰的讲解顺序、调用层级和分点总结，沿“地址交付 → 请求接收 → 模型请求”阅读。
- 历史 scope：[第一版](references/archive/scope-v1.md)与[第二版](references/archive/scope-v2.md)完整归档，保留原有内容与来源。
- [HTTP 请求怎样从监听进入处理函数](references/http-request-dispatch.md)：第②段的统一阅读入口；先看以同一个 app 为中心的 Mermaid 关系图，再沿请求主线、三段代码和函数位置表阅读。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：保留原先调入的两张旧卡，另复用现行 launch_and_wait、_AdapterService 类卡、路由卡和 [run_app_in_thread](02-short-term-memory/functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md)；其余现行记录由 scope 导航引用。
- [03 · 前序累计记忆](03-long-term-memory/overview.md)：历史合并快照，共 43 份函数与类记录；保留原话、未知和各自来源，本轮未刷新继承。
- [04 · 问题与解释](04-flow.md)：原始缺口、范围确认及后续理解修正。
- [05 · 阅读后的任务总结](05-task-flow.md)：收拢服务准备、地址交付、请求匹配、模型调用与响应返回；区分本轮复述、助手校准与未验证内容。
- [通信路径参考](references/run-communication-path.md#adapter-request-entry)：保留旧版监听、路由与请求解析说明，版本以该文为准。

从 [① launch_and_wait:92 的地址交付](01-scope.md#breadcrumb-cli-address)开始，追 `ctx.adapter_url → env → 沙箱中的 CLI`；再看 [② 路由与请求接收](01-scope.md#breadcrumb-adapter-entry)，最后接 [③ SGLang 请求与回复](01-scope.md#breadcrumb-sglang-request)。中间包装只跟参数传递；遇到不清楚的来源，再按 scope 回查并返回。主读 Claude Code / Anthropic 路径。
