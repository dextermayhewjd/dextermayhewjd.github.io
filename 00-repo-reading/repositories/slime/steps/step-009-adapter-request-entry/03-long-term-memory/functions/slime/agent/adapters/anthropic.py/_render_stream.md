# _render_stream

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../step-008-harness-communication/03-long-term-memory/functions/slime/agent/adapters/anthropic.py/_render_stream.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/adapters/anthropic.py:211–274](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L211-L274)，由助手核对。
- 首次接触：Step 1，2026-10-21；此前随 `_respond` 阅读，本次从其记录拆出。
- 最近认识更新：尚无本函数内部实现的直接复述；拆分不计为新增理解。

从 [_respond 的流式分支](../common.py/BaseAdapter._respond.md#response-tree)进入；事件写出后，响应对象返回 `_respond:74`，再交回 `_run_turn:363`。

- 继承自：[Step 1 的完整函数记录](../../../../../../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/_render_stream.md)；只继承与重算链接，原认识时间、原话和未知保留。

- 本次继承自：[Step 2 的完整记录](../../../../../../../step-003-swe-evaluation/03-long-term-memory/functions/slime/agent/adapters/anthropic.py/_render_stream.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据当前 Anthropic 实现整理，作为理解参考。

1. **使用场合**：`_respond` 已获得完整回复材料，且本次 `stream=True`，需要以 SSE 格式回应已有 HTTP 请求。

2. **具体内容**：创建并准备 `web.StreamResponse`，依次写出消息开始、每个内容块的开始/内容/结束、停止信息和消息结束事件，最后返回这个响应对象。

3. **建议构建的心智模型**：

   > `_render_stream` 将已经生成完的回复拆成 SSE 事件，并按顺序写入本次 HTTP 响应。返回时事件已写出，返回值仍是同一个响应对象。

4. **调用代码**（`anthropic.py:73–74`）：

   ```python
   if stream:
       return await _render_stream(request, blocks, stop_reason, in_tok, out_tok)
   ```

## 本场景的输入与输出

与父卡普通分支使用同一份回复、同样的构造计数 `100/40`；这里观察选择流式后的路径。`request` 是同一次 POST 的 `web.Request`，`body` 和 `stream` 不再作为参数传进本函数。

**输入：**

```python
blocks = [
    {"type": "thinking", "thinking": "需要先读取 README.md。"},
    {"type": "text", "text": "我先读取文件。"},
    {"type": "tool_use", "id": "toolu_1b7e0addea0582cf", "name": "read_file", "input": {"path": "README.md"}},
]
stop_reason = "tool_use"
in_tok = 100
out_tok = 40
```

**输出与副作用：** 返回已准备的 `web.StreamResponse`；状态 `200`，`Content-Type: text/event-stream`。本例的 12 个 SSE 事件已按以下顺序写出：

```text
message_start
content_block_start → content_block_delta → content_block_stop   # index=0，thinking
content_block_start → content_block_delta → content_block_stop   # index=1，text
content_block_start → content_block_delta → content_block_stop   # index=2，tool_use
message_delta
message_stop
```

| 事件中的内容 | 本例实际发送的数据 |
| --- | --- |
| `message_start` | 消息外层信息；`content=[]`，`output_tokens=0`，停止原因暂为 `null` |
| `thinking_delta` | `thinking: "需要先读取 README.md。"` |
| `text_delta` | `text: "我先读取文件。"` |
| `input_json_delta` | `partial_json: '{"path": "README.md"}'`，参数在这个事件里是 JSON 字符串 |
| `message_delta` | `stop_reason: "tool_use"`，用量更新为输入 `100`、输出 `40` |
| `message_stop` | 本条消息结束 |

**实现怎样接起来。** 源码中三个连续阶段各负责一件事：

| 源码位置 | 实际行为 | 进入下一段时已有的结果 |
| --- | --- | --- |
| `anthropic.py:215–238` | 创建响应，`await out.prepare(request)`，写出 `message_start` | HTTP 响应已准备，消息外层信息已写出 |
| `:240–262` | 按块类型生成 `start` 和 `delta`，每块依次写 start、delta、stop | 三个内容块依次写出，共 9 个事件 |
| `:264–274` | 写出停止原因、最终计数和 `message_stop`，`return out` | 返回已写出这些事件的同一个响应对象 |

当前实现每个内容块写一个完整的 delta。这里的“流式”描述 HTTP 发送格式；`_respond` 接到的已经是完整 `reply`，没有一边调用 SGLang 生成新 token、一边转发它们。全部 12 个事件的内容放在下方折叠区。

流式分支返回时，事件已在 `_render_stream` 内写出，返回值仍是同一个 `web.StreamResponse` 对象。写入成功也不能证明客户端业务代码已经消费了这些事件。

`_respond` 返回后继续执行 `common.py:376–390` 的调试回调和轨迹记录，最后由 `_run_turn` 返回响应对象。回到[父卡的返回位置](../common.py/BaseAdapter._respond.md#return-to-run-turn)，本轮不继续展开轨迹记录内部。

## 我的直接表述（原话）

尚无本函数的直接复述；用户对 `_respond` 内部实现的疑问保留在[父卡](../common.py/BaseAdapter._respond.md#personal-statements)。

## 尚不清楚

- SSE 字段、顺序和写出时机由助手核对，个人理解尚待反馈。
- CLI 如何消费这些事件并执行工具，本轮未展开；HTTP 写出不证明客户端业务代码已经处理完成。

<details>
<summary>来源、验证与完整例子</summary>

- 原始步骤上下文：[Step 1 的请求处理与发送时机纠正](../../../../../../../step-001-harness-to-adapter/04-flow.md#run-turn-reading-scope)。

- 固定源码：Slime `2f2318653f6f794dddd321eff7c9d4b7b174643f`，本机 `/home/hongshi/projects/slime`，`anthropic.py:211–274`。
- 原实验保持 `reply` 和计数不变，将 `body["stream"]` 改为 `True`；父函数据此选择本分支。另核对了 `Accept: text/event-stream` 也会选择本分支，即使 `body["stream"]` 为 `False`。这些参数判断仍由 `_run_turn` 执行，见[父卡输入准备](../common.py/BaseAdapter._respond.md#response-preparation)。
- 本版本流式分支固定写 `"model": "slime-actor"`；普通分支则从 `body` 取模型名，本例两者一致。
- 原局部 HTTP/SSE 运行的范围与发送时机见[父卡来源](../common.py/BaseAdapter._respond.md#source-evidence)。完整事件从原卡迁移，消息 ID 保留原运行值；没有新增 CLI、SGLang 或工具执行证据。
- 形成来源：Step 1 中随 `_respond` 展开的记录；[确认与迁移记录](../../../../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#respond-split-implemented)。

本例流式响应的完整事件帧（JSON 空格仅作排版）：

```text
event: message_start
data: {"type":"message_start","message":{"id":"msg_aa1997d2f4f94b0224a5c085","type":"message","role":"assistant","model":"slime-actor","content":[],"stop_reason":null,"stop_sequence":null,"usage":{"input_tokens":100,"output_tokens":0}}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"thinking","thinking":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"thinking_delta","thinking":"需要先读取 README.md。"}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: content_block_start
data: {"type":"content_block_start","index":1,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":1,"delta":{"type":"text_delta","text":"我先读取文件。"}}

event: content_block_stop
data: {"type":"content_block_stop","index":1}

event: content_block_start
data: {"type":"content_block_start","index":2,"content_block":{"type":"tool_use","id":"toolu_1b7e0addea0582cf","name":"read_file","input":{}}}

event: content_block_delta
data: {"type":"content_block_delta","index":2,"delta":{"type":"input_json_delta","partial_json":"{\"path\": \"README.md\"}"}}

event: content_block_stop
data: {"type":"content_block_stop","index":2}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"tool_use","stop_sequence":null},"usage":{"input_tokens":100,"output_tokens":40}}

event: message_stop
data: {"type":"message_stop"}
```

</details>
