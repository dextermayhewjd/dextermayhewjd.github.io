# 05 · 任务链路：以 _run_turn 串起一次模型请求

> `_run_turn` 接住一份模型请求，组织输入、生成与解析，把回复交给 HTTP 层，把本轮消息和生成记录交给 manager，再保存后续请求可检查的前缀候选，完成本次请求。

[本步范围与阅读路线](01-scope.md#reading-path) · [步骤入口](README.md) · [函数记录](02-short-term-memory/overview.md) · [本次整理依据](04-flow.md#scope-map-and-task-flow-refresh)

**版本说明**：本页按 `18868a79` 的实际调用与数据交接整理。原 `2f231865` 总结及上游讲解已[完整保留](references/task-flow-at-2f231865.md)。阅读时先看哪里、何时回查，统一见 scope；本页总结程序怎样完成这次请求。

## 1. 本步在任务中的位置

前一步的[核心骨架](../step-000-coding-agent/01-scope.md)说明整次 Coding Agent 任务。本页沿其中一次模型请求，连接本步已读的函数。

```text
_generate 的第 4 项：await harness.run(...)              generate.py:287–294
└─ 外部 Claude Code CLI 运行期间
   └─ HTTP POST /v1/messages
      └─ AnthropicAdapter 注册的处理器                  anthropic.py:49
         └─ BaseAdapter._run_turn(request)              adapters/common.py:387
```

这里 CLI → Adapter 的连接经过 HTTP，由路由触发处理器；Harness 没有直接调用 `_run_turn`。

- **起点：** Adapter 已监听并注册路由，请求交给 `_run_turn`；会话、tokenizer 和 SGLang 地址可用。
- **场景：** 沿用 Claude Code / Anthropic，以非流式响应为主，保留流式分支的发送时机差异。
- **终点：** 正常路径返回 HTTP 响应对象，本轮轨迹与前缀候选已保存，当前请求的在途登记已移除。CLI 得到响应后继续任务，Harness 仍等待它整体退出。

## 2. 已读部分怎样完成交接

<a id="run-turn-flow"></a>

下面按**实际执行顺序与嵌套关系**展开，行号默认属于 `slime/agent/adapters/common.py`。这是正常路径的教学裁剪：会话门禁、日志、调试回调与异常细节省略；启用追踪时保留两层 `trace_span`，未启用时相应位置使用 `nullcontext`，业务交接不变。

```text
BaseAdapter._run_turn(request)                                     387
│
├─ request.json()，预处理并定位会话                                394–407
│  → body、sid、Session；取得 tok，登记当前 task
│
├─ trace_span：agent_model_turn（启用追踪时）                       412–423
│  ├─ trace_span：agent_tokenize                                   414–421
│  │  ├─ self._translate(body)                                     415
│  │  │  → translated（消息历史）＋ tools_schema（工具定义）
│  │  └─ _session_prompt_ids(...)                                  416–421
│  │     ├─ _render_token_ids → apply_chat_template                 73–105
│  │     │  → 先取得本次全部消息与工具定义的普通编码 rendered
│  │     └─ 候选合格则拼接；全部不合格才返回 rendered               106–136
│  │        → prompt_ids：本次交给模型的 token ID 列表
│  └─ await call_sglang_generate(...)                              423
│     → HTTP 请求 SGLang /generate，整理结果为 turn
│       保存输入/输出 token、生成 token 的 logprob 和结束原因等
│
├─ tok.decode(turn.output_ids, ...)                                425
│  → raw_output：生成的原始文本，保留特殊标记
├─ parse_model_output(raw_output, ...)                             426–431
│  → parsed：思考、正文、工具调用描述与格式标记
├─ self._build_reply(parsed, ...)                                  432
│  → reply：wire 给协议响应，manager_message 给轨迹记录
├─ 补 turn.ill_formed；计算 in_tok / out_tok；确定 stream           433–436
│
├─ await self._respond(..., reply, in_tok, out_tok, stream)         442
│  ├─ 普通：_render_response → web.json_response                    anthropic.py:75
│  └─ 流式：await _render_stream                                   anthropic.py:73–74
│     → response：正常返回后，回到 _run_turn 继续保存数据
├─ self.manager.record_turn(...)                                  463–469
│  → 把 translated、reply.manager_message、turn 接入会话树
│    返回 None，结果保存在 manager 内部
├─ s.prompt_prefixes.append(PromptPrefix(...))                     470–472
│  → 保存消息、工具定义与 turn，供后续同一会话请求检查
└─ return response；真正返回前执行 finally                         473–475
   → 移除当前 task 的在途登记，把 response 交回 aiohttp
```

两层追踪都在 `tok.decode` 之前结束；输入准备的追踪先结束，才调用模型生成。正常路径中，`_respond` 和 `record_turn` 之间还会经过已折叠的调试回调。

从图中回查单函数时，使用对应的卡片：

- 输入到生成：[_translate](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md)、[_session_prompt_ids](02-short-term-memory/functions/slime/agent/adapters/common.py/_session_prompt_ids.md)、[call_sglang_generate](02-short-term-memory/functions/slime/agent/adapters/common.py/call_sglang_generate.md)。追踪包装见 [trace_span](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md)；模板编码从 `_session_prompt_ids` 卡片继续回查。
- 生成到回复材料：[decode](02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md)、[parse_model_output](02-short-term-memory/functions/slime/agent/parsing.py/parse_model_output.md)、[_build_reply](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md)。这里只产生工具调用描述，实际执行由 CLI 组织。
- 对外交付与内部保存：[_respond](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._respond.md)、[record_turn](02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md)、[PromptPrefix](02-short-term-memory/classes/slime/agent/adapters/common.py/PromptPrefix.md)。返回父函数后继续下一处交接；阅读时的回看次序仍以 [scope](01-scope.md#reading-path) 为准。

## 3. 本步结果的含义与去向

<a id="response-and-recording"></a>

### 同一轮结果交给谁

沿用 [_run_turn 卡片](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#本场景的输入与输出)的构造场景：本次生成“你好。”、无工具调用、普通响应。会话最初没有前缀候选，`s.trace = None`；具体 token ID、logprob 与计数没有实际运行值。

| 结果 | 来自什么 | 谁接走、用来做什么 |
| --- | --- | --- |
| `response` | `_respond` 读取 `reply.wire`，加上模型名、`in_tok` / `out_tok` 等；本例正文包含文本“你好。”与 `stop_reason = "end_turn"` | 返回给 aiohttp，再发给 CLI，供它继续任务 |
| 本轮轨迹 | `record_turn` 接到 `translated`、`reply.manager_message` 和 `turn`；本例内部回复为 `{"role": "assistant", "content": "你好。"}` | manager 保存到该 `sid` 的消息树，留给之后的轨迹导出 |
| 一份 `PromptPrefix` | 消息历史加本轮回复、工具定义分别深拷贝，`turn` 保留引用 | 追加到 `s.prompt_prefixes`，供后续同一会话请求的 `_session_prompt_ids` 检查 |
| 阶段事件（启用追踪时） | 两层 `trace_span` 记录被包围阶段；本例未启用 | 进入追踪记录，和 manager 中用于导出的生成轨迹分开 |

- **HTTP 响应与轨迹保存分别使用自己的材料。** `reply.wire` 由具体 Adapter 读取；`reply.manager_message` 是内部 assistant 消息，`turn` 另存 token 与 logprob 等生成信息。manager 不保存 `response` 对象。
- **先调用 `_respond`，再记录，不等于已确认客户端收到。** 普通分支先构造响应对象，在 handler 返回后由 aiohttp 发送；流式分支在 `_respond` 内准备连接并写出事件，然后返回。当前记录不是客户端消费回复的确认凭证。
- **前缀候选服务于后续请求。** 本次追加后继续返回；后续请求仍要检查历史匹配、生成状态、歧义与拼接位置。没有合格候选就使用当前请求的普通编码，不会在本次末尾自动重跑输入准备。

<a id="adapter-dispatch"></a>

### 不同协议怎样接入共同处理

当前 `_generate` 先按样本选择 agent，再取得对应的 Harness 与 Adapter 端点。`sample.metadata["agent"]` 可覆盖 `SWE_AGENT` 的默认选择；本步只核对入口配对，不展开端点初始化。

| 当前选择 | Harness | Adapter 与请求入口 |
| --- | --- | --- |
| `claude_code`（默认） | `ClaudeCodeHarness` | `AnthropicAdapter`，`POST /v1/messages` |
| `codex` | `CodexHarness` | `ResponsesAdapter`，`POST /v1/responses` |

两者都复用 `BaseAdapter._run_turn`：`ResponsesAdapter` 经 `OpenAIAdapter` 继承该流程，并实现自己的转换、回复组装与响应。本场景中 `self` 始终是 `AnthropicAdapter`，三个 `self._...` 调用使用它的具体实现。共同流程接收消息、工具定义、`TurnRecord` 和 `Reply`，各协议负责自己的格式；一次请求不会在两个 Adapter 之间切换。

旧版总结中的“Codex → `OpenAIAdapter` → `/v1/chat/completions`”属于旧版本配对，已随原文归档。新版 Responses 协议内部处理仍未在本步逐段展开。

## 4. 本步的收束与后续衔接

<a id="step-boundary"></a>
<a id="inflight-cleanup"></a>

本步连接的是：一份模型请求如何经过输入整理、模型生成、结果解析，交出协议响应，留下本轮轨迹和前缀候选。正常返回前清理当前请求的在途登记，已保存的数据继续保留；登记与移除的细节见 [_run_turn 的局部说明](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#inflight-cleanup)。

- CLI 怎样执行工具、组织下一次请求，属于外部工具循环；一次 `_run_turn` 完成不代表 CLI 已退出。
- 完整会话关闭、轨迹导出与训练样本组装、SGLang 内部、Trace 传播与导出，继续留在各自的阅读范围；函数卡片中的未知不会因本页整理而消失。
- 回到外层 `_generate`，只有 `harness.run` 等待的 CLI 整体结束后，才进入 [Step 002 的运行统计与补丁提取](../step-002-agent-results/01-scope.md)。这是一处后续交接，当前阅读进度仍以[唯一路线](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准。

<details>
<summary>旧版上游讲解与原链接入口</summary>

以下入口保留此前链接，打开后到完整旧稿查看；均属于 `2f231865` 的历史讲解，不能据此推定上游实现已按新版校准。

<a id="call-sites-and-implementations"></a>
<a id="source-jump-map"></a>

- [文件、调用行、具体实现与返回位置](references/task-flow-at-2f231865.md#source-jump-map)。

<a id="http-round-trip"></a>

- [为什么有 HTTP 服务、请求和响应怎样往返](references/task-flow-at-2f231865.md#http-round-trip)。

<a id="harness-to-adapter"></a>
<a id="run-execution-order"></a>

- [从 Harness.run 开始的旧版逐句讲解](references/task-flow-at-2f231865.md#run-execution-order)。

<a id="http-request-order"></a>

- [CLI 发起请求后的旧版处理顺序](references/task-flow-at-2f231865.md#http-request-order)。

</details>

<details>
<summary>源码、形成依据与验证范围</summary>

- 本地源码：`/home/hongshi/projects/slime`；固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。
- 共同编排：[_run_turn：387–475](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L387-L475)。前缀类型、模板编码与候选检查：[38–136](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L38-L136)。模型请求：[524–700](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L524-L700)。
- 解析：[parsing.py：25–56](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/parsing.py#L25-L56)。本场景的路由、转换与回复：[anthropic.py：39–75](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/anthropic.py#L39-L75)。轨迹写入：[trajectory.py：381–403](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/trajectory.py#L381-L403)。
- 配对选择：[generate.py：50–64](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L50-L64)、[端点创建：184–222](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L184-L222)、[本次选择：254–260](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L254-L260)。Responses 入口：[responses.py：171–195](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/responses.py#L171-L195)。
- 外层等待与下一交接：[generate.py：283–298](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L283-L298)。
- 本页由 LLM 汇总已发生的阅读；[原收束讨论](04-flow.md#run-turn-task-flow-closure)和[此次格式与版本整理](04-flow.md#scope-map-and-task-flow-refresh)保存用户反馈与修正依据。未新增用户掌握结论。
- 本次只做静态源码、文档与链接核对；例子沿用函数卡片的教学构造，没有新增真实 CLI、HTTP、SGLang 或沙箱运行。辅助库函数的既有核对见[版本记录](references/auxiliary-functions-version-check-2026-10-23.md)。

</details>
