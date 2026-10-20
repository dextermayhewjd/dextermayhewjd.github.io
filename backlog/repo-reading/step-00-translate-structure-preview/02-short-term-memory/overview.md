# 02 · 本步知识模型

[本步入口](../README.md) · [本步范围](../01-scope.md) · [关键学习记录](../04-flow.md)

本页保存当前可复用的关系。用户认识来自原 Step 01 的实际表述；助手根据源码提供的位置提示另列。Step 0 是结构示范编号，不改变首次接触或最近认识更新的归属。

## 用户已经表达的关系

```text
传入的 OpenAI 或 Anthropic 请求 body
    ↓ 按共同约定转换，由具体 Adapter 实现
    ├─ translated：整理后的对话历史
    └─ tools_schema：可用工具的定义
```

用户已经区分“一份保留历史，一份保留工具箱的定义”，并明确这里切换表示格式，不实际执行工具。common 规定共同约定，两个 Adapter 分别实现。详细字段与具体转换机制仍未说清。

这些关系的原话与未知见[common 函数卡片](functions/slime/agent/adapters/common.py/BaseAdapter._translate.md#我的直接表述原话)及[关键学习记录](../04-flow.md)。

## 源码中的交接位置

以下是助手提供的源码定位，帮助把局部函数接回任务，不代表用户已理解整条调用链：

```text
body ──→ self._translate(body)
             │
             └─ translated、tools_schema
                       │ 与 tokenizer 一起
                       ▼
                 _render_token_ids(...)
                       │
                       └─ prompt_ids
                              │ 与 session、body 等一起
                              ▼
                       call_sglang_generate(...)
```

两份转换结果在调用方汇合，用于同一次渲染；不是分别发起两次模型调用。后两步目前只定位职责与交接，内部机制继续留白。

实际调用见[固定版本 common.py 第 341 行起](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341)。本页不复制函数卡片中的整套输入输出。

## 函数索引

| 符号 | 当前记录 | 首次接触 / 最近认识更新 |
| --- | --- | --- |
| [BaseAdapter._translate](functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | 共同职责、代表性输入输出、个人表述与未知 | 原 Step 01 / 原 Step 01 |
| [AnthropicAdapter._translate](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md) | 具体实现的已有表述；字段规则仍待澄清 | 原 Step 01 / 原 Step 01 |
| `OpenAIAdapter._translate` | 仅定位，暂无个人实现模型 | 沿用原步骤的定位状态 |
| `_render_token_ids` | 仅定位结果的消费者，尚未建立个人函数模型 | 不因绘图而新增认识记录 |
| `call_sglang_generate` | 仅定位后续生成请求，尚未建立个人函数模型 | 不因绘图而新增认识记录 |

## 尚不清楚

- 完整请求结构、准确字段层级，以及具体转换规则。
- 运行时怎样选择 Adapter 的实现，Anthropic 与 OpenAI 有哪些差异。
- 渲染怎样使用两份输入，怎样得到 token IDs。
- 整个 Coding Agent 任务怎样到达这里、如何继续执行和返回结果。

函数内部未知保留在各卡片中；学习事件和原讨论见[04](../04-flow.md)。
