# Launch Agent 调度与准备数据流

![动作 4：run 调度配置与启动准备，在 CLI 执行处标出下一动作](flow.svg)

[返回动作 4](../README.md) · [返回原架构图](../../README.md) · [图文预览](index.html) · [完整示例](示例.json)

动作 4 从 Slime 侧调用 `run()` 开始，读清 Harness 的调度、配置与启动信息准备。Sandbox 的接收与落实在动作 5 下钻，真正执行 CLI 时接动作 6。本图给出分层骨架，不展开 CLI 运行或模型请求。

## 1 `generate()` 交出任务上下文

输入是已准备的 `sb`、工作目录、会话 ID、Adapter 地址、指令和时间预算。示例使用 `/workspace/demo`、`cagent-demo-0-0`、`http://192.0.2.10:18001` 和 `1800` 秒，均为教学值。

调用位置：`examples/coding_agent_rl/generate.py:205`，`await HARNESS_CLS().run(...)`。

## 2 `run()` 调度共同步骤

```text
ensure_agent_user(sb, workdir)
    → HarnessContext(workdir, session_id, adapter_url)
    → self.write_config(sb, ctx)
    → self.launch_and_wait(sb, ctx, prompt, time_budget_sec)
```

前三个上下文字段原样保留，另有默认 `model_label="slime-actor"`。`sb`、指令与预算继续独立传递。源码为 `slime/agent/harness/common.py:81`。

## 3 `write_config()`：配置内容 → 沙箱操作

| Harness | 内容 | 交给 Sandbox | 预期成果 |
| --- | --- | --- | --- |
| Claude Code | onboarding、运行权限设置 JSON | `sb.exec()` 写用户目录中的设置文件 | 配置可供 Agent 读取 |
| Codex | 模型、provider 地址、chat 协议 TOML | 编码后经 `sb.exec()` 写配置文件 | 指定模型入口配置就位 |

函数返回 `None`，成果是环境变化。记录器只捕获实际提交的命令，没有执行环境变化。动作 5 继续解释 `E2BSandbox.exec()` 怎样接收这些命令和用户参数。

## 4 `launch_and_wait()`：上下文与指令 → `cmd + env`

Claude 分支构造 `/usr/local/bin/claude -p ...`，并把 `adapter_url`、`session_id`、模型标签映射到进程环境变量。Codex 分支构造 `codex exec ...`，使用相应的模型入口和会话环境变量。

两者将工作目录、命令、环境和预算交给同一个 `run_agent()`。完整捕获值见示例中的 `exec_and_wait_input`。本例没有额外环境覆盖。

## 5 `run_agent()`：运行要求 → Sandbox 准备接口

先请求创建 `.harness` 日志目录，再交给 `exec_and_wait()`：

```text
cmd + user + env + workdir + out_file + time_budget_sec
```

动作 5 从这里继续：写启动脚本、清理旧状态、将准备好的启动请求交给执行后端。到真正启动 CLI 的 `setsid bash` / SDK `commands.run()` 接缝，进入动作 6。

**准备命令本身也会使用 `sb.exec()`**；它们的目的仍是管理环境。动作 6 专指这条图上通往 Agent CLI 的执行关系。

## 6 返回契约

`run()` 最终返回 `int`，调用者保存为 `agent_exit_code`。这个返回依赖下游执行与等待完成；本例的 `simulated_exit_code` 是记录器提供的模拟状态，不代表 Agent 已运行。

## 源码与校验

固定源码：`8c17b676cb57af1d17ee4402e91e9209af84b60b`。

已执行真实的公共 `run()`、两种 Harness 的配置与启动参数计算，以及 `run_agent()`。沙箱操作全部替换为记录器，`exec_and_wait()` 替换为参数捕获与模拟返回；单例元类以普通 ABC 元类替代。示例展示真实方法算出的配置请求、命令与环境数据。

Sandbox 后端、准备操作的实际副作用、CLI 启动和等待仅静态定位，未执行。环境接收端详见[动作 5](<../../5.Manage Sandbox/README.md>)。
