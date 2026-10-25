# BaseHarness.run

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 02 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

> **调用链面包屑**：[Step 7 范围](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/01-scope.md) > [02 短期概览](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/overview.md) > **BaseHarness.run** → [launch_and_wait](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) → [run_agent](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/run_agent.md) → [exec_and_wait](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)

- 源码定位：[slime/agent/harness/common.py:81–104](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L81-L104)，由助手核对。
- 首次接触：Step 1 的 Harness → Adapter 链路。
- 最近认识更新：2026-10-23，用户已按用户准备、上下文、配置、启动与等待复述本条调用链；继续指出 HTTP 请求怎样进入 Adapter 仍不清楚。配置位置、ctx 与 CLI 的关系以及准备/执行分界由助手校准，尚待反馈。
- 前序记录：[继承的完整旧卡片](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)，保留旧场景、原话、未知与来源。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`generate` 已取得可用的执行沙箱、准备好工作区并登记会话，现在通过选中的 Harness 启动 Agent。当前对象是 `ClaudeCodeHarness`，它继承本方法。

2. **具体内容**：确认运行用户，组合 `workdir`、`session_id` 与 `adapter_url` 为 `HarnessContext`；调用具体实现写 CLI 配置，再交出上下文、提示和时间预算，等待并返回 CLI 的退出码。

3. **建议构建的心智模型**：

   > `BaseHarness.run` 在 Slime 一侧组织一次 CLI 运行：接住准备好的沙箱与运行参数，把配置和启动交给具体 Harness，直到 CLI 整体退出才返回退出码。
   >
   > CLI 运行期间可以多次请求 Adapter；每次模型回复由另一条 HTTP 请求链交回 CLI，不是本函数的返回值。

4. **调用代码**（`generate.py:205–212`，保留本次交接的全部参数）：

   ```python
   agent_exit_code = await HARNESS_CLS().run(
       sb,
       workdir=md["workdir"],
       session_id=session_id,
       adapter_url=state.adapter_url,
       time_budget_sec=CONFIG.agent_time_budget_sec,
       prompt=swe.SWE_PROMPT,
   )
   ```

## 本场景的输入与输出

沿用 Step 6 的 auth0-python 工作目录；编号、地址和时间预算采用教学构造，不代表实际部署值。假定该 `sid` 已登记、地址可达，CLI 最终正常退出，未运行真实沙箱。

**输入：已有对象与五项运行参数。**

```python
# self：ClaudeCodeHarness；sb：已就绪的本地 E2BSandbox 对象
workdir = "/workspace/auth0-python"
session_id = "sid-demo"
adapter_url = "http://adapter-host:18001"
time_budget_sec = 300
prompt = swe.SWE_PROMPT
```

`prompt` 使用源码的任务提示：要求 CLI 读取当前目录的 `PROBLEM_STATEMENT.md`、修改源文件并验证，最后输出总结退出。具体题目已在远端文件中；函数接到的 `sb` 是访问该环境的本地对象。

**输出：CLI 的退出码；以下 0 是教学场景的假定结果。**

```python
agent_exit_code = 0  # int；不包含模型回复文本、token 或代码 diff
```

- 用户准备与 CLI 配置写入作用于原来的远端沙箱，随后具体实现启动 CLI。
- 模型回复在 CLI 运行期间经 HTTP 交给 CLI；本方法不会直接收到每轮回复作为自己的返回值。
- CLI 整体结束后，本方法把退出码交给 `generate:205`；下一行主业务操作是 213 行的 `swe.git_diff`。非零退出码也可能返回；异常则向外传播。

### 1. 运行参数 → 共同上下文（97–102）

```python
await _sandbox.ensure_agent_user(sb, workdir)
ctx = HarnessContext(
    workdir=workdir,
    session_id=session_id,
    adapter_url=adapter_url,
)
```

- **复用已有环境**：`ensure_agent_user` 接到同一个 `sb` 和工作目录，正常返回后继续；这里没有申请另一个沙箱。
- **组合传参材料**：`ctx` 保存工作目录、会话编号和 Adapter 地址；`model_label` 使用类定义的默认值 `"slime-actor"`。
- **保留其他实参**：`sb`、`prompt` 和 `time_budget_sec` 不在 `ctx` 中，后面仍作为独立参数交给启动方法。创建 `ctx` 本身不发送网络请求。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [ensure_agent_user（本步调取）](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)：用户和目录准备 | 正常返回 `None` 后组合 `ctx`，继续 103 行 |
| [HarnessContext 类卡片](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)：构造与四个字段 | 得到本地 `ctx` 对象，继续 103 行，将它与 `sb` 交给 `write_config` |

### 2. 上下文与提示 → 具体 CLI 运行 → 退出码（103–104）

```python
await self.write_config(sb, ctx)
return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)
```

- **调用具体配置实现**：当前进入 `ClaudeCodeHarness.write_config`，通过沙箱接口写入 Claude 的初始化与权限确认配置；正常返回后才启动 CLI。
- **交给具体启动实现**：`ClaudeCodeHarness.launch_and_wait` 把 `prompt` 放进命令，把地址与会话编号放进环境变量，再委派实际启动和等待。这些内部实现见子卡。
- **等待整次运行**：104 行在下层返回退出码后直接交回调用方；期间 CLI 与 Adapter 的交互独立发生。`run` 没有普通函数调用直接跳到 `_run_turn`。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [ClaudeCodeHarness.write_config](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md)：将初始化配置写入远端文件 | 返回 `None`，继续本函数 104 行 |
| [ClaudeCodeHarness.launch_and_wait](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)：命令、环境变量与启动等待 | 接住退出码，直接返回 `generate:205` |

## 我的直接表述（原话）

Step 1 的问题节选：

> 这里是怎么从harness_cls().run到这里的baseAdapter._run_turn的呢？

Step 7 的原始问题节选：

> 我的意思是怎么做到吧这里的信息在这个调度的地方
> 以及sandbox 还有这里的sglang里面发送到不同的地方的呢？

此前完整机制复述尚缺；本次启动链复述与新暴露的 HTTP 入口问题见下方记录。各局部表述仍分别保存在相应子卡。

2026-10-23，整条启动链的复述节选（完整原话见[本次讨论](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#launch-restatement-and-http-entry)）：

> 好的我觉得我大概读懂了这里的一系列的代码了
> 但是我觉得需要复述一下

助手校准：本次完整复述已串起各阶段，见下方来源。`ensure_agent_user` 使用已有沙箱与目录；配置写入远端沙箱；`launch_and_wait` 的末行会进入执行并等待。HTTP 接收入口是本步仍需接清的关系。

## 尚不清楚

- 用户已能串起启动链，当前明确卡在 CLI 请求怎样进入 Adapter；接收服务、路由分派与 Request/body 的关系已补入步骤参考，尚待反馈。
- 启动脚本、完成标记与具体等待机制尚未逐项展开；CLI 内部如何组织多轮模型请求和工具执行继续留白。
- 用户准备已有记录，当前 Claude Code 配置已在子卡展开；完整取消和异常路径仍只定位，没有实际远端运行结果。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本与函数定义见页首；实际调用见 `generate.py:205–212`，上下文定义见 `harness/common.py:42–54`，具体配置与启动见 `harness/claude_code.py:44–71`。
- 本例参数来自真实调用形状，编号、地址和预算为教学构造；退出码 0 是假定结果。仅静态核对，不等同于实际启动、网络连通或模型运行。
- 旧场景与来源完整保留在页首的继承卡片；原始追问见 [Step 1 · 从启动到请求入口](../../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#从启动到请求入口)。
- 当前形成过程：[Step 7 · 原始通信问题](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#run-cross-process-communication) · [独立成步的确认](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#separate-communication-step)。
- 跨组件解释：[运行位置、地址与返回方向](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/references/run-communication-path.md)。

</details>

<details>
<summary>进入 Step 7 时的完整旧场景与来源（历史快照）</summary>

下列内容保留前序场景；本次新增认识见上方主记录。

# BaseHarness.run

首次接触：Step 1｜最近认识更新：尚无用户新增职责表述；本步建立助手解释。

**我的理解（原话）**

尚无直接职责复述。用户当前的问题（节选）是：

> 这里是怎么从harness_cls().run到这里的baseAdapter._run_turn的呢？

**使用场景与源码**

`generate` 已准备工作区和会话，调用选中的 Harness 运行 Agent，收到退出码后继续收集代码改动。以下省略调用参数，保留实际接收返回值的方式：

```python
agent_exit_code = await HARNESS_CLS().run(...)
diff_text = await swe.git_diff(...)
```

**Input → Output**

教学构造，假设沙箱和工作区已存在，CLI 正常结束；以下返回值用于说明接口，未实际运行 Agent。

```python
# Input
# sb 已由调用方准备，是已有的 Sandbox 实例
workdir = "/workspace/repo"
session_id = "sid-demo"
adapter_url = "http://adapter-host:18001"
time_budget_sec = 300
prompt = "读取工作区中的任务并修复代码"

# Output：假设本次 CLI 以退出码 0 正常结束
agent_exit_code = 0
```

副作用：确保运行用户、构造上下文、写入配置，并由具体 Harness 启动和等待 CLI。CLI 运行期间可以向 Adapter 发送模型请求；每次请求的 HTTP 响应是 `_run_turn` 的产物，`run` 自身返回的是 CLI 退出码。

**LLM 根据调用处补充的模型**

> `BaseHarness.run` 将准备好的任务环境交给具体 Harness，运行外部 CLI 并等待退出。CLI 通过配置的地址向 Adapter 发起 HTTP 请求，路由再进入 `_run_turn`；两者之间通过运行中的 CLI 和 HTTP 相连。

**暂时不清楚**

- 用户尚未反馈是否已区分 Harness 的等待与一次 HTTP 请求的处理。
- CLI 内部怎样组织多轮模型请求与工具执行，尚未展开。
- 运行用户、配置写入、命令等待与取消的内部实现，尚未展开。

**来源**

静态源码：固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `generate.py:205`、`harness/common.py:81`、`harness/claude_code.py:57`、`adapters/anthropic.py:48` 与 `adapters/common.py:318`。完整关系与固定源码链接见[任务讲解](../../../../../../../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#harness-to-adapter)。形成过程见 [Step 1 的问题与澄清](../../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/04-flow.md#从启动到请求入口)。

- 继承自：[Step 1 的完整函数记录](../../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)；只继承与重算链接，原认识时间、原话和未知保留。

- 本次继承自：[Step 2 的完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/03-long-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。

</details>
