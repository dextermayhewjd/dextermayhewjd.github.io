本文件是 [Step 007 原任务总结](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/05-task-flow.md)的完整副本，2026-10-23 按用户确认保存为 task flow 的新 reference。重点参考第 2 节：入口函数的直接部分 → 各部分内部的子调用 → 作用、结果与返回位置。整体四部分结构继续沿用 [Step 003 主样例](step-003-trajectory-to-samples.md)。

正文保留，仅调整相对链接；四个主分支、函数名、行号、源码版本和已读边界属于此例，其他步骤按实际源码确定。较短的调用链可以更简洁，不要求所有 task flow 都展开到相同层数。

---

# 05 · 任务链路：启动沙箱中的 CLI，等待整次运行结束

> `generate` 把已经准备好的沙箱与任务参数交给 `BaseHarness.run`。Harness 准备运行账号与配置，把参数组成命令和环境变量，委派沙箱执行 CLI；CLI 结束后，退出码沿调用链回到 `generate`。

[本步 scope](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/01-scope.md) · [步骤入口](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/README.md) · [函数与类记录](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/overview.md) · [整体复述](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#launch-restatement-and-http-entry) · [本次整理](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#task-flow-step-three-format)

## 1. 本步接住哪些准备结果

入口是 `generate.py:205` 的 `await HARNESS_CLS().run(...)`。当前选择 `ClaudeCodeHarness`，它使用 **`slime/agent/harness/common.py` 中的 `BaseHarness.run`**，并提供自己的 `write_config` 与 `launch_and_wait` 实现。

| 进入时已有的材料 | 本步怎样使用 |
| --- | --- |
| `sb`：已关联远端执行沙箱的本地对象 | 通过它在远端写文件、执行命令；CLI 已由 Step 5 安装 |
| `workdir` 与其中的题目文件 | Step 6 的准备结果；CLI 在这个目录处理任务 |
| `prompt` | 组成 `claude -p ...` 的命令参数，引导 CLI 读取题目 |
| `adapter_url`、`session_id` | 形成 CLI 的 API 地址与认证环境变量；会话已在 Step 4 登记 |
| `time_budget_sec` | 交给下层控制本次等待的时间预算 |

沿用 `evaluation=False`、CLI 正常运行结束的场景。本页终点是 `run` 将退出码交回 `generate:205`；随后 `generate:213` 才开始收集代码改动。CLI 运行期间的 HTTP 接收入口由 Step 8 接续。

<a id="2-按执行顺序接起来"></a>

## 2. run 的四个部分，各自继续调用谁

<a id="launch-flow-diagram"></a>

`BaseHarness.run` 的主体只有①–④四个部分，依次完成。**缩进表示调用层级**：每个函数下面只展开它内部相关的调用；`→` 旁注交代产生的数据、作用与返回位置。图按已读范围裁剪，保留正常完成路径。

```text
generate.py:205  await HARNESS_CLS().run(...)
└─ BaseHarness.run                              [harness/common.py:81–104]
   │
   ├─ ① ensure_agent_user                       [run:97 → sandbox.py:390–399]
   │  └─ sb.exec                                [sandbox.py:392–399]
   │     → 在已有沙箱准备 agent 账号、目录归属和 Git 设置
   │  → 完成后回到 run:98
   │
   ├─ ② ctx = HarnessContext(...)               [run:98–102]
   │  → 构造本地上下文，将目录、会话编号、Adapter 地址交给③④
   │
   ├─ ③ ClaudeCodeHarness.write_config          [run:103 → claude_code.py:44–55]
   │  → 先在本地组装 settings JSON
   │  └─ sb.exec                                [claude_code.py:47–55]
   │     → 将配置写入远端 CLI 配置文件
   │  → 完成后回到 run:104
   │
   └─ ④ ClaudeCodeHarness.launch_and_wait       [run:104 → claude_code.py:57–71]
      → 先把 prompt 与 ctx 中的字段组成 cmd / env
      └─ run_agent                              [claude_code.py:71 → harness/common.py:107–122]
         ├─ sb.exec                             [harness/common.py:110]
         │  → 准备 .harness 输出目录并设置归属
         │
         └─ exec_and_wait                       [harness/common.py:111 → sandbox.py:82–145]
            ├─ sb.write_file                    [sandbox.py:113]
            │  → 把包含 CLI 命令的启动脚本写到远端
            ├─ sb.exec                          [sandbox.py:122–128]
            │  → 清理上一次运行的标记与输出
            ├─ sb.exec                          [sandbox.py:129–138]
            │  → 启动远端 CLI；启动操作返回后继续第 139 行
            └─ _await_done_marker               [sandbox.py:139 → 65–79]
               └─ sb.exec                       [sandbox.py:76]
                  → 反复查询完成标记，CLI 退出后取得脚本写入的退出码
            → 返回 (exit_code, output)           [sandbox.py:140–145]
         → 取出并返回 exit_code                  [harness/common.py:111、122]
      → 返回 exit_code                           [claude_code.py:71]
   → 返回 exit_code                              [harness/common.py:104]
generate.py:205 接住 agent_exit_code，随后在 213 行提取 diff
```

- **看 `run` 的整体职责时，先看四个主分支。** 需要追问某个部分如何完成，再沿它下面的缩进下钻；例如 `run_agent` 属于④内部。
- **读完子函数，回到它的父函数。** 第④分支要等 `run_agent`，后者要等 `exec_and_wait`；退出码就沿这些调用逐层返回。
- **远端运行与本地等待分开理解。** 启动操作返回后，CLI 可继续运行，本地进入 `_await_done_marker`；CLI 运行期间的 HTTP 请求由 Step 8 接续。它属于运行中的交互，图中不把 `_run_turn` 画成 `run_agent` 直接调用的子函数。

四个主分支的卡片：[① 用户与目录](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) · [② 上下文](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md) · [③ 配置](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) · [④ 启动与等待](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)。

④内部继续：[run_agent](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md) → [exec_and_wait（含完成标记等待）](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)。图中的 `sb.exec` / `sb.write_file` 保留沙箱接口层，不在此重复展开 SDK 内部。

<details>
<summary>展开四个主分支的源码与返回位置对照</summary>

此表按时间先后展开各分支；④内部占多行，仍属于同一个主分支。最后一列说明返回或继续的位置。行号属于本步固定版本，函数名直接链接对应卡片。

| 主分支 | 当前代码与卡片入口 | 动作与交接结果 | 接着执行哪里 |
| --- | --- | --- | --- |
| ① | `BaseHarness.run:97` → [ensure_agent_user](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) | 使用已有 `sb`，准备 `agent` 账号、目录归属与 Git 设置 | 返回 `run:98` |
| ② | `run:98–102` → [HarnessContext](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md) | 将工作目录、会话编号和 Adapter 地址收进本地 `ctx` | 继续 `run:103` |
| ③ | `run:103` → [ClaudeCodeHarness.write_config:44–55](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) | 经 `sb.exec` 写入远端 CLI 配置，配合启动选项支持无人值守运行；返回 `None` | 返回 `run:104` |
| ④ | `run:104` → [ClaudeCodeHarness.launch_and_wait:58–70](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | 将 `prompt` 组成 `cmd`，将 `ctx` 中的地址、编号等组成 `env`；Python `ctx` 留在本地 | 第 71 行调用并等待 `run_agent` |
| ④ | [run_agent:109–110](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md) | 经 `sb.exec` 准备 `.harness` 输出目录；将命令、环境、工作目录与运行用户 `agent` 交给执行层 | 第 111 行调用并等待 `exec_and_wait` |
| ④ | [exec_and_wait:107–138](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md) | 写启动脚本、清理上次标记，经 `sb.exec` 在远端启动 CLI | 启动操作返回，继续第 139 行；CLI 可在远端继续运行 |
| ④ | `exec_and_wait:139` → `_await_done_marker:65–79` | 查询完成标记；CLI 退出后，启动脚本把退出码写入标记，查询取得它 | 返回 `exec_and_wait:140` |
| ④ | `exec_and_wait:140–145` | 返回 `(exit_code, output)`；`run_agent` 取出退出码，忽略第二项 | `run_agent:122` 开始逐层返回 |

文件对应：`BaseHarness.run` 与 `run_agent` 在 `harness/common.py`；`ClaudeCodeHarness` 的方法在 `harness/claude_code.py`；`exec_and_wait` 与 `_await_done_marker` 在 `sandbox.py`。公共编排的完整输入输出见 [BaseHarness.run 卡片](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)。

退出码依次经过 **`run_agent:122 → launch_and_wait:71 → BaseHarness.run:104 → generate:205`**，赋给 `agent_exit_code`。第 4 行进入启动方法后，第 5–8 行都在这次调用内完成；最外层 `generate` 一直等待退出码返回。

- 第 1、3、5 行已经执行远端准备命令；第 6 行才启动 CLI 本身。
- 第 6 行的启动操作返回与第 7 行等到 CLI 整体结束，是两个时刻。等待期间，CLI 可以请求模型、处理工具结果并继续任务。

</details>

## 3. 最后交回什么，留下什么

沿用 [BaseHarness.run 的构造例](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md#本场景的输入与输出)：工作目录是 `/workspace/auth0-python`，假定 CLI 正常退出、退出码为 `0`。这是教学假定，没有执行真实任务。

| 结果或状态 | 保存在哪里，后续怎样使用 |
| --- | --- |
| `agent_exit_code = 0` | `exec_and_wait` 在本例返回 `(0, "")`；上层逐层只返回 `0`，由 `generate` 接住。它表示进程退出状态，任务正确性由后续评测判断 |
| CLI 配置文件 | 远端 `/home/agent/.claude.json` 与 `/home/agent/.claude/settings.json`；由启动的 CLI 使用，修改的是配置文件 |
| CLI 的标准输出与错误输出 | 远端工作目录下的 `.harness/trajectory.jsonl`；本次调用没有将整个文件作为返回值带回 |
| CLI 对工作区可能产生的改动 | 仍在同一远端沙箱；`run` 返回后，`generate:213` 调用 `swe.git_diff` 提取补丁，再交给后续评测 |

CLI 文件输出与训练轨迹分别保存。训练所需的每轮生成记录由 Adapter 的 manager 在处理模型请求时记录，沿用 Step 1 的链路；它们也不包含在这个整数退出码中。

## 4. 本步的收束与后续衔接

你的[整体复述](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#launch-restatement-and-http-entry)已经串起“用户与目录准备 → 收拢上下文 → 写 CLI 配置 → 组成启动材料 → 执行与等待”。本页据此收拢这些部分的交接，函数内部细节继续由各张卡片承接。

| 仍需接清或按需展开的部分 | 放在哪里继续 |
| --- | --- |
| CLI 的请求如何被 Adapter 接收、按路由交给 `_run_turn`，再得到 `body` | 已确认的 [Step 8](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/01-scope.md)，接回已有模型处理链 |
| 脱机启动、防重复、轮询与完整超时/清理机制 | 已有 [exec_and_wait 卡片](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)及其未知部分；根据具体卡点再深入 |
| SDK 内部通信与 CLI 内部工具循环 | 保留当前接口边界，后续需要解释内部实现时再展开 |

**Step 8 所研究的 HTTP 接收发生在本步等待 CLI 的期间。** 一次模型回复回到 CLI 后，CLI 仍可能继续执行；整次 CLI 退出才让本步返回。步骤编号表示阅读顺序。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 调用与返回：[generate.py:203–215](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L203-L215)。
- 本地编排与委派：[harness/common.py:81–122](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L81-L122)。
- 具体配置与启动：[harness/claude_code.py:44–71](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L44-L71)。
- 远端执行与等待：[sandbox.py:65–145](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L65-L145)。
- 本页由 LLM 根据已发生的阅读与用户整体复述整理，采用 [task-flow skill](../SKILL.md)的 Step 003 主 reference。配置写入位置、ctx 的去向及准备/执行边界的校准仍保留为助手说明，未代填为用户确认。
- [本次整理记录](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#task-flow-step-three-format)保留原话与改动范围；[修订前的完整稿](../../../../00-repo-reading/repositories/slime/topics/01-coding-agent-rl/steps/step-008-harness-communication/references/task-flow-before-step-003-format.md)保留此前版本。
- 本次静态核对；已有局部验证归属各卡片，没有新增真实沙箱、CLI 或模型运行。

</details>
