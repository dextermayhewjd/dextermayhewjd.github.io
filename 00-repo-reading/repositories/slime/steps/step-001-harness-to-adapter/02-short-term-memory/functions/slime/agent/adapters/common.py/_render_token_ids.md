# _render_token_ids

- 源码定位：[slime/agent/adapters/common.py:73](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L73-L90)，由助手核对。
- 首次接触：Step 1 的转换后交接。
- 最近认识更新：2026-10-21，用户尝试用“翻译”描述职责，仍不清楚 `apply_chat_template` 的具体作用。
- 版本校准：2026-10-23，模板编码职责保留，新增模板参数透传，当前由 `_session_prompt_ids` 调用；[旧版完整记录](../../../../../../references/render-token-ids-at-2f231865.md)保留。此项是源码校准，不改变个人认识时间。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`BaseAdapter._run_turn` 已通过 `_translate` 得到消息历史与工具定义，当前先进入 [_session_prompt_ids](_session_prompt_ids.md)，由它调用本函数进行普通模板编码。它是 `common.py` 中的模块函数；当前场景先以 `rendered` 接住结果，再由上层决定最终的 `prompt_ids`。

2. **具体内容**：`translated` 作为 `messages`、`tok` 作为 `tokenizer`、`tools_schema` 作为 `tools` 传入。内部以 `tokenize=True` 调用 `apply_chat_template`，默认传递 `add_generation_prompt=True`，同时将会话的 `apply_chat_template_kwargs` 展开交给模板；取得结果后，若包含 `input_ids` 字段便取出该字段，否则使用原结果，最后统一转为列表返回。

3. **建议构建的心智模型**：

   > `_render_token_ids` 通过聊天模板，把消息和工具定义组织成模型所需的提示，并因 `tokenize=True` 将其编码为 token ID，再统一返回列表。它返回普通编码结果；当前调用者 `_session_prompt_ids` 再决定是否接入历史原始 token，最后由 `_run_turn` 将 `prompt_ids` 交给 `call_sglang_generate`。

4. **调用代码**（[当前调用处](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L102-L103)；这里的 `messages`、`tokenizer`、`tools` 来自 `_session_prompt_ids` 的入参）：

   ```python
   kwargs = session.apply_chat_template_kwargs
   rendered = _render_token_ids(messages, tokenizer, tools=tools, apply_chat_template_kwargs=kwargs)
   ```

## 本场景的输入与输出

沿用 [BaseAdapter._translate 的教学缩减场景](BaseAdapter._translate.md)：工具已经返回文件内容，现在将消息历史和可用工具定义交给模型继续概括。以下直接接住该记录的两份输出；原请求由 `AnthropicAdapter._translate` 具体转换。

输入：

```python
translated = [
    {"role": "system", "content": "你是代码助手。"},
    {"role": "user", "content": "读取 README.md 并概括内容。"},
    {
        "role": "assistant",
        "content": "我先读取文件。",
        "tool_calls": [
            {"type": "function", "function": {"name": "read_file", "arguments": {"path": "README.md"}}}
        ]
    },
    {"role": "tool", "content": "# Demo\n这是一个学习项目。"},
    {"role": "user", "content": "请用一句话概括。"}
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
                "required": ["path"]
            }
        }
    }
]
tok = self.tokenizer  # 调用方使用的模型 tokenizer，具体实例尚未核对
add_generation_prompt = True
apply_chat_template_kwargs = {}  # 本例没有额外模板选项；实际由 session 传入
```

输出约定（具体值取决于模型 tokenizer 与模板参数）：

```python
rendered: list[int]  # 当前调用处对本函数返回列表的命名
```

本函数只返回一份 token ID 列表。当前先返回 `_session_prompt_ids:103`；后者确定最终的 `prompt_ids`，再由 `_run_turn:423` 交给 `call_sglang_generate`。本轮用已下载的 Qwen tokenizer 对相同场景做了局部验证，普通编码结果为 337 个 token，详见 [_session_prompt_ids 的输入输出](_session_prompt_ids.md#本场景的输入与输出)；这不代表已核对线上服务实际加载的 tokenizer。

`add_generation_prompt=True` 请求模板为下一条助手回复准备开头，具体效果由模板决定。`_session_prompt_ids` 检查历史前缀时还会以 `add_generation_prompt=False` 调用本函数，此时不额外请求下一条助手回复的开头。本函数始终只负责渲染与编码，不选择历史前缀。其中“套模板与编码”的简短记录见 [PreTrainedTokenizerBase.apply_chat_template](../../../../src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md)。

<a id="render-token-result-branches"></a>

### 编码函数自身的分支：统一返回形态

上层的“选哪份历史、在哪里拼接”见 [_session_prompt_ids 的分支图](_session_prompt_ids.md#session-prompt-branches)。本函数的 `73–90` 行只负责传递模板参数、编码，再将结果统一成列表：

```text
messages + tools + 模板参数
            ↓
tokenizer.apply_chat_template(..., tokenize=True) → enc
            ↓
enc 可取项，而且包含 "input_ids"？                  89 行
├─ 是 → ids = enc["input_ids"]   从结构化结果中取出 ID
└─ 否 → ids = enc                直接使用返回的 ID 序列
            ↓
return list(ids)                                    90 行
```

这两个分支处理的是 tokenizer 返回值的形态，最后都交出 `list[int]`。`add_generation_prompt=True / False` 则是传给模板的参数，决定是否请求补上下一条助手回复的开头；两种参数都会编码。当前上层两处调用怎样取值，见 [①完整编码与⑤前缀编码](_session_prompt_ids.md#session-render-calls)。

## 我的直接表述（原话）

以下是用户选择阅读对象时的问题，尚不是已经确认的职责模型：

> 那么这里是否比较适合的是在这里看一下这里的prompt_ids是如何把结果交给模板的呢？
> 我的意思是是不是这里就需要看一下这里的_render_token_ids了？ 按照之前的方法整理short term function的方式处理一下
>
> 看一下是否有这里对应的skill呢？

随后给出的初步理解与追问：

> 我的理解是这里把原先的translated和tools_schema 按照tokenizer内部的训练方式，实现了这里的内容？
> 我的意思是完成了对这里的翻译？
> 但是我不理解的是这里的tokenizer的apply chat plate是在做什么

助手澄清：“按照模型训练时使用的对话格式”更准确；这里应用已有模板，再编码成 token ID。模板负责如何组织对话，编码负责把组织好的提示转为编号；用户尚未确认这一划分。

## 尚不清楚

- 当前实际模型的模板怎样排列系统消息、历史工具调用、工具结果与可用工具定义，以及对应哪些 token ID，尚未展开。
- 用户已提出“翻译／转换”的初步理解，仍不清楚 `apply_chat_template` 的具体作用；尚未确认套用聊天格式与编码成 ID 的区别。

<details>
<summary>来源、验证与完整例子</summary>

- 当前源码校准：[函数体 73–90 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L73-L90)、[调用处 102–103、127–129 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L102-L129)。模板参数透传与历史前缀的配合见 [本轮记录](../../../../../../../step-001-harness-to-adapter/04-flow.md#session-prompt-ids)。
- 原始认识与以下历史验证使用固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`：[函数体 `common.py:58–73`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L58-L73)与[调用处 `341–344`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341-L344)。
- 下方保留的局部验证使用同版本的 [`FakeTokenizer`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/_fakes.py#L41-L113)。2026-10-21 从原文件按 AST 提取本函数、测试类及其常量，局部执行核对返回值和 `tok.rendered`；未运行真实模型或端到端请求。
- API 含义参照 [Hugging Face 聊天模板文档](https://huggingface.co/docs/transformers/chat_templating#add_generation_prompt)；逐行讲解与证据见[本次正文](../../../../../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#render-token-ids)。
- 形成过程：[Step 1 · 从转换结果接到模板编码](../../../../../../../step-001-harness-to-adapter/04-flow.md#render-token-ids)。
- 本次澄清：[Step 1 · 套模板和编码各做什么](../../../../../../../step-001-harness-to-adapter/04-flow.md#chat-template-two-actions)；[对应讲解](../../../../../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#chat-template-two-actions)。
- 主样例继续接住上游转换记录的全部消息和工具定义。此前的格式调整只做静态核对，未运行真实模型 tokenizer；2026-10-23 的版本校准另做了本地 Qwen tokenizer 验证，结果保存在 `_session_prompt_ids` 卡片。两次整理均不改变原话、认识时间或个人理解状态。

**此前的局部验证（保留原样例）**

教学构造：保留系统消息、用户消息和一个完整工具定义，观察参数交接。`tok` 使用原仓库 `tests/test_agent/_fakes.py` 的 `FakeTokenizer`，下面是局部实际执行的结果。**这些数字只属于测试替身；它接收并记录 `tools`，没有把工具定义编码进 token，不能据此判断真实模型的工具模板。**

```python
# Input
translated = [
    {"role": "system", "content": "你是代码助手。"},
    {"role": "user", "content": "读取 README.md。"},
]
tools_schema = [{
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
}]
tok = FakeTokenizer()

prompt_ids = _render_token_ids(translated, tok, tools=tools_schema, add_generation_prompt=True)

# Output：本函数只有这一项返回值；工具定义已经随 tools 参数传入模板调用。
[1, 100, 5, 2, 101, 102, 5, 3]
```

这份旧版测试替身样例只验证函数交接，保留作历史证据；新版另用本地 Qwen tokenizer 核对了上方主场景，完整数据见 [_session_prompt_ids 的验证记录](../../../../../../references/session-prompt-ids-version-check-18868a79.json)。

</details>
