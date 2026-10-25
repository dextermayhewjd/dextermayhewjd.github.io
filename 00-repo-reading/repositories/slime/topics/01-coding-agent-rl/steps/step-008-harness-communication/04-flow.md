# 04 · 问题、解释与范围确认

[本步 scope](01-scope.md) · [通信路径参考](references/run-communication-path.md)

下面第一节完整保留独立成步前提出的问题和当时的解释。其中“没有新建下一 step”等表述描述拆分前的状态；用户随后的归属纠正与本步安排见第二节。原提出位置保留[迁移指向](../step-007-prepare-workspace/04-flow.md#run-cross-process-communication)。

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

- 使用 [repo-reading-scope](../../../../../../../.agents/skills/repo-reading-scope/SKILL.md) 及其剪枝、局部导航 reference：scope 保留完整七项任务骨架，展开第 4 项，并区分本地函数调用、沙箱 SDK 操作和两次 HTTP 往返。与目标有关的地址和会话配置保留，其余配置、检查、日志、异常与失败包装暂时折叠。
- 使用 [repo-reading-short-term-memory](../../../../../../../.agents/skills/repo-reading-short-term-memory/SKILL.md)：按已认可栏目整理 `BaseHarness.run` 与 `ClaudeCodeHarness.launch_and_wait` 两张卡片；前者说明完整启动调用的输入输出与内部交接，后者解释命令、环境变量和委派启动。已有 `_run_turn` 等记录从长期记忆复用。
- 使用 [repo-reading-memory](../../../../../../../.agents/skills/repo-reading-memory/SKILL.md)：将 Step 6 的 35 份累计记录与 4 份本步记录合并为 38 份。同名 `ensure_agent_user` 保留执行沙箱和前序评测两个完整场景，来源与未知一并保留。
- [repo-reading-order](../../../../../../../.agents/skills/repo-reading-order/SKILL.md) 的选择理由继续沿用：当前卡点是启动参数怎样决定通信目标，所以从 `BaseHarness.run:104` 进入 `ClaudeCodeHarness.launch_and_wait` 的 `cmd` 与 `env`，不要求重读前序安装或先深入 SDK 网络栈。

本步首先提供整体位置、局部导航与两张函数卡片；`run_agent`、`exec_and_wait` 暂保留源码定位和交接解释，尚未为它们预建卡片。`05-task-flow.md` 保留待阅读后总结的职责，没有把初始解释写成已完成的学习结论。唯一进度转到 Step 7；Step 6 的末尾题目写入与收束状态如实保留。

本轮核对固定源码、目录与引用，保留 Slime 工作区原差异；没有执行 CLI、沙箱命令或模型请求。用户确认的是独立步骤与研究范围，尚未对新卡片中的机制逐项反馈。

<a id="reuse-ensure-agent-user"></a>

## 3. 2026-10-22：ensure_agent_user 是否已经读过，接下来怎样逐项接续

用户追问：

> 从这里的ensure agent user开始对吗？ 一个个看下去
> 还是这个之前已经处理过了？

核对固定源码，`BaseHarness.run:97` 确实先执行 `ensure_agent_user(sb, workdir)`。这个函数在 Step 2 首次接触，Step 6 又在执行沙箱场景中整理过；[Step 6 原卡片](../step-007-prepare-workspace/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)保留了用户对目录、Git、权限准备的复述及“大概理解了”的反馈。本步已有[完整继承记录](03-long-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)。

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

<a id="cmd-env-mental-model"></a>

## 7. 2026-10-22：澄清物理边界与 cmd/env 心智模型构建

用户对 `launch_and_wait` 的输入与环境处理提出疑问并复述：

> 之前是把这里的harnesscontext的部分写到了这里的harness context里面，然后吧这些写进了这个harness的配置里面。
> 然后这里的内容是launch and wait的内容，我可以简单的理解为这里做的事情更多的是在于把prompt的启动材料什么的全部都写在这里的cmd里面？
> 然后这里的aenv的内容感觉更多的是在处理这里的当前的anthropic base的url还是只是存在于ctx里面，现在需要吧这里的env都提取出来？我其实不是特别理解，没有办法完全构建这里的心智模型。

针对这一关键疑问，助手与用户澄清了**运行物理边界与进程隔离**的区别：

1. **`ctx` 与沙箱 CLI 的物理隔离**：`ctx` 只是宿主机 Python 进程中的一个 Dataclass 对象，而实际执行代码的 `claude` CLI 是远端独立沙箱中的外部程序，根本无法访问本地 Python 内存。
2. **官方 CLI 的环境变量协议**：Claude Code CLI 设计上只认操作系统的环境变量（`ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN`）来确定 API 请求目标与鉴权。
3. **心智模型确立**：
   - **`cmd`**：派发任务与提示词（如 `/usr/local/bin/claude -p "..." --permission-mode bypassPermissions`）；
   - **`env`**：通过注入环境变量实现“偷梁换柱”，把本该发往 Anthropic 官方公网的请求，重定向给 Slime 本地部署的 Adapter 服务。

随后用户完整复述了这一心智模型，并敏锐指出了单函数源码职责与整体解释背景的边界问题：

> 我对于这一个模块大概的理解是这里吧这个内容都组装好了，因为claude code cli时会读取环境变量的，然而这里在launch and wait的部分修改了这里的的系统变量，这样子之后发生交互的时候会向这里的这个http也就是后端的服务来发送请求，是这种方式我说对了吗？这里是我的心智模型。
> 但是当前这个function内部其实还是没有出现这里的后端服务或者转发推理请求什么的的对吧？这个function的心智模型里面是不是包含了整个问题的解释？
> 那么考虑一下这里应该怎么处理这里的图呢？全部删掉好像不合适，是否需要更加好的标注这里这个函数到底负责的模块是什么？

据此，在 [ClaudeCodeHarness.launch_and_wait 卡片](02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) 的纯文本 ASCII 架构流转图与分层对照表中，明确用双线框 `╔══ 【本函数直接职责：ClaudeCodeHarness.launch_and_wait (57–71 行)】 ══╗` 圈定本函数真正负责的 15 行代码范围（接收输入、组装 `cmd`/`env`、调用 `run_agent` 等待退出码），并将沙箱容器及后端服务明确标注为“下游协同背景（非本函数代码）”，既保留了为什么要组装 `env` 的全局动机，又严格守住了单函数卡片的源码边界。

随后用户进一步把该机制从 Claude 推广到 Codex 等通用 Harness 体系，阐明 Harness 架构设计的必然性：

> 好的那么我现在其实清楚为什么需要有这里的这一步的launch and wait的部分。
> 这里这一步更多的是因为这里的这个claude和codex的底层的机制，也就是说因为这里的这个运行方式所以我需要在底层不单是在write config，还需要修改本身的这里的env。
> 这是我对于这里的这个理解，包括codex也一样，底层都是会检查这个env，所以会需要处理这个问题。

助手核对：这一归纳非常深刻。`write_config` 负责沙箱文件系统的静态配置（如跳过引导、权限确认），而 `launch_and_wait` 负责运行时进程环境的动态注入。无论是 Claude（`ANTHROPIC_BASE_URL`）还是 Codex（`OPENAI_BASE_URL`），主流 CLI 均遵循读取环境变量确定服务端点的规范，因此 Harness 必须在启动材料中把环境提取并注入。该卡片已正式作为“跨环境调度型函数”标准样例沉淀至 Skill 模板库。本函数认知完全闭环，下一处候选接续为 `harness/common.py:107` 的 `run_agent`。

<a id="run-agent-entry"></a>

## 8. 2026-10-22：进入 run_agent 与建立短期记忆卡片

在完成 `launch_and_wait` 的认知闭环后，用户确认进入下游通用调度函数 `run_agent` 并提出先建卡：

> 好的那么我们来看一下这里的对于run agent的讨论吧
> 你要不先写一下这里的short term memory的笔记呢？

助手根据用户指令在 `02-short-term-memory/functions/slime/agent/harness/common.py/` 下创建了独立的 [run_agent 短期记忆卡片](02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md)，严格遵循 6 项规范：
1. **源码定位**：`slime/agent/harness/common.py:107–122`（共 15 行）。
2. **两阶段职责**：
   - 特权准备元数据目录：`sb.exec("mkdir -p {meta_dir} && chown agent:agent {meta_dir}", user="root")`；
   - 降权委派脱机执行并等待退出码：`exec_and_wait(sb, cmd=start_cmd, user="agent", env=env, workdir=workdir, out_file=f"{meta_dir}/trajectory.jsonl", ...)`。
3. **输入输出与边界**：输入由上层 Harness 传入构造好的 `start_cmd`、`env`、`sb` 与超时预算；输出仅返回 `int` 退出码。
4. **认知状态真实保留**：用户原话完整保留，注明机制理解尚待用户复述，绝不预填或假定用户已经掌握。

<a id="run-agent-and-exec-and-wait"></a>

## 9. 2026-10-23：拆分主体与面包屑，澄清执行主角与建立 exec_and_wait 卡片

用户在审视 `run_agent` 的 15 行代码后，提出主体拆分与阶段分析：

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

针对用户的疑问与直觉，助手进行了如下澄清与拆解：
1. **执行主角澄清**：
   - 用户提到“跑一下对应的test的部分”，助手明确指出：这里执行的不是基准评测的测试套件（grading test suite），而是**外部商业 Agent CLI 自身（例如 Claude Code CLI）**。
   - 上游传入的命令是 `/usr/local/bin/claude -p '...SWE_PROMPT...'`。Agent 正在沙箱里探索代码、定位问题与修改文件；真正的基准评测脚本会在 Agent 结束退出后由后续评估步骤拉起。
2. **下钻核心机制：`exec_and_wait` 的分布式工程设计**：
   - **痛点**：普通 `sb.exec` 的 HTTP/2 长流在长达数分钟的命令运行中极易因网关超时或网络波动断连（severed），丢失非幂等的退出状态；同时远端沙箱容器在无 RPC 时会被平台闲置垃圾回收（Idle-GC）。
   - **解法（脱机启动 + 文件标记 + 保活轮询）**：
     - 生成 `/tmp/.run.sh` 脚本，在结尾写入 `echo $? > /tmp/.run.done`；
     - 使用 `setsid bash ... &` 后台脱钩启动，短 RPC 立即返回；
     - `_await_done_marker` 每 5 秒调一次超短的 `test -f && cat` 轮询退出码，兼作向云平台发送心跳保活。
3. **沉淀主体与面包屑卡片**：
   - 用户确认：“好的那么请按照这种方式来写一下这里的主题函数以及独立卡片什么的吧”。
   - 更新主体卡片 [run_agent](02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md)，记录两阶段特权目录准备与降权委派；
   - 建立独立面包屑下钻卡片 [exec_and_wait](02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md)，完整绘制交互流程图并梳理脱机与保活机制；
   - 更新 [02/overview.md](02-short-term-memory/overview.md) 索引。详细机制尚待用户进一步复述确认。

<a id="breadcrumbs-and-shared-infra-boundary"></a>

## 10. 2026-10-23：辨析特化上游与通用基座，确立面包屑与跨卡链接规范

在卡片建立后，用户进一步提出了极具洞察力的架构与记录疑问：

> 我这里大概明白了那么这里是否需要考虑一下这里的run agent需要和exec_and_wait至少给一个链接呢？
> run agent的职责是这些 但是这里exec_and_wait的职责不止这些
> 
> 以及考虑一下应该如何处理这里的面包屑问题吧

针对用户的两个深刻关切，助手与用户确立了以下认知模型与记录规范：

### 1. 职责边界辨析：特化上游 vs 通用基座

- **`run_agent`（业务特化层）**：
  - 源码位置：`slime/agent/harness/common.py:107–122`（仅 15 行）；
  - 职责范围极窄：仅负责在具体工作区用 root 创建 `.harness` 目录赋权、指定以 `agent` 用户运行命令、将输出流定向至 `trajectory.jsonl`，并返回退出码。
- **`exec_and_wait`（通用沙箱长任务基础设施）**：
  - 源码位置：`slime/agent/sandbox.py:82–145`；
  - 职责范围极其宽广：它是整个 Slime 框架操作沙箱的底层通用设施，不仅被 `run_agent` 调用，还在 Step 5 的 [`install_npm_cli`](03-long-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md) 中用于安装 Node 与 CLI 工具包（配合外层重试循环、捕获完整日志），同时支持输出截断（`tail -c 512`）、防重复拉起锁（`lock_dir`）和超时处理。
  - **结论**：绝不能把 `exec_and_wait` 视作 `run_agent` 的专属私有函数，而应视作整个框架共享的脱机运行基础设施。

### 2. 面包屑与跨卡链接解决方案

为解决复杂调用链中的“迷航”问题（既不让顶层失焦，也不让底层脱节），确立三条规范：
1. **相对路径双向互通**：在 `run_agent.md` 与 `exec_and_wait.md` 之间建立精确的相对跳转超链接（`../../sandbox.py/exec_and_wait.md` 与 `../harness/common.py/run_agent.md`），确保在任何 Markdown 离线阅读器或渲染器中点击即可跳转。
2. **卡片顶部的统一面包屑导航条（Breadcrumb Trail）**：
   在每张卡片顶部标题下方，统一展示调用链位置，例如：
   `> **调用链面包屑**：[Step 7 范围] > [02 概览] > [BaseHarness.run] → [launch_and_wait] → [run_agent] → **exec_and_wait**`
   读者点开任何一张卡片，立刻明白“我是从哪一层进来的、前面走了几级”。
3. **“读完返回（Read & Return）”表格**：
   在 `exec_and_wait.md` 底部的展开表格中，明确列出它的两个已知上层入口（Step 5 的 `install_npm_cli` 与 Step 7 的 `run_agent`），并注明从这里读完后分别接回各自的业务主线。

随后，用户明确指示将该方案固化为标准参考：

> 好的那么把这个面包屑的部分也作为一种reference存在吧

助手据此在 Skill 库正式建立了第四种参考规范：[.agents/skills/repo-reading-short-term-memory/references/breadcrumb-navigation-and-shared-infra.md](../../../../../../../.agents/skills/repo-reading-short-term-memory/references/breadcrumb-navigation-and-shared-infra.md)，并将条目同步至 [SKILL.md](../../../../../../../.agents/skills/repo-reading-short-term-memory/SKILL.md) 的“模板与样例”章节，供后续跨层级与共享设施建卡直接复用。

<a id="reactivate-prior-function-memory"></a>

## 11. 2026-10-23：本步需要的旧函数调入短期记忆

用户指出反复跳回长期记忆会打断当前阅读：

> 使得也就是目前我们在做的内容是 这里的harness_cls
> run 之前到底是怎么起来的
>
> 我们之前应该是已经除了了 这里的sandbox的ensure agent user
> 但是有一个问题
> 我们这里如果是之前就处理过得这个函数我觉得当前也应该需要再次从long term memroy中拉出来？
> 放在short term memory里面啊
> 否则我还需要重新点击到long term memory 里面看岂不是非常麻烦嘛

**助手核对与处理**：

- 当前范围仍是 `HARNESS_CLS().run(...)` 内部的准备、启动和通信。`ensure_agent_user` 位于 `BaseHarness.run:97`，返回后到第 98 行组合 `ctx`；它是进入 `run` 后的准备动作。
- 原完整卡片已在本步 `03` 中。将其复制到 [本步短期卡片](02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md)，保留原话、未知和历史场景，仅将当前调用场景接到 `run:97 → 98`，与父卡采用同一工作目录示例。
- scope、`BaseHarness.run`、步骤入口与 `02` 索引直接链接本步副本；`03` 与旧步骤不改写。本次调用定位依据固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `harness/common.py:81–104` 与 `sandbox.py:390–399`，两份源码工作区无改动；没有运行远端命令。
- 通用约定补入现有记忆 skill 与工作流：`02` 收录本步需要的新旧函数，纯调取不算新认识，不递归复制全部依赖；下一步仍按源码路径与符号合并 `03 + 02`。

这次反馈确定的是取用方式，不表示新增了函数机制理解或读完 Step 7。详细规则与理由见[认知制度讨论](../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#reactivate-prior-function-memory)。

<a id="harness-run-file-and-symbol"></a>

## 12. 2026-10-23：在 scope 中同时标明文件与方法

用户指出只写方法名不便对应到源码文件：

> 看一下这里的scope吧 这里难道不是common的harness。run吗？
> 为什么这里写的是baseharness.run
> 我觉得是否适合在scope写一下这里的是common.py里的baseharness.run？

- 源码定位：`slime/agent/harness/common.py:57` 定义 `BaseHarness`，其中 `81–104` 行定义 `run`；`harness/claude_code.py:15` 的 `ClaudeCodeHarness` 继承该类，并沿用其 `run`。固定提交仍为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 助手澄清：文件名、类名与方法名分别是 `common.py`、`BaseHarness`、`run`；调用处的 `HARNESS_CLS().run(...)` 在当前场景进入这个共同实现。
- 已在 [scope](01-scope.md) 的指挥官入口、局部骨架及导航表中同时标出 `common.py` 与 `BaseHarness.run`。其余阅读范围、函数卡片及当前进度保留；此处记录定位说明的改进，不增加个人掌握结论。

<a id="launch-restatement-and-http-entry"></a>

## 13. 2026-10-23：启动链复述，以及 Request 怎样进入 Adapter

用户完成本轮启动链复述，并指出接收端仍有缺口。以下保留完整表述，未将助手校准混入引文：

> 好的我觉得我大概读懂了这里的一系列的代码了
> 但是我觉得需要复述一下
> 一开始的ensure agent suer部分是在准备sandbox还有workdir
> 然后第一个ensure agent 部分就是借助目前已经有的这个sandbox来处理的内容
> 并且准备agent账号以目录归属git设置的一系列基础造作
> 然后进入到西面的这个harness context
> 纯粹是把之前散落的上下文捡起来
> 然后是这里的write config
> 这里的write config的内容更多的是吧这里的claude code harness 的cli部分写清楚这里的配置
> 修改本身的cli的部分
> 这里修改的claude本身这里不需要再询问能够自动执行
> 修改本地的一系列配置到这里的settings里面
> 然后再考虑的是这里的launch and wait的部分
>
> 这里通过cmd启动
> 除此之外是让启动的这个claude自动读取之前写好的本地的config文件
> 以及这里的ctx这里都已经事先储存好的
>
> 到这里都是准备工作还没有执行
>
>
> 然后再推进到这里的run agent
> run agent部分的内容我可以理解为我在做的事情是几个部分
> 1.首先是准备元数据的目录什么的
> 2.然后是具体的运行
> 2.1具体运行部分所需要做的内容
> 2.2第二是 脱机执行和幂等保护
> 2.3 第三各是轮训marker与防闲置gc的设定
>
> 这些都是比较细节的内容了
>
>
> 至此是当前step做的所有的内容了
>
> 但是我们之前是否没有考虑处理过
> 这里的adapter在拿到这里来自claude或者codex的请求的时候怎么转发给sglang的？
>
> run_turn里面有一个简单的拿到了请求之后具体怎么做的一个图但是没有写清楚adapter是怎么做到接受到这里的来自于claude或者codex本身发过来的请求的部分？
> 之前在第一部直接默认的是这里已经有了这个请求的body？

**助手核对**：

1. `ensure_agent_user` 使用已有 `sb` 与已存在的工作目录准备账号、目录归属与 Git 设置；`HarnessContext` 收拢本地运行参数。
2. `write_config` 在本地组装 JSON，但通过 `sb.exec` 写入远端沙箱的 `/home/agent/.claude.json` 与 `/home/agent/.claude/settings.json`。这里写配置文件，配合后续启动选项，不修改 CLI 程序代码。
3. `launch_and_wait:58–70` 构造 `cmd/env`；第 71 行委派 `run_agent` 并等待执行结束。此前的账号与配置准备也已在远端执行，不能将整段概括成“都尚未执行”。CLI 使用配置和环境，`ctx` 本身仍是本地 Python 对象。
4. `run_agent` 准备输出目录、指定执行用户并委派；脱机启动和启动防重在 `exec_and_wait`，marker 轮询在 `_await_done_marker`。用户已概括这些阶段，详细机制与清理边界仍保留未知。
5. Step 1 的 `_run_turn` 明确接收 `request`，第 325 行解析出 `body`；监听和路由也曾在旧 task flow 折叠区说明。因此当前缺口是把那些材料接回当前主线，不是补造一个额外转发函数。

**本次整理与接续**：

- 原话分段补入本步相应卡片，校准内容单独标记。启动链已有整体复述；配置位置、准备与执行边界的本次校准尚待反馈。
- 将[既有 _run_turn 卡片](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)从本步 `03` 完整调入 `02`，补清显式输入 `request` 与函数内变量 `body` 的区别，原版本、原话与未知保留。
- 在[现有通信参考](references/run-communication-path.md#adapter-request-entry)补出“创建应用并注册路由 → 开始监听 → CLI 请求到达 → aiohttp 调用处理器 → 解析 body → 另行请求 SGLang”，scope 链接本步卡片与该入口说明。
- 建议下一个最小观察点为 `AnthropicAdapter._register_routes:48–50`，看 URL 怎样绑定处理函数；`run_app_in_thread` 仅按需补监听前置。尚未新建这两张函数卡片，也未收束 Step 7 的 task flow。

**证据与边界**：固定源码为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，涉及 `harness/claude_code.py:44–71`、`harness/common.py:97–122`、`adapters/common.py:159–175、318–344、470–484`、`adapters/anthropic.py:48–53`、`adapters/openai.py:47–51`、`aiohttp_threaded.py:65–88` 与 `generate.py:137–171`。本日官方 main 为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，与固定阅读版不同，继续沿用原版本。源码工作区 `swe.py` 有原有改动，本次未修改源码；没有运行 CLI、沙箱或模型请求，也没有核查 CLI 内部 HTTP 客户端的实现。

<a id="close-launch-open-request-entry"></a>

## 14. 2026-10-23：先收拢启动链，再单独研究 HTTP 接收

用户提出：

> 我觉得我们是否适合先把之前的step007的部分先吧这里的task flow写完？
> 然后在step08这里把这个内容讲清楚呢？

**本次按此分工整理**：

- Step 7 的 [task flow](05-task-flow.md)收拢 `BaseHarness.run → launch_and_wait → run_agent → exec_and_wait`：如何准备并启动 CLI，如何把退出码带回 `generate`。
- [Step 8](../step-009-adapter-request-entry/01-scope.md)接续已明确的缺口：CLI 的 HTTP 请求如何被服务接收、按路由交给 `_run_turn`，再解析出 `body` 并接上已有处理链。
- scope 的现行停止位置随之收窄；[拆分前版本](references/scope-before-step-008.md)、既有原话、函数记录与通信参考保留。Step 8 的 `03` 合并本步 `03 + 02` 为 43 份记录，并把本步要用的旧卡调入其 `02`。
- 两步是阅读分工：接收请求发生在 CLI 运行、Harness 等待期间。不能把 Step 8 画成 CLI 完全退出之后才发生的代码。

**认识与证据状态**：本次确认的是整理与接续范围；前一节尚待反馈的校准继续保留。新步的监听、路由和请求解析尚待逐处带读；未据此登记为已掌握，也未新增真实远端运行。

<a id="execution-order-table"></a>

## 15. 2026-10-23：调用树不足以直接读出执行顺序

用户指出：

> 但是这里的
> 这个2
> 真的按照执行顺序写清楚的吗？
> 我总感觉这里的这个流程图感觉不是特别合适了？
>
> 至少这个第二个图

用户随后明确所指位置为：

> Step 7 task flow：第 2 节调用树

**助手核对与本次修改**：

- 原树的主要调用关系与正常路径先后顺序成立，但父函数、子函数和内部阶段混排，读者需要自行按深度遍历，并补出返回时机。
- 将 [task flow 第 2 节](05-task-flow.md#2-按执行顺序接起来)改为执行顺序表，逐行写“当前代码 → 完成什么 → 完成后去哪里”；随后单列退出码返回链。
- 重点标明 `launch_and_wait` 调用内继续进入 `run_agent` 与 `exec_and_wait`，以及启动操作返回与 CLI 整体结束的区别。`generate:205` 要等退出码逐层返回后，才会进入 213 行。
- 只修订第 2 节原调用树及其说明，保留四次交接解释、其余章节和函数记忆。Step 8 的范围与接续方向保持原状。
- 这是助手针对可读性的修订，尚未收到用户对新顺序表的阅读反馈；没有新增个人掌握记录或真实运行结果。

<details>
<summary>修改前的第 2 节调用树与说明</summary>

## 2. 已读代码怎样接起来

下面按正常完成路径整理。行号绑定本步固定版本；命令内容、重试和异常分支留在函数卡片中。`exec_and_wait` 的细节合并为一次“远端启动并等到结果”，避免主线再次陷入底层实现。

```text
generate.py:205  await HARNESS_CLS().run(...)
└─ harness/common.py:81–104  BaseHarness.run
   ├─ 97       ensure_agent_user(sb, workdir)
   ├─ 98–102   ctx = HarnessContext(...)
   ├─ 103      ClaudeCodeHarness.write_config(sb, ctx)
   └─ 104      ClaudeCodeHarness.launch_and_wait(...)
      ├─ claude_code.py:58–70  组成 cmd 与 env
      └─ 71                   await run_agent(...)
         ├─ common.py:109–110  准备 .harness 输出目录
         └─ 111–121           await exec_and_wait(...)
            ├─ sandbox.py:107–138  写启动脚本，经 sb.exec 启动远端 CLI
            └─ 139–145            等完成标记，取得退出码

CLI 结束 → exec_and_wait → run_agent → launch_and_wait → BaseHarness.run
        → generate.py:205 的 agent_exit_code
        → generate.py:213 的 swe.git_diff(...)
```


</details>

**静态依据**：固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `harness/common.py:97–122`、`harness/claude_code.py:44–71` 与 `sandbox.py:65–145`。其中 `sandbox.py:112` 将“执行 CLI 后写退出码”放入启动脚本，139 行才进入本地等待；本轮按源码核对时机，未执行远端任务。


<a id="task-flow-step-three-format"></a>

## 16. 2026-10-23：用已有整体复述，按 Step 003 格式整理任务总结

用户指出已经给出了 Step 7 的总结，并要求落实到本步：

> 我在刚才的描述里面已经给出step07的总结了 那么现在是否应该修改一下这里的007的部分了呢？

**本次依据**：沿用[第 13 节的完整复述](#launch-restatement-and-http-entry)，使用已确认的 [task-flow skill](../../../../../../../.agents/skills/repo-reading-task-flow/SKILL.md)与 Step 003 主 reference。没有再要求用户复述，也不将此次修改请求记成新的源码理解。

- [任务总结](05-task-flow.md)采用“前序输入 → 按执行顺序交接 → 结果与去向 → 收束及后续”的四部分结构。保留执行顺序表，将原来四段交接中的必要信息并入表格及结果说明，减少重复。
- 逐处链接函数/类卡片，保留具体实现、源码行号、返回位置；区分远端准备命令、CLI 启动操作返回和整次 CLI 退出。
- 用已有构造例说明退出码、远端配置、文件输出和工作区改动的去向；保持 CLI 输出文件与 manager 训练轨迹的区别。
- Step 8 已确认的 HTTP 接收问题保留为等待期间的交接；本轮没有展开新接收函数。scope、短期/长期卡片和 Step 8 内容保持原样。
- [修订前完整稿](references/task-flow-before-step-003-format.md)保留旧版本；第 15 节的修改记录也继续保留。配置位置、ctx 与 CLI 的关系以及执行边界仍采用先前的证据状态，没有代填为用户已确认。

**验证范围**：核对本地固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `generate.py`、`harness/common.py`、`harness/claude_code.py` 与 `sandbox.py`；这些文件没有工作区改动。本轮只修改阅读材料，未运行真实 CLI、沙箱或模型请求。


<a id="task-flow-visible-diagram"></a>

## 17. 2026-10-23：任务总结需要直接可见的关系图

用户指出上一版仍需要沿表格逐行拼出关系：

> 不对啊 这里没有对应的图啊
> 真的就按照这个顺序去读还是比较麻烦

**本次修正**：在 [task flow 第 2 节](05-task-flow.md#launch-flow-diagram)加入直接可见的文本流程图。①–③表示依次完成的准备，④–⑥明确逐层调用，⑥之后分成远端 CLI 运行与本地轮询两条线；完成标记将两条线接回⑧，再沿调用链返回退出码。Step 8 放在 CLI 运行期间的 HTTP 分支上。

原有源码对照表及其说明完整折叠保留，图下提供按节点编号直达函数/类卡片的链接。此处使用仓库已有的文本图形式，普通 Markdown 也可直接阅读，无需额外图形渲染器。其余三个正文部分、scope、各层记忆和 Step 8 保持原样。

这条反馈明确的是当前文档的展示需要，不将本次补图记成新的源码理解，也不自动改写其他步骤或通用 skill。图中的调用与行号沿用上一轮已核对的固定版本；本轮未运行真实沙箱或 CLI。


<a id="task-flow-call-hierarchy"></a>

## 18. 2026-10-23：以 run 的四个部分为主层，逐层展开子调用

用户明确图应先保留调用层级：

> 之前的wrokflow图应该是包含了这里的层级关系才对吧
> 也就是我知道我需要运行这里的run
> 主题有4个部分
> 但是每一个function 应该有接下去的调用我是这么理解的

**助手核对与修改**：`BaseHarness.run:97–104` 直接包含用户准备、构造上下文、写配置、启动并等待四个部分。此前主图按时间将下层调用继续编号为⑤–⑧，未直观保留这四个部分的归属；本次将[第 2 节](05-task-flow.md#launch-flow-diagram)改为调用层级树。

- ①–④为 `run` 的四个直接部分，缩进展示各部分内部的已读调用；`run_agent → exec_and_wait → _await_done_marker` 归入④。
- `sb.exec` 和 `sb.write_file` 挂在实际调用它们的函数下面；`HarnessContext` 标为对象构造，不虚构下一层调用。局部赋值、结果及返回用 `→` 旁注说明。
- 已有顺序表继续折叠保存，分支标记同步为①–④；保留源码位置和卡片链接。远端 CLI 的 HTTP 请求继续作为运行期间的交互说明，不伪装成 Python 直接调用。
- 本次只修订当前 task flow 的图与对应说明；其余正文、scope、函数卡片与 Step 8 保持原样。用户确认的是所需的层级关系与表达方式，不据此增加其他机制的掌握记录。

**静态依据**：沿用固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，核对 `harness/common.py:81–122`、`harness/claude_code.py:44–71`、`sandbox.py:65–79、107–145、390–399`。未运行远端命令。

<details>
<summary>被替换的时间顺序图：保留此前展示与修正来由</summary>

此前①–⑧表示依次展开的时间位置，没有直观表现 run 的四个直接部分；现行主图以上面的调用层级为准。

```text
generate.py:205  调用并等待 HARNESS_CLS().run(...)
       │
       ▼
BaseHarness.run                              [harness/common.py:81–104]
       │
       ① ensure_agent_user                  [run:97]
       │  已有沙箱 → agent 账号、目录归属与 Git 设置就绪
       ▼
       ② HarnessContext                     [run:98–102]
       │  散落的运行参数 → 本地 ctx
       ▼
       ③ ClaudeCodeHarness.write_config     [run:103 → claude_code.py:44–55]
       │  配置内容 → 远端 CLI 配置文件；完成后回到 run:104
       ▼
       ④ ClaudeCodeHarness.launch_and_wait  [run:104 → claude_code.py:58–71]
       │  prompt + ctx → cmd + env；随后调用并等待⑤
       ▼
       ⑤ run_agent                          [harness/common.py:109–122]
       │  准备 .harness 目录；指定 agent 用户，调用并等待⑥
       ▼
       ⑥ exec_and_wait                      [sandbox.py:107–138]
       │  写启动脚本，经 sb.exec 发出启动命令
       │
       ├──────► 远端执行沙箱
       │           CLI 开始运行，读取配置、参数与环境
       │           │
       │           ├─ 运行期间：HTTP ↔ Adapter（Step 8）
       │           │              取得模型回复，继续任务
       │           ▼
       │           CLI 退出 → 启动脚本写入完成标记与退出码
       │                                       │
       │  本地：启动操作返回，继续等待         │
       ▼                                       │
       ⑦ _await_done_marker                    │
          轮询完成标记 ◄───────────────────────┘
          [sandbox.py:139 → 65–79]
       │  读到退出码后返回 exec_and_wait
       ▼
       ⑧ exec_and_wait 返回 (exit_code, output) [sandbox.py:140–145]
       │
       ▼
run_agent:111 接住结果，只将 exit_code 从 122 行返回
       → launch_and_wait:71
       → BaseHarness.run:104
       → generate.py:205 接住 agent_exit_code
       → generate.py:213 开始 swe.git_diff(...)
```

</details>


<a id="harness-scope-refresh-18868a79"></a>

## 19. 2026-10-24：按当前版本更新启动与等待的 scope

用户在 scope 审阅后确认：

> 好的那么现在更新一下现在的这个scope吧

本轮只更新 scope 与入口说明，沿用前几步已确认的格式：阅读目标和指挥官各三点，保留完整任务骨架、必要输入、局部四项主体及阅读导航，版本说明置于末尾。更新前的 scope 完整保存在 [2f231865 快照](references/scope-at-2f231865.md)，更早的宽范围快照继续保留。

本次核对与调整：

- 入口对齐 `_generate:287` 的 `harness.run`，指挥官仍为 `BaseHarness.run:81–104`；整体骨架接入 `baseline`、当前 Harness 实例与统计收集。
- 输入分为执行环境、请求去向、任务与预算。`baseline` 留在外层供后续比较，未传入 Harness；`workdir`、`session_id`、`adapter_url` 进入本地 `HarnessContext`。
- 对比 `2f231865` 与 `18868a79`，`BaseHarness.run`、`run_agent` 和 `exec_and_wait` 的函数体 AST 未变；`write_config` 增加 hook 配置，`launch_and_wait` 增加统计初始化、PID 与等待包装，`_await_done_marker` 改为直接读完成文件。
- 导航保留先定位四项主体、重点读命令与环境的顺序，前序已校准的用户准备和 hook 记录按需回查。HTTP 接收仍交给 Step 009；等待超时返回与所有后台活动停止分开说明。

当前固定源码为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。本轮未修改函数卡、类卡、长期继承或旧 task flow，没有新建函数记忆、运行 CLI 或增加掌握结论。后续从新 scope 继续，逐项校准旧材料。

验证：42 处本地链接有效，旧 scope 全文完整保留；前两节各三点、局部四项主体和返回关系已核对。Hugo 渲染确认两份骨架、导航表及既有锚点正常，版本说明位于末尾，差异空白检查通过。


<a id="cli-pid-and-compaction-question"></a>

## 20. 2026-10-24：复用新版启动卡，澄清 PID 与压缩事件

用户询问：

> 好的这里不是简单就是 真实的配置一下这里的claude 通过cli的方式?
> 还有就是如果压缩的话这里到底是怎么处理的?
> 还有什么需要特别记住的吗?
> 我不是特别理解
> 这里的保存pid又是为了做什么呢?
> 保存版本信息?
> 还是什么

本轮沿 `launch_and_wait:86–109`、`write_config:57–84` 和 `compaction.py::run_hook:23–68` 核对。启动函数组装本次 CLI 的命令、环境与统计初始化包装，交给下层执行；配置文件和 hook 注册在前面的 write_config 完成。

PID 是操作系统的进程编号，保存在 `.harness/cli.pid`，用于定位本次运行的 CLI。实际压缩由 Claude CLI 处理；注册的 PreCompact/PostCompact 事件调用 run_hook，更新 `.harness/compaction.json`。若启用次数限制，下一次压缩前发现预算已用完，hook 读取 PID、核验祖先关系后向该 CLI 发 SIGTERM。Shell 保留 `wait`，使 CLI 退出后的状态继续交给下层启动脚本写入完成标记。记录的 PID 不是软件版本或 Git 快照。

本轮将 Step 002 的完整新版 `launch_and_wait` 卡片调入本步，重算链接，保留源卡的原话、未知与认识日期；本步原卡完整归档到 [历史稿](references/launch-and-wait-before-current-reuse.md)。在当前卡片中补充上述协作关系及本次问题，不重新编写已经清楚的 cmd/env 主线。其他函数卡尚未因此同步替换，长期继承与旧 task flow 未改变。

网页在 [3.1 新版接续](../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#launch-pid-compaction-18868a79)保存对应解释。此次只静态核对，没有启动真实 CLI、触发压缩或发送信号；新解释尚待用户反馈，Step 008 未收束。

验证：原 Step 008 卡片完整归档，原认识日期保留，68 处相关本地链接有效；20 项现有章节检查通过。新增网页段落在维护正文与发布正文中一致，本地页面返回 200，PID 片段、事件表与折叠来源正常渲染。


<a id="launch-main-diagram-restored"></a>

## 21. 2026-10-24：恢复大图作为 launch_and_wait 的主读入口

用户对上一次呈现反馈：

> 不对啊 之前的卡片我觉得很好啊
> 特别是那个比较大的图
> 还是你觉得这里的这个图不应该放在这里? 我不是特别理解了

助手核对后说明：旧图适合当前 Step 008 的整体启动与通信问题。此前复用 Step 002 的统计视角，将大图放入历史折叠区，不适合作为当前主读布局；大图应保留在主读位置，更新源码与必要的新动作。用户随后要求：

> 好的那么请你给出这里的比较合适的解释吧
> 正常构成这里的这个launch and wait 部分的内容吧

本轮恢复主图，保留“本地组装与委派 → 执行沙箱中的 CLI → Adapter/SGLang 服务交互”的整体关系。双线框限定本函数直接职责，下层执行函数单独标出，模型请求发生在 CLI 运行期间；三段源码按 cmd/env、启动控制包装、委派并等待排列。PID 与压缩事件留在第 2 段附近，详细分支折叠，避免它取代整体模型。

当前函数体仍绑定 `18868a79`，24 行源码的全部有效语句由三段代码完整覆盖。旧大图和原话保留在此前档案，本轮整理前的完整卡片另存 [历史版本](references/launch-and-wait-before-main-diagram-restoration.md)。本轮仅调整讲解与呈现，不更改 Slime 源码或个人认识日期，不将版式反馈记成理解确认。

相同主图和讲解同步到 [Hugo 对应段落](../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#launch-and-wait-mainline-18868a79)；此前以 PID 为主的网页段落完整保存在 [网页历史稿](references/launch-explanation-before-main-diagram.md)。其他函数卡、长期继承和旧 task flow 保留。

验证：三个代码段覆盖当前函数全部有效语句，AST 一致；69 处相关本地链接有效。20 项现有章节检查通过，卡片与本地网页均确认大图位于默认可见区域，未被收入历史折叠；维护正文与发布正文内容一致，差异空白检查通过。


<a id="launch-three-part-model"></a>

## 22. 2026-10-24：采用三段式 launch_and_wait 心智模型

用户明确指定：

> 1. 组装启动材料：把 prompt 和 ctx 变成 cmd、env。
> 2. 补充运行控制：在命令中安排统计初始化、启动 CLI、保存 PID 和等待。
> 3. 委派并等待：交给 run_agent，由下层在沙箱执行，最后取回整数结果
>
> 按照这个构建心智模型吧

已将这三点写入当前函数卡的“建议构建的心智模型”，并在个人表述处保留用户采用该模型的原话，更新认识日期和索引。大图、三段源码、PID 的局部补充、历史与未知保留，网页开头同步同一组织方式。

此次确认的是这三项职责的模型，不据此将 PID、压缩、Shell 等具体机制全部记为已掌握；源码与运行状态没有变化。


<a id="exec-wait-read-file-update"></a>

## 23. 2026-10-24：仅更新 exec_and_wait 的完成文件读取部分

用户确认局部更新：

> 好的那么局部更新一下吧 不需要更新全部内容

已保留原图的位置与整体结构，仅将轮询箭头从 shell 查询改为 `sb.read_file`，同步缺失／空内容继续等待、读到整数后返回的表示。第 3 段替换为当前 `_await_done_marker` 的读取方式，保留每 5 秒检查、返回退出码或超时码的流程；同时校准相关源码行号。

原来的启动、清理旧状态、后台执行及输出处理继续保留。轮询说明中“无惧断网、绝不丢失”的断言改为实际边界：读取错误仍可能传播，超时返回未在此终止后台进程。完整旧卡归档到 [更新前记录](references/exec-and-wait-before-read-file-update.md)，原话与认识日期保留。

这次是源码与材料的局部同步，未改动其他函数实现、运行验证或长期继承，也不记为新的个人理解。

验证：除配套轮询函数外，其余 Python 代码块保持原样；新轮询代码与当前源码 AST 一致。原话、认识日期和图的行数及主要位置保留，旧卡完整归档，24 处本地链接有效；Hugo 渲染确认主图仍默认可见、箭头已改为文件读取，差异空白检查通过。


<a id="harness-execution-closure-20261025"></a>

## 24. 2026-10-25：三阶段职责反馈与本步收束

用户完整反馈：

> 好的 我大概明白了
> 职责还是没有变化
> 还是这三个部分对吗?
> 我其实不是特别清楚了
> 感觉绝大多数内容都是在除了sandbox 内部到底需压迫执行什么
> 当然这里有你说的这几个组装launcher 还有脱机执行和迷瞪保护
> 还有轮训完成文件等一系列内容
> 这些其实我差不多都明白了
> 总的来说就是脱离了主机 让起能够在sandbox中自动运行直到结束的部分对吧
> 除此之外之外这一个step还有什么需要了解和看的吗?

本轮按当前源码核对：这三部分对应 exec_and_wait 的 launcher 组装、后台启动与防重复、完成文件轮询。执行器只处理上游传入的命令和结果回传，命令本身要完成的任务由上游决定。

“脱离主机”需要补准：后台脚本可以在沙箱里继续运行，Slime 主机仍在读取完成文件并等待结果；脱机不表示主机与流程失去关系。正常读到标记后，二元组经 run_agent 取出整数，再由 launch_and_wait、BaseHarness.run 交回 _generate。达到等待预算时返回超时码，不保证后台进程已经停止。

对照 scope，启动材料、实际执行、等待和返回已有完整主线，本步可以按这个层次收束，不必再扩展一组新函数。用户大致理解和仍不确定的表述均保留；这不是全部 Shell、网络、进程清理机制均已掌握的声明。

[task flow](05-task-flow.md)已按 18868a79 更新，保留原有四项主体与下层调用关系；[旧总结](references/task-flow-at-2f231865.md)完整归档。其他旧函数卡、长期继承不在本轮扩写，也没有新增实际 CLI 或远端运行。

下一候选是 Step 009 的 HTTP 接收入口：运行中的 CLI 请求怎样抵达路由与 _run_turn。此关系发生在当前步骤等待期间，后续具体范围另行接续。

验证：84 处相关本地链接有效，旧 task flow 全文保留；新总结的四部分、调用层级、结果表和既有锚点经 Hugo 渲染检查正常。本地网页返回 200，并已显示主机继续等待的说明；差异空白检查通过。
