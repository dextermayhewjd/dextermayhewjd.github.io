# 函数记忆：用户认可的紧凑案例

配合[短期模板](short-term-memory-template.md)和[长期模板](long-term-memory-template.md)使用。下面是已讨论案例的精简呈现，展示填写方式；完整问答保留在原步骤，未创建后续学习步骤。

---

# AnthropicAdapter._translate

首次接触：Step 01｜最近理解更新：Step 01

**我的理解（以下为两次原话节选）**

> 一个是保留历史，一个是保留工具箱的tools schema

> 不会 这里的translate 只是作为一种格式的切换

**使用场景与源码**

收到 Anthropic 格式的请求后，`_run_turn` 调用该实现，先转换，再把结果交给模板渲染：

```python
translated, tools_schema = self._translate(body)
prompt_ids = _render_token_ids(translated, tok, tools=tools_schema, add_generation_prompt=True)
```

**Input → Output**

教学缩减例子：只看一条文本消息的转换，未提供工具定义。

```python
# Input
body = {
    "messages": [
        {"role": "user", "content": [{"type": "text", "text": "读取 README.md 并概括内容。"}]}
    ]
}

# Output：返回 (translated, tools_schema)
translated = [{"role": "user", "content": "读取 README.md 并概括内容。"}]
tools_schema = None
```

**LLM 根据调用处补充的模型**

它把外部协议中的消息和工具定义整理成下游可用的统一格式。这一步负责转换，不执行工具。

**暂时不清楚**

`system` 的字段层级、工具调用和工具定义具体怎样转换；内部辅助函数如何实现；与 OpenAI 实现有什么差异。

**来源**

源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`，[调用处 common.py:341](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341)，[实现 anthropic.py:58](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L58)。本例由[完整教学样本](translate-function-full-example.md)缩减，已做局部执行核对；[Step 01 实际讨论](../../../../00-repo-reading/discussions/step-01-translate-preview/04-flow.md)保留原话和澄清过程。

---

继承时，长期记录保留以上正文和实际认识更新步骤，只补充继承来源并重算链接。原始讨论仍指向 Step 01；这里的认可针对记录格式，不代表用户已掌握 LLM 补充的全部关系。
