本文件保留 2026-10-23 按 Step 003 主 reference 修订前的 task flow。正文保留，仅调整相对链接；现行总结见 [本步 task flow](../05-task-flow.md)。

---

# 05 · 任务链路：启动沙箱中的 CLI，等待整次运行结束

> `generate` 把已经准备好的沙箱与任务参数交给 `BaseHarness.run`。Harness 准备运行账号与配置，把参数组成命令和环境变量，委派沙箱执行 CLI；CLI 结束后，退出码沿调用链回到 `generate`。

[本步 scope](../01-scope.md) · [函数与类记录](../02-short-term-memory/overview.md) · [原话与校准](../04-flow.md#launch-restatement-and-http-entry) · [收束与下一步](../04-flow.md#close-launch-open-request-entry)

## 1. 从哪里进入，带着什么

入口是 `generate.py:205` 的 `await HARNESS_CLS().run(...)`。当前选择 `ClaudeCodeHarness`，它使用 **`slime/agent/harness/common.py` 中的 `BaseHarness.run`**，并提供自己的 `write_config` 与 `launch_and_wait` 实现。

| 进入时已有的材料 | 本步怎样使用 |
| --- | --- |
| `sb`：已关联远端执行沙箱的本地对象 | 通过它在远端写文件、执行命令；CLI 已由 Step 5 安装 |
| `workdir` 与其中的题目文件 | Step 6 的准备结果；CLI 在这个目录处理任务 |
| `prompt` | 组成 `claude -p ...` 的命令参数，引导 CLI 读取题目 |
| `adapter_url`、`session_id` | 形成 CLI 的 API 地址与认证环境变量；会话已在 Step 4 登记 |
| `time_budget_sec` | 交给下层控制本次等待的时间预算 |

## 2. 按执行顺序接起来

从 `generate.py:205` 调用并等待 `HARNESS_CLS().run(...)` 开始，下面按正常完成路径从上往下读。表中的 `→` 表示进入被调用的函数；“完成后到哪里”明确写出继续执行或返回的位置。

| 顺序 | 当前执行到的代码 | 这段完成什么 | 完成后到哪里 |
| --- | --- | --- | --- |
| 1 | `BaseHarness.run:97` → `ensure_agent_user` | 等远端账号、目录归属与 Git 设置准备完成 | 返回 `run:98` |
| 2 | `BaseHarness.run:98–102` | 创建本地 `ctx`，收拢运行参数 | 继续 `run:103` |
| 3 | `BaseHarness.run:103` → `ClaudeCodeHarness.write_config:44–55` | 经 `sb.exec` 写好远端 CLI 配置 | 返回 `run:104` |
| 4 | `BaseHarness.run:104` → `ClaudeCodeHarness.launch_and_wait:58–70` | 进入启动方法，先组成 `cmd` 与 `env` | 到 `launch_and_wait:71`，调用并等待 `run_agent` |
| 5 | `run_agent:109–110` | 经 `sb.exec` 准备 `.harness` 输出目录 | 到 `run_agent:111`，调用并等待 `exec_and_wait` |
| 6 | `exec_and_wait:107–138` | 写启动脚本、清理上次标记，经 `sb.exec` 启动远端 CLI | 启动操作返回后，继续 `exec_and_wait:139`；CLI 可在远端继续运行 |
| 7 | `exec_and_wait:139` → `_await_done_marker:65–79` | 反复查询完成标记；CLI 退出后，启动脚本写入退出码，查询读到它 | 返回 `exec_and_wait:140` |
| 8 | `exec_and_wait:140–145` | 根据退出码与输出选项，返回 `(exit_code, output)` | 回到 `run_agent:111` 解包，然后开始下面的逐层返回 |

源码位置：`BaseHarness.run` 与 `run_agent` 在 `harness/common.py`；两个 `ClaudeCodeHarness` 方法在 `harness/claude_code.py`；`exec_and_wait` 与 `_await_done_marker` 在 `sandbox.py`。下方各交接段链接对应函数卡片。

```text
exec_and_wait 返回 (exit_code, output)
    ↓ run_agent:111 解包，122 返回 exit_code
    ↓ launch_and_wait:71 返回同一个 exit_code
    ↓ BaseHarness.run:104 返回同一个 exit_code
    ↓ generate.py:205 赋给 agent_exit_code
    ↓ generate.py:213 才开始 swe.git_diff(...)
```

第 4 行进入 `launch_and_wait` 后，第 5–8 行都在这次调用内部完成。最外层 `generate` 一直等在第 205 行，直到退出码沿上面的返回链交回来。第 6 行的启动操作完成、第 7 行等到 CLI 整体结束，是两个不同的时刻。

命令内容、启动防重、输出读取与异常分支仍留在函数卡片中；下面沿用四次交接，解释这些执行步骤如何连接输入与结果。

### 交接一：已有沙箱与参数 → CLI 运行前提

- [ensure_agent_user](../02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) 使用已有 `sb`，准备 `agent` 账号、目录归属和 Git 设置。执行沙箱与工作目录已经存在。
- [HarnessContext](../02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md) 把 `workdir`、`session_id`、`adapter_url` 等收在一个本地对象中，供后面的具体 Harness 方法取用。
- 交接结果是“可用的账号与目录 + 本地上下文”，接着进入 `run:103`。

### 交接二：运行前提 → 远端 CLI 配置

- [ClaudeCodeHarness.write_config](../02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) 在本地组成 JSON，通过 `sb.exec` 写进远端沙箱的两个配置文件：`/home/agent/.claude.json` 与 `/home/agent/.claude/settings.json`。
- 这些配置配合后续启动选项，使 CLI 能按该 Harness 的无人值守方式运行；修改的是配置文件，CLI 程序代码保持原样。
- 此方法返回 `None`；结果保留在远端文件中，随后进入 `run:104`。

### 交接三：上下文与 prompt → 远端运行的 CLI

- [ClaudeCodeHarness.launch_and_wait](../02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) 的 58–70 行把 `prompt` 组成命令，把 `ctx` 的地址、编号等字段组成 `env`。CLI 最终获得命令参数、环境变量和配置文件；Python `ctx` 留在本地。
- 第 71 行进入 [run_agent](../02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md)：准备 `.harness` 目录，以 `agent` 用户、指定目录及输出文件委派 [exec_and_wait](../02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)。
- `exec_and_wait` 写入启动脚本，再经 `sb.exec` 启动远端 CLI。脱机运行、一次启动请求的重试防重和完成标记轮询保留在该卡片中。
- 账号与配置准备此前已经执行过远端命令；这里新发生的是启动 CLI 本身。`launch_and_wait` 包含准备以及委派执行、等待整个过程。

### 交接四：CLI 结束 → 退出码返回调用方

- 启动脚本在 CLI 命令结束后，把退出码写入完成标记；`_await_done_marker` 轮询取得它，交回 `exec_and_wait`。
- `exec_and_wait` 返回 `(exit_code, output)`；`run_agent` 接住退出码并忽略第二项，再逐层返回给 `generate` 的 `agent_exit_code`。
- CLI 的标准输出与错误输出写在 `.harness/trajectory.jsonl`；模型请求的训练轨迹由 Adapter 的 manager 另行记录。文件输出与训练轨迹各有自己的生成路径。
- 本页按正常完成路径说明返回；时间预算耗尽等分支继续保留在卡片中。接下来的 `swe.git_diff` 收集仓库改动，供后续评测使用。

## 3. 等待期间留下哪一个问题

```text
Step 7：启动 CLI ─────────── 等待整次 CLI 执行 ─────────── 取得退出码
                              │
                 CLI 需要模型时发出 HTTP 请求
                              │
                 Step 8：Adapter 怎样接收并处理？
                              │
                        回复交回 CLI，继续任务
```

到这里可以收拢“材料怎样变成一次 CLI 运行，以及怎样取得运行结果”。一次模型回复回到 CLI 时，整次 CLI 执行仍可能继续；接收机制发生在上面的等待区间。

[Step 8](../../step-009-adapter-request-entry/01-scope.md) 专门接清：服务怎样监听、URL 怎样绑定 `_run_turn`、`request` 怎样解析成 `body`，再接回已经读过的模型处理流程。Step 7 原有的接收入口追问与参考保留为形成过程。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 调用与返回：[generate.py:203–215](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L203-L215)。
- 本地编排与委派：[harness/common.py:81–122](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L81-L122)。
- 具体配置与启动：[harness/claude_code.py:44–71](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L44-L71)。
- 远端执行与等待：[sandbox.py:65–145](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L65-L145)。
- 本页由 LLM 根据已发生的阅读与用户整体复述整理。配置写入位置、ctx 的去向及准备/执行边界的校准仍保留为助手说明，未代填为用户确认。
- 本次静态核对；已有局部验证归属各卡片，没有新增真实沙箱、CLI 或模型运行。

</details>
