# run_agent

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../step-011-generate-and-rm-group/03-long-term-memory/functions/slime/agent/harness/common.py/run_agent.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../../step-010-generate-and-rm/03-long-term-memory/functions/slime/agent/harness/common.py/run_agent.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/run_agent.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 02 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

> **调用链面包屑**：[Step 7 范围](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/01-scope.md) > [02 短期概览](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/overview.md) > [BaseHarness.run](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md) → [ClaudeCodeHarness.launch_and_wait](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) → **run_agent** → [exec_and_wait](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)

- 源码定位：[slime/agent/harness/common.py:107–122](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L107-L122)，由助手核对。
- 首次接触：Step 1 与 Step 7 的上游链路定位；2026-10-22 首次独立建卡。
- 最近认识更新：2026-10-23，用户将目录准备、执行、脱机保护及 marker 轮询串起来；自身代码负责目录和委派，后几项在 exec_and_wait 与 _await_done_marker 内实现，层级由助手重新标明。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：具体 Harness（如 `ClaudeCodeHarness.launch_and_wait`）已把特定提示词和环境变量组装为 `start_cmd` 与 `env`，现在调用公共函数 `run_agent` 负责在沙箱中真正拉起 Agent 并等待其执行结束。

2. **具体内容**：在沙箱的工作目录下用 `root` 权限创建元数据目录 `.harness` 并修改归属为 `agent:agent`；随后以 `agent` 用户身份委派 `exec_and_wait`，将输出流重定向至 `trajectory.jsonl`，脱机运行并等待其结束，直接返回整数退出码。

3. **建议构建的心智模型**：

   > `run_agent` 是所有 Harness 实现通用的**沙箱执行桥梁与归档守门人**。
   >
   > 它不做命令与环境变量的特化组装（那由具体的 Harness 负责），而是统一负责两件事：
   > 1. 在沙箱建立日志与轨迹存储归属目录（`workdir/.harness/trajectory.jsonl`）；
   > 2. 降权切换为 `agent` 用户，委托通用的脱机执行与完成标记轮询器 `exec_and_wait`，挂起等待其跑完并接回退出码。

4. **调用代码**（`ClaudeCodeHarness.launch_and_wait:71`）：

   ```python
   return await run_agent(
       sb,
       workdir=ctx.workdir,
       start_cmd=cmd,
       env=env,
       time_budget_sec=time_budget_sec,
   )
   ```

## 本场景的输入与输出

接住 [ClaudeCodeHarness.launch_and_wait](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) 组装好的材料：工作目录为 auth0-python，命令与环境为构造值，假定沙箱已就绪、最终执行成功返回退出码 0。没有运行真实命令。

**输入：沙箱对象、工作目录、启动命令、环境变量字典与超时预算。**

```python
# sb：原来的 E2BSandbox 对象
workdir = "/workspace/auth0-python"
start_cmd = "/usr/local/bin/claude -p '请阅读并解决题目...' --permission-mode bypassPermissions"
env = {
    "ANTHROPIC_BASE_URL": "http://adapter-host:18001",
    "ANTHROPIC_AUTH_TOKEN": "sid-demo",
    "ANTHROPIC_MODEL": "slime-actor",
}
time_budget_sec = 300
```

**输出：返回 `int` 退出码；教学场景假定为 0。**

```python
exit_code = 0  # int；表示远端 Agent CLI 整体运行的进程退出码
```

### 1. 准备元数据目录并赋权（109–110）

```python
meta_dir = f"{workdir}/.harness"
await sb.exec(f"mkdir -p {meta_dir} && chown agent:agent {meta_dir}", user="root", check=True, timeout=30)
```

- **统一元数据归档路径**：在具体题目的工作目录下创建 `.harness` 隐藏目录，用于隔离存放本次 Agent 运行的轨迹日志（`trajectory.jsonl`）。
- **特权准备与权限切换**：使用 `user="root"` 确保目录创建成功，并通过 `chown agent:agent` 将该目录的所有权移交给普通用户 `agent`，为接下来以非特权用户运行 CLI 提供写入权限。

### 2. 降权委派 exec_and_wait 脱机执行并返回退出码（111–122）

```python
exit_code, _ = await exec_and_wait(
    sb,
    cmd=start_cmd,
    user="agent",
    env=env,
    workdir=workdir,
    out_file=f"{meta_dir}/trajectory.jsonl",
    time_budget_sec=time_budget_sec,
    tag="run",
    want_output=False,
)
return exit_code
```

- **降权执行**：指定 `user="agent"`，不以 root 身份运行商业 Agent CLI，符合沙箱安全规范。
- **输出重定向与脱机运行**：将命令标准输出与错误重定向到 `meta_dir/trajectory.jsonl`，设置标签 `tag="run"`。`want_output=False` 表明主流程不需要在 Python 内存中完整缓冲命令行的大段字符串输出，只关注进程结束状态。
- **挂起等待整次运行**：`await exec_and_wait` 会在沙箱中通过后台脱机进程运行 `cmd` 并轮询退出标记，直到 CLI 结束或超时。本函数接住 `exit_code` 原样返回给父函数。

| 需要展开时进入 | 读完回到这里，接着使用什么 |
| --- | --- |
| [exec_and_wait，82–145](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)：脱机脚本生成、后台启动与完成标记轮询 | 取得 `(exit_code, _)`，接住退出码并直接返回调用方 |

## 我的直接表述（原话）

2026-10-22，用户确认进入本函数并提出先建卡：

> 好的那么我们来看一下这里的对于run agent的讨论吧
> 你要不先写一下这里的short term memory的笔记呢？

2026-10-23，用户拆分主体与执行阶段，并关注下钻标记：

> 我简单的理解是这里的第一个代码在做的事情是创建元数据的目录
> 按照root形式来执行
>
> 第二个是给用户agent权限
> 然后让起开始脱机运行
>
> 这里是分成了 两个阶段执行的
>
> 第三个是await done marker
> 这里你还没有直接给出对应的内容
>
> 里面的内容我简单理解
> 跑一下对应的test的部分？
> 但是内部这里是在做什么我觉得需要好好理清楚？
>
> 这样子就可以吧run agent的组成部分通过拆分主体和读面包屑的方式生成卡片了

2026-10-23，用户明确指出跨函数链接、职责边界与面包屑处理需求：

> 我这里大概明白了那么这里是否需要考虑一下这里的run agent需要和exec_and_wait至少给一个链接呢？
> run agent的职责是这些 但是这里exec_and_wait的职责不止这些
>
> 以及考虑一下应该如何处理这里的面包屑问题吧

助手核对：
- 用户提炼的“root 建元数据目录”与“赋权给 agent 并脱机运行”两阶段极其准确，并敏锐指出了下层第三核心动作“等待完成标记（await done marker）”。
- 澄清目标：本阶段执行的是外部 Agent CLI 自身（如 Claude Code CLI），去探索工作区并修改代码，并非运行评测测试脚本（grading test suite）。
- 职责与链接：用户敏锐区分了职责范围——`run_agent` 是 Harness 的上层特化调用者（职责仅为准备 `.harness` 目录赋权并传参启动），而 `exec_and_wait` 是底层通用长任务运行基座（职责涵盖安装重试、Agent 运行、防断连脱机与保活轮询），两者职责范围完全不同。
- 拆分面包屑：已在卡片顶部和步骤表格建立双向相对超链接与完整调用链面包屑（Breadcrumb Trail），下钻委托由独立卡片 [exec_and_wait](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md) 承接。

2026-10-23，整条启动链的复述节选（完整原话见[本次讨论](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#launch-restatement-and-http-entry)）：

> 然后再推进到这里的run agent
> run agent部分的内容我可以理解为我在做的事情是几个部分
> 1.首先是准备元数据的目录什么的
> 2.然后是具体的运行
> 2.1具体运行部分所需要做的内容
> 2.2第二是 脱机执行和幂等保护
> 2.3 第三各是轮训marker与防闲置gc的设定

助手校准：`run_agent` 自身准备 `.harness` 目录，以 `agent` 用户委派命令并返回退出码。脱机启动与防重复启动在 `exec_and_wait`，marker 轮询在 `_await_done_marker`；把它们作为被委派的阶段即可。

## 尚不清楚

- 已经弄清：`run_agent` 自身负责两阶段的目录特权准备与非特权委派；运行的主体是 Agent CLI 自身；下层通过 `exec_and_wait` 的脱机脚本与 marker 轮询规避了 HTTP/2 长连接断开与沙箱空闲 GC 回收。
- 尚不清楚：轨迹输出文件 `trajectory.jsonl` 后续由哪个组件收集或消费。
- 尚不清楚：基准评测脚本（grading / test suite）在后续哪个函数中正式拉起。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码定义见页首；父调用见 `claude_code.py:71`，委派的沙箱执行器见 `sandbox.py:82–145`。
- 代码摘自源码 `slime/agent/harness/common.py:107–122`。2026-10-22 核对目录创建命令、`user="agent"`、输出文件路径与退出码交接。
- 形成过程：[Step 7 · 启动命令、环境变量与等待结果](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#launch-and-wait)。

</details>
