# HarnessContext

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../../../02-rollout-reward/steps/step-011-generate-and-rm-group/03-long-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 02-short-term-memory](../../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- 本步对照调取：2026-10-25，从[本步长期快照](../../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/03-long-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)调取完整类卡，用于比较数据对象与上下文管理器；保留原版本、原话和认识时间。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 02 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/harness/common.py:42–54](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L42-L54)，由助手核对；记录对象是 dataclass。
- 首次接触：Step 7 随 `BaseHarness.run:98–102` 定位运行上下文；2026-10-22 按用户要求首次单独展开。
- 最近认识更新：2026-10-23，用户将其概括为把散落的上下文收拢；对象在本地 Python 中传递，启动方法再取字段形成命令/环境，CLI 不直接接收 ctx。后一边界由助手补充，尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`BaseHarness.run` 已接到沙箱和运行参数，完成用户准备后，将后续配置与启动所需的共同信息组合起来。当前采用 `ClaudeCodeHarness`。

2. **具体内容**：`HarnessContext(...)` 创建一个本地对象，保存 `workdir`、`session_id`、`adapter_url`，并使用默认的 `model_label="slime-actor"`。调用方将对象命名为 `ctx`，传给后面的配置与启动方法。

3. **建议构建的心智模型**：

   > `HarnessContext` 定义一次 CLI 启动所需的共同参数；`ctx` 是本次调用创建的那份参数对象。
   >
   > 它把“在哪个目录运行、属于哪次会话、请求哪个 Adapter、使用什么模型名称标签”放在一起，供后续方法读取。这一步只组织本地数据。

4. **调用代码**（`BaseHarness.run:98–104`，保留构造与紧接着的两次交接）：

   ```python
   ctx = HarnessContext(
       workdir=workdir,
       session_id=session_id,
       adapter_url=adapter_url,
   )
   await self.write_config(sb, ctx)
   return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)
   ```

## 本场景的输入与输出

沿用 [BaseHarness.run 的输入示例](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)：工作目录为 `/workspace/auth0-python`，编号与地址是教学构造值。以下只验证本地对象的构造，不请求该地址。

**输入：三个已有的字符串参数。**

```python
ctx = HarnessContext(
    workdir="/workspace/auth0-python",
    session_id="sid-demo",
    adapter_url="http://adapter-host:18001",
)
```

**输出：一个 HarnessContext 实例，由局部变量 ctx 引用。**

| 对象中的字段 | 本例读取结果 | 在当前 Claude Code 场景中的用途 |
| --- | --- | --- |
| `ctx.workdir` | `"/workspace/auth0-python"` | 后续交给 `run_agent`，指定命令的工作目录 |
| `ctx.session_id` | `"sid-demo"` | 后续放入 `ANTHROPIC_AUTH_TOKEN`，携带已有的会话编号 |
| `ctx.adapter_url` | `"http://adapter-host:18001"` | 后续放入 `ANTHROPIC_BASE_URL`，指定 CLI 请求的 Adapter 地址 |
| `ctx.model_label` | `"slime-actor"` | 后续放入 `ANTHROPIC_MODEL`；是传给 CLI 的模型名称标签 |

### 类定义怎样对应这个结果（42–54）

仅省略源码中的说明文字，完整字段如下：

```python
@dataclass(frozen=True)
class HarnessContext:
    workdir: str
    session_id: str
    adapter_url: str
    model_label: str = "slime-actor"
```

- **类与实例**：`HarnessContext` 是类名；`HarnessContext(...)` 创建一个实例；`ctx` 是引用这个实例的局部变量名，后续通过 `ctx.workdir` 等属性取值。
- **构造与默认值**：`@dataclass` 生成初始化方法，本类没有另一个手写的 `__init__` 要追。调用处传入前三项，第四项使用默认值。
- **冻结字段**：`frozen=True` 防止创建后用普通赋值意外改写字段；例如 `ctx.session_id = "another-session"` 会抛出 `FrozenInstanceError`。语言依据见[补充参考](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/references/harness-context.md)。
- **本步数据边界**：`ctx` 保存已有的编号与地址；这次构造不会申请沙箱、登记新会话或发起 HTTP 请求。`sb`、`prompt`、`time_budget_sec` 仍由 `run` 作为独立参数传下去。

### 构造后交给谁（103–104）

- `self.write_config(sb, ctx)` 收到这个对象。当前 `ClaudeCodeHarness.write_config:44–55` 的函数体没有读取 `ctx`，只向沙箱写入 CLI 初始化配置；不能仅凭参数表就认为它使用了全部字段。
- `self.launch_and_wait(sb, ctx, prompt, time_budget_sec)` 继续接收同一个对象。当前实现的 62–65 行读取编号、地址和模型标签，放进 `env`；71 行读取工作目录并交给 `run_agent`。这里先知道字段去向，实际启动留在对应函数中展开。
- `model_label` 不负责加载或切换模型。类说明明确指出：它是 CLI 使用的名称标签，Slime Adapter 服务的是上游 SGLang 已加载的模型。

读完返回 [BaseHarness.run](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md) 的 **103 行**，下一处是 `write_config(sb, ctx)`。

## 我的直接表述（原话）

首次展开时的阅读请求：

> 好的那么现在看一下这里的ctx harnesscontext的部分吧
> 看一下这里到底是在做什么这件事情

随后对已理解内容的复述：

> 好的我现在知道了这个claude或者codex的harness是自带在哪一个workdir还有sessionid 以及对应的adapter url等一系列信息的

助手核对：已联系到 Harness 运行需要的三项信息。这里的“自带”需具体化为：调用方把信息传入 `run`，`run` 创建局部 `ctx` 保存它们，再传给配置和启动方法；源码没有在这里将这些值赋给 `self` 的属性。这一补充不自动视为用户已确认。

2026-10-23，整条启动链的复述节选（完整原话见[本次讨论](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#launch-restatement-and-http-entry)）：

> 然后进入到西面的这个harness context
> 纯粹是把之前散落的上下文捡起来

助手校准：`ctx` 是 Slime 本地的参数对象。后续 Python 代码从中取值，将工作目录、环境变量等交给执行端；CLI 不直接读取这个 Python 对象。

## 尚不清楚

- 用户已复述三项运行信息；局部 `ctx` 与 Harness 对象属性的区别、默认字段及冻结机制尚未逐项复述。
- `write_config` 已在[本步函数卡片](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md)展开；启动与等待已在子卡展开；本次继续区分本地 ctx 和远端进程实际拿到的环境变量。

<details>
<summary>来源、验证与完整例子</summary>

- 源码固定于 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：类定义见页首；构造与交接见 `harness/common.py:98–104`；当前配置与字段取用见 [harness/claude_code.py:44–71](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L44-L71)。
- 2026-10-22 从固定源码提取原类定义，在 Python 3.12.3 中构造本例，确认四个字段及默认标签；普通字段赋值抛出 `FrozenInstanceError`。没有导入或启动完整 Harness，也没有远端调用。
- [dataclass 的中英原文与验证范围](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/references/harness-context.md)；类记录的形式沿用此前 Session 卡片，保留相同栏目。
- 形成过程：[Step 7 · 展开 HarnessContext](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#harness-context)。
- 后续复述与归属澄清：[Step 7 · 配置准备与启动的边界](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/04-flow.md#write-cli-config)。

</details>
