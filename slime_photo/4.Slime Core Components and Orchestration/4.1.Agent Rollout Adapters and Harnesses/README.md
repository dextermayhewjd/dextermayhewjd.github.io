![Agent Rollout Adapters and Harnesses 架构图](<Agent Rollout Adapters and Harnesses.svg>)

# Agent Rollout Adapters and Harnesses 图中文字与源码对应

图中包含 7 个方框和 8 条箭头。以下将方框主标题与括号内容合并展示，保留全部英文原文，并列出每条箭头的起点、终点和文字，以及各方框对应的源码文件。

[原始 SVG](<Agent Rollout Adapters and Harnesses.svg>) · [CodeWiki 对应章节](https://codewiki.google/github.com/thudm/slime#slime-core-components-and-orchestration-agent-rollout-adapters-and-harnesses)

## 方框主标题

| 编号 | 方框主标题 |
| --- | --- |
| 1 | External Platforms (Anthropic, OpenAI, etc.) |
| 2 | HTTP Adapters (AnthropicAdapter, OpenAIAdapter) |
| 3 | Slime Core (BaseAdapter, TrajectoryManager) |
| 4 | SGLang Backend |
| 5 | Agent Harnesses (ClaudeCodeHarness, CodexHarness) |
| 6 | Sandbox Environment (E2BSandbox) |
| 7 | Coding Agent CLIs (Claude, Codex) |

## 箭头文字和连接方向

| 编号 | 起点 | 终点 | 箭头文字 |
| --- | --- | --- | --- |
| 1 | External Platforms | HTTP Adapters | API Requests |
| 2 | HTTP Adapters | Slime Core | Translate & Forward |
| 3 | Slime Core | SGLang Backend | Generate Tokens |
| 4 | Slime Core | Agent Harnesses | Launch Agent |
| 5 | Agent Harnesses | Sandbox Environment | Manage Sandbox |
| 6 | Sandbox Environment | Coding Agent CLIs | Exec Commands |
| 7 | Coding Agent CLIs | HTTP Adapters | Make API Calls |
| 8 | HTTP Adapters | External Platforms | API Responses |

## 方框对应的源码文件

以下路径均相对于 Slime 仓库根目录，即同时包含 `slime/` 和 `examples/` 的目录。

| 方框主标题 | 对应文件 |
| --- | --- |
| External Platforms (Anthropic, OpenAI, etc.) | 外部平台，本仓库中的协议适配见下一行 |
| HTTP Adapters (AnthropicAdapter, OpenAIAdapter) | `slime/agent/adapters/anthropic.py`、`slime/agent/adapters/openai.py` |
| Slime Core (BaseAdapter, TrajectoryManager) | `slime/agent/adapters/common.py`、`slime/agent/trajectory.py` |
| SGLang Backend | `slime/backends/sglang_utils/sglang_engine.py`、`slime/backends/sglang_utils/deployment.py`、`slime/backends/sglang_utils/engine_group.py` |
| Agent Harnesses (ClaudeCodeHarness, CodexHarness) | `slime/agent/harness/claude_code.py`、`slime/agent/harness/codex.py`、`slime/agent/harness/common.py` |
| Sandbox Environment (E2BSandbox) | `slime/agent/sandbox.py` |
| Coding Agent CLIs (Claude, Codex) | CLI 本体为外部安装包；安装与启动代码位于上述 Harness 文件 |

## 辅助文件和组件组装入口

- 输出解析：`slime/agent/parsing.py`
- HTTP 服务运行：`slime/agent/aiohttp_threaded.py`
- 组件组装：`examples/coding_agent_rl/generate.py`

## 动作详解

- [动作 2 Translate & Forward](<2.Translate & Forward/README.md>)：HTTP Adapters (AnthropicAdapter, OpenAIAdapter) → Slime Core (BaseAdapter, TrajectoryManager)。
- [动作 3 Generate Tokens](<3.Generate Tokens/README.md>)：Slime Core → SGLang Backend，从模板编码到本轮生成记录的纵向数据流。
- [3.5 完成一次模型请求](<3.5.完成一次模型请求/README.md>)：接住生成记录，展开解码、解析、协议响应、轨迹记录和本轮请求收尾；这是补充阅读编号。
- [动作 4 Launch Agent](<4.Launch Agent/README.md>)：从 Slime 侧进入 `run()`，展开 Harness 的用户准备、配置和启动信息调度；沙箱实现下钻动作 5，CLI 执行接动作 6。
- [动作 5 Manage Sandbox](<5.Manage Sandbox/README.md>)：Agent Harnesses → Sandbox Environment，从命令与文件操作读到 E2B 实现、创建和收尾。

## 按一次模型请求继续阅读

原图用于定位组件和动作；下面按一次请求的数据处理顺序连接阅读入口。

| 阅读顺序 | 入口 | 看清什么输入输出 |
| --- | --- | --- |
| 1 | [动作 2 纵向数据流](<2.Translate & Forward/纵向数据流/README.md>) | 原始请求 → 消息列表与工具定义 |
| 2 | [动作 3 纵向数据流](<3.Generate Tokens/README.md>) · [图文预览](<3.Generate Tokens/index.html>) | 消息与工具定义 → 输入 token → SGLang 请求与生成记录 |
| 3 | [3.5 完成一次模型请求](<3.5.完成一次模型请求/README.md>) · [图文预览](<3.5.完成一次模型请求/index.html>) | 输出 token → 解析结果与 Reply → 客户端响应，并保存会话轨迹、结束本轮请求 |

`BaseAdapter._run_turn()` 贯穿这次请求；`TrajectoryManager` 在轨迹记录处展开。响应和记录读通后，再回到原图的动作 4–7，看 Agent 怎样启动并多次发起这些请求。

## 按一次 Agent 启动继续阅读

从[动作 4 Launch Agent](<4.Launch Agent/README.md>)开始，或沿[启动参数的纵向数据流](<4.Launch Agent/纵向数据流/README.md>)查看[图文预览](<4.Launch Agent/纵向数据流/index.html>)。

原图的 Core → Harness 箭头表达任务组织职责。这个版本的真实组装点是 `examples/coding_agent_rl/generate.py`，在这里将已有执行环境与启动参数交给 Harness 的 `run()`。动作 4 展开 Harness 的调度与准备，动作 5 下钻沙箱的接收和落实，动作 6 从 CLI 真正执行处继续，动作 7 展开模型请求。各动作按跨组件职责分层，同一函数可连接多条边。

## 组件延伸阅读

- [Slime Core 完整请求流程](<Slime Core 完整请求流程.md>)：模型输入、生成、响应和轨迹管理的逐步函数说明。
