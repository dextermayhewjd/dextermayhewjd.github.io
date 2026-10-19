# AnthropicAdapter._translate

- 源码定位：[slime/agent/adapters/anthropic.py:58](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L58)，由助手核对。
- 首次接触：Step 01。
- 最近认识更新：Step 01。

## 我的直接表述（原话）

Step 01 本轮职责复述中，关于 Anthropic 消息的原话节选：

> 例如anthropic的messages 里面包括的system和和tool call和messages等内容

同一回答中，关于工具定义的原话节选：

> 同时这里还要吧tools 中的内容转换为工具定义的schema 例如input type object name之类的（anthropic的形式）

完整回答见[问题四](../../../../../../../step-01-translate-preview/04-flow.md#问题四重新复述转换职责并区分字段位置与执行边界)。这些原话中的字段层级仍待澄清，保留在未知中。

## 使用场景与调用代码

当前处理 Anthropic 请求：`_run_turn` 调用 `AnthropicAdapter._translate`，把转换结果交给共同的模板渲染步骤。

[原仓库调用处](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341)，仅摘录相邻两行：

```python
translated, tools_schema = self._translate(body)
prompt_ids = _render_token_ids(translated, tok, tools=tools_schema, add_generation_prompt=True)
```

## 本场景的输入与输出

教学缩减：只取完整例子的第一条用户消息，观察文本块变成字符串。本例没有传入 `tools`。

输入：

```python
body = {
    "messages": [
        {"role": "user", "content": [{"type": "text", "text": "读取 README.md 并概括内容。"}]}
    ]
}
```

输出，实际返回 `(translated, tools_schema)`：

```python
translated = [{"role": "user", "content": "读取 README.md 并概括内容。"}]
tools_schema = None
```

## LLM 基于使用场景的心智模型

把 Anthropic 请求中的消息和工具定义整理为统一格式，交回共同处理流程；这里只做格式转换。

## 当前心智模型

助手据用户原话整理：Anthropic 是共同约定的一个具体实现；请求内容变为统一消息与工具定义。用户已注意到工具名称和参数结构，具体字段对应仍待澄清。

两份结果的共同用途保存在 [BaseAdapter._translate 的记录](../common.py/BaseAdapter._translate.md)；这里保留它作为 Anthropic 具体实现的认识。

## 尚不清楚

- Anthropic 请求中消息和工具定义的详细结构。
- 它们分别怎样转换成内部结果，各个辅助函数如何工作。
- 与 OpenAI 实现的具体差异，尚未展开。
- `system` 与 `messages` 的字段层级，以及工具定义中的 `input_schema` 怎样对应到内部格式；助手已给出说明，尚无用户后续复述。

目前知道示例采用 Anthropic 协议及其转换作用，具体实现继续留白。

## 形成过程

[Step 01 · 这次转换交回什么](../../../../../../../step-01-translate-preview/04-flow.md#问题一这次转换交回什么)记录了最初从 Anthropic 示例形成的认识；[问题三](../../../../../../../step-01-translate-preview/04-flow.md#问题三共同约定与两个具体实现怎样分工)记录了共同约定与具体实现的区分。

[问题四](../../../../../../../step-01-translate-preview/04-flow.md#问题四重新复述转换职责并区分字段位置与执行边界)保留用户本轮对消息与工具定义的表述，以及字段位置的待澄清部分。

<details>
<summary>来源、验证与完整例子</summary>

- 短样本已用固定版本 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `_translate` 及四个纯辅助函数核对，只验证局部转换。
- [完整输入输出](<../../../../../../../../../slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/2.Translate & Forward/纵向数据流/示例.json>)沿用原页面的 `8c17b676` 教学样本；完整场景也已在当前版本核对。
- [详细解释](<../../../../../../references/translation-explanation.md>)保留消息历史、工具 schema 和后续交接的展开说明。

</details>
