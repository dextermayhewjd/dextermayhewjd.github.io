# _session_prompt_ids

- 源码定位：[slime/agent/adapters/common.py:93–136](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L93-L136)，固定版本 `18868a79`，由助手核对。
- 首次接触：2026-10-23，Step 1 新版校准，接在 `_translate` 之后。
- 最近认识更新：2026-10-23，用户选用“同一候选的连续检查”与“普通编码回退”的完整解释，并要求由它提炼简短心智模型，不清楚时回看详细理解；具体边界机制仍未逐项确认。
- 版本关系：旧版 `2f231865` 没有本函数，由 `_run_turn` 直接调用 `_render_token_ids`；新版增加这一层，再调用已有的模板编码函数。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`BaseAdapter._run_turn` 已取得 `translated`、`tools_schema` 和当前会话 `s`，现在需要准备本轮交给模型的 `prompt_ids`。

2. **具体内容**：先调用 `_render_token_ids` 得到普通编码结果，再逐个检查 `s.prompt_prefixes` 保存的历史材料。客户端传回的消息可能省略旧思考或重新整理工具参数，重新编码未必还原原始 token；如果找到可确认的历史前缀，就保留该轮真实的输入、输出 token，接上新内容。某个候选不合格就继续检查下一个；全部不合格才返回普通编码结果。

3. **建议构建的心智模型**：

   > - **准备输入**：先把本次全部消息和工具定义编码为 `rendered`。
   > - **检查候选**：逐个检查历史 `prefix`，核对基础条件与 `anchor` 的前缀、切口；不合格就继续检查下一个。
   > - **候选合格**：返回“旧输入 token + 旧输出 token + 新后缀”。
   > - **全部不合格**：返回开头已经算好的 `rendered`。
   > - **职责边界**：这里只准备模型输入，不生成摘要或新的模型回复。

   这是根据下方说明提炼的简短总结；不清楚时，查看[详细理解与两张图](#session-prompt-understanding)。

4. **调用代码**（[当前交接](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L415-L423)，省略后续处理）：

   ```python
   translated, tools_schema = self._translate(body)
   prompt_ids = _session_prompt_ids(translated, tok, tools=tools_schema, session=s)
   turn = await call_sglang_generate(prompt_ids, s, body, adapter=self, session_id=sid)
   ```

## 本场景的输入与输出

<a id="session-prompt-understanding"></a>

### 详细理解：前缀检查、anchor 与普通编码回退

：逐个检查 session.prompt_prefixes，判断能否复用某份历史来拼接。

需要调整的是：中间这些是同一个候选必须依次通过的检查，anchor 也在其中。

```text
取一个 prefix
    ↓
历史匹配、生成状态、歧义检查
    ├─ 不通过 → 检查下一个 prefix
    └─ 通过
         ↓
       计算这个候选的 anchor，检查前缀与拼接切口
         ├─ 不通过 → 检查下一个 prefix
         └─ 通过 → 拼接并返回
```

anchor 是把当前候选覆盖的那段消息重新编码得到的 token 列表，用来核对能否可靠地拼接。即使前面的历史匹配了，也必须经过这一步，才能拼接；它不是失败后寻找的另一份历史。

如果所有候选都不合格，直接返回 rendered。 它在函数开头就已经算好了：

```text
本次请求的全部 messages + tools
             ↓ 套模板、编码
          rendered
```

所以，最后并没有固定的“摘要＋工具结果”策略：

- 当前消息本来包含摘要和工具结果，就一起编码。
- 当前消息没有摘要，这个函数也不会生成摘要。
- 返回的是供后续模型使用的 token ID 列表，不是模型新生成的答案。

**为什么要保留原始 token？** 客户端传回的可见消息可能省略模型的思考，或重新组织工具参数。确认是同一段历史后，复用当时的原始 token，可以避免仅凭可见消息重新编码造成的差异。

### 一个完整场景的输入与输出

沿用 [BaseAdapter._translate](BaseAdapter._translate.md) 的“读取 README 并概括”场景。下面保留它的全部消息和工具定义；为观察返回值，局部验证选用已下载的 `Qwen/Qwen3.6-35B-A3B` tokenizer，未运行模型生成。

**输入：**

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
s = Session()  # 本例尚无本地保存的历史前缀，模板附加参数为 {}
# tok：已加载的本地 Qwen tokenizer；实际调用中来自 self.tokenizer
prompt_ids = _session_prompt_ids(translated, tok, tools=tools_schema, session=s)
```

- `translated`、`tools_schema`：当前请求的完整消息与工具定义，分别传入 `messages`、`tools`。
- `tok`：提供聊天模板、编码、解码与特殊 token 信息。
- `s`：本函数读取 `apply_chat_template_kwargs` 和 `prompt_prefixes`；不读取整个轨迹树。

### 本例的 Session 信息

本例 `s = Session()`，`s.prompt_prefixes` 为空。有历史记录时，其中每项是一个 [PromptPrefix 实例](../../../../../classes/slime/agent/adapters/common.py/PromptPrefix.md)，保存以下材料：

| 保存字段 | 在本例中的含义 |
| --- | --- |
| `prefix.messages` | 上轮输入消息加上轮助手回复，例如 `translated[:3]` |
| `prefix.tools` | 上轮使用的 `tools_schema` |
| `prefix.turn` | 上轮生成记录，包含真实的 `prompt_ids`、`output_ids`、`finish_reason` 等 |

这些材料在本轮 `_respond` 与 `manager.record_turn` 正常返回后，由 `_run_turn:470–472` 保存；本函数只读取。这里的 `messages` 用来匹配当前历史，`turn` 提供要保留的原始 token，两者并非同一份数据。

<a id="prompt-prefix-save"></a>

**这些候选怎样写入？** 相对旧版 `2f231865`，下面是 `18868a79` 新增在 `_run_turn` 中的保存语句，并非 `_session_prompt_ids` 内部的操作：

```python
s.prompt_prefixes.append(
    PromptPrefix(copy.deepcopy(translated + [reply.manager_message]), copy.deepcopy(tools_schema), turn)
)
```

`PromptPrefix` 的三个位置参数依次是 `messages`、`tools`、`turn`：

- `messages`：本轮输入的全部消息，加上本轮 assistant 回复；保存为下一次比较历史的候选。
- `tools`：本轮的工具定义；后续还要检查工具定义是否一致。
- `turn`：本轮生成记录，提供原始 `prompt_ids` 和 `output_ids` 等数据。

消息与工具定义通过 `deepcopy` 保存独立副本，后续改动原字典不会改写这里的候选；`turn` 在这句中没有复制，仍引用本轮同一个对象。`append` 只追加候选，不在这里筛选是否能复用，也不会当场拼接下一次输入。

本轮保存后，后续同一会话的 `_session_prompt_ids` 才会读取这个列表，按前面的条件逐项检查；全部不合格仍返回普通编码结果。与之相邻的 `manager.record_turn` 把消息和生成记录接入轨迹树，供后续整理样本；这里的列表服务于后续模型输入的准备。


**输出：**

```python
prompt_ids: list[int]  # 本函数返回的模型输入，随后交给 call_sglang_generate
```

| 情形 | 返回的 token ID 列表 |
| --- | --- |
| 没有合格候选；本例的 `s.prompt_prefixes` 为空 | `rendered`，即本次完整消息与工具定义的普通编码结果 |
| 存在通过全部检查的候选 | `turn.prompt_ids + turn.output_ids + rendered[end + 1:]` |

本例走第一条路径。第二条只有在历史候选与模板边界等检查全部通过时才发生。两条路径返回后，都由 `_run_turn:423` 将 `prompt_ids` 交给 `call_sglang_generate`。具体 token 数量与模板参数实验见下方验证记录。

<a id="session-render-calls"></a>

### 两处 _render_token_ids 各自做什么

| 调用位置 | 交给模板的消息 | `add_generation_prompt` | 结果用在哪里 |
| --- | --- | --- | --- |
| 103 行 | 当前全部 `messages` | `True`，使用默认值 | 得到 `rendered`：既是没有合格候选时的完整返回值，也提供接续时的新后缀 |
| 127–129 行 | 当前候选覆盖的 `messages[:depth]` | `False`，明确传入 | 得到 `anchor`：只用于检查历史前缀和定位切口，不直接作为最终返回值 |

两次调用都带上同一份 `tools` 和会话模板参数，并以 `tokenize=True` 得到 token ID。需要展开模板编码本身时，进入 [_render_token_ids 卡片](_render_token_ids.md#render-token-result-branches)，读完返回这里继续。

<a id="session-prompt-branches"></a>
<a id="session-history-purpose"></a>

<details>
<summary>源码细节：七步分支图、逐项检查与补充情境</summary>

### 分支图：一个候选失败，就继续检查下一个

这里的主要分支属于 `_session_prompt_ids`；`_render_token_ids` 是它调用的模板编码函数。图中的编号表示本函数的执行位置，行号均属于 `slime/agent/adapters/common.py`。

```text
① 编码全部消息 → rendered                         common.py:102–104
   _render_token_ids(..., add_generation_prompt=True)
                         ↓
② 按历史长度从长到短，取下一个 prefix              105–107
   ├─ 没有候选了 → return rendered                 136：普通编码结果
   └─ 取到一个候选
          ↓
③ 历史相符，而且生成记录可用于接续？               108–116
   ├─ 否 → continue，回到②检查下一个候选
   └─ 是
          ↓
④ 同样的可见历史，是否还对应另一份不同的 token？   120–126
   ├─ 是 → 有歧义；continue，回到②
   └─ 否
          ↓
⑤ 只编码候选前缀 → anchor                         127–131
   _render_token_ids(..., add_generation_prompt=False)
   anchor 是否等于 rendered 开头的同长部分？
   ├─ 否 → continue，回到②
   └─ 是
          ↓
⑥ 能找到切口，而且切口后只剩留白？                 132–134
   ├─ 否 → continue，回到②
   └─ 是
          ↓
⑦ return 旧输入 token + 旧输出 token + 新后缀      135：接续结果
   turn.prompt_ids + turn.output_ids + rendered[end + 1:]
```

**这些是同一候选必须依次通过的检查。** ③④通过后，还必须进入⑤计算 `anchor`，再通过⑤⑥的前缀与切口检查，才能到⑦拼接；不能因为消息匹配就直接跳到⑦。`anchor` 是对这个候选覆盖的消息临时编码得到的 token 列表，不是匹配失败后另外找来的备用历史。

**`continue` 与 `return` 要分开看：** ③—⑥检查失败，只放弃当前 `prefix`，从②继续取候选；第一次找到完全合格的候选就在⑦返回。只有②已经没有候选可取，才返回普通编码结果。初始列表为空，也直接走②的返回分支。

### 每项检查具体负责什么

| 图中位置 | 实际检查或操作 | 不满足时，为什么不能用这一份历史 |
| --- | --- | --- |
| ③ 历史对应 | `prefix.tools == tools`；`prefix.messages == messages[:depth]`；`depth < len(messages)` | 工具或历史变了，或者当前没有新增消息，这份记录不适合作为本次接续前缀 |
| ③ 生成记录可用 | `finish_reason == "stop"`；`output_ids` 非空；最后一个 ID 属于 `tokenizer.all_special_ids` | 生成未按 `stop` 结束，或缺少可用于定位边界的末尾 token，不能直接拼上新消息 |
| ④ 排除歧义 | 相同消息、相同工具若还对应不同的 `prompt_ids` 或 `output_ids`，跳过这一候选 | 可见回复一样，隐藏思考等原始 token 可能不同；仅凭当前消息不能选定其中一份 |
| ⑤ 模板上下文一致 | 将 `messages[:depth]` 单独编码为 `anchor`，比较 `rendered[:len(anchor)] == anchor` | 某些模板会根据后面的消息改变旧消息格式；单独编码的前缀不一定与完整编码的开头相同 |
| ⑥ 确认切口 | 在 `anchor` 中从后往前找 `turn.output_ids[-1]`；其后解码并去掉留白后必须为空 | 找不到同一标记，或标记后还有实际内容，就不能把这里当作旧输出与新内容的分界 |

例如，较长候选的历史不匹配，并不意味着整个请求只能普通编码：它会继续检查较短候选，较短候选仍可能通过全部检查并被采用。这对应图中的“③ → ②”，不是“③ → 返回”。

### 模板调用的补充说明

`prefix` 是会话里已经保存的一份历史记录；`anchor` 是当前候选通过前面检查后，调用 `_render_token_ids(messages[:depth], ...)` 新算出的 token 列表。后者用于验证前者能否在 token 层面接上，并不构成另一种备选拼接策略。

- 两次调用都带上同一份 `tools` 和会话模板参数，都以 `tokenize=True` 得到 token ID。
- `True` 请求模板准备下一条助手回复的开头；`False` 不额外请求这个开头，便于定位已经结束的历史。具体格式由 tokenizer 的模板决定。
- ①总是先执行；⑤只在当前候选通过③④后执行，可能随多个候选执行多次。确定切口后使用 `rendered[end + 1:]`，因为新后缀已包含在①的完整编码中。

需要展开模板编码本身时，进入 [_render_token_ids 卡片](_render_token_ids.md#render-token-result-branches)，读完返回①或⑤。

### 历史对不上时，本次消息仍然正常编码

这里比较的是 **CLI 本次请求带来的消息**与**同一会话已保存的消息历史**。当前这一轮模型还没有生成答案。本轮的 `_respond` 与 `manager.record_turn` 正常返回后，`_run_turn` 才会保存一份消息历史、工具定义和对应的原始输入／输出 token；`_session_prompt_ids` 读取这些材料。

只看“读取 README”的消息关系，暂时省略保持相同的系统消息和工具定义；A、B、C 各代表一条完整消息：

```text
已保存的消息历史：[A 用户要求读取 README，B 助手调用 read_file]
本次请求的消息：  [A 用户要求读取 README，B 助手调用 read_file，C 工具返回文件内容]
                  └───── 整段旧历史相同 ──────┘   └── 新内容 ──┘
```

- **能够对应，且其他检查也通过**：A、B 对应的历史部分使用保存过的原始 token，再接上 C 对应的新后缀。A、B 只保留一份，C 正常进入本轮输入。
- **所有候选都无法对应**：返回函数开头已经算好的 `rendered`，即本次全部消息与工具定义的普通编码结果。例如本次请求本来就带有 `[S 此前工作的摘要，D 接下来的问题]`，返回的就是 S、D 连同工具定义的编码；摘要必须已在请求里，本函数不会生成摘要，也不会额外执行工具。结果是供模型使用的 token ID 列表。

“对应”要求保存的整段消息历史与当前消息开头相同，源码检查为 `prefix.messages == messages[:depth]`；不是只要几句话相似、或任意部分重叠就算匹配。一个候选对不上，还会检查其他候选。

**为什么值得复用？** 已保存的原始输出 token 可能包含思考或特定的工具参数格式，而客户端传回的可见历史只保留了 B 这样的工具调用。利用可见消息确认“这是同一段历史”，才能接回当时真正的 token；找不到可靠对应时，就以本次请求提供的消息重新编码。这个选择决定的是历史部分的 token 来源，新增内容仍参与本轮输入。

</details>

## 我的直接表述（原话）

用户认可这两项解释并指定保存位置：

> 我觉得这二个解释比较清楚放在心智模型这里吧

已将连续检查与普通编码回退整理进上方第 3 项；记录本次清晰度反馈，具体边界检查仍按下方未知保留。

用户进一步选用前述完整解释及两张图，并明确两个层次的关系：

> 作为这里的理解可以吗？
> 心智模型是根据这句话生成的简单总结
> 如果不清楚就需要看这个

完整说明沿用先前助手解释，已保存在[详细理解](#session-prompt-understanding)；上方心智模型由它提炼。此处记录用户对说明与组织方式的选用，保留其早先的原话和具体未知。

<details>
<summary>此前讨论与修正（原文保留）</summary>

首次整理时，用户尚未直接复述本函数的职责或实现，只明确要求继续阅读它并核对版本变化；该要求记录在[本步讨论](../../../../../../04-flow.md#session-prompt-ids)，不记为已经理解。

2026-10-23，用户反馈当前卡片不足以解释分支，并提出用图说明：

> 我觉得这里的这个函数卡片还是缺了点东西
> 没有说明白这里的分支情况
> 也没有解释不同的分支具体大概做了什么？
> 是否适合画一个图呢？
> 我感觉这个render_token_id的部分还是比较复杂
> 有比较多的内容是可以做的

该反馈是阅读困难与呈现要求，不记作已经理解各项分支。

随后用户给出初步理解并追问：

> 我有点没有理解这里的意义
> 我的理解是
> 这里会保留一个历史消息？
> 然后如果返还的内容是和这里的历史消息重叠的才考虑加上去
> 如果不重叠的话会怎么样
> 我不是特别理解了？

助手校正：当前比较的是本次请求携带的历史，匹配用于选择历史 token 的来源；没有合格匹配时仍编码本次完整请求。这些校正在当时尚未得到用户确认。

接着用户提出“先匹配 prefix，失败后再找 anchor”的理解：

> 我有点不是特别理解了
> 我可以简单的理解为
> 这里做的事情是在对于session的prefixes部分做一系列的prefix检查
> 然后考虑一下是否满足继续使用前缀拼接？
>
> 如果最简单直接符合就拼接
>
> 如果不符合的话就需要找到可能的anchor来拼接？
> 这里是我对于这一部分的代码的理解中间具体的部分是不同的策略？
>
> 如果都找不到对饮的话
> 就变成当前输出的此前工作的摘要以及直接给出当前tool生成的结果来产出这里的 render过得代码？

助手澄清：prefix 检查与 anchor 检查是同一候选的连续步骤，所有检查通过后才拼接；回退直接返回预先计算的 `rendered`。前面的摘要只是请求内容的一个例子，本函数不生成摘要。上述澄清在当时尚待用户反馈；后续反馈见下。

</details>

本轮继续追问输入材料的保存来源：

> 那么再看一下这里的prompt_prefixes.append吧这里是不是之前没有出现过呢？

本次补充的是调用方保存候选与本函数读取候选的关系；原心智模型、用户指定的详细理解和既有未知保留。

## 尚不清楚

- 用户认可连续检查和普通编码回退的解释比较清楚；各个条件在具体数据下怎样通过或失败，尚未逐项确认。
- 用户是否已区分“消息历史”和“原始 token 历史”，以及为什么需要同时保留，尚待讨论。
- 各项回退检查怎样覆盖所有模型模板，以及历史被压缩后的轨迹如何导出，本轮没有完整展开；不能由本函数推断它会搜索、剪枝或合并轨迹树。
- 局部验证使用已下载的 tokenizer 与构造的旧输出，未验证真实 CLI、模型服务或并发请求的端到端行为。

<details>
<summary>来源、验证与完整例子</summary>

- 2026-10-23 最终源码核对：[核对范围与结果](../../../../../../04-flow.md#session-prompt-final-source-audit)。核心解释与 `18868a79` 一致，重新运行相关测试为 **9 passed、2 deselected**；本地 tokenizer 对照复算与保存数据一致。指定原文和图示未改，仅将其他说明中的历史保存时机限定到相关调用正常返回之后。
- 返回范围：卡片中的两条返回路径以模板编码等操作正常执行为前提。本函数没有捕获模板异常的分支，模板自身报错会向调用方传播，不属于“候选不合格后返回 rendered”。
- 阅读层次调整：[按用户确认方案展开主解释、收起补充材料](../../../../../../04-flow.md#confirmed-card-reading-layers)。本次只重排材料，沿用此前运行证据。
- 简短总结与详细理解的分层：[本次选用与整理](../../../../../../04-flow.md#session-model-and-understanding)。
- 心智模型收录：[用户认可两项解释并要求放入本栏](../../../../../../04-flow.md#accepted-session-prompt-model)。
- 连续检查澄清：[Step 1 · anchor 不是备用历史，回退不生成摘要](../../../../../../04-flow.md#anchor-is-a-sequential-check)。
- 复用意义澄清：[Step 1 · 比较对象与无法匹配时的处理](../../../../../../04-flow.md#session-history-purpose)；A、B、C 和 S、D 为消息关系示意，不是新增运行实验。
- 分支澄清：[Step 1 · 候选失败与最终回退](../../../../../../04-flow.md#session-prompt-branches)；本轮按固定源码逐项静态核对，沿用前次局部运行证据。
- 当前源码：[_session_prompt_ids 93–136 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L93-L136)；[Session / PromptPrefix 39–57 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L39-L57)；[取用 415–423 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L415-L423)；[保存 470–472 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L470-L472)。
- 旧版关系：[原先的直接调用 341–344 行](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L341-L344)。本次不是把旧函数改名，而是在原模板编码外增加会话历史检查。
- 2026-10-23 运行现有 `tests/test_agent/test_prompt_continuity.py` 的非 HTTP 测试：**9 passed，2 deselected**。覆盖思考与空白保留、历史或工具变化、压缩、未完成输出、缺少边界、同级分支和歧义回退。执行命令：`python -m pytest tests/test_agent/test_prompt_continuity.py -q -k 'not http'`；[固定版本测试源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/test_agent/test_prompt_continuity.py#L80-L150)。
- 本地 tokenizer 为 `Qwen/Qwen3.6-35B-A3B`，revision `995ad96eacd98c81ed38be0c5b274b04031597b0`，沿用 [decode 卡片中的下载来源](../../../../src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md)。直接调用当前 Slime 函数，未下载模型权重，未请求生成。
- [完整局部验证数据](../../../../../../references/session-prompt-ids-version-check-18868a79.json)保存构造的旧输出文本、各次参数、长度和返回后缀。完整主场景在无历史或默认模板边界不匹配时返回 337 个 token；只保留到工具结果时成功复用，返回 342 个；完整场景额外指定 `preserve_thinking=True` 时成功复用，返回 351 个。最后一项是明确改变模板参数的对照，**不是默认配置**。三种有历史的验证均确认本函数未修改 `Session`。
- 形成过程：[Step 1 · 新增的会话输入准备](../../../../../../04-flow.md#session-prompt-ids)；连贯讲解：[为何需要保留历史原始 token](../../../../../../../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#session-prompt-ids)。

### 本地 tokenizer 验证：无历史前缀的完整场景

以下保留前次对上方完整输入的局部执行结果：

**输出：**

```python
# prompt_ids 的类型仍是 list[int]，以下是本地 tokenizer 的实际局部结果
len(prompt_ids)     # 337
prompt_ids[:8]      # [248045, 8678, 198, 2, 13455, 271, 2523, 599]
```

本例没有保存过的前缀，因此输出等于普通 `_render_token_ids(...)` 的结果。即使请求里带有历史消息，也不意味着本地一定保存过对应的原始 token。返回 `_run_turn:423` 后，这份列表才交给 `call_sglang_generate`。

### 匹配成功后，返回值怎样组成

先观察**只有工具结果刚返回、尚未追加最后一条用户追问**的接续：输入改为 `translated[:-1]`，工具定义不变。验证中构造上轮记录：输入 277 个 token，输出 43 个 token；输出含有思考、读取文件的工具调用和结束标记。输出文本是教学构造，再由真实 tokenizer 编码，不冒充模型实际生成。

```python
# 若历史匹配与边界检查都通过，函数实际返回这一式：
prompt_ids = turn.prompt_ids + turn.output_ids + rendered[end + 1:]
# 本地接续示例：277 + 43 + 22 = 342 个 token
# 对照：只将当前消息重新套模板，会得到 332 个 token
```

- 前 320 个 token 来自已保存的上轮输入与输出，其中保留了那次输出中的思考。
- 后 22 个 token 来自当前渲染结果的后缀：工具结果，以及下一条助手回复的开头。
- 差别在于保留哪一份历史 token；这里仍没有生成本轮的新答案。

接回主场景：最后再加一条用户追问，会影响本地 Qwen 模板对旧助手消息的渲染。默认参数下，本例的前缀检查未通过，仍返回 337 个普通编码 token。这说明**保存过历史不等于一定复用**；模板参数与检查条件也影响结果。具体对照留在下方证据中。

</details>
