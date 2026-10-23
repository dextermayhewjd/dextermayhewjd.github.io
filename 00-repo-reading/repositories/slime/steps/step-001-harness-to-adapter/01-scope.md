# 01 · 阅读范围：沿 _run_turn 读清一次模型请求

[本步入口](README.md) · [Step 0 核心骨架](../step-000-coding-agent/01-scope.md) · [前序函数记忆](03-long-term-memory/overview.md) · [旧版 scope](references/scope-at-2f231865.md)

**版本说明**：本页骨架与行号按 `18868a79` 校准；`02` 的 `_run_turn`、`_translate` 共同记录与 Anthropic 引用入口、`_render_token_ids`、`call_sglang_generate`、`parse_model_output`、`_build_reply`、`_respond`、`TrajectoryManager.record_turn` 已校准，并新增 `_session_prompt_ids`、`trace_span` 卡片；[task flow](05-task-flow.md)已按同版源码更新，[原总结](references/task-flow-at-2f231865.md)单独保留。其余卡片保留各自标注的版本证据，不能把旧卡正文直接当作新版实现。[本次变化对照](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#run-turn-version-18868a79)单独列出需要重新阅读的关系。

## 1. 阅读目标

沿用理解 Coding Agent 的整体目标。本步沿 `BaseAdapter._run_turn`，读清一份模型请求怎样变成模型输入，再怎样生成回复、组织 HTTP 响应并记录轨迹。已有 Claude Code / Anthropic 分支作为具体场景；Harness 到 Adapter 的连接保留为进入本步的来路。

## 2. 指挥官函数与本步入口：`generate / _generate` → `BaseAdapter._run_turn`

整体入口沿用 Step 0 的 `generate`，实际业务编排在 `_generate`；本步从第 4 项运行中的 CLI 请求模型这一条路径，定位到局部编排函数 `_run_turn`。它串联一次请求的转换、编码、生成、解析、响应与记录，适合从头到尾逐段读。

外层调用位于 `examples/coding_agent_rl/generate.py:287–294`；HTTP 路由在 `slime/agent/adapters/anthropic.py:49` 绑定到 `self._run_turn`，实际执行体是 [slime/agent/adapters/common.py:387–475](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L387-L475)。本场景的 `self` 是 `AnthropicAdapter`，共同流程调用它的协议钩子。

可用 [_run_turn 函数卡片](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)建立新版输入输出与内部处理模型；下方导航按本轮观察顺序定位，函数卡片内部按源码实际执行顺序组织。

源码版本：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。进入时只需知道：CLI 已运行、Adapter 已监听并注册路由、tokenizer 与模型服务地址已配置、请求可关联到一个会话。创建这些条件的内部实现可从[旧版上游链路](references/task-flow-at-2f231865.md#http-round-trip)唤起职责，具体新版实现随对应步骤校准。

## 3. 给出真正干活的核心骨架

### 3.1 继承 Step 0：保留七项核心骨架

下面原样继承 [Step 0 的核心骨架](../step-000-coding-agent/01-scope.md)，用于定位本步。**当前只展开第 4 项，其余各项保留整体位置。**

这是 `evaluation=False` 正常路径的教学裁剪，保留函数名、执行顺序与返回值，调用参数通常用 `...` 省略，`git_diff` 保留本次校准涉及的 `baseline`。配置、检查、执行追踪、日志、异常、附加元数据和最终清理暂时折叠；这不是可直接运行的完整代码。

```python
# examples/coding_agent_rl/generate.py · _generate
adapter.open_session(...)                              # 1. 登记本次会话；Step 5
async with boot_agent_sandbox(...) as sb:                # 2. 启动执行沙箱；Step 6
    baseline = await swe.prepare_workspace(...)         # 3. 准备工作区并取得初始 Git 树；Step 7
    agent_exit_code = await harness.run(...)             # 4. 运行 CLI 并等待结束；Step 8
    # 等待期间：CLI --HTTP--> Step 9 接收与路由 --> Step 1 模型处理与回复
    agent_metrics = await harness.collect_metrics(...) # Step 2：读取运行统计，供后续标记截断等状态
    diff_text = await swe.git_diff(sb, ..., baseline)     # 5. 相对初始状态取得本次改动；Step 2

reward, applied_cleanly = await swe.run_evaluation(...)  # 6. 独立评测；Step 3
samples = await adapter.finish_session(...)              # 7. 导出本次会话的样本；Step 4
...  # 附加结果与截断状态；最终还需会话清理
return samples
```

<a id="step-1-branch"></a>

### 3.2 从第 4 项找到本步：Harness → CLI → Adapter

下面是面包屑导航，HTTP 箭头表示跨进程请求；不是 Harness 对 `_run_turn` 的直接函数调用。`harness/`、`adapters/` 路径均相对于 `slime/agent/`。

```text
_generate 的第 4 项：await harness.run(...)           # examples/coding_agent_rl/generate.py:287–294
└─ BaseHarness.run 启动并等待外部 CLI                  # harness/common.py:81
   └─ CLI 运行期间 ── HTTP POST /v1/messages ──→ Adapter
      └─ 路由绑定 self._run_turn                      # adapters/anthropic.py:49
         └─ BaseAdapter._run_turn(request)            # adapters/common.py:387，本步逐段读
```

**回到核心骨架：** 一次 HTTP 响应先回到 CLI；只有 CLI 整体退出，第 4 项才取得 `agent_exit_code`，随后读取 `collect_metrics`，再进入第 5 项 `swe.git_diff(...)`。

<a id="run-turn-normal-path"></a>

### 3.3 `_run_turn` 的正常处理顺序

以下是教学裁剪：保留真实函数名与顺序；参数通常用 `...` 省略，前置门禁、计时、调试回调和异常处理暂时折叠。`_translate` 保留 `body`，便于接回已有输入输出记录。本次为看清追踪与业务的关系，保留两层 `trace_span` 的阶段名与包围范围；追踪目标用 `...` 代指，省略目标绑定以及未启用追踪时的 `nullcontext` 分支。

```python
body = await request.json()                              # 1. 读取请求
self._preprocess_body(body)
sid = self._session_id(request, body)
...  # 检查会话，取得 Session，登记当前请求
try:
    with trace_span(..., "agent_model_turn", record_error=False):  # 追踪输入处理与模型生成
        with trace_span(..., "agent_tokenize", record_error=False):  # 其中的转换与编码阶段
            translated, tools_schema = self._translate(body)  # 2. 转换消息与工具定义
            prompt_ids = _session_prompt_ids(...)             # 3. 组织模型输入，可复用历史原始 token
        turn = await call_sglang_generate(...)                # 4. 获取本轮生成记录
    raw_output = tok.decode(...) if turn.output_ids else ""
    parsed = parse_model_output(...)                    # 5. 解析文本和工具调用
    reply = self._build_reply(...)                       #    组织协议回复
    ...  # 更新解析状态，统计 token，判断是否流式
    response = await self._respond(...)                  # 6. 构造或写出 HTTP 响应
    self.manager.record_turn(...)                       # 7. 记录本轮轨迹
    s.prompt_prefixes.append(PromptPrefix(...))          #    保存本轮前缀，供后续请求接续
    return response
finally:
    self.inflight.get(sid, set()).discard(task)           # 返回或异常离开前清理登记
```

**这里对 `trace_span` 先理解三点即可：**

- **作用**：为包围的执行阶段记录开始、结束、层级关系及附加信息，供后续诊断使用。
- **包围范围**：`agent_tokenize` 包住消息转换与输入编码；`agent_model_turn` 再包含模型生成。后面的解码、响应与 manager 记录位于这两层追踪范围之外。
- **交出什么**：业务调用仍交出 `prompt_ids` 和 `turn`，追踪另外留下执行记录；这些记录与训练使用的 `TurnRecord` 分工不同。

骨架先交代“为什么出现、包住哪里、留下什么”，足够对应回 [common.py:410–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L410-L425)。记录格式、上下文传递和导出留给[后续 Trace 专题](../../../../../slime_photo/code-reading/chapters/04-trace-validation/README.md#coding-agent-trace-candidate)。

<a id="confirmed-reading-order"></a>
<a id="reading-path"></a>

### 3.4 每次读哪一段，读到什么程度

下面按这一轮的**观察与回看顺序**列到请求结束。先读转换、输入准备和模型生成，第 4 项再回看包围它们的 `trace_span`，随后继续解码到收尾。真实执行与嵌套仍以上方 3.3 为准：追踪并非在模型生成后才开始执行。

入口已取好 `body`、`sid` 和会话 `s`，不清楚时回查 `common.py:394–407`，不作为这轮重新展开的第一项。表中的编号是阅读观察点；函数内的参数准备和收尾仍留在 `_run_turn` 中，不另建函数卡片。

先用图定位，再用下表打开对应卡片；两者使用同一组编号。这条路线由本轮已发生的观察与追问整理，后续复习可按当前缺口进入回查分支。

```text
从 _run_turn 的输入转换进入
│
├─ 1. _translate → translated ＋ tools_schema
├─ 2. _session_prompt_ids → prompt_ids
│     └─ 编码过程不清楚时：_render_token_ids → apply_chat_template
│        读完返回第 2 项，看候选检查与拼接／回退
├─ 3. call_sglang_generate → turn
│
├─ 4. 回看 trace_span：前面三个调用怎样被追踪包围
│     └─ 这是阅读时回看；看清包围范围后回到业务主线
│
├─ 5. tok.decode → raw_output
├─ 6. parse_model_output → parsed
├─ 7. _build_reply → reply.wire ＋ reply.manager_message
├─ 8. 留在 _run_turn：回填格式标记，准备计数与响应模式
│
├─ 9. _respond → response
│     ├─ 普通响应：需要时回查 _render_response → json_response
│     └─ 流式响应：需要时回查 _render_stream
│        看清本次采用的分支后，返回第 10 项
├─ 10. record_turn → 会话树中的消息与生成记录
├─ 11. 保存 PromptPrefix → 后续同一会话请求的前缀候选
│      └─ 接回第 2 项的读取用途，本次请求继续向下
└─ 12. 留在 _run_turn：返回 response，退出前清理请求登记
```

图中第 4 项的回看与第 11 项的用途关联都属于阅读导航。实际执行顺序及追踪嵌套见 [3.3](#run-turn-normal-path)，阅读后的数据交接总结见 [task flow](05-task-flow.md#run-turn-flow)。

| 阅读次序与卡片入口 | 调用处与源码入口 | 本处看清什么就停 | 读完接到哪里 |
| --- | --- | --- | --- |
| 1. [_translate](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | `common.py:415` → `anthropic.py:58–61、81–143` | 请求怎样分成 `translated` 与 `tools_schema`；多个工具结果如何按调用顺序整理 | 用这两份数据进入第 2 项 |
| 2. [_session_prompt_ids](02-short-term-memory/functions/slime/agent/adapters/common.py/_session_prompt_ids.md)，内部回看 [_render_token_ids](02-short-term-memory/functions/slime/agent/adapters/common.py/_render_token_ids.md) | `common.py:416–421` → [93–136](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L93-L136)；模板编码在 `73–90` | 普通编码怎样得到；历史候选怎样通过检查后拼接，全部不合格时怎样回退 | 接住 `prompt_ids`，到 `423` 请求模型；候选的保存来源留到第 11 项 |
| 3. [call_sglang_generate](02-short-term-memory/functions/slime/agent/adapters/common.py/call_sglang_generate.md) | `common.py:423` → [524–700](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L524-L700) | 输入怎样发送，最终 `TurnRecord` 带回哪些生成数据；续生成分支按已有卡片回查 | 接住 `turn`；先回看第 4 项追踪，再使用 `turn.output_ids` |
| 4. 回看 [trace_span](02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md) | `common.py:412、414` → [trace_utils.py:345–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L345-L425) | 已有 TraceHandle 怎样记录被包围阶段的事件；区分追踪记录与业务返回值 | 回到 `common.py:425`；完整传播与导出留给后续专题 |
| 5. 唤起 [tok.decode](02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) 的已有认识 | `common.py:425` → tokenizer 的 `decode` | `turn.output_ids` 怎样还原为 `raw_output` 字符串；此调用保留特殊 token | 将 `raw_output` 交给 `426–431` 的解析器 |
| 6. [parse_model_output](02-short-term-memory/functions/slime/agent/parsing.py/parse_model_output.md) | `common.py:426–431` → `parsing.py:25–56` | 字符串怎样拆成文本、思考、工具调用描述与格式标记 | 接住 `parsed`，到 `432` 组装回复 |
| 7. [_build_reply](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md) | `common.py:432` → `anthropic.py:63–69` | `parsed` 怎样变成 Reply；区分 `wire` 与 `manager_message` 的用途 | 保留 `reply`，继续 `433–436` 的准备语句 |
| 8. 留在 `_run_turn`：标记回填与响应参数准备 | [common.py:433–436](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L433-L436) | 将格式标记补回 `turn`，取得 `in_tok`、`out_tok` 与 `stream`；参数用途可回看 [_respond 的输入说明](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._respond.md#response-preparation) | 到 `442`，把 `reply`、计数和模式交给 `_respond` |
| 9. [_respond](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) | `common.py:442` → `anthropic.py:71–75` | 普通分支怎样返回响应对象，流式分支怎样写出事件；看清发送时机的区别 | 接住 `response`；正常路径经过调试回调后，到 `463–469` 记录轨迹 |
| 10. [TrajectoryManager.record_turn](02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md) | `common.py:463–469` → `trajectory.py:381–403` | `translated`、`reply.manager_message` 与 `turn` 怎样交给会话消息树；区分轨迹记录与路径搜索 | 返回 `_run_turn:470`，继续保存输入接续所需的候选 |
| 11. [PromptPrefix 类卡片](02-short-term-memory/classes/slime/agent/adapters/common.py/PromptPrefix.md)与追加动作 | `common.py:470–472` → 类定义 `38–42` | 一份候选保存哪三个字段，怎样加入 `s.prompt_prefixes`；接回第 2 项的读取用途 | 本次继续 `473` 返回响应；后续同一会话请求才检查这些候选 |
| 12. 留在 `_run_turn`：返回与清理 | [common.py:473–475](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L473-L475)；回查 [inflight 说明](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#inflight-cleanup) | 正常返回前先清理当前请求的任务登记；已保存的轨迹与前缀继续保留 | 本次请求处理到此收束，回到 `_run_turn` 整体模型 |

<details>
<summary>主线后集中复核的四个辅助函数：需要时从父函数进入</summary>

这些函数在本轮主线之后集中核对过，均未发现实现变化，原卡片保留。回看时按所属父函数进入，不把它们重新排成四个外层阶段：

| 回查位置 | 辅助函数 | 看清后返回哪里 |
| --- | --- | --- |
| 第 2 项的 `_render_token_ids` 内部 | [apply_chat_template](02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md) | 取得编码结果后返回 `_render_token_ids`，再回到 `_session_prompt_ids` 的检查 |
| 第 9 项的普通响应分支 | [_render_response](02-short-term-memory/functions/slime/agent/adapters/anthropic.py/_render_response.md) | 把正文字典交给 `json_response` |
| 第 9 项的普通响应分支 | [json_response](02-short-term-memory/functions/aiohttp/web_response.py/json_response.md) | 响应对象经 `_respond` 返回 `_run_turn` |
| 第 9 项的流式响应分支 | [_render_stream](02-short-term-memory/functions/slime/agent/adapters/anthropic.py/_render_stream.md) | 写出事件后，响应对象经 `_respond` 返回 `_run_turn` |

固定版本与核对范围见[辅助函数版本记录](references/auxiliary-functions-version-check-2026-10-23.md)。

</details>

本轮仍以这次模型请求为边界。上游 `BaseHarness.run` 只用于恢复来路；三个 Anthropic 引用文件从共同卡片定位实现，不增加独立阅读阶段。各卡片继续按自身标注的版本使用；`_run_turn` 整卡与 task flow 已按新版执行顺序校准。

本步各函数在 `18868a79` 下的数据交接见 [task flow](05-task-flow.md#run-turn-flow)，旧版逐段讲解见[从 `_run_turn` 读清一次请求](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#run-turn-step-by-step)。原始问题与纠正放 `04-flow.md`，可复用的函数模型放 `02`，scope 只负责路线与阅读深度。

本轮以能连接上述输入输出、区分协议响应与轨迹记录，并说明最后清理什么为停止条件。CLI 的工具执行循环、线程启动、SGLang 内部及轨迹树完整算法不作为本步收束的前提；已读函数的内部解释与未知保留在各卡片，函数出现在骨架中不等于已读懂其全部实现。

当前接续统一见[阅读路线](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。正常路径的收束说明见 [task flow 的阅读边界](05-task-flow.md#step-boundary)；不在本文件另存一份实时进度。
