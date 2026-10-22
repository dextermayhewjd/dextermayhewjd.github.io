# 01 · 阅读范围：沿 _run_turn 读清一次模型请求

[本步入口](README.md) · [Step 0 核心骨架](../step-000-coding-agent/01-scope.md) · [前序函数记忆](03-long-term-memory/overview.md)

## 1. 阅读目标

沿用理解 Coding Agent 的整体目标。本步沿 `BaseAdapter._run_turn`，读清一份模型请求怎样变成模型输入，再怎样生成回复、组织 HTTP 响应并记录轨迹。已有 Claude Code / Anthropic 分支作为具体场景；Harness 到 Adapter 的连接保留为进入本步的来路。

## 2. 指挥官函数与本步入口：`generate` → `BaseAdapter._run_turn`

整体指挥官沿用 Step 0 的 `generate`；本步从第 4 项运行中的 CLI 请求模型这一条路径，定位到局部编排函数 `_run_turn`。它串联一次请求的转换、编码、生成、解析、响应与记录，适合从头到尾逐段读。

外层调用位于 `examples/coding_agent_rl/generate.py:205`；HTTP 路由在 `slime/agent/adapters/anthropic.py:49` 绑定到 `self._run_turn`，实际执行体是 [slime/agent/adapters/common.py:318–393](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L318-L393)。本场景的 `self` 是 `AnthropicAdapter`，共同流程调用它的协议钩子。

从这里进入 [_run_turn 函数卡片](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)，建立该函数的输入输出与内部处理模型；需要展开子函数时，使用卡片中相应调用处的链接，读完回到该处继续。

源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。进入时只需知道：CLI 已运行、Adapter 已监听并注册路由、tokenizer 与模型服务地址已配置、请求可关联到一个会话。创建这些条件的内部实现留在[上游链路](05-task-flow.md)按需回查。

## 3. 给出真正干活的核心骨架

### 3.1 继承 Step 0：保留七项核心骨架

下面原样继承 [Step 0 的核心骨架](../step-000-coding-agent/01-scope.md)，用于定位本步。**当前只展开第 4 项，其余各项保留整体位置。**

这是 `evaluation=False` 正常路径的教学裁剪，保留函数名、执行顺序与返回值，调用参数统一用 `...` 省略。配置、检查、日志、异常、附加元数据和最终清理暂时略去；这不是可直接运行的完整代码。

```python
state.adapter.open_session(...)                          # 1. 登记本次会话
async with boot_agent_sandbox(...) as sb:                 # 2. 启动执行沙箱
    await swe.prepare_workspace(...)                     # 3. 准备工作区
    agent_exit_code = await HARNESS_CLS().run(...)        # 4. 运行 Coding Agent
    diff_text = await swe.git_diff(...)                   # 5. 取得代码改动

reward, applied_cleanly = await swe.run_evaluation(...)   # 6. 独立评测
samples = await state.adapter.finish_session(...)        # 7. 导出本次会话的样本
return samples
```

<a id="step-1-branch"></a>

### 3.2 从第 4 项找到本步：Harness → CLI → Adapter

下面是面包屑导航，HTTP 箭头表示跨进程请求；不是 Harness 对 `_run_turn` 的直接函数调用。`harness/`、`adapters/` 路径均相对于 `slime/agent/`。

```text
generate 的第 4 项：await HARNESS_CLS().run(...)       # examples/coding_agent_rl/generate.py:205
└─ BaseHarness.run 启动并等待外部 CLI                  # harness/common.py:81
   └─ CLI 运行期间 ── HTTP POST /v1/messages ──→ Adapter
      └─ 路由绑定 self._run_turn                      # adapters/anthropic.py:49
         └─ BaseAdapter._run_turn(request)            # adapters/common.py:318，本步逐段读
```

**回到核心骨架：** 一次 HTTP 响应先回到 CLI；只有 CLI 整体退出，第 4 项才取得 `agent_exit_code`，随后进入第 5 项 `swe.git_diff(...)`。

### 3.3 `_run_turn` 的正常处理顺序

以下是教学裁剪：保留真实函数名与顺序；参数用 `...` 省略，前置门禁、计时、调试回调和异常处理暂时折叠。仅 `_translate` 保留 `body`，便于接回已有输入输出记录。

```python
body = await request.json()                              # 1. 读取请求
self._preprocess_body(body)
sid = self._session_id(request, body)
...  # 检查会话，取得 Session，登记当前请求
try:
    translated, tools_schema = self._translate(body)      # 2. 转换消息与工具定义
    prompt_ids = _render_token_ids(...)                  # 3. 编码模型输入
    turn = await call_sglang_generate(...)               # 4. 获取本轮生成记录
    raw_output = tok.decode(...) if turn.output_ids else ""
    parsed = parse_model_output(...)                    # 5. 解析文本和工具调用
    reply = self._build_reply(...)                       #    组织协议回复
    ...  # 更新解析状态，统计 token，判断是否流式
    response = await self._respond(...)                  # 6. 构造或写出 HTTP 响应
    self.manager.record_turn(...)                       # 7. 记录本轮轨迹
    return response
finally:
    self.inflight.get(sid, set()).discard(task)           # 返回或异常离开前清理登记
```

### 3.4 每次读哪一段，读到什么程度

下列行号均属于 `slime/agent/adapters/common.py`。沿实际执行顺序前进，子函数先看本处的输入输出；影响交接时再下钻。

| 次序 | 源码行 | 本段只解决的问题 | 交给下一段的东西 |
| --- | --- | --- | --- |
| 1 | 325–338 | 哪份请求、哪个会话？ | `body`、`sid`、`s` |
| 2 | 341 | 消息历史与工具定义如何分开？ | `translated`、`tools_schema`；复用[原转换记录](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) |
| 3 | 342 → 58–73 | 两份转换结果如何交给模板？ | `prompt_ids`；已整理 [_render_token_ids](02-short-term-memory/functions/slime/agent/adapters/common.py/_render_token_ids.md) 的参数交接与返回值 |
| 4 | 344 → 442–514 | 本轮生成交回什么？ | `turn`；内部交接见 [call_sglang_generate](02-short-term-memory/functions/slime/agent/adapters/common.py/call_sglang_generate.md) 的六段执行地图 |
| 5 | 346–357 | 输出 token 如何变成回复内容？ | `parsed`、`reply`、token 数与流式选择 |
| 6 | 363 | 回复如何交给 HTTP 层？ | `response`；非流式构造对象，流式在此写出 |
| 7 | 384–393 | 记录什么、清理什么、返回哪里？ | 会话轨迹；响应交回 aiohttp，CLI 继续运行 |

本步各函数的数据交接见 [task flow](05-task-flow.md#run-turn-flow)，已有逐段讲解见[从 `_run_turn` 读清一次请求](../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#run-turn-step-by-step)。原始问题与纠正放 `04-flow.md`，可复用的函数模型放 `02`，scope 只负责路线与阅读深度。

本轮以能连接上述输入输出、区分协议响应与轨迹记录，并说明最后清理什么为停止条件。CLI 的工具执行循环、线程启动、SGLang 内部及轨迹树完整算法不作为本步收束的前提；已读函数的内部解释与未知保留在各卡片，函数出现在骨架中不等于已读懂其全部实现。

当前接续统一见[阅读路线](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。本步正常路径的收束说明见 [task flow 的阅读边界](05-task-flow.md#step-boundary)；不在本文件另存一份实时进度。
