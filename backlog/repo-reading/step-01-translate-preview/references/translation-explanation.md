# 1.3 · 同一请求如何变成两份内部数据

本文保留助手此前的解释与源码核对，供按需查阅；它不是学习者已经表达的认知，不随个人记忆自动继承。


[推演入口](../README.md) · [本步范围](../01-scope.md)

本稿示范 flow 怎样保存解释，不代表用户已经理解了以下全部内容。沿用原页面的完整案例：用户要求读取 README，历史里已有一次工具调用和结果，现在请求模型继续概括。

## 当前位置与已有条件

原页面用 generate 和 CLI 定位当前转换发生的位置。本步从“请求内容已经成为 `body`”接手；先看这份数据长什么样，再解释转换。HTTP 请求如何构造、解析与路由，仍未展开。

```text
已经取得请求 body
  → _translate(body)
      → 消息转换，得到 translated
      → 工具定义转换，得到 tools_schema
  → 两份结果一起交回 _run_turn
```

这两条转换按上述先后执行。它们分别处理消息与工具定义，不表示两个并发请求。

## 输入：请求 body 的具体格式

这里展示请求的 JSON 内容体，不是完整 HTTP 报文。进入函数后对应 Python 字典。以下字段和值沿用页面的[完整输入输出示例](<../../../../slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/2.Translate & Forward/纵向数据流/示例.json>)。

```json
{
  "system": [{"type": "text", "text": "你是代码助手。"}],
  "messages": [
    {
      "role": "user",
      "content": [{"type": "text", "text": "读取 README.md 并概括内容。"}]
    },
    {
      "role": "assistant",
      "content": [
        {"type": "text", "text": "我先读取文件。"},
        {"type": "tool_use", "id": "toolu_demo", "name": "read_file", "input": {"path": "README.md"}}
      ]
    },
    {
      "role": "user",
      "content": [
        {"type": "tool_result", "tool_use_id": "toolu_demo", "content": [{"type": "text", "text": "# Demo\n这是一个学习项目。"}]},
        {"type": "text", "text": "请用一句话概括。"}
      ]
    }
  ],
  "tools": [
    {
      "name": "read_file",
      "description": "读取文件",
      "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    }
  ],
  "max_tokens": 128
}
```

这次输入包含系统指令、三条历史消息、一个可用工具定义，以及后续生成使用的参数。历史中已经有一次 `read_file` 的调用和返回内容；转换这些历史记录不会再次执行工具。

| 输入部分 | 本步读取它做什么 | 本步结果 |
| --- | --- | --- |
| `system` 和 `messages` | 按顺序整理指令、消息和历史工具记录 | `translated` |
| `tools` | 整理模型当前可以选择的工具及参数定义 | `tools_schema` |
| `max_tokens` | 本次转换不使用；保留在 body 中供后续使用 | 不属于两份转换结果 |

## 转换入口：同一个问题中的两个部分

以下是 `_translate` 的真实实现，加上教学注释；没有改动接口和字段名：

```python
def _translate(self, body: dict) -> tuple[list[dict], list[dict] | None]:
    # 先把系统指令和对话历史交给消息转换函数。
    translated = _translate_messages(body.get("messages") or [], body.get("system"))
    # 再把当前可用的工具定义交给工具转换函数。
    tools_schema = _tools_to_chat_tools(body.get("tools"))
    return translated, tools_schema  # 两项结果一起交回调用者。
```

函数内部的两个 helper 分别接到有关字段，并不是整份 body 依次经过每个 helper。

## 消息路：具体记录怎样对应

这一段沿原页面的同一份历史，逐项建立输入与输出的关系。详细源码仍见[已采用的讲解](<../../../../slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/2.Translate & Forward/纵向数据流/reading.md>)。

| 输入中的内容 | 转换后的内容 | 本例解释 |
| --- | --- | --- |
| `system` 的文本块 | `role: system` 的字符串消息 | 系统指令成为第一条消息 |
| 第一条 user 的文本块 | `role: user` 的字符串消息 | 保留用户角色和请求文本 |
| assistant 的文本及 `tool_use` | 一条带 `content` 和 `tool_calls` 的 assistant 消息 | 保留助手说过的话、调用的工具名及参数；协议中的工具调用 id 未带入该内部记录 |
| 第二条 user 中的 `tool_result` | `role: tool` 的消息 | 读取结果成为工具消息 |
| 同一条 user 中后续的文本 | 另一条 `role: user` 消息 | 继续保留“请用一句话概括”的要求 |

因此，这个例子的 `translated` 有五条按历史顺序排列的消息：system、user、assistant、tool、user。这里只解释本例路径，不据此声称所有输入都一定得到五条消息。

## 工具路：可用工具定义怎样对应

输入告诉我们，本轮仍可以选择 `read_file`，它需要一个字符串类型的 `path` 参数。输出中的关键对应为：

```json
{
  "type": "function",
  "function": {
    "name": "read_file",
    "description": "读取文件",
    "parameters": {
      "type": "object",
      "properties": {"path": {"type": "string"}},
      "required": ["path"]
    }
  }
}
```

这个对象放在 `tools_schema` 列表中。工具名和描述保留，`input_schema` 的参数定义进入 `function.parameters`。它表示工具如何调用，转换本身不执行工具。

## 结束：输出交到哪里，哪些仍然未知

`_translate()` 返回二元组，`_run_turn()` 接住 `translated` 与 `tools_schema`。本步到这里结束；下一行怎样渲染 token，以及模型之后怎样工作，仍属于后续问题。

所以本步建立的是一个明确的局部关系：一份 Anthropic 请求的数据，经转换得到内部消息列表和工具定义。它不意味着已经懂了 generate、CLI 的请求发送、HTTP 服务、整个 `_run_turn()` 或训练。

用户当前已经表达的理解以[本步短期记忆](../02-short-term-memory/overview.md)为准；上面的具体格式与字段变化是本稿提供的解释，需要根据后续反馈记录理解情况。

## 从调用处建立的候选职责模型

以下是助手根据固定版本源码建立的解释模型，用于与用户原话对照；其中新增的下游用途尚未得到用户复述，不算个人已经形成的认识。

调用处是 [BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341)，局部源码为：

```python
translated, tools_schema = self._translate(body)
prompt_ids = _render_token_ids(translated, tok, tools=tools_schema, add_generation_prompt=True)
```

这段代码直接表明：调用方接收转换后的消息及工具定义，并立即把两份结果交给 `_render_token_ids`。该 helper 调用 tokenizer 的 `apply_chat_template`，设置 `tokenize=True`，得到供后续模型生成使用的 token IDs，见[实现](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L58)。

结合两个 Adapter 的独立转换实现，可以给出这样的职责模型：

> `_translate` 位于外部协议请求与内部统一处理之间。对应 Adapter 将请求内容整理为统一的消息列表和工具定义，让后续同一个 chat template 渲染步骤能够消费这些结果。`_translate` 完成格式适配，下一步的 `_render_token_ids` 将结果渲染成模型输入 token IDs。

“隔开协议差异、供共同渲染流程消费”是助手依据调用关系对设计作用的归纳；不能仅凭两行调用推断所有字段都被无损保留、所有输入都被支持，或所有异常行为。这里只展开紧邻的下游交接，详细实现和其他消费者仍可按需阅读。

这份模型相对用户原话新增的是：**统一给哪个后续步骤使用，以及当前函数在哪里结束。** 后续可以围绕这一点提问；没有用户的新表述前，继续标为助手提供的模型。

## 来源与验证边界

本稿沿用原页面及 `示例.json`，保留其历史 `8c17b676` 来源。另对照当前本地 `2f231865` 中 `_translate`、两个转换 helper 和它们的调用处。示例是教学构造；原页面列出的完整 HTTP 生命周期不因此成为本步已读内容。
