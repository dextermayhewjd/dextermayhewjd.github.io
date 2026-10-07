---
title: "S14 MCP Tools：通过标准协议接入外部工具"
weight: 140
aliases: ["/projects/learn-claude-code/s19/"]
summary: "连接并发现 server 工具，映射名称与 schema，每轮组装工具池，经宿主权限和调用适配返回原 tool_result。"
ShowToc: false
compactDiagramLegends: true
---

{{< chapter-outline id="s14-chapter-outline" title="S14 本章目录" >}}

## 1. 定位：工具来源变了，基础循环还在 {#mcp-position}

### 1.1 我想弄清楚的问题 {#mcp-question}

S02 的工具由 Harness 手写定义和函数。接入文档系统、部署服务时，我不想在 Agent 里为每个服务重写一套能力，能否让服务提供工具列表，再接进现有循环？

我的理解是：**MCP Tools 把“服务提供什么”与“Agent 怎样使用”分开。Server 提供工具定义与调用入口；Harness 发现、适配、检查权限，再把结果接回 S01 的工具循环。** 模型选择工具和参数，实际调用仍由 Harness 执行。

源码基准为本地 `ce8f9f1` 的 [s14_mcp_plugin/code.py](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s14_mcp_plugin/code.py)。完整函数按源码摘录，类方法保留 `self`；伪代码和局部片段另行说明。按 [MIT 许可](/examples/s14-repo/NOTICE.txt)使用。

### 1.2 先分清模型、Harness、Client 和 Server {#mcp-boundaries}

| 角色 | 知道什么／负责什么 |
|---|---|
| 模型 | 本轮可见工具的 name、description、参数 schema；产生 tool_use |
| Harness / host | 连接哪些 server、组装工具池、权限策略与 tool_result 回传 |
| MCP Client | 保存发现的定义，将原始工具名与参数交给对应 server |
| MCP Server | 提供业务工具，例如 search、status、trigger |

MCP 的工具协议用 `tools/list` 发现定义，用 `tools/call` 提交 name 与 arguments；返回值也可以包含多种内容。本章模拟这两个接口的职责，只返回字符串。依据：[MCP Tools 规范（2025-11-25）](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)。

**本例边界：** docs / deploy 是进程内 mock，搜索、版本和部署状态都是固定示例文本。代码没有发出 JSON-RPC 请求，也没有实现 stdio、HTTP、握手、认证或服务启动；`MCPClient` 是教学替身，不是真实 SDK Client。

### 1.3 整体过程：从 S13 到 S14 {#mcp-architecture}

#### 图 1：回顾 S13 的默认总览

{{< architecture from="/projects/learn-claude-code/s13" width="1200" src="images/team-agent-integration.svg" mode="baseline" modified="prepare,tools,system,handler,pre-event" folded="team-spawn,team-work,team-mailbox,team-idle,team-wake" label="图 1：保留 S13 原图，标记动态工具池的改造位置与团队细节合并" caption="图 1：仍是上章默认节点与连线。橙色位置本章改为按连接状态组装 schema、handlers、SYSTEM，并增加 MCP 权限策略；五个灰色团队细节在图 2 合并到 S13 接口索引。" >}}

#### 图 2：发现与调用怎样接入已有系统

{{< architecture-explorer id="s14-mcp-explorer" modules="explorer.json" roles="function-roles.json" width="1200" src="images/mcp-agent-integration.svg" legend="evolution" label="图 2：connect 经原工具入口发现服务，保存注册状态，下一轮组装模型工具与分发表，外部调用经权限后回传结果" caption="图 2：紫色展开连接、工具注册、每轮组装和 MCP 调用。组装分别输出模型 schema 与本地 handlers；调用仍经过 PreToolUse、PostToolUse 和配对 tool_result。蓝色 S13 接口保留启动确认和后续事件交付，内部循环回到 S13。" >}}

**比较范围：** 图 2 是累积学习骨架。独立 S14 脚本实际从 S04 基础工具和 Hooks 出发，只加 MCP 连接／发现／调用；没有合入 Task、Background、Cron、Team、Worktree、Memory、Skills 或 Compact。这些旧节点是复习接口；到 S15 才讨论综合 Harness。

#### 图 3：动态工具池的最小核心

{{< architecture figureId="s14-mcp-core" functionExplorer="s14-mcp-explorer" width="1000" src="images/mcp-core.svg" legend="evolution" label="图 3：连接保存、每轮组装、模型选择、宿主权限、原名调用和结果回传，区分工具错误与组装请求错误" caption="图 3：上方是发现到模型可见，下方是调用与回传；回到下一轮才重新组装工具池。工具错误返回 tool_result；组装或模型请求失败记录 assistant 错误并结束本轮。点击内部函数名就近阅读实现。" >}}

{{< mechanism-function-index id="s14-mcp-functions" explorer="s14-mcp-explorer" class="MCPClient" >}}

## 2. 连接与发现：先保存服务提供的能力 {#mcp-discovery}

### 2.1 模型工具入口与内部 Client 分层 {#mcp-layers}

| 层次 | 对应代码 | 作用 |
|---|---|---|
| 模型可见 schema | CONNECT_TOOL 与组装后的 tools | 描述工具名称、参数与用途 |
| 具体工具入口 | run_connect_mcp | 接收 name，转交内部连接逻辑 |
| Harness 组装逻辑 | assemble_tool_pool / assemble_system_prompt | 每轮生成模型定义、本地分发表和请求背景 |
| Harness 执行入口 | execute_tool / permission_hook | 权限、函数查找、异常和 Hooks |
| Client 内部方法 | register / call_tool | 保存定义与调用映射，执行原始工具 |
| 模拟服务实现 | _mock_server_docs / _mock_server_deploy | 代替发现响应与远端业务逻辑 |

`run_` 前缀不是自动注册规则。下面的绑定明确把 connect_mcp 模型工具接到 run_connect_mcp；外部工具则由 assemble_tool_pool 生成 handler，不要求每个 server 工具另写一个 run_* 函数。

```python
CONNECT_TOOL = {
    "name": "connect_mcp",
    "description": "Connect to an MCP server and discover its tools.",
    "input_schema": {
        "type": "object",
        "properties": {"name": {"type": "string", "enum": ["docs", "deploy"]}},
        "required": ["name"],
    },
}

BUILTIN_TOOLS = [*BASE_TOOLS, CONNECT_TOOL]

BUILTIN_HANDLERS = {**BASE_HANDLERS, "connect_mcp": run_connect_mcp}
```

```python
def run_connect_mcp(name: str) -> str:
    return connect_mcp(name)
```

初始工具池是五个基础工具加 connect_mcp，共 **6 个工具**。连接 docs 后是 8 个，docs 和 deploy 都连接后是 10 个；这是本例固定 mock 的数量，不是 MCP 限制。

### 2.2 MCPClient 的内部状态与 register {#mcp-client}

**所属层：** Client 内部状态初始化。name 保存服务身份；tools 保存定义列表；_handlers 保存原始工具名到本地 mock 函数的映射。

```python
def __init__(self, name: str):
    self.name = name
    self.tools: list[dict] = []
    self._handlers: dict[str, callable] = {}
```

**register 输入：** 工具定义与模拟函数表。**输出／副作用：** 检查非空名字、同 server 重名及缺失 handler，再保存两份状态。这里模拟已经拿到 tools/list 结果后的登记，不会调用模型，也没有真实网络发现。

```python
def register(self, tool_defs: list[dict], handlers: dict[str, callable]):
    names = [tool.get("name") for tool in tool_defs]
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("Every MCP tool needs a non-empty name")
    if len(set(names)) != len(names):
        raise ValueError(f"Duplicate MCP tool name on server {self.name!r}")
    missing = [name for name in names if name not in handlers]
    if missing:
        raise ValueError(f"Missing MCP handlers: {', '.join(missing)}")
    self.tools = list(tool_defs)
    self._handlers = dict(handlers)
```

`list` / `dict` 复制的是外层容器，内部 schema 并没有深拷贝。注册检查也不等于完整 JSON Schema 校验；本章关注发现与分发边界。

### 2.3 docs server：定义与业务函数各放在哪里 {#mcp-mock-docs}

**所属层：** 模拟服务工厂。创建 Client，再 register 两项工具：search 需要 query，get_version 无必需参数。服务使用 `inputSchema`，暂时还不是传给模型 SDK 的 `input_schema`。

```python
def _mock_server_docs() -> MCPClient:
    server = MCPClient("docs")
    server.register(
        tool_defs=[
            {
                "name": "search",
                "description": "Search the documentation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
                "annotations": {"readOnlyHint": True},
            },
            {
                "name": "get_version",
                "description": "Get the documentation API version.",
                "inputSchema": {"type": "object", "properties": {}},
                "annotations": {"readOnlyHint": True},
            },
        ],
        handlers={
            "search": lambda query: f"[docs] Found 3 results for '{query}'",
            "get_version": lambda: "[docs] API v2.1.0",
        },
    )
    return server
```

annotations 的 readOnlyHint 描述服务声称的行为；实际宿主授权不在这里。两个 lambda 才是本例业务实现，固定返回搜索示例与版本示例，不能把这里的 v2.1.0 当成当前真实服务版本。

### 2.4 connect_mcp：选择工厂并记录连接状态 {#mcp-connect}

**所属层：** Harness 内部连接／发现逻辑。输入注册的 server 名；重复连接返回说明，未知名字返回可选列表。成功时调用工厂、保存 mcp_clients[name]，返回发现工具数量和原始名字。

```python
MOCK_SERVERS = {
    "docs": _mock_server_docs,
    "deploy": _mock_server_deploy,
}
```

```python
def connect_mcp(name: str) -> str:
    if name in mcp_clients:
        return f"MCP server '{name}' already connected"
    factory = MOCK_SERVERS.get(name)
    if not factory:
        return f"Unknown server '{name}'. Available: {', '.join(MOCK_SERVERS)}"
    server = factory()
    mcp_clients[name] = server
    names = ", ".join(tool["name"] for tool in server.tools)
    print(f"  [mcp] connected: {name} -> {names}")
    return (
        f"Connected to MCP server '{name}'. "
        f"Discovered {len(server.tools)} tools: {names}"
    )
```

此时改变的是 Client 注册表。connect_mcp 的 tool_result 只是连接确认；新工具的 schema 要等下一次 assemble_tool_pool 才发给模型。mcp_clients 在进程内保存，同一 CLI 的后续用户回合继续可用，进程重启不自动恢复。

## 3. 工具池：模型定义和本地 handler 必须一起变 {#mcp-pool}

### 3.1 名字适配：前缀与规范化 {#mcp-names}

server 的原始工具名可以重复，例如两个服务都有 search。本例把模型可见名字变成 `mcp__{safe_server}__{safe_tool}`；调用时仍使用原名。

**所属层：** 命名辅助。替换模型工具名字符集以外的字符，空字符串不能通过。

```python
_DISALLOWED_CHARS = re.compile(r"[^a-zA-Z0-9_-]")
```

```python
def normalize_mcp_name(name: str) -> str:
    """Replace characters outside the model tool-name alphabet."""
    normalized = _DISALLOWED_CHARS.sub("_", name)
    if not normalized:
        raise ValueError("MCP names cannot normalize to an empty string")
    return normalized
```

| 原始来源 | 本例模型可见名称 |
|---|---|
| docs / search | mcp__docs__search |
| deploy / status | mcp__deploy__status |
| docs.one / get.version | mcp__docs_one__get_version |

最后一行可能与 docs_one / get_version 冲突，所以不能只替换字符然后覆盖旧条目。组装时会检查冲突和 64 字符上限。**前缀、规范化和这个长度上限是本例给模型适配的约定，不是 MCP 协议要求使用这套名称。**

### 3.2 assemble_tool_pool：一轮的一对快照 {#mcp-assemble}

**所属层：** Harness 动态组装。输入内置工具及所有已连接 Client；输出 tools 列表与 handlers 字典，同时更新本轮 mcp_tool_policies。两份快照使用同一组名称。

```python
def assemble_tool_pool() -> tuple[list[dict], dict[str, callable]]:
    """Combine built-in tools with every connected server tool."""
    global mcp_tool_policies
    tools = list(BUILTIN_TOOLS)
    handlers = dict(BUILTIN_HANDLERS)
    policies: dict[str, str] = {}
    origins = {
        tool["name"]: f"built-in tool {tool['name']!r}"
        for tool in tools
    }

    for server_name, server in mcp_clients.items():
        safe_server = normalize_mcp_name(server_name)
        for tool_def in server.tools:
            raw_name = tool_def["name"]
            safe_tool = normalize_mcp_name(raw_name)
            prefixed = f"mcp__{safe_server}__{safe_tool}"
            if len(prefixed) > 64:
                raise ValueError(f"MCP tool name is longer than 64 characters: {prefixed}")
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
                lambda *, client=server, tool=raw_name, **kwargs:
                client.call_tool(tool, kwargs)
            )
            policies[prefixed] = MCP_HOST_POLICY.get(
                (server_name, raw_name), "confirm"
            )

    mcp_tool_policies = policies
    return tools, handlers
```

这里每轮重建：先复制内置部分，再遍历已经保存的 server 定义。检查命名冲突、长度与参数 schema 的对象类型；把 `inputSchema` 适配为 SDK 的 `input_schema`，并建立带前缀名字到原始调用的 handler。

**它不会每轮重新连 server 或重新发送 tools/list。** 本例只重读 mcp_clients 里的缓存；没有 list_changed 通知与自动刷新实现。模型只收到 name / description / input_schema，Python handler 和权限字典都留在 Harness。

### 3.3 为什么 lambda 要写 client=server、tool=raw_name {#mcp-binding}

这是上一段源码的**局部摘录**：

```python
handlers[prefixed] = (
    lambda *, client=server, tool=raw_name, **kwargs:
    client.call_tool(tool, kwargs)
)
```

循环每次都换 server / raw_name。默认参数在创建函数时求值，让各 handler 默认保存当次 Client 引用与原始工具名；稍后调用时，kwargs 才是模型提供的业务参数。这里保存引用，不会复制或冻结整个 Client。依据：[Python 函数定义](https://docs.python.org/3/reference/compound_stmts.html#function-definitions)。

如果直接在函数体引用循环变量，多个 handler 会在调用时读到循环最终的绑定。下面是**独立语言示例**，说明两种写法的结果：

```python
late = [lambda: i for i in range(3)]
bound = [lambda i=i: i for i in range(3)]

assert [f() for f in late] == [2, 2, 2]
assert [f() for f in bound] == [0, 1, 2]
```

对这个 MCP 示例而言，默认参数保证正常业务调用分别去 docs.search、docs.get_version、deploy.trigger、deploy.status，不全指向最后一个工具。

### 3.4 SYSTEM 是背景，TOOLS 才是可调用定义 {#mcp-system}

**所属层：** 请求背景组装。无连接时返回 BASE_SYSTEM；有连接时只附上 server 名称。工具参数 schema 由 tools 提供，handlers 由 Harness 保存。

```python
def assemble_system_prompt() -> str:
    if not mcp_clients:
        return BASE_SYSTEM
    return BASE_SYSTEM + "\n\nConnected MCP servers: " + ", ".join(mcp_clients)
```

“Connected MCP servers: docs” 说明当前背景，但不会单独注册 search。真正注册本轮可调用名称的是 assemble_tool_pool 返回的 tools / handlers。

### 3.5 为什么同批 connect 后不能立刻调用新工具 {#mcp-round}

这一轮发送模型前，tools / handlers 已经组装好。connect 工具虽然在执行时更新 mcp_clients，当前工具批次仍用旧 handlers；直到回传结果后进入下一轮，模型才看到新定义。

```text
Round 1: 6 tools -> connect_mcp("docs") -> connection tool_result
Round 2: 8 tools -> mcp__docs__search(query="hooks") -> search tool_result
Round 3: 8 tools -> answer, or another tool call
```

如果模型在第 1 轮同一批里自行写出 mcp__docs__search，它先走当前默认的外部工具确认；放行后，旧 handler 仍查不到这个名字，会返回 Unknown tool。不是 connect 一执行就修改了已经发出去的模型请求或本轮分发表。

### 3.6 扩展理解：工具搜索与按需加载 {#mcp-tool-search}

**这一节是官网行为对照与扩展示意，本地 S14 尚未实现。** 前面三张图和源码仍对应“已连接工具全量进入模型 tools”的版本。

#### 3.6.1 服务发现与模型搜索是两层 {#mcp-search-layers}

工具很多时，可以保留完整工具池，再缩小模型当轮要阅读的定义。关键是区分 **Harness 已经登记的工具** 与 **模型当前可见的工具定义**。

| 层次 | 谁负责 | 得到什么 |
|---|---|---|
| 服务发现 | Client / Harness | 已连接 server 的工具定义，保存在完整目录中 |
| 工具搜索 | 模型提出需求，Harness 或 API 执行查找 | 当前任务相关的工具 |
| 按需加载 | Harness 或 API | 将匹配工具的完整 schema 提供给模型 |
| 业务调用 | 模型选择，Harness 执行 | 实际文档、部署状态等结果 |

`search_tools("查询部署状态")` 是寻找合适的工具；随后调用 `mcp__deploy__status(service="web")`，才查询业务数据。搜索范围是已接入的工具目录。

本地 connect 的 schema 只列出 docs / deploy 名称。若希望模型更容易判断何时使用服务，可另提供简短的用途目录，例如 docs 负责文档搜索，deploy 负责部署状态；下面的示意把这份轻量目录作为请求背景。

#### 3.6.2 现代 Claude 的公开做法 {#mcp-search-official}

Claude Code 启用 ToolSearch 时，先提供工具名称与 server instructions，完整工具定义按需加载。server instructions 用于说明服务用途和何时查找其工具；完整参数 schema 可以等选中能力后再加载。[Claude Code 官方说明](https://code.claude.com/docs/en/mcp#scale-with-mcp-tool-search)

API 的 Tool Search 还区分“发送给 API”与“进入模型初始上下文”：请求仍可提交全部定义，把延迟项标记为 `defer_loading: true`；模型先看到搜索工具和未延迟工具，搜索返回 `tool_reference`，由 API 展开为完整定义后再调用。[Tool Search API 文档](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)

所以，“都登记进工具池”与“都立即占用模型上下文”可以分开。下面只示意 API 请求中的工具配置；它不是本地 agent_loop 的完整替换：

```python
request_tools = [
    {"type": "tool_search_tool_bm25_20251119",
     "name": "tool_search_tool_bm25"},
    *[
        {**tool, "defer_loading": True}
        if tool["name"].startswith("mcp__") else tool
        for tool in discovered_tools
    ],
]
```

`discovered_tools` 表示组装出的工具定义；原始 handlers 留在 Harness。这里只展示配置，使用官方机制还需支持 Tool Search 的模型和相应的响应处理。

#### 3.6.3 扩展局部图：完整目录与可见定义分开 {#mcp-search-diagram}

{{< architecture width="1000" src="images/mcp-tool-search-extension.svg" legend="evolution" label="扩展示意：完整工具目录提供轻量信息，模型搜索并加载匹配 schema，再通过已有入口调用业务工具" caption="扩展局部图：以本地 S14 为参照，蓝色保留工具登记和业务执行，橙色调整模型可见信息，紫色新增工具搜索与按需加载。该图说明下方自建 Harness 伪代码，不是本地已有源码或 Claude Code 内部实现。" >}}

#### 3.6.4 如何接回原循环：自建 Harness 伪代码 {#mcp-search-pseudocode}

下面选择一种容易理解的教学实现：Harness 自己搜索目录、记录 loaded_names，下一轮只提供已加载的外部 schema。**这是自建方案；官方 API 的延迟加载由 API 处理，不要求应用照搬这个集合。**

假定 SEARCH_TOOL_SCHEMA 定义了 `search_tools(query)`；summarize_catalog 只返回简短名称与用途，search_catalog 在已登记 MCP 工具中查找。示例省略连接、异常、搜索算法与 Hooks 细节，业务调用沿用 execute_tool 的权限入口。

```python
loaded_names = set()
while True:
    all_tools, all_handlers = assemble_tool_pool()
    catalog = {
        tool["name"]: tool for tool in all_tools
        if tool["name"].startswith("mcp__")
    }
    visible_tools = [
        tool for tool in all_tools
        if tool["name"] not in catalog or tool["name"] in loaded_names
    ]
    # 本轮分发表固定；刚搜索到的工具也要等下一轮
    visible_handlers = {
        tool["name"]: all_handlers[tool["name"]]
        for tool in visible_tools
    }
    response = ask_model(
        system=assemble_system_prompt() + summarize_catalog(catalog),
        messages=messages,
        tools=[*visible_tools, SEARCH_TOOL_SCHEMA],
    )
    messages.append(assistant_message(response))
    if not response.tool_calls:
        break
    results = []
    for call in response.tool_calls:
        if call.name == "search_tools":
            matches = search_catalog(catalog, call.input["query"])
            loaded_names.update(tool["name"] for tool in matches)
            output = json.dumps([tool["name"] for tool in matches])
        else:
            output = execute_tool(call, visible_handlers)
        results.append(tool_result(call.id, output))
    messages.append(user_message(results))
```

搜索结果先作为 tool_result 告诉模型找到了什么；下一轮 visible_tools 才包含这些工具的参数 schema。找不到就返回空列表，模型可以调整搜索需求。loaded_names 在这段示意中保留到会话结束，长期使用还可设计卸载策略。

**加载不是授权。** 查到或加载工具，只改变可见能力；实际调用仍走宿主权限和原来的 Client 分发。MCP 的服务发现、工具搜索、参数 schema 加载与业务执行分别承担不同职责。

## 4. 调用、权限与错误：接回原来的工具循环 {#mcp-execution}

### 4.1 宿主策略与 deploy 示例 {#mcp-permission}

deploy 的定义与 mock 函数如下，status 和 trigger 有相同 service 参数，但实际授权不同：

```python
def _mock_server_deploy() -> MCPClient:
    server = MCPClient("deploy")
    server.register(
        tool_defs=[
            {
                "name": "trigger",
                "description": "Trigger a deployment.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"service": {"type": "string"}},
                    "required": ["service"],
                },
                "annotations": {"destructiveHint": True},
            },
            {
                "name": "status",
                "description": "Check deployment status.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"service": {"type": "string"}},
                    "required": ["service"],
                },
                "annotations": {"readOnlyHint": True},
            },
        ],
        handlers={
            "trigger": lambda service: f"[deploy] Triggered: {service}",
            "status": lambda service: f"[deploy] {service}: running (v1.4.2)",
        },
    )
    return server
```

```python
MCP_HOST_POLICY = {
    ("docs", "search"): "allow",
    ("docs", "get_version"): "allow",
    ("deploy", "status"): "allow",
    ("deploy", "trigger"): "confirm",
}
```

**所属层：** PreToolUse 权限回调。模型选中的 mcp__ 名称用本轮策略查询；allow 才直接放行，其他值都需要 CLI 确认，用户拒绝则返回拒绝文本。

```python
def permission_hook(block):
    if block.name == "bash":
        command = block.input.get("command", "")
        for pattern in DENY_LIST:
            if pattern in command:
                return f"Permission denied by deny list: {pattern}"
        if contains_destructive_command(command) or any(
            keyword in command for keyword in DESTRUCTIVE
        ):
            print(f"\n[permission] {block.name}({block.input})")
            if input("Allow? [y/N] ").strip().lower() not in {"y", "yes"}:
                return "Permission denied by user"

    if block.name in {"read_file", "write_file", "edit_file"}:
        raw_path = block.input.get("path", "")
        if not (WORKDIR / raw_path).resolve().is_relative_to(WORKDIR.resolve()):
            print(f"\n[permission] {block.name}({block.input})")
            if input("Allow? [y/N] ").strip().lower() not in {"y", "yes"}:
                return "Permission denied by user"

    if block.name.startswith("mcp__"):
        policy = mcp_tool_policies.get(block.name, "confirm")
        if policy != "allow":
            print(f"\n[permission] External tool {block.name}({block.input})")
            if input("Allow? [y/N] ").strip().lower() not in {"y", "yes"}:
                return "Permission denied by user"
    return None
```

宿主用原始 (server_name, raw_name) 配置策略，组装时映射到模型可见名字；未配置默认 confirm。annotations / description 不直接变成权限。MCP 规范也要求按来源信任工具 annotations；本例采取的是明确的宿主配置。依据：[MCP Tools 规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)。

这不是一个完整 allow / deny / confirm 策略解析器：当前代码仅区分 allow 与其余需确认，不把字符串 deny 自动解释成永久拒绝。

### 4.2 execute_tool 与 call_tool 分别在哪一层 {#mcp-call}

**所属层：** Harness 统一执行入口。输入模型 block 与本轮 handlers；先 PreToolUse，再按名称取 handler，执行或把异常变成错误文本，最后运行 PostToolUse。

```python
def trigger_hooks(event: str, *args):
    for callback in HOOKS[event]:
        result = callback(*args)
        if result is not None:
            return result
    return None
```

```python
def execute_tool(block, handlers: dict[str, callable]) -> str:
    blocked = trigger_hooks("PreToolUse", block)
    if blocked:
        return str(blocked)
    handler = handlers.get(block.name)
    if not handler:
        return f"Unknown tool: {block.name}"
    try:
        output = str(handler(**block.input))
    except Exception as exc:
        output = f"Error: {type(exc).__name__}: {exc}"
    trigger_hooks("PostToolUse", block, output)
    return output
```

**所属层：** MCPClient 内部调用。handler 已保存 Client 和原名；call_tool 用原名找到 mock 业务函数，将 args 展开传入，并把输出或异常转成字符串。

```python
def call_tool(self, tool_name: str, args: dict) -> str:
    handler = self._handlers.get(tool_name)
    if not handler:
        return f"MCP error: unknown tool '{tool_name}'"
    try:
        return str(handler(**args))
    except Exception as exc:
        return f"MCP error: {type(exc).__name__}: {exc}"
```

于是 `mcp__docs__search` 只在模型／Harness 侧存在，Client 收到的是 `search` 和 `{"query": "hooks"}`。权限拒绝、未知工具与业务参数错误都能作为配对 tool_result 回到模型。

### 4.3 哪些错误可以修正，哪些会结束这一轮 {#mcp-errors}

| 出错位置 | 本例行为 |
|---|---|
| Client 未知工具、漏参数或业务异常 | MCP error 字符串，仍回传 tool_result |
| Harness handler 未找到／执行异常 | Unknown tool / Error 字符串，仍回传 tool_result |
| 用户拒绝 | Permission denied 字符串，handler 不运行 |
| 工具池命名冲突、过长或 schema 外形错误 | 在模型请求前抛错，agent_loop 记录 assistant 错误并结束 |
| 模型 API 请求异常 | 同样记录 assistant 错误并结束本轮 |

例如 search 漏 query 会在 Python 参数绑定处形成 TypeError；模型可在下一轮重新调用。schema 当前只检查是否是对象定义，没有按完整 JSON Schema 检查 required、数值类型或额外字段。真正 MCP 的结构化结果、isError 等字段也没有在这份 mock 中保留。

### 4.4 完整 Agent Loop 与串联伪代码 {#mcp-loop}

**所属层：** 模型／工具循环。每次请求前组装当前 tools / handlers，模型输出照常追加；所有工具按当前 handlers 执行，结果配对追加到 user 消息后继续。

```python
def agent_loop(messages: list):
    while True:
        try:
            tools, handlers = assemble_tool_pool()
            response = client.messages.create(
                model=MODEL,
                system=assemble_system_prompt(),
                messages=messages,
                tools=tools,
                max_tokens=8000,
            )
        except Exception as exc:
            messages.append({
                "role": "assistant",
                "content": [{
                    "type": "text",
                    "text": f"[Error] {type(exc).__name__}: {exc}",
                }],
            })
            trigger_hooks("Stop", messages)
            return

        messages.append({"role": "assistant", "content": response.content})
        tool_calls = [
            block for block in response.content if block.type == "tool_use"
        ]
        if not tool_calls:
            trigger_hooks("Stop", messages)
            return

        results = []
        for block in tool_calls:
            print(f"> {block.name}")
            output = execute_tool(block, handlers)
            print(output[:300])
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            })
        messages.append({"role": "user", "content": results})
```

下面是**流程伪代码**，省略异常和 Hooks；它把新增部分放回 S01 的原循环：

```python
messages.append(user_message(question))
while True:
    tools, handlers = assemble_tool_pool()
    response = ask_model(
        system=assemble_system_prompt(), messages=messages, tools=tools
    )
    messages.append(assistant_message(response))
    if not response.tool_calls:
        break
    results = []
    for call in response.tool_calls:
        output = execute_tool(call, handlers)
        results.append(tool_result(call.id, output))
    messages.append(user_message(results))
```

connect 的调用属于这条循环里的一个工具。它修改注册状态；下一轮重新组装时才使外部工具变成模型可用能力，不需要另外一套推理循环。

### 4.5 我的理解：接入边界，而不是新的 Agent {#mcp-understanding}

S02 让我理解“工具多了，循环不变”；S14 再往前一步：**工具定义和实现可以来自服务，Harness 负责把发现与调用适配到同一个循环。**

本章已经说明动态工具池、名称与 schema 映射、宿主授权、原名调用和错误回传。真正接服务时，还需实现协议初始化、transport、认证、分页发现、连接生命周期、结果适配与更新通知；这些不是本章 mock 已完成的内容。
