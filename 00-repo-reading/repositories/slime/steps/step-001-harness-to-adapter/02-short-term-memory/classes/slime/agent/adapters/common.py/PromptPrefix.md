# PromptPrefix

- 源码定位：[slime/agent/adapters/common.py:38–42](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L38-L42)，固定版本 `18868a79`；记录对象是 dataclass。
- 首次接触：2026-10-23，Step 1 新版校准，先在 `_session_prompt_ids` 中接触候选，再回看 `_run_turn` 的保存位置。
- 最近认识更新：2026-10-23，用户初步概括为通过 deepcopy 把对应信息放进 PromptPrefix；助手补充消息、工具定义复制，turn 保留原对象引用的区别。独立类卡的格式已由用户确认，字段区别的细化尚待反馈。
- 版本关系：旧版 `2f231865` 没有这个类型及对应的 `Session.prompt_prefixes` 字段。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、源码和本页构造例子整理，作为理解参考。

1. **使用场合**：`_run_turn` 已得到本轮回复和生成记录，在 `_respond` 与 `manager.record_turn` 正常返回后，把本轮材料保存到当前会话，供后续请求准备模型输入时取用。

2. **具体内容**：用三个字段保存一份候选：`messages` 是本轮输入历史加本轮 assistant 回复，`tools` 是本轮工具定义，`turn` 是本轮生成记录。`_run_turn` 创建实例并加入 `s.prompt_prefixes`；`_session_prompt_ids` 读取这些实例。

3. **建议构建的心智模型**：

   > - **保存一份历史候选**：把这轮的消息、工具定义和真实生成记录放在一起，留给后续同一会话的请求。
   > - **两种材料各有用途**：消息和工具定义用于核对历史，`turn` 提供当时的原始输入、输出 token。
   > - **保存后仍需检查**：`PromptPrefix` 只组织数据，能否复用由 `_session_prompt_ids` 判断。

4. **调用代码**（`_run_turn:470–472`，构造实例并由调用方保存）：

   ```python
   s.prompt_prefixes.append(
       PromptPrefix(copy.deepcopy(translated + [reply.manager_message]), copy.deepcopy(tools_schema), turn)
   )
   ```

## 本场景的输入与输出

源码中的类只定义三个字段（38–42）：

```python
@dataclasses.dataclass
class PromptPrefix:
    messages: list[dict]
    tools: list[dict] | None
    turn: TurnRecord
```

沿用“读取 README.md 并概括”的场景，观察其中请求读取文件的这一轮：输入只有 system 与 user 消息，模型已返回 `read_file` 工具调用描述。这里只观察保存材料；以下为教学构造，未实际调用模型，具体 token ID 和 logprob 未取得。

**输入（构造前已有的材料）**：

```python
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

# 已有 reply.manager_message 的值：
{
    "role": "assistant",
    "content": "我先读取文件。",
    "tool_calls": [
        {"type": "function", "function": {"name": "read_file", "arguments": {"path": "README.md"}}}
    ],
}
# turn：本轮已有的 TurnRecord，保存 prompt_ids、output_ids、
# output_log_probs、finish_reason 等字段；此处不重新生成或转换它。
```

**输出（`PromptPrefix(...)` 构造出的实例）**：用 `prefix` 指代新实例，便于展示；源码将它直接交给 `append`，没有这个局部赋值。

```text
prefix → PromptPrefix 实例
         ├─ messages = [上述 system 消息, user 消息, assistant 工具调用消息]
         ├─ tools    = [上述 read_file 工具定义]
         └─ turn     = 本轮已有的 TurnRecord 对象
```

- **`messages` 保存完整历史加回复**：本例有三条消息。这轮保存的材料包含 `read_file` 调用描述，没有 tool 结果消息；保存动作不会执行工具或添加执行结果。
- **消息与工具定义保存副本**：调用方先执行 `copy.deepcopy`，再传给构造器；复制动作不在 `PromptPrefix` 类内部。`tools` 字段也允许为 `None`，保存调用方实际传入的内容。
- **`turn` 保留同一对象**：这里没有复制它。后续检查通过时，读取其中原始 `prompt_ids`、`output_ids` 来准备接续输入。

**调用方的状态变化**：假设本例是会话中第一份候选，执行上面的保存代码后：

```text
s.prompt_prefixes：[] → [prefix]
```

已有其他候选时，追加在它们后面。实例构造得到的是 `PromptPrefix`；外层 `_run_turn` 随后继续返回原先取得的 HTTP `response`。

后续请求在 [_session_prompt_ids](../../../../../functions/slime/agent/adapters/common.py/_session_prompt_ids.md#session-prompt-understanding) 中检查这些候选，再决定复用 token 或返回普通编码。本卡保存对象的含义与构造结果，检查和拼接规则继续由该函数卡片解释。

读完回到 [_run_turn 的新版保存入口](../../../../../functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#prompt-prefix-save)，继续看保存候选后如何返回本轮响应。

## 我的直接表述（原话）

用户确认单独保存：

> 好的那么这里单独建一个函数卡片吧

随后明确记录类型：

> 如果是类的话 我记得构建的是class类型

随后，用户给出初步职责概括：

> 好的我大概理解了
> 简单来说九十八对应的信息通过deecoppy的方式放在这里的promptprefix里面对吧

助手据源码补充：`messages` 和 `tools` 由调用方通过 `deepcopy` 复制；`turn` 直接传入，保留本轮同一个生成记录对象。用户已表达保存材料的基本认识，这一字段区别的细化尚待反馈。[本次复述与接续](../../../../../../04-flow.md#prompt-prefix-understanding-and-tail)。

## 尚不清楚

- 消息和工具定义的复制、生成记录的引用已由助手区分；没有据初步概括推定三个字段的细节均已掌握。
- 哪份候选能通过检查，继续回看 `_session_prompt_ids` 已有说明；保存这一份实例本身不能证明后续一定复用。

<details>
<summary>来源、验证与完整例子</summary>

- 固定提交：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。已静态核对 [PromptPrefix 定义与 Session 容器](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L38-L57)、[构造与追加](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L463-L473)、[候选读取](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L93-L136)。
- 本例沿用 [_session_prompt_ids 的 README 场景](../../../../../functions/slime/agent/adapters/common.py/_session_prompt_ids.md)，展示更早的工具调用轮次；没有把该卡“当前候选为空”的输入当成这里追加后的状态。对象结构与状态变化为静态推导，未新增模型、tokenizer 或 HTTP 运行。
- 形成过程：[Step 1 · 新版保存语句](../../../../../../04-flow.md#prompt-prefix-save)、[记录分工建议](../../../../../../04-flow.md#prompt-prefix-memory-shape)、[确认建立类卡片](../../../../../../04-flow.md#prompt-prefix-class-card)。

</details>
