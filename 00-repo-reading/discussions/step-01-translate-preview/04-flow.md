# 04 · 本步理解形成的过程

[推演入口](README.md) · [本步范围](01-scope.md) · [本步短期记忆](02-short-term-memory/overview.md) · [继承的长期记忆](03-long-term-memory/overview.md)

下面按实际讨论的问题组织：用户当时怎样理解、助手提供了什么材料、随后形成了什么认识。问题的先后不是函数执行顺序。源码片段由助手按固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 核对，属于静态证据，没有把它们记作用户已经运行或读懂全部实现。

## 起点：在一次请求的转换处接手

按 [scope 的进入条件](01-scope.md#入口与暂时接受的条件)，先接受“已经取得 body”。它怎样从 CLI 到达 Adapter，暂时没有展开。

## 问题一：这次转换交回什么

用户最初描述：

> 我只是知道这里有一个_translate 会把请求中的body 变成为translated 和tools schema

这句话提供了本步最初的输入输出关系：

```text
请求中的 body
  → _translate
  → translated 和 tools_schema
```

随后用户进一步说明它的作用：

> anthropic格式的messages
> 转换成为统一的格式，
> 1.得到对话历史 2.得到对应的tool的schema

同时，用户明确表示不清楚具体怎样转换。因此，当前先记录转换职责与两份结果的用途，内部机制继续留白。

## 问题二：历史内容与工具定义有什么区别

为区分两份结果，助手提供了下面的源码材料。片段摘自 [AnthropicAdapter._translate](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L58)，只保留两处转换调用：

```python
translated = _translate_messages(body.get("messages") or [], body.get("system"))
tools_schema = _tools_to_chat_tools(body.get("tools"))
```

助手据此提示：历史内容已经在请求中；两份结果分别整理历史和工具定义。读取 `messages`、`system`、`tools` 的具体字段关系，是助手提供的源码说明，尚未当成用户已经解释清楚的内容。

在区分“历史中发生过的工具调用”和“可用工具的定义”时，用户回答：

> 一个是保留历史，一个是保留工具箱的tools schema

这使模型从“两份返回值”进一步明确为“历史内容”和“工具箱定义”两种用途。这个职责区别已经进入个人记忆；每个字段如何转换、helper 如何工作，仍然留白。

## 问题三：共同约定与两个具体实现怎样分工

助手曾提出继续看结果交给谁使用，用户转而提出一个更基础的问题：共同的转换认识是否应记在 common，Anthropic 和 OpenAI 分别记具体实现。于是先沿这个问题核对源码。

[common.py 中的 BaseAdapter._translate](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L189) 定义如下：

```python
def _translate(self, body: dict) -> tuple[list[dict], list[dict] | None]:
    """Return (chat_messages, tools_schema) from the wire body."""
    raise NotImplementedError
```

助手同时定位到 `_run_turn()` 的 `self._translate(body)` 调用，以及两个子类各自的 `_translate()`。这组材料用来区分共同约定与具体转换，运行时怎样选中子类方法仍未展开。

用户随后解释：

> common 的约定
> 两个adapter都需要返回对应的信息
> 具体的adapter 范围的两个接口具体的实现

据此，共同职责保存在 [BaseAdapter._translate 的个人记录](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md)，Anthropic 例子中的特有认识保存在[对应实现记录](02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md)。OpenAI 目前只定位，不预填内部解释。

## 问题四：重新复述转换职责，并区分字段位置与执行边界

按照新约定，助手先定位 `_run_turn()` 中的 `translated, tools_schema = self._translate(body)`，请用户用自己的话说明这个函数完成什么事情。用户回答：

> 这一轮是把传输进来的openai或者anthropic的请求body转换为对应的好处理的统一的格式
> 例如anthropic的messages 里面包括的system和和tool call和messages等内容
>
> 同时这里还要吧tools 中的内容转换为工具定义的schema 例如input type object name之类的（anthropic的形式）

这次表述说明用户将这一步理解为外部请求协议到内部统一格式的转换，并将消息内容与 `tools` 定义分开。`system` 的层级及工具定义字段的准确对应仍需澄清，不能把这句原话直接保存为准确的完整请求结构。

助手核对同一固定版本的 [AnthropicAdapter._translate](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L58)：

```python
translated = _translate_messages(body.get("messages") or [], body.get("system"))
tools_schema = _tools_to_chat_tools(body.get("tools"))
```

据此澄清：Anthropic 请求通常把 `system`、`messages` 和 `tools` 放在 body 的同一层；历史工具调用以消息内容中的 `tool_use` 块表示。`tools` 原本就带有工具名称和 `input_schema`，转换 helper 将其组织为内部工具定义，并把参数 schema 放入 `function.parameters`。本地 helper 也兼容消息列表里的 `role="system"`，不能将这种兼容分支当作标准请求层级。上述字段映射是助手的源码说明，尚未记为用户已经复述的认识。

追加问题聚焦转换与执行的边界：**如果 messages 中出现对 `read_file` 的一次 `tool_use`，`_translate` 会因此真正读取文件吗？** 追问原因是确认“请求中出现工具调用记录”和“当前函数负责执行工具”是否已被区分。这比继续展开每个转换分支更直接地检验当前职责模型。

用户回答：

> 不会 这里的translate 只是作为一种格式的切换

据此，短期记忆补充“这里只转换表示格式，不实际执行工具”。这个回答明确了职责边界，但没有解释字段层级或 helper 的转换规则；相关未知继续保留。

本轮可展示的候选记忆由四项组成：转换为统一内部格式、返回消息和工具定义、共同约定与具体实现分工、只转换而不执行工具。值得保留最后一项，是因为它明确了函数职责在哪里结束；不继续追问全部字段，实现细节仍可留白。候选记录是否便于回忆，等待用户对展示结果的反馈。

## 本步形成的认识与仍留白的部分

理解从最初的“两份返回值”，推进到“两份结果的不同用途”，再推进到“共同接口与具体实现的分工”。本轮重新复述补充了“把外部协议转换成内部统一格式”的目的，并提出字段位置和转换/执行边界的澄清。当前模型统一保存在 [02 短期记忆](02-short-term-memory/overview.md)，这里保留形成过程。

当前仍是：**知道它做什么，还不清楚它怎样做到。**

- 用户已提到 body 中的消息与工具定义、工具名称和参数类型，但字段层级、完整结构与精确映射尚未说清。
- 用户已明确 `_translate` 只转换格式，不实际执行工具；具体工具由谁执行尚未在本步展开。
- 具体字段转换、辅助函数和运行时选择实现的机制，继续留白。
- 在整个任务中怎样到达这里、两份结果怎样用于后续处理，尚未在本步形成用户表述。

此前提出的“不同 Adapter 的结果怎样接入后续共同处理”仍可留待后续讨论，不因整理完本文件就自动视为已经回答。

## 参考与记录约定

完整请求样例和助手说明见[参考讲解](references/translation-explanation.md)。本文件的组织方式以及目录、记忆迁移的历史见[格式讨论](../2026-10-19-step-folder-format.md#scope-flow-conventions)，与源码理解过程分开保存。
