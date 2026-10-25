# 01 · 阅读范围：Harness 启动 CLI 与等待返回

[步骤入口](README.md) · [前一步任务总结](../step-007-prepare-workspace/05-task-flow.md) · [本步记录](02-short-term-memory/overview.md) · [旧版 scope](references/scope-at-2f231865.md)

## 1. 阅读目标

- **整体目标**：理解 Coding Agent / Coding RL 的运行流程。
- **本步问题**：已就绪的沙箱与任务参数怎样变成一次 CLI 运行，执行结果怎样返回调用方？
- **阅读范围**：沿 Claude Code 的正常路径，接清运行上下文、CLI 配置、启动命令与环境变量、执行和等待；HTTP 接收留在 Step 009。

## 2. 指挥官函数

- **整体位置**：Step 007 已准备好工作区和题目；现在从 [_generate:287](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L298) 的 `await harness.run(...)` 进入运行阶段。
- **本步指挥官**：[BaseHarness.run:81–104](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L81-L104)。本轮采用的 `ClaudeCodeHarness` 继承这个方法，具体配置与启动由自身实现。
- **选择理由**：它串联用户准备、上下文、配置和启动等待，能够从同一个入口跟住参数传递及返回结果。

## 3. 给出真正干活的核心骨架

### 3.1 继承整体骨架，定位第 4 项

沿用 `evaluation=False` 的正常路径。以下为教学裁剪：省略多数参数、检查、日志、追踪、超时和失败包装，保留真实顺序及沙箱使用边界。

```python
adapter.open_session(...)  # 1. Step 005：登记会话
async with boot_agent_sandbox(...) as sb:  # 2. Step 006：沙箱与 CLI 就绪
    baseline = await swe.prepare_workspace(...)  # 3. Step 007：准备工作区，保存初始基准
    agent_exit_code = await harness.run(...)  # 4. 本步：启动 CLI，等待执行结果
    # CLI 运行期间，通过 HTTP 进入 Adapter 的模型请求流程
    agent_metrics = await harness.collect_metrics(...)  # Step 002：收集统计
    diff_text = await swe.git_diff(...)  # 5. 用 baseline 提取补丁

reward, applied_cleanly = await swe.run_evaluation(...)  # 6. Step 003：独立评测
samples = await adapter.finish_session(...)  # 7. Step 004：导出样本
...  # 返回前的结果处理及最终会话清理
return samples
```

本步在 `agent_exit_code` 交回 `_generate:287` 处停止。统计、补丁提取、评测和样本导出只保留位置。

### 3.2 接住已有输入，展开本地编排

- **执行环境**：`sb` 和 `workdir=md["workdir"]` 来自前面的准备；本轮沿用已就绪的 Sunabako 沙箱。`baseline` 保留在外层供后续比较，没有传入 Harness。
- **模型请求的去向**：`adapter_url` 和 `session_id` 来自前序服务与会话登记，和 `workdir` 一起收进本地 `HarnessContext`。
- **任务与预算**：调用方传入 `prompt=swe.SWE_PROMPT` 和 `time_budget_sec=CONFIG.agent_time_budget_sec`。默认提示要求 CLI 读取题目文件；预算交给下层等待逻辑。

完整实参见 [_generate:287–294](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L287-L294)。下面是 `BaseHarness.run` 的四项主体，调用参数按 scope 约定省略：

```python
await _sandbox.ensure_agent_user(...)  # 97：复用账号与目录准备
ctx = HarnessContext(...)  # 98–102：收拢本地运行上下文
await self.write_config(...)  # 103：准备 CLI 所需的配置文件
return await self.launch_and_wait(...)  # 104：启动、等待并交回结果
```

本例的 `self.write_config` 进入 `ClaudeCodeHarness:57–84`；`self.launch_and_wait` 进入 `86–109`。先接清 `ctx → 配置文件` 与 `prompt / ctx → cmd / env`，再跟住 `run_agent → exec_and_wait` 的执行与等待。`ctx` 是本地对象，命令和环境变量供执行沙箱中的 CLI 使用。

<a id="harness-local-navigation"></a>
<a id="reading-path"></a>

### 3.3 阅读导航与停止位置

先定位 `run` 的四项主体，重点进入决定启动命令与请求地址的 `launch_and_wait`；输入不清楚时回查对应前置，再返回主线。按函数分轮接续，每轮最多向下追两层。

| 阅读入口 | 本步看清什么 | 返回或继续位置 |
| --- | --- | --- |
| [BaseHarness.run:81–104](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L81-L104) | 输入怎样经过四项主体，结果怎样交回；已有[函数卡](02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)保留历史理解 | 重点定位 `104` 的启动调用 |
| `97–102`：[用户准备](../step-007-prepare-workspace/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)与 [HarnessContext 旧类卡](02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md) | 复用账号准备；确认上下文保存工作目录、会话编号与 Adapter 地址 | 继续 `103` 写配置 |
| [ClaudeCodeHarness.write_config:57–84](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L57-L84) | 配置与 hook 在 CLI 启动前怎样准备；可回看 [Step 002 已校准记录](../step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md)，不重讲全部 hook 机制 | 返回 `run:104` |
| [ClaudeCodeHarness.launch_and_wait:86–109](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | 复用已有认识，以整体图接清本地组装、沙箱执行与服务交互；PID 和压缩作为命令段的补充 | 在 `109` 交给 `run_agent`，完成后返回 `run:104` |
| [run_agent:111–126](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L111-L126) → [exec_and_wait:99–162](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L99-L162) | 命令、环境、工作目录与输出文件如何交给沙箱，启动后怎样等待完成标记 | 结果回到 `run_agent:115`，取退出码并在 `126` 返回 |
| [_await_done_marker:79–96](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L79-L96) | 当前直接读取完成文件，取得退出码；预算耗尽时返回超时码 | 回到 `exec_and_wait:156`，沿调用链交回 `_generate:287` |

**等待期间的交互**：CLI 可以多次经 HTTP 请求 Adapter，模型回复回到 CLI 后继续任务。接收路由与请求处理由 [Step 009](../step-009-adapter-request-entry/01-scope.md)接续，本步只保留地址、会话标识及发生时机。

**停止条件**：能串起“已有环境与参数 → 配置 → 命令和环境变量 → 启动与等待 → 执行结果返回”。正常完成时得到 CLI 退出码；等待预算耗尽也可能返回超时码，不能据此认定所有后台活动已停止。完整恢复、SDK 传输和 CLI 工具内部实现继续按需深入。

## 版本说明

- **源码基准**：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本机 checkout 为 `/home/fredkeira/projects/slime`。
- **主线可复用**：`BaseHarness.run`、`run_agent`、`exec_and_wait` 的函数体与 `2f231865` 相同；调用者已使用当前 `harness` 实例，并接回 `baseline` 和统计收集。
- **需要校准的实现**：`write_config` 增加 hook 配置；`launch_and_wait` 增加统计、PID 与等待包装；`_await_done_marker` 从执行 Shell 查询改为 `sb.read_file`。因此 `exec_and_wait` 本体未变不等于它依赖的等待行为也未变。
- **材料边界**：[更新前 scope](references/scope-at-2f231865.md)与[更早的宽范围](references/scope-before-step-008.md)分别保留。`launch_and_wait` 已复用新版，`exec_and_wait` 已局部同步完成文件读取，当前 [task flow](05-task-flow.md)接清启动与结果返回；其余旧卡及 `03` 仍保留原版本来源。前序记录与个人理解不因整理而改写，见[本轮收束](04-flow.md#harness-execution-closure-20261025)。
