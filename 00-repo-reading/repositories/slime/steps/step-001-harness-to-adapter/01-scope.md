# 01 · 阅读范围：从启动到模型请求入口

[本步入口](README.md) · [前序函数记忆](03-long-term-memory/overview.md)

## 1. 阅读目标

沿用理解 Coding Agent 的整体目标。本步只回答：`HARNESS_CLS().run(...)` 怎样启动 CLI，CLI 的模型请求又怎样进入 `BaseAdapter._run_turn(...)`？以已有 Claude Code / Anthropic 分支说明连接。

## 2. 找到指挥官函数：`BaseHarness.run`

外层调用位于 `examples/coding_agent_rl/generate.py:205`，实现入口为 `slime/agent/harness/common.py:81`。它组织运行上下文、配置和启动等待；本步沿 `launch_and_wait` 找到外部 CLI，再定位 Adapter 的 HTTP 路由。

源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。必要前提是已有沙箱、工作区、任务提示、会话与 Adapter 地址；只在影响本步连接时回查其创建。

## 3. 给出真正干活的核心骨架

以下是阅读导航，箭头中的 HTTP 明确表示跨进程请求，其余箭头表示调用交接；参数省略。

```text
HARNESS_CLS().run(...)
  → BaseHarness.run(...)
  → ClaudeCodeHarness.launch_and_wait(...)
  → run_agent(...)：启动外部 Claude Code CLI，等待退出

CLI 运行期间：
  Claude Code CLI
    ── HTTP POST /v1/messages ──→ AnthropicAdapter 的 HTTP 服务
                                  → BaseAdapter._run_turn(request)
```

本步最初定位到 `_run_turn` 收到请求。用户确认函数调用链清楚后，进一步明确追问“为什么这里有 HTTP 服务，以及信息怎样传来传去”。据此在同一步补充服务监听、请求解析和响应回到 CLI 的过程；主要新增源码为 `slime/agent/aiohttp_threaded.py:46–98` 和 `slime/agent/adapters/anthropic.py:71–75`。

CLI 的完整工具循环、环境安装、线程生命周期与模型生成内部细节继续留白；HTTP 往返发生在 Harness 等待 CLI 整体退出期间。
