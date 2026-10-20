# 01 · 本步范围

[本步入口](README.md) · [本步知识模型](02-short-term-memory/overview.md)

## 为什么读这里

沿一次模型请求进入 Adapter 后，需要先说明外部请求怎样接入共同处理流程。已有表述提到 `_translate` 返回 `translated` 与 `tools_schema`，本步围绕这两份结果的用途、转换边界和共同接口与具体实现的分工展开。

## 本步核心问题

**`_translate` 从 `body` 中整理出哪两类信息？共同约定与具体 Adapter 怎样分工？两份结果接下来交给哪里？**

前两个问题已有用户表述；下游交接目前由助手据源码定位，尚未据此记录为用户已经理解。

## 入口条件

暂时接受“请求内容已经成为 `body`”。本步从 `_run_turn()` 中这次转换调用开始：

```python
translated, tools_schema = self._translate(body)
```

上游怎样发送、接收和解析请求不在本步展开。[前序累计模型](03-long-term-memory/overview.md)没有导入其他步骤的个人技术模型。

## 源码范围

固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。路径相对 `/home/hongshi/projects/slime`。

| 文件与符号 | 本步用途 | 展开程度 |
| --- | --- | --- |
| `slime/agent/adapters/common.py` · `BaseAdapter._translate` | 共同返回约定 | 说明职责与输入输出 |
| `slime/agent/adapters/anthropic.py` · `AnthropicAdapter._translate` | 代表场景中的具体实现 | 说明协议来源；helper 细节按需查参考 |
| `slime/agent/adapters/common.py` · `BaseAdapter._run_turn` | 调用转换并接收结果 | 只看相邻调用 |
| `slime/agent/adapters/common.py` · `_render_token_ids` | 接收消息与工具定义 | 只定位，不展开内部 |
| `slime/agent/adapters/common.py` · `call_sglang_generate` | 接收渲染后的 token IDs | 只定位，不展开内部 |
| `slime/agent/adapters/openai.py` · `OpenAIAdapter._translate` | 共同约定的另一处实现 | 仅定位 |

具体固定源码链接集中在[组合关系](02-short-term-memory/overview.md#源码中的交接位置)、函数卡片和[可选参考](references/translation-details.md)。

## 阅读边界

读到“外部请求被整理为消息和工具定义，转换本身不执行工具；调用方将结果交给渲染”为止。是否形成个人认识，仍按实际表述记录。

当前保留的未知包括字段细节、helper 内部规则、运行时如何选择 Adapter，以及渲染和生成机制。下一问可从“两份结果怎样参与渲染”接续；这里仅给出问题，不预建后续步骤。
