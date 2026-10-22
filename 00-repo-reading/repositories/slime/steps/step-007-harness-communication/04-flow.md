# 04 · 问题、解释与范围确认

[本步 scope](01-scope.md) · [通信路径参考](references/run-communication-path.md)

下面第一节完整保留独立成步前提出的问题和当时的解释。其中“没有新建下一 step”等表述描述拆分前的状态；用户随后的归属纠正与本步安排见第二节。原提出位置保留[迁移指向](../step-006-prepare-workspace/04-flow.md#run-cross-process-communication)。

<a id="run-cross-process-communication"></a>

## 1. 2026-10-22：准备完成后，信息怎样经过沙箱、Adapter 和模型服务

用户继续指出跨组件交接的缺口：

> 但是还有一个问题吧
> 也就是
> 是准备好了adapter
> 也吧sandbox准包好了
> 也把workspace准备好了
> 但是这里的harness_cli run的时候
> 之前有讲清楚这里的harness是怎么把对应的请求发到sb或者怎么run的
> 我的意思是怎么做到吧这里的信息在这个调度的地方
> 以及sandbox 还有这里的sglang里面发送到不同的地方的呢？
>
> 之前的run的第一步是不是只是说了格式是怎么跑的
> 但是没有说明信息是怎么在不同的地方流动或者传输的？

核对发现：Step 1 的 scope 与 task flow 主体沿 `_run_turn` 解释一份请求的内部转换、生成和响应；task flow 第 6 节的折叠区也保留了 Harness 启动、HTTP 回连和响应往返。因此不能说此前完全没有说明传输，但这些材料分散，用户当前仍未建立连贯的运行位置与交接模型。

本轮补充的关系独立放在 [从 Harness 启动到模型回复：信息经过哪些地方](references/run-communication-path.md)：

1. `generate` 与 Harness 的方法先在 Slime 侧调用；`sb` 是本地操作对象，经 SDK 将命令和环境发给远端执行沙箱。
2. CLI 启动时取得 `ANTHROPIC_BASE_URL` 和会话标识，运行期间自行通过 HTTP 请求 Adapter。Adapter 在独立服务线程中接收请求，进入已读的 `_run_turn`。
3. Adapter 使用另一个地址 `sglang_url` 请求 SGLang，发送 token ID 与采样参数；结果先回 Adapter，经解析与协议组装后再回应 CLI。
4. 一次模型响应回来后，CLI 可以继续任务；Harness 等待的是 CLI 整次运行结束。启动命令、模型请求与完成标记不是同一个交付结果。

本次建议优先回查 `BaseHarness.run:104 → ClaudeCodeHarness.launch_and_wait:57–71`，观察已准备的输入怎样变成 `cmd`、`env`，再沿 `run_agent → exec_and_wait` 接清启动边界。当前只补跨组件说明，没有新建下一 step、重写原函数卡片或标记完整启动机制已掌握；题目写入和父函数收束仍保留为原步骤待接续项。

证据仍绑定本地 `2f2318653f6f794dddd321eff7c9d4b7b174643f`；已有 `swe.py` 空白改动和未跟踪文件保留。2026-10-22 再查官方 main 仍为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本轮未更新 checkout。CLI 外部行为查阅官方环境变量、命令参数和网关接口文档，没有声称读过当前安装包内部的发送函数；没有实际运行 CLI、沙箱或模型服务。解释与建议均为助手提供，尚待用户反馈。

<a id="separate-communication-step"></a>

## 2. 2026-10-22：确认独立成步，并沿用既有 skills

用户纠正记录归属：

> 不是放在step06啊 应该单独创建一个step吧
> 把这里的讲清楚 同时使用之前的skill来做这件事情

按此确认建立 Step 7，负责 Harness 启动与跨组件通信；Step 6 保留任务工作区准备。原通信参考和上面的原始讨论迁到本步，原位置保留链接，未删除形成过程或改写个人理解。

- 使用 [repo-reading-scope](../../../../../.agents/skills/repo-reading-scope/SKILL.md) 及其剪枝、局部导航 reference：scope 保留完整七项任务骨架，展开第 4 项，并区分本地函数调用、沙箱 SDK 操作和两次 HTTP 往返。与目标有关的地址和会话配置保留，其余配置、检查、日志、异常与失败包装暂时折叠。
- 使用 [repo-reading-short-term-memory](../../../../../.agents/skills/repo-reading-short-term-memory/SKILL.md)：按已认可栏目整理 `BaseHarness.run` 与 `ClaudeCodeHarness.launch_and_wait` 两张卡片；前者说明完整启动调用的输入输出与内部交接，后者解释命令、环境变量和委派启动。已有 `_run_turn` 等记录从长期记忆复用。
- 使用 [repo-reading-memory](../../../../../.agents/skills/repo-reading-memory/SKILL.md)：将 Step 6 的 35 份累计记录与 4 份本步记录合并为 38 份。同名 `ensure_agent_user` 保留执行沙箱和前序评测两个完整场景，来源与未知一并保留。
- [repo-reading-order](../../../../../.agents/skills/repo-reading-order/SKILL.md) 的选择理由继续沿用：当前卡点是启动参数怎样决定通信目标，所以从 `BaseHarness.run:104` 进入 `ClaudeCodeHarness.launch_and_wait` 的 `cmd` 与 `env`，不要求重读前序安装或先深入 SDK 网络栈。

本步首先提供整体位置、局部导航与两张函数卡片；`run_agent`、`exec_and_wait` 暂保留源码定位和交接解释，尚未为它们预建卡片。`05-task-flow.md` 保留待阅读后总结的职责，没有把初始解释写成已完成的学习结论。唯一进度转到 Step 7；Step 6 的末尾题目写入与收束状态如实保留。

本轮核对固定源码、目录与引用，保留 Slime 工作区原差异；没有执行 CLI、沙箱命令或模型请求。用户确认的是独立步骤与研究范围，尚未对新卡片中的机制逐项反馈。

<a id="reuse-ensure-agent-user"></a>

## 3. 2026-10-22：ensure_agent_user 是否已经读过，接下来怎样逐项接续

用户追问：

> 从这里的ensure agent user开始对吗？ 一个个看下去
> 还是这个之前已经处理过了？

核对固定源码，`BaseHarness.run:97` 确实先执行 `ensure_agent_user(sb, workdir)`。这个函数在 Step 2 首次接触，Step 6 又在执行沙箱场景中整理过；[Step 6 原卡片](../step-006-prepare-workspace/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)保留了用户对目录、Git、权限准备的复述及“大概理解了”的反馈。本步已有[完整继承记录](03-long-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)。

本次接续按 `run` 的实际顺序走，已读函数只恢复必要关系：

1. **97 行，短回顾**：接住已有 `sb` 和 `workdir`，在远端准备 `agent` 用户、目录归属与 Git 设置，正常返回 `None`；后面继续用同一个 `sb`。源码仍会再次执行这次调用，阅读时复用已有认识。
2. **98–102 行，当前观察点**：`HarnessContext(...)` 将 `workdir`、`session_id`、`adapter_url` 组合为本地 `ctx`，供后面的调用取用。这一步本身不发送网络请求。
3. **103 行，随后接续**：查看当前 `ClaudeCodeHarness.write_config` 写入哪些 CLI 配置，说明结果留在哪里，再回到 `run`。
4. **104 行，再深入启动**：进入 `ClaudeCodeHarness.launch_and_wait`，接清 `cmd`、`env` 和远端执行；它仍是本步通信问题的重点。

此前推荐“首先深入 launch_and_wait”指需要重点展开的函数；局部接续仍需说明到达它之前的上下文和配置。这里将导航明确为先回顾 97 行、再从 98 行接着读，不把当前问题记成用户已理解 `ctx`、配置或启动机制，也不为这些中间操作预建新卡片。

<a id="harness-context"></a>

## 4. 2026-10-22：展开 ctx 与 HarnessContext

用户确认当前阅读点：

> 好的那么现在看一下这里的ctx harnesscontext的部分吧
> 看一下这里到底是在做什么这件事情

从 `BaseHarness.run:98–102` 回查同文件 42–54 行。`HarnessContext` 是实际定义的 dataclass，沿用此前 Session 的记录方式，保存为[本步类卡片](02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)；父函数卡片仍保留完整调用和返回位置，并加上局部跳转。

本轮解释围绕同一组输入展开：

1. `run` 已经收到工作目录、会话编号和 Adapter 地址。构造调用把这三个字符串存入一个本地 `HarnessContext` 实例；未显式传入的 `model_label` 采用 `"slime-actor"`。
2. `HarnessContext` 是类名，`HarnessContext(...)` 创建实例，`ctx` 是引用这份实例的局部变量。`ctx` 是本次启动的参数集合；这次构造不创建远端资源，也不自动发出请求。
3. 后续把同一个 `ctx` 传给 `write_config` 和 `launch_and_wait`。核对当前 Claude Code 实现后补充：前者接收但没有读取 `ctx`；后者才读取四个字段，组织工作目录与 CLI 环境变量。不能根据函数参数表推断每个实现都读取了全部字段。
4. `@dataclass` 提供生成的初始化方法；`frozen=True` 防止普通赋值意外改写字段。语法依据单独放在[中英参考](references/harness-context.md)，本次不展开装饰器或特殊方法机制。

从原始类定义提取的本地构造例子在 Python 3.12.3 中确认了四个字段、默认标签和冻结行为。Slime HEAD 仍为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，官方 main 复核为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；未切换源码版本、启动远端沙箱或请求模型。

这次确认的是阅读对象，尚无用户对解释的复述。当前停在“得到 `ctx`，准备交给下一行”；回到 `run:103` 的 `write_config(sb, ctx)` 是下一处接续候选，尚未展开其内部命令。

<a id="write-cli-config"></a>

## 5. 2026-10-22：运行信息的复述，以及 write_config 的配置准备

用户先复述运行信息，再要求进入下一行，并给出对写配置的理解：

> 好的我现在知道了这个claude或者codex的harness是自带在哪一个workdir还有sessionid 以及对应的adapter url等一系列信息的
> 好了继续吧
> 这里再通过这里的write_config做了什么呢？
>
> 我的简单理解是把这里关于是否会会自动化的运行什么的设置了
> 然后这里同时在通过sb 传输一系列的配置内容
>
> 这是我的理解
> 写一下cli配置 设置不需要人为给提示 直接全自动执行
> 这是我对于这里的理解
>
> 这里对于harness的write config的理解

对前一项的核对：用户已经联系起工作目录、会话编号和 Adapter 地址。这里补充“自带”的准确位置：这些值由调用方传入 `run`，组合到局部 `ctx`，再传给具体 Harness 方法；本段没有把它们写成 `self` 的属性。原话与补充已进入 [HarnessContext 卡片](02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md)，不把细分区别视为用户已确认。

本轮从 `BaseHarness.run:103` 进入实际的 `ClaudeCodeHarness.write_config:44–55`，解释以下对应关系：

1. **准备什么**：本地生成包含 `hasCompletedOnboarding=true` 和 `bypassPermissionsModeAccepted=true` 的 JSON。按源码意图，它们分别记录已完成首次引导、已接受绕过权限确认模式。
2. **怎样传递**：JSON 文本被放进一条组合 shell 命令，通过已有的 `sb.exec` 提交给远端沙箱，执行用户为 `root`；当前实现没有读取 `ctx`。
3. **在哪里生效**：命令创建 `/home/agent/.claude`，用 `tee` 将同一份 JSON 写进 `/home/agent/.claude.json` 和 `/home/agent/.claude/settings.json`，再将归属设为 `agent:agent`。效果是远端配置文件变化，正常返回值为 `None`。
4. **与自动运行的边界**：这一步预先记录两项确认状态。实际启动以及 `-p`、任务 `prompt` 和 `--permission-mode bypassPermissions` 在后续 `launch_and_wait` 中组织。程序仍需提供任务提示；不能把“不等待这些人工确认”理解成没有任务输入，或单凭写配置就已开始执行任务。

已按短期 memory 格式新建 [ClaudeCodeHarness.write_config 卡片](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md)，保留用户原话、完整输入输出和代码对应说明；`run` 的调用处链接到它。Codex 的配置内容由另一实现负责，这次不把 Claude 的两个字段推广到所有 Harness。

使用原函数和本地操作记录器，核对了提交次数、两项配置、文件路径、执行参数、没有读取 `ctx` 及返回 `None`。未执行 shell、写入远端文件或启动 CLI。固定源码与官方 main 的版本复核均未变化。当前新增的是配置准备的理解，启动与等待仍待接续；回到 `run:104` 后的下一处为 `launch_and_wait`。

<a id="launch-and-wait"></a>

## 6. 2026-10-22：启动命令、环境变量与等待结果

用户继续指定当前入口：

> 好的那么现在再来看一下这里的launch and wait具体是要做什么吧

从 `BaseHarness.run:104` 进入 `ClaudeCodeHarness.launch_and_wait:57–71`。前一步已写好 CLI 配置，本轮沿已有 `sb`、`ctx`、`prompt` 和时间预算，观察三项交接：

1. **`prompt → cmd`**：在 Slime 一侧拼出 `/usr/local/bin/claude -p ...` 命令。提示沿用 `swe.SWE_PROMPT`，要求读取题目文件并解决问题；固定开关设置权限模式和输出格式。构造字符串本身尚未启动 CLI。
2. **`ctx → env`**：将 Adapter 地址、会话编号和模型标签放入对应环境变量，并合入固定开关。`env` 此时是本地字典，下层会把它交给远端进程，CLI 再从自己的环境中取值。主例不启用额外覆盖，卡片仍保留追加参数及覆盖环境的完整代码。
3. **启动材料 → `run_agent` → 退出码**：同一个 `sb`、工作目录、命令、环境字典和时间预算一起交给共同执行函数。`launch_and_wait` 委派执行并等待，正常返回值为整次 CLI 运行的退出码；运行期间的模型回复通过 HTTP 回到 CLI。具体写脚本、启动及等待标记的实现只定位，留在下一层展开。

直接补充[已有 launch_and_wait 卡片](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md)，保留原格式和两段代码，增加完整环境结果、运行位置及返回值边界。没有为 `run_agent`、`exec_and_wait` 预建卡片。

验证使用提取的原方法、原类设置和默认任务提示；用本地记录器代替 `run_agent`，检查提示整体作为一个命令参数、六项环境、沙箱对象、目录与预算的传递，以及替身退出码原样返回。没有运行远端 CLI 或真实模型请求。复核公开 CLI 与环境变量文档，仅用于接口含义对照；Slime 固定 HEAD 与官方 main 均未变化。

本轮是用户明确要求展开后的助手讲解，尚无对命令和环境关系的直接复述。当前先看清本函数怎样交出启动材料、接回退出码；下一处接续候选是 `harness/common.py:107` 的 `run_agent`。
