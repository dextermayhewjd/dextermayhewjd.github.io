# BaseAdapter._translate

- 源码定位：[slime/agent/adapters/common.py:254](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L254)，由助手核对。
- 首次接触：Step 01。
- 最近认识更新：2026-10-23，用户复述按工具调用顺序整理已有结果；具体分组与异常 ID 分支仍保留为后续细节。
- 源码校准：2026-10-23，对照 `2f231865 → 18868a79`；保留[旧版全文](../../../../../../../step-001-harness-to-adapter/references/translate-at-2f231865.md)，该次源码校准本身不计个人认识更新。本场景实际调用 [AnthropicAdapter._translate:58–61](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L58-L61)。
- 材料来源：[原 Step 01 记录](../../../../../../../../../../../.agents/skills/repo-reading-memory/references/base-adapter-translate.md)；本步引用并保留来源，不计为认识更新。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`_run_turn` 收到模型请求 `body` 后，在渲染 prompt 之前调用 `_translate`，把不同协议的请求接入共同的渲染流程。

2. **具体内容**：`body.system` 和 `body.messages` 整理为 `translated`，本例包括系统指令、用户文本、助手文本、历史工具调用和工具结果；`body.tools` 单独整理为 `tools_schema`，描述可用工具及其参数。工具定义中的 `name`、`description` 放到 `function` 下，`input_schema` 放到 `function.parameters`，外层加上 `type: "function"`。`BaseAdapter` 规定共同接口，具体转换由相应 Adapter 实现，本例采用 Anthropic Adapter。

3. **建议构建的心智模型**：

   > `_translate` 在模型输入之前整理两路信息：
   >
   > `translated`：系统指令和对话历史，包括说过的话、已有的工具调用及其结果。
   >
   > `tools_schema`：当前可用的工具，以及调用这些工具需要的参数定义。
   >
   > 两份结果一起交给后续模板渲染。这里转换已有数据，不执行工具，也不生成下一条模型回复。

4. **调用代码**（[源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L415-L421)）：

   ```python
   translated, tools_schema = self._translate(body)
   prompt_ids = _session_prompt_ids(translated, tok, tools=tools_schema, session=s)
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

`tools_schema` 描述可用工具；`tool_calls` 记录历史中的具体调用；`role: tool` 的消息记录工具结果。当前输出仍不带工具调用的 `id` 和 `tool_use_id`，`arguments` 保持字典；新版在去掉 ID 之前，会借助它们恢复可对应的工具结果顺序。

### 新版补充：多个工具结果的顺序

上面的单工具样例已经用新旧版本分别验证，输出相同；两路输出的职责与字段结构不变。新增差异出现在多个工具结果按不同顺序返回时。

**输入节选**：此前助手按 `toolu_a`、`toolu_b` 的顺序调用 `read_file`，分别读取 `A.py`、`B.py`。随后这条用户消息的 `content` 却按相反顺序带回结果：

```python
[
    {"type": "tool_result", "tool_use_id": "toolu_b", "content": "B 的内容"},
    {"type": "tool_result", "tool_use_id": "toolu_a", "content": "A 的内容"},
]
```

**新版输出节选**：`translated` 中对应的两条消息恢复为调用顺序；`tools_schema` 不变。

```python
[
    {"role": "tool", "content": "A 的内容"},
    {"role": "tool", "content": "B 的内容"},
]
```

旧版这里保持 `B → A`。新版对一组待输出的工具结果，在 ID 都能对应已知调用时按调用顺序整理；有无法匹配的 ID 时保留这一组的原顺序。普通文本等内容划分结果组，不会将整段对话重新排序。实现注释给出的动机是：模板可能按位置关联工具结果，因此在丢弃协议 ID 前先恢复对应顺序。

这仍然是转换已有历史，不会执行 `read_file`。完整教学输入与新旧输出见[局部验证记录](../../../../../../../step-001-harness-to-adapter/references/translation-version-check-18868a79.json)。

## 我的直接表述（原话）

Step 01 本轮对转换职责的复述：

> 这一轮是把传输进来的openai或者anthropic的请求body转换为对应的好处理的统一的格式
> 例如anthropic的messages 里面包括的system和和tool call和messages等内容
>
> 同时这里还要吧tools 中的内容转换为工具定义的schema 例如input type object name之类的（anthropic的形式）

被问到消息中有工具调用时是否会真正读取文件，我补充：

> 不会 这里的translate 只是作为一种格式的切换

原话及上下文见原 Step 01 的[问题四](../../../../../../../../../../../backlog/repo-reading/step-01-translate-preview/04-flow.md#问题四重新复述转换职责并区分字段位置与执行边界)。原话中的字段层级仍待澄清，保留在未知中。

2026-10-23，对新版工具结果排序的复述：

> 好的我理解了简单来说其实就是这里在收集信息的时候会考虑这里的返回顺序
> 以当时传输出call的时候为准
> 而不是单纯的只是考虑这里返还的顺序对吗？
> 这是我对于这里的理解

助手核对：排序依据的理解准确。这里整理的是请求中已经存在的工具结果，不改变工具实际返回的先后；只有结果组的 ID 都能对应已知调用时才排序，否则保留输入顺序。后两个边界是助手补充，未视为用户已独立说明。来源见[本次复述](../../../../../../../step-001-harness-to-adapter/04-flow.md#translate-order-understanding)。

## 尚不清楚

- 请求与返回结果的详细字段结构，以及具体转换规则。
- 运行时怎样选中某个 Adapter 的具体实现。
- Anthropic 和 OpenAI 两处实现内部有哪些差异。

目前知道共同职责，还不清楚这些实现细节。

<details>
<summary>来源、验证与完整例子</summary>

- 2026-10-23：执行两个固定版本中实际 `_translate` 方法与四个纯辅助函数的 AST 节点，验证原卡单工具样例、多工具结果排序、未知 ID、相邻用户消息与普通文本边界；不启动 CLI、tokenizer 或模型服务。结果见[验证记录](../../../../../../../step-001-harness-to-adapter/references/translation-version-check-18868a79.json)，本轮问题与解释见[Step 1 形成过程](../../../../../../../step-001-harness-to-adapter/04-flow.md#translate-version-calibration)。
- 新版差异位于 [Anthropic _translate_messages:81–143](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L81-L143)；共同接口、Anthropic 的三行转换入口和工具 schema 转换在两个版本间未变。用户后续已复述排序依据，见上方原话；本轮未展开分组实现，也不把助手补充的边界自动记为个人已经掌握。

[Step 01 · 共同约定与两个具体实现怎样分工](../../../../../../../../../../../backlog/repo-reading/step-01-translate-preview/04-flow.md#问题三共同约定与两个具体实现怎样分工)。两份结果用途的讨论见同一文件的[问题二](../../../../../../../../../../../backlog/repo-reading/step-01-translate-preview/04-flow.md#问题二历史内容与工具定义有什么区别)，用户原话和源码核对保存在那里。

[问题四](../../../../../../../../../../../backlog/repo-reading/step-01-translate-preview/04-flow.md#问题四重新复述转换职责并区分字段位置与执行边界)保存本轮职责复述和追问：用户明确说明这里只转换格式，不执行消息中的工具调用。

- 短样本已用固定版本 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `_translate` 及四个纯辅助函数核对，只验证局部转换。
- [完整输入输出](<../../../../../../../../../../../slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/2.Translate & Forward/纵向数据流/示例.json>)沿用原页面的 `8c17b676` 教学样本；完整场景也已在上述 `2f231865` 版本核对。
- [详细解释](<../../../../../../../../../../../backlog/repo-reading/step-01-translate-preview/references/translation-explanation.md>)保留消息历史、工具 schema 和后续交接的展开说明。

</details>
