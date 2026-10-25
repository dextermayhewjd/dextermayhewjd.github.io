# 05 · 任务链路：启动沙箱中的 CLI 并等待执行结果

> `BaseHarness.run` 接住已有沙箱与任务参数，完成运行前配置；`launch_and_wait` 组装命令、环境及运行控制，交给下层在沙箱中启动 CLI。Slime 继续读取完成文件，取得执行结果后沿调用链返回给 `_generate`。

[本步 scope](01-scope.md) · [函数记录](02-short-term-memory/overview.md) · [原整体复述](04-flow.md#launch-restatement-and-http-entry) · [本次收束](04-flow.md#harness-execution-closure-20261025) · [旧版完整总结](references/task-flow-at-2f231865.md)

## 1. 本步接住哪些准备结果

从 `_generate:287` 的 `await harness.run(...)` 进入，当前采用 Claude Code 实现，运行在已经就绪的执行沙箱中。已有材料的来源如下：

| 材料 | 本步的用途 |
| --- | --- |
| Step 006 提供的 `sb` | 操作已安装 CLI 的执行环境 |
| Step 007 准备好的 `workdir` 与题目文件 | 决定 CLI 工作目录和要解决的问题 |
| `adapter_url`、`session_id` | 进入 CLI 环境变量，连接既有模型请求服务并关联会话 |
| `prompt` | 进入 `claude -p` 的任务参数 |
| `time_budget_sec` | 控制等待完成标记的预算 |

`baseline` 留在 `_generate`，供后续提取代码补丁，本步没有把它传入 Harness。正常完成时返回 CLI 退出码；等待预算耗尽时也可能返回超时状态。

<a id="2-按执行顺序接起来"></a>
<a id="launch-flow-diagram"></a>

## 2. run 的四个部分怎样连接到执行与等待

下面保留原有调用层级的读法，位置校准到 `18868a79`。①–④是 `BaseHarness.run` 的四项主体；④里的执行器再分为组装 launcher、后台启动与防重、读取完成文件三段。

```text
_generate:287  await harness.run(...)
└─ BaseHarness.run [harness/common.py:81–104]
   ├─ ① ensure_agent_user [97]
   │  → 复用账号、按后端处理目录访问、配置 Git
   ├─ ② ctx = HarnessContext(...) [98–102]
   │  → 收拢工作目录、会话编号与 Adapter 地址
   ├─ ③ ClaudeCodeHarness.write_config [103 → claude_code.py:57–84]
   │  → 放置 hook 脚本，写 CLI 配置和事件处理命令
   └─ ④ ClaudeCodeHarness.launch_and_wait [104 → 86–109]
      ├─ 组装 cmd / env [87–99]
      ├─ 加入统计清零、CLI PID 与 wait 包装 [100–108]
      └─ await run_agent(...) [109 → harness/common.py:111–126]
         ├─ 准备 .harness 输出目录 [113–114]
         └─ await exec_and_wait(...) [115 → sandbox.py:99–162]
            ├─ 组装并写入 launcher [124–130]
            ├─ 清理旧状态，防止同次启动重试重复拉起 [139–155]
            └─ await _await_done_marker(...) [156 → 79–96]
               → 每隔 5 秒 read_file，取得退出状态或达到预算
            → 返回 (exit_code, output) [157–162]
         → 只取 exit_code 返回 [126]
      → 返回执行结果 [109]
   → 返回执行结果 [104]
_generate:287 接住 agent_exit_code，随后收集统计并提取补丁
```

各处记录：[账号准备](../step-007-prepare-workspace/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) · [运行上下文](02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md) · [新版配置](../step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) · [本步启动卡](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) · [run_agent 的已有记录](02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md) · [局部校准后的执行等待](02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)。旧卡中的历史行号以其版本为准，本图用于当前调用定位。

这里有两种等待：沙箱中的 Shell `wait` 等待 CLI 子进程，主机中的 Slime 读取完成文件取得状态。后台启动让 CLI 不必依赖同一条长时间保持的命令连接，主机仍持续参与结果监控。

CLI 运行期间的 HTTP 请求由 Adapter 处理；它们是运行中的交互，不能画成拿到 `agent_exit_code` 以后才发生的下一步，也不是 `exec_and_wait` 的普通直接调用。

## 3. 最后交回什么，留下什么

| 结果或状态 | 所在位置与去向 |
| --- | --- |
| `agent_exit_code` | `exec_and_wait` 先返回二元组，`run_agent` 取整数，经上层返回 `_generate` |
| CLI 配置与 hook 脚本 | 留在执行沙箱，供本次 CLI 使用 |
| `.harness/cli.pid` | 记录本次 CLI 进程编号，供压缩触限停止逻辑定位进程 |
| `.harness/compaction.json` | 启动时初始化，压缩事件更新，后续由 `collect_metrics` 读取 |
| `.harness/trajectory.jsonl` | 保存 CLI 输出；与 Adapter 为训练记录的模型轨迹分别维护 |
| 工作区中的代码改动 | 留在同一沙箱，`_generate:298` 用 `git_diff` 提取补丁 |

例如正常得到 `agent_exit_code=0`，只表示这次进程成功退出，不直接等同题目已修复；正确性由后续评测判断。本例是返回关系的说明，没有运行真实任务。

## 4. 本步的收束与后续衔接

用户已采用 `launch_and_wait` 的三段模型，并概括 `exec_and_wait` 的 launcher、脱机启动与防重、完成文件轮询。按当前 scope，本步的“运行材料 → 沙箱启动 → 监控等待 → 返回结果”可以收束，具体机制的未知继续保留。

- “脱机”不表示主机不再参与。Slime 仍在轮询；启动防重主要针对同一次启动请求被传输重试，不能扩大为任何命令都可重复执行。
- `EXIT_TIME_BUDGET_EXCEEDED=-1` 表示等待预算耗尽，不保证沙箱中的全部后台活动已经停止。完整超时回收、进程关系与 SDK 故障处理留待需要时深入。
- 真实 CLI 行为、网络与压缩事件尚未进行端到端运行验证，已有源码和局部验证不等于所有机制已掌握。

下一候选是已有 Step 009 的 HTTP 接收入口：CLI 发出请求后，服务怎样把它交给 `_run_turn`。它发生在本步运行期间；新一轮仍先确认该步 scope，不在本次自动展开。

<details>
<summary>源码、历史与验证范围</summary>

- 当前固定版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`：[调用方](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L298)、[BaseHarness.run 与 run_agent](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L81-L126)。
- [配置与启动](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L57-L109)、[脱机执行与完成文件读取](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L79-L162)。
- 先前的完整任务总结保存在[旧版记录](references/task-flow-at-2f231865.md)，原 scope、图、个人原话与长期快照分别保留历史来源。
- [本次整体反馈与澄清](04-flow.md#harness-execution-closure-20261025)。本轮静态核对调用链及返回位置，未执行真实 CLI、压缩事件或远端命令。

</details>
