# parse_model_output

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../step-011-generate-and-rm-group/03-long-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 03-long-term-memory](../../../../../../step-010-generate-and-rm/03-long-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- Step 010 继承：2026-10-25，来自 [Step 009 · 03-long-term-memory 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)。正文、原话、认识日期、源码版本与未知沿用来源；仅继承和重算链接。

- 本次继承：2026-10-23，[Step 7 · 03 完整记录](../../../../../../../../01-coding-agent-rl/steps/step-008-harness-communication/03-long-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)。仅合并与重算链接，首次接触、认识时间、原话和未知沿用原卡。

- 源码定位：[slime/agent/parsing.py:25–56](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/parsing.py#L25-L56)，由助手核对。
- 首次接触：Step 1，承接 `tok.decode` 得到的 `raw_output`。
- 最近认识更新：2026-10-21，用户进一步表述了“原始输出逐步拆成 reasoning、text、工具相关字段，再继续处理 parsed”的关系；具体分支实现及后续处理仍待展开。

- 继承自：[Step 1 的完整函数记录](../../../../../../../../01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)；只继承与重算链接，原认识时间、原话和未知保留。

- 本次继承自：[Step 2 的完整记录](../../../../../../../../01-coding-agent-rl/steps/step-003-swe-evaluation/03-long-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)；仅复制、补来源与重算链接，原话、认识时间和未知保留。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`_run_turn` 已把本轮生成的 token ID 解码成 `raw_output`，需要区分其中的思考文本、正文与工具调用，供下一步 `_build_reply` 组织响应。

2. **具体内容**：先按 `reasoning_parser_name` 分离思考文本，再将剩余文本交给 `parse_tool_uses`，结合 `tools_schema` 和 `tool_parser_name` 提取工具名称与参数。最后返回 `ParsedModelOutput`，包含 `reasoning`、`text`、`tool_uses` 和 `ill_formed` 四项。

3. **建议构建的心智模型**：

   > `decode` 把编号变成字符串；`parse_model_output` 再把这个字符串拆成“思考文本、正文、工具调用描述”，并附上解析异常标记。
   >
   > 三类内容可以同时存在。工具调用描述保存“调用什么、传什么参数”，这里不执行工具；工具执行后的返回结果属于后续交互。

4. **调用代码**（[common.py:347–353](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L347-L353)）：

   ```python
   parsed = parse_model_output(
       raw_output,
       tools_schema=tools_schema,
       tool_parser_name=self.tool_parser,
       reasoning_parser_name=self.reasoning_parser,
   )
   reply = self._build_reply(parsed, turn.finish_reason, translated, tools_schema)
   ```

## 本场景的输入与输出

沿用“读取 README.md 并概括”的任务，以及[上一步的本地 Qwen tokenizer](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md)。为看清工具调用分支，下面观察这个任务**尚需读取文件的一轮**；末尾再接回上一步已有的纯文本输出。

示例文本由助手构造，经同一 tokenizer 实际编码、解码后交给解析器。解析值已局部运行核对；没有调用模型生成文本，也没有实际读取 README.md。解析器名称采用 Slime 当前 Qwen 示例的 `qwen3` 与 `qwen3_coder`。

**① 输入：一段原始文本、工具定义、两个解析器名称。**

```python
raw_output = """<think>需要先读取 README.md。</think>
我先读取文件。
<tool_call>
<function=read_file>
<parameter=path>README.md</parameter>
</function>
</tool_call><|im_end|>"""

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
tool_parser_name = "qwen3_coder"
reasoning_parser_name = "qwen3"
```

| 输入 | 在本例中的作用 |
| --- | --- |
| `raw_output` | 提供实际要拆分的内容；此时标签和参数都还在一个字符串中 |
| `reasoning_parser_name` | 选择识别 `<think>…</think>` 等思考边界的规则 |
| `tool_parser_name` | 选择识别 `<tool_call>`、`<function=…>`、`<parameter=…>` 的规则 |
| `tools_schema` | 提供工具定义；本例让解析器知道 `read_file` 的 `path` 参数是字符串 |

**② 先分离思考文本，剩余内容继续往下传。**

`parsing.py:38–48` 先令 `reasoning = ""`、`body_text = raw_output`，再调用 SGLang 的 `ReasoningParser(...).parse_non_stream(raw_output)`。本例得到：

```python
reasoning = "需要先读取 README.md。"
body_text = """
我先读取文件。
<tool_call>
<function=read_file>
<parameter=path>README.md</parameter>
</function>
</tool_call><|im_end|>"""
```

`body_text` 开头保留换行；其中仍有正文和工具调用。接下来的工具解析处理这个剩余字符串，不再处理已经分离出的 `reasoning`。

**③ 再提取工具调用：先得到 JSON 参数字符串，再转成字典。**

`parsing.py:50` 调用同文件的 `parse_tool_uses`。其 `:67–76` 将 `tools_schema` 包装成 SGLang 的 `Tool` / `Function` 对象，并选择 `FunctionCallParser(..., tool_call_parser="qwen3_coder")`。检测到 `<tool_call>` 后，解析器在本例交出：

```python
body_text = "\n我先读取文件。\n"
calls = [
    ToolCallItem(
        tool_index=0,
        name="read_file",
        parameters='{"path": "README.md"}',
    )
]
```

这里的 `parameters` 仍是 **JSON 字符串**。Slime 随后执行 `json.loads(c.parameters or "{}")`，再整理为自己的结构（`:79–85`）：

```python
args = {"path": "README.md"}
tool_uses = [
    {"name": "read_file", "input": {"path": "README.md"}}
]
ill_formed = False
```

这一步的 `input` 是准备传给工具的参数；这里还没有文件内容，也没有工具执行结果。SGLang 中间结果的 `tool_index` 不会写入这个 `tool_uses`。

**④ 返回：将三类内容和状态装进同一个对象。**

`parsing.py:51–56` 对剩余正文调用 `.strip()` 去除两端空白，并返回：

```python
ParsedModelOutput(
    reasoning="需要先读取 README.md。",
    text="我先读取文件。",
    tool_uses=[
        {"name": "read_file", "input": {"path": "README.md"}}
    ],
    ill_formed=False,
)
```

这就是本函数完整的返回值。`reasoning`、`text` 和 `tool_uses` 可以同时非空；它们还没有包装成 Anthropic 或 OpenAI 的协议消息，调用方下一步把 `parsed` 交给 `_build_reply`。

`ill_formed=False` 表示本路径没有触发对应的解析错误标记，不代表工具已经执行成功，也不保证通过了完整 JSON Schema 校验。当前代码在工具参数无法 `json.loads` 时保留 `{"_raw_arguments": ...}` 并设为 `True`。

**⑤ 接回上一步：原始输出只有正文时，另外两项为空。**

保持同一份工具定义和解析器名称，只把输入换成上一步实际解码得到的字符串：

```python
raw_output = "这是一个学习项目。<|im_end|>"
```

本次局部运行得到：

```python
ParsedModelOutput(
    reasoning="",
    text="这是一个学习项目。<|im_end|>",
    tool_uses=[],
    ill_formed=False,
)
```

即使传入了 `tools_schema`，原文没有工具调用，也不会凭空产生 `tool_uses`。这里的 `<|im_end|>` 仍保留在正文中：本函数不会统一删除所有特殊标记，`.strip()` 只去两端空白。上面的工具分支中，Qwen 工具解析器取第一个 `<tool_call>` 前的文字作为正文，不能据那个例子推断纯文本分支也会删掉结束标记。

## 我的直接表述（原话）

本轮确认继续阅读解析函数，并提出当前理解与疑问：

> 那么现在请继续吧是不是能够继续处理这里的parse_model_output了呢？
> 我个人的理解就是这里的output做的事情就是 把这里一系列的raw的output
> 按照合理的tools schema和tool parser的逻辑，以及这里的thinking chain的逻辑切换成为模型的真实可能tool output或者是这里的message对吗？
> 但是我不是特别清楚这里的具体是怎么实现的以及数据格式
> 请你帮我整理一下吧

助手据源码澄清：这里的 `tool_uses` 是工具调用请求，工具返回结果尚未产生；思考文本、正文和调用描述可以并存。

随后对职责与交接的复述：

> 所以就是基本上就是按照这个output来做到逐渐的拆解对吗？
> 把这些拆解成为reasoning text tools 以及这一系列的规范的内容
> 然后在考虑如何继续生成或者处理这里的parsed了 是我的理解

助手补充后续边界：`parsed` 是这次拆分得到的结构化对象。紧接着的 `_build_reply` 把已有字段组织成协议回复；此处没有再次调用模型生成 token。后续处理的内部实现尚未展开。

随后提出下一处阅读入口：

> 好的这里是否需要考虑看一下这里的build reply了对吗？

助手定位：当前 `self` 是 `AnthropicAdapter`，建议从 `common.py:353` 进入 `anthropic.py:63` 的 `_build_reply`，再看 `anthropic.py:147–186` 的 `_build_reply_parts`。本次推荐的范围是 `parsed → Reply`，先看清协议内容与轨迹消息怎样组装；HTTP 发送由后面的 `_respond` 负责，另行展开。

## 尚不清楚

- 已表达“原始输出 → 结构化字段 → 后续处理”的关系；具体解析分支及异常处理尚未逐项确认，不据此标为全部理解。
- 其他模型格式、多个或不完整工具调用、参数异常的详细处理。
- `_build_reply` 怎样把这些字段包装为协议响应：后续说明已保存到 [BaseAdapter._build_reply 的短期记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md)，个人理解尚待反馈。

<details>
<summary>来源、验证与完整例子</summary>

- Slime 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：返回类型在 [parsing.py:15–22](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/parsing.py#L15-L22)，工具参数解包在 [:59–90](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/parsing.py#L59-L90)。工具解析未得到调用时，带工具定义的请求还会进入同文件的 XML 备用解析（`:93–114`）；本例工具调用由 Qwen 解析器直接取得。
- `reasoning_parser_name="qwen3"`、`tool_parser_name="qwen3_coder"` 来自 [Coding Agent 示例脚本](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/run_qwen36_35b_a3b_swe_8nodes.sh#L185-L186)。SGLang 参考版本采用该 Slime 提交 [docker/README.md](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/docker/README.md#L7-L8) 中的 `v0.5.15.post1`，提交 `0b3bb0cbe31873994c9f989fddfe2f87ca839fdd`。
- 思考分离依据 [ReasoningParser](https://github.com/sgl-project/sglang/blob/0b3bb0cbe31873994c9f989fddfe2f87ca839fdd/python/sglang/srt/parser/reasoning_parser.py#L1065-L1153) 与同文件的 `Qwen3Detector`、`BaseReasoningFormatDetector.detect_and_parse`；工具格式及参数类型处理依据 [Qwen3CoderDetector](https://github.com/sgl-project/sglang/blob/0b3bb0cbe31873994c9f989fddfe2f87ca839fdd/python/sglang/srt/function_call/qwen3_coder_detector.py#L60-L237)。工具 schema 用于查参数类型，不把它描述成会自动补齐缺失参数的完整校验器。
- 验证环境沿用上一步：Python `3.12.3`、Transformers `4.57.6`、Tokenizers `0.22.2`，Qwen tokenizer revision `995ad96eacd98c81ed38be0c5b274b04031597b0`。构造文本经本地 tokenizer 编码后，用 `skip_special_tokens=False` 解码，逐字核对一致后送入解析。
- 本机未安装完整 SGLang。局部验证从上述固定源码提取 Qwen 相关数据类与非流式方法，保留其原方法体；注册表只留本次用到的 Qwen 项，省略其他模型和未调用的方法。工具严格度配置用本路径不会读取的占位值提供。随后执行未修改的 Slime `parsing.py`，核对完整字段及中间结果；这属于局部解析验证，不是模型服务的端到端运行。
- 已核对四种构造输入：上一步纯文本、思考加工具调用、思考加正文、缺少开头 `<think>` 但保留 `</think>`。最后一种走 Slime `:47–48` 的备用分割，得到与完整标签例子一致的结果。未调用模型推理或执行工具，不将构造的思考文本当成真实模型内部过程。
- 讨论来源：2026-10-21 本轮对话，用户原话保存在本页；前置见 [decode 的短期记录](../../../../../../../../01-coding-agent-rl/steps/step-009-adapter-request-entry/03-long-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md)。

</details>
