---
title: "S15 Integrated Harness：把各层机制接回完整循环"
weight: 150
aliases: ["/projects/learn-claude-code/s20/"]
summary: "以本地综合运行时理解消息、上下文、SYSTEM、工具池、权限与异步事件如何组装成一条主循环。"
ShowToc: false
compactDiagramLegends: true
---

{{< chapter-outline id="s15-chapter-outline" title="S15 本章目录" >}}

## 1. 定位：这一次真正把前面各层接起来 {#harness-position}

### 1.1 我想弄清楚的问题 {#harness-question}

前面各章已经分别理解工具、记忆、压缩、任务、团队和 MCP。但很多脚本只从基础循环增加一个机制；博客总图中的旧节点主要帮助复习，还不是一份合并运行时。

S15 的重点是：**这些机制在本地实际从哪里进入同一轮请求，怎样共用消息、配置与执行入口，异步结果又怎样回到主循环？** 新增的主要是组装与协调，不是再发明一种推理循环。

源码基准为本地 `ce8f9f1` 的 [s15_integrated_harness/code.py](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s15_integrated_harness/code.py)。完整函数按本地源码摘录，局部摘录与伪代码另行标记；按 [MIT 许可](/examples/s15-repo/NOTICE.txt)使用。

本次先聚焦组件组装与正常消息流，不展开 Error Recovery。本地版本仍保留相关请求包装，以下只把它视为模型调用入口的内部细节。

这里的“一个循环”指主 Agent 的统一调度骨架。subagent 和 teammate 仍有自己的 messages 与模型循环，后台进程／调度线程也有独立生命周期；它们通过工具返回或事件与主循环协调。

### 1.2 从上游配图学什么，哪些要看源码 {#harness-upstream}

本地上游 [system-architecture.svg](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s15_integrated_harness/images/system-architecture.svg) 把主循环放在上方，下方按四组组件说明挂接位置。这种分层适合综合章；本博客沿用它的分组思路，演化颜色继续按已有规则解释。

| 上游图的分组 | 本章对应的接入位置 |
|---|---|
| 上下文与知识 | 请求前的压缩、Memory 召回、Skills 目录、SYSTEM 组装 |
| 治理与扩展点 | PreToolUse / PostToolUse、权限、Stop；本次不展开错误恢复 |
| 持久工作 | TODO、任务图、后台 Bash、Cron |
| 团队与插件 | subagent、Teams／协议／worktree、MCP 工具池 |

分组图回答“模块归属”，源码再回答“执行先后”。例如 MCP 工具池在调用模型前组装，后台完成通知有请求前与工具结果回传时两个收集位置，`compact` 是单独分支。

本地的绝大多数机制直接定义在这一份 code.py 中，Memory 另通过 load_memory_runtime 装载 S09。这里的“组装”是共享配置、状态与接口，再串入主循环；并不是程序自动导入前面每个章节就完成整合。

<details>
<summary>查看上游分层图原图</summary>

![上游 S15 分层架构图，完整保留本地资源](/examples/s15-repo/system-architecture.svg)

这张图沿用上游主题配色，不使用本博客的演化图例；下面三张教学图才以 S14 为参照标记变化。

</details>

### 1.3 三图对照：保留上一轮，再解释真实组装 {#harness-architecture}

#### 图 1：回顾 S14 的默认总览

{{< architecture from="/projects/learn-claude-code/s14" width="1200" src="images/mcp-agent-integration.svg" mode="baseline" modified="prepare,model,decision,handler,tools,system,pre-event,compact-processor,memory-recall,memory-persist,background-collect,cron-interface,team-interface" folded="mcp-connect,mcp-registry,mcp-pool,mcp-call" label="图 1：复用 S14 原图，标记综合运行时中会调整的已有接口与 MCP 内部合并" caption="图 1：节点和连线仍是 S14 默认总图，未加入 S14.3.6 的扩展示意。橙色是 S15 将调整或真实接入的请求、权限、记忆、压缩与事件接口；四个灰色 MCP 内部节点在图 2 合并到工具池与同步分发，原机制保留。" >}}

#### 图 2：综合运行时的接入总图

{{< architecture-explorer id="s15-harness-explorer" modules="explorer.json" roles="function-roles.json" width="1200" src="images/harness-agent-integration.svg" legend="evolution" label="图 2：保留已有主循环，接入请求组装、动态工具池、同步与后台工具、Cron 和团队事件，共用主会话锁" caption="图 2：沿用 S14 的主线与已有模块位置。右侧分别解释请求组装、工具池、事件桥和后台执行；原 MCP 发现与调用细节回到 S14，实际 tools 与 handlers 合入本章组装。橙色是整合后有变化的旧接口；已有机制的内部算法保留章节来源。" >}}

这张图以 S15 的组装与消息流为阅读范围。图 1 的历史学习骨架含 Stop 反馈续轮，本地 S14／S15 未实现这条控制路径；图 2 校正为正常收尾，蓝色 Stop 保留其实际统计职责。已学模块保留接口和章节来源；内部方法是否相同仍以本章代码为准。S14 的 Tool Search 扩展没有被合入 S15，MCP 仍是 mock server 加全量发现工具池。

#### 图 3：组装一轮请求的最小核心

{{< architecture figureId="s15-harness-core" functionExplorer="s15-harness-explorer" width="1000" src="images/harness-core.svg" legend="evolution" label="图 3：事件注入、上下文整理、配置与工具池组装、模型响应、权限分发、结果回传和正常收尾，入口用锁串行化" caption="图 3：上方回答一轮请求需要哪些输入，下方区分有 tool_use 的执行回传、无 tool_use 的正常收尾与外层事件入口。所有函数来自本地源码；点击可就近查看实现。本次只展开组装与消息流，完整 agent_loop 在正文末尾。" >}}

{{< mechanism-function-index id="s15-harness-functions" explorer="s15-harness-explorer" >}}

## 2. 请求前：消息、上下文与可用能力一起准备 {#harness-request}

### 2.1 三份输入与几种不同状态 {#harness-inputs}

| 数据 | 交给谁／怎样使用 |
|---|---|
| messages | 模型对话：用户输入、assistant、tool_result、通知和压缩后历史 |
| context | Harness 当前状态，用于组装 SYSTEM，按历史选择记忆 |
| tools | 模型本轮可见 schema；对应 handlers 留在 Harness |
| active_request | 压缩后仍需保留的当前用户／定时工作要求 |

`agent_lock` 序列化用户回合与异步回合，避免它们同时改主 history。队友用自己的历史与线程，不复用主 messages；任务文件、邮箱和 MCP 注册表另外管理。

### 2.2 每轮先注入 Cron 与后台结果 {#harness-events}

**所属层：** Harness 消息入口。每次 while 迭代先 consume_cron_queue，把 prompt 写为 Scheduled user 消息，同时扩展 active_request；再 inject_background_notifications。

```python
def consume_cron_queue() -> list[CronJob]:
    with cron_lock:
        fired = list(cron_queue)
        cron_queue.clear()
    return fired
```

```python
def inject_background_notifications(messages: list):
    notes = collect_background_results()
    if notes:
        messages.append({"role": "user", "content": [
            {"type": "text", "text": note} for note in notes]})
```

Cron 触发的是待执行 prompt，后台通知报告已经启动命令的 completed / failed 状态。主循环还在 TODO 计数达到 3 时插入提醒；计数在普通同步工具之后更新，不能简单理解成每三次模型请求提醒。

### 2.3 prepare_context：完整预算管线接在请求前 {#harness-prepare}

**输入：** messages 与 active_request。**副作用：** 用切片更新同一个 messages 列表，保证调用者持有的主历史也变更。先限制大结果、裁历史，超限才缩旧结果；仍过大再处理新结果或调用摘要。

```python
def prepare_context(messages: list, active_request: str) -> list:
    # Every LLM turn enters through the same context budget pipeline.
    messages[:] = tool_result_budget(messages)
    messages[:] = snip_compact(messages)
    if estimate_size(messages) > CONTEXT_LIMIT:
        target = int(CONTEXT_LIMIT * 0.8)
        messages[:] = micro_compact(messages, target)
        if estimate_size(messages) > CONTEXT_LIMIT:
            messages[:] = fit_tool_results(messages, target)
    if estimate_size(messages) > CONTEXT_LIMIT:
        messages[:] = compact_history(messages, active_request)
    return messages
```

| 阶段 | 本地实现的职责 |
|---|---|
| tool_result_budget | 最新工具批次超过预算时保存大输出、保留预览 |
| snip_compact | 归档历史并裁中段，尽量保持调用与结果相邻 |
| micro_compact | 超限时压缩较早且已读取的结果，保留最近 3 项 |
| fit_tool_results | 仍超限时转存较大结果，包括未读取的新结果 |
| compact_history | 最后归档并请求事实摘要，保留 Authoritative request |

源码通过字符长度估计容量；50,000 是本例估算阈值，不是模型真实 token 上限。摘要与记忆选择都可能产生额外模型调用，纯字符串 SYSTEM 组装本身不会调用模型。具体压缩方法可回看 [S08](../s08/)，本章调用顺序以上面源码为准。

### 2.4 update_context：每轮刷新，而不只在用户入口召回 {#harness-context}

**所属层：** 运行状态收集。读取 Memory 索引，按当前 messages 加载相关正文，收集已连接 MCP 与活动队友名称。

```python
def update_context(context: dict, messages: list) -> dict:
    return {
        "memory_catalog": MEMORY_RUNTIME.read_memory_index(),
        "memories": MEMORY_RUNTIME.load_memories(messages),
        "connected_mcp": list(mcp_clients.keys()),
        "active_teammates": list(active_teammates.keys()),
    }
```

S15 直接导入 S09 runtime，并共享当前 client、MODEL、WORKDIR 与 .memory 路径。`load_memories` 有记录时会用模型选相关项，异常时回退关键词；不是每轮把全部记忆读进 SYSTEM。

```python
def load_memory_runtime():
    """Load s09 once and share this host's client, model, and workspace."""
    path = Path(__file__).resolve().parents[1] / "s09_memory" / "code.py"
    spec = importlib.util.spec_from_file_location(
        f"integrated_memory_{id(client)}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load memory runtime from {path}")
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    runtime.WORKDIR = WORKDIR
    runtime.MEMORY_DIR = WORKDIR / ".memory"
    runtime.MEMORY_INDEX = runtime.MEMORY_DIR / "MEMORY.md"
    runtime.client = client
    runtime.MODEL = MODEL
    return runtime
```

函数返回一个新 context；旧参数没有被合并保留。`active_teammates` 虽在 context 收集，当前 assemble_system_prompt 没有把这个字段追加进去。不要把“收集了状态”当成“模型已经看到了状态”。

### 2.5 assemble_system_prompt 与 Skills 目录 {#harness-system}

**所属层：** 请求背景拼接。固定身份、工具、任务、团队、workspace、记忆和压缩规则，加当前时间、Skills 目录、Memory 目录与选中的正文，以及 MCP 名称。

```python
def list_skills() -> str:
    if not SKILL_REGISTRY:
        return "(no skills found)"
    return "\n".join(
        f"- {skill['name']}: {skill['description']}"
        for skill in SKILL_REGISTRY.values())
```

```python
def load_skill(name: str) -> str:
    skill = SKILL_REGISTRY.get(name)
    if not skill:
        available = ", ".join(SKILL_REGISTRY.keys()) or "(none)"
        return f"Skill not found: {name}. Available: {available}"
    return skill["content"]
```

```python
def assemble_system_prompt(context: dict) -> str:
    # The system prompt is rebuilt each turn from live context. This is where
    # memory, skill catalog, MCP state, and active teammates become visible.
    sections = [PROMPT_SECTIONS["identity"],
                PROMPT_SECTIONS["tools"],
                PROMPT_SECTIONS["tasks"],
                PROMPT_SECTIONS["teams"],
                PROMPT_SECTIONS["workspace"],
                PROMPT_SECTIONS["memory"],
                PROMPT_SECTIONS["compaction"]]
    sections.append(f"Current time: {datetime.now().isoformat(timespec='seconds')}")
    sections.append("Skills catalog:\n" + list_skills() +
                    "\nUse load_skill(name) when a skill is relevant.")
    if context.get("memory_catalog"):
        sections.append(f"Memory catalog:\n{context['memory_catalog']}")
    if context.get("memories"):
        sections.append(f"Relevant memory records:\n{context['memories']}")
    mcp_names = list(mcp_clients.keys())
    if mcp_names:
        sections.append(f"Connected MCP servers: {', '.join(mcp_names)}")
    return "\n\n".join(sections)
```

Skills 本例从 WORKDIR/skills 下扫描 SKILL.md，目录写 SYSTEM，完整内容通过 load_skill 的 tool_result 进入 messages。它是本地教学 loader，不包含 S07 讨论的现代 Skills 全部配置与执行能力。

各段 SYSTEM 写什么，以及哪些输入放在 messages／tools，见 [S15.1 System Prompt：模型需要哪些指令与背景](system-prompt/#prompt-composition)。完整组装函数与执行顺序仍在本章维护。

### 2.6 26 个 schema 与 25 个 handler 怎么组装 {#harness-pool}

按当前源码计数，`BUILTIN_TOOLS` 有 **26 个 schema**，`BUILTIN_HANDLERS` 有 **25 个映射**；差的一项 compact 在 agent_loop 中单独处理。上游 README 对比表写 25，本文以实际 schema 列表为准。

| 工具组 | 模型工具名 |
|---|---|
| 基础文件／Shell，5 项 | bash、read_file、write_file、edit_file、glob |
| 单 Agent 能力，4 项 | todo_write、task、load_skill、compact |
| 任务，6 项 | create_task、update_task、list_tasks、get_task、claim_task、complete_task |
| 定时，3 项 | schedule_cron、list_crons、cancel_cron |
| 团队，6 项 | spawn_teammate、list_teammates、send_message、request_shutdown、request_plan、review_plan |
| 目录与外部接入，2 项 | create_worktree、connect_mcp |

工具 schema 给模型；Python 函数留在分发表。`task` 直接绑定 spawn_subagent，load_skill 绑定 loader，具体任务包装绑定 owner="agent"。名字和 run_ 前缀不决定自动注册。

下面是源码的完整基础分发表：

```python
BUILTIN_HANDLERS = {
    "bash": run_agent_bash,
    "read_file": run_agent_read,
    "write_file": run_agent_write,
    "edit_file": run_agent_edit,
    "glob": run_agent_glob,
    "todo_write": run_todo_write, "task": spawn_subagent,
    "load_skill": load_skill,
    "create_task": run_create_task, "update_task": run_update_task,
    "list_tasks": run_list_tasks,
    "get_task": run_get_task,
    "claim_task": run_claim_task, "complete_task": run_complete_task,
    "schedule_cron": run_schedule_cron,
    "list_crons": run_list_crons,
    "cancel_cron": run_cancel_cron,
    "spawn_teammate": run_spawn_teammate,
    "list_teammates": run_list_teammates,
    "send_message": run_send_message,
    "request_shutdown": run_request_shutdown,
    "request_plan": run_request_plan, "review_plan": run_review_plan,
    "create_worktree": run_create_worktree,
    "connect_mcp": run_connect_mcp,
}
```

**所属层：** 动态组装。每轮复制内置定义和函数映射，再适配已连接 MCP 工具，并同步宿主策略；MCP 仍按 S14 的发现／原名调用方式工作。

```python
def assemble_tool_pool() -> tuple[list[dict], dict]:
    """Merge builtin tools + all MCP tools into one pool."""
    global mcp_tool_policies
    tools = list(BUILTIN_TOOLS)
    handlers = dict(BUILTIN_HANDLERS)
    policies: dict[str, str] = {}
    origins = {tool["name"]: f"built-in tool {tool['name']!r}"
               for tool in tools}
    for server_name, mcp_client in mcp_clients.items():
        safe_server = normalize_mcp_name(server_name)
        for tool_def in mcp_client.tools:
            raw_name = tool_def["name"]
            safe_tool = normalize_mcp_name(raw_name)
            prefixed = f"mcp__{safe_server}__{safe_tool}"
            if len(prefixed) > 64:
                raise ValueError(
                    f"MCP tool name is longer than 64 characters: {prefixed}"
                )
            origin = f"MCP tool {server_name!r}/{raw_name!r}"
            if prefixed in origins:
                raise ValueError(
                    "MCP tool name collision after normalization: "
                    f"{prefixed!r} maps both {origins[prefixed]} and {origin}"
                )
            schema = tool_def.get("inputSchema", {})
            if not isinstance(schema, dict) or schema.get("type", "object") != "object":
                raise ValueError(f"Invalid input schema for {origin}")
            origins[prefixed] = origin
            tools.append({
                "name": prefixed,
                "description": tool_def.get("description", ""),
                "input_schema": schema,
            })
            handlers[prefixed] = (
                lambda *, client=mcp_client, tool=raw_name, **kwargs:
                client.call_tool(tool, kwargs)
            )
            policies[prefixed] = MCP_HOST_POLICY.get(
                (server_name, raw_name), "confirm"
            )
    mcp_tool_policies = policies
    return tools, handlers
```

因此普通任务、Skills、subagent、Team 和 MCP 的可调用入口确实位于同一个主工具池；它们的内部生命周期并不因此变成一样。连接新 MCP server 后，下一轮重建才更新模型可见 schema。

## 3. 执行：统一入口，保留每类工作的生命周期 {#harness-execution}

### 3.1 call_llm：SYSTEM、messages、tools 汇成一次请求 {#harness-model}

**所属层：** 模型请求包装。输入当前历史、context 与本轮 tools；SYSTEM 由 assemble_system_prompt 拼接，实际 SDK 请求接收这三份输入。以下保留完整函数，with_retry 与状态对象内部暂不展开。

```python
def call_llm(messages: list, context: dict, tools: list,
             state: RecoveryState, max_tokens: int):
    system = assemble_system_prompt(context)
    return with_retry(
        lambda: client.messages.create(
            model=state.current_model,
            system=system,
            messages=messages,
            tools=tools,
            max_tokens=max_tokens),
        state)
```

```python
def has_tool_use(content) -> bool:
    # Do not rely on stop_reason alone; the concrete tool_use block is the
    # continuation signal used by the loop.
    return any(getattr(block, "type", None) == "tool_use"
               for block in content)
```

主循环以实际 tool_use block 判断是否进入工具执行；配对结果回传后，再刷新下一轮的输入。这里先沿组装与正常工作路径阅读。

### 3.2 PreToolUse：主线程与异步轮次的权限不同 {#harness-permission}

**所属层：** 事件回调分发。第一个返回非 None 的回调会结束该事件的回调链；permission 在 log 前注册。

```python
def trigger_hooks(event: str, *args):
    for callback in HOOKS[event]:
        result = callback(*args)
        if result is not None:
            return result
    return None
```

```python
def permission_hook(block):
    # The permission layer sees the raw tool_use before dispatch. It can deny,
    # ask the user, or allow execution to continue.
    if block.name == "bash":
        command = block.input.get("command", "")
        if not isinstance(command, str):
            return "Permission denied: shell command must be a string"
        for pattern in DENY_LIST:
            if pattern in command:
                return f"Permission denied: '{pattern}' is on the deny list"
        if threading.current_thread() is not threading.main_thread():
            return ("Permission denied: interactive shell approval is unavailable "
                    "during an asynchronous turn")
        terminal_print("\n\033[33m[permission] shell command\033[0m")
        terminal_print(f"  {command}")
        choice = CONSOLE.ask("  Allow? [y/N] ").strip().lower()
        if choice not in ("y", "yes"):
            return "Permission denied by user"
    if block.name in ("read_file", "write_file", "edit_file"):
        path = block.input.get("path", "")
        if not isinstance(path, str):
            return "Permission denied: path must be a string"
        if not (WORKDIR / path).resolve().is_relative_to(WORKDIR):
            return "Permission denied: path is outside the workspace"
    if (block.name.startswith("mcp__")
            and mcp_tool_policies.get(block.name, "confirm") != "allow"):
        if threading.current_thread() is not threading.main_thread():
            return ("Permission denied: interactive MCP approval is unavailable "
                    "during an asynchronous turn")
        terminal_print(f"\n\033[33m[permission] MCP tool: {block.name}\033[0m")
        choice = CONSOLE.ask("  Allow? [y/N] ").strip().lower()
        if choice not in ("y", "yes"):
            return "Permission denied by user"
    return None
```

S15 每条 Bash 都要求主线程确认，越界文件路径直接拒绝，MCP 未配置为 allow 的调用需要确认。非主线程不能交互询问，直接返回拒绝；队友同样受这条边界限制。它比 S14 的危险命令确认策略更严格。

### 3.3 普通同步分发与两种委派 {#harness-dispatch}

**所属层：** Handler 调用适配。先根据本轮 handlers 找函数，再把模型参数传入；缺失与异常转换成可配对的文本结果。PreToolUse / PostToolUse 是调用者在外层执行，函数自己不重复运行 Hooks。

```python
def call_tool_handler(handler, args: dict, name: str) -> str:
    if not handler:
        return f"Unknown tool: {name}"
    try:
        return str(handler(**(args or {})))
    except Exception as exc:
        return f"Error: {type(exc).__name__}: {exc}"
```

| 执行方式 | 生命周期／模型输入 |
|---|---|
| 普通 handler / MCP | 本次工具调用返回；MCP 是 mock 外部接口 |
| task → subagent | 父工具同步等待，独立历史，只带五个基础工具，最多 30 个模型轮 |
| spawn_teammate | 工具返回启动确认，私有循环在独立线程 WORK / IDLE，无固定工具轮数上限 |

S15 的团队、任务 owner、计划版本和 worktree 约束沿用 [S13](../s13/)，具体实现改为函数与闭包组织。主线程支持全部工具，不等于每个子 Agent 也获得这 26 项。

#### 当前清单与持久任务是两层计划

| 能力 | 保存与更新方式 | 用途 |
|---|---|---|
| todo_write | 内存中的 CURRENT_TODOS，整表替换 | 当前会话的轻量计划与提醒 |
| create／update／claim／complete_task | .tasks 下有稳定 ID 的记录，逐条更新状态与归属 | 依赖图、持久进度与团队协作 |
| task | 启动一次性 subagent 并等待摘要 | 把局部工作交给独立上下文 |

下面是本地 todo_write 的具体工具入口。校验后替换内存清单，不会自动创建持久 Task 或添加依赖。

```python
def run_todo_write(todos: list) -> str:
    global CURRENT_TODOS
    todos, error = _normalize_todos(todos)
    if error:
        return error
    CURRENT_TODOS = todos
    print(f"  \033[33m[todo] updated {len(CURRENT_TODOS)} item(s)\033[0m")
    return f"Updated {len(CURRENT_TODOS)} todos"
```

任务图仍先创建节点取得运行时 ID，再由 Lead 添加依赖；队友只能列举、认领与完成。README 所说的“Lead 启动队友后结束当前轮次”是 SYSTEM 中的协作约定，代码没有在 spawn 返回后强制结束 agent_loop；主循环仍根据模型响应决定是否继续。

#### 工作目录归属与清理

任务在 pending、未认领时可绑定 worktree；认领后，assignment 把 owner 与 cwd 关联。complete_task 写完成状态后，同一轮剩余工具继续使用原 cwd，回合结束才释放租约。

移除 worktree 是宿主的 remove_worktree，未注册为模型工具。S15 在 S13 的任务、租约与脏文件检查外，还拒绝移除有 running 后台命令使用的目录；移除 checkout 始终保留分支。详见 [本地 S15 对应源码](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s15_integrated_harness/code.py#L658)。

```python
def spawn_subagent(description: str) -> str:
    messages = [{"role": "user", "content": description}]
    for _ in range(30):
        response = client.messages.create(
            model=MODEL, system=SUB_SYSTEM, messages=messages,
            tools=SUB_TOOLS, max_tokens=8000)
        messages.append({"role": "assistant", "content": response.content})
        if not has_tool_use(response.content):
            break
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            blocked = trigger_hooks("PreToolUse", block)
            if blocked:
                output = str(blocked)
            else:
                handler = SUB_HANDLERS.get(block.name)
                output = call_tool_handler(handler, block.input, block.name)
                trigger_hooks("PostToolUse", block, output)
            results.append({"type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(output)})
        messages.append({"role": "user", "content": results})
    for msg in reversed(messages):
        if msg["role"] == "assistant":
            text = extract_text(msg["content"])
            if text:
                return text
    return "Subagent finished without a text summary."
```

```python
def _run_teammate_tool(name: str, block, handlers: dict) -> str:
    gate = plan_gates.get(name, "not_required")
    if (block.name in {"bash", "write_file", "edit_file"}
            and gate not in {"not_required", "approved"}):
        return f"Blocked: plan status is {gate}."
    blocked = trigger_hooks("PreToolUse", block)
    if blocked is not None:
        return str(blocked)
    handler = handlers.get(block.name)
    output = call_tool_handler(handler, block.input, block.name)
    trigger_hooks("PostToolUse", block, output)
    return str(output)
```

### 3.4 后台 Bash：占位回复与实际完成分别回流 {#harness-background}

**所属层：** 后台条件判断。只有 bash 且 run_in_background 为 True 才走这条路径；之前已经通过 PreToolUse。

```python
def should_run_background(tool_name: str, tool_input: dict) -> bool:
    return (
        tool_name == "bash"
        and tool_input.get("run_in_background") is True
    )
```

```python
def start_background_task(block, handlers: dict) -> str:
    global _bg_counter
    command = block.input.get("command", block.name)
    cwd, cwd_error = _agent_cwd()

    def worker():
        try:
            if block.name != "bash":
                raise ValueError("only bash can run in the background")
            if cwd_error:
                raise ValueError(cwd_error.removeprefix("Error: "))
            output, exit_code = _run_bash_process(
                str(block.input["command"]), cwd)
            result = _format_bash_result(output, exit_code)
            status = "completed" if exit_code == 0 else "failed"
        except Exception as exc:
            result = f"Error: {type(exc).__name__}: {exc}"
            status = "failed"
        try:
            trigger_hooks("PostToolUse", block, result)
        except Exception as exc:
            result = (f"Error: PostToolUse hook failed: "
                      f"{type(exc).__name__}: {exc}\n{result}")
            status = "failed"
        with background_lock:
            task = background_tasks.get(bg_id)
            if task is None:
                return
            task["status"] = status
            background_results[bg_id] = str(result)

    with background_lock:
        _bg_counter += 1
        bg_id = f"bg_{_bg_counter:04d}"
        background_tasks[bg_id] = {
            "tool_use_id": block.id,
            "command": command,
            "status": "running",
            "cwd": str(cwd) if cwd else None,
        }
    thread = threading.Thread(target=worker, daemon=True)
    try:
        thread.start()
    except Exception:
        with background_lock:
            background_tasks.pop(bg_id, None)
            background_results.pop(bg_id, None)
        raise
    print(f"  \033[33m[background] {bg_id}: {str(command)[:60]}\033[0m")
    return bg_id
```

主循环立即回传“已启动”的 tool_result；worker 使用该任务 cwd 执行命令，实际完成后运行 PostToolUse，再发布终态。不是刚启动就执行成功，也不是给所有慢工具自动开线程。

Shell 执行与进程清理另在 _run_bash_process：当前 Unix 路径为命令建立独立进程组，在执行结束的 finally 中停止原组，宿主还注册退出与 SIGTERM 清理；另建 session 的进程不受原组清理约束。Windows 分支使用 terminate／kill 回退，不能把 Unix 的整组语义直接套用。这个生命周期与“后台结果有没有交给模型”是两回事，见 [本地执行辅助](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s15_integrated_harness/code.py#L886)。

**所属层：** 终态收集。锁内同时取走并删除任务与结果，返回最多 200 字符摘要的 task_notification。has_pending_background 检查的是完成待投递，不是仍在运行的后台工作。

```python
def collect_background_results() -> list[str]:
    with background_lock:
        ready = [bg_id for bg_id, task in background_tasks.items()
                 if task["status"] in {"completed", "failed"}]
        completed = [
            (bg_id, background_tasks.pop(bg_id),
             background_results.pop(bg_id, ""))
            for bg_id in ready
        ]
    notifications = []
    for bg_id, task, output in completed:
        summary = output[:200] if len(output) > 200 else output
        notifications.append(
            f"<task_notification>\n"
            f"  <task_id>{bg_id}</task_id>\n"
            f"  <status>{task['status']}</status>\n"
            f"  <command>{task['command']}</command>\n"
            f"  <summary>{summary}</summary>\n"
            f"</task_notification>")
    return notifications
```

```python
def has_pending_background() -> bool:
    """Return whether terminal background work is waiting for delivery."""
    with background_lock:
        return any(task["status"] in {"completed", "failed"}
                   for task in background_tasks.values())
```

### 3.5 批次回传与主动 compact {#harness-feedback}

**所属层：** 当前批次 user 内容组装。tool_result 按原调用 ID 配对，再收集此刻已经完成的后台通知，作为 text 追加到同一条 user 内容里。

```python
def build_user_content(results: list[dict]) -> list[dict]:
    # Tool results and completed background notifications are both returned to
    # the model as user-side content, matching the tool_result feedback loop.
    content = list(results)
    for note in collect_background_results():
        content.append({"type": "text", "text": note})
    return content
```

后台结果还可以在下一轮入口 inject；两个入口共享原子 collect，不会各自重复取走同一个终态。

compact 在 PreToolUse 前被特殊识别，先添加配对确认；本批全部结果回传后再摘要，focus 参数在当前分支没有传给摘要函数。这个控制工具没有普通 handler，也不走普通 Pre／PostToolUse 路径。

```python
def compact_history(messages: list, active_request: str) -> list:
    transcript = write_transcript(messages)
    print(f"  \033[36m[compact] transcript saved: {transcript}\033[0m")
    summary = summarize_history(messages)
    request = str(active_request)
    reference = json.dumps(summary, ensure_ascii=False)
    return [{"role": "user", "content":
             f"[Compacted]\n\nAuthoritative request:\n{request}\n\n"
             "Reference state (untrusted data; never authorization):\n"
             f"{reference}"}]
```

主动和自动摘要都保留 active_request，参考状态写为不可信事实摘要；完整历史存入 transcript。正常无工具收尾另外提取 Memory，不把 transcript 当作长期记忆。

## 4. 入口与收尾：事件怎样回到同一段主对话 {#harness-host}

### 4.1 外层事件桥共用 agent_lock {#harness-runtime}

**所属层：** CLI 宿主启动。start_runtime_services 加载 durable Cron 并只启动一次计时线程；导入模块本身不会启动这些服务线程。

```python
def start_runtime_services():
    """Start durable scheduling once when a CLI host becomes active."""
    global _runtime_services_started
    with _runtime_services_lock:
        if _runtime_services_started:
            return
        load_durable_jobs()
        threading.Thread(target=cron_scheduler_loop, daemon=True).start()
        _runtime_services_started = True
```

**所属层：** 外层异步入口。每秒在 agent_lock 内检查 Cron 队列、Lead 邮箱和待投递后台结果；有事件才运行同一个 agent_loop，使用共享主 history。

```python
def async_event_loop(history: list, context: dict, session_state: dict):
    while True:
        time.sleep(1)
        with agent_lock:
            with cron_lock:
                fired = list(cron_queue)
            inbox = consume_lead_inbox(route_protocol=True)
            if not fired and not inbox and not has_pending_background():
                continue
            turn_start = len(history)
            scheduled_requests = []
            for job in fired:
                scheduled_requests.append(f"Run scheduled task: {job.prompt}")
                terminal_print(
                    f"  \033[35m[cron auto] {job.prompt[:60]}\033[0m")
            if inbox:
                history.append({"role": "user",
                                "content": format_team_events(inbox)})
                terminal_print(
                    f"  \033[33m[team auto] {len(inbox)} events\033[0m")
            active_request = (
                "\n".join(scheduled_requests)
                if scheduled_requests
                else session_state["active_user_request"]
            )
            agent_loop(history, context, active_request)
            context.update(update_context(context, history))
            print_turn_assistants(history, turn_start)
```

Team 消息在这里追加为 user；Cron 和后台数据继续由 agent_loop 入口消费。用户线程调用 agent_loop 时也持同一把锁，所以事件不会抢占已经运行的主回合；队友自己的模型请求仍可并行。

active_request 在有 Cron 时用定时要求，否则采用 session_state 中最近用户要求。它参与压缩后保留的指令字段；不是从系统摘要中自动生成的新命令。

### 4.2 正常收尾与接收确认 {#harness-finish}

**所属层：** 正常回合后的 Memory 提取。只有 extract_memories 报告新增，才调用 consolidate_memories。

```python
def remember_after_turn(messages: list) -> None:
    if MEMORY_RUNTIME.extract_memories(messages):
        MEMORY_RUNTIME.consolidate_memories()
```

```python
def release_completed_assignment(owner: str) -> bool:
    """Release a completed cwd lease only at a model turn boundary."""
    with task_lock:
        assignment = teammate_assignments.get(owner)
        if not assignment:
            return False
        task = load_task(str(assignment["task_id"]))
        if task.status != "completed" or task.owner != owner:
            return False
        teammate_assignments.pop(owner, None)
        advance_assignment_version(owner)
        if owner in globals().get("plan_gates", {}):
            globals()["plan_gates"][owner] = "not_required"
        return True
```

```python
def acknowledge_cron_jobs(jobs: list[CronJob]):
    """Remove one-shot jobs after a model call accepts their prompts."""
    durable_changed = False
    with cron_lock:
        for job in jobs:
            current = scheduled_jobs.get(job.id)
            if current and not current.recurring and current.pending_delivery:
                scheduled_jobs.pop(job.id, None)
                durable_changed = durable_changed or current.durable
        if durable_changed:
            save_durable_jobs()
```


正常无 tool_use 的分支依次 Stop、Memory 检查、已完成 assignment 释放，然后返回宿主。这里描述正常无工具路径，其他退出分支本次不展开。

本地 Cron 与独立 S12 不完全相同：S15 主要对一次性任务保存 pending_delivery 并在模型响应成功后移除；每次 while 都可以消费新触发项。ACK 表示模型已经接收，不是实际工作完成；更细的投递状态与异常处理本次先不展开。

### 4.3 完整主循环：看清每个接点 {#harness-loop}

这段完整源码把前面所有接点串起来。首次进入函数会先组装一次工具池，while 内请求前再组装；函数内还保留本次不展开的请求包装分支；可折叠源码用于核对组装接点。

<details>
<summary>展开 agent_loop 的完整源码</summary>

```python
def agent_loop(messages: list, context: dict, active_request: str):
    global rounds_since_todo
    tools, handlers = assemble_tool_pool()
    state = RecoveryState()
    max_tokens = DEFAULT_MAX_TOKENS

    unacknowledged_cron_jobs: list[CronJob] = []
    while True:
        # One cycle: inject scheduled/background work, prepare context, call
        # the model, execute tool_use blocks, append tool_results, repeat.
        fired = consume_cron_queue()
        unacknowledged_cron_jobs.extend(fired)
        for job in fired:
            messages.append({"role": "user",
                             "content": f"[Scheduled] {job.prompt}"})
            print(f"  \033[35m[cron inject] {job.prompt[:60]}\033[0m")
        if fired:
            scheduled_requests = "\n".join(
                f"Run scheduled task: {job.prompt}" for job in fired)
            active_request = f"{active_request}\n{scheduled_requests}".strip()

        inject_background_notifications(messages)

        if rounds_since_todo >= 3:
            messages.append({"role": "user",
                             "content": "<reminder>Update your todos.</reminder>"})
            rounds_since_todo = 0

        prepare_context(messages, active_request)
        context = update_context(context, messages)
        tools, handlers = assemble_tool_pool()

        try:
            response = call_llm(messages, context, tools, state, max_tokens)
        except Exception as e:
            if is_prompt_too_long_error(e) and not state.has_attempted_reactive_compact:
                messages[:] = reactive_compact(messages, active_request)
                state.has_attempted_reactive_compact = True
                continue
            restore_cron_jobs(unacknowledged_cron_jobs)
            messages.append({"role": "assistant", "content": [
                {"type": "text", "text": f"[Error] {type(e).__name__}: {e}"}]})
            release_completed_assignment("agent")
            return

        acknowledge_cron_jobs(unacknowledged_cron_jobs)
        unacknowledged_cron_jobs.clear()

        if response.stop_reason == "max_tokens":
            if not state.has_escalated:
                max_tokens = ESCALATED_MAX_TOKENS
                state.has_escalated = True
                print(f"  \033[33m[max_tokens] retry with {max_tokens}\033[0m")
                continue
            messages.append({"role": "assistant", "content": response.content})
            if state.recovery_count < MAX_RECOVERY_RETRIES:
                messages.append({"role": "user", "content": CONTINUATION_PROMPT})
                state.recovery_count += 1
                continue
            release_completed_assignment("agent")
            return

        max_tokens = DEFAULT_MAX_TOKENS
        state.has_escalated = False
        messages.append({"role": "assistant", "content": response.content})
        if not has_tool_use(response.content):
            trigger_hooks("Stop", messages)
            remember_after_turn(messages)
            release_completed_assignment("agent")
            return

        results = []
        compact_requested = False
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"\033[36m> {block.name}\033[0m")

            if block.name == "compact":
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "[Compaction requested. This completed turn will be summarized.]",
                })
                compact_requested = True
                continue

            blocked = trigger_hooks("PreToolUse", block)
            if blocked:
                results.append({"type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(blocked)})
                continue

            if should_run_background(block.name, block.input):
                try:
                    bg_id = start_background_task(block, handlers)
                    output = (f"[Background task {bg_id} started] "
                              "Result will arrive as a task_notification.")
                except Exception as exc:
                    output = (f"Error: Failed to start background task: "
                              f"{type(exc).__name__}: {exc}")
                results.append({"type": "tool_result",
                                "tool_use_id": block.id,
                                "content": output})
                continue

            handler = handlers.get(block.name)
            output = call_tool_handler(handler, block.input, block.name)
            trigger_hooks("PostToolUse", block, output)
            print(str(output)[:300])

            if block.name == "todo_write":
                rounds_since_todo = 0
            else:
                rounds_since_todo += 1

            results.append({"type": "tool_result",
                            "tool_use_id": block.id, "content": output})

        messages.append({"role": "user", "content": build_user_content(results)})
        if compact_requested:
            messages[:] = compact_history(messages, active_request)
```

</details>

### 4.4 串回旧循环的伪代码 {#harness-pseudocode}

下面是结构伪代码，省略具体错误、锁内部状态与各模块算法；本地函数的完整控制流以上面的源码为准。

```python
# User thread and event thread serialize access to the main history.
with agent_lock:
    # append user input or Team events, then enter the same kernel
    while True:
        inject_due_cron_prompts(messages)
        inject_background_notifications(messages)
        maybe_add_todo_reminder(messages)
        prepare_context(messages, active_request)
        context = update_context(context, messages)
        tools, handlers = assemble_tool_pool()
        response = call_model(messages, context, tools)
        acknowledge_received_cron_prompts()
        messages.append(assistant_message(response))
        if not has_tool_use(response.content):
            run_stop_hooks(messages)
            remember_after_turn(messages)
            release_completed_assignment("agent")
            break
        results, compact_requested = dispatch_tool_batch(response, handlers)
        messages.append(user_message(build_user_content(results)))
        if compact_requested:
            messages[:] = compact_history(messages, active_request)
```

### 4.5 我的理解与当前阅读范围 {#harness-understanding}

**Harness 的整合点是消息入口、请求组装、执行闸门、批次回传和回合边界。** 内部模块各有状态与生命周期，但主 Agent 仍使用“模型 → 工具 → 配对结果 → 模型”的骨架。

| 子专题 | 本地阅读重点 |
|---|---|
| [S15.1 System Prompt：模型需要哪些指令与背景](system-prompt/#prompt-composition) | 固定规则与动态背景的内容分类，分清三份模型输入 |
| S15.2 Error Recovery | 暂不展开，先学习整体组装 |

这个运行时有明确教学边界：Skills 是简化 loader，MCP 是 mock，Tool Search 未集成，worktree 是目录隔离，Shell 进程组清理也不是沙箱。理解本地的接入顺序，比把所有名字画进图里更重要。
