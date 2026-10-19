# 02 · 本步形成的短期记忆

[推演入口](../README.md) · [继承的长期记忆](../03-long-term-memory/overview.md) · [本步表述](../04-flow.md)

- 所属步骤：Step 01 · 从请求 body 到消息与工具定义。
- 记忆范围：本步新形成或修正的认识。

本页的个人整体模型只保存用户已经表达的理解；源码场景参考另列。本步没有导入前序技术模型；下一步继承这些理解、未知，以及函数记录中有明确来源的场景材料。

## 当前整体模型

当前共同认识是：转换请求内容，得到整理后的对话历史和对应工具 schema；已经区分“一份保留历史、一份保留工具箱的定义”。用户进一步说明 common 规定约定，两个 Adapter 都要返回对应信息，由各自实现具体转换。具体转换机制仍不清楚。

本轮复述将目的说为“把传入的 OpenAI 或 Anthropic 请求整理为便于处理的统一格式”，并提到工具名称与参数结构。用户在追问中进一步明确：这里仅转换格式，不实际执行消息中的工具调用。字段层级与具体映射仍待澄清。

## 函数索引

| 源码文件 | 函数与记忆入口 | 首次接触 | 最近认识更新 |
| --- | --- | --- | --- |
| `slime/agent/adapters/common.py` | [BaseAdapter._translate](functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | Step 01 | Step 01 |
| `slime/agent/adapters/anthropic.py` | [AnthropicAdapter._translate](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md) | Step 01 | Step 01 |
| `slime/agent/adapters/openai.py` | `OpenAIAdapter._translate`：仅定位，暂无个人实现模型 | Step 01 | 暂无 |

`BaseAdapter._run_turn` 是使用转换结果的共同流程；目前只定位其调用关系，不把整个请求处理过程记为已经理解。

## 源码场景参考

以下是助手提供的源码解释入口，与上面的个人整体理解分开：

- [共同约定的使用场景](functions/slime/agent/adapters/common.py/BaseAdapter._translate.md#使用场景与调用代码)：真实调用、输入输出及独立标注的 LLM 模型。
- [Anthropic 的具体场景](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md#使用场景与调用代码)：同一请求如何由具体实现转换。

使用原页面已有教学样本；局部转换已用当前源码核对。新增示例和 LLM 模型不改变个人理解与未知的状态。

## 尚不清楚

整个 Coding Agent 的运行模型、该函数具体实现、输入输出的详细结构，仍然留白。这里没有把“未记录”解释成遗忘，也没有覆盖以前的已读历史。

## 形成过程

[Step 01 的实际讨论](../../step-01-translate-preview/04-flow.md)依次保存两份输出的用途、历史与工具定义的区别，以及共同接口与具体实现的分工。各函数记录链接到对应问题段落。

[问题四](../../step-01-translate-preview/04-flow.md#问题四重新复述转换职责并区分字段位置与执行边界)接续本轮复述、源码澄清，以及用户对转换和执行边界的回答。
