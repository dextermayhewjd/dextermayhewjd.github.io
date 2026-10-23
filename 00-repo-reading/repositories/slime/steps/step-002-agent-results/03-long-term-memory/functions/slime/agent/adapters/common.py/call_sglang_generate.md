# call_sglang_generate

- 源码定位：[slime/agent/adapters/common.py:524](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L524-L700)，由助手核对。
- 首次接触：Step 1，承接 `_render_token_ids`。
- 最近认识更新：2026-10-23，用户尝试从“按 SGLang 格式处理输入、输出及对应概率”概括职责，并询问与现有心智模型的区别及当前阅读边界；本轮澄清尚待反馈。
- 此前认识更新：2026-10-21，用户说明输入是编号列表、经 HTTP 请求模型，要求逐步拆解响应整理；尚未确认理解 `TurnRecord` 的构造。本轮进一步询问实际生成 token 的概率与全词表概率分布的区别。在助手澄清后，用户反馈“大概理解了”，并提出下一处阅读 `tok.decode`。

- 本轮源码校准：2026-10-23，对照 `2f231865 → 18868a79`，保留原正常场景，补充中断续生成、校验与返回字段；这是助手核对，不代表用户已理解新增机制。[旧版完整卡片](../../../../../../../step-001-harness-to-adapter/references/call-sglang-generate-at-2f231865.md)保留原证据。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据使用场景、调用代码和本页的输入输出整理，作为理解参考。

1. **使用场合**：`_run_turn` 已取得 `_session_prompt_ids` 返回的 `prompt_ids`，需要向模型服务请求本轮生成，并取得结果供后续解码与记录。

2. **具体内容**：将 `prompt_ids` 放入请求的 `input_ids`，将会话默认值、请求参数和剩余上下文预算整理成 `sampling_params`，通过 HTTP POST 请求 SGLang。每次响应先校验，再把生成编号、对应 logprob 和附加资料累计到 `captured`；符合中断续生成条件时继续请求，收束时连同原输入编号构成一份 `TurnRecord`。下面仍用同一组数值展示正常路径，再补充续生成分支。

3. **建议构建的心智模型**：

   > - **请求生成**：按 SGLang 的接口格式，发送已有的输入 token 和生成设置，请模型生成。
   > - **接收结果**：读取并校验新生成的 token 及其 logprob，取得结束原因。
   > - **形成记录**：把原输入和本轮生成结果整理成本地 `TurnRecord`，交回调用方。

   当前先建立这层职责模型：对外按 SGLang 接口收发，对内使用 Slime 的 `TurnRecord`。原输入来自调用者，`output_log_probs` 对应新生成的 token。一轮可能包含多次请求；累计、续生成、预算及重放资料的内部处理保留在下方，按需再读。

4. **调用代码**（[源码](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L423)）：

   ```python
   turn = await call_sglang_generate(prompt_ids, s, body, adapter=self, session_id=sid)
   ```

## 本场景的输入与输出

仍沿用[上一步](_session_prompt_ids.md)的场景：读 README 后请模型继续概括。为看清本函数里的数据变化，本例**假定**上一步返回 `[101, 102, 103]`，模型服务返回 `[701, 702]`。这些是教学占位编号，不是实际 tokenizer 对 README 场景的编码，也不指定它们解码成哪句话。下面的正常返回路径及续生成例子已用当前原函数配合本地 HTTP 测试服务核对；没有运行真实模型。

**① 输入：调用这个函数时带进来什么。**

```python
prompt_ids = [101, 102, 103]  # 假定为 _session_prompt_ids 的输出
s = Session(
    sampling_defaults={"max_new_tokens": 8, "temperature": 0.7},
    max_context_tokens=6,
)
body = {  # 当前请求的生成参数节选；原请求还保留上游的 system/messages/tools
    "max_tokens": 5,
    "temperature": 0.2,
}
sid = "demo-session"

# self 沿用当前 AnthropicAdapter，列出影响本例请求的配置；日志配置省略。
self.sglang_url = "http://127.0.0.1:30000"  # 示例地址，验证时替换为本地 HTTP 测试服务地址
self.max_token_keys = ("max_tokens",)
self.stop_keys = ("stop_sequences",)
self.rollout_args = SimpleNamespace(partial_rollout=False)  # 本例的最小配置对象
```

调用处的 `s / self / sid` 分别对应函数内的 `session / adapter / session_id`。

本例未开启 score centering、路由重放或推测解码，也未另设服务端上下文上限；这些缺省项采用源码的默认分支。`SimpleNamespace` 仅用于构造这组教学配置。

本例的参数变化可以直接算出来：

```text
最多生成多少：会话默认 8，当前请求 5 → 先取 min(8, 5) = 5
上下文还剩多少：上限 6，输入有 3 个 token → 剩余 3
最终生成上限：min(5, 3) = 3
温度：会话默认 0.7，被当前请求的 0.2 覆盖
```

**② 函数内部发出的请求：这些输入怎样变成 HTTP 数据。**

```text
POST http://127.0.0.1:30000/generate
X-SMG-Routing-Key: demo-session
```

请求 JSON：

```json
{
  "rid": "00000000000000000000000000000001",
  "input_ids": [101, 102, 103],
  "sampling_params": {
    "skip_special_tokens": false,
    "spaces_between_special_tokens": false,
    "no_stop_trim": true,
    "max_new_tokens": 3,
    "temperature": 0.2
  },
  "return_logprob": true
}
```

这里的 `rid` 在真实代码中由 `uuid.uuid4().hex` 生成，保存本例记录时将随机值规范为固定序号，便于对照。`input_ids` 原样接住输入编号；`sampling_params` 是刚才算出的设置；`return_logprob: true` 要求响应带回生成 token 的 logprob。客户端另设 `ClientTimeout(total=None, sock_read=900)`，这项等待设置不放进请求 JSON。

**③ 模拟服务响应：函数拿到了什么。**

下面是替身返回的 JSON，采用仓库测试服务的字段形状；只展示本函数读取的字段。`data = await r.json(content_type=None)` 接住它：

```json
{
  "meta_info": {
    "output_token_logprobs": [
      [-0.2, 701],
      [-0.5, 702]
    ],
    "finish_reason": {
      "type": "stop"
    }
  }
}
```

每一项的第一个值是 logprob，第二个值是 token 编号。以下节选只展示取值；新版还会校验字段存在、数量、编号和数值合法性，检查通过后才累计：

```python
meta = data.get("meta_info") or {}
output_token_logprobs = meta.get("output_token_logprobs") or []
output_ids = [x[1] for x in output_token_logprobs]             # [701, 702]
output_log_probs = [float(x[0]) for x in output_token_logprobs] # [-0.2, -0.5]
finish = (meta.get("finish_reason") or {}).get("type", "stop") or "stop"  # "stop"
```

于是 `701` 对应 `-0.2`，`702` 对应 `-0.5`；取编号与取 logprob 时都保留同一顺序。

**这里记录的是实际生成 token 的对数概率（logprob）。** 第一个生成位置输出 `701`，保存它的 `-0.2`；第二个生成位置输出 `702`，保存它的 `-0.5`。这两个数属于前后两个生成位置，不是同一个位置的两个候选 token 的概率。`output_log_probs` 不保存每个生成位置整个词表的概率分布；`-0.2` 和 `-0.5` 也不是普通概率值。新版可选的 `replay` 能另外携带 top-p 候选编号、相关概率或 top-k 概率等资料，不能再把“只保存生成 token 的 logprob”当成整个 `TurnRecord` 的全部内容。

**④ 输出：本函数返回什么对象。**

```python
TurnRecord(
    prompt_ids=[101, 102, 103],  # 原输入编号保留下来
    output_ids=[701, 702],      # 从响应中提取的新生成编号
    finish_reason="stop",
    output_log_probs=[-0.2, -0.5],
    ill_formed=False,          # TurnRecord 定义中的默认值
    replay=None,              # 本例没有请求或返回训练重放资料
    weight_versions=[],       # 本例响应没有 weight_version
    spec_info=Sample.SpecInfo(),
    prefix_cache_info=Sample.PrefixCacheInfo(),
)
```

调用处的 `turn` 接住这个对象。虽然允许最多生成 3 个 token，本次模拟响应在生成 2 个后以 `stop` 结束；上限并不要求一定生成满。后续 `_run_turn` 使用 `turn.output_ids` 解码，`turn.prompt_ids` 则保留这一轮原本送入模型的内容。

本例两个统计对象的字段均为 `0`：响应未提供缓存统计，配置也未开启推测解码。这是此处教学响应的结果，不代表真实服务的统计值总是零。

<a id="generation-continuation"></a>

**⑤ 新增分支：中断后怎样继续同一轮。**

`captured = Sample(tokens=list(prompt_ids))` 是本次函数调用的临时累计容器，最初只有原输入，`response_length=0`。它与 `_session_prompt_ids` 读取的跨轮历史用途不同；最终返回的仍是 `TurnRecord`。

```text
发送 /generate 请求
    ↓
校验返回的数据 → 追加到 captured → 查看结束原因
    ├─ 不是 abort → 结束累计，打包 TurnRecord
    └─ 是 abort
         ├─ 未开启 partial_rollout → 打包，保留 abort
         └─ 已开启 partial_rollout
              ├─ 本轮额度已用完 → 改为 length，打包
              └─ 还有额度 → 用“原输入 + 已生成部分”再发请求
                            只申请剩余额度，每次生成新的 rid
```

保持上述输入与总额度 `3`，只把 `partial_rollout` 改为 `True`，并让测试服务分两次返回：

| 交接 | 输入或返回的数据 | 本地累计结果 |
| --- | --- | --- |
| 第一次请求 | `input_ids=[101,102,103]`，最多生成 `3` 个 | 初始 `captured.tokens=[101,102,103]` |
| 第一次返回 | `[701]`，logprob `[-0.2]`，结束原因 `abort` | `captured.tokens=[101,102,103,701]`，已生成 `1` 个 |
| 第二次请求 | `input_ids=[101,102,103,701]`，最多再生成 `2` 个 | 原输入和已生成部分一起作为续生成条件 |
| 第二次返回 | `[702]`，logprob `[-0.5]`，结束原因 `stop` | 累计输出 `[701,702]`，最终返回与上面的正常例子相同的 `TurnRecord` |

这里的 `abort` 是有效响应体内的结束原因。HTTP 错误或响应校验失败会抛出异常，不会按这个分支自动重试。若有效上下文已耗尽，函数在发请求前直接返回空输出、结束原因 `length`。

<a id="generation-version-changes"></a>

<details>
<summary>其他版本变化与源码定位</summary>

| 位置 | 旧版 → 新版 |
| --- | --- |
| `537–542`：采样与附加请求 | 仍合并会话默认值和请求参数；按 top-p、score centering 和路由重放设置，请求相应候选、概率或专家路由资料 |
| `544–568`：上下文预算 | 从会话上限扩展为同时考虑服务端上限；`EAGLE / EAGLE3 / NEXTN` 分支先为草稿 token 预留服务端空间 |
| `630–660`：响应检查 | 必须有 `output_token_logprobs`，并核对返回数量、可选的 `output_ids`、数值和本轮剩余额度；已请求的重放资料也不能缺失 |
| `661–677`：累计与继续 | 用 `append_response_tokens` 累积数据；只有上述中断条件成立才继续，空输出的中断另等待 `0.1` 秒 |
| `678–685`：取消与通信错误 | 仍清理上游请求；现在按当前那次请求的 `rid` 调用 `_abort_sglang_request`，然后继续抛出异常 |
| `687–700`：返回字段 | 保留原有五项，增加 `replay`、`weight_versions`、`spec_info`、`prefix_cache_info` |

`trace_span` 包住每次模型请求及空中断后的等待；它按已确认的阅读顺序另行展开。`append_response_tokens` 内部的重放数组拼接、专家路由形状和统计规则，本页只标明交接，尚未逐项带读。

</details>

需要继续细读时，可从 `574–588` 的 **`captured → payload`** 开始：看清最初放入什么、每次发出什么。再接 `609–663` 的请求与追加、`664–677` 的继续条件、`687–700` 的最终切片。`537–568` 的配置和额度先保留上面的输入输出关系，遇到相应疑问再下钻。

## 我的直接表述（原话）

本轮对输入与请求的理解，以及需要继续拆解的部分：

> 这里prompt id 我理解为就是一串数字
> 通过http post 发送给这里的sglang让模型生成答案
> 这里把数据整理成为turnrecord 什么的我觉得需要非常仔细的一点点拆解一下？
> 我觉得这里的call sglang generate还是非常复杂

随后明确反馈，单个字段的解释仍不能消除整体黑盒感：

> 这里的call sglang我完全就不是特别这里怎么就变成了这个样子完全像是一个黑盒子
> 我需要怎么拆解这里的call sglang呢？
> 感觉当前的心智模型在拆解比较不求甚解的函数的时候是没有问题的
> 但是碰到这种函数的时候我其实不知道内部具体做了什么这件事情

本轮对记录范围和呈现方式的要求（不作为源码理解结论）：

> 或者说如果这里的call sglang这里的输入和输出能够稍微详细一点不只是单纯的中文是否会好很多？
> 你现在记住我现在要求的都是你修改本地的repo reading的中short term 版本的function
> 这里的心智模型要怎么处理这件事情
> 而不是在别的地方进行修改

本轮对记录范围的核对：

> 也就是说最后这里的turn record 并不会记录每一个token在生成过程中的在词表中每一个token的概率 但是会记录生成的token的概率？

在上述记录范围得到澄清后，用户反馈并提出下一处阅读候选；这不等于确认已理解整个生成函数：

> 好的我大概理解了
> 那么接下来是是否应该考虑的是这里的tok.decode了呢？

本轮重新校准时，用户指定：

> 好的那么我们接下去继续看吧 下一个应该看什么呢？ 看call sglang generate 这里的部分有变化吗？

这是本轮阅读范围的确认，尚未新增对续生成或重放机制的个人理解表述。

随后尝试概括整个函数的职责，并询问当前应读到多深：

> 这里可以简单理解为
> 是按照sgalng的内容格式来 输出和记录这里的input和output以及对一哦能够的概率内容对吗？
> 和这个心智模型有什么区别吗？
> 暂时应该不考虑别的内容对吧

本轮助手将“按 SGLang 接口请求生成”与“整理为本地 TurnRecord”区分；上述表述记录为待核对的职责概括，不记为已掌握所有内部机制。

## 尚不清楚

- 函数从入口到返回的完整内部过程仍有黑盒感；此前的 `output_ids` 局部说明不能视为已理解整体。本页现用同一组具体输入、请求、响应和返回对象连接这些变化，是否消除黑盒感仍待反馈。
- logprob 的数值含义，以及结束原因怎样提取。
- 采样参数、上下文预算、请求配置与取消清理的具体处理。
- 真实模型下的输入编号、生成编号及其解码文本。
- 新版 `captured` 的累计、`abort` 续生成条件，以及重放字段在训练侧怎样使用，尚待按问题逐段理解。

<details>
<summary>来源、验证与完整例子</summary>

- 当前源码绑定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；调用处为 [common.py:423](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L423)，函数体为 [524–700](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L524-L700)。采样合并为 `498–521`，局部取值代码省略了分散在 `630–660` 的校验。
- 返回字段见 [trajectory.py:25–54](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L25-L54)；累计入口见 [Sample.append_response_tokens](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L277-L397)。`TurnRecord` 的旧文档字符串仍写“一次 /generate snapshot”，本页依照当前调用循环和实际返回代码说明“一轮可含多次请求”。
- [旧版完整卡片](../../../../../../../step-001-harness-to-adapter/references/call-sglang-generate-at-2f231865.md)保留 `2f231865` 的正常请求例子、个人原话及当时的验证方式；没有将旧实验改标为新版本。
- **本轮实际验证**：Python 3.12.3 导入当前原函数，用本地 `aiohttp` HTTP 测试服务验证正常 `stop`、`abort → stop` 续生成、未开启续生成、额度耗尽、上下文耗尽五个场景。结果见 [输入请求与返回 JSON](../../../../../../../step-001-harness-to-adapter/references/call-sglang-generate-version-check-18868a79.json)；保存时仅把随机 `rid` 规范为固定序号，没有调用真实模型、CLI 或 tokenizer 编码。
- 当前仓库 `test_token_contract.py` 中 `model_wire / generation_budget` 共 **14 项通过，6 项未选取**，覆盖 token/logprob 检查与推测解码的预算预留。另一个 `test_sampler_replay.py` 在收集时因本地缺少 `wandb` 失败，未运行整个重放测试套件；上面的五个场景是另行运行的局部核对，不替代该套件。
- 当前职责模型与阅读边界：[Step 1 · 先建立请求与记录模型](../../../../../../../step-001-harness-to-adapter/04-flow.md#call-sglang-responsibility-model)。
- 本轮问题与校准：[Step 1 · 生成函数版本变化](../../../../../../../step-001-harness-to-adapter/04-flow.md#call-sglang-version-calibration)。
- 既有扩展材料仅供按需回查：[响应字段例子](../../../../../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#call-sglang-output-ids)、[内部执行地图](../../../../../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#call-sglang-internal-flow)。本页的输入输出与模型可以独立阅读。
- 本轮纠正：[Step 1 · 函数内部仍是黑盒](../../../../../../../step-001-harness-to-adapter/04-flow.md#call-sglang-internal-flow)。
- 形成过程：[Step 1 · 逐步拆解返回记录](../../../../../../../step-001-harness-to-adapter/04-flow.md#call-sglang-output-ids)。此前的[阅读入口建议](../../../../../../../step-001-harness-to-adapter/04-flow.md#call-sglang-reading-proposal)只用于定位，不算已读懂内部实现。

</details>
