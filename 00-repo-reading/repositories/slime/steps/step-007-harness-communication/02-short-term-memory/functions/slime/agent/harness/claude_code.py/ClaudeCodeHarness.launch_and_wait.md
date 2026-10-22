# ClaudeCodeHarness.launch_and_wait

- 源码定位：[slime/agent/harness/claude_code.py:57–71](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L57-L71)，由助手核对。
- 首次接触：Step 1 的上游链路定位；Step 7，2026-10-22 首次独立建卡。
- 最近认识更新：用户已确认单独研究启动与通信，尚无本函数的直接机制复述；以下为助手补充的输入输出与实现解释。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`BaseHarness.run` 已确认用户、组合运行上下文并写好 CLI 配置，现在调用当前 Claude Code 实现启动任务。

2. **具体内容**：把任务提示与 CLI 开关组合成命令，把 Adapter 地址、会话标识和模型标签放入环境变量；应用可选的额外配置，交给 `run_agent` 执行并等待，返回同一个退出码。

3. **建议构建的心智模型**：

   > `launch_and_wait` 把通用运行参数翻译为 Claude Code 的启动材料：`cmd` 决定运行什么，`env` 告诉 CLI 请求哪个 Adapter、携带哪个会话标识。
   >
   > 它把材料交给沙箱启动流程，等待 CLI 整体退出并返回退出码；模型 HTTP 请求由启动后的 CLI 发起。

4. **调用代码**（`BaseHarness.run:104`）：

   ```python
   return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)
   ```

## 本场景的输入与输出

接住 [BaseHarness.run 的同一个教学场景](../common.py/BaseHarness.run.md)：[write_config](ClaudeCodeHarness.write_config.md) 已完成配置准备，工作目录沿用 auth0-python，编号、地址和预算为构造值；假定没有额外参数或环境覆盖，CLI 最终退出码为 0。没有运行真实命令。

**输入：`sb`、`ctx`、`prompt` 与 `time_budget_sec`。**

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

**输出：返回 `int` 退出码；教学场景假定为 0。**

```python
agent_exit_code = 0
```

`cmd` 和 `env` 是交给子函数的中间材料，并非本函数返回值。下层会使用它们启动远端 CLI；取得退出码后，本方法把它交回 `BaseHarness.run:104`，再返回 `generate:205`。

### 1. 提示与运行上下文 → 命令和环境变量（58–70）

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

### 2. 启动材料 → 沙箱启动流程 → 退出码（71）

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
| [run_agent，107–122](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L107-L122)：启动材料怎样交给等待流程 | 接住 `exit_code`，直接返回父函数；需要进一步观察时再以本函数为起点追到 `exec_and_wait`，暂不深入 SDK 编码 |

## 我的直接表述（原话）

本步问题节选：

> 但是没有说明信息是怎么在不同的地方流动或者传输的？

2026-10-22，读过配置准备后，明确进入本函数：

> 好的那么现在再来看一下这里的launch and wait具体是要做什么吧

尚无对 `launch_and_wait` 内部命令与环境变量关系的直接复述；不能把这张卡片的解释记为个人已经掌握。

## 尚不清楚

- 本轮已沿 `prompt → cmd`、`ctx → env`、`run_agent → 退出码` 展开，并补充完整环境字典，仍待用户阅读反馈；启动脚本和等待标记尚未逐项展开。
- CLI 内部构造 HTTP 请求、执行工具和组织下一轮的函数没有检查。
- 额外环境覆盖、超时与重试的真实运行效果尚未验证。

<details>
<summary>来源、验证与完整例子</summary>

- 固定定义见页首；类的开关和环境变量名称见 `claude_code.py:18–34`，父调用见 `harness/common.py:104`，委派见 107–122 行，脚本启动与等待见 `sandbox.py:107–145`，SDK 参数见 324–331 行。
- 命令与环境代码直接摘自源码。2026-10-22 提取原方法及类的设置，使用原始默认 `SWE_PROMPT`，将 `run_agent` 换成本地操作记录器，并提供空的额外配置环境；核对完整提示保持为一个命令参数、六项环境变量、同一个 `sb`、工作目录与 300 秒预算的传递。返回的 0 由记录器设定，确认本函数原样交回；它不是实际 CLI 的退出结果。没有执行 shell、启动 CLI 或请求模型。
- CLI 接口依据：[环境变量](https://code.claude.com/docs/en/env-vars)、[命令行参数](https://code.claude.com/docs/en/cli-reference)，2026-10-22 复核 `-p`、输出格式与环境变量的公开含义。当前文档只用于接口对照，不证明固定版本安装包的全部运行行为，也不替代其内部函数实现。
- 形成过程：[Step 7 · 原始通信问题](../../../../../../../step-007-harness-communication/04-flow.md#run-cross-process-communication) · [独立成步的确认](../../../../../../../step-007-harness-communication/04-flow.md#separate-communication-step)。
- 本轮展开：[Step 7 · 启动命令、环境变量与等待结果](../../../../../../../step-007-harness-communication/04-flow.md#launch-and-wait)。
- 完整跨组件关系见[通信路径参考](../../../../../../references/run-communication-path.md)。

</details>
