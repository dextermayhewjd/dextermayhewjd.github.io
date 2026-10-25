# ClaudeCodeHarness.launch_and_wait

- Step 010 继承：2026-10-25，来自 [Step 009 · 02-short-term-memory 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- **Step 009 调取（2026-10-25）**：完整复用 [Step 008 的现行卡片](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)，用于回看 `env` 与 Adapter 地址的交接；保留原文、图示、原话、未知及认识时间，仅增加本条来源说明并重算相对链接。

- 源码定位：[slime/agent/harness/claude_code.py:86–109](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L86-L109)，由助手核对。
- 首次接触：Step 1 的上游链路定位；Step 7，2026-10-22 首次独立建卡。
- 最近认识更新：2026-10-24，用户选定“组装启动材料 → 补充运行控制 → 委派并等待”作为本函数的心智模型；具体 PID、压缩与等待机制仍按实际反馈记录。此前认识与原话保留。
- Step 002 调取：2026-10-23，从[此前累计的完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)调入 Step 002。旧记录完整保留在页末折叠中；本页上半部按新版核对，新增说明尚未成为个人理解。

- Step 008 本次调取：2026-10-24，复用 [Step 002 的完整新版记录](../../../../../../../../../01-coding-agent-rl/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)；[本步原卡片](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/references/launch-and-wait-before-current-reuse.md)单独保留。本轮补充 PID 与压缩事件的衔接，未改变认识日期。

- 本轮呈现整理：2026-10-24，恢复整体大图作为主要入口，按图解释本函数的三个阶段；[整理前完整版本](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/references/launch-and-wait-before-main-diagram-restoration.md)保留，认识日期不变。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`BaseHarness.run` 已准备好账号和 `ctx`，前一步也写好 CLI 配置，现在把任务交给当前 Claude Code Harness 启动。
2. **具体内容**：从提示与上下文组装 `cmd/env`，给命令加上统计初始化、CLI PID 和等待包装，再委派 `run_agent` 执行，等待并返回结果。
3. **建议构建的心智模型**：

   > 1. **组装启动材料**：把 `prompt` 和 `ctx` 变成 `cmd`、`env`。
   > 2. **补充运行控制**：在命令中安排统计初始化、启动 CLI、保存 PID 和等待。
   > 3. **委派并等待**：交给 `run_agent`，由下层在沙箱执行，最后取回整数结果。

4. **调用代码**（`BaseHarness.run:104`）：

   ```python
   return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)
   ```

## 本场景的输入与输出

沿用 Step 002 的教学参数，继续操作已经准备好的 `sb`。目录、编号和地址用于说明字段关系，未启动真实 CLI；与前面 auth0-python 的题目数据分开。

```python
ctx = HarnessContext(
    workdir="/workspace/repo",
    session_id="sid-demo",
    adapter_url="http://adapter-host:18001",
)  # model_label 默认是 "slime-actor"
prompt = swe.SWE_PROMPT
time_budget_sec = 300
```

`sb` 提供执行环境，`ctx` 保存目录与连接信息，`prompt` 是任务提示，`time_budget_sec` 是等待预算。当前例子不设置额外命令参数或环境覆盖。

本函数交回一个整数执行结果；正常完成时是 CLI 退出码，下层等待预算耗尽时也可能返回超时码。`cmd` 和 `env` 是中间材料：前者说明启动什么，后者把 Adapter 地址、会话编号等交给 CLI。它们在这里组装，经下层执行后才产生文件与进程变化。

<a id="launch-and-wait-boundary-map"></a>

### 先看整体图：本地准备、沙箱运行、模型服务怎样接起来

双线框是 `launch_and_wait` 自身的职责；其余框帮助解释输入最终在哪里使用、结果从哪里回来。图中的模型往返发生在 CLI 运行期间。

```text
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║ A. 本函数直接职责：Slime / Python 中的 launch_and_wait（86–109）                             ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║ 输入：sb、ctx、prompt、time_budget_sec                                                       ║
║ ① prompt → cmd；ctx 的地址、会话编号、模型标签 → env                                         ║
║ ② 给 cmd 加入：统计清零 → 后台启动 CLI → 保存 PID → wait                                     ║
║ ③ await run_agent(sb, start_cmd=cmd, env=env, ...)                                           ║
║ 等待返回整数结果，再交给 BaseHarness.run                                                     ║
║ 这里组装的是字符串和字典；命令的效果在下层执行时产生                                         ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
                   │                                                 ▲
                   │ 下交 cmd / env 等材料                           │ 上返 exit_code
                   ▼                                                 │
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ B. 同一 Slime 进程中的下层：run_agent → exec_and_wait                                        │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ 准备 .harness 输出目录，将命令写成启动脚本                                                   │
│ 通过 sb 启动脚本，读取完成文件，取得执行结果                                                 │
│ exec_and_wait 返回 (exit_code, output)，run_agent 只交回 exit_code                           │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                   │                                                 ▲
                   │ 通过 sb 提交并启动                              │ 读取完成文件
                   ▼                                                 │
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ C. 执行沙箱：启动脚本与独立的 Claude Code CLI                                                │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ 实际执行 cmd：清零 compaction.json → 启动 CLI → 写 cli.pid → wait                            │
│ CLI 读取题目和 env；需要模型回复时发出 HTTP 请求                                             │
│ CLI 接收回复后继续工具操作、修改工作区，可能发起下一轮请求                                   │
│ 压缩由 CLI 完成；hook 记录次数，触限时按 PID 发送停止信号                                    │
│ CLI 结束 → wait 返回 → 外层启动脚本写入完成文件                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                   │                                                 ▲
                   │ HTTP 请求                                       │ 模型回复
                   ▼                                                 │
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ D. 模型请求路径：已有 Adapter 与 SGLang 服务                                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ POST /v1/messages → Adapter 按会话编号找到配置 → SGLang 推理                                 │
│ 推理结果 → Adapter 组装协议回复 → 返回给 CLI                                                 │
│ 本区域说明协作关系，请求处理的实现属于其他函数                                               │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

下面三个阶段对应双线框中的①②③。先看本函数怎样组装与委派；遇到下层问题再沿图回查。

### 1. 把 prompt 和 ctx 变成 cmd、env（87–99）

```python
cmd = f"/usr/local/bin/claude -p {shlex.quote(prompt)} {self.launch_flags}"
extra = os.environ.get(self.extra_args_env, "").strip()
if extra:
    cmd = f"{cmd} {extra}"
env = {
    "ANTHROPIC_BASE_URL": ctx.adapter_url,
    "ANTHROPIC_AUTH_TOKEN": ctx.session_id,
    "ANTHROPIC_MODEL": ctx.model_label,
    **self.static_env,
}
extra_envs = os.environ.get(self.extra_envs_env, "").strip()
if extra_envs:
    env.update(json.loads(extra_envs))
```

- `prompt` 放进 `claude -p` 命令；`self.launch_flags` 提供运行开关。`shlex.quote` 保留提示作为一个命令参数。
- `ctx.adapter_url`、`ctx.session_id` 和 `ctx.model_label` 进入三个 `ANTHROPIC_*` 字段；CLI 后续读取这些环境变量，再向 Adapter 发送模型请求。
- 两个可选配置分别追加命令参数、覆盖环境变量；本例不触发它们。此时已经有启动材料，CLI 仍未在这一段 Python 赋值中启动。

<a id="compaction-initialization"></a>

### 2. 给启动命令加上统计、PID 和等待（100–108）

```python
directory = shlex.quote(f"{ctx.workdir}/.harness")
# The detached launcher stays alive to write its normal completion
# marker when the compaction hook stops only the CLI child.
cmd = (
    f'printf \'%s\\n\' \'{{"attempts":0,"count":0,"limit_reached":false}}\' '
    f"> {directory}/compaction.json; {cmd} &\n"
    f"slime_cli_pid=$!\nprintf '%s\\n' \"$slime_cli_pid\" > {directory}/cli.pid\n"
    'wait "$slime_cli_pid"'
)
```

这一段继续修改 `cmd` 字符串。等它在沙箱中执行时，顺序才是：清零统计 → 用 `&` 启动 CLI → 用 `$!` 取该进程 PID → 写入文件 → `wait` 等待这个子进程。

| 运行中使用的文件 | 在这里安排的作用 |
| --- | --- |
| `.harness/compaction.json` | 启动前写入零值，之后由已注册的 hook 更新压缩计数 |
| `.harness/cli.pid` | 记录这次 CLI 的进程编号，供压缩触限时定位停止对象 |

<a id="cli-pid-and-compaction"></a>

**PID 是当前进程的系统编号。** 它回答“正在运行的是哪个进程”，与软件版本和 Git 快照无关。`wait` 等待这个子进程结束，外层启动脚本随后才能继续记录退出状态。

<details>
<summary>压缩事件怎样使用这两份文件</summary>

前一步 [write_config](../../../../../../../../../01-coding-agent-rl/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) 已放好脚本并注册 `PreCompact`、`PostCompact`。实际压缩由 Claude CLI 完成；[run_hook](../../../../../../../../../01-coding-agent-rl/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/compaction.py/run_hook.md) 负责计数与预算控制。

- 压缩前：尚未触限时增加 `attempts`。
- 压缩后：增加 `count`。
- 启用了次数限制、下一次压缩前发现预算已用完：设置 `limit_reached`，读取 `cli.pid`，核验进程关系后向这个 CLI 发 `SIGTERM`。默认上限为 `-1`，此时不因次数停止。

这解释了为什么要记录 PID，也解释了为什么保留等待 CLI 的外层脚本：CLI 被停止后，外层仍有机会写好完成标记。进程祖先核验与实际压缩算法继续按需深入。

</details>

### 3. 交给 run_agent，等待并返回执行结果（109）

```python
return await run_agent(sb, workdir=ctx.workdir, start_cmd=cmd, env=env, time_budget_sec=time_budget_sec)
```

`sb`、工作目录、完整命令、环境变量和预算一起交给下层。`run_agent` 先准备输出目录，`exec_and_wait` 再写启动脚本、启动并读取完成文件；两者在同一个 Slime 进程中编排沙箱操作。

等待期间，CLI 可以反复请求模型、执行工具和修改工作区。等下层取得结果，本函数将整数原样返回 `BaseHarness.run:104`，再回到 `_generate:287` 的 `agent_exit_code`。

| 需要继续查看时 | 读完回到哪里 |
| --- | --- |
| [run_agent 的当前源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L111-L126) · [本步已有卡片](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md) | 返回本函数的 109 行，随后交回 `run:104` |
| [exec_and_wait 与完成标记](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L79-L162) · [本步已有卡片](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md) | 结果先交回 `run_agent:115`，再逐层返回 |

## 我的直接表述（原话）

2026-10-24，用户明确指定采用上一轮提出的三段式表述：

> 1. 组装启动材料：把 prompt 和 ctx 变成 cmd、env。
> 2. 补充运行控制：在命令中安排统计初始化、启动 CLI、保存 PID 和等待。
> 3. 委派并等待：交给 run_agent，由下层在沙箱执行，最后取回整数结果
>
> 按照这个构建心智模型吧

这是对本函数模型组织方式的明确采用，具体机制的理解不由此扩大；见[本轮记录](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#launch-three-part-model)。

用户在本轮要求恢复大图，并据此整理本函数的完整说明：

> 不对啊 之前的卡片我觉得很好啊
> 特别是那个比较大的图
> 还是你觉得这里的这个图不应该放在这里? 我不是特别理解了

> 好的那么请你给出这里的比较合适的解释吧
> 正常构成这里的这个launch and wait 部分的内容吧

这些表述确认的是呈现方式，尚不表示已经理解本轮的 PID 或等待机制。

<details>
<summary>此前关于启动材料、PID 与展示方式的完整记录入口</summary>

2026-10-24，关于压缩与 PID 的疑问节选：

> 还有就是如果压缩的话这里到底是怎么处理的?
> 还有什么需要特别记住的吗?
> 我不是特别理解
> 这里的保存pid又是为了做什么呢?
> 保存版本信息?
> 还是什么

完整问题和职责澄清见[本轮记录](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#cli-pid-and-compaction-question)。这是用户的问题，不作为已理解上述机制的确认。

本轮明确限定阅读前两步：

> 好的
> 那么当前只是在run hook中保留这个函数做的事情
> 但是需要看一下
> 这里的1和2

此前关于 `cmd`、`env`、物理边界与委派执行的原话，完整保留在页末旧记录；本轮尚无对初始化命令的新复述。

更早的完整原话、大图与版本来源见[本步原卡片](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/references/launch-and-wait-before-current-reuse.md)；本轮整理前的全部内容见[保存的完整版本](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/references/launch-and-wait-before-main-diagram-restoration.md)。

</details>

## 尚不清楚

- 沿用旧记录：用户已说明命令与环境的物理边界及本函数与下游服务的分工；不将本次回看记作从零学习。
- 沿用旧记录：配置位置、`ctx` 与委派等待的校准仍待反馈；下层目录准备、脱机运行、marker 的阶段理解不等于掌握全部实现。
- 初始统计、PID 保存与 `wait` 的关系尚待反馈；本轮补清 PID 用于定位 CLI 和压缩触限停止，进程祖先核验未逐句展开。
- CLI 内部请求、工具循环与实际环境覆盖行为未做在线验证。

<details>
<summary>源码、继承与验证范围</summary>

- 当前固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`：[完整函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L86-L109)。三段源码按实际顺序保留全部有效语句。
- 仍以 [Step 002 新版记录](../../../../../../../../../01-coding-agent-rl/steps/step-002-agent-results/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) 为来源；[原有局部验证](../../../../../../../../../01-coding-agent-rl/steps/step-002-agent-results/references/hook-preparation-example-18868a79.json)只核对启动材料和返回值传递，没有执行真实 CLI。
- 图中的下游行为分别由 `run_agent`、`exec_and_wait`、外部 CLI、Adapter 和 SGLang 负责；本函数不直接处理 HTTP。超时返回也不能作为所有后台活动已停止的证明。
- [本轮结构恢复与解释](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#launch-main-diagram-restored)。原话与认识日期保留；展示方式改善不等于新增掌握结论。

</details>

<details>
<summary>同名旧快照与继承边界</summary>

[Step 009 的 03 完整旧快照](../../../../../../references/inherited-step009-long/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)另行保留。本页采用上一步 02 的记录；旧版的表述、未知和证据没有删除，版本差异不在本轮强行统一。

</details>
