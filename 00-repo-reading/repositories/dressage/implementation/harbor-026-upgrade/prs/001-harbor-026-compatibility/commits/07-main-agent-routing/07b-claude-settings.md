# C07b · Claude Code 的 settings 能否覆盖 Trial 路由？

**来源与状态**　C07 评审意见 ①。Harbor 0.26.0，定向修复已在工作树验证，尚未提交。

## ① 上游约定 · Claude 同时收到启动环境和 settings 文件

Harbor 把 `agent.kwargs.config` 作为原生 settings。用户可以传内联 JSON 或本地 JSON 文件。Harbor 的 `ClaudeCode._upload_base_settings()` 把它上传到沙箱，再通过 `claude --settings` 交给客户端。

## ② 修前表现 · 第二个 Trial 在 settings 写了另一地址，插件仍尝试申请 Gateway

第一个 Trial 配置正常，第二个在 `settings.env.ANTHROPIC_BASE_URL` 填了另一地址。C07a 校验通过；修前回归在调用 Gateway 的 `acquire()` 时失败。评审还观察到 Harbor 把另一地址交给了 CLI。这份证据截至启动配置，未观察到模型请求或凭证实际发往其他端点。

## ③ 原因定位 · 原探测检查了启动环境，遗漏了单独上传的 JSON

`model_connection` 指向 Gateway，只能说明 Harbor 解析出的连接正确。Claude 随后还能从 settings 读取同名环境变量。这就是为什么 C07a 的正常路由测试可以通过，而本例仍需要处理。

## ④ 修复决策 · 在申请 Gateway 前核对 settings 里的三个连接变量

显式的 `ANTHROPIC_BASE_URL` 须匹配配置中公布的 Gateway 地址。`ANTHROPIC_API_KEY` 和 `ANTHROPIC_AUTH_TOKEN` 由 Trial 注入，settings 中出现任一项就报错。普通工具权限照常交付。对文件输入，Job 保留已检查内容的私有副本供启动和重试使用，Trial 配置只记录路径，Job 关闭时清理副本。

## ⑤ 回归验证 · 先看拒绝时机，再看 Harbor 最终上传了什么

| 用例 | 从哪里判断通过？ |
|---|---|
| 三个变量各设一次冲突，分别使用内联和文件输入（6 例） | 第二个 Trial 导致整 Job 提前拒绝，Gateway 尚未申请，已分配凭证为零。 |
| 工具权限和匹配的公布地址，分别使用内联和文件输入（2 例） | Harbor 准备上传的 JSON 保留原设置。校验后改动源文件不影响待上传内容；关闭 Job 后原文件仍在，私有副本已清理。 |

测试入口在 Dressage 的 `tests/integrations/harbor/test_execution.py`，分别是 `test_claude_settings_conflict_precedes_gateway_allocation` 和 `test_claude_uploads_checked_settings`。[Harbor 上传原生 settings](https://github.com/harbor-framework/harbor/blob/3cb627394b95d3ae605f31e0d694edf508cf4b7b/src/harbor/agents/installed/claude_code.py#L542-L574) · [返回 C07 总览](README.md)
