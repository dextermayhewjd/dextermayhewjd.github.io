---
title: "沿 generate 走完 4.1：一次 Agent 任务"
linkTitle: "沿 generate 走完一次任务"
description: "按完整任务顺序进入 Harness、Sandbox、Adapter 与轨迹，读清职责后回到主线。"
weight: 1
ShowToc: true
---

<!-- Derived from slime_photo/code-reading/chapters/01-task-execution/walkthrough.md. -->

本轮先完成 **Agent Rollout Adapters and Harnesses**：以 `generate()` 为书签，沿一份任务进入各组件，读清职责和输入输出后返回主线。第一遍走通正常路径，再补一条失败清理路径；实现细节按问题继续深入。

源码固定在 `22a89f96835969a47055a659c588f46151f8b07a`。本篇选择 **Claude Code Harness / Anthropic Adapter**，与已有 4.1 图文一致；Codex/OpenAI 留作完整链读通后的实现对照。本轮已核对：这些核心源码与旧 `8c17b676` 资料版本没有差异，原有动作讲解可以继续使用。

## 为什么从 generate 进入

CodeWiki 原图展示组件关系；本篇按任务执行读它们的组装和交接。`_AdapterService` 在示例的 `generate.py` 中，负责准备图内的 Adapter/模型连接和 HTTP 服务。它不是单轮请求处理，也不是 Harness 的启动逻辑。先扫 generate 骨架，到 state 初始化处下钻，再回外层继续；上游训练、调度和模型服务部署先视为已提供的前提。

动作 4 的前置阅读包括调用方的 Adapter、任务、Session、环境和题目准备；Launch Agent 本体继续进入 run 内部的用户、配置、命令与启动。两层串起来阅读，职责仍各自保留。

## 先把整体顺序看清

![一次 Agent 任务的生命周期](/images/slime-lifecycle/overview.svg)

```text
generate()
  prepare adapter + task metadata + session
  with agent sandbox:
    prepare workspace
    await Harness.run()
      CLI runs and requests the model
        HTTP -> translate -> generate -> reply + record
        tools -> another request -> ...
    collect diff
  evaluate diff in a fresh sandbox
  return eval result OR export training samples
  finally: drop session
```

`generate()` 组织的是整次任务，`_run_turn()` 组织一次模型请求。**外层等待 Harness 时，CLI 在独立环境中工作，Adapter 的 HTTP 服务也在接收请求。** CLI 内的工具调用与模型请求可能重复多轮；等 CLI 整体结束，外层才继续收集 diff。Sandbox 的操作贯穿安装、题目准备、CLI 运行与 diff 收集。

## 一份用于贯穿阅读的任务

下面只是假设的阅读参数，不是运行记录：规范化任务信息包含 `instance_id=demo`、`image=demo-image`、`workdir=/workspace/demo`，题目是“修复一个函数并通过测试”。样本 `index=0`、`group_index=0`，没有已有 Session；代码据此构造 `cagent-demo-0-0`。假设 Adapter 地址为 `http://192.0.2.10:18001`，SGLang 地址为 `http://192.0.2.20:30000`。

CLI 使用 Adapter 地址；Adapter 使用 SGLang 地址。题目、环境、会话、生成结果、diff 与 reward 会在不同层交接，不必一次理解所有字段。

## 连续阅读顺序

| 步骤 | 主线停在哪里 | 下钻职责 | 看完回到哪里 | 原有图文 |
| --- | --- | --- | --- | --- |
| 1 | generate 准备任务与 Session | 模型入口、任务元数据、会话注册 | generate 的任务预算/环境入口 | Launch Agent 的参数来源 |
| 2 | 进入 Agent 沙箱上下文 | 创建环境、安装 CLI、准备题目和工作区 | generate 的 Harness.run 调用 | Manage Sandbox |
| 3 | await Harness.run，暂时停在等待 | 用户与配置、CLI 命令/环境、后台进程与退出标记 | 留在 CLI 运行期间，转看请求端 | Launch Agent → Exec Commands |
| 4 | 外层仍等待 CLI | CLI 回连 Adapter、HTTP 路由、Session 身份 | _run_turn 的输入处理 | Make API Calls |
| 5 | _run_turn 处理模型输入 | 协议转换、模板 token、采样预算、SGLang 生成 | _run_turn 接回 TurnRecord | Translate & Forward → Generate Tokens |
| 6 | _run_turn 接回生成记录 | 解码、解析、协议响应、本轮轨迹 | HTTP 结果回 CLI，重复 4–6 或结束 | 3.5 完成一次模型请求 |
| 7 | CLI 结束后回 generate | 收集 diff、退出工作环境、独立评分 | generate 的模式分支 | 7.1 任务组装，先只看收尾 |
| 8 | generate 返回结果并退出 | 评测结果或训练轨迹导出、Session 清理 | generate 结束，完成一次任务 | 会话结束与轨迹导出 |

原图动作编号用于定位职责。沿上述主线读：**任务准备 → 5 创建与准备环境 → 4 组织启动（继续使用 5 的环境操作）→ 6 CLI 执行与等待 → 7 回连 → 2/3/3.5 请求循环 → 回到 generate 收尾**。步骤 7、8 只补齐 4.1 组件如何接回外层，不在这里展开全部 SWE 数据集与训练框架。

## 1．准备 Adapter、任务和 Session

**从主线进入：** [generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182)（`examples/coding_agent_rl/generate.py:182`） 的第 184 行调用 [_AdapterService](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L137)（`examples/coding_agent_rl/generate.py:137`）；随后 [get_metadata](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L77)（`examples/coding_agent_rl/swe.py:77`） 从样本中整理任务信息。

`_AdapterService` 准备 tokenizer 与 Adapter，并通过 [run_app_in_thread](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/aiohttp_threaded.py#L46)（`slime/agent/aiohttp_threaded.py:46`） 在后台线程的事件循环中运行 HTTP 服务，得到 `adapter_url`。因此后面等待 CLI 时，模型请求仍有处理入口。第一遍定位启动与运行位置即可，线程实现无需逐行展开。

任务信息检查后，[_session_id](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L308)（`examples/coding_agent_rl/generate.py:308`） 决定 sid，[BaseAdapter.open_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L210)（`slime/agent/adapters/common.py:210`） 注册默认采样参数与上下文预算：

```python
    session_id = base_sample.session_id = _session_id(base_sample, instance_id)
    state.adapter.open_session(
        session_id,
        sampling_defaults=sampling_params,
        max_context_tokens=state.max_context_len,
    )
```


**交接：** `args/base_sample/sampling_params` → 可用 Adapter 地址、规范化 `md`、sid 与 Session 默认设置。**返回主线：** `generate:202–203`，准备进入任务预算和沙箱上下文。

第一遍停止标准：知道模型入口和会话身份从哪来，能说明为什么一次模型请求可以找到这次任务。这里的准备在外层 `try` 前；不要把它的所有失败都当作已进入后面的统一清理分支。

## 2．创建执行环境，准备工作区

**从主线进入：** `generate:203` → [boot_agent_sandbox](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L96)（`examples/coding_agent_rl/generate.py:96`）；环境交出后，`generate:204` → [prepare_workspace](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L177)（`examples/coding_agent_rl/swe.py:177`）。

```python
            async with boot_agent_sandbox(md["image"], instance_id) as sb:
                await swe.prepare_workspace(sb, md["workdir"], md)
                agent_exit_code = await HARNESS_CLS().run(
                    sb,
                    workdir=md["workdir"],
                    session_id=session_id,
                    adapter_url=state.adapter_url,
                    time_budget_sec=CONFIG.agent_time_budget_sec,
                    prompt=swe.SWE_PROMPT,
                )
                diff_text = await swe.git_diff(sb, md["workdir"])
```


先看 [Sandbox](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L28)（`slime/agent/sandbox.py:28`） 的命令、文件和上下文操作合同，再看 [E2BSandbox.__aenter__](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L281)（`slime/agent/sandbox.py:281`）。构造包装对象尚未创建远端环境；`__aenter__` 才执行创建。随后安装所选 Harness 的 CLI。`prepare_workspace` 准备用户权限、数据集需要的命令和 `PROBLEM_STATEMENT.md`。

**交接：** 镜像、目录、题目与 `sb` → 已有工具链和题目材料的工作区。**返回主线：** `generate:205` 的 `await HARNESS_CLS().run(...)`。

本步第一遍只走创建、安装、文件/命令操作与退出位置；启动重试和 E2B SDK 内部后读。这个 `async with` 一直包住后面的 Agent 运行和 diff 收集。

## 3．Harness 配置并启动 CLI，然后等待

**从主线进入：** `generate:205` → [BaseHarness.run](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L81)（`slime/agent/harness/common.py:81`）。它先确保 Agent 用户，建立 `HarnessContext`，再委派所选子类的配置与启动。

进入 [ClaudeCodeHarness.write_config](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/claude_code.py#L44)（`slime/agent/harness/claude_code.py:44`） 看 CLI 配置，进入 [ClaudeCodeHarness.launch_and_wait](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/claude_code.py#L57)（`slime/agent/harness/claude_code.py:57`） 看命令与模型地址/会话身份：

```python
        env = {
            "ANTHROPIC_BASE_URL": ctx.adapter_url,
            "ANTHROPIC_AUTH_TOKEN": ctx.session_id,
            "ANTHROPIC_MODEL": ctx.model_label,
            **self.static_env,
        }
        extra_envs = os.environ.get(self.extra_envs_env, "").strip()
        if extra_envs:
            env.update(json.loads(extra_envs))
        return await run_agent(sb, workdir=ctx.workdir, start_cmd=cmd, env=env, time_budget_sec=time_budget_sec)
```


再进入 [run_agent](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/harness/common.py#L107)（`slime/agent/harness/common.py:107`） → [exec_and_wait](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L82)（`slime/agent/sandbox.py:82`） → [_await_done_marker](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/sandbox.py#L65)（`slime/agent/sandbox.py:65`）：命令在环境中后台启动，输出写入文件，完成时写退出标记；等待端读取标记得到退出码。模型 token/logprob 的训练轨迹由 Adapter 保存，CLI 输出文件不代替它。

**交接：** `sb/workdir/sid/adapter_url/prompt/budget` → CLI 配置、命令、环境变量、进程与完成标记。最终输出是 `exit_code`。

**此时先停在等待处。** `Harness.run()` 尚未返回，`generate()` 尚未到 diff。为了理解等待期间发生什么，接下来进入 CLI 发起的模型请求。配套：[动作 4](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/4-launch-agent/)、[动作 5](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/5-manage-sandbox/)、[动作 6](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/6-exec-commands/)。

## 4．CLI 的请求进入 Adapter，找回 Session

<a id="harness-to-adapter"></a>
<a id="run-execution-order"></a>

### 从 run 开始：一句执行完，下一句去哪里

这次沿 Claude Code / Anthropic 分支，只看正常执行路径。起点是 `generate` 已经拿到沙箱 `sb`、工作目录、任务提示和 Adapter 地址，开始等待 `HARNESS_CLS().run(...)`。Adapter 的 HTTP 服务此时也已经启动。

`HARNESS_CLS` 在这个分支是 `ClaudeCodeHarness`，它继承了 `BaseHarness.run`。因此下面进入的是 `BaseHarness.run` 的函数体，`self` 仍是这个 Claude Code Harness 对象。

**1．先在 run 里面，按顺序做四件事。**

下面是函数体的源码，加了阅读注释：

```python
await _sandbox.ensure_agent_user(sb, workdir)  # ① 准备 agent 用户及目录权限；完成后继续
ctx = HarnessContext(                       # ② 把下面三个已有值放进一个上下文对象
    workdir=workdir,
    session_id=session_id,
    adapter_url=adapter_url,
)
await self.write_config(sb, ctx)             # ③ 写 Claude 的配置；完成后回到这里
return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)  # ④ 进入启动和等待
```

① 先处理运行用户。② 只是整理数据：后面需要地址时，从 `ctx.adapter_url` 取。③ 进入 `ClaudeCodeHarness.write_config`，将跳过初次引导、接受权限模式所需的设置写入沙箱，写完回到 `run`。④ 才进入 `ClaudeCodeHarness.launch_and_wait`。

**到④时，run 还没有返回。** `return await ...` 要先等右边完成、拿到结果，再把结果返回给 `generate`。接下来跟进右边的函数。

**2．进入 launch_and_wait：准备要启动的程序、任务和环境。**

下面从实际实现中裁剪，只保留本次需要的字段；其他环境变量及额外参数处理省略：

```python
cmd = f"/usr/local/bin/claude -p {shlex.quote(prompt)} {self.launch_flags}"  # 要执行的命令
env = {
    "ANTHROPIC_BASE_URL": ctx.adapter_url,     # Claude 向这个 API 地址请求模型
    "ANTHROPIC_AUTH_TOKEN": ctx.session_id,    # 本次会话凭据
}
return await run_agent(                      # 交给下一层执行，并等待它的结果
    sb, workdir=ctx.workdir, start_cmd=cmd, env=env, time_budget_sec=time_budget_sec
)
```

这里的 `/usr/local/bin/claude` 是已经安装在沙箱中的 Claude Code 命令行程序；`-p` 后面是任务提示。它相当于接下来要在沙箱的终端里执行的一条命令。

**写出 cmd 字符串、构造 env 字典时，Claude 还没有启动。** `launch_and_wait` 随后调用 `run_agent`，自己等着它返回。

**3．进入 run_agent，再进入 exec_and_wait：真正把程序启动起来。**

`run_agent` 先准备 `.harness` 输出目录，然后调用 `exec_and_wait`。这一层把 `start_cmd` 原样作为 `cmd` 传下去，也传下去环境变量和工作目录。

`exec_and_wait` 接着按顺序：

1. 把这条 Claude 命令写进一个沙箱内的启动脚本；脚本在命令退出后，会把退出码写入完成标记文件。
2. 调用 `sb.exec(...)`，在沙箱后台启动这个脚本；脚本开始执行其中的 Claude 命令。
3. 启动命令返回后，进入 `_await_done_marker`，反复检查完成标记，等待 Claude 这次运行结束。

第 2 项对应源码中的这次调用，保留实际参数与命令：

```python
await sb.exec(
    f"chmod +x {launcher}; "
    f"mkdir {lock_dir} 2>/dev/null || exit 0; "
    f"setsid bash {launcher} < /dev/null > {out_file} 2>&1 &",  # 在后台执行启动脚本
    user=user,
    env=env,                # 前面准备的 API 地址在这里交给所启动的程序
    timeout=30,
    check=True,
    idempotent=True,
)
exit_code = await _await_done_marker(        # 启动成功后，继续等整条命令退出
    sb, done_file, user=user, time_budget_sec=time_budget_sec
)
```

`sb` 是操作沙箱的接口，`sb.exec` 负责让沙箱执行命令。这里需要分清两个时刻：**后台启动命令返回了，Claude 程序还在运行。** 所以 `exec_and_wait` 还要继续等退出标记，上层的 `run_agent`、`launch_and_wait`、`run` 也都还没完成。

<a id="http-request-order"></a>

**4．现在停住 Python 主线，看看同时运行的 Claude 在做什么。**

这时 Claude 已经拿到了任务提示、工作目录和环境变量。它运行到需要模型回复的地方，会使用自己内部的 HTTP 客户端向 `ANTHROPIC_BASE_URL` 指定的地址发送模型请求，路径是 `/v1/messages`。这个地址正是前面传下来的 Adapter 地址。

所以，“下一步发送 HTTP”发生在**已经启动的 Claude 程序内部**。Slime 这边仍在等待它退出。CLI 内部构造请求、调用 HTTP 客户端的具体函数不在上述 Python 源码里；本步没有检查对应安装包，不能补写一个虚构的发送函数。

Claude Code 的[环境变量文档](https://code.claude.com/docs/en/env-vars)说明了 API 地址的配置，[网关协议文档](https://code.claude.com/docs/en/llm-gateway-protocol#api-formats)说明了 `/v1/messages` 接口；[`-p` 参数文档](https://code.claude.com/docs/en/cli-reference)说明了非交互运行方式。这里用这些接口说明连接外部程序的行为，不把它当作本次实际运行日志。

**5．Adapter 收到这个 HTTP 请求，才进入 _run_turn。**

Adapter 启动时已经执行过下面的路由注册：

```python
app.router.add_post("/v1/messages", self._run_turn)  # 收到此路径的 POST 时，交给这个处理器
```

注册只是先记下处理规则。现在请求到达，Web 服务按规则执行 `self._run_turn(request)`，实际实现来自 `BaseAdapter`。其中：

```python
body = await request.json()  # 从收到的 HTTP 请求中读取 JSON 数据
```

后面才会走到已有记录中的 `self._translate(body)`。它的输入来自收到的请求。

在 Adapter 处理这次请求时，三边的状态是：

| 执行位置 | 此刻在做什么 |
| --- | --- |
| Slime 的 `run` 调用这一侧 | 通过下层等待逻辑，等 Claude 整次运行结束 |
| 沙箱里的 Claude 程序 | 等这一轮模型请求的 HTTP 响应，收到后继续任务 |
| Adapter 服务 | 执行 `_run_turn`，处理这一个模型请求 |

Adapter 服务运行在单独的服务线程，能在主线等待期间处理请求。**收到一次 HTTP 响应，只让 Claude 继续运行；不会让 run 立刻结束。** Claude 后续需要模型回复时，还可以再次请求 Adapter。

**6．等 Claude 整体退出，才沿原来的调用层层返回。**

正常结束时，启动脚本写下退出码，`_await_done_marker` 读到标记；`exec_and_wait` 返回退出码和输出，`run_agent` 取出退出码，再经 `launch_and_wait`、`run` 返回给 `generate`：

```python
agent_exit_code = await HARNESS_CLS().run(...)  # 到这时，这一行才拿到退出码；调用参数省略
diff_text = await swe.git_diff(...)            # generate 然后继续下一句；调用参数省略
```

可以沿这个具体过程回看：`run` 准备用户和配置，逐层调用到沙箱命令启动；Claude 在沙箱里执行任务并请求模型；Adapter 收到请求后处理；Claude 整体退出后，`run` 才交回结果。当前只展开到 HTTP 处理入口与返回方向，模型生成和 CLI 工具循环仍留待对应问题。


<a id="call-sites-and-implementations"></a>
<a id="source-jump-map"></a>

### 源码导航：这一行调用谁，读完回哪里

**现在先打开 `slime/agent/harness/common.py:97`，看 `BaseHarness.run` 的函数体。** 定义从第 81 行开始。下面区分 `harness/common.py` 和 `adapters/common.py`，不把它们都简称为 `common.py`。

本篇沿用 Claude Code 分支。[`generate.py:46、52`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L45)选出的配对是 **`ClaudeCodeHarness` + `AnthropicAdapter`**：

- **启动端：** `ClaudeCodeHarness` 继承 `BaseHarness.run`，所以 `run` 要看 `harness/common.py`；它自己实现的 `write_config` 和 `launch_and_wait` 则在 `harness/claude_code.py`。
- **接收端：** `AnthropicAdapter` 在 `adapters/anthropic.py` 注册 HTTP 路由；它继承的 `_run_turn` 在 `adapters/common.py`。这里的 Anthropic 是 Adapter 的协议实现。

#### 启动端：顺着调用行走

下面各路径相对于 `slime/agent/`。每个框列出实际执行的函数及阅读范围，每条箭头标出调用语句的位置。行号按固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 核对。

```text
外层入口：examples/coding_agent_rl/generate.py:205
agent_exit_code = await HARNESS_CLS().run(...)
                  │
                  ▼
A  harness/common.py:81–104
   BaseHarness.run
   97–103：准备运行用户、上下文和配置
   104：return await self.launch_and_wait(...)
                  │ 第 104 行调用 B
                  ▼
B  harness/claude_code.py:57–71
   ClaudeCodeHarness.launch_and_wait
   58–70：准备 Claude 命令、任务提示和环境变量
   71：return await run_agent(...)
                  │ 第 71 行调用 C
                  ▼
C  harness/common.py:107–122
   run_agent
   109–110：准备输出目录
   111–121：exit_code, _ = await exec_and_wait(...)
                  │ 第 111 行开始调用 D
                  ▼
D  sandbox.py:82–145
   exec_and_wait
   107–113：写入启动脚本
   129–138：调用 sb.exec，后台启动脚本中的 Claude 命令
   139：等待 _await_done_marker（定义在 65–79）
                  │
                  └─ Claude 已运行；A、B、C 仍在等结果
```

代码入口：[A · run](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L97) · [B · launch_and_wait](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L57) · [C · run_agent](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L107) · [D · exec_and_wait](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L107)。

`run` 前半段的小调用先完成，再进入上面的 B：

| 当前语句 | 实际读取位置 | 做什么，完成后回哪里 |
| --- | --- | --- |
| `harness/common.py:97` 的 `ensure_agent_user` | `sandbox.py:390–399` | 准备 agent 用户、目录权限与 Git 设置；回来继续第 98 行 |
| `harness/common.py:98–102` 的 `HarnessContext(...)` | 字段定义在 `harness/common.py:43–54` | 包装工作目录、会话和 Adapter 地址；继续第 103 行 |
| `harness/common.py:103` 的 `self.write_config(...)` | `harness/claude_code.py:44–55` | 写 Claude 启动配置；回来继续第 104 行 |

#### 接收端：这里通过 HTTP 接上

```text
沙箱中的 Claude CLI（外部安装包）
   请求地址来自 harness/claude_code.py:63
                  │ HTTP POST /v1/messages
                  ▼
已启动的 Adapter 服务
   按 adapters/anthropic.py:49 预先登记的路由分派
                  │ 路由绑定的是 self._run_turn
                  ▼
adapters/common.py:318  BaseAdapter._run_turn
   325：body = await request.json()
   341：self._translate(body)  ← 已有函数记忆的接续位置
```

[`adapters/anthropic.py:49`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L49) 是提前执行的路由注册。请求到达时，服务使用这条规则进入 [`adapters/common.py:318`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L318)。它不是从 `exec_and_wait` 直接调用过来的。

CLI 内部发送 HTTP 的函数尚未检查，所以在图上标为外部程序；`sb.exec` 的具体 Sandbox 后端实现也未在本步展开。图只把已经核对的连接接起来。

#### 嵌套时保留返回位置

每次只沿当前的一条箭头读，并保留“从哪一行进来、这段要看什么、读到哪一行、完成后回哪里”。例如第一跳：

| 当前这一跳 | 具体位置与问题 |
| --- | --- |
| 从哪里进来 | `harness/common.py:104` 的 `self.launch_and_wait(...)` |
| 打开哪里 | `harness/claude_code.py:57–71` |
| 这段看什么 | 第 58 行怎样形成命令，第 62–70 行怎样形成环境；第 71 行交给谁执行 |
| 遇到下一层 | 到第 71 行，转看 C；保留“B 第 71 行在等结果”这个返回位置 |
| 最终回哪里 | C 交回退出码后，B 第 71 行把它返回给 A 第 104 行；A 直接返回外层 `generate.py:205` |

正常结束时的完整返回方向是：D 的第 141 或 145 行交回 `(exit_code, output)` → C 第 111 行接收、第 122 行返回退出码 → B 第 71 行 → A 第 104 行 → `generate.py:205` 接收退出码、随后执行第 213 行收集 diff。

一次 HTTP 响应先回到 Claude CLI；只有 CLI 整体结束并由启动脚本写下退出码，启动端才沿上述方向返回。这里只做静态源码核对，没有运行 CLI、沙箱或模型服务。


<a id="http-round-trip"></a>

### 为什么这里有 HTTP，信息怎样往返

函数调用链把我们带到了正在运行的 Claude CLI。现在只展开它与 Adapter 之间的一次模型请求：**Claude CLI 是发送方，Adapter 是接收并回复的一方。**

Claude CLI 是沙箱中的独立程序，通过模型 API 获取回复。这个实现让 Slime 提供一个兼容的 API 入口，再把 Claude 的请求地址指向它；Adapter 收到请求后可以接入 SGLang，并保存这一轮的轨迹。对应处理位置是 `adapters/common.py:344、384`，本段只把模型处理视为中间步骤。

这里的“HTTP 服务”，就是 Slime 中持续监听网络地址和端口、接收请求并回复的那部分程序。Adapter 提供处理逻辑，`aiohttp` 负责网络接收、HTTP 解析、路由和响应发送。

#### 1．Slime 先准备接收方，并开始监听

启动顺序及源码位置如下。路径以 Slime 仓库为起点：

| 先后 | 源码位置 | 这一段做什么 |
| --- | --- | --- |
| ① 创建 Web 应用 | `slime/agent/adapters/common.py:159` | `web.Application(...)` 创建保存路由等配置的应用对象 |
| ② 登记接收规则 | `slime/agent/adapters/common.py:175` → `adapters/anthropic.py:49` | 将 `POST /v1/messages` 交给 `self._run_turn` |
| ③ 启动服务 | `examples/coding_agent_rl/generate.py:161–170` | 把 `self.adapter.app` 交给 `run_app_in_thread` |
| ④ 监听地址和端口 | `slime/agent/aiohttp_threaded.py:69–72` | 创建 `TCPSite` 并启动监听，实际开始接收网络连接 |

第④处的源码是：

```python
runner = web.AppRunner(app, **(runner_kwargs or {}))  # 让运行器管理这个 Web 应用
loop.run_until_complete(runner.setup())
site = web.TCPSite(runner, host, port)              # 指定监听地址与端口
loop.run_until_complete(site.start())              # 开始监听
```

这个服务在独立线程中运行（`aiohttp_threaded.py:87–88`）。因此，外层 Harness 等待 Claude 退出时，它仍能接收请求。注册路由、开始监听是两件按顺序发生的事；只有创建应用和登记路由，还没有启动网络服务。

代码入口：[创建与启动调用](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L150) · [实际监听](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/aiohttp_threaded.py#L69)。

#### 2．Slime 把接收地址交给 Claude

`generate.py:171` 组成对外地址：

```python
self.adapter_url = f"http://{CONFIG.adapter_public_host}:{self.app_handle.port}"
```

这个地址经过已经读过的 Harness 调用链，在 `harness/claude_code.py:63` 放进 Claude 的环境变量：

```python
"ANTHROPIC_BASE_URL": ctx.adapter_url,  # Claude 的模型 API 请求使用这个地址
```

可以把请求地址分成三部分：`主机地址` 找到接收方，`端口` 找到接收服务，`/v1/messages` 选择服务内的接口。`adapter_public_host` 必须是沙箱能够访问的地址；监听时使用的 `adapter_bind_host` 与客户端访问的主机地址分别配置，不能把两者混为一个值。

Claude Code 支持用 `ANTHROPIC_BASE_URL` 改变 API 地址，见[官方环境变量说明](https://code.claude.com/docs/en/env-vars)。设置地址是在告诉客户端去哪里，真正发请求发生在 Claude 程序运行期间。

#### 3．Claude 发出请求，Adapter 把网络数据交给 Python 处理器

下面是本次信息流，HTTP 发送发生在外部 CLI 内部，具体发送函数尚未检查：

```text
Claude CLI 中的消息、工具定义等请求数据
     │ 编码为 JSON，作为 HTTP POST 的请求体发送
     ▼
Adapter 的监听地址和端口
     │ aiohttp 接收请求，并按方法和路径查路由
     │ 路由依据：adapters/anthropic.py:49
     ▼
BaseAdapter._run_turn(request)             adapters/common.py:318
     │ await request.json()               adapters/common.py:325
     ▼
Python 中的 body 字典
     │ 后续交给转换、模型调用与响应组织
```

传过来的是序列化后的数据；`await request.json()` 将请求体里的 JSON 解析成这里使用的 Python 字典。原始 CLI 数据对象和 Adapter 中的 `body` 并不是共享内存里的同一个对象。

以消息字段为例，下面只截取一小部分，省略其他请求字段：

```json
{"messages": [{"role": "user", "content": "请检查这个函数。"}]}
```

解析后，处理器就能从 `body["messages"][0]["content"]` 取得这段文字。这是教学构造的字段节选，不是实际抓包，也不是完整的 Claude 请求。

#### 4．处理器给出响应，aiohttp 将它回送给这次请求的发送方

模型处理完成后，`adapters/common.py:363` 调用 `self._respond(...)`，具体实现是 `adapters/anthropic.py:71–75`：

```python
blocks, stop_reason = reply.wire
if stream:
    return await _render_stream(request, blocks, stop_reason, in_tok, out_tok)
return web.json_response(_render_response(body, blocks, stop_reason, in_tok, out_tok))
```

两条分支的返回方向相同，表达方式不同：

- **非流式：** `web.json_response(...)` 把组织好的回复变成 JSON 响应对象；`_run_turn` 在 `adapters/common.py:391` 返回这个对象，由 aiohttp 发送。
- **流式：** `_render_stream` 在 `adapters/anthropic.py:223` 用 `out.prepare(request)` 关联这次请求，再通过 `out.write(...)` 写出事件数据。这些数据仍属于这次 HTTP 响应。

**响应沿客户端发起的这次请求连接回去。** aiohttp 保留了请求与连接的对应关系；Adapter 不需要另找 Claude 的监听地址再发一个 POST。Claude 的 HTTP 客户端读到响应，把它交回自己的任务处理逻辑。

```text
请求：Claude CLI ── HTTP 请求体 ──▶ Adapter ──▶ _run_turn
响应：Claude CLI ◀─ JSON / 事件流 ◀─ aiohttp ◀─ _respond
```

这次 HTTP 往返结束，只表示 Claude 得到了这一轮模型结果。它可以继续任务、再发下一次请求；外层 `run` 继续等待整个 CLI 退出。

代码入口：[调用响应实现](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L363) · [JSON 与流式分支](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L71) · [向请求连接写事件](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L211)。`aiohttp` 的请求处理与响应机制见[官方入门](https://docs.aiohttp.org/en/stable/web_quickstart.html#handler)和[服务端接口](https://docs.aiohttp.org/en/stable/web_reference.html#streamresponse)。

本段按固定源码做静态核对，未运行沙箱、Claude CLI 或模型服务。网络协议的更底层实现、CLI 内部发送函数和模型生成内部过程继续留白。


CLI 用 `ANTHROPIC_BASE_URL` 回连 Adapter，用会话凭据标识此次任务。Slime 可核对配置与 HTTP 接收端；CLI 怎样完整组织请求、选择工具、执行命令和编辑文件，属于外部实现。

HTTP 请求到 `POST /v1/messages`，由 [AnthropicAdapter._register_routes](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L48)（`slime/agent/adapters/anthropic.py:48`） 接到共享处理函数：

```python
    def _register_routes(self, app: web.Application) -> None:
        app.router.add_post("/v1/messages", self._run_turn)
        app.router.add_post("/v1/messages/count_tokens", _count_tokens)
```


进入 [BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L318)（`slime/agent/adapters/common.py:318`） 的开头，读 JSON、预处理 body、解析 sid、检查会话与轮数门禁，并把当前 handler 加入 `inflight`。sid 关联到步骤 1 已注册的 Session。

**交接：** CLI 的消息历史、工具定义、参数与身份 → handler 持有 `body/sid/Session`。**返回位置：** `_run_turn:341` 的 `_translate(body)`；外层仍停在 `generate:205`。配套：[动作 7](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/7-make-api-calls/)。

## 5．翻译输入，向 SGLang 请求生成

<a id="translate-breadcrumb"></a>

### 先定位：为什么这里开始读 _translate

下面是当前局部在任务中的面包屑。它保留来路；只需知道经过这些职责，即可先读消息转换，不要求提前深入每个函数。

```text
generate()
└─ HARNESS_CLS().run(...)：启动并等待 CLI
   └─ CLI 运行期间发送 HTTP POST /v1/messages
      └─ BaseAdapter._run_turn(...)：处理一次模型请求
         └─ self._translate(body)     ← 当前局部观察点
```

`body` 是这次 HTTP 请求解析出的内容。当前问题是：模型请求里的消息和工具定义，怎样被整理成后续渲染需要的数据？`_translate` 适合承担这项局部细读；整次任务的七项骨架用于定位，消息字段与转换规则在函数层展开。

缩进表示阅读位置，其中 CLI 到 Adapter 经过 HTTP；`_translate` 是 `_run_turn` 内的调用。这里给出的定位不表示 Harness 直接调用了 `_translate`。

沿同一函数继续：

```python
            translated, tools_schema = self._translate(body)
            prompt_ids = _render_token_ids(translated, tok, tools=tools_schema, add_generation_prompt=True)

            turn = await call_sglang_generate(prompt_ids, s, body, adapter=self, session_id=sid)
```


进入 [AnthropicAdapter._translate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L58)（`slime/agent/adapters/anthropic.py:58`），沿 Anthropic 消息与工具转换各走一次；结果是规范化 chat messages 与 tools schema。回到 `_run_turn`，进入 [_render_token_ids](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L58)（`slime/agent/adapters/common.py:58`），由外部 tokenizer 的聊天模板编码得到 `prompt_ids`。

再进入 [call_sglang_generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L442)（`slime/agent/adapters/common.py:442`）：读取 Session/body 的采样与上下文预算，将 `input_ids`、采样参数、rid、`return_logprob=True` 交给 SGLang `/generate`。收到完整 JSON 后提取真实输出 token/logprob 与结束原因，构造 [TurnRecord](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L29)（`slime/agent/trajectory.py:29`）。

**交接：** 协议消息/tools → `prompt_ids` → SGLang 请求 → 含 `prompt_ids/output_ids/output_log_probs/finish_reason` 的 `TurnRecord`。**返回位置：** `_run_turn:344` 后的解码与解析。

第一遍到“token、logprob 和结束原因从哪里来”就够；tokenizer 与 SGLang 服务内部留给后续。此路径先取得完整生成结果，再包装客户端协议响应。配套：[动作 2](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/2-translate-forward/)、[动作 3](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/3-generate-tokens/)。

## 6．组织响应，记录这一轮，然后回到 CLI

进入 [parse_model_output](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L25)（`slime/agent/parsing.py:25`），看输出文本怎样拆成 reasoning、可见 text、tool uses 和格式状态；再看 [AnthropicAdapter._build_reply](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L63)（`slime/agent/adapters/anthropic.py:63`），将解析结果组织成客户端回复与规范化助手消息。

本轮的实际调用顺序为：

```text
decode -> parse -> build_reply
       -> _respond
       -> record_turn
       -> finally: discard inflight task
       -> handler returns response to aiohttp
```

[AnthropicAdapter._respond](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L71)（`slime/agent/adapters/anthropic.py:71`） 位于 `_run_turn:363`，[TrajectoryManager.record_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L283)（`slime/agent/trajectory.py:283`） 位于调用处 `_run_turn:384`，`:391` 的 return 先确定返回值，随后 `finally:393` 移除 inflight，handler 才将 response 交回 aiohttp。记录输入是 sid、本轮 token 记录、输入消息与助手消息；副作用是更新会话轨迹树。

这里说的是函数调用顺序：非流式分支先构造 JSON response，由 HTTP 框架完成发送；流式分支写协议事件。不能把所有分支都表述成 `_respond` 返回时客户端已收到全部字节。记录中的 `TurnRecord.finish_reason` 仍来自 SGLang，不能用协议 Reply 的结束原因替代。

**交接：** 生成记录 → CLI 协议响应 + 会话轨迹更新。**返回位置：** CLI 可以执行工具、把工具结果加入下一次请求，重复步骤 4–6；这一轮 HTTP 请求结束并不表示整次任务结束。第一遍在 `record_turn` 内只追正常追加历史，消息重写、分叉和漂移细节后置。

配套：[3.5 完成一次模型请求](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/3-5/)。等 CLI 最终退出，等待端得到退出码，沿 Harness 返回外层 `generate:213`。

## 7．回到 generate，收集 diff 并独立评分

**从主线进入：** `generate:213` → [git_diff](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L230)（`examples/coding_agent_rl/swe.py:230`），从 Agent 工作区收集代码改动。离开 Agent 沙箱上下文后，`generate:215` → [run_evaluation](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L239)（`examples/coding_agent_rl/swe.py:239`）：

```python
                diff_text = await swe.git_diff(sb, md["workdir"])

            reward, applied_cleanly = await swe.run_evaluation(
                md,
                diff_text=diff_text,
                timeout_sec=CONFIG.eval_timeout_sec,
            )
```


第一遍选 [_grade_scaleswe](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/swe.py#L253)（`examples/coding_agent_rl/swe.py:253`） 的 `eval_cmd` 分支：在一个新的评估环境中准备基线、应用 diff，再执行评测命令，得到 `reward/applied_cleanly`。工作环境与评分环境分别退出各自上下文。

**交接：** Agent 工作区 → diff；任务元数据 + diff + 评分预算 → 独立评分结果。**返回主线：** `generate:220` 的模式分支。

CLI 退出码描述进程状态，reward 描述任务评测结果；非零退出不直接等于评分失败。第一遍只走一条评分路径，把组件接回任务；SWE-bench 与全部数据集准备细节以后按需读。

## 8．导出结果，再清理 Session

现在沿 `generate` 分清两个返回：

- **evaluation 模式：** [_eval_result](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L336)（`examples/coding_agent_rl/generate.py:336`） 返回用于结果统计的评测 Sample，不走训练轨迹导出。
- **训练模式：** `generate:237` 调 [BaseAdapter.finish_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L245)（`slime/agent/adapters/common.py:245`）；它关闭会话并等待在途请求，调用 [TrajectoryManager.get_trajectory](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L307)（`slime/agent/trajectory.py:307`） 得到 Sample 列表，再解码训练尾部填充 `response`。

轨迹导出第一遍走一条正常、没有 token 漂移的多轮链：[TrajectoryManager._chain_to_samples](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L479)（`slime/agent/trajectory.py:479`） → [TrajectoryManager._split_chain_into_builders](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L456)（`slime/agent/trajectory.py:456`） → [_SampleBuilder.append_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L193)（`slime/agent/trajectory.py:193`） → [_SampleBuilder.to_sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L234)（`slime/agent/trajectory.py:234`）。解释完整 tokens、response_length、loss_mask、rollout_log_probs 如何对齐即可。后续工具/上下文 token 的 mask 与模型实际生成 token 的 mask 不同；每份输出 Sample 当前赋完整任务 reward。导出的 `response` 是多轮训练尾部，不一定只是最后一句回答。

**最终返回主线：** `generate` 确定返回值后，先执行 `finally` 的 [BaseAdapter.drop_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L278)（`slime/agent/adapters/common.py:278`）。它等待/取消在途请求，移除会话与轨迹，是 cleanup-only，不再次导出样本。 源码接着执行 `await asyncio.sleep(10)`，完成这段等待后，函数才真正把结果返回调用方；阅读任务耗时时要把它计入。

第一遍停止标准：能区分一次 HTTP 请求结束、CLI 进程结束、Session 导出与清理、整次任务结束。环境退出调用只表示进行了回收尝试，实际远端回收成功还需要运行证据。

## 再补一条失败路径

用同一书签，假设步骤 2 的 `prepare_workspace` 在沙箱已交出后抛出 `RuntimeError`：环境上下文退出 → `generate` 的 `except Exception` 生成 ABORTED 结果 → `finally` 清理 Session。只要把异常怎样返回、谁做环境与会话清理说清，就完成第一条异常链。

随后按问题选读：等待 CLI 超时返回 `-1` 与环境回收、客户端取消与服务端 abort、上下文预算耗尽、轨迹导出为空。不要假设等待函数返回超时就已经终止 CLI。

## 什么时候算读通 4.1

拿上面的假设任务，连续回答以下问题：谁准备模型入口和 Session？谁创建环境、配置并启动 CLI？外层在哪等，模型请求怎样在等待期间发生？一轮请求怎样返回并记录？CLI 退出后 diff 和评分从哪里来？评测和训练返回有何不同？失败后环境与 Session 由谁处理？

配套先读 [tests/test_agent/test_adapters.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_adapters.py#L1)（`tests/test_agent/test_adapters.py:1`） 中工具调用 → 工具结果 → 再次请求 → 导出的 fixture/断言，及 [tests/test_agent/test_trajectory_manager_branching.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_trajectory_manager_branching.py#L1)（`tests/test_agent/test_trajectory_manager_branching.py:1`） 中正常多轮链的断言。这里的文件/符号与调用关系是静态核对；本轮没有运行真实 CLI、E2B、SGLang、训练或源码仓库测试。

代码片段来自 [THUDM/slime 的固定提交](https://github.com/THUDM/slime/tree/22a89f96835969a47055a659c588f46151f8b07a)，许可见 [Apache 2.0](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/LICENSE)；片段为阅读上下文中的摘录，不是独立可执行脚本。
