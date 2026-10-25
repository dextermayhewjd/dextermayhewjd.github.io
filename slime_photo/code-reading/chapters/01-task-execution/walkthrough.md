# 沿 generate 走完 4.1：一次 Agent 任务

[本章入口](README.md) · [当前阅读主线](../../repo-reading-route.md#当前优先沿-generate-读完-41) · [需求对照](../../job-alignment.md)

本轮先完成 **Agent Rollout Adapters and Harnesses**：以 `generate()` 为书签，沿一份任务进入各组件，读清职责和输入输出后返回主线。第一遍走通正常路径，再补一条失败清理路径；实现细节按问题继续深入。

本地仓库根目录已确认是 `/home/fredkeira/projects/slime`。源码固定在 `22a89f96835969a47055a659c588f46151f8b07a`。本篇选择 **Claude Code Harness / Anthropic Adapter**，与已有 4.1 图文一致；Codex/OpenAI 留作完整链读通后的实现对照。本轮已核对：这些核心源码与旧 `8c17b676` 资料版本没有差异，原有动作讲解可以继续使用。

**版本阅读提示**：既有段落保留各自固定提交的讲解；`18868a79` 的服务对象与后台监听见 [1.1 新版接续](#adapter-service-startup-18868a79)，会话登记见 [1.2 新版接续](#session-registration-18868a79)，执行沙箱见 [2.1 新版接续](#boot-agent-sandbox-18868a79)，工作区准备见 [2.3 新版接续](#prepare-workspace-18868a79)，请求处理变化见 [Step 1 新版对照](#run-turn-version-18868a79)，评测结果与环境退出见 [7.3 新版接续](#evaluation-result-18868a79)，样本导出见 [8.1 新版接续](#sample-export-mainline-18868a79)。不要将下方旧版实现直接当作当前实现。

## 为什么从 generate 进入

CodeWiki 原图展示组件关系；本篇按任务执行读它们的组装和交接。`_AdapterService` 在示例的 `generate.py` 中，负责准备图内的 Adapter/模型连接和 HTTP 服务。它不是单轮请求处理，也不是 Harness 的启动逻辑。先扫 generate 骨架，到 state 初始化处下钻，再回外层继续；上游训练、调度和模型服务部署先视为已提供的前提。

动作 4 的前置阅读包括调用方的 Adapter、任务、Session、环境和题目准备；Launch Agent 本体继续进入 run 内部的用户、配置、命令与启动。两层串起来阅读，职责仍各自保留。

## 先把整体顺序看清

![一次 Agent 任务的生命周期](../../../../static/images/slime-lifecycle/overview.svg)

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

<a id="adapter-service-startup-18868a79"></a>

### 1.1 新版接续：服务对象怎样提供一个可用的 Adapter

本节按 `18868a79` 接续。先分清三个对象：`state` 引用 `_AdapterService`，`adapter` 处理会话与模型请求，`app_handle` 保存 HTTP 服务的运行资源。

```python
state = _AdapterService(args)
agent_name = agent_name_for(base_sample)
adapter, adapter_url, _ = state.endpoint(agent_name)
# 随后取得 session_id，并调用 adapter.open_session(...)
```

`_AdapterService.__init__` 准备 tokenizer、模型服务地址等共用依赖，并通过 `endpoint(AGENT_NAME)` 建立默认端点。服务实例可以复用；初始化方法本身返回 `None`，类调用才把服务实例交给调用方。

<a id="adapter-endpoint-cache-entry"></a>

`__init__` 先用 `self._endpoints = {}` 建立缓存，再调用 `endpoint`。缓存的键是 Agent 类型名称，例如 `"claude_code"`，值是准备好的 `(adapter, adapter_url, app_handle)`。

先看 endpoint 开头的两行：

```python
if agent_name in self._endpoints:  # 查找这个 Agent 类型是否已有端点
    return self._endpoints[agent_name]  # 交回缓存中的三元组，本次调用结束
```

已有条目就在这里返回；缺少条目时才继续创建 Adapter，再调用 `run_app_in_thread(adapter.app, ...)` 启动 HTTP 服务。第一次初始化时字典为空；默认端点建立后，后续获取同一类型即可命中缓存。

<a id="adapter-app-service-handle"></a>

#### run_app_in_thread：运行已经配好路由的 HTTP 应用

> 在后台启动已有 HTTP 应用，使它开始接收请求，并把服务管理对象交回调用方。

请求交给谁处理，已经在 Adapter 注册路由时确定。例如下面这句来自 `AnthropicAdapter._register_routes`：

```python
app.router.add_post("/v1/messages", self._run_turn)  # 提前登记这个 HTTP 方法和路径的处理函数
```

服务启动后，发到此服务、匹配 `POST /v1/messages` 的请求才交给 `_run_turn`。其他路径按各自的规则处理。启动函数负责运行这个应用，路由注册负责指定处理函数。

<details>
<summary>回看应用创建、运行位置与 AppHandle</summary>

HTTP 应用由 Adapter 显式创建。`BaseAdapter.__init__:224` 使用 Python 的 aiohttp 库建立应用对象：

```python
self.app = web.Application(client_max_size=64 * 1024 * 1024)  # 创建 HTTP 应用对象
```

当前 AnthropicAdapter 随后在 `_register_routes:49` 登记消息请求的处理入口：

```python
app.router.add_post("/v1/messages", self._run_turn)  # 指定此路径的 POST 请求由哪个函数处理
```

此时定义了请求处理规则，尚未建立监听。`run_app_in_thread` 接过这个 `adapter.app`，在运行 Slime 的当前 Python 进程内启动后台线程，让 HTTP 服务开始监听并执行这些规则。正常启动后的关系是：

```text
运行 Slime 的节点
└─ 当前 Python 进程
   ├─ 调用方：拿到 app_handle，继续后面的流程
   └─ 后台线程：运行 HTTP 服务，按 adapter.app 的规则处理请求
```

沙箱中的 CLI 通过 `adapter_url` 请求这个服务。调用方保存的 `app_handle` 则是本项目定义的 AppHandle 数据对象，里面是服务运行的信息和对象引用；例如 `app_handle.port` 可读取实际端口，`app_handle.stop()` 提供之后关闭服务的操作入口。它的具体线程、循环和 runner 字段可以随实现逐项阅读。

当前先理解“应用规定如何处理请求 → 启动函数让服务运行 → 句柄供调用方查看和管理”即可。以下代码仍按静态源码解释，没有在本次阅读中启动真实 Adapter 服务。

</details>

<a id="adapter-thread-start-first-step"></a>

#### 先看两行：创建线程对象与启动线程

HTTP 服务需要持续处理请求，外层还需要继续执行任务。这里先看怎样把服务工作交给另一个线程。下面是 `run_app_in_thread` 的 87–88 行，增加了阅读注释；本次只关注 `target` 和 `start()`。

```python
thread = threading.Thread(target=_run, name=thread_name, daemon=True)  # 创建线程对象，指定入口函数
thread.start()  # 启动新线程，由它调用 _run()
```

`_run` 是前面用普通 `def` 定义的函数，定义时函数体还没有执行。第一行将这个函数交给线程对象；`target=_run` 没有括号，这里没有调用它。第二行启动新线程，由新线程调用 `_run()`。

原调用线程继续执行 `run_app_in_thread` 后面的代码，新线程负责 `_run` 中的工作。先读清这两个执行位置，再看下一行怎样等待启动通知。

#### 后续阅读：完整的启动交接

`run_app_in_thread` 的正常启动路径是：

```text
Caller thread                          Adapter thread
-------------                          --------------
thread.start() ----------------------> create event loop
started.wait()                         set up AppRunner
                                       start TCP listener
                <--------------------- started.set()
return AppHandle                       loop.run_forever()
endpoint continues                     handles HTTP requests
```

这里要同时看清返回与持续运行：调用线程等待启动通知后拿到 AppHandle，后台线程继续运行 HTTP 事件循环。句柄保留线程、循环、runner 和实际监听地址。

<a id="adapter-listen-port"></a>

#### 在启动参数处看监听端口

下面是 `endpoint` 调用启动函数的参数节选：

```python
app_handle = run_app_in_thread(
    adapter.app,
    host=CONFIG.adapter_bind_host,  # HTTP 服务的监听绑定地址
    port=CONFIG.adapter_port if not self._endpoints else 0,  # 请求监听的端口
    # 阅读节选：这里省略 thread_name 和 runner_kwargs
)
```

`port` 指定这个 HTTP 服务的监听入口。第一份端点使用配置的端口；后续新建端点传入 `0`，由系统分配可用端口。正常启动后，`app_handle.port` 保存实际监听端口。

<a id="adapter-node-ip-and-thread"></a>
<a id="adapter-public-host"></a>

#### 在 public_host 处看节点 IP

```python
# 自动取得当前节点 IP，或直接采用已配置的对外主机
public_host = get_current_node_ip() if CONFIG.adapter_public_host == "auto" else CONFIG.adapter_public_host
```

node 可以先理解为运行 Adapter 服务的计算节点，node IP 是它的网络地址。配置为 `"auto"` 时取得当前节点 IP；显式配置时直接使用该对外主机地址。

<a id="adapter-url-assembly"></a>

#### 在 URL 拼接处连接两项结果

```python
adapter_url = f"http://{public_host}:{app_handle.port}"  # 组成对外访问地址
# 省略日志
self._endpoints[agent_name] = (adapter, adapter_url, app_handle)  # 按 Agent 名称缓存三项结果
return self._endpoints[agent_name]  # 把这份三元组交回调用方
```

这里使用前两处已经取得的结果。`endpoint` 随后缓存并返回 `(adapter, adapter_url, app_handle)`；地址供沙箱中的 CLI 访问。示意值 `192.0.2.10` 与 `18001` 组合为 `http://192.0.2.10:18001`，并未执行真实网络验证。

<details>
<summary>可选回顾：请求与服务的运行位置</summary>

```text
沙箱中的 CLI
    │ HTTP 请求：http://192.0.2.10:18001
    ▼
运行 Adapter 服务的节点
    └─ Python 进程
       └─ 后台线程运行 adapter.app，监听 18001 端口
```

IP 与端口用于找到服务，后台线程执行服务代码。此处的整体图只用于回顾，具体说明分别紧跟端口参数、IP 取值和 URL 拼接的代码。

</details>

本节只读清服务准备与正常启动交接。HTTP 请求分派、启动失败与超时的完整处理、`AppHandle.stop()` 的停止回收另行展开；这些静态说明没有实际运行 Adapter、模型或沙箱。

<details>
<summary>本节固定源码入口</summary>

- [初始化与 endpoint：generate.py:167–222](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L167-L222)。
- [调用与会话登记：generate.py:254–279](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L254-L279)。
- [AppHandle 与后台启动：aiohttp_threaded.py:25–98](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/aiohttp_threaded.py#L25-L98)。

</details>

<a id="session-registration-18868a79"></a>

### 1.2 新版接续：用已有编号登记一份 Session

服务与 Adapter 已经准备好，调用方还需要从基础样本整理题目信息。`md` 在新版中仍参与这次准备；下面保留 `_generate:261–269` 的关键语句，省略条件检查：

```python
md = swe.get_metadata(base_sample, protocol)  # 按任务协议整理题目信息
instance_id = md["instance_id"]  # 取出题目编号
session_id = base_sample.session_id = _session_id(base_sample, instance_id)  # 取得并保存执行编号
```

`md["image"]` 与 `md["workdir"]` 后续继续用于沙箱和工作区准备，评测也会使用 md 中的材料。随后 `adapter.open_session(...)` 登记会话状态；完整 md 没有作为这个方法的参数传入。

沿用教学例：题目编号为 `demo-1`，两个样本索引都是 0，原先没有编号，得到 `cagent-demo-1-0-0`。为观察登记，传入采样参数 `{"temperature": 0.7, "top_p": 0.9}`、上下文长度 `4096`、空模板选项与 `trace=None`；实际调用处的 trace 由调用方准备，本例只检验存储行为。

`open_session` 在 `common.py:284–292` 执行以下语句：

```python
"""Register a fresh per-sid Session; sids must be unique."""
if sid in self.store:  # 同一编号不能重复登记
    raise ValueError(f"session_id {sid!r} already exists; sids must be unique per agent run")
self.store[sid] = Session(  # 创建会话状态，用编号保存
    sampling_defaults=dict(sampling_defaults or {}),
    max_context_tokens=int(max_context_tokens or 0),
    apply_chat_template_kwargs=dict(apply_chat_template_kwargs or {}),
    trace=trace,
)
```

编号直接作为 store 的键；Session 接收配置并创建新对象。两个 `dict(...)` 复制顶层字典，长度整理为整数，trace 引用直接保存。假定原 store 为空，登记后包含：

```python
{
    "cagent-demo-1-0-0": Session(
        sampling_defaults={"temperature": 0.7, "top_p": 0.9},
        max_context_tokens=4096,
        apply_chat_template_kwargs={},
        prompt_prefixes=[],
        trace=None,
    )
}
```

`prompt_prefixes` 由 Session 的默认工厂建立，open_session 没有显式传入它。函数正常返回 `None`，这次产生的结果保存在 `adapter.store[sid]` 中；后续请求按编号使用它，结束时 `finish_session` 再取走。HTTP 服务已在前面启动，这里完成的是当前进程内的一次状态登记。

<details>
<summary>本节源码与验证范围</summary>

- 固定版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[编号与登记调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L269-L279)、[编号规则](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L438-L443)。
- [Session 定义](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L45-L57)、[open_session](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L292)。
- 局部执行原始类与函数，以只有 store 的对象承载方法，核对了本例字段、返回值、字典复制、默认列表与重复编号保留旧记录。没有创建完整 Adapter、HTTP 服务、模型或沙箱。

</details>

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

<a id="boot-agent-sandbox-18868a79"></a>

### 2.1 新版接续：选择执行沙箱，准备 CLI，再交给调用方

以下依据 `18868a79`。调用方在 `_generate:283` 传入任务镜像、题目编号、当前 Harness 和追踪上下文：

```python
async with boot_agent_sandbox(md["image"], instance_id, harness=harness, trace=base_sample) as sb:
    baseline = await swe.prepare_workspace(sb, md["workdir"], md)
    ...  # 同一个 sb 继续用于运行 Agent、收集统计和提取补丁
```

创建入口由直接构造 E2B 改为 `create_sandbox(image)`。工厂按 `SWE_SANDBOX_PROVIDER` 选择后端，默认 Sunabako，也可选择 E2B；创建对象之后，才通过进入方法使执行环境就绪。下面是一次成功路径的教学裁剪，省略并发、追踪、重试与安装失败包装：

```python
cand = create_sandbox(image)  # 得到当前后端的候选对象
await cand.__aenter__()  # 使对应的执行环境就绪
await (harness or HARNESS_CLS()).install_cli(cand)  # 在同一环境准备 CLI
sb = cand  # 保留同一个对象
try:
    yield sb  # 交给调用处，本函数暂停
finally:
    await sb.__aexit__(*sys.exc_info())  # 调用方离开上下文后请求回收
```

`yield` 交出的是能够操作执行环境的本地对象。调用方使用期间环境仍保留；工作区准备、CLI 运行和结果收集都在调用方的上下文块中完成。离开块时才执行这里的退出处理，正常结束后回到独立评测。

当前 Claude Code 安装方法新增 native 包分支；未指定 native 包时沿用公共 npm 安装。配置并发门限为 0 时不使用准备信号量，设置正数时限制环境进入与 CLI 安装，交付给调用方前即释放。失败、取消与后端清理的完整细节按对应实现继续核对。

<details>
<summary>固定源码与验证边界</summary>

- [boot_agent_sandbox:110–164](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L110-L164)、[调用与使用期:283–306](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L306)。
- [沙箱工厂](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sandbox.py#L8-L16)、[Claude Code 安装分支](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L38-L55)。
- 使用原始父函数和替身核对正常交付、调用方异常、安装失败后重试及耗尽路径；没有运行真实沙箱或安装软件。

</details>

<a id="sunabako-lifecycle-18868a79"></a>

### 2.2 SunabakoSandbox：从初始字段，到环境就绪，再到退出

前面已经有“准备 → 交付使用 → 退出”的外层骨架。现在沿同一个 `cand` 看三个方法各自增加什么。以下依据 `18868a79`，采用默认 Sunabako 路径；配置和路径是教学占位，没有创建真实环境。

#### 2.2.1 `__init__`：先给本地对象备好字段

`create_sandbox(image)` 选中 Sunabako 后，执行 `SunabakoSandbox(image)`，触发这个初始化方法。下面保留完整方法，只添加注释：

```python
def __init__(self, image: str) -> None:
    self.image = image                 # 用于查找本次镜像的配置
    self.sandbox_id = ""               # 进入成功后再填写编号
    self._sandbox = None              # 进入成功后再保存 SDK 操作对象
    self._commands: list[dict] = []    # 后续积累命令与执行结果
    self._workdir = "/testbed"         # 默认工作目录路径
    self._runtime = None              # 进入成功后记录运行方式
```

这些字段在运行 Slime 的 Python 对象中。此时还没有调用 SDK 创建环境，工作目录字段也只是一个路径字符串。工厂返回后，`cand` 指向这个对象；后续方法中的 `self` 仍指向它。

#### 2.2.2 `__aenter__`：创建环境，保存操作它的入口

进入方法先根据 `self.image` 查到创建资料：

```python
cluster = Cluster.from_file(os.environ["SUNABAKO_CLUSTER"])
images = json.loads(Path(os.environ["SUNABAKO_IMAGES"]).read_text())
info = images[self.image]
self._workdir = info.get("workdir", "/testbed")
```

`SUNABAKO_CLUSTER` 指向提供可分配节点信息的配置文件；`SUNABAKO_IMAGES` 指向镜像映射 JSON。它们在 Slime 主机上读取。`info` 是这次镜像的配置，其中 `rootfs` 指向所选节点可访问的镜像或根文件系统材料。

然后把资料交给 Sunabako SDK。以下节选省略网络、资源、环境变量参数及日志、可选清单；完整实参见下方固定源码入口。

```python
runtime = os.environ.get("SUNABAKO_RUNTIME", "proot")
self._sandbox = await AsyncSandbox.create(
    info["rootfs"],
    cluster=cluster,
    runtime=runtime,
)
self._runtime = runtime
self.sandbox_id = self._sandbox.sandbox_id
return self
```

现在最重要的变化是：`cand._sandbox` 从 `None` 变成了本地 SDK 操作对象。它负责后续与节点上执行环境的交互；`cand` 本身仍是外层的 Slime 封装对象。

返回的 `self` 还是同一个对象。当前父函数没有接这个返回值，而是继续把已经就绪的 `cand` 传给 `install_cli`。CLI 安装由 `boot_agent_sandbox` 安排，随后才通过 `yield sb` 交给调用方使用。

<details>
<summary>本轮暂时折叠的创建选项</summary>

原调用还指定 `network="host"`、内存与进程数限制、创建超时、内存管理方式，以及合并后的环境变量。运行方式默认 `proot`；这些参数的后端实现留待需要时深入。

设置 `SUNABAKO_ARTIFACTS` 时，返回前会在本机保存创建清单，记录镜像、沙箱编号和节点；写清单失败时先请求回收，再抛出异常。SDK 创建部分失败时的内部清理仍需另查，不能由这段包装代码推断。

</details>

#### 2.2.3 `__aexit__`：用同一个操作入口收尾

调用方离开外层的 `async with` 后，`boot_agent_sandbox` 调用 `sb.__aexit__(*sys.exc_info())`。此时 `sb` 就是此前的 `cand`。

下面保留退出方法的前半段，后半段的特定异常转换放在折叠说明中：

```python
async def __aexit__(self, exc_type, exc, tb) -> None:
    if self._sandbox is None:
        return
    try:
        if destination := os.environ.get("SUNABAKO_ARTIFACTS"):
            await self._save_artifacts(Path(destination) / self.sandbox_id)
    except Exception:
        logger.exception("[sunabako] could not save artifacts for %s", self.sandbox_id)
    finally:
        await self._sandbox.kill(defer_cleanup=os.environ.get("SUNABAKO_DEFER_ROOTFS_DELETE") == "1")
```

<a id="sunabako-artifact-boundary"></a>

只有设置 `SUNABAKO_ARTIFACTS` 时，才先把指定的运行记录和日志文件保存到 Slime 主机上按沙箱编号区分的目录；这里不保存整个执行环境的快照。未设置时，直接请求回收。普通保存异常会记日志，`finally` 中仍尝试 `kill`，因此回收不以保存成功为前提。回收调用本身失败会向外传播。

正常完成返回 `None`，本地的 `_sandbox` 和 `sandbox_id` 没有被清空。字段仍在，不说明执行环境仍可使用。正常退出这段使用期后，外层继续独立评测。

<details>
<summary>产物、延后清理与异常转换</summary>

产物包括创建清单、命令记录、可取得的状态以及轨迹／安装／评测日志。部分内容需要通过 SDK 从执行环境读取，因此保存安排在回收之前。

`SUNABAKO_DEFER_ROOTFS_DELETE="1"` 时，向 SDK 传入 `defer_cleanup=True`；具体延后删除的行为属于后端实现。

退出方法在回收正常完成后，还检查传入的 `exc`：如果它是 SDK 的 `SandboxError`，且可解析的 JSON 中 `error` 恰为 `"sandbox must be running"`，就改抛 `SandboxTerminatedError`。其他原异常由外层继续传播；正常退出时三个异常参数均为 `None`。

</details>

<details>
<summary>固定源码与阅读边界</summary>

- [初始化：21–27](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L21-L27)。
- [进入与完整创建参数：35–82](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L35-L82)。
- [退出及异常转换：84–103](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L84-L103)。
- [产物辅助函数：105–124](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/sunabako_sandbox.py#L105-L124)，只核对产物含义和保存位置。
- 本轮为静态源码阅读，止于 SDK 的创建和回收接口；没有启动真实沙箱、安装 CLI 或运行模型。

</details>


<a id="prepare-workspace-18868a79"></a>

### 2.3 prepare_workspace：布置题目工作区，留下运行前的基准

执行环境和 CLI 已就绪后，`_generate:285` 调用：

```python
baseline = await swe.prepare_workspace(sb, md["workdir"], md)
```

三个输入各有分工：`sb` 用于操作同一个执行环境，`workdir` 指定本题代码目录，`md` 提供准备配置与题目文字。下面依据 `18868a79`，沿用 auth0-python 题目的字段：工作目录是 `/workspace/auth0-python`，`swepro=None`，而 `pre_commands` 含有切换到题目基础版本的命令。本例只用于阅读，没有启动镜像或执行命令。

#### 2.3.1 准备账号与目录访问

```python
await agent_sandbox.ensure_agent_user(sb, workdir)
```

<a id="ensure-agent-user-execution"></a>

这里的 `agent` 是执行环境中的系统账号，已有时复用，没有时才创建。函数还准备 Git 安全目录设置，目录归属按后端条件处理。沿前文的 Sunabako / `proot` 场景时，跳过递归 `chown`；所需代码仓库仍须已在环境中。

函数以 `root` 身份调用 `sb.exec`，并通过 `await` 等待命令执行完成。正常返回的是 `None`，准备效果留在执行环境中，调用方继续使用同一个 `sb`。源码中已保留失败检查与 600 秒命令预算。

#### 2.3.2 按题目配置整理工作区

```python
if md.get("protocol") == PROTOCOL_SCALESWE:
    grading = md.get("grading") or {}
    swepro = grading.get("swepro")
    if swepro:
        await apply_before_repo_set_cmd(sb, workdir, swepro)
    pre_commands = grading.get("pre_commands")
    if pre_commands:
        await apply_pre_commands(sb, workdir, pre_commands)
```

本例跳过 `swepro`，执行 `pre_commands`，其中包含切换到题目基础提交的操作。两项是独立条件，都有值时就按顺序处理；其他协议跳过这一段。

<a id="apply-before-preparation"></a>

`apply_before_repo_set_cmd` 处理的是题目配置指定的那部分前置准备：取出 `swepro["before_repo_set_cmd"]` 中已有的命令，写成 `/workspace/swepro_setup/before.sh`，再以 `agent` 身份执行；脚本先进入 `workdir`，再运行这些命令。例如教学配置 `mkdir -p .cache` 只会创建目录，安装软件要由配置中的具体命令决定。返回后父函数仍继续其余准备与题目写入，实际修复题目发生在后续 Agent 运行阶段。

这些辅助函数把配置里的命令写成脚本并在环境中执行。当前 `pre_commands` 脚本位置是 `/tmp/__cagent_pre__.sh`，而命令工作的目录是传入的 `workdir`。Python 编排留在 Slime 主机上，命令执行产生的变化留在工作区。

<details>
<summary>准备命令与评测字段的边界</summary>

本函数不读取 `eval_cmd` 或 `f2p_script`，它们留给后续独立评测。两个准备入口的最终命令使用 `check=False`，父函数没有验收其退出码，所以正常返回不保证可选准备命令已达到预期效果。

第二段的条件判断、调用顺序与两个辅助函数体均和旧版相同。但 `_PRE` 常量由 `/workspace/__cagent_pre__.sh` 改到 `/tmp/__cagent_pre__.sh`，因此脚本的保存位置变化了，执行目录仍是 `workdir`。源码注释说明，`/workspace` 在某些后端可能归 root 所有，而脚本由 `agent` 写入；新版改用各沙箱自己的 `/tmp`。

父函数新增的 `baseline` 返回属于下方第 4 段。它扩展了准备完成后的交接，不改变这里先检查 `swepro`、再检查 `pre_commands` 的顺序。

</details>

#### 2.3.3 写入 Agent 要读取的题目

```python
await sb.write_file(
    f"{workdir}/PROBLEM_STATEMENT.md",
    md.get("problem_statement") or "",
    user="agent",
)
```

本例的文件是 `/workspace/auth0-python/PROBLEM_STATEMENT.md`，内容为原题目的问题描述。这里以 `agent` 身份写入字符串；后续默认 `SWE_PROMPT` 要求 Agent 读取这个文件并解决问题。写好说明后，当前函数还剩最后一次交接。

#### 2.3.4 记录准备后的状态，返回 baseline

```python
return await _repository_tree(sb, workdir)
```

`_repository_tree` 取得纳入比较的工作区文件状态，返回 Git 树标识。调用方用 `baseline` 接住这个字符串，同时继续把原来的 `sb` 交给 `harness.run`。

基准取在准备动作之后、调用 `harness.run` 之前。这样，准备阶段已有的变化属于比较起点；等待该调用返回后，`git_diff` 再取得当时的状态并与 `baseline` 比较，返回本次改动的补丁。比较时显式排除根目录的题目文件与 `.harness`；快照如何处理这些路径见[下一节](#repository-tree-18868a79)。

环境中的准备效果与返回值分开理解：文件和目录状态留在执行环境，`baseline` 回到 Slime 调用方。它不是本次补丁，也不能证明前面的可选命令一定成功。

<details>
<summary>四段版本差异、固定源码与样例来源</summary>

| 部分 | `2f231865` → `18868a79` 的变化 |
| --- | --- |
| 1. 用户与目录准备 | 父函数的调用不变；`ensure_agent_user` 增加后端条件，按需跳过递归 `chown`，并改进路径引用及命令预算 |
| 2. 按配置执行准备命令 | 分支、顺序和两个辅助函数体不变；`pre_commands` 脚本的运行时路径由 `/workspace` 改为 `/tmp`，执行目录仍是 `workdir` |
| 3. 写入题目文件 | 调用及其参数不变，仍把题目字符串写入 `PROBLEM_STATEMENT.md` |
| 4. 返回初始状态 | 新增 `_repository_tree` 调用，返回 `baseline` 字符串供后续比较；旧版返回 `None` |

路径变化发生在沙箱内的脚本保存位置，两个准备函数仍位于 `swe.py`。第 2、3 段可沿用既有职责模型，第 1 段补后端条件，第 4 段补初始状态与后续比较的交接。

- [prepare_workspace：187–209](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L187-L209)。
- [调用与后续比较：generate.py:283–298](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L298)。
- [用户准备：sandbox.py:409–420](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L409-L420)；[准备命令与快照：swe.py:212–262](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L212-L262)。
- 题目字段来自 [Scale-SWE 固定版本](https://huggingface.co/datasets/AweAI-Team/Scale-SWE/blob/d8db20390a936bbda9c96d88b97cc4778dff1481/processed_to_upload.jsonl) 的 `auth0_auth0-python_pr671`；字段映射用于解释输入，不代表镜像已经接入当前 Sunabako 部署。
- 这段保留父函数的静态交接；Git 临时索引在[下一节](#repository-tree-18868a79)展开，SDK 通信与其他辅助函数的完整实现按需回查。

</details>


<a id="repository-tree-18868a79"></a>

### 2.4 _repository_tree：用临时索引记录当前文件状态

`prepare_workspace` 最后需要一份运行前的代码基准；调用方等待 `harness.run` 返回后，`git_diff` 还会调用同一函数再取一次状态。本节依据 `18868a79`，解释“工作区 → 临时索引 → Git 树标识”这一条交接。

索引（index）是 Git 记录路径与文件版本的清单。下面用独立的小型 Git 实验，只看同一个 `source.py`：

| 位置 | 调用前的内容 |
| --- | --- |
| `HEAD` 所指提交 | `result = 0` |
| 原暂存区 | `result = 1` |
| 工作区文件 | `result = 2` |

这次要记录工作区里的 `2`，同时保留原暂存区的 `1`。示例在本地临时仓库验证，展示路径写为 `/workspace/repo`，与前文的真实题目分开。

#### 2.4.1 临时索引先载入 HEAD

前两段展示源码拼出的 Shell 文本，长行只做排版换行。Python 先组装整串 `cmd`，在第 3 段通过一次 `sb.exec` 执行。

```bash
set -e
cd /workspace/repo
agent_index=$(mktemp)
rm -f "$agent_index"
trap 'rm -f "$agent_index" "$agent_index.lock" "$agent_index.paths"' EXIT
export GIT_INDEX_FILE="$agent_index"
git read-tree HEAD
```

`GIT_INDEX_FILE` 指定这次 Shell 中 Git 命令使用的临时索引。空临时文件先移除，让 Git 创建有效索引；退出清理登记在 `trap` 中。`git read-tree HEAD` 把原提交状态载入临时索引，此时里面是 `result = 0`，工作区和原暂存区都保持原样。

#### 2.4.2 用工作区内容更新，再写成树

```bash
git ls-files -z --cached --others --exclude-standard -- . \
  ':(top,exclude)PROBLEM_STATEMENT.md' \
  ':(top,exclude).harness' > "$agent_index.paths"
git update-index --add --remove -z --stdin < "$agent_index.paths"
git write-tree
```

`ls-files` 收集要更新的路径，写到 `.paths` 文件；`-z` 使用 NUL 分隔路径。`update-index` 再按这些路径读取工作区内容，处理新增与删除。因此临时索引中的 `source.py` 更新为 `result = 2`，原暂存区的 `1` 不变。

`git write-tree` 根据临时索引写出树对象，并将树标识打印到标准输出。这里没有创建新提交，也没有移动 `HEAD`。

<details>
<summary>题目文件与运行记录怎样被排除</summary>

路径名单不更新 `PROBLEM_STATEMENT.md` 和 `.harness`。如果这些路径已在 `HEAD` 中，初始化临时索引时载入的旧条目仍可能保留，所以不能把它理解为“树里绝对没有这些文件”。本地实验验证了已跟踪的题目文件保留 `HEAD` 版本，而未跟踪的运行日志没有加入。

后续 `git_diff` 在比较两棵树时，还会显式排除这两类路径的差异。

</details>

#### 2.4.3 取回树标识，交给调用方

```python
_, out, _ = await sb.exec(cmd, user="agent", timeout=600, check=True)
tree = out.strip()
if len(tree) not in (40, 64) or any(c not in "0123456789abcdef" for c in tree):
    raise RuntimeError(f"Invalid repository snapshot: {tree!r}")
return tree
```

前两段命令在执行环境中运行。Python 等待结束，接住标准输出，去掉两端空白，并检查它是否为 40 或 64 位小写十六进制字符串。

同一个返回值，在 `prepare_workspace` 的调用链里成为 `baseline`，在 `git_diff` 中成为 `current`；名称不同来自调用时机。返回的是树标识，补丁文本要在之后比较两棵树时才产生。

这里的 `current` 是 `git_diff` 保存的一次快照标识。CLI 运行期间可以反复请求 `_run_turn` 并通过工具修改工作区；这些文件变化不会自动改写已经取得的树标识或旧树内容。

<details>
<summary>固定源码、实验与边界</summary>

- [完整函数：swe.py:241–262](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L241-L262)。
- 当前调用顺序见 [generate.py:283–330](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L330)。`_run_turn` 不引用这个 `current` 局部变量；它负责模型请求与会话、轨迹的更新。
- 快照不会冻结文件系统。[等待函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L79-L162)超时时可返回超时码，而未在此同步停止远端进程；因此不能把所有返回情况都视为所有后台活动已停止。即使后续还有文件写入，旧树仍保持原内容。
- 本次本地实验使用原样提取的函数，以 Bash/Git 执行器替代沙箱；核对工作区版本、新文件、删除、忽略项与已跟踪排除项，以及原暂存区、`HEAD` 和业务文件保持原样。
- Git 对象写入仓库对象库，临时索引等文件在 Shell 退出时清理；没有创建真实沙箱、切换系统用户或运行 Agent。
- 索引文件格式、Git 对象的回收机制、并发写入与真实 SDK 传输暂不展开。

</details>


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

<a id="launch-pid-compaction-18868a79"></a>
<a id="launch-and-wait-mainline-18868a79"></a>

### 3.1 新版接续：launch_and_wait 怎样连接启动材料、沙箱与模型服务

`BaseHarness.run` 已准备好账号、运行上下文和 CLI 配置，随后调用 `launch_and_wait(sb, ctx, prompt, time_budget_sec)`。本函数按三段理解：

- **组装启动材料**：把 `prompt` 和 `ctx` 变成 `cmd`、`env`。
- **补充运行控制**：在命令中安排统计初始化、启动 CLI、保存 PID 和等待。
- **委派并等待**：交给 `run_agent`，由下层在沙箱执行，最后取回整数结果。

以下绑定 `18868a79`，沿 Claude Code 场景说明。图中目录、地址和编号采用教学值，未运行真实 CLI。

#### 先看整体关系

双线框表示本函数直接负责的内容。下方是同一调用链中的执行层与协作服务；模型请求发生在 CLI 运行期间。

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

#### ① 组装 cmd 与 env（87–99）

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

`prompt` 放进 `claude -p` 命令，`ctx` 的地址、会话编号与模型标签放进三个 `ANTHROPIC_*` 环境变量。CLI 之后读取这些变量并向 Adapter 请求模型。本段只在本地构造字符串和字典，运行开关来自类配置，额外参数与环境覆盖是可选项。

#### ② 加入统计、PID 与等待包装（100–108）

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

这段继续构造 `cmd`。当下层在沙箱执行它时，才会清零 `compaction.json`、后台启动 CLI、保存 PID 并等待子进程。这里的 PID 是本次运行进程的编号。

<details>
<summary>PID 和压缩事件怎样配合</summary>

- `compaction.json` 保存压缩尝试、完成次数与是否触限；`cli.pid` 保存本次 CLI 的进程编号。
- 前面的 `write_config` 已放好脚本并注册 `PreCompact`、`PostCompact`。压缩由 Claude CLI 自身处理；hook 在事件发生时记录次数。
- 若启用了次数上限，下一次压缩前发现预算已用完，hook 读取 PID、核验进程关系后向该 CLI 发 `SIGTERM`；默认上限为 `-1` 时不因次数停止。
- `wait` 等待该子进程结束，外层启动脚本随后可以写完成标记，使退出状态返回给 Slime。

</details>

#### ③ 委派执行，等待返回结果（109）

```python
return await run_agent(sb, workdir=ctx.workdir, start_cmd=cmd, env=env, time_budget_sec=time_budget_sec)
```

`run_agent` 接住同一个沙箱、工作目录、命令、环境变量和预算，先准备输出目录，再交给 `exec_and_wait` 启动并等待完成标记。CLI 在此期间可以请求模型、执行工具与修改代码。

下层取得执行结果后，整数结果沿 `run_agent → launch_and_wait → BaseHarness.run` 返回到 `_generate:287`。一次模型回复会回到仍在运行的 CLI，整次调用的结果则回到等待它的 Slime 主线。

<details>
<summary>固定源码与边界</summary>

- [launch_and_wait：86–109](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L86-L109)；[BaseHarness.run：81–104](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L81-L104)。
- [run_agent：111–126](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L111-L126)；[执行与等待：sandbox.py:79–162](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/sandbox.py#L79-L162)。
- [配置与 hook 注册](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/claude_code.py#L57-L84)；[压缩事件处理与停止](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/compaction.py#L23-L68)。
- 正常完成时返回 CLI 退出码；等待预算耗尽也可能返回超时码，不能据此断言所有后台活动已停止。本轮只核对源码与材料，没有执行真实 CLI 或发送停止信号。

</details>


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

这里的后台执行不依赖启动请求一直保持连接；主机上的 Slime 仍会读取完成文件，等待结果或达到预算。“脱机运行”不表示主机不再参与。

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

<a id="run-turn-version-18868a79"></a>

## Step 1 新版对照：请求主线保留，token 接续与生成记录变化

本节比较 Slime `2f231865` 与 `18868a79`，沿用 Claude Code / Anthropic 场景。先区分两个层次：整次任务的七个业务环节仍在，但具体调用和数据交接已经变化；一次模型请求也仍经过“转换 → 输入 token → 生成 → 解析 → 响应与记录”，其中输入准备、生成过程和留下的状态需要重新校准。

### 哪些旧认识可以保留，哪些需要补齐

| 位置 | 旧版认识 | 新版需要补上的关系 |
| --- | --- | --- |
| 消息转换 | `_translate` 交出 `translated` 与 `tools_schema` | 两路输出保留；Anthropic 转换在工具结果的 ID 都能匹配既有调用时，恢复调用顺序，避免并行工具按不同顺序返回后配错位置 |
| 模型输入 | `_run_turn` 直接调用 `_render_token_ids` | 改为 `_session_prompt_ids`：先正常渲染，满足历史、工具定义及 token 边界等检查时，使用历史原始 token 接上新内容；不满足条件时返回正常渲染结果 |
| 模型生成 | 一次 HTTP POST 后构成一份 `TurnRecord` | 开启 `partial_rollout` 且 SGLang 以 `abort` 结束、仍有生成预算时，带着已生成 token 继续请求；最终汇总为一轮记录。普通 HTTP 错误并非都自动重试 |
| 生成输出 | `TurnRecord` 保存输入与输出 ID、生成 token 的 logprob、结束原因及格式标记 | 原字段保留，增加 `replay`、`weight_versions`、`spec_info`、`prefix_cache_info`，承接训练重放资料、权重版本及生成统计；字段可能为空，不代表每次都取得所有附加信息 |
| 请求尾部 | manager 记下本轮轨迹，随后返回响应并清理在途登记 | 额外向 `Session.prompt_prefixes` 保存本轮消息、工具定义与 `turn`，供下次 `_session_prompt_ids` 使用；这是输入接续状态，与 manager 的轨迹树分工不同 |

### 本轮的阅读顺序

先按 `_translate → _session_prompt_ids → call_sglang_generate → trace_span` 阅读。前三处依次回答“请求如何变成消息与工具定义、如何准备输入 token、如何获得生成记录”；再解释追踪包住了哪些已经读清的业务阶段。

这是讲解顺序。运行时仍先进入外层追踪范围，再执行其中的转换、编码与生成；不能将它读成生成结束后才启动追踪。本轮先解释局部追踪职责与范围，完整传播和导出机制仍可独立展开。

<a id="translate-version-calibration"></a>

### 先看 _translate：核心职责保留，工具结果顺序有变化

对比 `2f231865 → 18868a79`，共同接口、Anthropic 的转换入口与工具 schema 转换未变。真实入口仍然是下面三行：

```python
translated = _translate_messages(body.get("messages") or [], body.get("system"))
tools_schema = _tools_to_chat_tools(body.get("tools"))
return translated, tools_schema
```

因此原来的核心模型继续成立：`translated` 保存系统指令与对话历史，包括已有工具调用及其结果；`tools_schema` 保存当前可用工具与参数定义。这里只转换已有数据，不执行工具。原卡片中“读取 README.md”的单工具样例已用新旧版本局部执行，输出相同。

变化在 `_translate_messages` 内：对可按 ID 对应的多个工具结果，先恢复调用顺序，再输出不带协议 ID 的 `role: tool` 消息。

```text
此前工具调用：       A → B
请求携带工具结果：   B → A
旧版 translated：  B → A
新版 translated：  A → B
```

这只调整一组工具结果：ID 有无法匹配的项时保留原顺序，遇到普通文本等内容时先交出已积累的结果，不重排整段对话。这里整理的是请求中已经存在的结果排列，不控制工具实际完成或返回的先后。实现注释指出，模板可能按位置关联结果，因此丢弃 ID 之前需恢复对应关系。

本次执行了固定版本的转换方法与四个纯辅助函数，检查原样例、结果重排、未知 ID、相邻用户消息以及普通文本边界；没有运行真实工具、CLI、tokenizer 或模型。[入口方法](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L58-L61) · [消息转换差异所在](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L81-L143)。读完仍接到 `_run_turn:416` 的 `_session_prompt_ids`。

<a id="session-prompt-ids"></a>

### 输入准备：先普通编码，再判断能否接回历史原始 token

旧版 `2f231865` 直接用 `_render_token_ids` 把消息与工具定义转成输入 token。新版 `18868a79` **新增 `_session_prompt_ids` 这一层**，原来的模板编码函数仍在内部使用。

```python
# _run_turn:415–423 的交接，省略其他处理
translated, tools_schema = self._translate(body)
prompt_ids = _session_prompt_ids(translated, tok, tools=tools_schema, session=s)
turn = await call_sglang_generate(prompt_ids, s, body, adapter=self, session_id=sid)
```

**为什么增加这一层？** 模型上轮生成的内容可能包含思考和工具调用。CLI 下次传回历史时，可能省略思考，或重新整理工具参数的表示。可见消息仍在，但重新套模板得到的 token 不一定等于模型当时真正使用和生成的 token。

本函数的输入因此除了消息、工具定义和 tokenizer，还包括当前 `Session`。会话的 `prompt_prefixes` 将两类材料保存到一起：`messages + tools` 用来匹配客户端传回的历史，`turn.prompt_ids + turn.output_ids` 提供那一轮的原始 token。

<a id="session-history-purpose"></a>

### 历史对不上时，本次消息仍然正常编码

这里比较的是 **CLI 本次请求带来的消息**与**同一会话已保存的消息历史**。当前这一轮模型还没有生成答案。本轮的 `_respond` 与 `manager.record_turn` 正常返回后，`_run_turn` 才会保存一份消息历史、工具定义和对应的原始输入／输出 token；`_session_prompt_ids` 读取这些材料。

只看“读取 README”的消息关系，暂时省略保持相同的系统消息和工具定义；A、B、C 各代表一条完整消息：

```text
已保存的消息历史：[A 用户要求读取 README，B 助手调用 read_file]
本次请求的消息：  [A 用户要求读取 README，B 助手调用 read_file，C 工具返回文件内容]
                  └───── 整段旧历史相同 ──────┘   └── 新内容 ──┘
```

- **能够对应，且其他检查也通过**：A、B 对应的历史部分使用保存过的原始 token，再接上 C 对应的新后缀。A、B 只保留一份，C 正常进入本轮输入。
- **所有候选都无法对应**：返回函数开头已经算好的 `rendered`，即本次全部消息与工具定义的普通编码结果。例如本次请求本来就带有 `[S 此前工作的摘要，D 接下来的问题]`，返回的就是 S、D 连同工具定义的编码；摘要必须已在请求里，本函数不会生成摘要，也不会额外执行工具。结果是供模型使用的 token ID 列表。

“对应”要求保存的整段消息历史与当前消息开头相同，源码检查为 `prefix.messages == messages[:depth]`；不是只要几句话相似、或任意部分重叠就算匹配。一个候选对不上，还会检查其他候选。

**为什么值得复用？** 已保存的原始输出 token 可能包含思考或特定的工具参数格式，而客户端传回的可见历史只保留了 B 这样的工具调用。利用可见消息确认“这是同一段历史”，才能接回当时真正的 token；找不到可靠对应时，就以本次请求提供的消息重新编码。这个选择决定的是历史部分的 token 来源，新增内容仍参与本轮输入。

<a id="session-prompt-branches"></a>

### 分支图：一个候选失败，就继续检查下一个

这里的主要分支属于 `_session_prompt_ids`；`_render_token_ids` 是它调用的模板编码函数。图中的编号表示本函数的执行位置，行号均属于 `slime/agent/adapters/common.py`。

```text
① 编码全部消息 → rendered                         common.py:102–104
   _render_token_ids(..., add_generation_prompt=True)
                         ↓
② 按历史长度从长到短，取下一个 prefix              105–107
   ├─ 没有候选了 → return rendered                 136：普通编码结果
   └─ 取到一个候选
          ↓
③ 历史相符，而且生成记录可用于接续？               108–116
   ├─ 否 → continue，回到②检查下一个候选
   └─ 是
          ↓
④ 同样的可见历史，是否还对应另一份不同的 token？   120–126
   ├─ 是 → 有歧义；continue，回到②
   └─ 否
          ↓
⑤ 只编码候选前缀 → anchor                         127–131
   _render_token_ids(..., add_generation_prompt=False)
   anchor 是否等于 rendered 开头的同长部分？
   ├─ 否 → continue，回到②
   └─ 是
          ↓
⑥ 能找到切口，而且切口后只剩留白？                 132–134
   ├─ 否 → continue，回到②
   └─ 是
          ↓
⑦ return 旧输入 token + 旧输出 token + 新后缀      135：接续结果
   turn.prompt_ids + turn.output_ids + rendered[end + 1:]
```

**这些是同一候选必须依次通过的检查。** ③④通过后，还必须进入⑤计算 `anchor`，再通过⑤⑥的前缀与切口检查，才能到⑦拼接；不能因为消息匹配就直接跳到⑦。`anchor` 是对这个候选覆盖的消息临时编码得到的 token 列表，不是匹配失败后另外找来的备用历史。

**`continue` 与 `return` 要分开看：** ③—⑥检查失败，只放弃当前 `prefix`，从②继续取候选；第一次找到完全合格的候选就在⑦返回。只有②已经没有候选可取，才返回普通编码结果。初始列表为空，也直接走②的返回分支。

### 每项检查具体负责什么

| 图中位置 | 实际检查或操作 | 不满足时，为什么不能用这一份历史 |
| --- | --- | --- |
| ③ 历史对应 | `prefix.tools == tools`；`prefix.messages == messages[:depth]`；`depth < len(messages)` | 工具或历史变了，或者当前没有新增消息，这份记录不适合作为本次接续前缀 |
| ③ 生成记录可用 | `finish_reason == "stop"`；`output_ids` 非空；最后一个 ID 属于 `tokenizer.all_special_ids` | 生成未按 `stop` 结束，或缺少可用于定位边界的末尾 token，不能直接拼上新消息 |
| ④ 排除歧义 | 相同消息、相同工具若还对应不同的 `prompt_ids` 或 `output_ids`，跳过这一候选 | 可见回复一样，隐藏思考等原始 token 可能不同；仅凭当前消息不能选定其中一份 |
| ⑤ 模板上下文一致 | 将 `messages[:depth]` 单独编码为 `anchor`，比较 `rendered[:len(anchor)] == anchor` | 某些模板会根据后面的消息改变旧消息格式；单独编码的前缀不一定与完整编码的开头相同 |
| ⑥ 确认切口 | 在 `anchor` 中从后往前找 `turn.output_ids[-1]`；其后解码并去掉留白后必须为空 | 找不到同一标记，或标记后还有实际内容，就不能把这里当作旧输出与新内容的分界 |

例如，较长候选的历史不匹配，并不意味着整个请求只能普通编码：它会继续检查较短候选，较短候选仍可能通过全部检查并被采用。这对应图中的“③ → ②”，不是“③ → 返回”。

<a id="session-render-calls"></a>

### 两处 _render_token_ids 各自做什么

`prefix` 是会话里已经保存的一份历史记录；`anchor` 是当前候选通过前面检查后，调用 `_render_token_ids(messages[:depth], ...)` 新算出的 token 列表。后者用于验证前者能否在 token 层面接上，并不构成另一种备选拼接策略。

| 调用位置 | 交给模板的消息 | `add_generation_prompt` | 结果用在哪里 |
| --- | --- | --- | --- |
| ① / 103 行 | 当前全部 `messages` | `True`，使用默认值 | 得到 `rendered`：既是没有合格候选时的完整返回值，也提供接续时的新后缀 |
| ⑤ / 127–129 行 | 当前候选覆盖的 `messages[:depth]` | `False`，明确传入 | 得到 `anchor`：只用于检查历史前缀和定位切口，不直接作为最终返回值 |

- 两次调用都带上同一份 `tools` 和会话模板参数，都以 `tokenize=True` 得到 token ID。
- `True` 请求模板准备下一条助手回复的开头；`False` 不额外请求这个开头，便于定位已经结束的历史。具体格式由 tokenizer 的模板决定。
- ①总是先执行；⑤只在当前候选通过③④后执行，可能随多个候选执行多次。确定切口后使用 `rendered[end + 1:]`，因为新后缀已包含在①的完整编码中。

沿用“读取 README”的局部例子：完整上游消息在没有本地历史时，按已下载的 Qwen 模板编码得到 **337 个 token**。另构造一轮带思考与文件读取调用的旧输出：旧输入 277 个 token、旧输出 43 个。当新的请求只追加工具结果、尚未追加用户追问时，新函数保留前 320 个原始 token，再接上工具结果和下一轮助手开头的 22 个 token，共 **342 个**；普通重新编码则是 332 个。旧输出是教学构造，由真实 tokenizer 编码，未调用模型生成。

这个例子也说明边界检查的必要：追加新的用户追问，会影响该 Qwen 模板对旧助手消息的渲染。本地默认参数下，它没有通过前缀检查，返回普通结果；明确改用 `preserve_thinking=True` 才通过。这是参数对照，不是所有模型或所有请求都一定复用的承诺。

**历史在哪里保存？** 仍在 `_run_turn`，而且发生在本轮生成、解析、响应与 manager 记录之后。下面两处不是相邻执行的代码：

```python
# 本轮开始准备输入：读取以前保存的材料
prompt_ids = _session_prompt_ids(translated, tok, tools=tools_schema, session=s)
...  # 生成、解析、响应与轨迹记录
# _run_turn:470–472：保存本轮材料，供后续请求使用
s.prompt_prefixes.append(
    PromptPrefix(copy.deepcopy(translated + [reply.manager_message]), copy.deepcopy(tools_schema), turn)
)
```

这里的保存用途是下轮输入接续；manager 的轨迹记录服务于之后的训练样本导出。本函数不修改会话，也不负责树的搜索或剪枝。

源码：[_session_prompt_ids，93–136 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L93-L136) · [取用与保存，415–472 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L415-L472)。现有连续性测试本次运行结果为 9 项通过、2 项 HTTP 测试未选取；本地 Qwen tokenizer revision 为 `995ad96eacd98c81ed38be0c5b274b04031597b0`。验证只涉及本地输入处理，没有运行真实 CLI 或模型。

<a id="call-sglang-version-calibration"></a>

### call_sglang_generate：一轮生成可能包含多次请求

接在 `_session_prompt_ids` 后面，调用仍为 `turn = await call_sglang_generate(prompt_ids, s, body, adapter=self, session_id=sid)`。输入 token 经 HTTP 发给 SGLang，最后交回一个 `TurnRecord`，这个职责保留。

`2f231865 → 18868a79` 的主要变化发生在函数内部：

| 关系 | 当前实现 |
| --- | --- |
| 一轮与一次请求 | 一轮可包含多次 `/generate` 请求；中间用局部 `captured` 累计原输入、生成 token、logprob 和附加资料 |
| 何时继续 | 有效响应的结束原因是 `abort`、开启 `partial_rollout` 且额度未耗尽时继续；HTTP 错误与校验错误不会走这条续生成分支 |
| 上下文预算 | 同时考虑会话和服务端限制；特定推测解码算法还预留草稿 token 空间 |
| 响应与返回 | 严格检查 token/logprob 与已请求的重放资料；`TurnRecord` 增加 `replay`、`weight_versions`、`spec_info`、`prefix_cache_info` |

```text
原输入 prompt_ids → captured（初始只有原输入）
                         ↓
                    POST /generate
                         ↓
                  校验并累计本次返回
                         ├─ abort + 开启续生成 + 还有额度
                         │       └─ 带上已生成部分，再次 POST
                         └─ 其余结束条件 → 一个 TurnRecord
```

例如原输入 `[101,102,103]`，本轮最多生成 `3` 个 token：第一次返回 `[701]`、结束原因 `abort`；开启续生成后，第二次发送 `[101,102,103,701]`，最多再生成 `2` 个。第二次返回 `[702]`、结束原因 `stop`，最终 `turn.prompt_ids=[101,102,103]`，`turn.output_ids=[701,702]`。这些数字是教学构造，已用当前原函数和本地 HTTP 测试服务验证。

`output_log_probs` 仍只逐个对应实际生成的 token。可选 `replay` 另外携带候选编号、相关概率或专家路由资料，因此旧版“只记录生成 token 的概率”的说法需要限定到具体字段。

<a id="call-sglang-responsibility-model"></a>

当前可先用三点建立职责模型：

- 按 SGLang 接口发送已有输入 token 和生成设置，请求生成。
- 读取并校验输出 token 及其 logprob，取得结束原因。
- 保留调用者传入的原输入，把本轮结果整理成 Slime 本地的 `TurnRecord`。

接口格式决定怎样与 SGLang 通信，`TurnRecord` 决定本地怎样把结果交给后续处理。`output_log_probs` 对应新生成的 token。累计容器、续生成、预算和重放结构属于下一层实现；先保留“一轮可能有多次请求”这个边界即可。

需要继续细读时，可看 [574–588 行的 captured 与 payload](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L574-L588)，弄清发出的数据；再接返回追加、续生成判断和最后打包。`trace_span` 的内部机制仍放在这段业务之后解释。

源码：[call_sglang_generate，524–700 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L524-L700) · [TurnRecord 字段](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L25-L54)。本轮 `test_token_contract.py` 相关测试 14 项通过，另以本地 HTTP 服务验证五个分支；重放套件因缺少 `wandb` 未运行，未验证真实模型生成。

### 保留的分工与本次核对边界

- `decode → parse_model_output → _build_reply → _respond → manager.record_turn` 的主调用关系保留。`parse_model_output`、Anthropic 的回复构造与响应函数、`record_turn` 的函数本体在这两个提交间相同；这不等于相关外部库或所有下游行为都未改变。
- 执行追踪包住模型请求和编码阶段，负责诊断记录；骨架显示其包围关系，按本轮阅读顺序在三个业务函数之后解释。`prompt_prefixes` 会影响下一次模型输入，也保留在骨架中。
- 当前只讨论已选定的 Anthropic 场景。新版 Codex 使用 Responses Adapter，其协议差异在对应范围内另行核对。

源码：[Anthropic 转换与协议方法](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L58-L143)。仓库还提供了 [原始 token 接续测试](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/test_agent/test_prompt_continuity.py#L80-L150)、[partial rollout 续接测试](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/test_agent/test_sampler_replay.py#L216-L325)和 [token/logprob 校验测试](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/test_agent/test_token_contract.py#L83-L126)。上述测试链接同时作为固定版本的源码依据；已实际运行的局部检查以各小节说明为准，没有运行真实 CLI 或 SGLang 模型推理。旧卡片中的 aiohttp、Transformers 版本仍保留原证据。

<a id="trace-infrastructure-boundary"></a>

### 理解业务处理后，再看 trace_span 的追踪包装

`trace_span` 可视为跨模块的执行追踪基础设施：多个业务阶段共用它记录起止、嵌套关系与附加结果。它在旧版已经存在；新版在 Coding Agent 的任务、沙箱准备、模型请求、评测与收尾等位置增加了接入，不能将工具本身和新增使用场景混为一谈。

当前骨架应先交代追踪的职责、包围范围与记录用途，便于对应真实源码：

- `agent_tokenize` 包住消息转换与输入编码；外层 `agent_model_turn` 再包含模型生成，解码和响应位于这两层追踪范围之外。
- 业务调用仍交出 `prompt_ids` 和 `turn`；追踪另外记录执行阶段的开始、结束、层级和附加信息。
- Trace 用于执行诊断；`TurnRecord` 与 manager 的轨迹用于保存生成数据和后续训练。知道这层分工后，可以继续阅读当前业务流程。

独立专题再展开“内部怎样做到”：记录的数据格式、上下文怎样跨 Adapter 事件循环传递、怎样导出与查看。骨架中的职责说明和后续机制讲解分层承担，不把当前读懂代码所需的含义全部推迟。

源码定位：[追踪工具](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345) · [模型请求中的接入](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L410-L423)。这些位置说明 Slime 端的接入，不代表已经验证 CLI、模型服务及远端环境都有完整的追踪记录。

<a id="trace-span-local-model"></a>

### trace_span 的局部模型：圈住代码，留下开始与结束

<a id="trace-span-data-structure"></a>

`s` 是当前会话的 `Session`；它的 `trace` 字段保存一个 `TraceHandle` 对象。这个对象指向 `carrier` 字典，字典里的 `events` 是保存事件的列表。图中只列本轮需要的字段：

```text
s                                      # Session 对象
└─ trace                               # TraceHandle 对象
   └─ carrier                          # dict：一份追踪的数据
      ├─ trace_id = "demo-trace"        # 这份追踪的标识
      └─ events = []                   # list：每个元素是一条事件 dict
```

因此，`s.trace.carrier["events"]` 就是沿这条路径取到**那个待追加的列表**。`carrier` 是字段名；在当前场景，它保存的是本地 Python 字典。

可以把这套功能理解为结构化的执行日志。本场景的 `TraceHandle` 已保存在 `s.trace`，`trace_span` 使用它向 `carrier["events"]` 追加事件。`trace_id` 标记事件属于哪份追踪，实际写入位置由对象中的 `carrier` 引用提供；`span_id` 则配对某一段执行的开始与结束。当前记录先保存在内存列表中，打印或导出由后续机制处理。

初始列表是 `[]`。下面只展示外层 `agent_model_turn` 对应的开始、结束两条事件，内层事件及公共元数据暂时省略；编号 `A` 和时间 `10.0 / 12.0` 是教学替换值：

```python
[
    {"type": "span_start", "name": "agent_model_turn", "span_id": "A", "ts": 10.0},
    {"type": "span_end",   "name": "agent_model_turn", "span_id": "A", "ts": 12.0},
]
```

- **进入 `with`**：为这一段执行生成编号，追加第一条字典，表示它从何时开始。
- **执行块内代码**：仍由调用处进行消息转换、编码和模型请求。
- **离开 `with`**：追加第二条字典，沿用编号 `A`，表示同一段执行何时结束。
- `name` 是阶段名称，同一个阶段可以多次执行；`span_id` 用来区分具体哪一次，并把其开始和结束配对。`ts` 是时间戳，后续可以据两者之差计算耗时。

实际写入最终落到 `_append_event` 的这一句：

```python
handle.carrier["events"].append(event)
```

当前外层场景的 `handle` 就是传入的 `s.trace`，`event` 是刚组好的事件字典。这里的可观察结果是**已有列表增加了记录**；`trace_span(...)` 返回的上下文管理器负责让这项工作发生在 `with` 的进入和退出处。模型结果仍由 `turn` 接住。

| 阅读层次 | 当前需要做到什么 |
| --- | --- |
| **现在需要读清** | `TraceHandle → carrier 字典 → events 列表`；一条事件的 `type / name / span_id / ts`；进入、退出各追加什么；包住了哪段业务 |
| **暂时认得作用** | `parent_span_id` 表示属于哪个外层阶段；`record_error=False` 不自动记异常详情，仍会传播异常 |
| **以后按问题展开** | ContextVar 栈怎样维护嵌套、`TraceSpanContext` 怎样补属性、多目标兼容、跨事件循环传递、导出和查看器 |

这轮先停在第一层。父子关系的实现、对象创建链和完整追踪系统不作为当前继续阅读的前提；读清第一层后，再决定是否需要向下追。

<details>
<summary>继续看嵌套调用与源码依据</summary>

在 `_run_turn` 中，先观察两个已经包住业务代码的阶段。下面假定 `s.trace` 已配置，省略空追踪分支及业务实参；顺序和缩进与 `common.py:412–425` 对应：

```python
with trace_span(s.trace, "agent_model_turn", record_error=False):
    target = bind_trace_carrier(s.trace.carrier)
    with trace_span(target, "agent_tokenize", record_error=False):
        translated, tools_schema = self._translate(body)
        prompt_ids = _session_prompt_ids(...)
    turn = await call_sglang_generate(...)

raw_output = tok.decode(...)
```

- `agent_tokenize` 记录转换和编码这一段，`agent_model_turn` 再圈住模型生成。解码和后续响应已经位于两层包装之外。
- `trace_span` 进入时记录 `span_start`，退出时记录 `span_end`，写入目标的 `carrier["events"]`。两个事件用同一个 `span_id` 配对；子阶段的开始事件通过 `parent_span_id` 指向外层。
- 这些事件保存名称、时间戳、关联标识及显式追加的属性。它们供后续查看过程与耗时，`TurnRecord` 则保存输入、生成结果及 logprob。

只运行上面的两层追踪、略去业务函数时，局部实验得到：

```text
agent_model_turn 开始
    agent_tokenize 开始
    agent_tokenize 结束
agent_model_turn 结束
```

这四个事件是局部实验结果；真实模型调用内部还可记录 `sglang_generate` 子阶段。事件当前写在内存字典中，导出与查看是后续处理。

`record_error=False` 只是不自动把异常类型和消息写入事件，异常仍会传播；没有 `s.trace` 时，调用处使用 `nullcontext()` 执行业务。当前先理解包装范围和记录去向即可，不同时展开跨事件循环的传递与完整导出链。

源码：[trace_span](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345-L425) · [写入事件](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L587-L613) · [真实调用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L410-L425)。局部实验核对了嵌套配对和异常传播，现有 Trace 测试 3 项通过；没有执行真实模型或 CLI。

</details>

<a id="parse-model-output-version-calibration"></a>

### 解析输出：Slime 的职责模型保留，依赖版本另行核对

`parse_model_output` 接住 `tok.decode` 得到的 `raw_output`，先分离思考文本，再从剩余内容提取工具调用，最后返回 `ParsedModelOutput(reasoning, text, tool_uses, ill_formed)`。工具调用描述记录名称和参数，尚未执行工具；调用方接着将 `parsed` 交给 `_build_reply`。

对比 `2f231865 → 18868a79`，Slime 的整个 `parsing.py` 内容相同，调用实参相同；调用处从 `common.py:347` 移到 `:426`。因此原来的“原始字符串 → 思考、正文、工具调用及格式标记”模型继续适用。

<details>
<summary>版本、局部验证与来源</summary>

[当前解析函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/parsing.py#L25-L56)与[调用位置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L425-L432)已对照。新版 [Docker 配置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docker/README.md#L12-L20)引用 SGLang `v0.5.21`；其中 Qwen 的参数类型识别和思考解析有扩展，不能据 Slime 文件相同推断全部依赖都相同。

以旧卡片的四组构造文本调用新版 Qwen 相关原方法体，纯文本、思考加工具、思考加正文以及缺少开头思考标记的输出均与原结果一致。已有解析测试 3 项通过，1 项因未安装完整 SGLang 而跳过。局部提取只保留本次所需方法和 Qwen 注册项，不是完整模型服务验证；其他模型与复杂 schema 的全部分支不在这次验证范围。

</details>

<a id="build-reply-version-calibration"></a>

### 回复组装：原有输入输出保留，内部消息增加一个下游用途

`_build_reply` 仍把 `parsed` 组织成 `Reply`：`wire` 保存协议回复材料，`manager_message` 保存内部 assistant 消息，`finish_reason` 保存内部命名的结束原因。对照 `2f231865 → 18868a79`，Anthropic 实现、返回类型与直接辅助函数都相同；原有心智模型和五种局部场景的输出继续成立，随机工具 ID 每次会变化。

新版 [调用方](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L432-L472)还会把 `reply.manager_message` 与 `translated` 一起复制进 `prompt_prefixes`，供后续输入接续。这个状态更新发生在调用方，`_build_reply` 本身仍只组装三项回复数据。组装后先回到格式标记回填、token 计数与模式判断，再交给 `_respond`。局部对照没有运行 HTTP、模型或工具。

<a id="before-respond-version-18868a79"></a>

### 进入响应函数前：接清三项准备

`_build_reply` 已经交出两份材料：`reply.wire` 供 `_respond` 组织协议响应；`reply.manager_message` 供 manager 留下内部记录。记录用的消息正是后者。

在调用 `_respond` 之前，`_run_turn` 还要完成下面的连续语句。这是当前函数内部的准备阶段，与旧版逻辑相同（`common.py:433–436`）：

```python
turn = dataclasses.replace(turn, ill_formed=parsed.ill_formed)
in_tok, out_tok = len(prompt_ids), len(turn.output_ids)
stream = body.get("stream") is True or "text/event-stream" in request.headers.get("Accept", "")
```

- `turn`：把解析器发现的格式状态补回本轮生成记录，供后续轨迹记录使用。
- `in_tok / out_tok`：取得输入、输出 token 数量，交给响应函数填写用量。
- `stream`：请求正文明确设置 `True`，或 Accept 头包含 `text/event-stream`，就选择流式响应。

之后才到 `common.py:442` 的 `_respond(request, body, reply, in_tok, out_tok, stream)`。当前 Anthropic 实现位于 `anthropic.py:71–75`，下一处要看清的是这些输入怎样变成普通 JSON 响应或流式事件。[当前源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L432-L442)

<a id="respond-record-version-calibration"></a>

### 响应与记录：接住两份不同材料

```text
reply.wire + 请求与 token 计数
    → AnthropicAdapter._respond → response（HTTP 响应对象）

translated + reply.manager_message + turn + sid
    → TrajectoryManager.record_turn → manager._trees[sid]（内存消息树）
```

`record_turn` 不接收上面的 HTTP 响应对象。它复用输入历史的已有路径，补上新消息，再为本轮 assistant 节点挂上内部消息与整份 `TurnRecord`，更新轮次计数，函数返回 `None`。

对比 `2f231865 → 18868a79`，这两个入口及直接处理逻辑未变。新版 `TurnRecord` 带有 `replay`、`weight_versions`、`spec_info`、`prefix_cache_info`，节点会随整份对象一起保留它们。另一个场景变化是：Coding Agent 未设置合并环境变量时默认传入阈值 0，关闭短 assistant 历史改写的特殊合并；共同历史的正常复用继续工作。单独创建 `TrajectoryManager()` 的类默认阈值仍为 1024。

**调用顺序和发送时机要分开看。** `_run_turn` 取得 `_respond` 的返回对象后，继续调试回调、轨迹记录、保存前缀，最后返回。普通分支这时才由 aiohttp 发送；流式分支已经在 `_respond` 内写出 SSE 事件。写出事件也不代表客户端业务代码已经消费。

<details>
<summary>当前定位与验证边界</summary>

- [Anthropic 响应入口与分支](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L71-L75)：普通渲染在 `:221–231`，SSE 渲染在 `:234–297`。
- [轨迹记录入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L381-L403)与[关闭特殊合并的条件](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L492-L493)。阈值由 [Coding Agent 配置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L81-L99)传入。
- [实际调用与前缀保存](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L442-L475)。17 项已有测试通过，其中 3 项使用本地模拟 HTTP 服务，其余验证轨迹记录。另以构造数据验证普通响应返回时尚未准备发送，以及本轮记录完整对象；没有运行真实模型、CLI 或训练。

</details>

<a id="prompt-prefix-save"></a>

### 前缀保存：本轮追加候选，后续请求检查取用

相对 `2f231865`，当前版本新增了 `PromptPrefix`、`Session.prompt_prefixes`，以及 `_run_turn` 收尾处的这句：

```python
s.prompt_prefixes.append(
    PromptPrefix(copy.deepcopy(translated + [reply.manager_message]), copy.deepcopy(tools_schema), turn)
)
```

三个字段依次保存本轮完整消息（输入历史加 assistant 回复）、工具定义和生成记录。前两份复制为独立副本；`turn` 引用同一对象，其中的原始输入、输出 token 留给后续输入准备使用。

```text
本轮：_run_turn 保存 PromptPrefix → 当前 Session 的 prompt_prefixes 列表
后续同一会话请求：_session_prompt_ids 读取候选 → 检查历史、工具和拼接边界
                                             ├─ 合格：保留旧 token，接上新后缀
                                             └─ 全部不合格：返回预先算好的普通编码
```

这里先保存候选，实际复用由后续请求判断。相邻的 `manager.record_turn` 服务于轨迹与样本整理，前缀列表则服务于后续模型输入；两处用途不同。[保存位置](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L463-L473) · [三个字段与 Session 列表](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L38-L57) · [后续取用](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L93-L136)

<a id="run-turn-step-by-step"></a>

## 从 _run_turn 读清一次模型请求

这一节从已经到达 Adapter 的 `POST /v1/messages` 开始。上游的 Harness 正在等待 CLI 结束；CLI 此时请求一次模型回复，HTTP 路由将请求交给 `BaseAdapter._run_turn`。先把这一次请求读通，再回查影响当前理解的前置代码。

这里有两个编排层：`generate` 组织整次 Coding Agent 任务，`_run_turn` 组织其中一次模型请求。一次 `_run_turn` 返回不代表 CLI 已退出，也不代表整道代码任务已经完成。

```text
CLI 发来 HTTP 请求
  → body / sid / Session
  → translated + tools_schema
  → prompt_ids
  → turn（本轮生成记录）
  → parsed → reply
  → response → 记录轨迹 → 清理本次登记
  → HTTP 层完成响应，CLI 继续运行
```

这张图表示处理与交接顺序。`response` 在非流式分支是待框架发送的响应对象，在流式分支则对应已开始写出的响应；具体区别见第 6 段。

<details>
<summary>源码入口与本节版本</summary>

本节按提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 静态核对；其他既有章节保留各自版本。

- HTTP 路由：[slime/agent/adapters/anthropic.py:48–49](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L48-L49)。
- 本节主线：[slime/agent/adapters/common.py:318–393](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L318-L393)。下文未特别注明的行号均指这个文件。
- 本场景的协议实现：[AnthropicAdapter](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L39-L75)。`_run_turn` 继承自基类，协议钩子由这个子类实现。

以下代码为指定范围的摘录或明确标注的裁剪。没有运行 CLI、沙箱或模型服务；示例输入与生成结果是教学构造。

</details>

### 1．读取请求，找到它所属的会话（325–338）

先只看三行：

```python
body = await request.json()
self._preprocess_body(body)
sid = self._session_id(request, body)
```

`request` 是 HTTP 框架交进来的请求对象。第一行读出 JSON 数据，得到字典 `body`；第二行做当前协议需要的预处理；第三行确定请求属于哪个会话。这个阶段尚未调用模型。

用一份最小请求贯穿后面的阅读：

```python
# 教学构造：请求头与 JSON 请求体
headers = {"Authorization": "Bearer sid-demo"}
body = {
    "model": "slime-actor",
    "system": "你是代码助手。",
    "messages": [{"role": "user", "content": "只回答：你好。"}],
    "tools": [],
    "max_tokens": 128,
    "stream": False,
}
```

在 Anthropic 分支，`_session_id` 从请求头取得 `sid-demo`，并非从 `messages` 推导身份。本例没有需要折叠的消息中间 system 项，预处理不会改变这些消息。

会话通过关闭检查和轮数检查后，代码取得 tokenizer、取出或创建 `Session`，并登记正在处理的请求：

```python
tok = self.tokenizer
s = self.store.setdefault(sid, Session())
task = asyncio.current_task()
self.inflight.setdefault(sid, set()).add(task)
```

此后带着三个东西继续：`body` 是本次输入，`sid` 是会话标识，`s` 保存该会话的默认采样配置和上下文预算。这里的 `Session` 不是对话历史容器；这次发送的历史仍在 `body` 中，轨迹由 `manager` 管理。

### 2．把输入整理成两路数据（341）

```python
translated, tools_schema = self._translate(body)
```

在本场景，调用进入 `AnthropicAdapter._translate`：系统指令和消息历史整理到 `translated`，可用工具的参数定义整理到 `tools_schema`。本例静态推导的结果是：

```python
translated = [
    {"role": "system", "content": "你是代码助手。"},
    {"role": "user", "content": "只回答：你好。"},
]
tools_schema = None  # 本例 tools 为空
```

换成有历史工具调用的请求，`translated` 还会包含相应调用与结果，`tools_schema` 则保存当前可用工具。两者不能合并成“工具信息”后略去其中一路。这一步只转换已经收到的数据，不执行工具；原有完整转换场景仍可按需回查。

<a id="render-token-ids"></a>

### 3．把两路数据编码成模型输入（342 → 58–73）

沿上一段继续，接下来的问题是：`translated` 和 `tools_schema` 怎样变成 `prompt_ids`？这里进入 `_render_token_ids`，返回后仍接回 `_run_turn` 的第 342 行。

```python
prompt_ids = _render_token_ids(translated, tok, tools=tools_schema, add_generation_prompt=True)
```

先认清赋值两侧的方向：右边把上一段的两份结果传入函数，左边的 `prompt_ids` 接住返回值。可以顺着这一条数据流读：

```text
translated（消息）＋ tools_schema（工具定义）
    → _render_token_ids：调用 tokenizer.apply_chat_template
    → 模板按模型所需格式组织内容，并编码为 token ID
    → 返回列表，由 _run_turn 命名为 prompt_ids
    → 下一行 call_sglang_generate 接收这份模型输入
```

实际函数位于 `slime/agent/adapters/common.py:58–73`，是模块函数：

```python
def _render_token_ids(
    messages: list[dict],
    tokenizer,
    *,
    tools: list[dict] | None,
    add_generation_prompt: bool = True,
) -> list[int]:
    """Render a chat-message list to token ids with the served chat template."""
    enc = tokenizer.apply_chat_template(
        messages,
        tools=tools,
        tokenize=True,
        add_generation_prompt=add_generation_prompt,
    )
    ids = enc["input_ids"] if hasattr(enc, "__getitem__") and "input_ids" in enc else enc
    return list(ids)
```

先把调用处的名字和函数内部的名字对上：

| `_run_turn` 提供的值 | `_render_token_ids` 内的名字 | 用途 |
| --- | --- | --- |
| `translated` | `messages` | 系统指令和消息历史；历史中的工具调用及其结果也在这一路 |
| `tok` | `tokenizer` | 提供当前模型的聊天模板与编码能力 |
| `tools_schema` | `tools` | 当前可用工具的定义，单独传入 `apply_chat_template` |
| `True` | `add_generation_prompt` | 请求模板准备下一条助手回复的开头 |

函数体可以分成两个动作：

1. **第 66–71 行：调用模板并编码。** `apply_chat_template` 接收消息和工具定义；`tokenize=True` 要求得到 token ID。格式由 tokenizer 的模板决定，工具定义怎样被放入提示也由支持工具的模板处理。本函数负责把两路数据传到那里。
2. **第 72–73 行：统一返回形式。** 如果 `enc` 是带 `input_ids` 的字典类结果，就取出该项；若它已经是 token ID 序列，就直接使用。最后 `list(ids)` 返回一个列表，由调用处的 `prompt_ids` 接住。

`add_generation_prompt=True` 的作用是为下一条助手消息准备前缀，实际添加什么、是否添加，取决于模板。助手的回复正文要在后续生成阶段获得。参数语义参照 [Hugging Face 聊天模板说明](https://huggingface.co/docs/transformers/chat_templating#add_generation_prompt)，工具参数参照[工具使用说明](https://huggingface.co/docs/transformers/chat_extras#passing-tools)。这里尚未选定真实模型模板来检查其渲染结果。

<a id="chat-template-two-actions"></a>

#### 把 `apply_chat_template` 单独拆开看

这里容易产生一个疑问：是不是“按照 tokenizer 内部的训练方式，把内容翻译一下”？可以保留“转换格式”这个方向，但更准确地说，是**按照模型训练时使用的对话格式来组织输入**。tokenizer 带着相应的聊天模板和编码规则，本次调用应用这些已有规则。

`apply_chat_template` 就是“应用聊天模板”。在当前 `tokenize=True` 的调用中，可以把它拆成两个动作：

```text
消息列表 + 工具定义
    │ 套用聊天模板：标明角色、消息边界，放入工具说明
    ▼
按模型所需格式组织好的提示文本
    │ token 编码：把内容转成编号
    ▼
token ID 序列
```

例如，输入包含系统要求“你是代码助手”、用户要求“读取 README.md”，以及工具 `read_file` 的定义。模板要把这些信息组织到提示里。下面只示意组织效果，方括号不是任何模型的真实控制符，工具说明的实际位置与写法由支持工具的模板决定：

```text
[系统消息开始]
你是代码助手。
[可用工具说明]
read_file：读取文件；必填参数 path，类型为字符串。
[系统消息结束]
[用户消息开始]
读取 README.md。
[用户消息结束]
[助手消息开始]
```

这里新增的是角色与边界的表达方式，以及工具定义在提示中的呈现方式；最后的助手开头为后续生成留出位置。它还没有写出助手的回复。

要单独观察第一个动作，可以在已配置好真实 `tok`、`translated` 和 `tools_schema` 的场景中这样调用：

```python
prompt_text = tok.apply_chat_template(
    translated,
    tools=tools_schema,
    tokenize=False,
    add_generation_prompt=True,
)
```

这是观察用法，相对实际源码只把 `tokenize` 改成 `False`，用 `prompt_text` 接住可读字符串。实际 `_render_token_ids` 使用 `True`，因此同一次调用还完成编码；外层再把编码结果统一成列表。此处没有执行真实 tokenizer，示意文本不能当作这段代码的实测输出。API 行为依据 [Hugging Face 聊天模板文档](https://huggingface.co/docs/transformers/chat_templating#using-apply_chat_template)。

把它接回前一步，两个转换的目标就分开了：

| 位置 | 转换目标 |
| --- | --- |
| `_translate` | 将请求协议中的消息和工具定义整理为统一的数据结构 |
| `apply_chat_template`，当前 `tokenize=True` | 将这些结构组织成模型所需的聊天格式，再编码为 token ID |

回到调用处，`prompt_ids` 接到的是第二项的编码结果，接下来才能作为生成输入。

<details>
<summary>局部运行样例：观察传入参数和返回值（使用仓库测试 tokenizer）</summary>

下面改用一条读文件请求，给出两条消息和一个完整工具定义。`FakeTokenizer` 来自同版本 `tests/test_agent/_fakes.py`；它按空白分词并记录工具参数，不能代表真实模型如何编码工具定义。

```python
translated = [
    {"role": "system", "content": "你是代码助手。"},
    {"role": "user", "content": "读取 README.md。"},
]
tools_schema = [{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "读取文件",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
}]
tok = FakeTokenizer()
prompt_ids = _render_token_ids(translated, tok, tools=tools_schema, add_generation_prompt=True)

# 实际返回的 prompt_ids
[1, 100, 5, 2, 101, 102, 5, 3]
```

这些数字属于仓库测试替身：`1 / 2` 分别标记 system / user 开头，`5` 标记消息结束，`100–102` 是按空白拆分后分配的文本编号，末尾 `3` 是助手开头。局部执行已确认两条消息和完整工具定义被传入；该替身只记录 `tools`，没有把工具定义编码进 token，因此这组数字不表示真实模型如何渲染工具。

</details>

回到第 342 行，现在得到的是一份模型输入 `prompt_ids`。本次读到这里即可接上下一段；具体模型的模板内容仍是后续问题。

### 4．请求本轮生成，取得生成记录（344）

```python
turn = await call_sglang_generate(prompt_ids, s, body, adapter=self, session_id=sid)
```

`prompt_ids` 是待送入模型的内容，`s` 和 `body` 提供默认配置、上下文预算与请求参数，`self` 提供模型服务等配置，`sid` 保持本次会话关联。正常路径中，这个函数向 SGLang 请求生成，交回一个 `TurnRecord`。

`turn` 包含输入、输出 token，输出 token 的 logprob 和结束原因等。它还不是发回 CLI 的协议 JSON。为了继续观察数据形态，本例假设模型成功生成“你好。”并正常停止；这是假设的生成结果，不是实际运行输出。

先按下面的执行地图定位，再沿顺序逐段阅读。每一段都连接“进来时有哪些值、代码改变了什么、交出什么、接下来去哪”；仅知道函数总职责，还不足以跟踪内部执行。

<a id="call-sglang-internal-flow"></a>

#### 把 `call_sglang_generate` 展开成六段

以下行号属于固定版本的 `slime/agent/adapters/common.py`。这张表是代码分段，不是六个新函数；后面可逐段深入，仍返回同一条请求主线。

| 段 | 源码行 | 进入时的材料 | 这段做什么、留下什么 |
| --- | --- | --- | --- |
| 1．准备生成设置 | 454–455，调用 416–439 | 当前会话 `session`、请求 `body`、协议参数名 | `_sampling_params` 合并设置，返回字典 `sp` |
| 2．检查剩余长度 | 457–468 | `prompt_ids` 的长度、会话上下文上限、`sp` | 有上限时计算剩余空间，再限制 `sp["max_new_tokens"]`；空间已耗尽则提前返回，不发送请求 |
| 3．准备请求信息 | 470–473 | Adapter 的服务地址、会话标识 | 得到 `sglang_url`、本次请求编号 `rid`、请求头 `headers`、超时设置 `timeout` |
| 4．请求并读取响应 | 475–496 | 输入编号、`sp` 及请求信息 | 进入 HTTP 请求上下文，取得响应 `r`；检查状态，再等待读取并解析 JSON，得到 `data` |
| 5．提取生成结果 | 497–501 | 响应字典 `data` | 取出 `output_ids`、`output_log_probs`、`finish` |
| 6．返回本轮记录 | 509–514 | 原输入编号和第五段得到的三个值 | 在本地创建 `TurnRecord`，返回 `_run_turn:344`，由 `turn` 接住 |

还有一条必须标在地图上的失败路径：HTTP 错误状态在第 495 行抛出异常；取消、连接错误或超时进入第 502–507 行，请求中止上游生成后重新抛出异常。它们不会正常走到第六段。长度耗尽的提前返回也不能因为是 `if` 就从执行图中删除。

先跟随一条正常请求，可以把变量连起来：

```text
session + body → sp
                  ↓ 剩余长度检查可能继续修改 sp
prompt_ids + sp + 请求信息
                  ↓ HTTP 请求；取得响应 r，再读取 JSON
                 data
                  ↓ 提取字段
output_ids + output_log_probs + finish
                  ↓ 加上原 prompt_ids
              TurnRecord → 回到 _run_turn 的 turn
```

第四段既要讲传输的数据，也要讲等待位置。只说“发给模型”会遗漏：哪个调用启动请求、哪个对象表示响应、读取响应时何时等待、失败时去哪里。当前先把这些位置标出，逐段读到这里时再展开；网络库内部的连接实现按实际问题继续追踪。

<a id="call-sglang-sampling-first"></a>

#### 第一段先回答：`sp` 从哪里来，里面发生了什么变化？

第 455 行的真实调用，按参数换行展示：

```python
sp = _sampling_params(
    session,
    body,
    max_token_keys=adapter.max_token_keys,
    stop_keys=adapter.stop_keys,
)  # 返回本次准备发送的生成设置字典
```

这里需要继续打开 `_sampling_params`，因为“生成设置怎样得到”正是当前问题。它在第 416–439 行，先放入固定默认项及会话默认设置，再读取当前请求的生成长度、采样和停止参数。

沿用读 README 后继续概括的请求，另外构造两项生成设置来观察这一段；消息和工具内容不变，下面只展示相关字段：

```python
session.sampling_defaults = {"max_new_tokens": 256, "temperature": 0.7}
body["max_tokens"] = 128
body["temperature"] = 0.2
# 当前 AnthropicAdapter 的参数名约定：
# max_token_keys = ("max_tokens",)，stop_keys = ("stop_sequences",)
```

在此输入下，`sp` 中这两个字段的结果是：

```python
# 输出节选；固定的其他设置仍保留在 sp 中。
{"max_new_tokens": 128, "temperature": 0.2}
```

对应到源码，变化不是一句笼统的“合并”：

| 字段 | 依次发生的变化 | 依据 |
| --- | --- | --- |
| `max_new_tokens` | 固定默认值 4096 → 会话默认值 256 → 与请求的 128 取较小值，得到 128 | 421–427 |
| `temperature` | 会话默认值 0.7 → 当前请求覆盖为 0.2 | 422、430–432 |

到这里仅在本地算出了一个字典，还没有发送 HTTP。第 439 行返回后，回到第 455 行完成赋值，接下来执行第 457 行的上下文长度检查；该检查可能再次压低生成长度。

```text
455：调用 _sampling_params
    → 416–439：算出 sp 并返回
    → 455：用 sp 接住
    → 457：接着检查剩余长度
```

这就是一个阶段需要记录到的程度：能对照输入算出局部结果，也知道为什么要进入子函数，以及返回后从哪里继续。其余五段沿同一方式逐段展开。下面保留的输出编号例子属于第五段，可在读到该处时回查。

<details>
<summary>执行地图与第一段的源码、验证</summary>

- 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：[完整函数](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L442-L514)、[生成设置合并](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L416-L439)、[Anthropic 参数名](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L45-L46)。
- 第一段的数值为教学构造，使用该版本的原函数做局部执行核对；输入沿用 README 场景，仅增加上面列出的生成设置。仅验证 `_sampling_params`，不代表后续预算检查、HTTP、模型生成或整条函数已经运行。

</details>

<a id="call-sglang-output-ids"></a>

#### 第五段的局部例子：响应里的 token 怎样进入 `turn.output_ids`

**与前一段的连接：** `prompt_ids` 是准备好的输入 token 编号列表，`call_sglang_generate` 把它放进 HTTP 请求。现在只增加一个问题：请求返回以后，生成的 token 编号在哪里，又怎样交回 `_run_turn`？

先把函数分成三段，作为阅读定位：

```text
准备本次生成设置 → 通过 HTTP 请求 SGLang → 整理响应并返回 TurnRecord
                                           本小节只展开这里的 output_ids
```

HTTP 响应提供的是 JSON 数据；`TurnRecord` 是本函数用这些数据创建的一轮记录。先沿 `output_ids` 这一条线走，其他字段的提取随后再读。

**1．拿到响应数据（496）。**

```python
data = await r.json(content_type=None)  # 等待读取响应体，并把 JSON 解析成 Python 数据
```

`r` 是这次 HTTP 请求的响应对象，`data` 接住解析后的内容。下面用仓库测试服务采用的字段形状构造一个小响应。编号和数值只是教学数据，不对应前一段 README 场景的真实模型结果，也不表示这些编号解码成某句话。

**2．沿字段取出生成的 token（497–499）。**

下面是可以单独运行的局部例子：用构造的 `data` 代替网络响应，其余三行提取代码保留源码写法。

```python
# 教学构造：只保留本小节需要的响应字段，不发送网络请求。
data = {
    "meta_info": {
        "output_token_logprobs": [[-0.2, 701], [-0.5, 702]],
        "finish_reason": {"type": "stop"},
    }
}

meta = data.get("meta_info") or {}  # 先取到生成信息这一层
output_token_logprobs = meta.get("output_token_logprobs") or []  # 再取出逐 token 的记录
output_ids = [x[1] for x in output_token_logprobs]  # 依次保留每项的第二个值
print(output_ids)
```

输出：

```text
[701, 702]
```

本例中的每一项都有两个位置：

```text
[-0.2, 701]
   ↑     ↑
  x[0]  x[1]
 logprob token ID
```

先只看第二个位置：第一项取出 `701`，第二项取出 `702`，按原顺序组成 `output_ids`。第一项的 logprob 数值如何理解、如何保存，留到下一小段。

**3．把这一列装进返回记录（509–514）。**

```python
return TurnRecord(
    prompt_ids=list(prompt_ids),          # 保存本次送入模型的编号
    output_ids=output_ids,                # 本小节追踪的生成编号放在这里
    finish_reason=finish,                # 结束原因，提取过程随后再读
    output_log_probs=output_log_probs,    # 与输出编号对应的 logprob，随后再读
)
```

这里只需要对上一行：`output_ids=output_ids` 左侧是 `TurnRecord` 的字段名，右侧是刚刚得到的列表。返回到 `_run_turn:344` 后，调用者用 `turn` 接住这份记录，于是可以用 `turn.output_ids` 取出生成编号。下一行的 `tok.decode(...)` 再使用这些编号还原文本。

这一步的新增关系是：**响应中的逐 token 记录 → 取出编号列表 → 存入 `turn.output_ids`。** 采样参数、上下文预算、结束原因、logprob 的含义以及取消清理，都按后续问题逐项展开。

<details>
<summary>本小节的源码位置与验证范围</summary>

- 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：[请求及响应读取](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L475-L496)、[字段提取](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L497-L501)、[返回记录](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L509-L514)。
- [TurnRecord 定义](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L28-L38)列出本轮记录的字段；[测试服务](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/_fakes.py#L156-L168)提供这里采用的响应形状。这里只用到各项的前两个位置，不假定所有真实响应都只有两个元素。
- 局部例子用 Python 3.12.3 执行核对，仅验证响应字段提取；未调用真实 tokenizer、HTTP 服务或模型。输入 token、响应中的 token 和最终文字的真实对应关系尚未取得。

</details>

### 5．把生成结果解析成回复（346–357）

```python
raw_output = tok.decode(turn.output_ids, skip_special_tokens=False) if turn.output_ids else ""
parsed = parse_model_output(
    raw_output,
    tools_schema=tools_schema,
    tool_parser_name=self.tool_parser,
    reasoning_parser_name=self.reasoning_parser,
)
reply = self._build_reply(parsed, turn.finish_reason, translated, tools_schema)
turn = dataclasses.replace(turn, ill_formed=parsed.ill_formed)
```

解码先将输出 token 还原成字符串；解析器再识别文本、推理内容和工具调用等结构；协议钩子 `_build_reply` 最后把这些结构整理成 `Reply`。

`reply.wire` 供下一段组织客户端响应，`reply.manager_message` 供最后记录轨迹。在本例的纯文本假设下，客户端内容块含有 `{"type": "text", "text": "你好。"}`，轨迹中的消息则是 `{"role": "assistant", "content": "你好。"}`。同一段回答面向两个消费者，形状不同。

随后代码统计输入和输出 token 数，并根据 `body.stream` 或请求头的 `Accept` 判断响应方式。解析出工具调用仍然不等于执行工具；执行由外部 CLI 接手。

### 6．组织 HTTP 响应（363）

```python
response = await self._respond(request, body, reply, in_tok, out_tok, stream)
```

在 Anthropic 分支，必须分清两条路径：

| 本次响应方式 | `_respond` 完成什么 | 后续交接 |
| --- | --- | --- |
| 非流式，本例采用 | 用 `web.json_response(...)` 构造 JSON 响应对象 | `_run_turn` 返回对象后，由 aiohttp 发送 |
| 流式 | 调用 `_render_stream`，准备响应并写出 SSE 数据 | 写出完成后回到 `_run_turn`，继续记录轨迹 |

所以准确的顺序是“先调用 `_respond`，它正常返回后才继续 `record_turn`”。不能把它概括成“所有情况下都先确认客户端收到回复，再记录轨迹”：非流式分支此时只是构造了响应对象。

### 7．记录轨迹，清理本次登记，回到 HTTP 层（384–393）

省略可选调试回调后，正常路径来到：

```python
self.manager.record_turn(
    sid,
    turn=turn,
    prompt_messages=translated,
    response_message=reply.manager_message,
    metadata={"sid": sid},
)
return response
```

轨迹管理器接收本轮 token 记录、规范化输入消息和助手回复，归到这个 `sid`。它没有把 HTTP 响应对象当作轨迹内容保存。

离开外层 `try` 时还会执行：

```python
finally:
    self.inflight.get(sid, set()).discard(task)
```

这只移除“本次请求正在处理”的登记，不关闭整个会话。handler 返回后，HTTP 框架继续完成响应交接；CLI 得到本次结果后可以继续发请求或执行工具。只有 CLI 整体退出，上游的 `HARNESS_CLS().run(...)` 才返回退出码，`generate` 才继续收集 diff。

### 第一遍读完，保留哪些边界

这次已经沿一条正常路径连接了请求、两路转换结果、token、生成记录、协议回复与轨迹。再标出三处会改变这条路径的检查即可：关闭的会话返回 503，超过轮数上限返回 429；`_respond` 抛出连接重置或取消时不会继续到正常的轨迹记录，进入外层 `try` 后的清理仍由 `finally` 负责。

下一次深读只选其中一个仍不清楚的交接，例如“`translated` 和 `tools_schema` 怎样参与模板编码”，再进入对应函数。无需为读懂本轮先通读所有辅助函数，也不因为现在列出了调用就视为已掌握它们的实现。

<!-- end-run-turn-step-by-step -->


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

<a id="swe-evaluation-contract"></a>

### 7.1 先看清评测交接：新环境、补丁状态与奖励

这一段按固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 补充。当前观察点是：`run_evaluation` 接收的已经是任务信息、代码补丁和评分预算；它不接收模型的 `TurnRecord`。对话轨迹留在 manager，代码是否完成任务由评测链路判断。 新版环境包装与返回位置见 [7.3](#evaluation-result-18868a79)。

<a id="two-grading-protocols"></a>

`run_evaluation` 先按协议选择评分器，一次调用只进入一个分支：

```text
run_evaluation(md, diff_text, timeout_sec)
├─ protocol == "swebench" → _grade_swebench
│  └─ 任务实例 → 评测脚本 → 测试日志 → 报告的 resolved → reward
└─ 其余值（本例 "scaleswe"）→ _grade_scaleswe
   └─ swepro / eval_cmd / f2p_script 按优先级选一种评分方式
```

- **共同接口**：两个实现都接收任务信息、补丁和时间参数，在新环境中应用补丁并评分，返回 `EvalResult`。
- **不同材料与规则**：ScaleSWE 从 `grading` 中选择一种评分材料；SWE-bench 需要 `grading["sweb_instance"]`，并根据评测报告评分。因此，不能只改主例的 `protocol` 就认为已经准备好另一分支的输入。
- **阅读取舍**：先展开 `scaleswe → eval_cmd`，因为它保留了新环境、补丁、测试与奖励的完整交接，同时只需把给定命令的退出码转为分数。SWE-bench 还需要理解任务实例如何生成测试规格与脚本，以及日志如何解析成报告并得到 `resolved`。先建立共同模型，再读这些协议差异，首轮需要处理的新概念较少。这里较简单的是选定的命令路径；如果目标是复现或排查 SWE-bench 基准，应优先读 `_grade_swebench`。

选定 `scaleswe → eval_cmd` 场景后，真正组织流程的是 `_grade_scaleswe`：

<a id="scaleswe-first-function"></a>

第一次局部展开从第 269 行的 `async with E2BSandbox(image) as ev` 开始，进入 `sandbox.py:281` 的 `E2BSandbox.__aenter__`。先只弄清 `image` 如何用于申请环境，以及 `ev` 是什么；具体代码和对象关系见 [7.2：配置怎样变成可操作的环境](#e2b-aenter)。看到创建调用的输入输出用途后返回主线，第 270 行才准备执行用户与目录权限；SDK 内部、重试算法和服务端部署在此保留边界。

```python
# 教学裁剪：只保留 eval_cmd 场景；无 swepro 和额外 pre_commands
async with E2BSandbox(image) as ev:
    await agent_sandbox.ensure_agent_user(ev, workdir)
    applied = await _apply_diff(ev, workdir, diff_text)
    if not applied:
        return EvalResult(0.0, False)
    r = await _run_eval_cmd(ev, workdir, eval_cmd, timeout_sec)
    return EvalResult(r, True)
```

- **任务镜像 → 新评测环境**：`ev` 与运行 CLI 的执行环境 `sb` 是不同实例。按照相同任务镜像及必要准备恢复基线，再将补丁应用进去。
- **补丁文本 → 工作区改动**：`_apply_diff` 先写补丁文件，再尝试应用。返回 `False` 时不执行测试，直接得到补丁失败结果。
- **测试命令 → 奖励**：本场景 `_run_eval_cmd` 执行指定命令，退出码为 `0` 时返回 `1.0`，其他正常返回的退出码得到 `0.0`。
- **两个结果 → 调用者**：`EvalResult` 的两个字段分别是 `reward` 与 `applied_cleanly`。退出环境上下文后，把结果交回 `generate`。

以“修复加法函数，然后运行测试”为教学假设：

| 条件 | 返回结果 | 能够说明什么 |
| --- | --- | --- |
| 补丁成功，测试命令退出码为 0 | `EvalResult(1.0, True)` | 命令型评分成功，补丁处理成功 |
| 补丁成功，测试命令退出码非零 | `EvalResult(0.0, True)` | 命令评分失败；尚不能仅凭分数区分断言失败和命令执行错误 |
| 补丁应用失败 | `EvalResult(0.0, False)` | 没有继续运行本次评分命令 |

这张表是静态推导，不是真实测试结果。空补丁在当前实现中也可返回应用成功；`applied_cleanly=True` 并不保证改动有效，更不表示测试通过。底层操作抛出的异常还可能直接向外传播，不能把所有故障都概括为零分。

Sandbox 在这里提供创建/回收、文件读写与命令执行能力，SWE 层决定评分规则。当前具体后端是 `E2BSandbox`；它退出时尝试回收资源，实际成功仍需运行证据。传给测试命令的 `timeout_sec` 也不是整个评测流程统一的截止时间。

<a id="grader-and-kubernetes"></a>

**选择 grader 并不决定是否使用 Kubernetes。** `_grade_scaleswe` 与 `_grade_swebench` 都创建 `E2BSandbox`，由它调用 E2B SDK 的 `AsyncSandbox.create`。当前源码展示的是“评分逻辑 → 沙箱操作接口 → E2B 或兼容服务”；服务端是否使用 Kubernetes，需要查看对应部署。不能把“会调用沙箱”直接理解为“这里实现了 Kubernetes 调度”。

<a id="sandbox-options-and-depth"></a>

<details>
<summary>补充：公开项目怎样运行，本轮需要了解多深</summary>

公开项目有多种运行方式；以下是有文档依据的例子，不是市场占比统计。

| 方式 | 公开依据 |
| --- | --- |
| 本机或服务器上的容器 | [SWE-bench 官方评测](https://www.swebench.com/SWE-bench/guides/evaluation/)使用 Docker 执行补丁测试 |
| 通过 SDK 使用托管沙箱 | [Open R1 的 E2B 案例](https://e2b.dev/customers/how-hugging-face-is-using-e2b-to-replicate-deepseek-r1)将代码题的执行结果用于奖励计算 |
| 用 Kubernetes 管理自建沙箱平台 | [OpenSandbox](https://github.com/opensandbox-group/OpenSandbox)支持 Docker 与 Kubernetes；[Kubernetes Agent Sandbox](https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/)提供环境管理与预热池 |

这些层次可以组合：应用通过 SDK 请求环境，服务端用 Kubernetes 编排任务，再由具体容器或虚拟机运行时执行。Kubernetes 编排与运行时隔离各有职责。

本轮先读清评测需要的创建、命令、文件、结果和退出接口，能解释“任务与补丁 → 新环境中的测试 → 分数与补丁状态”，并区分补丁失败、测试失败和环境故障。后续要研究部署时，再沿具体实现进入环境就绪、并发资源、网络、日志和回收；各类运行时的内部机制按问题深入。

</details>

<details>
<summary>本段源码入口与验证边界</summary>

- [统一入口与实际编排，swe.py:239–287](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L239-L287)。
- [SWE-bench 的任务材料，swe.py:113–137](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L113-L137)；[独立评测与报告评分，swe.py:440–492](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L440-L492)。
- [补丁应用，swe.py:299–313](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L299-L313)；[命令评分，swe.py:341–343](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L341-L343)。
- [Sandbox 接口，sandbox.py:28–59](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L28-L59)；[具体环境的进入与退出，sandbox.py:281–307](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L281-L307)。
- [E2B 兼容服务的环境要求，README:21–25](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/README.md#L21-L25)。[E2B 官方 SDK 说明](https://e2b.dev/docs/sdk-reference/python-sdk/v2.5.0/sandbox_sync)用于核对沙箱创建、命令和文件操作的能力；不作为本例服务端部署方式或本地 SDK 版本的证据。
- 仅核对静态调用与分支；未运行真实沙箱、pytest 或模型训练。其他评分协议按具体问题另行展开。

</details>

<a id="e2b-aenter"></a>

### 7.2 E2BSandbox.__aenter__：配置怎样变成可操作的环境

本节接在 `_grade_scaleswe` 的环境入口，源码仍使用固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：

```python
# swe.py:269–270；只摘录进入环境后的第一句
async with E2BSandbox(image) as ev:
    await agent_sandbox.ensure_agent_user(ev, workdir)
```

<a id="async-with-entry"></a>

这里先分清语法安排与业务动作。`with` 和 `async with` 都管理“进入 → 执行代码块 → 退出”；异步版本会等待异步的进入、退出方法完成：

| 语法 | 进入时 | 退出时 |
| --- | --- | --- |
| `with` | 调用 `__enter__()` | 调用 `__exit__(...)` |
| `async with` | 等待 `__aenter__()` | 等待 `__aexit__(...)` |

本例从正常进入到第一句的顺序，可以展开为下面三行。`manager` 是展示中间对象用的名称；省略了退出与异常处理，不能作为完整替换代码。

```python
manager = E2BSandbox(image)       # ① 构造本地对象，保存配置
ev = await manager.__aenter__()  # ② 运行进入方法，等它准备好环境并返回
await agent_sandbox.ensure_agent_user(ev, workdir)  # ③ 才开始原缩进块的第一句
```

- **先完成进入，再执行代码块**：第 ② 步成功返回后，结果才赋给 `ev`，然后执行第 ③ 步；进入时抛出异常则不会开始缩进块。
- **本例的进入动作**：整理创建配置 → 请求创建沙箱并等待 → 保存 SDK 对象与 ID → 返回 `self`。下文展开的就是第 ② 步内部。
- **异步等待的作用**：本次评测流程等待创建结果，挂起期间事件循环可以运行其他任务；当前缩进块仍须等进入完成。
- **代码在哪里运行**：缩进块仍由本地 Python 进程执行；后续通过 `ev` 提交的命令才在远端沙箱中运行。

<a id="ev-is-same-object"></a>

**`ev` 是进入方法返回的本地对象。** 本例 `__aenter__` 最后执行 `return self`，因此它和教学展开中的 `manager` 指向同一个 `E2BSandbox` 对象。

```python
# 正常进入后的关系；manager 是上面教学展开中临时起的变量名
ev is manager  # True：同一个对象，并未另建一个 ev 对象
ev.image       # "teaching/calc:v1"：仍保留构造时传入的镜像标识
```

- **先构造对象**：`E2BSandbox(image)` 在调用 `__aenter__` 之前创建本地对象，并通过 `self.image = image` 保存镜像标识字符串。
- **再补充状态**：进入方法按配置创建远端环境，将返回的 SDK 对象和沙箱 ID 保存到原对象的 `_sb` 与 `sandbox_id`，没有改写 `self.image`。
- **最后交给 `ev`**：`return self` 返回原对象，`as ev` 接住它。镜像的完整文件内容没有被复制到 `ev`；后续通过这个本地对象操作环境。其他上下文管理器可返回其他对象，具体看进入方法的返回值。

**输入是已保存配置的当前对象。** 沿用 `image="teaching/calc:v1"` 的教学例子，假设环境变量 `SLIME_AGENT_SANDBOX_IMAGE_METADATA_KEY=image` 已提供，其他配置为默认值：

```python
# __aenter__ 开始时的字段示意，不是额外执行的赋值
self.image = "teaching/calc:v1"
self.image_metadata_key = "image"
self.size = "md"
self.timeout = 3600
self._sb = None
self.sandbox_id = ""
```

`timeout` 是交给创建接口的沙箱存活时间设置，单位为秒；外层测试命令的 `timeout_sec=60` 此时没有传入。镜像名为教学占位值，规格 `md` 的具体资源含义由服务端决定。

**第一段：把配置整理为创建接口的 metadata（291–296）。** 此前的 282–287 行会检查镜像键名；缺少配置时直接报错。

```python
md = {self.image_metadata_key: self.image}

if self.size:
    prefix = self.image_metadata_key.rsplit("/", 1)[0] if "/" in self.image_metadata_key else ""
    size_key = f"{prefix}/size" if prefix else "size"
    md[size_key] = self.size
```

- 先写入镜像，再补入规格，本例得到 `{"image": "teaching/calc:v1", "size": "md"}`。
- 这里的 `md` 是新建的局部字典，和评分器中保存整份任务的 `md` 不是同一个对象。它没有包含补丁、工作目录或测试命令。
- 这些键需要与所使用服务的约定匹配。若镜像键是 `sandbox/image`，规格键就使用 `sandbox/size`。

**第二段：请求创建，接住 SDK 对象（298）。** `AsyncSandbox` 来自此前第 289 行的 `from e2b import AsyncSandbox`。

```python
self._sb = await self._rpc_retry(
    "create",
    lambda: AsyncSandbox.create(timeout=self.timeout, metadata=md),
)
```

- `AsyncSandbox.create` 接收本例的 `timeout=3600` 与创建参数，通过 SDK 和配置的服务通信。
- `lambda` 把一次创建操作交给 `_rpc_retry`；重试器执行它，符合条件的失败会重试，成功时交回创建结果。本节先保留这个职责，不进入重试实现。
- 创建接口返回的是用于操作远端沙箱的本地 SDK 对象，保存在 `self._sb` 中。

**第三段：保存标识，返回当前对象（299–300）。**

```python
self.sandbox_id = self._sb.sandbox_id
return self
```

- 将 SDK 对象上的沙箱 ID 保存到当前对象。
- 返回当前 `E2BSandbox` 对象，由外层的 `as ev` 接住。于是 `ev._sb` 就是上一段取得的 SDK 对象。
- 回到 `swe.py:270`，下一句才用 `ev` 准备执行用户与目录权限；补丁应用和评分继续在同一上下文中进行。

```text
ev：本地的 E2BSandbox 对象，即这里的 self
└─ ev._sb：本地的 AsyncSandbox SDK 对象
   └─ 通过服务接口操作远端沙箱
```

> 本函数把已保存的配置交给创建接口，保存操作沙箱所需的 SDK 对象，再把当前对象交回调用方。它返回的是环境操作对象；评测分数在后续执行测试时形成。

<details>
<summary>本节源码与验证范围</summary>

- [默认配置与构造器，sandbox.py:168–205](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L168-L205)；[本函数完整实现，281–300](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L281-L300)。
- [调用处，swe.py:269–270](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L269-L270)；[配置约定，README:21–25](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/README.md#L21-L25)。
- 局部运行使用真实 Slime 方法与替身 SDK：核对了普通键名、带前缀键名及空规格的参数；确认返回的 `ev` 就是原对象、SDK 对象被保存、ID 被复制；缺少镜像键名时在创建前报错。
- 进入顺序用 Python 3.12.3 再作局部验证：替身创建调用等待返回期间，代码块未开始；创建返回后才执行块内第一句，正常退出时调用回收。语言机制参照《流畅的 Python》第 2 版第 21 章“异步上下文管理器”；沙箱业务行为由上述固定源码核对。
- 未请求真实服务，没有验证镜像可用、远端创建、网络重试或真实回收。SDK 的具体通信与服务端实现仍在本节边界之外。

</details>

<a id="evaluation-result-18868a79"></a>

### 7.3 新版接续：测试分数和补丁状态怎样一起返回

本段使用固定版本 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。已知命令评测会返回 `1.0` 或 `0.0`，接下来要分清：父函数返回的 `True` 是不是也表示测试通过？

先分清返回值所在的层级：`_run_eval_cmd` 返回分数 `r`；`_grade_scaleswe` 组装 `EvalResult`；`run_evaluation` 原样交回该结果；最外层 `_generate` 解包取得 `reward` 和 `applied_cleanly`。因此，得到 `EvalResult` 的整体理解成立，具体取得它的位置应放在评分编排与统一入口这一层。

`_run_eval_cmd` 执行任务配置中已有的命令，按退出码评分：`0` 对应 `1.0`，其他正常返回的退出码对应 `0.0`。测试内容由命令决定；函数不负责设计测试。随后回到父函数的这两行，省略其余评分分支和追踪包装：

```python
r = await _run_eval_cmd(ev, workdir, eval_cmd, timeout_sec,
                        user=grading.get("eval_user", "agent"))
return EvalResult(r, True)
```

- `r` 填入 `reward`，表示本次评分。
- `True` 填入 `applied_cleanly`：前面的补丁失败分支已经提前返回，所以走到这里表示补丁处理成功。
- 因此，补丁成功但测试未通过时是 `EvalResult(0.0, True)`；补丁应用失败则提前得到 `EvalResult(0.0, False)`，不会继续运行测试。空白补丁按辅助函数的规则视为处理成功。

以上对应 [EvalResult 定义](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L79-L83)和[补丁判断、评分及返回](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L329-L340)。

新版的环境入口使用 `_evaluation_sandbox`，内部由工厂选择后端。第 340 行仍处于这个环境上下文中，正常返回的先后关系是：

```text
形成 EvalResult
    → 离开 async with，等待后端 __aexit__
    → run_evaluation 原样交回结果
    → _generate 解包为 reward, applied_cleanly
```

退出交接见[环境包装与分派入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/swe.py#L278-L298)，接收处见 [_generate](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L301-L307)。若评分或退出抛异常，这条正常返回路径会被打断；不能把所有异常都写成零分。后端退出接口被等待，也不等于已经验证了真实远端资源的回收。

本段以原始函数配合替身验证正常成功、测试零分、补丁失败、评分异常、无评分材料和退出异常，未运行真实沙箱或测试命令。

## 8．导出结果，再清理 Session

现在沿 `generate` 分清两个返回：

- **evaluation 模式：** [_eval_result](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L336)（`examples/coding_agent_rl/generate.py:336`） 返回用于结果统计的评测 Sample，不走训练轨迹导出。
- **训练模式：** `generate:237` 调 [BaseAdapter.finish_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L245)（`slime/agent/adapters/common.py:245`）；它关闭会话并等待在途请求，调用 [TrajectoryManager.get_trajectory](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L307)（`slime/agent/trajectory.py:307`） 得到 Sample 列表，再解码训练尾部填充 `response`。

轨迹导出第一遍走一条正常、没有 token 漂移的多轮链：[TrajectoryManager._chain_to_samples](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L479)（`slime/agent/trajectory.py:479`） → [TrajectoryManager._split_chain_into_builders](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L456)（`slime/agent/trajectory.py:456`） → [_SampleBuilder.append_turn](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L193)（`slime/agent/trajectory.py:193`） → [_SampleBuilder.to_sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L234)（`slime/agent/trajectory.py:234`）。解释完整 tokens、response_length、loss_mask、rollout_log_probs 如何对齐即可。后续工具/上下文 token 的 mask 与模型实际生成 token 的 mask 不同；每份输出 Sample 当前赋完整任务 reward。导出的 `response` 是多轮训练尾部，不一定只是最后一句回答。

**最终返回主线：** `generate` 确定返回值后，先执行 `finally` 的 [BaseAdapter.drop_session](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L278)（`slime/agent/adapters/common.py:278`）。它等待/取消在途请求，移除会话与轨迹，是 cleanup-only，不再次导出样本。 源码接着执行 `await asyncio.sleep(10)`，完成这段等待后，函数才真正把结果返回调用方；阅读任务耗时时要把它计入。

第一遍停止标准：能区分一次 HTTP 请求结束、CLI 进程结束、Session 导出与清理、整次任务结束。环境退出调用只表示进行了回收尝试，实际远端回收成功还需要运行证据。

<a id="sample-export-mainline-18868a79"></a>

### 8.1 新版接续：从会话配置和已有轨迹，走到 Sample 列表

本段依据固定版本 `18868a79`，沿 `evaluation=False` 的正常路径。评测已经给出 `reward`，manager 已经保存这次会话的轨迹；`shutdown_session` 先按“关闭入口并处理未结束的请求”理解，跨循环机制留待后续。

`finish_session` 接着完成三项交接：

1. **取会话配置。** `session = self.store.pop(sid, None)` 取出并移除配置，读取 `max_context_tokens` 作为样本长度上限。此时轨迹还在 manager 中。
2. **把轨迹导出为样本。** `manager.get_trajectory(...)` 按 sid 找到消息树，逐条路径委托组装，汇总 `Sample`，给每个样本赋 `reward`，再移除 manager 中这次会话的轨迹登记。
3. **补文本并交回列表。** Adapter 按每个样本的 `response_length` 解码末尾 token，写入 `response`，最后 `return samples`。

以下为主流程的教学裁剪，省略参数和长度读取细节：

```python
await self.shutdown_session(...)
session = self.store.pop(...)
max_sample_tokens = ...
samples = self.manager.get_trajectory(...)
for s in samples:
    rlen = int(s.response_length or 0)
    s.response = self.tokenizer.decode(...) if rlen and s.tokens else ""
return samples
```

读这段时，把三份信息分开：**配置在 store，轨迹在 manager，最终数据在返回的 samples 中。** `base_sample` 提供编号、prompt 等基础字段；轨迹组装提供 token、mask 与 logprob；评测提供 reward；Adapter 最后补上文本。

返回的是样本列表，可能为空、一个或多个；导出过程本身没有执行训练。外层 `_generate` 随后检查空结果、补退出信息和截断状态，并最终清理会话。本段在样本列表交回处收束；token 拼接、分段、mask 算法和跨线程细节继续保留为后续问题。

<details>
<summary>本段源码与版本边界</summary>

- [实际调用与返回后的处理](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L325-L349)。
- [finish_session](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L314-L345) 与 [get_trajectory](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L405-L442)。
- [新版样本字段](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L311-L359)还包含权重版本、统计、追踪与可选 replay 信息；本段没有展开其内部实现。
- 本段为静态源码讲解，没有新增真实模型、沙箱或训练运行。

</details>

## 再补一条失败路径

用同一书签，假设步骤 2 的 `prepare_workspace` 在沙箱已交出后抛出 `RuntimeError`：环境上下文退出 → `generate` 的 `except Exception` 生成 ABORTED 结果 → `finally` 清理 Session。只要把异常怎样返回、谁做环境与会话清理说清，就完成第一条异常链。

随后按问题选读：等待 CLI 超时返回 `-1` 与环境回收、客户端取消与服务端 abort、上下文预算耗尽、轨迹导出为空。不要假设等待函数返回超时就已经终止 CLI。

## 什么时候算读通 4.1

拿上面的假设任务，连续回答以下问题：谁准备模型入口和 Session？谁创建环境、配置并启动 CLI？外层在哪等，模型请求怎样在等待期间发生？一轮请求怎样返回并记录？CLI 退出后 diff 和评分从哪里来？评测和训练返回有何不同？失败后环境与 Session 由谁处理？

配套先读 [tests/test_agent/test_adapters.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_adapters.py#L1)（`tests/test_agent/test_adapters.py:1`） 中工具调用 → 工具结果 → 再次请求 → 导出的 fixture/断言，及 [tests/test_agent/test_trajectory_manager_branching.py](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_agent/test_trajectory_manager_branching.py#L1)（`tests/test_agent/test_trajectory_manager_branching.py:1`） 中正常多轮链的断言。这里的文件/符号与调用关系是静态核对；本轮没有运行真实 CLI、E2B、SGLang、训练或源码仓库测试。

代码片段来自 [THUDM/slime 的固定提交](https://github.com/THUDM/slime/tree/22a89f96835969a47055a659c588f46151f8b07a)，许可见 [Apache 2.0](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/LICENSE)；片段为阅读上下文中的摘录，不是独立可执行脚本。
