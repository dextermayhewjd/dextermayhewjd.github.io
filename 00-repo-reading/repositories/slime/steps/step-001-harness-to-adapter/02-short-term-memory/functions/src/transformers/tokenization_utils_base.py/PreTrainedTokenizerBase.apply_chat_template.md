# PreTrainedTokenizerBase.apply_chat_template

- 源码定位：[Transformers · tokenization_utils_base.py:1546](https://github.com/huggingface/transformers/blob/v4.57.1/src/transformers/tokenization_utils_base.py#L1546-L1721)，接口参考版本为 `v4.57.1`，由助手核对。
- 首次接触：Step 1 的 `_render_token_ids`。
- 最近认识更新：2026-10-21 提出疑问；本次调整格式与场景，不计为已掌握。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`_translate` 已整理好消息历史和工具定义，`_render_token_ids` 调用本方法，把它们准备成模型输入。

2. **具体内容**：`messages` 接住 `translated`，包括系统指令、普通消息、历史工具调用和结果；`tools` 接住 `tools_schema`，描述可用工具。方法按 tokenizer 的聊天模板组织这些内容，再因 `tokenize=True` 编码成 token ID；`add_generation_prompt=True` 请求模板准备下一条助手消息的开头，具体效果由模板决定。

3. **建议构建的心智模型**：

   > `apply_chat_template` 先按模型需要的聊天格式组织消息和工具定义，再按当前调用要求编码成 token ID。返回值是供后续生成使用的输入，这里还没有生成下一条回复。

4. **调用代码**（[`common.py:66–71`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L66-L71)）：

   ```python
   enc = tokenizer.apply_chat_template(
       messages,
       tools=tools,
       tokenize=True,
       add_generation_prompt=add_generation_prompt,
   )
   ```

## 本场景的输入与输出

沿用 [BaseAdapter._translate 的场景](../../../slime/agent/adapters/common.py/BaseAdapter._translate.md)：文件已经读取，消息历史与工具定义已转换好，现在准备让模型继续概括。下面直接接住它的两份输出，保留真实调用中的工具信息和 `tokenize=True`。

输入：

```python
messages = [
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
tools = [
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
tokenize = True
add_generation_prompt = True
```

输出约定（当前参考版本、单组对话、默认不返回张量或字典）：

```python
enc: list[int]  # 消息与工具信息按模板组织、编码后的 token ID
```

这是已核对的返回类型，具体整数值尚未取得：需要确定实际模型的 tokenizer、词表与模板后才能运行填写。`enc` 交回 `_render_token_ids` 统一为列表，随后由 `_run_turn` 用 `prompt_ids` 接住；此处不以另一个模板或 `tokenize=False` 的字符串代替当前输出。

## 我的直接表述（原话）

用户上一轮的疑问（节选）：

> 但是我不理解的是这里的tokenizer的apply chat plate是在做什么

## 尚不清楚

- 当前实际模型的模板怎样放入历史工具调用、工具结果和工具定义，以及具体 token ID，尚未核对。
- 用户尚未确认套模板与编码的区别；助手的模型仍是理解参考。

<details>
<summary>来源、验证与完整例子</summary>

- Slime 调用绑定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`；Transformers `v4.57.1` 仅用于核对接口及渲染、编码分支，不冒称当前运行版本。Slime 未锁定该依赖，本机当前解释器也未安装它。
- 输入原样复用上游转换记录中的两份结果，仅改为此调用中的参数名；本函数未用真实模型 tokenizer 执行，输出只核对到类型与后续用途。
- 形成过程：[Step 1 · 套模板和编码](../../../../../../step-001-harness-to-adapter/04-flow.md#chat-template-two-actions)；[单独建卡](../../../../../../step-001-harness-to-adapter/04-flow.md#apply-chat-template-card)。
- 完整解释与 `tokenize=False` 的观察方式见[原讲解](../../../../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#chat-template-two-actions)；此前“你好”的自定义模板实验保留在[修正前快照](../../../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/references/2026-10-21-short-term-template-drift-before.md)，不作为本场景的主样例。

</details>
