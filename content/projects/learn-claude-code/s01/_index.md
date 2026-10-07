---
title: "S01 Agent Loop：模型提出行动，Harness 推动循环"
weight: 10
ShowToc: true
---

**源码范围：** 本节保留迁移前旧 20 章原型的学习记录。主目录编号已对齐新版，但这些教学摘录尚未逐段替换为更新后的本地实现；涉及现代产品行为的部分按文内官网来源说明。

## 我想弄清楚的问题

模型可以告诉我“应该运行什么命令”，但光有这句话，文件并不会被读取，程序也不会真的运行。要让模型根据执行结果继续工作，程序需要把它和外部工具连接起来。

我现在的理解是：**模型负责判断下一步，Harness 负责执行工具并把观察结果送回来。** 让两者持续配合的，就是 Agent Loop。

## 整体过程

{{< architecture src="images/agent-loop.svg" label="Agent Loop 主流程与下方的工具回传循环" caption="S01 是基础系统起点，所有功能节点统一蓝色。模型提出工具请求，Harness 执行并将结果追加到历史；下方箭头表示继续下一轮。" >}}

因此，一个 Agent 任务通常不是一次模型调用，而是多轮“决策 → 执行 → 观察”。

## 一轮循环如何工作

### 1. 保存用户任务

用户输入先成为消息历史的第一条内容：

```python
messages = [{"role": "user", "content": query}]
```

后续的模型回答和工具结果也会追加到 `messages`，组成模型下一轮需要的上下文。

### 2. 把上下文和工具交给模型

每轮请求都带上对话历史、系统指令和工具定义。工具定义告诉模型有哪些操作可选，以及参数应该是什么格式。

```python
response = client.messages.create(
    model=MODEL,
    system=SYSTEM,
    messages=messages,
    tools=TOOLS,
    max_tokens=8000,
)
```

模型不会因此直接访问终端。它返回的是普通文本，或描述工具名称和参数的结构化请求。

### 3. 判断是否继续

先把模型回答保存进历史，再根据响应判断是否需要执行工具。S01 通过 `stop_reason` 判断：值为 `tool_use` 就继续；否则结束当前循环。

```python
messages.append({"role": "assistant", "content": response.content})

if response.stop_reason != "tool_use":
    return
```

<span id="bash-tool-implementation"></span>

### 4. 执行工具请求

模型提出请求，Harness 才是真正执行操作的一方。S01 只有一个 Bash 工具，因此 Harness 从请求中取出命令，再交给 `run_bash`：

```python
for block in response.content:
    if block.type == "tool_use":
        output = run_bash(block.input["command"])
```

工具执行完成后，Harness 收集输出。若响应里有多个工具调用块，就逐个处理。

### 5. 把结果送回模型

每个结果通过 `tool_use_id` 与对应请求配对，然后追加到消息历史：

```python
results.append({
    "type": "tool_result",
    "tool_use_id": block.id,
    "content": output,
})

messages.append({"role": "user", "content": results})
```

循环回到模型请求处。模型现在能看到工具实际返回了什么，可以继续行动，也可以给出最终回答。

## 把步骤连起来

```python
def agent_loop(messages):
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return

        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = run_bash(block.input["command"])
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})
```

## 几个容易混淆的地方

- **工具请求不等于工具执行。** 模型决定调用什么；Harness 根据请求找到并运行本地工具。
- **`role: "user"` 里的工具结果不是用户的新输入。** 这是 Anthropic 消息格式承载工具结果的方式，语义上表示外部环境把观察结果交还给模型。
- **“不调用工具就结束”是这个最小实现的规则。** 生产系统还要考虑错误、取消、权限、轮数或 token 预算等停止与恢复情况。

## 当前的一句话理解

**Agent Loop 让模型反复提出行动、观察执行结果、再做判断；模型提供决策，Harness 连接并操作外部环境。**
