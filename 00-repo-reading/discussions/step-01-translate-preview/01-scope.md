# 01 · 阅读范围：请求转换的职责与边界

[本步入口](README.md) · [前序记忆](03-long-term-memory/overview.md) · [理解形成过程](04-flow.md) · [本步认识](02-short-term-memory/overview.md)

## 为什么读这里

用户选择从已有的 [Translate & Forward 页面](http://localhost:1313/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/2-translate-forward/)推演一个阅读步骤。这个局部位于 Coding Agent 运行期间的一次模型请求中，本步从 Adapter 的请求转换处接手。

进入本步时，用户已经说过：知道 `_translate` 会把请求的 `body` 变成 `translated` 和 `tools_schema`，其他环节仍不清楚。本步承接这个具体问题，不以读懂整个 `_run_turn()` 为前提。这里暂无从前序步骤导入的技术模型，见[前序记忆](03-long-term-memory/overview.md)。

## 本步核心问题

**已经取得请求 body 后，`_translate` 应当交回哪两类信息，共同约定与具体 Adapter 各负责什么？**

其中“两份信息是什么”是起始问题；共同约定与实现的范围，是随后根据用户关于 common 的追问补入的。后来的认识不倒写为进入本步前已经知道的内容。

## 入口与暂时接受的条件

助手提供的进入条件是：请求内容已经成为 `body`，代码来到 `BaseAdapter._run_turn()` 中的这次调用：

```python
translated, tools_schema = self._translate(body)
```

片段来自当前固定版本的 [common.py 第 341 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341)。它说明本步的入口和两个返回值，不包含请求接收及转换内部的实现。

“已经取得 body”是讲解的场景条件；CLI 怎样构造请求、HTTP 入口怎样解析它，暂不追溯。这些条件与用户已形成的认识分开记录。

## 本步源码范围

本地源码根目录：`/home/hongshi/projects/slime`。本次定位绑定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`；下表路径相对该根目录。

| 文件 | 符号与入口 | 本步为什么看 | 阅读深度 |
| --- | --- | --- | --- |
| `slime/agent/adapters/common.py` | [BaseAdapter._run_turn](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341) | 定位转换的调用和结果交回的位置 | 只定位这一处交接 |
| `slime/agent/adapters/common.py` | [BaseAdapter._translate](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L189) | 查看共同接口约定 | 展开职责和返回约定 |
| `slime/agent/adapters/anthropic.py` | [AnthropicAdapter._translate](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L58) | 用已选的 Anthropic 请求说明转换作用 | 只看入口与两份输出；内部留白 |
| `slime/agent/adapters/openai.py` | [OpenAIAdapter._translate](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/openai.py#L53) | 定位同一约定的另一处实现 | 仅定位，内部尚未展开 |

这里列的是阅读边界，不能据此认定表中所有函数都已经读懂。完整请求样例和转换说明保留在[可选参考](references/translation-explanation.md)，不要求本步逐项展开。

## 本步读到哪里

本步以看清“输入 body → 转换职责 → 两份结果交回调用方”，以及共同接口与具体实现的分工为目标。是否形成这些认识，按[实际讨论](04-flow.md)和[本步记忆](02-short-term-memory/overview.md)记录，不以填满实现细节为结束条件。

出口回到 `_run_turn()` 接收 `translated` 和 `tools_schema` 的位置。下一行会把它们交给 `_render_token_ids(...)`；这里只提供后续位置线索，不展开其实现，也不记为用户已经理解。

本步允许继续留白：请求的详细字段、转换 helper 的内部规则、运行时如何选中具体 Adapter、上游任务准备，以及后续 token 渲染、模型调用、响应与轨迹处理。将来遇到相关问题再展开；本步不重读整个 generate 任务链。
