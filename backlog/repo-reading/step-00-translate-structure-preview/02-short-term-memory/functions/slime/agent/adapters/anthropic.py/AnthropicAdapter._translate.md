# AnthropicAdapter._translate

- 源码定位：[slime/agent/adapters/anthropic.py:58](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L58)，由助手核对。
- 首次接触：Step 01。
- 最近认识更新：Step 01。
- 结构示范：Step 0；以上认知来源与更新时间沿用原 Step 01。

## LLM 整理：使用场合、具体内容与心智模型

以下为助手的源码说明，与用户原话分开。

1. **使用场合**：处理 Anthropic 请求时，为共同的 `_run_turn()` 流程提供转换结果。
2. **具体内容**：把 `messages` 与 `system` 交给消息转换函数，把 `tools` 交给工具定义转换函数，再一起返回。
3. **建议构建的心智模型**：

   > 这是共同转换约定的一种具体实现。它把 Anthropic 请求中的消息和工具定义整理为内部格式；这里只做格式转换。

4. **实现中的调用代码**（[源码](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L59)）：

   ```python
   translated = _translate_messages(body.get("messages") or [], body.get("system"))
   tools_schema = _tools_to_chat_tools(body.get("tools"))
   return translated, tools_schema
   ```

## 本场景的输入与输出

保留原记录的最小教学分支：只有一条文本消息，没有传入工具定义。包含系统指令、历史工具调用、结果及可用工具的完整代表场景见[common 卡片](../common.py/BaseAdapter._translate.md#本场景的输入与输出)。

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

这里的 `None` 对应本输入没有传入 `tools`，不代表转换接口总是没有工具定义。

## 我的直接表述（原话）

Step 01 本轮职责复述中，关于 Anthropic 消息的原话节选：

> 例如anthropic的messages 里面包括的system和和tool call和messages等内容

同一回答中，关于工具定义的原话节选：

> 同时这里还要吧tools 中的内容转换为工具定义的schema 例如input type object name之类的（anthropic的形式）

这些原话中的字段层级仍待澄清，保留在未知中。完整原话及上下文见来源中的原问题四。

## 尚不清楚

- Anthropic 请求中消息和工具定义的详细结构。
- 它们分别怎样转换成内部结果，各个辅助函数如何工作。
- 与 OpenAI 实现的具体差异，尚未展开。
- `system` 与 `messages` 的字段层级，以及工具定义中的 `input_schema` 怎样对应到内部格式；助手已给出说明，尚无用户后续复述。

目前知道示例采用 Anthropic 协议及其转换作用，具体实现继续留白。

<details>
<summary>来源、验证与完整例子</summary>

- 原认识与未知保留自[原 Step 01 的函数记录](../../../../../../../step-01-translate-preview/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md)。
- 初始表述见[原问题一](../../../../../../../step-01-translate-preview/04-flow.md#问题一这次转换交回什么)，共同约定与具体实现的区分见[原问题三](../../../../../../../step-01-translate-preview/04-flow.md#问题三共同约定与两个具体实现怎样分工)，本轮职责复述见[原问题四](../../../../../../../step-01-translate-preview/04-flow.md#问题四重新复述转换职责并区分字段位置与执行边界)。
- 样本来自原页面的教学构造，使用固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的局部转换核对，不代表实际运行模型请求。
- [额外机制说明](../../../../../../references/translation-details.md)只展开两个 helper 的输入分工。

</details>
