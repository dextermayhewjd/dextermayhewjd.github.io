<!-- Historical draft archived before the S15.1 content refocus. Not the current S15 implementation. -->

---
title: "S15.1 System Prompt：按运行时信息组装指令"
weight: 10
summary: "先看本地 S15 每轮状态与 SYSTEM 组装，再保留旧版四段原型、Skills 与缓存设计作为对照。"
ShowToc: true
---

## 本地 S15：先看当前运行时的真实组装 {#s15-local-assembly}

本节先对照当前本地 S15；后面保留早先写好的旧版原型与设计讨论。综合主章的图和调用顺序对应这里的实际代码，[返回 S15 请求组装](../#harness-context)。

当前顺序是：整理 messages → update_context 选择 Memory → assemble_tool_pool → call_llm 内拼 SYSTEM → 请求模型。每个主模型轮次都刷新，并非只在新用户输入时召回。

**状态收集的完整函数：**

```python
def update_context(context: dict, messages: list) -> dict:
    return {
        "memory_catalog": MEMORY_RUNTIME.read_memory_index(),
        "memories": MEMORY_RUNTIME.load_memories(messages),
        "connected_mcp": list(mcp_clients.keys()),
        "active_teammates": list(active_teammates.keys()),
    }
```

context 包含 Memory 索引与相关正文、MCP 名称和活动队友。后者虽被收集，当前 SYSTEM 函数没有将 active_teammates 字段追加；已连接 MCP 名称则直接读全局注册表。

**SYSTEM 拼接的完整函数：**

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

| 内容 | 本地 S15 的输入位置 |
|---|---|
| 固定身份、工具、任务、团队、workspace、Memory／压缩规则 | SYSTEM 固定片段 |
| 当前时间、Skills 名称与描述 | SYSTEM 动态片段 |
| Memory 目录与选中记录 | SYSTEM，来自 update_context |
| MCP server 名称 | SYSTEM，来自 mcp_clients |
| 用户问题、工具结果、通知、Skills 完整内容 | messages |
| 26 个内置及动态 MCP 工具的参数定义 | tools；Python handlers 留在 Harness |

本地 SYSTEM 每轮拼接，没有旧版原型的本地缓存。Skills registry 在模块加载时扫描，目录不等于每轮重新读全部 SKILL.md；load_skill 返回原始内容，再作为工具结果加入历史。本次先聚焦模型输入组装，Error Recovery 暂不展开。

## 旧版原型与设计对照

以下保留原有笔记中的旧版四段组装、缓存和更完整上下文设计，不能把它们全部当作当前 S15 已实现行为。

## 我想弄清楚的问题

S09 关心哪些信息值得保留下来。接下来还要解决一个问题：工具、工作目录和记忆都准备好之后，Harness 怎样把模型需要的指令与背景组织成一次请求？如果所有内容都写在一大段字符串里，修改和更新会越来越难。

我的理解是：**System Prompt 由 Harness 按现有片段与运行状态组装，让模型每一轮拿到适合当前环境的指令和背景。** 本节没有额外调用 LLM 来生成这份提示。

本篇保留旧 20 章版本的 S10 `s10_system_prompt/code.py` 与[教学网页](https://learn.shareai.run/en/s10/)作为最小原型。当前博客主线已对齐新版 17 章，这份笔记归入 S15 综合 Harness 的独立子专题，再与[新版 S15 组装实现](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s15_integrated_harness/code.py)对照。下文的四段简化代码仍指旧版原型，不是更新后本地 S10 Task System 的代码。

## 整体过程

{{< architecture src="images/system-prompt-flow.svg" label="读取状态、复用或组装提示，再进入模型工具循环" caption="主线从运行状态走到模型请求；工具结果加入历史后，从下方返回并刷新状态。紫色标出提示组装这一层。" >}}

这里有两份不同的数据：`context` 保存用于组装提示的运行状态，`messages` 保存用户问题、模型响应和工具结果。历史变化时，system 不一定变化；system 命中本地缓存时，下一次模型请求仍可能包含新的消息。

## 旧版简化原型由哪些部分组成

| 部分 | 内容 | 本地加载方式 |
|------|------|--------------|
| `identity` | 身份与工作方式 | 始终拼接 |
| `tools` | 可用工具的文字说明 | 始终拼接，内容是固定字符串 |
| `workspace` | 工作目录 | 始终拼接，启动时取得目录 |
| `memory` | 记忆信息 | 索引文件存在且非空时追加 |

这四项是旧版 S10 的最小组织方式，不是完整 Harness 的全部组成。分段方便维护，但模型最终拿到的仍是一份拼接后的 system 字符串。

## 更完整的组装还应考虑什么

**Skills 也应纳入组装设计。** 除了“能调用哪些工具”，模型还需要知道“有哪些可复用的方法可以加载”。下面按职责列出设计时可以考虑的组成，不把它当作 Claude Code 固定的内部 section 列表。

| 组成 | 要让模型知道什么 | 组织方式 |
|------|------------------|----------|
| 身份与行为指导 | 角色、工作方式、回答要求 | 相对稳定的基础指令 |
| Workspace 与环境 | 项目目录、操作系统、必要的环境状态 | 按实际环境生成目录与环境说明 |
| 项目规则 | 项目约定、构建方式和用户维护的要求 | 读取相应项目指令，区分作用范围 |
| Enabled tools | 当前有哪些操作可用、怎样使用 | 工具说明与实际工具池一致；输入 schema 仍通过 API 的 `tools` 提供 |
| Skills | 可用方法的名称、描述和调用入口 | 先提供可见目录，调用时再加载正文 |
| Memory | 可复用的偏好和背景 | 索引与相关正文分层，按需提供 |
| 任务与团队指导 | 怎样管理任务、协作和交接 | 在相应能力启用时提供规则，状态按任务需要取得 |
| 外部服务与运行信息 | MCP 服务说明、必要的时间等信息 | 按配置和状态提供，避免无关内容持续占用输入 |

`enabled_tools` 是状态字段，渲染后可以成为工具说明；它本身不是工具 schema。Workspace 可以包含目录与环境信息。Skills、Memory 则分别提供方法和长期背景，不能仅用工具名称代替。

还有一层需要分清：**完整的模型输入包含 system、messages 和 tools，而这些组成不必都塞进 system。** 现代 Claude Code 的公开说明将项目指令、记忆、已加载 Skills、文件内容、历史和系统指令都列为上下文来源，并说明部分内容通过会话中的提醒加入。[依据：上下文组成](https://code.claude.com/docs/en/how-claude-code-works#the-context-window)。

新版上游 S15 的具体教学实现也扩展了这四段：固定部分增加任务、团队、记忆使用与压缩规则；动态部分加入当前时间、Skills 目录、Memory 目录和相关记录，以及已连接 MCP 服务说明。它的 Skills 目录加入 system，正文通过 `load_skill` 工具结果进入 messages。这个实现可作为更完整的对照，不代表所有 Agent 产品都采用相同的消息安排。[依据：S15 组装代码](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s15_integrated_harness/code.py#L848)。

## 一次组装怎样发生

### 1. 先定义可以复用的文字片段

本地代码用字典存放各段：

```python
PROMPT_SECTIONS = {
    "identity": "You are a coding agent. Act, don't explain.",
    "tools": "Available tools: bash, read_file, write_file.",
    "workspace": f"Working directory: {WORKDIR}",
    "memory": "Relevant memories are injected below when available.",
}
```

这样可以分别维护身份、工具说明和环境信息。模板中的文字仍由人写好，运行时决定怎样组合它们；“组装”不等于“模型自动写提示”。

还有一个代码细节：这里声明了 `memory` 说明，但下面的组装函数没有引用这个字典项，而是直接追加读取到的内容。

### 2. 从真实环境收集状态

`update_context()` 读取工具分发表、工作目录和记忆索引：

```python
def update_context(context: dict, messages: list) -> dict:
    memories = ""
    if MEMORY_INDEX.exists():
        content = MEMORY_INDEX.read_text().strip()
        if content:
            memories = content
    return {
        "enabled_tools": list(TOOL_HANDLERS.keys()),
        "workspace": str(WORKDIR),
        "memories": memories,
    }
```

没有索引文件，或文件只有空白时，`memories` 就是空字符串。程序根据文件的实际状态判断，不根据用户问题里有没有“记忆”这个词判断。

**这里读的是 `.memory/MEMORY.md` 索引。** 它没有运行 S09 的相关性选择，也没有按条目读取主题文件正文。变量叫 `memories`，不代表完整的记忆召回已经发生。

函数虽然接收 `context` 和 `messages`，但当前实现没有使用这两个参数；返回状态完全来自全局分发表、目录和文件。

### 3. 始终加入基础段落，按条件加入索引

拿到状态后，`assemble_system_prompt()` 选择段落并拼接：

```python
def assemble_system_prompt(context: dict) -> str:
    sections = [
        PROMPT_SECTIONS["identity"],
        PROMPT_SECTIONS["tools"],
        PROMPT_SECTIONS["workspace"],
    ]

    memories = context.get("memories", "")
    if memories:
        sections.append(f"Relevant memories:\n{memories}")

    return "\n\n".join(sections)
```

基础三段始终保留，非空的记忆索引接在后面。假设工作目录为 `/project`，索引有一条写作偏好，组装结果可以是：

```text
You are a coding agent. Act, don't explain.

Available tools: bash, read_file, write_file.

Working directory: /project

Relevant memories:
- [notes-style](notes-style.md) - Explain each step before the code.
```

这个例子展示的是模型可见的索引入口，主题文件的详细要求仍需另外读取。

### 4. 状态未变时，复用已经拼好的字符串

`get_system_prompt()` 将状态序列化为缓存键，再比较是否与上次相同：

```python
def get_system_prompt(context: dict) -> str:
    global _last_context_key, _last_prompt
    key = json.dumps(context, sort_keys=True, ensure_ascii=False, default=str)
    if key == _last_context_key and _last_prompt:
        return _last_prompt
    _last_context_key = key
    _last_prompt = assemble_system_prompt(context)
    return _last_prompt
```

这段摘录省略了终端日志。`sort_keys=True` 让相同键值的字典不因键的排列顺序不同而生成不同表示。

缓存只保存最近一份状态及对应结果。状态相同就直接返回字符串，变化后再重新组装；它没有额外请求模型。

### 5. 将组装结果放进模型请求

主循环用缓存包装函数取得 `system`：

```python
system = get_system_prompt(context)
response = client.messages.create(
    model=MODEL,
    system=system,
    messages=messages,
    tools=TOOLS,
    max_tokens=8000,
)
```

三个输入各有作用：

| 输入 | 提供什么 |
|------|----------|
| `system` | 工作指令与本例组装的背景信息 |
| `messages` | 用户任务、模型响应和工具结果 |
| `tools` | 工具名称、说明和输入 schema |

在 system 里写出 `read_file` 的名字，不会自动注册这个工具。模型提出结构化调用需要 `tools` 定义，实际执行还需要 Harness 的 handler。

### 6. 工具返回后，重新读取状态

本地循环将整批工具结果追加到历史之后，再更新状态和提示：

```python
messages.append({"role": "user", "content": results})
context = update_context(context, messages)
system = get_system_prompt(context)
```

因此，如果某次工具执行创建或修改了 `MEMORY.md`，下一次读取会得到新的索引，缓存键随之变化，system 会重新拼接。

如果工具只读取普通文件，运行状态没变，system 可以复用；读取结果仍作为新消息进入模型请求。

## 用三个状态看清变化

| 情况 | `context["memories"]` | 下一次使用的 system |
|------|-----------------------|--------------------|
| 没有索引，或索引为空 | 空字符串 | 基础三段 |
| 工具写入非空索引 | 新的索引文字 | 基础三段 + 索引 |
| 再次读取，状态没有变化 | 相同文字 | 复用上次拼接结果 |

模型是否继续执行工具，仍由 S01 的循环决定。提示组装这一层只负责准备输入。

## 把组装接回 Agent Loop

下面是机制伪代码。`user`、`assistant`、`tool_result` 简写消息构造，其余函数沿用前面的职责：

```python
messages = [user(query)]
context = {}

while True:
    context = update_context(context, messages)
    system = get_system_prompt(context)

    response = call_model(
        system=system, messages=messages, tools=TOOLS
    )
    messages.append(assistant(response.content))

    if response.stop_reason != "tool_use":
        break

    results = []
    for call in response.tool_calls:
        output = TOOL_HANDLERS[call.name](**call.input)
        results.append(tool_result(call.id, output))
    messages.append(user(results))
```

本地代码在进入循环前准备第一份 system，在每批工具执行后刷新；伪代码把准备步骤统一放在每轮开头，便于看清顺序。两种安排都会在下一次模型调用前使用更新后的状态。

关键插入点是：**请求模型前准备 system，工具执行改变环境后重新检查状态。** 本节沿用最小停止判断，异常与输出截断的恢复在 [S15.2 Error Recovery]({{< relref "/projects/learn-claude-code/s15/error-recovery/" >}})中继续讨论。

## 把 Skills 接入这套组装

下面是针对旧版简化原型的扩展示意，沿用 S07 的目录与加载机制；这些代码不在旧版原 S10 文件里。

{{< architecture src="images/skills-context-flow.svg" label="Skills 目录进入 system，正文通过工具结果进入消息历史" caption="目录帮助模型发现可用方法；选用后才加载正文，结果加入 messages，再继续模型决策。下方回传线不经过目录渲染。" >}}

### 1. 收集目录，而不是全部正文

给组装状态增加一个 Skills 目录字段：

```python
context = {
    "workspace": str(WORKDIR),
    "enabled_tools": list(TOOL_HANDLERS.keys()),
    "skills_catalog": list_skills(),
    "memory_index": read_memory_index(),
}
```

这里的 `list_skills()` 提供名称和简短描述，`read_memory_index()` 读取记忆入口，均沿用前面章节的职责。示例使用 `memory_index`，明确它还不是相关主题正文。

目录例如告诉模型：`review-diff` 用于检查未提交改动。此时它知道有这个方法，但还没有得到完整的审查步骤。

### 2. 渲染工具、目录与记忆入口

在扩展组装函数中，从实际状态渲染说明，再按是否存在内容加入两个目录：

```python
def assemble_extended_prompt(context):
    sections = [
        PROMPT_SECTIONS["identity"],
        f"Available tools: {', '.join(context['enabled_tools'])}.",
        f"Working directory: {context['workspace']}",
    ]
    for label, key in (
        ("Skills catalog", "skills_catalog"),
        ("Memory index (background context)", "memory_index"),
    ):
        if context.get(key):
            sections.append(f"{label}:\n{context[key]}")
    return "\n\n".join(sections)
```

这个示例先增加 Skills，并修正原例工具、目录说明不跟随 context 变化的问题。项目规则、任务与团队说明可按同样的分段思路继续扩展，具体取舍由当前能力和任务决定。

接入本地缓存时，包装函数要调用新的渲染函数，缓存键也要覆盖 Skills 目录等实际输入。目录描述变化后需要重新组装；已经通过工具结果加载的正文则属于消息历史，具有另一套保留与更新过程。

### 3. 模型选用时，再加载正文

`load_skill` 仍然需要工具定义和 handler，按 S02 的方式注册：

```python
TOOLS.append({
    "name": "load_skill",
    "description": "Load the instructions for a named skill.",
    "input_schema": {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    },
})
TOOL_HANDLERS["load_skill"] = load_skill
```

这里的 handler 沿用 S07：按名称读取注册表里的正文，找不到时返回错误说明。模型提出 `load_skill(name="review-diff")` 后，原 Agent Loop 执行它，将正文作为配对的 `tool_result` 放进 messages；同一响应的其他工具结果也收齐后，再请求模型。

因此，system 里可以持续保留目录入口，而完整正文在选用后进入上下文。参考文件和脚本再按任务需要读取或执行，这与 S07 的渐进式披露衔接起来。

现代 Claude Code 也公开说明，通常先让模型看到 Skill 描述，调用时加载完整内容；可见性还受 `disable-model-invocation` 等配置影响，不能假定每个 Skill 的描述都始终出现。[依据：按需加载](https://code.claude.com/docs/en/how-claude-code-works#manage-context-with-skills-and-subagents)。调用后的内容生命周期见 [S07.4]({{< relref "/projects/learn-claude-code/s07/04-context.md" >}})。

## 两种缓存各管什么

| 缓存 | 复用的对象 | 怎样观察 |
|------|------------|----------|
| 本地拼接缓存 | Python 已经拼好的字符串 | 本例终端的 `[cache hit]` 日志 |
| API Prompt Cache | 服务端已经处理过的输入前缀 | API 返回的缓存 usage 字段 |

本地缓存命中后，程序仍然把 `system` 传给 API。它既没有缩短提示，也没有让记忆索引退出上下文；不能据此推断输入免费或服务端缓存命中。

官方 API 通过 `cache_control` 开启自动缓存或指定内容块的缓存断点，缓存范围按 `tools → system → messages` 的前缀组织。本地这份代码没有配置 `cache_control`。[依据：Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)。

这里的教学重点是组织输入。稳定的内容顺序可以为 API 缓存设计提供基础，但真实命中还需要按对应接口的规则检查。

## 简化原型还需要看清哪些边界

- **工具说明尚未真正动态渲染。** `enabled_tools` 被收集并参与缓存键，但组装时仍读取固定的工具说明；只改变分发表，不会自动改变那段文字。
- **目录也来自启动时的模板。** 组装函数没有使用 `context["workspace"]`，而是使用提前写好的 workspace 段落。
- **缓存键没有包含模板版本。** 如果运行期间修改 `PROMPT_SECTIONS`，而 context 没变，缓存仍可能返回旧提示。继续完善时，应让缓存覆盖真正影响输出的输入。
- **本节没有完整的记忆、Skill 或压缩管线。** 可用工具只有 Bash、读取和写入文件，Memory 也只读取索引；前面章节的完整能力没有在这里重新实现。
- **文字指令不能代替执行限制。** system 可以说明工作规则，权限与路径检查仍需要由实际执行代码处理。

前面的扩展示意给出了动态工具、Workspace、Skills 和 Memory 索引的渲染方式。渲染时仍要保证说明、API 的 `TOOLS` 定义和实际 handler 一致；Skill 方法与记忆背景也不能代替权限检查或当前用户任务。

## 当前的一句话理解

**Harness 组织指令、环境、工具、Skills 和 Memory 等输入；system 提供指导与入口，历史承载当前任务和已取回的内容，再由 Agent Loop 使用这些信息继续工作。**

本篇依据旧版原型、教学网页及新版综合实现整理；上下文、Skills 与 API 缓存文档核对日期：**2026-10-04**。
