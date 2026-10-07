---
title: "S05 TodoWrite：把计划放进 Agent 的工作流"
weight: 50
ShowToc: true
---

**源码范围：** 本节已按当前本地仓库的 `s05_todo_write/code.py` 核对。图 1 复用博客 S04 总图的结构，标出本轮将扩展的旧接口；本节介绍教学实现，不将固定三轮提醒等设计视为现代 Claude Code 的内部规则。

## 我想弄清楚的问题

工具和 Hook 已经能帮助 Agent 执行与检查行动，但它做了几步之后，仍可能被眼前的工具结果带偏，忘记还有哪些工作没有完成。

S05 增加 `todo_write`，让模型把计划与进度变成显式状态。**TODO 记录要做什么、做到哪里；真正的工作仍由原工具完成。**

## 整体过程：从 S04 到 S05

先认出上一轮，再看这一轮的变化，最后单独理解 TODO 核心。图 1 保留 S04 的结构，橙色标出本轮将扩展的工具表与分发接口，仍展示旧实现；图 2、图 3 展示蓝色保留、橙色改造后的接口、紫色新增机制。本节没有真实移除的功能。

### 1. 上一轮：S04 在原循环中触发 Hook

{{< architecture from="/projects/learn-claude-code/s04" src="images/hooks-flow.svg" mode="baseline" modified="tools,handler" label="S04 旧系统：橙色工具表与分发接口将在 S05 扩展" caption="图 1：保留 S04 的结构；橙色工具表和分发接口是本轮将扩展的旧部分，其他功能蓝色。不补画 SYSTEM、TODO 或提醒计数器。" >}}

输入、执行前后和结束时的 Hook 已经存在，但没有专门管理计划的工具。

### 2. 这一轮：把计划更新接入同一套工具循环

{{< architecture legend="evolution" src="images/todo-flow.svg" label="S05 保留 Hook 与工具循环，改造工具表和规划提示，新增 TODO 状态与结果提醒" caption="图 2：蓝色保留 S04 流程；橙色工具表、分发表与 SYSTEM 被扩展。紫色 TODO 分支管理内存状态，紫色计数与提醒接在结果回传之前。灰色虚线表示实现关联，不是另一条执行循环。" >}}

| 位置 | S04 | S05 |
|---|---|---|
| 请求模型 | 通用 SYSTEM、五个工具 | SYSTEM 增加规划要求，TOOLS 增加 `todo_write` |
| 分发执行 | 按工具名找到 handler | 分发表增加 TODO handler，原执行方式保留 |
| 计划状态 | 没有专门的 TODO 管理器 | 新增内存中的 `TodoManager.items` |
| 回传结果 | 工具输出组成 `tool_result` | 记录本轮是否使用 TODO，必要时将提醒附在同一结果消息中 |
| 输入、权限、执行后、结束 | S04 的 Hook 机制 | 继续保留，不用 TODO 替代 |

`SYSTEM` 原先就参与模型请求，只是没有单独画框。本轮展开它并用橙色表示内容修改。用户输入已经在 S04 画出，本轮保留蓝色，不再标为“本轮展开”。

蓝色文件工具实现继续保留在原位置；橙色分发框表示映射表增加了 `todo_write`，按名称查找 handler 的方式仍沿用。新增的 TODO handler 在下方单独展开，工具定义与本地实现各有清楚的归属。

### 3. 最小核心：校验整份清单，替换状态，回传进度

{{< architecture legend="evolution" src="images/todo-core.svg" label="TodoWrite 核心：模型提交清单，管理器校验并替换内存状态，将进度回传" caption="图 3：TODO 更新走普通工具调用路径；下方计数器只决定是否附加提醒。计划不会自动执行，状态也不会自动推进。" >}}

这里有两条配合的机制：**模型主动更新清单；Harness 在连续未使用 TODO 的工具轮次后提醒模型。**

## 先让模型知道：什么时候计划，参数怎么传

SYSTEM 增加规划要求：

```python
SYSTEM = (
    f"You are a coding agent at {WORKDIR}. "
    "Before starting any multi-step task, use todo_write to plan your steps. "
    "Update status as you go."
)
```

这是引导，不是一个阻止“没有计划就执行”的硬门禁。源码还有环境说明，此处省略与规划无关的部分。

工具的输入 schema 则定义清单形状，下面保留当前实现的关键约束：

```python
todo_tool = {
    "name": "todo_write",
    "description": "Create and manage a task list for your current coding session.",
    "input_schema": {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "maxItems": 20,
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "minLength": 1},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                        },
                    },
                    "required": ["content", "status"],
                },
            },
        },
        "required": ["todos"],
    },
}
```

`todos` 是整份列表，最多 20 项；每项都有任务描述和三选一的状态。示例参数：

```json
{
  "todos": [
    {"content": "检查现有模块", "status": "completed"},
    {"content": "实现所需改动", "status": "in_progress"},
    {"content": "运行测试", "status": "pending"}
  ]
}
```

然后加入原有工具表与分发表：

```python
TOOLS.append(todo_tool)
TOOL_HANDLERS["todo_write"] = run_todo_write
```

模型决定调用哪个工具，原 handler 分发机制负责执行。TODO 没有专属的模型循环。

<span id="todo-tool-implementation"></span>

## 管理器保存什么，怎样接受更新

当前实现用 `TODO = TodoManager()` 保存内存状态。下面是其主要校验与替换逻辑的教学摘录，省略字符串兼容解析和部分错误信息：

```python
class TodoManager:
    def __init__(self):
        self.items = []

    def update(self, todos):
        if not isinstance(todos, list):
            raise ValueError("todos must be a list")
        if len(todos) > 20:
            raise ValueError("Max 20 todos allowed")

        validated = []
        active = 0
        for todo in todos:
            if not isinstance(todo, dict):
                raise ValueError("Each todo must be an object")
            content = str(todo.get("content", "")).strip()
            status = str(todo.get("status", "pending")).lower()
            if not content:
                raise ValueError("Content must not be empty")
            if status not in ("pending", "in_progress", "completed"):
                raise ValueError("Invalid status")
            active += status == "in_progress"
            validated.append({"content": content, "status": status})

        if active > 1:
            raise ValueError("Only one todo can be in_progress at a time")

        self.items = validated
        return self.render()
```

**先校验全部条目，再替换旧列表。** 更新失败时，旧计划保留；更新成功时，整份清单被覆盖，模型可以同时调整步骤与状态。

原实现还接受字符串形式的列表：先尝试 `json.loads`，再尝试 `ast.literal_eval`，没有使用 `eval`。这是 handler 的兼容处理，schema 仍要求数组。

## Schema 与运行时检查的区别

| 约束 | Schema | 管理器 |
|---|---|---|
| 输入为列表、每项为对象 | 描述类型 | 显式检查解析后的类型 |
| 最多 20 项 | `maxItems: 20` | 检查长度 |
| 描述不能为空 | `minLength: 1` | 去掉首尾空白后检查；也会转换成字符串 |
| 状态合法 | 必需字段、枚举 | 默认 `pending`，转小写后检查 |
| 最多一项进行中 | 未表达跨条目约束 | 统计 `in_progress` 数量并拒绝超限 |

两者并非完全相同：schema 是模型应该提交的接口约定，handler 还有自己的校验与兼容行为。不能仅凭 schema 就推断本地会怎样处理所有输入。

当前实现允许空列表；也不强制状态只能按 `pending → in_progress → completed` 转换。它是一份可覆盖的计划快照，还不是带依赖关系、自动调度和状态迁移规则的任务系统。

## 进度怎样回到模型

管理器把清单渲染成文本，handler 将其打印到终端并返回：

```python
TODO = TodoManager()

def run_todo_write(todos):
    try:
        output = TODO.update(todos)
    except ValueError as error:
        return f"Error: {error}"
    print(output)  # 此处省略终端标题与颜色
    return output
```

返回结果类似：

```text
[x] 检查现有模块
[>] 实现所需改动
[ ] 运行测试

(1/3 completed)
```

这个文本沿普通 `tool_result` 路径加入消息历史，所以模型能在后续请求中看到进度。**源码没有在每次请求前把整个 TODO 列表重新注入 SYSTEM。**

本节也没有将清单写入 `.tasks/current_todos.json` 或自动加载文件。状态存在当前进程的管理器中，不能据此认为它已经实现跨进程或跨会话持久化。

<span id="todo-loop-reminder"></span>

## 提醒插在回传前，而不是另开一个循环

循环每轮记录是否实际进入了 `todo_write` 的 handler 路径：

```python
rounds_since_todo = 0 if used_todo else rounds_since_todo + 1
if rounds_since_todo >= 3:
    results.append({
        "type": "text",
        "text": "<reminder>Update your todos.</reminder>",
    })
    rounds_since_todo = 0

messages.append({"role": "user", "content": results})
```

一次模型响应有多个工具调用，仍只算一个工具轮次；没有工具调用的响应走 Stop 分支，不计入这里。

连续三轮没有使用 TODO 时，第三轮结果消息里同时包含 `tool_result` 与提醒文本，随后计数清零。下一次模型请求自然会读到它。模型仍需主动决定是否更新计划。

源码按工具名标记“使用过 TODO”，不检查更新是否成功：handler 返回校验错误，也会清零；若在 `PreToolUse` 阶段被拒绝，则不会标记为已使用。这个计数器记录的是调用路径，不是成功更新次数。

## 把 S05 串回已有 Agent Loop

下面是按当前源码控制流程整理的伪代码，省略 API 参数和结果字典构造细节：

```python
# 输入阶段：沿用 S04
trigger_hooks("UserPromptSubmit", query)
messages.append(user_message(query))

rounds_since_todo = 0  # 每次进入 agent_loop 重新开始
while True:
    response = ask_llm(SYSTEM, TOOLS, messages)
    messages.append(assistant_message(response))
    calls = extract_tool_calls(response)

    if not calls:
        feedback = trigger_hooks("Stop", messages)
        if feedback:
            messages.append(user_message(feedback))
            continue
        break

    results = []
    used_todo = False                 # S05 新增：本轮是否使用 TODO
    for call in calls:
        blocked = trigger_hooks("PreToolUse", call)
        if blocked:
            results.append(tool_result(call.id, blocked))
            continue

        output = dispatch_with_error_capture(call)
        # todo_write -> TODO.update()；其他工具 -> 原有实际工作
        trigger_hooks("PostToolUse", call, output)
        if call.name == "todo_write":
            used_todo = True          # 不等于更新成功
        results.append(tool_result(call.id, output))

    rounds_since_todo = 0 if used_todo else rounds_since_todo + 1
    if rounds_since_todo >= 3:        # S05 新增：回传前附加提醒
        results.append(reminder_text("Update your todos."))
        rounds_since_todo = 0

    messages.append(user_message(results))
    # 原有回环：把工具结果与可能的提醒一起交给模型
```

新增部分集中在三个位置：**请求前的工具与提示定义、分发中的 TODO handler、结果回传前的计数与提醒。** S04 的 Hook 仍处于原来的调用时机。

## 当前的一句话理解

**TodoWrite 让模型显式管理计划与进度，再借原有工具回环读到自己的更新；它记录工作，不执行工作，也不证明工作已经完成。**

源码对照：[S05 教学实现](https://github.com/shareAI-lab/learn-claude-code/blob/main/s05_todo_write/code.py)。
