---
title: "S06 Subagent：给子任务一份独立上下文"
weight: 60
ShowToc: true
---

**源码范围：** 本节按当前本地仓库 `s06_subagent/code.py`（`ce8f9f1`）核对。它是独立教学脚本：保留基础工具和 Hook，加入子循环，但没有带入 S05 的 TODO 与三轮提醒。图中的红色只表示这两个示例之间的范围变化，不表示 TODO 能力被整个项目淘汰。

## 我想弄清楚的问题

主 Agent 为了解决一个子问题，可能读取大量文件、尝试多种办法。探索结束后，过程仍堆在主任务的消息历史里，影响后续阅读。

S06 增加 `task` 工具，让这段探索在另一份 `messages` 中完成。**父 Agent 提供明确任务，子 Agent 用自己的历史工作，最后把文本结论交回父循环。**

## 整体过程：从 S05 到 S06

第一张保留 S05 的实际结构，标出将修改的接口和本章示例未带入的组件。第二张展示 S06 的真实范围；第三张单独展开子循环。所有图都保留工具定义与实现的区别。

### 1. 上一轮：S05 的计划与执行循环

{{< architecture from="/projects/learn-claude-code/s05" src="images/todo-flow.svg" mode="baseline" modified="tools,handler,system" removed="reminder,todo-handler,todo-manager" removedLabel="红色虚线：S06 将省去该组件" label="S05 旧系统：工具接口与提示将修改，TODO 和提醒将在 S06 示例中移出" caption="图 1：节点与连线仍是 S05 的旧流程。橙色接口将在本轮调整；红色虚线提示 TODO handler、管理器和提醒未带入 S06，并非折叠到其他框中。" >}}

本地代码写的是 `TOOLS = [*BASE_TOOLS, TASK_TOOL]`，没有 `todo_write`、`TodoManager` 或提醒计数器。因此不能为了让图只增长，就把它们画成 S06 仍在运行的模块。

### 2. 这一轮：在工具执行处调用另一段循环

{{< architecture legend="evolution" removedLabel="红色虚线：S06 示例未包含" src="images/subagent-flow.svg" label="S06 沿用原来的工具小框，简记 TODO 的 S05 实现链接，完整展开 Subagent 分支并连接父循环" caption="图 2：原工具小框保留 read / write / edit / glob，只补上 TODO → S05 的历史索引。本章的 task、新消息历史、子循环、返回文本与子配置完整接在整体系统上；子任务返回后才进入父调用的 PostToolUse。" >}}

S05 已经讲过的 TodoWrite，在这个小框中只留 [TODO → S05](/projects/learn-claude-code/s05/#todo-tool-implementation) 的实现索引；图 2 不再展开它的管理器、状态更新与提醒。原来的文件工具仍简记为 read / write / edit / glob，不另外展开 Shell 或能力目录。

本章正在学习的 Subagent 则像 S05 当时展开 TodoWrite 一样，作为完整分支连接工具分发、子上下文、子循环和返回位置。第三张图再放大内部机制。TODO 链接只是复习入口，当前 S06 示例仍未包含它；三轮提醒属于父循环，说明保留在 [S05](/projects/learn-claude-code/s05/#todo-loop-reminder)。

| 位置 | S05 | S06 |
|---|---|---|
| SYSTEM | 引导规划、更新 TODO | 引导聚焦的子任务委派 |
| 父工具表 | 五个基础工具 + `todo_write` | 五个基础工具 + `task` |
| 工具执行入口 | 循环内做权限检查、分发和后置处理 | 提取为父子共用的 `execute_tool` |
| 计划状态与提醒 | TODO 管理器、三轮提醒 | 本章独立脚本未包含 |
| 子任务上下文 | 没有独立子循环 | 新建消息历史，最多运行 30 轮 |
| 基础工具与 Hook | 已有 | 继续使用，子工具也经过权限检查 |

`task` 是工具分发中的一个分支。普通工具完成实际操作；`task` 的 handler 则运行另一段 Agent Loop。子循环只把返回文本交回当前工具调用，父循环随后继续。

<span id="subagent-core"></span>

### 3. 最小核心：新消息历史、子循环、最终文本

{{< architecture legend="evolution" removedLabel="红色虚线：S06 示例未包含" src="images/subagent-core.svg" label="子任务用新的 messages 请求模型，共用工具执行入口，结束后返回最终文本" caption="图 3：紫色是新增的子任务上下文与循环；橙色 execute_tool 将原权限、分发和后置处理整理成共享入口。子工具结果沿下方回环进入子历史；最终文本才回到蓝色父流程。共享 WORKDIR 是原有条件，本轮单独展开。" >}}

这里的边界是消息历史。父 Agent 不拿到子 Agent 的完整对话，但能看到子 Agent 对共享文件做出的修改。

## task 怎样描述一个子任务

当前参数叫 `prompt`，工具入口是 `run_subagent`。模型可见的 schema 如下：

```python
TASK_TOOL = {
    "name": "task",
    "description": (
        "Run a subagent with fresh conversation context "
        "and return its final text."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "minLength": 1},
        },
        "required": ["prompt"],
    },
}

TOOLS = [*BASE_TOOLS, TASK_TOOL]
TOOL_HANDLERS = {**BASE_HANDLERS, "task": run_subagent}
```

`BASE_TOOLS` 是五个基础工具的定义；`BASE_HANDLERS` 指向 Bash 与文件操作函数。新增的是 `task` 定义和它对应的 handler，不是另一套父工具分发协议。

schema 要求非空字符串，但源码的 `run_subagent` 没有额外做同样的参数校验，不能把 schema 当成 handler 中已经写好的检查。

因为子 Agent 不继承父对话，`prompt` 应交代目标、相关文件、约束和希望返回什么。例如：

```json
{
  "prompt": "检查 src/auth.py 的调用路径，找出重复登录请求的可能原因。先不要修改文件；返回相关函数、证据和建议验证步骤。"
}
```

只说“继续刚才的调查”不够，子 Agent 没有父历史中的“刚才”。

## 新建的是上下文，而不是工作目录

子任务入口先创建局部消息列表：

```python
def run_subagent(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    # 之后所有子工具调用和结果都追加到这个列表
```

父循环原来的 `messages` 没有传入，也没有复制给子循环。子 Agent 的初始信息由任务描述、自己的系统提示和工具定义组成：

```python
SUB_SYSTEM = (
    f"You are a coding agent at {WORKDIR}. "
    "Complete the given task, then return a concise final answer."
)

SUB_TOOLS = list(BASE_TOOLS)
SUB_HANDLERS = dict(BASE_HANDLERS)
```

这里省略了源码中的环境说明。子 Agent 只有 Bash、读取、写入、编辑和查找五个工具，没有 `task`，所以本章没有递归委派；父子也都没有 TODO 工具。

工作目录则共享。源码只设置一个 `WORKDIR`，父子分发表都引用这些基础函数：

```python
WORKDIR = Path.cwd()

def run_write(path: str, content: str) -> str:
    # 摘录写入路径，省略异常处理与返回文案
    file_path = (WORKDIR / path).resolve()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

# run_bash 中同样使用 cwd=WORKDIR
```

`run_subagent` 没有新建进程、目录或 worktree。子 Agent 修改文件后，父 Agent 可以读取同一份文件。独立的消息历史不等于独立的文件系统。

## 子工具为什么仍然经过权限检查

S06 将工具执行的共同流程提取到 `execute_tool`：

```python
def execute_tool(block, handlers: dict) -> str:
    blocked = trigger_hooks("PreToolUse", block)
    if blocked:
        return str(blocked)

    handler = handlers.get(block.name)
    try:
        output = handler(**block.input) if handler else f"Unknown: {block.name}"
    except Exception as error:
        output = f"Error: {error}"

    trigger_hooks("PostToolUse", block, output)
    return str(output)
```

父循环传 `TOOL_HANDLERS`，子循环传 `SUB_HANDLERS`；二者共用 Hook 注册表。当前权限回调包含 Bash 拒绝列表、部分风险命令确认，以及读写编辑工具的工作区外路径确认。旧文中“只有 Bash 拒绝列表”的说明已不适用于当前源码。

这里有两层工具调用：父循环先对 `task` 触发一次前置 Hook；子循环中的每次实际工具调用也各自触发前后 Hook。等子循环返回，父 `task` 调用才触发自己的后置 Hook。

父子无工具调用时都会进入各自的 `Stop` 判断。子入口没有再触发 `UserPromptSubmit`；源码只在外层用户输入时触发它。共享注册表不意味着每个事件在父子入口都执行一次。

## 发出 task 后，父 Agent 会做什么

它同步等待。父循环执行到下面这一句时，会一直留在调用栈中，直到子循环返回：

```python
output = execute_tool(block, TOOL_HANDLERS)
# 如果 block.name == "task"：
# execute_tool -> run_subagent(prompt) -> 子循环结束 -> 返回文本
```

之后才构造父工具结果：

```python
results.append({
    "type": "tool_result",
    "tool_use_id": block.id,
    "content": output,
})
```

同一响应有多个工具调用时，代码也按顺序处理；后面的工具要等当前 `task` 返回。这里没有后台线程、异步任务或让父模型同时继续工作的调度机制。

## 返回的是最终文本，不是完整子历史

子循环在响应中找不到 `tool_use`，并且 `Stop` 没有要求续跑时，返回：

```python
return extract_text(response.content) or "(no summary)"
```

`extract_text` 只提取最终响应里的文本块；它不会额外调用模型来压缩整份历史。简短结论来自 `SUB_SYSTEM` 对模型的要求。

| 结束情况 | 返回父循环的内容 |
|---|---|
| 正常结束且有文本 | 最终响应的文本 |
| 正常结束但没有文本 | `(no summary)` |
| 30 轮仍未结束 | `Subagent stopped after 30 turns without a final answer.` |

这里的 30 轮是子循环迭代上限，包括 `Stop` 要求续跑的轮次，不是 30 个工具调用或固定的时间上限。达到上限直接返回说明，当前代码不会回头搜索早期 assistant 消息作为摘要。

子历史没有整体复制回父历史，也没有持久化或恢复机制。终端可能显示子工具的日志和部分输出，这与它们是否进入父 `messages` 是两件事。最终文本也只是一份报告，父 Agent 仍需按任务要求检查文件改动或测试证据。

## 把子循环串回已有 Agent Loop

下面按源码顺序整理为伪代码，省略 API 参数、日志与消息字典的具体构造：

```python
def run_subagent(prompt):
    child_messages = [user_message(prompt)]

    for turn in range(30):
        response = ask_llm(SUB_SYSTEM, SUB_TOOLS, child_messages)
        child_messages.append(assistant_message(response))
        calls = extract_tool_calls(response)

        if not calls:
            feedback = trigger_hooks("Stop", child_messages)
            if feedback:
                child_messages.append(user_message(feedback))
                continue
            return extract_text(response.content) or "(no summary)"

        results = []
        for call in calls:
            output = execute_tool(call, SUB_HANDLERS)
            results.append(tool_result(call.id, output))
        child_messages.append(user_message(results))

    return "Subagent stopped after 30 turns without a final answer."


# 父循环：仍使用自己的历史、SYSTEM 和工具表
trigger_hooks("UserPromptSubmit", query)
parent_messages.append(user_message(query))

while True:
    response = ask_llm(SYSTEM, TOOLS, parent_messages)
    parent_messages.append(assistant_message(response))
    calls = extract_tool_calls(response)

    if not calls:
        feedback = trigger_hooks("Stop", parent_messages)
        if feedback:
            parent_messages.append(user_message(feedback))
            continue
        break

    results = []
    for call in calls:
        output = execute_tool(call, TOOL_HANDLERS)
        # task 在这里同步运行上面的子循环，返回后才继续
        results.append(tool_result(call.id, output))
    parent_messages.append(user_message(results))
```

这一轮改变的是：**工具分发表多了一个能运行独立消息循环的 handler；父循环的请求、判断与结果回传仍然存在。** S05 的 TODO 和提醒未带入这个示例，应按实际代码标出，而不能当作被隐藏的保留功能。

## 当前的一句话理解

**Subagent 在独立消息历史中处理子任务，再把最终文本作为普通工具结果交回父 Agent；本章父 Agent 同步等待，父子共享工作目录与工具策略。**

源码对照：[S06 实现](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f1/s06_subagent/code.py)、[子 Agent 测试](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f1/tests/test_s06_subagent.py)。
