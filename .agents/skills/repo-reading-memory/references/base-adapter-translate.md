# BaseAdapter._translate

- 源码定位：[slime/agent/adapters/common.py:189](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L189)，由助手核对。
- 首次接触：Step 01。
- 最近认识更新：Step 01。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和前文的输入输出整理，作为理解参考。

1. **使用场合**：`_run_turn` 收到模型请求 `body` 后，在渲染 prompt 之前调用 `_translate`，把不同协议的请求接入共同的渲染流程。

2. **具体内容**：`body.system` 和 `body.messages` 整理为 `translated`，本例包括系统指令、用户文本、助手文本、历史工具调用和工具结果；`body.tools` 单独整理为 `tools_schema`，描述可用工具及其参数。工具定义中的 `name`、`description` 放到 `function` 下，`input_schema` 放到 `function.parameters`，外层加上 `type: "function"`。`BaseAdapter` 规定共同接口，具体转换由两个 Adapter 分别实现。

3. **建议构建的心智模型**：

   > `_translate` 在模型输入之前整理两路信息：
   >
   > `translated`：系统指令和对话历史，包括说过的话、已有的工具调用及其结果。
   >
   > `tools_schema`：当前可用的工具，以及调用这些工具需要的参数定义。
   >
   > 两份结果一起交给后续模板渲染。这里转换已有数据，不执行工具，也不生成下一条模型回复。

4. **调用代码**（[源码](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341)）：

   ```python
   translated, tools_schema = self._translate(body)
   prompt_ids = _render_token_ids(translated, tok, tools=tools_schema, add_generation_prompt=True)
   ```

## 本场景的输入与输出

教学缩减：从完整例子保留系统指令、普通文本、一次已有的工具调用及其结果，以及可用工具定义。场景是工具已返回文件内容，现在将这段历史交给模型继续概括；本次转换不会执行工具。

输入：

```python
body = {
    "system": [{"type": "text", "text": "你是代码助手。"}],
    "messages": [
        {"role": "user", "content": [{"type": "text", "text": "读取 README.md 并概括内容。"}]},
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
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_demo",
                    "content": [{"type": "text", "text": "# Demo\n这是一个学习项目。"}]
                },
                {"type": "text", "text": "请用一句话概括。"}
            ]
        }
    ],
    "tools": [
        {
            "name": "read_file",
            "description": "读取文件",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }
    ]
}
```

输出，实际返回 `(translated, tools_schema)`：

```python
translated = [
    {"role": "system", "content": "你是代码助手。"},
    {"role": "user", "content": "读取 README.md 并概括内容。"},
    {
        "role": "assistant",
        "content": "我先读取文件。",
        "tool_calls": [
            {"type": "function", "function": {"name": "read_file", "arguments": {"path": "README.md"}}}
        ]
    },
    {"role": "tool", "content": "# Demo\n这是一个学习项目。"},
    {"role": "user", "content": "请用一句话概括。"}
]
tools_schema = [
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
]
```

字段层级要分开看：本例的 `body.system` 是顶层系统指令；消息的 `role` 表示发言角色；`content` 内的 `type` 表示内容块类型，例如 `text`、`tool_use`、`tool_result`。转换后，系统指令成为 `role: system` 的消息，`tool_use` 进入助手消息的 `tool_calls`，`tool_result` 成为 `role: tool` 的消息；同一条输入中的工具结果和后续用户文本会分成两条输出消息。

`tools_schema` 描述可用工具；`tool_calls` 记录历史中的具体调用；`role: tool` 的消息记录工具结果。当前实现不把工具调用的 `id` 和 `tool_use_id` 带入这些输出，`arguments` 保持字典。

## 我的直接表述（原话）

Step 01 本轮对转换职责的复述：

> 这一轮是把传输进来的openai或者anthropic的请求body转换为对应的好处理的统一的格式
> 例如anthropic的messages 里面包括的system和和tool call和messages等内容
>
> 同时这里还要吧tools 中的内容转换为工具定义的schema 例如input type object name之类的（anthropic的形式）

被问到消息中有工具调用时是否会真正读取文件，我补充：

> 不会 这里的translate 只是作为一种格式的切换

原话及上下文见下方形成过程的[问题四](../../../../backlog/repo-reading/step-01-translate-preview/04-flow.md#问题四重新复述转换职责并区分字段位置与执行边界)。原话中的字段层级仍待澄清，保留在未知中。

## 尚不清楚

- 请求与返回结果的详细字段结构，以及具体转换规则。
- 运行时怎样选中某个 Adapter 的具体实现。
- Anthropic 和 OpenAI 两处实现内部有哪些差异。

目前知道共同职责，还不清楚这些实现细节。

## 形成过程

[Step 01 · 共同约定与两个具体实现怎样分工](../../../../backlog/repo-reading/step-01-translate-preview/04-flow.md#问题三共同约定与两个具体实现怎样分工)。两份结果用途的讨论见同一文件的[问题二](../../../../backlog/repo-reading/step-01-translate-preview/04-flow.md#问题二历史内容与工具定义有什么区别)，用户原话和源码核对保存在那里。

[问题四](../../../../backlog/repo-reading/step-01-translate-preview/04-flow.md#问题四重新复述转换职责并区分字段位置与执行边界)保存本轮职责复述和追问：用户明确说明这里只转换格式，不执行消息中的工具调用。

<details>
<summary>来源、验证与完整例子</summary>

- 短样本已用固定版本 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `_translate` 及四个纯辅助函数核对，只验证局部转换。
- [完整输入输出](<../../../../slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/2.Translate & Forward/纵向数据流/示例.json>)沿用原页面的 `8c17b676` 教学样本；完整场景也已在当前版本核对。
- [详细解释](<../../../../backlog/repo-reading/step-01-translate-preview/references/translation-explanation.md>)保留消息历史、工具 schema 和后续交接的展开说明。

</details>
