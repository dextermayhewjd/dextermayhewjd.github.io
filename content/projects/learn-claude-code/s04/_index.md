---
title: "S04 Hooks：把扩展逻辑挂在循环上"
weight: 40
ShowToc: true
---

**源码范围：** 本节保留迁移前旧 20 章原型的学习记录。主目录编号已对齐新版，但这些教学摘录尚未逐段替换为更新后的本地实现；涉及现代产品行为的部分按文内官网来源说明。

## 我想弄清楚的问题

S03 把权限判断放在工具执行前。但如果接下来还要加日志、输入检查、输出检查和结束时的收尾逻辑，是不是每加一种行为，都得继续改 `agent_loop`？这样主循环会渐渐塞满各种细节。

S04 用 Hook 把这些扩展逻辑移到循环外：循环在关键时机发出事件，已注册的回调负责处理对应工作。**循环负责控制流程，Hook 负责响应事件。**

## 整体过程：从 S03 到 S04

第一张图复用 S03 总图的结构，让我直接认出上一章看到的流程：蓝色保留，橙色权限检查是本轮将改造的旧模块。第二张图展示 S04 的改造结果，第三张图单独解释 Hook 核心。第一张不补节点、不重排，仍展示原来的权限实现。

**两张总图都以本轮变化为参照。** 图 1 的橙色权限检查表示“将改造”，图 2 的橙色权限回调表示“改造后的实现”；蓝色保留、紫色新增等规则不变。

| 标记 | 含义 | 本节例子 |
|------|------|----------|
| 蓝色 | 已有且保留 | 用户输入、历史、工具、执行、回传、结束动作 |
| 橙色 | 已有对象被修改或职责迁移 | 权限函数改成回调，返回约定改变 |
| 紫色 | 真正新增 | 事件触发点、注册机制、日志回调 |
| 红色虚线／删除线 | 对象移出或被替换，不参与当前路径 | 本节没有整个旧功能被删除，因此不强行画红块 |
| 灰色来源标签 | 已有但之前未展开，仍是蓝色对象 | “用户输入：原先已有，本轮展开” |

颜色描述系统变化；来源标签说明这次是否展开了旧细节。**图上第一次出现，不等于系统里第一次存在。** 用户输入在 S03 已经存在，只是包含在“对话历史”之前；所以图 1 不补画，图 2 才展开蓝色输入入口，并在它与历史之间新增紫色 `UserPromptSubmit`。

### 1. 上一轮：S03 直接调用权限判断

{{< architecture from="/projects/learn-claude-code/s03" src="images/permission-flow.svg" mode="baseline" modified="permission-site" label="S03 旧权限系统：橙色权限检查将在 S04 改造成回调" caption="图 1：保留 S03 的结构，橙色权限检查是本轮将改造的旧模块；其他功能蓝色，不补画用户输入。" >}}

权限保护已经存在。S04 要改变的是主循环怎样调用这些扩展逻辑，并让日志、输出观察和收尾也能挂接进来。

### 2. 这一轮：S04 把扩展逻辑挂在事件点

{{< architecture legend="evolution" src="images/hooks-flow.svg" label="S04 展开蓝色已有输入，新增紫色 Hook，并将原权限逻辑改造为橙色回调" caption="图 2：以 S03 为参照，蓝色保留、橙色修改、紫色新增。蓝色用户输入是本轮首次展开的旧步骤；灰色虚线表示注册关系。工具结果和 Stop 反馈直接回到历史。" >}}

| 对照位置 | S03 | S04 |
|----------|-----|-----|
| 用户输入入口 | 已有输入与历史写入 | 输入仍保留，另加紫色 `UserPromptSubmit` |
| 执行工具之前 | 已有权限函数 | 权限逻辑橙色改造为回调，另加紫色 `PreToolUse` |
| handler 返回之后 | 已有工具输出和结果构造 | 输出与回传保留，另加紫色 `PostToolUse` |
| 不再请求工具时 | 已有结束动作 | 结束仍保留，另加紫色 `Stop` 判断与条件续跑 |
| 工具与历史 | 五个工具、名称分发和配对结果 | 继续保留 |

这里没有让 Hook 代替模型决策或工具执行。它把扩展行为接到原流程的明确位置，事件的调用处仍掌握是否继续。

`check_permission` 的调用位置被改造、判断逻辑转为 `permission_hook`，属于修改与职责迁移；权限保护没有消失。输入入口也是已有步骤，真正新增的是在它与历史之间触发事件。图 2 保留上方主流程、工具定义和文件工具实现的位置，下方为事件和回调腾出空间；结束动作、权限模块的位置调整不表示它们被删除后重建。

文件工具继续由原分发表调用，灰色虚线表示实现关联；权限和日志回调的虚线表示注册关联。TOOLS 保存工具定义，这些本地实现与回调的归属分别标在各自调用位置。

### 3. 最小核心：登记回调，再在事件处触发

{{< architecture legend="evolution" src="images/hooks-core.svg" label="Hook 最小核心：新增注册与调度机制接入已有改造权限回调和新日志回调" caption="图 3：只展开 Hook 机制。紫色注册与调度器可以运行橙色的原权限行为，也可以运行紫色新日志；灰色虚线说明回调关联，返回值仍由主流程解释。" >}}

核心链路是：**先注册 → 原流程触发事件 → 顺序运行回调 → 返回给调用处 → 主流程处理结果。** 注册不是执行，触发事件也不必导致停止。

## Hook 如何组织

一个事件可以注册多个回调，注册表按事件名保存回调列表：

```python
HOOKS = {
    "UserPromptSubmit": [],
    "PreToolUse": [],
    "PostToolUse": [],
    "Stop": [],
}

def register_hook(event, callback):
    HOOKS[event].append(callback)

def trigger_hooks(event, *args):
    for callback in HOOKS[event]:
        result = callback(*args)
        if result is not None:
            return result
    return None
```

`register_hook` 负责登记回调；循环到达相应时机时，`trigger_hooks` 按注册顺序调用它们。遇到第一个非 `None` 返回值，就停止这一事件的后续回调并将该值交给调用处。它是否改变流程，还取决于调用处怎样使用返回值。

## 四个事件放在 Agent 流程中的位置

- `UserPromptSubmit`：用户输入送给模型之前。示例只打印当前工作目录。
- `PreToolUse`：工具执行之前。权限检查和工具调用日志放在这里。
- `PostToolUse`：工具执行之后。示例检查输出是否过大。
- `Stop`：Agent Loop 准备结束时。示例统计本轮工具调用次数。

### 用户输入时：`UserPromptSubmit`

入口收到用户输入后、把输入加入历史并请求模型之前，会触发这个事件。当前回调只打印工作目录，展示“在请求模型前运行逻辑”的位置：

```python
def context_inject_hook(query: str):
    print(f"[HOOK] working in {WORKDIR}")
    return None

register_hook("UserPromptSubmit", context_inject_hook)

trigger_hooks("UserPromptSubmit", query)
history.append({"role": "user", "content": query})
agent_loop(history)
```

名字里有 `inject`，但这个示例并没有修改或注入 prompt；它只是记录日志。

## 把权限检查改成 Hook

S03 的权限逻辑可以包装成 `PreToolUse` 回调，再和日志回调一起注册：

```python
def permission_hook(block):
    if block.name == "bash":
        command = block.input.get("command", "")
        if any(pattern in command for pattern in DENY_LIST):
            return "Permission denied by deny list"
        if any(word in command for word in DESTRUCTIVE):
            choice = input("Allow? [y/N] ").strip().lower()
            if choice not in ("y", "yes"):
                return "Permission denied by user"

    if block.name in ("write_file", "edit_file"):
        path = block.input.get("path", "")
        target = (WORKDIR / path).resolve()
        if not target.is_relative_to(WORKDIR):
            choice = input("Writing outside workspace. Allow? [y/N] ").strip().lower()
            if choice not in ("y", "yes"):
                return "Permission denied by user"
    return None

def log_hook(block):
    print(f"[HOOK] {block.name}")
    return None

register_hook("PreToolUse", permission_hook)
register_hook("PreToolUse", log_hook)
```

`PreToolUse` 的回调按注册顺序运行。`trigger_hooks` 遇到第一个非 `None` 返回值就会停止调用后续回调；所以权限 Hook 拒绝工具时，后面的日志 Hook 在这个实现中也不会运行。

返回约定也发生了变化：S03 的权限函数用布尔值表示是否允许；这里的权限回调用 `None` 表示继续，用拒绝说明交给 PreToolUse 调用处处理。因此循环从 `if not check_permission(...)` 改成取得 `blocked` 后判断它是否为真。

这里有两类权限判断：Bash 命令先经过硬拒绝列表，可能有破坏性的命令需要用户确认；文件写入和编辑则检查目标路径是否位于工作目录内，写到目录外时询问用户。它们都是示例规则，不构成完整的安全边界。

循环不需要知道权限规则和日志细节，只要在执行前触发事件：

```python
blocked = trigger_hooks("PreToolUse", block)
if blocked:
    results.append({
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": str(blocked),
    })
    continue

output = TOOL_HANDLERS[block.name](**block.input)
trigger_hooks("PostToolUse", block, output)
```

被拦截时，循环把原因作为工具结果送回模型；放行时才执行工具，然后触发 `PostToolUse`。

工具执行之后，`PostToolUse` 回调能同时看到调用和输出。示例在输出超过 100000 个字符时给出提示：

```python
def large_output_hook(block, output):
    if len(str(output)) > 100000:
        print(f"[HOOK] Large output from {block.name}")
    return None

register_hook("PostToolUse", large_output_hook)
```

当前主循环不会使用这个 Hook 的返回值，所以它用于观察或副作用，不会拦截已经执行完的工具。

## Stop Hook 可以影响循环

这个示例里，`Stop` 回调不只做收尾统计。如果它返回了内容，Agent Loop 会把内容追加到消息历史并继续请求模型；返回空值则正常结束：

```python
if response.stop_reason != "tool_use":
    force = trigger_hooks("Stop", messages)
    if force:
        messages.append({"role": "user", "content": force})
        continue
    return
```

因此，Hook 的效果取决于事件位置和循环如何处理回调返回值。它不是自动生效的魔法：要由主流程触发，并定义返回值的含义。

示例里的 Stop Hook 统计消息历史中已经回传的工具结果：

```python
def summary_hook(messages):
    tool_count = sum(
        1 for message in messages
        for block in (message.get("content")
                      if isinstance(message.get("content"), list) else [])
        if isinstance(block, dict) and block.get("type") == "tool_result"
    )
    print(f"Session used {tool_count} tool calls")
    return None
```

```python
register_hook("Stop", summary_hook)
```

在这个实现中，`UserPromptSubmit` 和 `PostToolUse` 的返回值也会被 `trigger_hooks` 返回，但调用它们的位置没有读取这个值；真正会据返回值改变流程的是 `PreToolUse`（拦截工具）和 `Stop`（注入消息并续跑）。

## 把四类事件接回原循环

下面是控制流程伪代码，省略 SDK 适配与异常处理。用户输入事件位于入口，工具结果与 Stop 反馈直接回到内部循环，不再次经过用户输入事件：

```python
trigger_hooks("UserPromptSubmit", query)
messages.append(user(query))

while True:
    response = call_model(system=SYSTEM, tools=TOOLS, messages=messages)
    messages.append(assistant(response.content))
    calls = get_tool_use_blocks(response.content)

    if not calls:
        follow_up = trigger_hooks("Stop", messages)
        if follow_up:
            messages.append(user(follow_up))
            continue
        break

    results = []
    for call in calls:
        blocked = trigger_hooks("PreToolUse", call)
        if blocked:
            output = str(blocked)
        else:
            output = TOOL_HANDLERS[call.name](**call.input)
            trigger_hooks("PostToolUse", call, output)
        results.append(tool_result(call.id, output))
    messages.append(user(results))
```

这条链保留了 S03 的权限拒绝回传，也解释了两个新增位置：PostToolUse 观察已执行的结果，Stop 可以要求继续一轮。当前示例登记的 Stop 统计回调返回 `None`，所以默认仍会结束；可续跑是调用处支持的能力，不是每次都会发生。

## 和 S03 的关系

S03 在循环里直接调用 `check_permission(block)`；S04 把权限判断注册为 Hook，由循环在 `PreToolUse` 时统一触发。新增日志或输出检查时，只需注册新的回调，不必把细节继续堆进主循环。

## 当前的一句话理解

**Hook 是 Agent 流程中的扩展点：主循环在关键时机触发事件，回调添加行为，循环本身继续保持清楚。**
