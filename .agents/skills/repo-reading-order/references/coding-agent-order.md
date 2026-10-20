# 推荐实例：为什么可以先看 Harness.run

本例承接已建立的 [Coding Agent 核心骨架](../../repo-reading-scope/references/coding-agent-scope.md)，展示怎样选择下一处入口。它是阅读建议，不表示当前已开始或完成相关函数的学习。

## 当前问题决定入口

若当前问题是“Agent 怎样被启动并开始处理任务”，优先推荐 `BaseHarness.run`：它把准备好的工作区、会话和 Adapter 地址交给具体 Harness，继续配置并启动 CLI。这处能把外层任务编排接到真正运行的 Agent。

`generate` 的七个步骤先用来建立方向，深入顺序可以从其中最能回答当前问题的一步开始。选择 Harness 的理由是它与启动问题直接相关。

| 当前想弄清的问题 | 优先候选 | 第一遍停止位置 |
| --- | --- | --- |
| Agent 怎样开始工作？ | `BaseHarness.run` → 具体 Harness 的 `launch_and_wait` | 看清上下文、配置、CLI 启动以及等待退出 |
| 运行中的 Agent 怎样获得一次模型回复？ | `BaseAdapter._run_turn` | 看清一次请求的转换、生成、响应与轨迹交接 |
| 为什么评测结果或 reward 不符合预期？ | `swe.run_evaluation` 及选中的评测分支 | 看清输入的 diff、评测协议与评分结果来源 |
| 已有轨迹怎样成为返回的样本？ | `BaseAdapter.finish_session` | 看清会话轨迹、评分与样本的交接 |

用户已明确要研究消息格式时，沿用既有 `_translate` 场景即可，不强制改为 Harness 起步。

## 以启动问题为例：最小前置和回查

进入 `run` 前，先知道三组信息：工作区与任务提示、本次会话标识、CLI 将访问的 Adapter 地址；时间预算作为本次运行的上限。首次阅读先知道这些输入的用途。

在 `run` 内看清 `ensure_agent_user`、上下文构造、`write_config` 与 `launch_and_wait` 的交接。需要时再回查：

- 工作区里准备了什么：看 `swe.prepare_workspace`。
- 会话标识从哪里来、在哪里登记：看 `generate` 的标识赋值与 `BaseAdapter.open_session`。
- 沙箱如何创建或隔离：看 `boot_agent_sandbox` 与具体环境实现。
- CLI 的请求怎样到达模型处理：沿具体 Harness 的地址配置，接到 Adapter 的路由与 `_run_turn`。

每次只补当前缺少的关系，随后回到 Harness 或外层骨架。涉及底层隔离、安装、网络或协议细节时再另定问题。

## 真实执行边界

以 Claude Code Harness 为例，`launch_and_wait` 配置 `ANTHROPIC_BASE_URL=ctx.adapter_url`、`ANTHROPIC_AUTH_TOKEN=ctx.session_id`，通过 `run_agent` 启动外部 CLI 并等待结束。

CLI 运行期间会经 HTTP 请求 Adapter；这发生在等待 CLI 退出的期间。CLI 的整个工具循环不位于 `BaseHarness.run` 中，`BaseAdapter._run_turn` 也只处理其中一次模型请求。完成启动入口的阅读后，可以把这项运行期交互作为下一问。

## 固定源码依据

以下均基于 Slime 提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，静态核对，不是运行验证：

- [generate.py · generate，182 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L182)：准备调用所需信息并连接七个外层环节。
- [harness/common.py · BaseHarness.run，81 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L81)：确保用户、构造上下文、写配置、启动并等待。
- [harness/claude_code.py · launch_and_wait，57 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L57)：具体 CLI 命令、环境配置和运行交接。
- [adapters/common.py · open_session，210 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L210)、[finish_session，245 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L245)、[_run_turn，318 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L318)：会话登记、样本导出和一次模型请求处理。
- [swe.py · prepare_workspace，177 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L177)、[run_evaluation，239 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L239)：工作区内容准备与评测入口。
