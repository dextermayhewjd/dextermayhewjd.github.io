# 可选参考 · 两路数据怎样进入转换函数

[本步入口](../README.md) · [函数卡片与完整代表性输入输出](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md)

这里补充函数卡片没有展开的参数分工。它是助手提供的源码解释，不能自动记为用户已经理解。

## 具体实现怎样分配输入

本例使用 `AnthropicAdapter._translate`。真实实现是：

```python
def _translate(self, body: dict) -> tuple[list[dict], list[dict] | None]:
    translated = _translate_messages(body.get("messages") or [], body.get("system"))
    tools_schema = _tools_to_chat_tools(body.get("tools"))
    return translated, tools_schema
```

[固定版本源码：anthropic.py 第 58 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L58)。

| 从 body 取出的内容 | 交给谁 | 为什么这样分 |
| --- | --- | --- |
| `messages` 与 `system` | `_translate_messages` | 两者共同构成系统指令与消息历史 |
| `tools` | `_tools_to_chat_tools` | 这里描述可用工具及参数定义，独立于历史中的具体调用 |

先执行消息转换，再执行工具定义转换，最后把两个返回值一起交回。不是整个 `body` 依次通过两个 helper，也不是发起两个并发请求。

## 两份结果怎样汇合

`return translated, tools_schema` 交回两个值，调用方将它们传给同一次模板渲染。真实交接位置见[组合关系图](../02-short-term-memory/overview.md#源码中的交接位置)；整套输入输出不在这里重复展示。

## 请求中其他字段怎么办

原完整示例还含有 `max_tokens`。上面这个转换方法没有读取它，所以它不属于两份转换结果；`body` 仍作为请求对象在后续流程使用。这里仅说明本方法读取了哪些字段，不展开后续生成参数的处理。

## 需要更详细的历史讲解时

[原 1.3 · 同一请求如何变成两份内部数据](../../step-01-translate-preview/references/translation-explanation.md)保留了完整讲解，包括消息块逐项对应和原始样例。当前示范优先使用函数卡片恢复认识，遇到字段问题再查这份历史参考。
