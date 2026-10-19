# 第 2 章 模型协议、上下文与训练轨迹

[阅读路线](../../repo-reading-route.md) · [总目录](../../README.md)

**目录 ID：** `02-model-context`
**产物状态：** planned
**学习状态：** 统一见[阅读路线的当前接续](../../repo-reading-route.md#当前接续)。

**问题：** CLI 的模型请求如何进入共享流程，返回协议响应，并留下可用于训练的真实轨迹？

**前置：** 01；已连接 CLI 配置、HTTP 路由与任务会话。

**图文对照：** 4.1 的动作 2、3、3.5；补读会话结束。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 共享模型请求流程 | [slime/agent/adapters/common.py · BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L318) | trace | 协议转换、模板编码、模型生成、解析、响应与轨迹记录；具体协议见旁边 openai.py/anthropic.py。 |
| 实际模型调用 | [slime/agent/adapters/common.py · call_sglang_generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L442) | trace | 原生 SGLang /generate；协议兼容不表示已经支持任意云 API。 |
| 输出与工具解析 | [slime/agent/parsing.py · parse_model_output](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L25) | trace | 解析工具调用不等于执行工具；执行者是 CLI 或其他自定义 Agent。 |
| 会话轨迹与上下文分支 | [slime/agent/trajectory.py · TrajectoryManager](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L269) | trace | 第一遍看 record_turn/get_trajectory；token drift、分叉、mask 细节作为第二遍 explain 范围。 |
| 会话结束与训练样本导出 | [slime/agent/adapters/common.py · BaseAdapter.finish_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L245) | trace | 区分当前 HTTP 请求结束、会话关闭、Sample 导出和 cleanup-only drop_session。 |

**章内顺序：**

1. 取一份带工具的请求，沿 7 → 2 → 3 → 3.5 画输入输出。
2. 分别定位 OpenAI/Anthropic 路由、_translate、_respond；确认实际生成端是 SGLang。
3. 从 TurnRecord 到 record_turn，再到 finish_session/get_trajectory，核对 token、logprob、mask 与 reward 的来源。
4. 第二遍只选择一种上下文变化：追加工具结果、上下文压缩或分支；用 test_trajectory_manager_branching 理解行为。

**轨迹管理专题入口：** 已读过 `coding_agent_rl.generate()` 和 `BaseAdapter._run_turn()` 后，接着读 [Trajectory Management 专题阅读入口](<../../../4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/Trajectory Management/README.md>)。按三个小单元深入：历史接续与分叉、assistant 改写、token 对齐与 Sample 导出。该入口是本章第二遍的细分，不改变章节顺序或学习状态。

**验收问题：** 一轮协议响应和一份训练 Sample 有什么关系？为什么仅保存最终文本无法还原生成时的全部训练信息？

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](../../repo-reading-route.md#当前接续)。
