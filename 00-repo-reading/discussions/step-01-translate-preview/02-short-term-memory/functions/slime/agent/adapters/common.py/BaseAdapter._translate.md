# BaseAdapter._translate

- 源码定位：[slime/agent/adapters/common.py:189](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L189)，由助手核对。
- 首次接触：Step 01。
- 最近认识更新：Step 01。

## 我的直接表述（原话）

Step 01 本轮对转换职责的复述：

> 这一轮是把传输进来的openai或者anthropic的请求body转换为对应的好处理的统一的格式
> 例如anthropic的messages 里面包括的system和和tool call和messages等内容
>
> 同时这里还要吧tools 中的内容转换为工具定义的schema 例如input type object name之类的（anthropic的形式）

被问到消息中有工具调用时是否会真正读取文件，我补充：

> 不会 这里的translate 只是作为一种格式的切换

原话及上下文见下方形成过程的[问题四](../../../../../../../step-01-translate-preview/04-flow.md#问题四重新复述转换职责并区分字段位置与执行边界)。原话中的字段层级仍待澄清，保留在未知中。

## 使用场景与调用代码

一次模型请求已成为 `body`；`_run_turn` 调用转换接口，随后把结果交给模板渲染。本例使用 `AnthropicAdapter` 的具体实现，`BaseAdapter._translate` 只规定共同约定。

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

这是连接外部协议与共同渲染流程的转换接口：各 Adapter 整理消息和工具定义，供下一步使用；转换本身不执行工具。

## 当前心智模型

助手据用户原话整理：输入 body，得到对话历史与工具 schema；common 规定共同约定，两个 Adapter 分别实现。这里只切换格式，不执行工具。

这份记录保存共同职责；Anthropic 示例对应的认识见[具体实现记录](../anthropic.py/AnthropicAdapter._translate.md)。

## 尚不清楚

- 请求与返回结果的详细字段结构，以及具体转换规则。
- 运行时怎样选中某个 Adapter 的具体实现。
- Anthropic 和 OpenAI 两处实现内部有哪些差异。

目前知道共同职责，还不清楚这些实现细节。

## 形成过程

[Step 01 · 共同约定与两个具体实现怎样分工](../../../../../../../step-01-translate-preview/04-flow.md#问题三共同约定与两个具体实现怎样分工)。两份结果用途的讨论见同一文件的[问题二](../../../../../../../step-01-translate-preview/04-flow.md#问题二历史内容与工具定义有什么区别)，用户原话和源码核对保存在那里。

[问题四](../../../../../../../step-01-translate-preview/04-flow.md#问题四重新复述转换职责并区分字段位置与执行边界)保存本轮职责复述和追问：用户明确说明这里只转换格式，不执行消息中的工具调用。

<details>
<summary>来源、验证与完整例子</summary>

- 短样本已用固定版本 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 `_translate` 及四个纯辅助函数核对，只验证局部转换。
- [完整输入输出](<../../../../../../../../../slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/2.Translate & Forward/纵向数据流/示例.json>)沿用原页面的 `8c17b676` 教学样本；完整场景也已在当前版本核对。
- [详细解释](<../../../../../../references/translation-explanation.md>)保留消息历史、工具 schema 和后续交接的展开说明。

</details>
