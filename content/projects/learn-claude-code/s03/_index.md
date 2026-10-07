---
title: "S03 Permission：工具执行前加一道权限门"
weight: 30
ShowToc: true
---

**源码范围：** 本节保留迁移前旧 20 章原型的学习记录。主目录编号已对齐新版，但这些教学摘录尚未逐段替换为更新后的本地实现；涉及现代产品行为的部分按文内官网来源说明。

## 我想弄清楚的问题

S02 里，模型一旦请求工具，Harness 就会分发并执行。可是工具可能改写文件、删除数据，甚至运行危险命令。只靠模型“应该知道什么安全”并不够，执行前还需要一层由程序控制的判断。

我的理解是：**工具调用是模型提出的行动建议，是否执行要由权限管线决定。** S03 在 S02 的工具分发之前加入检查；Agent Loop 仍然是原来的循环。

## 整体过程：从 S02 到 S03

图 1 复用 S02 总图的结构，以蓝色表示已有功能，包括文件工具实现。图 2 保留这些节点，为紫色权限检查增加空间。工具定义与本地执行分别可见，便于看清权限机制插在原循环的什么位置。

### 1. 上一轮：S02 的请求直接进入执行

{{< architecture from="/projects/learn-claude-code/s02" src="images/tool-dispatch.svg" mode="baseline" label="S02 已有工具分发系统，文件工具实现继续保留" caption="图 1：保留 S02 的节点、位置与连线，已有功能统一蓝色；文件工具实现将在下一张图继续可见。" >}}

S02 解决了“由哪个函数执行”，还需要补上“这次是否允许执行”。新增权限判断不会替换工具实现。

`TOOLS` 保存模型可见的名称、描述和参数 schema；`TOOL_HANDLERS` 将工具名映射到本地函数。文件工具框表示这些实际操作的实现，灰色虚线说明它们与分发入口的关联，不是另一条执行顺序。

### 2. 这一轮：S03 在执行入口插入权限层

{{< architecture legend="evolution" src="images/permission-flow.svg" label="S03 保留文件工具与工具定义，在实际执行之前增加权限检查" caption="图 2：S02 的八个已有节点保留在原位置，紫色权限检查加入下方。允许进入分发，拒绝直接返回工具结果；回传循环仍在最下方。" >}}

本节保留文件工具这个小框，内部函数的具体代码不在总图中展开。完整框架需要保留调用关系与能力归属，但不要求每个内部细节永久独立成框；[旧图与采用版本的对照记录](/reviews/s03-tool-ownership/)保存了这次选择。

| 对照位置 | S02 | S03 |
|----------|-----|-----|
| 执行前入口 | 请求直接进入名称分发与执行 | 先调用 `check_permission(block)` |
| 工具定义与实现 | 五个工具、schema 与 handler 表 | 继续保留 |
| 结果来源 | handler 的实际输出 | 获准时是输出，拒绝时是未执行说明 |
| 下一轮请求 | 配对结果追加到消息历史 | 两类结果都沿相同循环回到模型 |

拒绝结果也带原调用 ID。模型能够知道工具没有执行，再选择其他做法；一次拒绝不会直接替代整个 Agent 的停止判断。

### 3. 最小核心：决定执行、拒绝或暂停询问

{{< architecture legend="evolution" src="images/permission-core.svg" label="权限核心管线：硬拒绝、规则匹配、条件询问，以及放行和拒绝的结果路径" caption="图 3：只展开图 2 的权限判断。硬拒绝先挡下；未命中再查规则；只有需要确认时才询问用户。放行与拒绝最终都产出工具结果，完整 Agent 回环见图 2。" >}}

本节的最小机制是：**工具请求 → 判断是否允许 → 执行或生成拒绝结果 → 交还模型。** 不需要用户确认的调用直接放行；需要确认的调用停在询问处，得到明确批准后才执行。

## 三道检查怎样实现

### 1. 硬拒绝：不允许的命令直接挡下

代码先检查 Bash 命令是否包含拒绝列表中的模式：

```python
DENY_LIST = ["rm -rf /", "sudo", "shutdown", "reboot", "mkfs"]

def check_deny_list(command: str) -> str | None:
    for pattern in DENY_LIST:
        if pattern in command:
            return f"Blocked: '{pattern}' is on the deny list"
    return None
```

命中后不继续询问，也不会调用 Bash handler。

### 2. 规则匹配：判断是否需要用户确认

有些操作不能一概禁止，但风险较高时应该先问。例如，写入工作目录以外的位置，或 Bash 命令可能删除文件：

```python
PERMISSION_RULES = [
    {
        "tools": ["write_file", "edit_file"],
        "check": lambda args: not (WORKDIR / args.get("path", "")).resolve().is_relative_to(WORKDIR),
        "message": "Writing outside workspace",
    },
    {
        "tools": ["bash"],
        "check": lambda args: "rm " in args.get("command", ""),
        "message": "Potentially destructive command",
    },
]
```

规则把“什么情况需要确认”从工具执行代码中单独表达出来：

```python
def check_rules(tool_name: str, args: dict) -> str | None:
    for rule in PERMISSION_RULES:
        if tool_name in rule["tools"] and rule["check"](args):
            return rule["message"]
    return None
```

匹配到规则后，程序展示原因和工具参数，并等待用户输入；只有明确输入 `y` 或 `yes` 才允许：

```python
choice = input("Allow? [y/N] ").strip().lower()
decision = "allow" if choice in ("y", "yes") else "deny"
```

### 3. 把检查集中到一个入口

`check_permission` 先做硬拒绝，再检查需要询问的规则：

```python
def check_permission(block) -> bool:
    if block.name == "bash":
        reason = check_deny_list(block.input.get("command", ""))
        if reason:
            print(reason)
            return False

    reason = check_rules(block.name, block.input)
    if reason and ask_user(block.name, block.input, reason) == "deny":
        return False

    return True
```

工具循环只需在分发前调用它：

```python
if not check_permission(block):
    results.append({
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": "Permission denied.",
    })
    continue

output = TOOL_HANDLERS[block.name](**block.input)
```

被拒绝的调用也会变成工具结果交还模型。这样模型能知道操作没有执行，并据此调整做法或向用户解释。

## 和 S02 的关系

S02 解决“模型请求哪个工具，程序就调用哪个 handler”；S03 在调用 handler 之前加上权限判断。主循环、工具描述和分发表都保留，改变的是执行路径：

```text
S02：tool_use → handler → tool_result
S03：tool_use → permission check → handler 或拒绝结果
```

## 几个容易混淆的地方

- **模型的请求不等于用户授权。** 是否执行由 Harness 的规则和用户确认决定。
- **拒绝某次工具调用不等于结束整个 Agent 任务。** 拒绝结果回到模型后，它仍可能换一种方式继续。
- **这是教学用的简化权限系统。** 字符串黑名单可能漏掉命令变体；示例规则也只覆盖少数情况，不能当成可靠沙箱。它展示的是“把检查放在执行之前”的结构。

## 当前的一句话理解

**权限检查位于工具请求与实际执行之间：规则决定直接放行、直接拒绝，或暂停等待用户批准。**
