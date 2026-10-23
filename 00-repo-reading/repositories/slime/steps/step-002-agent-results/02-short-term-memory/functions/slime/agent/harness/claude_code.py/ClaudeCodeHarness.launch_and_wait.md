# ClaudeCodeHarness.launch_and_wait

- 源码定位：[slime/agent/harness/claude_code.py:86–109](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L86-L109)，由助手核对。
- 首次接触：Step 1 的上游链路定位；Step 7，2026-10-22 首次独立建卡。
- 最近认识更新：2026-10-23，用户复述 cmd 启动、配置读取和 ctx 已备好；助手进一步区分 58–70 行材料构造与 71 行委派执行并等待。整函数不止准备，ctx 也不直接交给 CLI；本次校准待反馈。
- 本步调取：2026-10-23，从[此前累计的完整记录](../../../../../../../step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)调入 Step 002。旧记录完整保留在页末折叠中；本页上半部按新版核对，新增说明尚未成为个人理解。

## LLM 整理：使用场合、具体内容与心智模型

以下按当前 `18868a79` 整理整个函数；本轮只进一步展开统计初始化与启动的先后关系。

1. **使用场合**：`BaseHarness.run` 已通过 [write_config](ClaudeCodeHarness.write_config.md) 写好脚本与配置，随后调用本函数启动 CLI 并等待退出。

2. **具体内容**：把任务提示和运行上下文组织成 `cmd` 与 `env`，应用可选覆盖；新版在命令中加入统计清零、启动 CLI、保存子进程 PID 和等待。将材料交给 `run_agent`，最终返回它取得的整数退出码。

3. **建议构建的心智模型**：

   > - 先准备 CLI 的命令和环境变量，让它知道任务内容与 Adapter 地址。
   > - 命令在沙箱执行时，先把统计清零，再启动 CLI，记下其 PID 并等待。
   > - 本函数把这些材料交给 `run_agent` 并等待退出码；CLI 运行期间的事件统计由已注册的 hook 更新。

4. **调用代码**（`harness/common.py:104`）：

   ```python
   return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)
   ```

## 本场景的输入与输出

### 输入

`self` 是 `ClaudeCodeHarness`，`sb` 与前一张卡是同一个沙箱；脚本和配置已写好。教学场景的目录与 `run_hook` 卡片一致，提示使用源码的默认 `SWE_PROMPT`，没有额外参数或环境变量覆盖。

```python
ctx = HarnessContext(
    workdir="/workspace/repo",
    session_id="sid-demo",
    adapter_url="http://adapter-host:18001",
)  # model_label 默认是 "slime-actor"
prompt = swe.SWE_PROMPT
time_budget_sec = 300
```

### 返回值与中间材料

正常返回 `int` 退出码。本地验证用 `run_agent` 记录器返回 `0`，本函数原样返回 `0`；这不代表实际 CLI 成功运行。

`cmd` 与 `env` 是交给下层的材料，不是返回值。`env` 包含 `ANTHROPIC_BASE_URL`、`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_MODEL` 及三个类级固定开关；完整值和默认提示见页末验证记录。可选的 `SLIME_AGENT_CC_EXTRA_ARGS` 和 `SLIME_AGENT_CC_EXTRA_ENVS` 分别追加命令参数、覆盖环境字段，本例均未设置。

```text
╔════════ 本函数：宿主机 Python（86–109）════════╗
║ ctx + prompt → cmd、env                      ║
║ cmd 加入：清零 → 启动 CLI → 记 PID → 等待     ║
║ await run_agent(..., start_cmd=cmd, env=env)  ║
║ 接住退出码并返回                             ║
╚════════════════════╤═════════════════════════╝
                     │ 下层负责执行
                     ▼
    沙箱：准备 .harness → 执行命令 → 等待 CLI 结束
           文件写入、CLI 进程和 hook 都在这里运行
```

### 1. 保留已有的命令与环境准备（87–99）

`prompt` 进入 `claude -p` 命令；`ctx` 的地址、编号和模型标签进入三个 `ANTHROPIC_*` 环境变量。固定参数来自类定义，额外配置可以追加或覆盖。本轮不重讲网络请求和多轮工具执行；这些是启动后 CLI 的行为，旧记录完整保留在页末。

<a id="compaction-initialization"></a>

### 2. 本轮重点：把统计清零放在启动之前（100–109）

下面保留这段连续源码：

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
return await run_agent(sb, workdir=ctx.workdir, start_cmd=cmd, env=env, time_budget_sec=time_budget_sec)
```

- **定位文件**：仍使用 `ctx.workdir`，因此统计路径与前一步注册命令带给 hook 的目录相同。
- **先写零值**：命令中的 `printf … > …/compaction.json` 会创建或覆盖文件，写入 `attempts=0、count=0、limit_reached=false`。这是 CLI 启动前的初始状态，返回时文件可能已被 hook 更新。
- **再启动 CLI**：`{cmd} &` 使用此前组装的 CLI 命令在后台启动；下一行 `$!` 取得它的 PID 并保存到 `cli.pid`。这个 PID 供触限停止逻辑使用，具体停止机制本轮留白。
- **继续等待**：`wait "$slime_cli_pid"` 等待这个子进程；`run_agent` 负责将整条命令交给沙箱的执行与等待流程，本函数接住最终退出码返回。
- **区分准备与执行**：100–108 行只在宿主机拼接字符串。109 行委派后，下层先准备 `.harness` 目录，再在沙箱执行命令；不是拼接字符串时已经清零文件。

这里与 `run_hook` 衔接的是同一份文件：启动前写初值，事件到来时再读取并更新。跨阶段顺序见[机制参考](../../../../../../references/compaction-metrics-lifecycle.md#function-coverage)。

## 我的直接表述（原话）

本轮明确限定阅读前两步：

> 好的
> 那么当前只是在run hook中保留这个函数做的事情
> 但是需要看一下
> 这里的1和2

此前关于 `cmd`、`env`、物理边界与委派执行的原话，完整保留在页末旧记录；本轮尚无对初始化命令的新复述。

## 尚不清楚

- 沿用旧记录：用户已说明命令与环境的物理边界及本函数与下游服务的分工；不将本次回看记作从零学习。
- 沿用旧记录：配置位置、`ctx` 与委派等待的校准仍待反馈；下层目录准备、脱机运行、marker 的阶段理解不等于掌握全部实现。
- 本轮新增的初始统计、PID 保存与 `wait` 的关系尚待反馈。只解释清零与启动的顺序，未展开进程管理细节。
- CLI 内部请求、工具循环与实际环境覆盖行为未做在线验证。

<details>
<summary>来源、验证与完整例子</summary>

- 当前源码：`slime/agent/harness/claude_code.py:86–109`，固定版本 `18868a79`。父调用为 `harness/common.py:104`，`run_agent:113–125` 先建 `.harness` 再委派执行。
- [本轮局部验证](../../../../../../references/hook-preparation-example-18868a79.json)：原方法生成完整启动命令与环境字典，传给记录器；检查同一工作目录、清零位置、PID 文件、等待语句、时间预算与返回值。只验证材料构造和交接，没有执行 shell 或真实 CLI。
- 旧版 `2f231865` 只有 57–71 行；旧图与“仅 15 行”的说明只属于页末历史记录。当前入口为 86–109 行，增加了统计初始化和子进程等待包装。
- [本轮形成过程](../../../../../../../step-002-agent-results/04-flow.md#hook-upstream-preparation)；旧记录中的完整图、原话、未知和来源全部保留如下。

</details>

<details>
<summary>此前完整函数记录（2f231865；旧图、原话与来源）</summary>

# ClaudeCodeHarness.launch_and_wait

- 本次继承：2026-10-23，[Step 7 · 02 完整记录](../../../../../../../step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

> **调用链面包屑**：[Step 7 范围](../../../../../../../step-008-harness-communication/01-scope.md) > [02 短期概览](../../../../../../../step-008-harness-communication/02-short-term-memory/overview.md) > [BaseHarness.run](../../../../../../../step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md) → **ClaudeCodeHarness.launch_and_wait** → [run_agent](../../../../../../../step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/run_agent.md) → [exec_and_wait](../../../../../../../step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)

- 源码定位：[slime/agent/harness/claude_code.py:57–71](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L57-L71)，由助手核对。
- 首次接触：Step 1 的上游链路定位；Step 7，2026-10-22 首次独立建卡。
- 最近认识更新：2026-10-23，用户复述 cmd 启动、配置读取和 ctx 已备好；助手进一步区分 58–70 行材料构造与 71 行委派执行并等待。整函数不止准备，ctx 也不直接交给 CLI；本次校准待反馈。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`BaseHarness.run` 已确认用户、组合运行上下文并写好 CLI 配置，现在调用当前 Claude Code 实现启动任务。

2. **具体内容**：把任务提示与 CLI 开关组合成命令，把 Adapter 地址、会话标识和模型标签放入环境变量；应用可选的额外配置，交给 `run_agent` 执行并等待，返回同一个退出码。

3. **建议构建的心智模型**：

   > `launch_and_wait` 负责在宿主机一侧跨过“本地 Python 内存”与“远端沙箱独立程序”的物理边界，将运行参数打包翻译为 Claude Code 的两项启动材料：
   > 
   > - **`cmd`（命令）**：告诉远端沙箱“要干什么”，传入非交互提示词 `-p prompt` 与绕过确认权限等开关；
   > - **`env`（环境）**：告诉远端沙箱“向谁发网络请求”，利用官方 Claude CLI 读取环境变量的机制，把本地 `ctx.adapter_url` 与 `session_id` 注入为 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN`，将请求从官方公网“偷梁换柱”重定向到我们自己的 Slime Adapter。
   >
   > 它把这两项材料打包交给下层沙箱启动流程，挂起等待 CLI 进程整体退出并交回退出码；模型多轮 HTTP 请求则由启动后的 CLI 在沙箱内部发起。

4. **调用代码**（`BaseHarness.run:104`）：

   ```python
   return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)
   ```

## 本场景的输入与输出

接住 [BaseHarness.run 的同一个教学场景](../../../../../../../step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)：[write_config](ClaudeCodeHarness.write_config.md) 已完成配置准备，工作目录沿用 auth0-python，编号、地址和预算为构造值；假定没有额外参数或环境覆盖，CLI 最终退出码为 0。没有运行真实命令。

### 跨边界流转与职责边界标注

本函数自身只有 15 行（`claude_code.py:57–71`），**不包含任何 HTTP 服务或推理转发代码**。但要看懂为什么要把 `ctx` 组装成特定的 `env` 字典，需要结合下游协同背景。下图中**双线框 `╔══╗` 内是本函数真正负责的源码范围**，双线框外是下游模块与前序已读组件（Step 1）的协同效应：

```text
+---------------------------------------------------------------------------------------------------------+
|  本地宿主机 (Host Machine - Python 进程: Slime)                                                          |
|                                                                                                         |
|  ╔══════════════════ 【本函数直接职责：ClaudeCodeHarness.launch_and_wait (57–71 行)】 ═════════════════╗ |
|  ║                                                                                                     ║ |
|  ║   1. 接收输入:                                                                                      ║ |
|  ║     ├── prompt: "请阅读并解决题目..." ────────┐                                                     ║ |
|  ║     └── ctx: HarnessContext                   │                                                     ║ |
|  ║           ├── adapter_url: "http://adapter" ──┼─────────────┐                                       ║ |
|  ║           └── session_id:  "sid-demo"       ──┼───────┐     │                                       ║ |
|  ║                                               │       │     │                                       ║ |
|  ║   2. 组装启动材料 (58–70 行):                 │       │     │                                       ║ |
|  ║     ├── cmd: "/usr/local/bin/claude -p ..." ◄─┘ (将 prompt 拼入命令)                                ║ |
|  ║     └── env 字典:                             │       │     │                                       ║ |
|  ║           ├── ANTHROPIC_BASE_URL:  "http..." ◄────────┼─────┘ (把 adapter_url 设为请求基址)         ║ |
|  ║           └── ANTHROPIC_AUTH_TOKEN: "sid..." ◄────────┘ (把 session_id 设为请求令牌)                ║ |
|  ║                                                                                                     ║ |
|  ║   3. 委派执行并等待退出码 (71 行):                                                                  ║ |
|  ║     return await run_agent(sb, start_cmd=cmd, env=env, ...) ◄─── 传入组装好的 cmd 与 env            ║ |
|  ║       │                                                      ▲                                      ║ |
|  ╚═══════│══════════════════════════════════════════════════════│══════════════════════════════════════╝ |
|          │ (以下交由下层 run_agent / exec_and_wait 处理)        │ 拿到整数 exit_code 返回父函数 run()    |
+----------│------------------------------------------------------│---------------------------------------+
           │                                                      │
           │ 1. sb.exec(cmd, env=env)                             │ 4. 退出码 (exit_code)
           │    (跨网络将环境变量注入容器并启动 CLI)              │    (进程结束回传)
           v                                                      │
+-----------------------------------------------------------------│---------------------------------------+
|  【下游协同背景 1：远端独立沙箱容器】(非本函数代码，解释为何要组装 env) │                                |
|                                                                 │                                       |
|   OS 进程环境: 注入了 ANTHROPIC_BASE_URL 与 ANTHROPIC_AUTH_TOKEN│                                       |
|                                                                 │                                       |
|   ┌─────────────────────────────────────────────────────────────│────────────────────────────┐          |
|   │  Claude Code CLI (独立运行的外部程序, Node.js)              │                            │          |
|   │                                                             │                            │          |
|   │  2. 读取系统环境变量:                                       │                            │          |
|   │     发现自身网络目标已被重定向到 Adapter (偷梁换柱)         │                            │          |
|   │                                                             │                            │          |
|   │  3. 执行题目任务与多轮模型交互:                             │                            │          |
|   │     读取工作区题目 ──> 发起模型请求 (HTTP) ─────────────────┼───────┐                    │          |
|   │     接收工具指令   <── 收到回复并修改代码 / 跑测试 ◄────────┼───────┼──────────┐         │          |
|   │                                                             │       │          │         │          |
|   │  4. 任务结束 / 超时退出:                                    │       │          │         │          |
|   │     产生进程退出码 (例如 0) ────────────────────────────────┘       │          │         │          |
|   └─────────────────────────────────────────────────────────────────────│──────────│─────────┘          |
+-------------------------------------------------------------------------│----------│--------------------+
                                                                          │          │
                                                   HTTP POST /v1/messages │          │ HTTP 流式回复
                                                   (Header 带 session_id) │          │ (模型生成 Token)
                                                                          v          │
+------------------------------------------------------------------------------------│--------------------+
|  【下游协同背景 2：后端服务层】(Step 1 已读的 Adapter 与 SGLang，非本函数代码)     │                    |
|                                                                                    │                    |
|   Slime Adapter (HTTP :18001)  ───────────── 转发模型推理请求 ───────────────────> │  SGLang (:30000)   |
|   (按 session_id 提取会话与配置，转换格式) <────── 返回推理生成结果 ───────────────┴  (大模型实际推理)  |
+---------------------------------------------------------------------------------------------------------+
```

| 层次 / 物理位置 | 是否属于本函数代码 | 承载介质与实体 | 具体内容与职责 |
| :--- | :--- | :--- | :--- |
| **1. 本地接收输入** | **是（57 行）** | Python 进程内存 (`ctx`, `prompt`) | 接收 `workdir`、`session_id`、`adapter_url` 与题目提示 |
| **2. 本地组装材料** | **是（58–70 行）** | 命令字符串与字典 (`cmd`, `env`) | `cmd`：拼入 `-p prompt` 与权限开关<br>`env`：将 `adapter_url` 映射为 `ANTHROPIC_BASE_URL` |
| **3. 委派并挂起等待** | **是（71 行）** | 调用 `await run_agent(...)` | 把材料交给下层启动函数，挂起等待并最终返回整数退出码 |
| **4. 跨越沙箱边界** | 否（下层 `run_agent`） | 沙箱 SDK (`sb.exec(..., env=env)`) | 将本地字典作为进程环境变量注入远端容器操作系统 |
| **5. 远端沙箱容器** | 否（外部 `claude` CLI） | 独立 CLI 程序 (Node/二进制) | 自动读取环境变量，将模型请求发往 Adapter 而非官方公网 |
| **6. 后端服务处理** | 否（Step 1 已读） | Slime Adapter & SGLang | Adapter 接收 HTTP 请求、转换格式并转发给 SGLang 推理 |

**输入：`sb`、`ctx`、`prompt` 与 `time_budget_sec`（均位于本地宿主机 Python 内存）。**

```python
# sb：原来的 E2BSandbox 对象；self：ClaudeCodeHarness
ctx = HarnessContext(
    workdir="/workspace/auth0-python",
    session_id="sid-demo",
    adapter_url="http://adapter-host:18001",
)  # model_label 默认是 "slime-actor"
prompt = swe.SWE_PROMPT
time_budget_sec = 300
```

**输出：返回 `int` 退出码（表示远端独立进程的执行结果）；教学场景假定为 0。**

```python
agent_exit_code = 0
```

`cmd` 和 `env` 是交给子函数的中间材料，并非本函数返回值。下层会使用它们启动远端 CLI；取得退出码后，本方法把它交回 `BaseHarness.run:104`，再返回 `generate:205`。

### 1. 提示与运行上下文 → 本地命令与环境变量字典（58–70）

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

- **提示进入命令**：`shlex.quote(prompt)` 将提示作为一个 shell 参数，放在 `claude -p` 后。`prompt` 沿用 `swe.SWE_PROMPT`，要求读取当前目录的题目文件并解决问题；`-p` 指定非交互方式。`self.launch_flags` 加上 `--permission-mode bypassPermissions`、`--output-format stream-json` 等开关。此处仍在本地构造字符串，CLI 尚未启动。
- **地址进入环境**：本例 `ANTHROPIC_BASE_URL` 为 `http://adapter-host:18001`，供 CLI 确定模型 API 的目标。`env` 此时只是本地字典；随后经沙箱接口，成为远端 CLI 进程可读取的环境变量。模型服务的 `sglang_url` 保存在 Adapter，不从这里交给 CLI。
- **会话与标签分别传递**：`ANTHROPIC_AUTH_TOKEN` 为 `sid-demo`，用于请求头中的会话关联；`ANTHROPIC_MODEL` 为 `slime-actor`，是 CLI 使用的模型标签。固定行为开关从 `self.static_env` 合入。
- **额外配置可能改变结果**：`SLIME_AGENT_CC_EXTRA_ARGS` 可追加命令参数，`SLIME_AGENT_CC_EXTRA_ENVS` 可覆盖环境字段，包括地址或会话标识。本例未提供它们，所以保留上面的对应关系。

本例得到的完整 `env` 如下。前三项承接刚读过的 `ctx`，后三项来自类的固定设置，当前只需知道它们一起传给进程：

```python
env = {
    "ANTHROPIC_BASE_URL": "http://adapter-host:18001",
    "ANTHROPIC_AUTH_TOKEN": "sid-demo",
    "ANTHROPIC_MODEL": "slime-actor",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1",
    "CLAUDE_CODE_ATTRIBUTION_HEADER": "0",
}
```

### 2. 启动材料 → 跨沙箱边界交给 run_agent 并等待进程退出码（71）

下面只调整原行排版，实参保持不变：

```python
return await run_agent(
    sb,
    workdir=ctx.workdir,
    start_cmd=cmd,
    env=env,
    time_budget_sec=time_budget_sec,
)
```

- **交给同一个沙箱**：`sb` 指定操作哪个远端环境；`workdir` 指定启动工作目录。题目文件已经在目录中，`prompt` 要求 CLI 读取它。
- **传递命令与环境**：`launch_and_wait` 自身没有直接调用 `sb.exec`，而是把 `cmd`、`env`、工作目录和时间预算一起交给 `run_agent`。后者继续委派 `exec_and_wait` 写启动脚本，并通过 `sb.exec(..., env=env)` 启动；E2B 实现把环境字典作为 `envs` 交给 SDK。这里先保留交接，脚本与等待标记留在下一层展开。
- **等待的对象是整次 CLI 运行**：启动后 CLI 可根据环境变量请求 Adapter，模型回复先回 CLI；只有下层取得整次运行的退出码，本函数才正常返回该整数。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [run_agent，107–122](../../../../../../../step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/run_agent.md)：启动材料怎样交给等待流程 | 接住 `exit_code`，直接返回父函数；下层继续通过 [exec_and_wait](../../../../../../../step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md) 脱机执行并轮询 |

## 我的直接表述（原话）

本步问题节选：

> 但是没有说明信息是怎么在不同的地方流动或者传输的？

2026-10-22，读过配置准备后，明确进入本函数：

> 好的那么现在再来看一下这里的launch and wait具体是要做什么吧

2026-10-22，用户提出对 `cmd` 与 `env` 的直觉理解与心智模型疑问：

> 之前是把这里的harnesscontext的部分写到了这里的harness context里面，然后吧这些写进了这个harness的配置里面。
> 然后这里的内容是launch and wait的内容，我可以简单的理解为这里做的事情更多的是在于把prompt的启动材料什么的全部都写在这里的cmd里面？
> 然后这里的aenv的内容感觉更多的是在处理这里的当前的anthropic base的url还是只是存在于ctx里面，现在需要吧这里的env都提取出来？我其实不是特别理解，没有办法完全构建这里的心智模型。

2026-10-22，经物理隔离边界解释后，用户完整复述核心机制并指出单函数职责边界：

> 我对于这一个模块大概的理解是这里吧这个内容都组装好了，因为claude code cli时会读取环境变量的，然而这里在launch and wait的部分修改了这里的的系统变量，这样子之后发生交互的时候会向这里的这个http也就是后端的服务来发送请求，是这种方式我说对了吗？这里是我的心智模型。
> 但是当前这个function内部其实还是没有出现这里的后端服务或者转发推理请求什么的的对吧？这个function的心智模型里面是不是包含了整个问题的解释？
> 那么考虑一下这里应该怎么处理这里的图呢？全部删掉好像不合适，是否需要更加好的标注这里这个函数到底负责的模块是什么？

2026-10-22，用户进一步总结 Harness 抽象的设计必然性（推广到 Claude 与 Codex 等底层机制）：

> 好的那么我现在其实清楚为什么需要有这里的这一步的launch and wait的部分。
> 这里这一步更多的是因为这里的这个claude和codex的底层的机制，也就是说因为这里的这个运行方式所以我需要在底层不单是在write config，还需要修改本身的这里的env。
> 这是我对于这里的这个理解，包括codex也一样，底层都是会检查这个env，所以会需要处理这个问题。

助手核对：
1. **机制复述完全正确**：`launch_and_wait` 组装 `cmd` 与 `env` 字典，利用 Claude CLI 读取环境变量的特性，使 CLI 启动后将 HTTP 请求发往 Slime Adapter。
2. **源码职责边界非常准确**：本函数内部仅 15 行，只负责本地组装 `cmd`/`env` 并调用 `run_agent` 等待退出码；后端 HTTP 服务与推理转发并不在本函数内（属于 Step 1 已读的 Adapter/SGLang）。因此图与表格用双线框 `╔══╗` 与“是否属于本函数代码”列明确划出了本函数直接职责与下游协同背景的分界。
3. **架构抽象理解到位**：`write_config` 解决磁盘静态配置（如权限、引导），而 `launch_and_wait` 通过组装 `env` 解决运行时网络重定向。主流 Agent CLI（无论是 Claude 的 `ANTHROPIC_BASE_URL` 还是 Codex/OpenAI 的 `OPENAI_BASE_URL`）底层 SDK 都遵循读取环境变量确定服务端点的行业协议，因此 Harness 必须在启动前将环境注入远端进程。

2026-10-23，整条启动链的复述节选（完整原话见[本次讨论](../../../../../../../step-008-harness-communication/04-flow.md#launch-restatement-and-http-entry)）：

> 然后再考虑的是这里的launch and wait的部分
>
> 这里通过cmd启动
> 除此之外是让启动的这个claude自动读取之前写好的本地的config文件
> 以及这里的ctx这里都已经事先储存好的
>
> 到这里都是准备工作还没有执行

助手校准：“还没有执行”只适用于本函数 58–70 行构造 `cmd/env` 的阶段，且此前远端用户与配置准备已经执行。第 71 行调用 `run_agent`，会等待整次 CLI 执行结束。CLI 启动后使用沙箱里的配置文件和进程环境；`ctx` 由本地 Python 代码取值。

## 尚不清楚

- 已经弄清：`cmd` 与 `env` 的物理边界、环境变量重定向原理，以及本函数直接职责（本地组装与委派等待）与下游协同背景（CLI 请求、Adapter 转发）的代码边界。
- 用户已概括下层目录准备、脱机执行与 marker 等待；具体实现不因阶段级复述而视为全部掌握。本次配置位置、ctx 与委派执行边界的校准仍待反馈。
- CLI 内部发起请求、多轮循环与工具执行的细节保留黑盒状态，后续按需展开。
- 额外参数覆盖（`SLIME_AGENT_CC_EXTRA_ARGS` / `ENVS`）在真实环境下的覆盖行为未做在线验证。

<details>
<summary>来源、验证与完整例子</summary>

- 固定定义见页首；类的开关和环境变量名称见 `claude_code.py:18–34`，父调用见 `harness/common.py:104`，委派见 107–122 行，脚本启动与等待见 `sandbox.py:107–145`，SDK 参数见 324–331 行。
- 命令与环境代码直接摘自源码。2026-10-22 提取原方法及类的设置，使用原始默认 `SWE_PROMPT`，将 `run_agent` 换成本地操作记录器，并提供空的额外配置环境；核对完整提示保持为一个命令参数、六项环境变量、同一个 `sb`、工作目录与 300 秒预算的传递。返回的 0 由记录器设定，确认本函数原样交回；它不是实际 CLI 的退出结果。没有执行 shell、启动 CLI 或请求模型。
- CLI 接口依据：[环境变量](https://code.claude.com/docs/en/env-vars)、[命令行参数](https://code.claude.com/docs/en/cli-reference)，2026-10-22 复核 `-p`、输出格式与环境变量的公开含义。当前文档只用于接口对照，不证明固定版本安装包的全部运行行为，也不替代其内部函数实现。
- 形成过程：[Step 7 · 原始通信问题](../../../../../../../step-008-harness-communication/04-flow.md#run-cross-process-communication) · [独立成步的确认](../../../../../../../step-008-harness-communication/04-flow.md#separate-communication-step)。
- 本轮展开：[Step 7 · 启动命令、环境变量与等待结果](../../../../../../../step-008-harness-communication/04-flow.md#launch-and-wait)。
- 完整跨组件关系见[通信路径参考](../../../../../../../step-008-harness-communication/references/run-communication-path.md)。

</details>

</details>
