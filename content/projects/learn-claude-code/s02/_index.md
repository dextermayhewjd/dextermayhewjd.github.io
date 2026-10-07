---
title: "S02 Tool Use：工具增加，循环不变"
weight: 20
ShowToc: true
---

**源码范围：** 本节保留迁移前旧 20 章原型的学习记录。主目录编号已对齐新版，但这些教学摘录尚未逐段替换为更新后的本地实现；涉及现代产品行为的部分按文内官网来源说明。

## 我想弄清楚的问题

S01 只有 Bash 一个工具。模型要读文件，就得自己拼 `cat` 命令；要改文件，也得把操作翻译成 Shell。这样既绕，也让模型更容易生成格式错误或不合适的命令。

S02 给 Agent 增加了读取、写入、编辑文件和查找文件等专用工具。我的理解是：**模型仍然负责选择行动，Harness 根据工具名称把请求交给对应的实现。Agent Loop 没变，变化的是它能使用的工具，以及 Harness 分发工具的方式。**

## 整体过程：从 S01 到 S02

先回顾上一章的结构，再看本章的改造，最后展开核心机制。图 1 保留上一章的节点、布局与连线：蓝色是已有部分，橙色标出本轮将改造的旧执行入口，框内仍是“执行 Bash”。图 2 展示改造结果：**蓝色保留，橙色修改，紫色新增，红色表示真实移除。** 原有但首次画出的细节仍用蓝色，并说明来源；本节没有删除 Bash 功能。

### 1. 上一轮：S01 怎样完成任务

{{< architecture from="/projects/learn-claude-code/s01" src="images/agent-loop.svg" mode="baseline" modified="execute" label="S01 旧系统：蓝色保留，橙色执行 Bash 入口将在 S02 改造" caption="图 1：保留 S01 的节点与连线；橙色“执行 Bash”是本轮将改造的旧入口，仍展示旧实现，其他功能蓝色。" >}}

S01 已经能完成“请求模型 → 执行工具 → 回传结果”的循环。要增加文件工具，需要扩大工具定义，并让执行入口能按名称找到对应实现。

### 2. 这一轮：S02 在相同骨架上改什么

{{< architecture legend="evolution" src="images/tool-dispatch.svg" label="S02 修改已有工具表和执行入口，并增加紫色文件工具模块" caption="图 2：已有 TOOLS 容器与执行入口用橙色表示改造，新增四个文件工具用紫色表示。Bash 仍保留，停止分支与回传循环保留。" >}}

Bash 仍然是工具集合中的一项。这里改造的是“只有一个选择、执行入口写死”的结构，不是把 Bash 删除或另建一套循环。

两张图的橙色框对应同一个执行入口：图 1 是旧的“执行 Bash”，图 2 是改造后的“分发并执行”。橙色表示入口的调用方式被改造，不代表 Bash 工具本身消失。工具表原先没有独立框，所以只在图 2 展开，不往图 1 补画。

`TOOLS` 在 S01 请求模型时已经存在，只是没有单独画框。图 2 将它展开，并用橙色表示工具表内容被扩充；新增的四个文件工具才是紫色。

| 对照位置 | S01 | S02 |
|----------|-----|-----|
| 工具定义 | 只有 Bash 的 schema | 五个工具各有自己的 schema |
| 执行入口 | 直接调用 `run_bash(command)` | 用 `block.name` 查表，传入 `block.input` |
| 历史、判断与回传 | 保存消息、判断调用、配对结果 | 沿用原循环 |

### 3. 最小核心：把工具说明接到本地实现

{{< architecture legend="evolution" src="images/tool-use-core.svg" label="S02 最小核心：改造工具接口，新增名称映射，保留模型调用与结果格式" caption="图 3：TOOLS 与执行接口的改造是橙色，新增名称映射表是紫色，模型提出调用与配对结果仍是蓝色。描述面向模型，映射表面向本地程序。" >}}

核心不是“多调用几次模型”，而是建立一个统一接口：**描述工具 → 模型提出调用 → 名称映射到函数 → 参数传给函数 → 返回配对结果。** 第三张图聚焦这条链，完整回环仍由第二张图解释。

<span id="file-tool-implementation"></span>

## 一个工具由几部分组成

工具需要告诉模型“能做什么”和“需要什么参数”，程序还需要有真正执行操作的处理函数。S02 把工具描述放在 `TOOLS` 里，例如读取文件：

```python
{
    "name": "read_file",
    "description": "Read file contents.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "limit": {"type": "integer"},
        },
        "required": ["path"],
    },
}
```

`input_schema` 描述参数结构，供模型生成符合格式的请求。真正读文件的是本地函数：

```python
def run_read(path: str, limit: int | None = None) -> str:
    file_path = safe_path(path)
    lines = file_path.read_text().splitlines()
    if limit and limit < len(lines):
        lines = lines[:limit]
    return "\n".join(lines)
```

S02 用同样的方式提供 `bash`、`read_file`、`write_file`、`edit_file` 和 `glob` 五个工具。文件操作通过 `safe_path` 限定在工作目录下。

## Harness 如何找到处理函数

工具名到处理函数的对应关系保存在字典里：

```python
TOOL_HANDLERS = {
    "bash": run_bash,
    "read_file": run_read,
    "write_file": run_write,
    "edit_file": run_edit,
    "glob": run_glob,
}
```

模型返回 `tool_use` 后，Harness 用请求里的工具名查表，并把参数传给对应函数：

```python
handler = TOOL_HANDLERS.get(block.name)
output = handler(**block.input) if handler else f"Unknown: {block.name}"
```

因此，新增工具主要需要三步：写好工具描述、实现处理函数、把名称注册到 `TOOL_HANDLERS`。模型只负责提出调用，不会直接运行这些 Python 函数。

## 循环本身没有改变

S02 的工具执行结果仍然按 `tool_use_id` 配对，并作为 `tool_result` 追加到消息历史。之后模型读取结果，再决定下一步做什么。核心变化可以概括为：

```python
# S01：工具写死
output = run_bash(block.input["command"])

# S02：按模型请求的工具名分发
handler = TOOL_HANDLERS[block.name]
output = handler(**block.input)
```

`while True`、模型请求、结果回传和停止条件都沿用 S01。工具从一个变成五个，不意味着要为每种工具复制一套 Agent Loop。

## 几个容易混淆的地方

- **工具描述不是工具实现。** Schema 让模型知道如何提出请求；本地 handler 才会执行操作。
- **这五个工具在教学实现中按返回顺序逐个执行。** 一次响应可以包含多个工具调用，但这里没有并行执行机制。
- **文件路径检查不等于所有工具都安全。** `safe_path` 用于文件类操作，Bash 仍然可以执行命令；简单的危险命令黑名单也不是完整的权限系统。下一节会进一步讨论执行前的权限检查。

## 当前的一句话理解

**S02 把工具从写死的单个 Bash 扩展成可描述、可实现、可分发的工具集合；Agent Loop 继续保持不变。**
