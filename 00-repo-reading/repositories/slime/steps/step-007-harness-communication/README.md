# Step 7 · Harness 启动与跨组件通信

[前一步：准备任务工作区](../step-006-prepare-workspace/README.md) · [当前阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

Adapter、执行沙箱和工作区已有准备记录。本步单独回答：Harness 怎样启动沙箱里的 CLI，CLI 怎样请求 Adapter，Adapter 怎样请求 SGLang，结果又怎样返回。

- [01 · 阅读范围](01-scope.md)：继承完整任务骨架，展开第 4 项的启动、通信与返回位置。
- [02 · 本步短期记忆](02-short-term-memory/overview.md)：`BaseHarness.run` 负责组织本次启动，`ClaudeCodeHarness.write_config` 准备远端 CLI 配置，`ClaudeCodeHarness.launch_and_wait` 把输入变成 CLI 命令与环境变量；[HarnessContext 类卡片](02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)解释中间传递的参数对象。
- [03 · 前序记忆](03-long-term-memory/overview.md)：合并 Step 6 的 `03 + 02`，共 38 份函数与类记录；已有 `_run_turn`、模型请求与沙箱对象记录从这里复用。
- [04 · 问题与解释](04-flow.md)：保存原始通信问题、助手解释和用户要求独立成步的纠正。
- [05 · 阅读后的任务总结](05-task-flow.md)：沿 scope 读通后再收拢，不把初始解释当作阅读完成。

先看 [scope 的局部导航](01-scope.md#harness-local-navigation)：短回顾 `BaseHarness.run:97` 已读的 `ensure_agent_user`，从 98–102 行的 `ctx` 接着读，经 103 行的配置，再到 104 行进入重点 `ClaudeCodeHarness.launch_and_wait:57–71`。需要恢复整体关系时，打开 [通信路径参考](references/run-communication-path.md)：它按运行位置、目标地址、传递内容与返回方向连接各函数。

本步沿用 Claude Code / Anthropic Adapter / E2B 场景，以及 Slime 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。用户已确认独立研究这条链路；目前的源码解释仍待阅读反馈，没有真实远端运行证据。Step 6 的工作区准备记录和未收束项保留。
