# 3.5 完成一次模型请求 · 候选阅读稿

## 本节局部数据流

[![生成之后到本轮请求完成的局部数据流](flow.svg)](flow.svg)

**读完本章，你应能解释：一份生成记录怎样成为客户端响应，同时让这一轮的输入和输出留在会话轨迹中。**

上一章返回了 `TurnRecord`。本章在同一个 `_run_turn()` 中继续，直到返回响应并移除当前在途任务；这次请求结束后，Agent 仍可以继续执行工具或请求模型。

仍使用上一章的同一份示例：218 个输入 token、5 个输出 token。生成结果与 log probability 是构造的演示数据；原材料记录了其后解码、解析、响应构造与轨迹记录的本地计算结果。本轮整理不把这些记录写成一次真实模型运行。

<details class="reading-extra">
<summary>查看这一步在完整任务中的位置</summary>

[![3.5 在任务生命周期中的位置](/images/slime-lifecycle/action-3-5.svg)](/images/slime-lifecycle/action-3-5.svg)

CLI 已经启动，并发出了本次模型请求。这里承接生成结果，再回到 CLI；它不是准备或启动另一个 Agent。

[返回任务生命周期总览](/projects/slime/#agent-lifecycle)

</details>

## 把图接到真实调用

下面摘出共享处理器接到 `turn` 后的主线；省略响应方式计算、可选调试回调和错误处理，相关分支在后面补充。



```python
raw_output = tok.decode(turn.output_ids, skip_special_tokens=False) if turn.output_ids else ""
parsed = parse_model_output(
    raw_output,
    tools_schema=tools_schema,
    tool_parser_name=self.tool_parser,
    reasoning_parser_name=self.reasoning_parser,
)
reply = self._build_reply(parsed, turn.finish_reason, translated, tools_schema)
turn = dataclasses.replace(turn, ill_formed=parsed.ill_formed)

response = await self._respond(request, body, reply, in_tok, out_tok, stream)
self.manager.record_turn(
    sid,
    turn=turn,
    prompt_messages=translated,
    response_message=reply.manager_message,
    metadata={"sid": sid},
)
return response
```


<details class="reading-source" id="source-c01" data-source-check="c01">
<summary>查看源码出处与行号</summary>

| 定位内容 | 文件与行号 |
| --- | --- |
| 共享处理器中的调用 | [`slime/agent/adapters/common.py:344`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L344-L393) |

</details>


先认出三份结果：`parsed` 是解析结果，`reply` 为协议与轨迹分别准备内容，`response` 是要交回 HTTP 服务的响应对象。下面沿它们的实际交接顺序阅读。

## 1．接住生成结果：本章需要哪些数据

**输入：** 共享 `_run_turn()` 中的 `turn`，以及仍然持有的 `translated`、`tools_schema` 和原始 `body`。

| 接到的数据 | 本章交给谁 | 最小理解 |
| --- | --- | --- |
| `turn` | 共享 `_run_turn()` 继续处理，随后交给 `record_turn()` | 这一轮的输入、输出 token，输出概率和生成结束原因 |
| `translated` | `record_turn()` | 5 条按历史顺序排列的输入消息，轨迹要保留它们与本轮输出的关系 |
| `tools_schema` | `parse_model_output()` | 本轮可用工具的定义，用于解释模型输出中的工具名称和参数 |
| 原始 `body` | `_run_turn()` 与 `_respond()` | 客户端的同一份请求，决定响应方式及部分协议字段 |
| `sid` | `record_turn()` 与在途任务管理 | 当前 Agent 会话的标识，使多轮请求能归入同一会话 |

这里先保留完整生成记录与请求的交接。后面用到 `turn.output_ids`、`reply.wire` 等成员时，再展开其具体作用。

本例采用 Anthropic 协议、非流式响应，工具与推理专用解析器都未配置，调试回调也未启用。

生成记录的输出部分如下。`prompt_ids` 仍是上一站完整的 218 项列表，放在完整示例中。

```json
{
  "output_ids": [105464, 100134, 73345, 1773, 151645],
  "finish_reason": "stop",
  "output_log_probs": [-0.12, -0.08, -0.06, -0.03, -0.01],
  "ill_formed": false
}
```

<details>
<summary>展开从动作 3 接收到的完整 TurnRecord</summary>

```json
{
  "prompt_ids": [
    151644,
    8948,
    198,
    105043,
    46100,
    110498,
    3407,
    2,
    13852,
    271,
    2610,
    1231,
    1618,
    825,
    476,
    803,
    5746,
    311,
    7789,
    448,
    279,
    1196,
    3239,
    382,
    2610,
    525,
    3897,
    448,
    729,
    32628,
    2878,
    366,
    15918,
    1472,
    15918,
    29,
    11874,
    9492,
    510,
    27,
    15918,
    397,
    4913,
    1313,
    788,
    330,
    1688,
    497,
    330,
    1688,
    788,
    5212,
    606,
    788,
    330,
    878,
    2458,
    497,
    330,
    4684,
    788,
    330,
    57553,
    18158,
    26898,
    497,
    330,
    13786,
    788,
    5212,
    1313,
    788,
    330,
    1700,
    497,
    330,
    13193,
    788,
    5212,
    2343,
    788,
    5212,
    1313,
    788,
    330,
    917,
    9207,
    2137,
    330,
    6279,
    788,
    4383,
    2343,
    1341,
    3417,
    532,
    522,
    15918,
    1339,
    2461,
    1817,
    729,
    1618,
    11,
    470,
    264,
    2951,
    1633,
    448,
    729,
    829,
    323,
    5977,
    2878,
    220,
    151657,
    151658,
    11874,
    9492,
    510,
    151657,
    198,
    4913,
    606,
    788,
    366,
    1688,
    11494,
    8066,
    330,
    16370,
    788,
    366,
    2116,
    56080,
    40432,
    31296,
    151658,
    151645,
    198,
    151644,
    872,
    198,
    57553,
    18158,
    61945,
    21324,
    74577,
    114,
    109193,
    43815,
    1773,
    151645,
    198,
    151644,
    77091,
    198,
    35946,
    60726,
    57553,
    18158,
    26898,
    8997,
    151657,
    198,
    4913,
    606,
    788,
    330,
    878,
    2458,
    497,
    330,
    16370,
    788,
    5212,
    2343,
    788,
    330,
    54675,
    21324,
    95642,
    151658,
    151645,
    198,
    151644,
    872,
    198,
    27,
    14172,
    9655,
    397,
    2,
    28523,
    198,
    105464,
    100134,
    73345,
    8997,
    522,
    14172,
    9655,
    29,
    151645,
    198,
    151644,
    872,
    198,
    14880,
    11622,
    105321,
    109193,
    1773,
    151645,
    198,
    151644,
    77091,
    198
  ],
  "output_ids": [
    105464,
    100134,
    73345,
    1773,
    151645
  ],
  "finish_reason": "stop",
  "output_log_probs": [
    -0.12,
    -0.08,
    -0.06,
    -0.03,
    -0.01
  ],
  "ill_formed": false
}
```

</details>

<details class="reading-source" id="source-c02" data-source-check="c02">
<summary>查看源码出处与行号</summary>

| 定位内容 | 文件与行号 |
| --- | --- |
| 会话与输入准备 | [`slime/agent/adapters/common.py:325`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L325-L344) |

</details>


## 2．解码：输出 token 变成文本

共享流程先取出 `turn.output_ids`，用当前 tokenizer 恢复模型输出的文本：

```python
raw_output = tok.decode(turn.output_ids, skip_special_tokens=False) if turn.output_ids else ""
```

<details class="reading-source" id="source-c03" data-source-check="c03">
<summary>查看源码出处与行号</summary>

| 定位内容 | 文件与行号 |
| --- | --- |
| 解码调用 | [`slime/agent/adapters/common.py:346`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L346-L346) |

</details>


**输入：**

```json
[
  105464,
  100134,
  73345,
  1773,
  151645
]
```

**输出：** 一个字符串 `raw_output`：

```json
"这是一个学习项目。<|im_end|>"
```

这一步恢复 token 对应的文本，还没有分离正文和工具调用。本例的最后一个 ID `151645` 对应 `<|im_end|>`；因为保留特殊 token，它会出现在解码结果中。

**交出：** `raw_output` 进入解析器。它仍是一整段字符串，正文、推理和工具调用还未分开。

## 3．解析：识别正文、推理和工具调用

共享流程把输出文本、可用工具定义和当前解析器配置一起传入：

```python
parsed = parse_model_output(
    raw_output,
    tools_schema=tools_schema,
    tool_parser_name=self.tool_parser,
    reasoning_parser_name=self.reasoning_parser,
)
```

<details class="reading-source" id="source-c04" data-source-check="c04">
<summary>查看源码出处与行号</summary>

| 定位内容 | 文件与行号 |
| --- | --- |
| 解析调用 | [`slime/agent/adapters/common.py:347`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L347-L352) |
| 主解析器 | [`slime/agent/parsing.py:25`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L25-L56) |
| 工具与XML回退解析 | [`slime/agent/parsing.py:59`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L59-L114) |
| 解析结果字段 | [`slime/agent/parsing.py:15`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/parsing.py#L15-L22) |

</details>

**输入：** 上面的 `raw_output`、上一站的 `tools_schema`，以及解析器配置。本例配置如下：

```json
{
  "tool_parser_name": null,
  "reasoning_parser_name": null
}
```

**输出：** `ParsedModelOutput` 对象，下面用 JSON 展示字段：

```json
{
  "reasoning": "",
  "text": "这是一个学习项目。<|im_end|>",
  "tool_uses": [],
  "ill_formed": false
}
```

| 字段 | 本例结果 | 含义 |
| --- | --- | --- |
| `reasoning` | 空字符串 | 本例没有解析出推理内容 |
| `text` | 解码后的这段文本 | 给后续响应构造使用的正文 |
| `tool_uses` | 空列表 | 本轮没有解析出工具调用 |
| `ill_formed` | `false` | 本例没有标记工具参数格式异常 |

本例未启用专用解析器，文本中也没有回退解析器能识别的工具调用。因此 `text` 保留了 `<|im_end|>`。**解码与解析承担不同职责，调用解析函数并不保证所有模型标记都会被移除。** 这里保留源码的实际输出，不手工删改示例。

<details>
<summary>再看一个小对照 有工具调用时 ParsedModelOutput 怎样变化</summary>

下面是另一个构造的输出文本，仅用于观察同一函数如何分离工具调用。它使用本实现的 XML 回退格式，仍然提供同一个 `read_file` 工具定义。

输入 `raw_output`：

```json
"我先读取文件。<tool_call><function=read_file><parameter=path>README.md</parameter></function></tool_call>"
```

真实函数输出：

```json
{
  "reasoning": "",
  "text": "我先读取文件。",
  "tool_uses": [
    {
      "name": "read_file",
      "input": {
        "path": "README.md"
      }
    }
  ],
  "ill_formed": false
}
```

正文与调用已经分开：`text` 只剩“我先读取文件。”，调用信息进入 `tool_uses`。这里仅识别和描述调用，实际执行工具的是客户端 Agent。

专用 SGLang 推理与工具解析器的配置、格式分支及异常处理，可以在理解这一契约后继续展开。

</details>

**交出：** 完整 `parsed` 进入协议适配器。普通文本仍进入 `text`；如果识别出工具调用，其名称与参数进入 `tool_uses`，由客户端 Agent 决定后续执行。

## 4．构造 Reply：同一份结果准备两种表示

**输入：** `parsed`、生成结束原因 `stop`，以及共享流程传入的消息和工具定义。这个 Anthropic 构造函数根据解析结果和结束原因组织回复内容。统一接口也传入历史消息和工具定义，但当前 Anthropic 实现只读取 `parsed` 与生成结束原因。

接着调用当前协议适配器：

```python
reply = self._build_reply(parsed, turn.finish_reason, translated, tools_schema)
```

<details class="reading-source" id="source-c05" data-source-check="c05">
<summary>查看源码出处与行号</summary>

| 定位内容 | 文件与行号 |
| --- | --- |
| 共享调用 | [`slime/agent/adapters/common.py:353`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L353-L354) |
| Reply数据合同 | [`slime/agent/adapters/common.py:45`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L45-L55) |
| Anthropic协议适配入口 | [`slime/agent/adapters/anthropic.py:63`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L63-L69) |
| 构造协议块和助手消息 | [`slime/agent/adapters/anthropic.py:147`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L147-L186) |
| 冻结的生成记录 | [`slime/agent/trajectory.py:28`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L28-L38) |

</details>

**输出：** 一个 `Reply` 对象。字段如下；其中 `wire` 在 Python 中是 `(blocks, stop_reason)` 二元组，用 JSON 展示时成为数组。

```json
{
  "manager_message": {
    "role": "assistant",
    "content": "这是一个学习项目。<|im_end|>"
  },
  "finish_reason": "stop",
  "wire": [
    [
      {
        "type": "text",
        "text": "这是一个学习项目。<|im_end|>"
      }
    ],
    "end_turn"
  ]
}
```

| Reply 字段 | 谁使用 | 本例表达什么 |
| --- | --- | --- |
| `wire` 的第 1 项 `blocks` | `_respond()` | Anthropic 内容块列表 |
| `wire` 的第 2 项 `stop_reason` | `_respond()` | `end_turn`，用于客户端协议 |
| `manager_message` | `record_turn()` | 统一的 `role: assistant` 消息 |
| `finish_reason` | 当前 `_run_turn()` 未读取此字段 | 本例为 `stop`；轨迹记录使用 `turn.finish_reason` |

客户端的内容块和内部助手消息描述同一段内容，但结构不同；协议结束原因 `end_turn` 和生成结束类型 `stop` 也分别用于不同位置。此版本的 `_run_turn()` 后续使用 `reply.wire` 和 `reply.manager_message`，没有读取 `reply.finish_reason`；轨迹记录中的结束原因来自 `turn`。

共享流程随后将解析器的格式判断带回生成记录：

```python
turn = dataclasses.replace(turn, ill_formed=parsed.ill_formed)
```

这会产生一个新的 `TurnRecord`，再绑定到变量 `turn`，不是直接修改冻结对象的字段。它是浅复制，输入和输出列表仍复用已有引用。本例标记为 `False`，内容与上一章的记录一致。

<details>
<summary>补充工具调用例子的 Reply 对照</summary>

前面解析出的 `read_file` 调用会成为协议的 `tool_use` 内容块，并成为内部助手消息的 `tool_calls`。

```json
{
  "manager_message": {
    "role": "assistant",
    "content": "我先读取文件。",
    "tool_calls": [
      {
        "type": "function",
        "function": {
          "name": "read_file",
          "arguments": {
            "path": "README.md"
          }
        }
      }
    ]
  },
  "finish_reason": "tool_calls",
  "wire": [
    [
      {
        "type": "text",
        "text": "我先读取文件。"
      },
      {
        "type": "tool_use",
        "id": "toolu_aaaaaaaaaaaaaaaa",
        "name": "read_file",
        "input": {
          "path": "README.md"
        }
      }
    ],
    "tool_use"
  ]
}
```

示例中的工具调用 ID 已固定，便于逐项对照；真实运行会生成新的 ID。ID 保留在客户端协议块中，内部规范化的 `tool_calls` 只保留名称和参数。协议的 `stop_reason` 变成 `tool_use`，内部 `finish_reason` 变成 `tool_calls`。

</details>

**交出：** 整个 `reply` 传入 `_respond()`，其中的 `wire` 用来构造协议响应；`manager_message` 留到第 6 步记录轨迹。

## 5．准备客户端响应：先区分对象与实际发送

**输入：** 整个 `Reply`、原始请求、token 数量和响应方式；`_respond()` 内部读取 `reply.wire`。

```python
in_tok, out_tok = len(prompt_ids), len(turn.output_ids)
stream = body.get("stream") is True or "text/event-stream" in request.headers.get("Accept", "")
response = await self._respond(request, body, reply, in_tok, out_tok, stream)
```

<details class="reading-source" id="source-c06" data-source-check="c06">
<summary>查看源码出处与行号</summary>

| 定位内容 | 文件与行号 |
| --- | --- |
| 响应方式和调用 | [`slime/agent/adapters/common.py:356`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L356-L374) |
| Anthropic响应入口 | [`slime/agent/adapters/anthropic.py:71`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L71-L75) |
| 非流式协议字典 | [`slime/agent/adapters/anthropic.py:198`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L198-L208) |
| 流式响应发送 | [`slime/agent/adapters/anthropic.py:211`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/anthropic.py#L211-L274) |

</details>


本例 `body.get("stream")` 不是 `True`，请求头也没有要求事件流，因此走非流式分支：先 `_render_response()` 构造协议字典，再用 `web.json_response()` 构造响应对象。

**输出：** HTTP 响应对象，协议 body 的完整内容是：

```json
{
  "id": "msg_aaaaaaaaaaaaaaaaaaaaaaaa",
  "type": "message",
  "role": "assistant",
  "model": "slime-actor",
  "content": [
    {
      "type": "text",
      "text": "这是一个学习项目。<|im_end|>"
    }
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 218,
    "output_tokens": 5
  }
}
```

本例的状态为 `200`，内容类型为 `application/json`。`usage` 中的 `218` 和 `5` 来自本轮输入、输出 ID 列表的长度。请求没有指定 `model` 字段，所以响应采用源码默认值 `slime-actor`；实际服务的模型配置和上一站使用的 tokenizer 是另一层信息。

响应 ID 标识这条协议消息，与表示 Agent 会话的 `sid` 不同；本例为便于对照固定了响应 ID。协议 body 由真实构造函数计算，示例用本地对象承载 HTTP 响应，没有启动网络服务。

**此时 `_respond()` 已返回响应对象，主路径接着记录轨迹。** 对于本例的非流式分支，最终由 HTTP 处理器返回这个对象；流式分支会在 `_respond()` 内写出事件。读主路径时先保持这两种情况的区别，事件格式可以以后展开。

**交出：** `response` 暂存在共享处理器中，接着进行轨迹记录。本例构造出响应对象，不等于此刻已经确认客户端收到了网络数据。

## 6．记录轨迹：保存输入历史与本轮生成

本例没有启用调试回调，共享流程继续调用轨迹管理器：

```python
self.manager.record_turn(
    sid,
    turn=turn,
    prompt_messages=translated,
    response_message=reply.manager_message,
    metadata={"sid": sid},
)
```

<details class="reading-source" id="source-c07" data-source-check="c07">
<summary>查看源码出处与行号</summary>

| 定位内容 | 文件与行号 |
| --- | --- |
| 可选回调与轨迹调用 | [`slime/agent/adapters/common.py:376`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L376-L390) |
| 轨迹记录实现 | [`slime/agent/trajectory.py:283`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L283-L305) |
| 挂载历史与本轮输出 | [`slime/agent/trajectory.py:428`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/trajectory.py#L428-L454) |

</details>

**输入：**

| 参数 | 本例数据 |
| --- | --- |
| `sid` | `demo-session` |
| `prompt_messages` | 动作 2 的完整 5 条 `translated` 消息 |
| `response_message` | 上面 `Reply.manager_message` |
| `turn` | 包含输入 ID、输出 ID、log probability 和格式标记的本轮记录 |
| `metadata` | `{"sid": "demo-session"}` |

本例从一个尚未记录任何交互的会话树开始；请求自带的历史消息也会接入树中。

**函数返回值：** Python `None`。变化发生在 `TrajectoryManager` 的会话状态里。

记录前的状态：

```json
{
  "has_session": false,
  "turn_count": 0,
  "paths": []
}
```

记录后的状态摘要如下。这是为了阅读而提取的观察视图，不是 `record_turn()` 的返回值：

```json
{
  "has_session": true,
  "turn_count": 1,
  "path_roles": [
    "system",
    "user",
    "assistant",
    "tool",
    "user",
    "assistant"
  ],
  "last_message": {
    "role": "assistant",
    "content": "这是一个学习项目。<|im_end|>"
  },
  "last_node_has_turn": true
}
```

本例形成一条消息路径，其中前 5 条来自输入，第 6 条是本轮输出：

| 路径位置 | 角色 | 来源 | 是否挂有生成记录 |
| --- | --- | --- | --- |
| 1 | `system` | 请求带来的历史消息 | 无 |
| 2 | `user` | 请求带来的历史消息 | 无 |
| 3 | `assistant` | 请求带来的历史消息 | 无 |
| 4 | `tool` | 请求带来的历史消息 | 无 |
| 5 | `user` | 请求带来的历史消息 | 无 |
| 6 | `assistant` | 本轮模型输出 | 本轮 TurnRecord |

历史里已经有一条 assistant 消息，但它来自客户端带回的历史。本次记录只给新的助手节点挂上当前 `TurnRecord`，因此会话的已记录轮数为 `1`。

<details>
<summary>展开记录后的完整路径快照</summary>

```json
{
  "has_session": true,
  "turn_count": 1,
  "paths": [
    [
      {
        "role": "system",
        "message": {
          "role": "system",
          "content": "你是代码助手。"
        },
        "has_generation_record": false,
        "turn_index": null
      },
      {
        "role": "user",
        "message": {
          "role": "user",
          "content": "读取 README.md 并概括内容。"
        },
        "has_generation_record": false,
        "turn_index": null
      },
      {
        "role": "assistant",
        "message": {
          "role": "assistant",
          "content": "我先读取文件。",
          "tool_calls": [
            {
              "type": "function",
              "function": {
                "name": "read_file",
                "arguments": {
                  "path": "README.md"
                }
              }
            }
          ]
        },
        "has_generation_record": false,
        "turn_index": null
      },
      {
        "role": "tool",
        "message": {
          "role": "tool",
          "content": "# Demo\n这是一个学习项目。"
        },
        "has_generation_record": false,
        "turn_index": null
      },
      {
        "role": "user",
        "message": {
          "role": "user",
          "content": "请用一句话概括。"
        },
        "has_generation_record": false,
        "turn_index": null
      },
      {
        "role": "assistant",
        "message": {
          "role": "assistant",
          "content": "这是一个学习项目。<|im_end|>"
        },
        "has_generation_record": true,
        "turn_index": 1
      }
    ]
  ]
}
```

完整记录入参和更新后的 `TurnRecord` 见[示例.json](示例.json)中的 `record_input`。消息节点匹配、分叉和重写合并的内部算法，留到轨迹管理专题继续展开。

</details>

这一阶段保存会话轨迹。会话结束后再导出训练样本，是另一阶段，见 [完整任务主线](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/task-walkthrough/)的会话结束部分。

**交出：** 函数没有生成新的 HTTP 结果；它更新会话状态，让下一步可以返回先前保存的 `response`。

## 7．返回并解除在途登记：结束的是这次请求

轨迹记录完成后，共享处理器返回第 5 节构造的同一个响应对象；退出时从 `inflight[sid]` 中移除当前任务。

本例退出后的观察结果：

```json
{
  "returned_same_response_object": true,
  "inflight_session_key_exists": true,
  "inflight_task_count": 0,
  "session_trajectory_retained": true
}
```

`inflight` 仍有这个会话的空任务集合，但当前请求已经不在其中。会话轨迹继续保留，Agent 可以发起下一次请求。本轮请求完成不等于整个 Agent 任务结束。

下面只摘出外层 `try/finally` 的结束部分，其间的处理已在前面逐步说明：

```python
try:
    # ...此处省略前面已讲的生成、解析、响应构造和轨迹记录...
    return response
finally:
    self.inflight.get(sid, set()).discard(task)
```

<details class="reading-source" id="source-c08" data-source-check="c08">
<summary>查看源码出处与行号</summary>

| 定位内容 | 文件与行号 |
| --- | --- |
| 返回与finally | [`slime/agent/adapters/common.py:384`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L384-L393) |

</details>


<details class="reading-extra">
<summary>补充：响应期间断连或取消，轨迹还会记录吗？</summary>

如果 `_respond()` 抛出 `ConnectionResetError`，共享处理器返回状态 `499`；如果抛出 `asyncio.CancelledError`，则继续抛出取消。两条路径都会跳过后面的 `record_turn()`，但仍执行 `finally`，从在途集合移除当前任务。

本例的非流式分支只构造响应对象，所以不能据此声称所有客户端断连都会在这里被发现，也不能把“响应对象构造成功”当成“网络已经送达”。流式分支会在 `_respond()` 内实际写事件，可能在这段写入中触发上述错误。

</details>

<details class="reading-source" id="source-c09" data-source-check="c09">
<summary>查看源码出处与行号</summary>

| 定位内容 | 文件与行号 |
| --- | --- |
| 响应失败的处理 | [`slime/agent/adapters/common.py:359`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L359-L374) |
| 最终清理 | [`slime/agent/adapters/common.py:392`](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/agent/adapters/common.py#L392-L393) |

</details>

## 回到局部图，检查是否能独立解释

1. `turn`、`parsed`、`reply`、`response` 各代表哪一层结果？为什么不能把它们当成同一个对象？
2. `Reply.wire` 与 `Reply.manager_message` 最终分别交给谁？`stop` 与 `end_turn` 为什么可以同时出现？
3. 非流式示例为什么先构造响应对象、再记录轨迹、最后返回？这和流式分支在哪里不同？
4. `record_turn()` 返回 `None`，为什么仍然完成了工作？当前请求退出后，哪些状态还会保留？

## 接回任务主线

本章结束的是一次模型请求。客户端 Agent 可以继续执行工具、再次请求模型，或者结束任务；会话结束后的训练样本导出属于外层流程。

目录下一项 [Pre-4：启动前准备](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/pre-4/) 是回看谁为已运行的 Agent 准备条件，再接 [Launch Agent](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/4-launch-agent/)。这是学习顺序，实际执行中先启动 Agent，再发生这里的一轮或多轮请求。可随时回到 [完整任务主线](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/task-walkthrough/)。

<details class="reading-extra">
<summary>补充：原图、完整示例与验证边界</summary>

[完整原示例](示例.json) 保留生成记录、解析结果、Reply、协议响应和会话树快照。该示例的模型输出是构造数据；原材料记录了随后真实函数的本地计算，本轮没有重新运行模型。

[原始材料](https://github.com/dextermayhewjd/dextermayhewjd.github.io/tree/main/slime_photo/4.Slime%20Core%20Components%20and%20Orchestration/4.1.Agent%20Rollout%20Adapters%20and%20Harnesses/3.5.%E5%AE%8C%E6%88%90%E4%B8%80%E6%AC%A1%E6%A8%A1%E5%9E%8B%E8%AF%B7%E6%B1%82)

</details>

<details class="reading-source">
<summary>集中查看源码校验清单</summary>

[源码出处与校验清单](SOURCE-CHECK.md)

</details>
