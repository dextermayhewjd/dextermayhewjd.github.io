# BaseAdapter._build_reply

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../../../02-rollout-reward/steps/step-011-generate-and-rm-group/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：共同接口在 [slime/agent/adapters/common.py:193–195](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L193-L195)；本场景实际执行 [AnthropicAdapter._build_reply，anthropic.py:63–69](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L63-L69)，由助手核对。
- 首次接触：Step 1，2026-10-21，承接 `parse_model_output` 返回的 `parsed`。
- 最近认识更新：2026-10-21，用户提出了“将 parsed 还原为对应 Adapter 需要发送的内容”的职责理解；助手补充模型输出格式与 API 协议组装的区别，具体内部字段尚未逐项确认。

- 继承自：[Step 1 的完整函数记录](../../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md)；只继承与重算链接，原认识时间、原话和未知保留。

- 本次继承自：[Step 2 的完整记录](../../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。共同接口要求返回 `Reply`；下面的具体字段转换采用当前 Anthropic 实现。

1. **使用场合**：`_run_turn` 已完成本轮模型生成、解码和解析，现在要把 `parsed` 整理成协议回复材料和内部记录用的消息。当前 `self` 是 `AnthropicAdapter`，执行的是它覆盖的 `_build_reply`；基类只声明接口。

2. **具体内容**：读取 `parsed.reasoning`、`parsed.text`、`parsed.tool_uses` 和 `raw_finish`，构造 `Reply(manager_message, finish_reason, wire)`。本例的 `wire` 是 Anthropic 内容块与停止原因组成的二元组；`manager_message` 是统一格式的 assistant 消息。`translated` 和 `tools_schema` 随共同接口传入，但本实现没有读取它们。

3. **建议构建的心智模型**：

   > `_build_reply` 把同一份已解析内容，整理成供两个接收方使用的表示。
   >
   > `reply.wire`：当前协议的回复材料，交给后面的 `_respond` 封装并返回 CLI。
   >
   > `reply.manager_message`：内部记录用的 assistant 消息，交给后面的轨迹记录；`reply.finish_reason` 另存内部命名的结束原因。
   >
   > 这里完成数据组装。模型内容已经生成，工具调用仍是“要调用什么、传什么参数”的描述；HTTP 响应和工具执行属于后续环节。

4. **调用代码**（[common.py:353](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L353)）：

   ```python
   reply = self._build_reply(parsed, turn.finish_reason, translated, tools_schema)
   ```

## 本场景的输入与输出

沿用 [parse_model_output 的工具调用例子](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)：用户要求读取 `README.md` 并概括，模型本轮提出读取文件。`parsed` 完整接住上一张卡片的返回值；`raw_finish="stop"` 是本例设定的生成结束原因，来自 `turn.finish_reason`。

以下是构造输入的局部运行结果。没有运行模型或执行文件工具；工具调用 ID 由源码中的随机函数实际生成，每次运行会不同。

**① 输入：保留调用处传入的四项数据。**

```python
parsed = ParsedModelOutput(
    reasoning="需要先读取 README.md。",
    text="我先读取文件。",
    tool_uses=[
        {"name": "read_file", "input": {"path": "README.md"}}
    ],
    ill_formed=False,
)
raw_finish = "stop"

# 本轮尚未执行读取；这里只保留系统指令和用户请求。
translated = [
    {"role": "system", "content": "你是代码助手。"},
    {"role": "user", "content": "读取 README.md 并概括内容。"},
]
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文件",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    }
]
```

`translated` 和 `tools_schema` 在这份实现中不参与组装。`parsed.ill_formed` 也不写入 `Reply`，调用者稍后在 `common.py:354` 将它写回 `TurnRecord`。

**② 内部先组装内容，再包装成 `Reply`。**

`AnthropicAdapter._build_reply` 的实际函数体只有下面这段：

```python
blocks, stop_reason, manager_message = _build_reply_parts(parsed, raw_finish)
return Reply(
    manager_message=manager_message,
    finish_reason=manager_finish_reason(parsed.tool_uses, raw_finish),
    wire=(blocks, stop_reason),
)
```

其中 `_build_reply_parts`（`anthropic.py:147–186`）对同一份内容分别组装两种格式：

| 输入内容 | 协议内容 `blocks` | 内部消息 `manager_message` |
| --- | --- | --- |
| `parsed.reasoning` | `{"type": "thinking", "thinking": ...}` | `reasoning_content` 字段 |
| `parsed.text` | `{"type": "text", "text": ...}` | `content` 字段 |
| `parsed.tool_uses` 中的每项 | `type: "tool_use"`，保留 `name`、`input`，新增随机 `id` | `tool_calls` 列表，工具名放入 `function.name`，参数放入 `function.arguments` |

思考文本和正文非空时才添加对应内容块；内部消息始终有 `role: "assistant"` 和 `content`。本例三类内容都存在，所以 `blocks` 按思考、正文、工具调用的顺序放入三项。

**③ 输出：完整的 `Reply`，包含三个字段。**

```python
reply = Reply(
    manager_message={
        "role": "assistant",
        "content": "我先读取文件。",
        "reasoning_content": "需要先读取 README.md。",
        "tool_calls": [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "arguments": {"path": "README.md"},
                },
            }
        ],
    },
    finish_reason="tool_calls",
    wire=(
        [
            {"type": "thinking", "thinking": "需要先读取 README.md。"},
            {"type": "text", "text": "我先读取文件。"},
            {
                "type": "tool_use",
                "id": "toolu_1b7e0addea0582cf",
                "name": "read_file",
                "input": {"path": "README.md"},
            },
        ],
        "tool_use",
    ),
)
```

`reply.wire` 当前是 `(blocks, stop_reason)`，还不是完整的 HTTP 响应 JSON。后面的 `_respond` 才根据流式模式继续封装。`reply.manager_message` 随后作为 `response_message` 传入 `manager.record_turn`，具体记录过程留到对应函数展开。

工具调用 ID 只放进协议内容；内部 `tool_calls` 没有这个 ID，`arguments` 保持字典。这样，CLI 后续把这条 assistant 消息作为历史传回时，经 `_translate` 转换出的工具调用可以与内部保存的表示按字典内容匹配。

本例同时出现三个名称：`raw_finish="stop"` 是模型生成端的结束原因；协议的 `stop_reason="tool_use"` 表示回复中有工具调用；`reply.finish_reason="tool_calls"` 使用内部命名。它们描述同一轮的不同接口，不是三次生成。

**④ 对照：没有工具调用时怎样返回？**

如果改用上一张卡片的纯文本输出，其他参数保持不变：

```python
parsed = ParsedModelOutput(
    reasoning="",
    text="这是一个学习项目。<|im_end|>",
    tool_uses=[],
    ill_formed=False,
)
```

完整返回值为：

```python
reply = Reply(
    manager_message={"role": "assistant", "content": "这是一个学习项目。<|im_end|>"},
    finish_reason="stop",
    wire=([{"type": "text", "text": "这是一个学习项目。<|im_end|>"}], "end_turn"),
)
```

这里继续保留 `parsed.text` 中的结束标记，组装阶段没有额外清洗正文。

停止原因的规则可以单独对照：

| 条件 | `wire` 中的 `stop_reason` | `reply.finish_reason` |
| --- | --- | --- |
| 有工具调用，包括 `raw_finish="length"` 时 | `"tool_use"` | `"tool_calls"` |
| 无工具调用，`raw_finish="length"` | `"max_tokens"` | `"length"` |
| 无工具调用，`raw_finish="stop"` | `"end_turn"` | `"stop"` |
| 无工具调用，其他结束原因 | `"end_turn"` | 保留 `raw_finish`，为空时用 `"stop"` |

若思考、正文和工具调用都为空，`blocks` 会补一个 `{"type": "text", "text": ""}`；内部消息仍为 `{"role": "assistant", "content": ""}`。

## 我的直接表述（原话）

先确认下一处阅读入口：

> 好的这里是否需要考虑看一下这里的build reply了对吗？

随后要求保存为短期函数记录：

> 那么现在是否考虑一下把这个builder reply的部分也写一下 作为一个short term memory的部分写出来呢？

以上两次发言确认了阅读与记录范围。前一步对 `parsed` 的理解保留在 [parse_model_output 记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)。

随后对本函数职责提出理解：

> 我的理解是这里把之前特定模型的特定输出 以及一系列的thinking或者parsed 内容做到把原来的parsed output也做一个还原
> 还原为真实的需要被发送的对应adapter的部分 我可以这么理解吗？

助手据源码澄清：整体方向对应“把已解析内容组织成客户端能接收的协议格式”。这里的“还原”更准确地说是**按目标 API 协议重新组装**：`parse_model_output` 已经处理模型特定的文本格式，得到统一的 `reasoning`、`text` 和 `tool_uses`；当前 `AnthropicAdapter._build_reply` 再把这些字段组织成 Anthropic 的 `thinking`、`text`、`tool_use` 内容块，同时准备内部记录用的消息。

例如，底层可以是 Qwen 模型，而客户端使用 Anthropic 协议；模型的输出格式和客户端的 API 协议是两层不同约定。这里不会重建 Qwen 原来的标签文本。`reply.wire` 先保存待发送的协议材料，完整响应的封装与发送交给后面的 `_respond`。

## 尚不清楚

- 已提出“parsed → 对应 Adapter 的待发送内容”的职责理解；`wire`、`manager_message` 与两种结束原因的具体关系尚未逐项确认。
- `_respond` 怎样把 `wire` 封装成普通响应或流式响应，见后续的 [BaseAdapter._respond 短期记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._respond.md)；个人理解尚待反馈，后续轨迹记录的内部实现仍未展开。

<details>
<summary>来源、验证与完整例子</summary>

- 固定源码：Slime `2f2318653f6f794dddd321eff7c9d4b7b174643f`，本机 `/home/hongshi/projects/slime`。`Reply` 定义在 [common.py:45–55](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L45-L55)；本场景的组装过程在 [anthropic.py:147–186](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L147-L186)。
- 内部工具调用形状与结束原因来自 [tool_call_dict、manager_finish_reason，common.py:110–124](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L110-L124)；传回的 assistant 历史使用同一工具调用构造函数，见 [anthropic.py:99–117](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L99-L117)。
- 返回后的使用位置：`_respond` 从 `wire` 取出内容，见 [anthropic.py:71–75](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L71-L75)；`record_turn` 接收 `reply.manager_message` 和 `turn`，见 [common.py:384–390](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L384-L390)。本版本 `_run_turn` 没有把 `reply.finish_reason` 写回 `turn.finish_reason`，不能仅据字段名称或注释推断它已经进入轨迹。
- 样例与验证：`parsed` 沿用上一张卡片；补入同一任务阶段的消息历史和 `raw_finish="stop"`。局部提取固定源码中的两个数据类、`_build_reply`、`_build_reply_parts`、`tool_call_dict` 和 `manager_finish_reason`，保留原函数体执行；隔离其余模块依赖，方法的 `self` 未被读取。核对了三类内容并存的主例、纯文本、无工具时达到长度上限、有工具时达到长度上限、全空输出五种情况。未启动 HTTP、调用模型或执行工具。
- 讨论来源：2026-10-21 本轮对话，原话保存在本页；前置及入口推荐见 [Step 1 的 parse_model_output 记录](../../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)。本页只记录当前 Anthropic 场景，其他协议实现的差异尚未展开。

</details>
