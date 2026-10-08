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

## 组件延伸阅读

- [Slime Core 完整请求流程](<Slime Core 完整请求流程.md>)：模型输入、生成、响应和轨迹管理的逐步函数说明。
