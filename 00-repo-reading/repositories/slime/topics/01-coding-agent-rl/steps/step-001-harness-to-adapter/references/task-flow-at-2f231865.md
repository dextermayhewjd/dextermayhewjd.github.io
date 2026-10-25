> 历史快照：2026-10-23 在新版校准前保存，正文对应 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。除为迁移位置调整相对链接外，原文完整保留。文中的“当前”、步骤编号与实现选择属于当时语境；函数卡片链接可能已更新，技术依据仍以本页固定源码链接为准。新版总结见 [当前 task flow](../05-task-flow.md)。

# 05 · 任务链路：以 _run_turn 串起一次模型请求

> `_run_turn` 接住一份模型请求，组织输入、生成与解析，把回复交给 HTTP 层，把本轮消息和 token 记录交给 manager，最后清理当前请求的在途登记。

[本步范围](../01-scope.md) · [步骤入口](../README.md) · [函数记录](../02-short-term-memory/overview.md) · [本次问题与澄清](../04-flow.md#run-turn-task-flow-closure)

## 1. 本步在任务中的位置

前一步的[核心骨架](../../step-000-coding-agent/01-scope.md)说明整次 Coding Agent 任务。本页沿其中一次模型请求，连接本步已读的函数。scope 保留阅读范围与骨架，本页说明数据怎样交接，单函数实现继续从 `02` 的记录打开。

```text
generate 的第 4 项：HARNESS_CLS().run(...)，启动并等待 CLI
└─ Claude Code CLI 运行期间
   └─ HTTP POST /v1/messages
      └─ BaseAdapter._run_turn(request) ← 本页核心
```

- **起点：** Adapter 已监听并注册路由，请求交给 `_run_turn`；会话、tokenizer 和 SGLang 地址可用。
- **终点：** 正常路径返回 HTTP 响应对象，本轮数据已交给 manager，当前请求的在途登记已移除。CLI 得到响应后继续任务，Harness 仍等待它整体退出。
- **场景：** 沿用 Claude Code / Anthropic，以非流式响应为主，保留流式分支的发送时机差异。以下为固定源码的解释，不是一次实际运行日志。

<a id="run-turn-flow"></a>

## 2. 沿 _run_turn 看数据交接

下面是正常路径的阅读图，行号均属于 `slime/agent/adapters/common.py`。调用实参按需省略；会话门禁、日志、调试回调和异常分支折叠，具体实现以链接的源码与函数记录为准。

```text
BaseAdapter._run_turn(request)                               318
│
├─ request.json()，预处理并定位会话                          325–338
│  → body、sid、Session；取得 tok，登记当前 task
│
├─ self._translate(body)                                     341
│  → translated（系统指令与消息历史）＋ tools_schema（工具定义）
├─ _render_token_ids(...)                                    342
│  → prompt_ids：按模板组织并编码后的 token ID 列表
├─ await call_sglang_generate(...)                           344
│  → turn：输入/输出 token、生成 token 的 logprob、结束原因
│
├─ tok.decode(turn.output_ids, ...)                          346
│  → raw_output：生成的原始文本，保留特殊标记
├─ parse_model_output(raw_output, ...)                       347–352
│  → parsed：reasoning、text、工具调用描述与格式标记
├─ self._build_reply(parsed, ...)                            353
│  → reply：wire 给协议响应，manager_message 给轨迹记录
├─ 补 turn.ill_formed；计算 in_tok / out_tok；确定 stream      354–357
│
├─ await self._respond(..., reply, in_tok, out_tok, stream)   363
│  → response：HTTP 响应对象；正常返回后继续
├─ self.manager.record_turn(...)                            384–390
│  → 把 translated、reply.manager_message、turn 接入会话树
│    返回 None，结果保存在 manager 内部
└─ return response；真正返回前执行 finally                  391–393
   → 移除当前 task 的在途登记，把 response 交回 aiohttp
```

按图中的顺序回查单函数，读完返回图中的下一行：

- 输入到生成：[_translate](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) → [_render_token_ids](../02-short-term-memory/functions/slime/agent/adapters/common.py/_render_token_ids.md) → [call_sglang_generate](../02-short-term-memory/functions/slime/agent/adapters/common.py/call_sglang_generate.md)。最后一个函数向 SGLang `/generate` 发起 HTTP 请求，携带 `prompt_ids` 与采样参数，再把服务端结果整理成 `TurnRecord`。
- 生成到回复材料：[decode](../02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) → [parse_model_output](../02-short-term-memory/functions/slime/agent/parsing.py/parse_model_output.md) → [_build_reply](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md)。这里产生的是工具调用的结构化描述；工具的实际执行在 CLI 一侧。
- 两项交付：[_respond](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) → [record_turn](../02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md)。下方区分各自消费的数据。

<a id="response-and-recording"></a>

### HTTP 响应和轨迹记录各接走什么

`reply.wire` 由具体 Adapter 的 `_respond` 读取，组织为 CLI 能接收的协议响应；`reply.manager_message` 是供 manager 使用的内部 assistant 消息。`turn` 另外保存 token 与 logprob 等生成信息。

下面摘录实际交接，省略中间的异常处理与调试回调：

```python
response = await self._respond(request, body, reply, in_tok, out_tok, stream)
self.manager.record_turn(
    sid,
    turn=turn,
    prompt_messages=translated,
    response_message=reply.manager_message,
    metadata={"sid": sid},
)
return response
```

因此，manager 保存的是本轮的消息与生成记录，`response` 留给 aiohttp。树按消息组织节点，本轮 assistant 节点附带 `turn`；响应对象本身不会被挂到树上。token 计数则由 `_respond` 写入协议响应的用量字段。

**先调用 `_respond`，再调用 `record_turn`，不等于先确认客户端收到，再记录。** 非流式分支先构造 `response`，在 handler 返回后由 aiohttp 发送；流式分支在 `_respond` 内准备连接并写出事件，然后返回。两种情况下，当前记录都不是客户端消费回复的确认凭证。

<a id="adapter-dispatch"></a>

## 3. 两个 Adapter 怎样共用这条流程

`generate.py:45–52` 根据 `SWE_AGENT` 选出 Harness 与 Adapter 的配对，在 `:150` 创建 Adapter 实例：

| 运行前选择 | Harness | Adapter 与请求入口 |
| --- | --- | --- |
| `claude_code`（默认） | `ClaudeCodeHarness` | `AnthropicAdapter`，`POST /v1/messages` |
| `codex` | `CodexHarness` | `OpenAIAdapter`，`POST /v1/chat/completions` |

两者都把路由绑定到继承的 `BaseAdapter._run_turn`。本场景中，`self` 始终是同一个 `AnthropicAdapter` 实例，`self._translate`、`self._build_reply`、`self._respond` 执行它的具体实现；选择 OpenAI 分支时，同样的位置执行 OpenAI 的实现。

共同流程因此能够接收相同的内部交接形式：转换后的消息与工具定义、`TurnRecord`、解析结果，以及含 `wire` / `manager_message` 的 `Reply`。各协议负责自己的输入转换和响应格式；会话识别、预处理及采样参数名称也有各自约定。**这是运行前选择实现、请求处理中复用共同流程，一次请求不会在两个 Adapter 之间来回切换。**

<a id="inflight-cleanup"></a>

## 4. 结束本次请求

离开请求处理时，清理当前请求的在途登记（`common.py:392–393`）。登记与移除的具体代码、前后状态见 [_run_turn 的局部说明](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#inflight-cleanup)。

<a id="step-boundary"></a>

## 5. 这一步可以在哪里收束

**本步可以收束为：一份模型请求如何经过输入整理、模型生成、结果解析，交出协议响应并留下本轮轨迹，最后清理请求登记。** 上面的交接图把已读函数接回了这个目标；不要求同时展开每个子函数的全部内部机制。

CLI 怎样执行收到的工具调用、怎样组织下一次请求，属于外部工具循环；manager 怎样导出训练样本，以及会话关闭的完整取消机制，也超出本次收束范围。它们保留为后续问题，不因本页整理完成就视为已读懂。

## 6. 按需恢复 Harness 到 HTTP 的来路

<details>
<summary>展开此前的调用行、HTTP 往返与启动说明</summary>

以下保留此前“追到请求入口”的讲解与当时边界。需要恢复上游时再打开；本次请求内部的完整交接以上方 `_run_turn` 图为准。

### 上游源码导航

<!-- 同步自 slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#source-jump-map；先改源文，再同步此段。 -->

<a id="call-sites-and-implementations"></a>
<a id="source-jump-map"></a>

### 源码导航：这一行调用谁，读完回哪里

**现在先打开 `slime/agent/harness/common.py:97`，看 `BaseHarness.run` 的函数体。** 定义从第 81 行开始。下面区分 `harness/common.py` 和 `adapters/common.py`，不把它们都简称为 `common.py`。

本篇沿用 Claude Code 分支。[`generate.py:46、52`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L45)选出的配对是 **`ClaudeCodeHarness` + `AnthropicAdapter`**：

- **启动端：** `ClaudeCodeHarness` 继承 `BaseHarness.run`，所以 `run` 要看 `harness/common.py`；它自己实现的 `write_config` 和 `launch_and_wait` 则在 `harness/claude_code.py`。
- **接收端：** `AnthropicAdapter` 在 `adapters/anthropic.py` 注册 HTTP 路由；它继承的 `_run_turn` 在 `adapters/common.py`。这里的 Anthropic 是 Adapter 的协议实现。

#### 启动端：顺着调用行走

下面各路径相对于 `slime/agent/`。每个框列出实际执行的函数及阅读范围，每条箭头标出调用语句的位置。行号按固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 核对。

```text
外层入口：examples/coding_agent_rl/generate.py:205
agent_exit_code = await HARNESS_CLS().run(...)
                  │
                  ▼
A  harness/common.py:81–104
   BaseHarness.run
   97–103：准备运行用户、上下文和配置
   104：return await self.launch_and_wait(...)
                  │ 第 104 行调用 B
                  ▼
B  harness/claude_code.py:57–71
   ClaudeCodeHarness.launch_and_wait
   58–70：准备 Claude 命令、任务提示和环境变量
   71：return await run_agent(...)
                  │ 第 71 行调用 C
                  ▼
C  harness/common.py:107–122
   run_agent
   109–110：准备输出目录
   111–121：exit_code, _ = await exec_and_wait(...)
                  │ 第 111 行开始调用 D
                  ▼
D  sandbox.py:82–145
   exec_and_wait
   107–113：写入启动脚本
   129–138：调用 sb.exec，后台启动脚本中的 Claude 命令
   139：等待 _await_done_marker（定义在 65–79）
                  │
                  └─ Claude 已运行；A、B、C 仍在等结果
```

代码入口：[A · run](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L97) · [B · launch_and_wait](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/claude_code.py#L57) · [C · run_agent](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/harness/common.py#L107) · [D · exec_and_wait](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/sandbox.py#L107)。

`run` 前半段的小调用先完成，再进入上面的 B：

| 当前语句 | 实际读取位置 | 做什么，完成后回哪里 |
| --- | --- | --- |
| `harness/common.py:97` 的 `ensure_agent_user` | `sandbox.py:390–399` | 准备 agent 用户、目录权限与 Git 设置；回来继续第 98 行 |
| `harness/common.py:98–102` 的 `HarnessContext(...)` | 字段定义在 `harness/common.py:43–54` | 包装工作目录、会话和 Adapter 地址；继续第 103 行 |
| `harness/common.py:103` 的 `self.write_config(...)` | `harness/claude_code.py:44–55` | 写 Claude 启动配置；回来继续第 104 行 |

#### 接收端：这里通过 HTTP 接上

```text
沙箱中的 Claude CLI（外部安装包）
   请求地址来自 harness/claude_code.py:63
                  │ HTTP POST /v1/messages
                  ▼
已启动的 Adapter 服务
   按 adapters/anthropic.py:49 预先登记的路由分派
                  │ 路由绑定的是 self._run_turn
                  ▼
adapters/common.py:318  BaseAdapter._run_turn
   325：body = await request.json()
   341：self._translate(body)  ← 已有函数记忆的接续位置
```

[`adapters/anthropic.py:49`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L49) 是提前执行的路由注册。请求到达时，服务使用这条规则进入 [`adapters/common.py:318`](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L318)。它不是从 `exec_and_wait` 直接调用过来的。

CLI 内部发送 HTTP 的函数尚未检查，所以在图上标为外部程序；`sb.exec` 的具体 Sandbox 后端实现也未在本步展开。图只把已经核对的连接接起来。

#### 嵌套时保留返回位置

每次只沿当前的一条箭头读，并保留“从哪一行进来、这段要看什么、读到哪一行、完成后回哪里”。例如第一跳：

| 当前这一跳 | 具体位置与问题 |
| --- | --- |
| 从哪里进来 | `harness/common.py:104` 的 `self.launch_and_wait(...)` |
| 打开哪里 | `harness/claude_code.py:57–71` |
| 这段看什么 | 第 58 行怎样形成命令，第 62–70 行怎样形成环境；第 71 行交给谁执行 |
| 遇到下一层 | 到第 71 行，转看 C；保留“B 第 71 行在等结果”这个返回位置 |
| 最终回哪里 | C 交回退出码后，B 第 71 行把它返回给 A 第 104 行；A 直接返回外层 `generate.py:205` |

正常结束时的完整返回方向是：D 的第 141 或 145 行交回 `(exit_code, output)` → C 第 111 行接收、第 122 行返回退出码 → B 第 71 行 → A 第 104 行 → `generate.py:205` 接收退出码、随后执行第 213 行收集 diff。

一次 HTTP 响应先回到 Claude CLI；只有 CLI 整体结束并由启动脚本写下退出码，启动端才沿上述方向返回。这里只做静态源码核对，没有运行 CLI、沙箱或模型服务。


### 上游 HTTP 服务怎样传递请求和响应

<!-- 同步自 slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#http-round-trip。 -->

<a id="http-round-trip"></a>

### 为什么这里有 HTTP，信息怎样往返

函数调用链把我们带到了正在运行的 Claude CLI。现在只展开它与 Adapter 之间的一次模型请求：**Claude CLI 是发送方，Adapter 是接收并回复的一方。**

Claude CLI 是沙箱中的独立程序，通过模型 API 获取回复。这个实现让 Slime 提供一个兼容的 API 入口，再把 Claude 的请求地址指向它；Adapter 收到请求后可以接入 SGLang，并保存这一轮的轨迹。对应处理位置是 `adapters/common.py:344、384`，本段只把模型处理视为中间步骤。

这里的“HTTP 服务”，就是 Slime 中持续监听网络地址和端口、接收请求并回复的那部分程序。Adapter 提供处理逻辑，`aiohttp` 负责网络接收、HTTP 解析、路由和响应发送。

#### 1．Slime 先准备接收方，并开始监听

启动顺序及源码位置如下。路径以 Slime 仓库为起点：

| 先后 | 源码位置 | 这一段做什么 |
| --- | --- | --- |
| ① 创建 Web 应用 | `slime/agent/adapters/common.py:159` | `web.Application(...)` 创建保存路由等配置的应用对象 |
| ② 登记接收规则 | `slime/agent/adapters/common.py:175` → `adapters/anthropic.py:49` | 将 `POST /v1/messages` 交给 `self._run_turn` |
| ③ 启动服务 | `examples/coding_agent_rl/generate.py:161–170` | 把 `self.adapter.app` 交给 `run_app_in_thread` |
| ④ 监听地址和端口 | `slime/agent/aiohttp_threaded.py:69–72` | 创建 `TCPSite` 并启动监听，实际开始接收网络连接 |

第④处的源码是：

```python
runner = web.AppRunner(app, **(runner_kwargs or {}))  # 让运行器管理这个 Web 应用
loop.run_until_complete(runner.setup())
site = web.TCPSite(runner, host, port)              # 指定监听地址与端口
loop.run_until_complete(site.start())              # 开始监听
```

这个服务在独立线程中运行（`aiohttp_threaded.py:87–88`）。因此，外层 Harness 等待 Claude 退出时，它仍能接收请求。注册路由、开始监听是两件按顺序发生的事；只有创建应用和登记路由，还没有启动网络服务。

代码入口：[创建与启动调用](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L150) · [实际监听](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/aiohttp_threaded.py#L69)。

#### 2．Slime 把接收地址交给 Claude

`generate.py:171` 组成对外地址：

```python
self.adapter_url = f"http://{CONFIG.adapter_public_host}:{self.app_handle.port}"
```

这个地址经过已经读过的 Harness 调用链，在 `harness/claude_code.py:63` 放进 Claude 的环境变量：

```python
"ANTHROPIC_BASE_URL": ctx.adapter_url,  # Claude 的模型 API 请求使用这个地址
```

可以把请求地址分成三部分：`主机地址` 找到接收方，`端口` 找到接收服务，`/v1/messages` 选择服务内的接口。`adapter_public_host` 必须是沙箱能够访问的地址；监听时使用的 `adapter_bind_host` 与客户端访问的主机地址分别配置，不能把两者混为一个值。

Claude Code 支持用 `ANTHROPIC_BASE_URL` 改变 API 地址，见[官方环境变量说明](https://code.claude.com/docs/en/env-vars)。设置地址是在告诉客户端去哪里，真正发请求发生在 Claude 程序运行期间。

#### 3．Claude 发出请求，Adapter 把网络数据交给 Python 处理器

下面是本次信息流，HTTP 发送发生在外部 CLI 内部，具体发送函数尚未检查：

```text
Claude CLI 中的消息、工具定义等请求数据
     │ 编码为 JSON，作为 HTTP POST 的请求体发送
     ▼
Adapter 的监听地址和端口
     │ aiohttp 接收请求，并按方法和路径查路由
     │ 路由依据：adapters/anthropic.py:49
     ▼
BaseAdapter._run_turn(request)             adapters/common.py:318
     │ await request.json()               adapters/common.py:325
     ▼
Python 中的 body 字典
     │ 后续交给转换、模型调用与响应组织
```

传过来的是序列化后的数据；`await request.json()` 将请求体里的 JSON 解析成这里使用的 Python 字典。原始 CLI 数据对象和 Adapter 中的 `body` 并不是共享内存里的同一个对象。

以消息字段为例，下面只截取一小部分，省略其他请求字段：

```json
{"messages": [{"role": "user", "content": "请检查这个函数。"}]}
```

解析后，处理器就能从 `body["messages"][0]["content"]` 取得这段文字。这是教学构造的字段节选，不是实际抓包，也不是完整的 Claude 请求。

#### 4．处理器给出响应，aiohttp 将它回送给这次请求的发送方

模型处理完成后，`adapters/common.py:363` 调用 `self._respond(...)`，具体实现是 `adapters/anthropic.py:71–75`：

```python
blocks, stop_reason = reply.wire
if stream:
    return await _render_stream(request, blocks, stop_reason, in_tok, out_tok)
return web.json_response(_render_response(body, blocks, stop_reason, in_tok, out_tok))
```

两条分支的返回方向相同，表达方式不同：

- **非流式：** `web.json_response(...)` 把组织好的回复变成 JSON 响应对象；`_run_turn` 在 `adapters/common.py:391` 返回这个对象，由 aiohttp 发送。
- **流式：** `_render_stream` 在 `adapters/anthropic.py:223` 用 `out.prepare(request)` 关联这次请求，再通过 `out.write(...)` 写出事件数据。这些数据仍属于这次 HTTP 响应。

**响应沿客户端发起的这次请求连接回去。** aiohttp 保留了请求与连接的对应关系；Adapter 不需要另找 Claude 的监听地址再发一个 POST。Claude 的 HTTP 客户端读到响应，把它交回自己的任务处理逻辑。

```text
请求：Claude CLI ── HTTP 请求体 ──▶ Adapter ──▶ _run_turn
响应：Claude CLI ◀─ JSON / 事件流 ◀─ aiohttp ◀─ _respond
```

这次 HTTP 往返结束，只表示 Claude 得到了这一轮模型结果。它可以继续任务、再发下一次请求；外层 `run` 继续等待整个 CLI 退出。

代码入口：[调用响应实现](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L363) · [JSON 与流式分支](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L71) · [向请求连接写事件](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L211)。`aiohttp` 的请求处理与响应机制见[官方入门](https://docs.aiohttp.org/en/stable/web_quickstart.html#handler)和[服务端接口](https://docs.aiohttp.org/en/stable/web_reference.html#streamresponse)。

本段按固定源码做静态核对，未运行沙箱、Claude CLI 或模型服务。网络协议的更底层实现、CLI 内部发送函数和模型生成内部过程继续留白。


### 上游逐句解释

<details>
<summary>展开 run 的逐句说明与数据交接</summary>

<a id="harness-to-adapter"></a>
<a id="run-execution-order"></a>

### 从 run 开始：一句执行完，下一句去哪里

这次沿 Claude Code / Anthropic 分支，只看正常执行路径。起点是 `generate` 已经拿到沙箱 `sb`、工作目录、任务提示和 Adapter 地址，开始等待 `HARNESS_CLS().run(...)`。Adapter 的 HTTP 服务此时也已经启动。

`HARNESS_CLS` 在这个分支是 `ClaudeCodeHarness`，它继承了 `BaseHarness.run`。因此下面进入的是 `BaseHarness.run` 的函数体，`self` 仍是这个 Claude Code Harness 对象。

**1．先在 run 里面，按顺序做四件事。**

下面是函数体的源码，加了阅读注释：

```python
await _sandbox.ensure_agent_user(sb, workdir)  # ① 准备 agent 用户及目录权限；完成后继续
ctx = HarnessContext(                       # ② 把下面三个已有值放进一个上下文对象
    workdir=workdir,
    session_id=session_id,
    adapter_url=adapter_url,
)
await self.write_config(sb, ctx)             # ③ 写 Claude 的配置；完成后回到这里
return await self.launch_and_wait(sb, ctx, prompt, time_budget_sec)  # ④ 进入启动和等待
```

① 先处理运行用户。② 只是整理数据：后面需要地址时，从 `ctx.adapter_url` 取。③ 进入 `ClaudeCodeHarness.write_config`，将跳过初次引导、接受权限模式所需的设置写入沙箱，写完回到 `run`。④ 才进入 `ClaudeCodeHarness.launch_and_wait`。

**到④时，run 还没有返回。** `return await ...` 要先等右边完成、拿到结果，再把结果返回给 `generate`。接下来跟进右边的函数。

**2．进入 launch_and_wait：准备要启动的程序、任务和环境。**

下面从实际实现中裁剪，只保留本次需要的字段；其他环境变量及额外参数处理省略：

```python
cmd = f"/usr/local/bin/claude -p {shlex.quote(prompt)} {self.launch_flags}"  # 要执行的命令
env = {
    "ANTHROPIC_BASE_URL": ctx.adapter_url,     # Claude 向这个 API 地址请求模型
    "ANTHROPIC_AUTH_TOKEN": ctx.session_id,    # 本次会话凭据
}
return await run_agent(                      # 交给下一层执行，并等待它的结果
    sb, workdir=ctx.workdir, start_cmd=cmd, env=env, time_budget_sec=time_budget_sec
)
```

这里的 `/usr/local/bin/claude` 是已经安装在沙箱中的 Claude Code 命令行程序；`-p` 后面是任务提示。它相当于接下来要在沙箱的终端里执行的一条命令。

**写出 cmd 字符串、构造 env 字典时，Claude 还没有启动。** `launch_and_wait` 随后调用 `run_agent`，自己等着它返回。

**3．进入 run_agent，再进入 exec_and_wait：真正把程序启动起来。**

`run_agent` 先准备 `.harness` 输出目录，然后调用 `exec_and_wait`。这一层把 `start_cmd` 原样作为 `cmd` 传下去，也传下去环境变量和工作目录。

`exec_and_wait` 接着按顺序：

1. 把这条 Claude 命令写进一个沙箱内的启动脚本；脚本在命令退出后，会把退出码写入完成标记文件。
2. 调用 `sb.exec(...)`，在沙箱后台启动这个脚本；脚本开始执行其中的 Claude 命令。
3. 启动命令返回后，进入 `_await_done_marker`，反复检查完成标记，等待 Claude 这次运行结束。

第 2 项对应源码中的这次调用，保留实际参数与命令：

```python
await sb.exec(
    f"chmod +x {launcher}; "
    f"mkdir {lock_dir} 2>/dev/null || exit 0; "
    f"setsid bash {launcher} < /dev/null > {out_file} 2>&1 &",  # 在后台执行启动脚本
    user=user,
    env=env,                # 前面准备的 API 地址在这里交给所启动的程序
    timeout=30,
    check=True,
    idempotent=True,
)
exit_code = await _await_done_marker(        # 启动成功后，继续等整条命令退出
    sb, done_file, user=user, time_budget_sec=time_budget_sec
)
```

`sb` 是操作沙箱的接口，`sb.exec` 负责让沙箱执行命令。这里需要分清两个时刻：**后台启动命令返回了，Claude 程序还在运行。** 所以 `exec_and_wait` 还要继续等退出标记，上层的 `run_agent`、`launch_and_wait`、`run` 也都还没完成。

<a id="http-request-order"></a>

**4．现在停住 Python 主线，看看同时运行的 Claude 在做什么。**

这时 Claude 已经拿到了任务提示、工作目录和环境变量。它运行到需要模型回复的地方，会使用自己内部的 HTTP 客户端向 `ANTHROPIC_BASE_URL` 指定的地址发送模型请求，路径是 `/v1/messages`。这个地址正是前面传下来的 Adapter 地址。

所以，“下一步发送 HTTP”发生在**已经启动的 Claude 程序内部**。Slime 这边仍在等待它退出。CLI 内部构造请求、调用 HTTP 客户端的具体函数不在上述 Python 源码里；本步没有检查对应安装包，不能补写一个虚构的发送函数。

Claude Code 的[环境变量文档](https://code.claude.com/docs/en/env-vars)说明了 API 地址的配置，[网关协议文档](https://code.claude.com/docs/en/llm-gateway-protocol#api-formats)说明了 `/v1/messages` 接口；[`-p` 参数文档](https://code.claude.com/docs/en/cli-reference)说明了非交互运行方式。这里用这些接口说明连接外部程序的行为，不把它当作本次实际运行日志。

**5．Adapter 收到这个 HTTP 请求，才进入 _run_turn。**

Adapter 启动时已经执行过下面的路由注册：

```python
app.router.add_post("/v1/messages", self._run_turn)  # 收到此路径的 POST 时，交给这个处理器
```

注册只是先记下处理规则。现在请求到达，Web 服务按规则执行 `self._run_turn(request)`，实际实现来自 `BaseAdapter`。其中：

```python
body = await request.json()  # 从收到的 HTTP 请求中读取 JSON 数据
```

后面才会走到已有记录中的 `self._translate(body)`。它的输入来自收到的请求。

在 Adapter 处理这次请求时，三边的状态是：

| 执行位置 | 此刻在做什么 |
| --- | --- |
| Slime 的 `run` 调用这一侧 | 通过下层等待逻辑，等 Claude 整次运行结束 |
| 沙箱里的 Claude 程序 | 等这一轮模型请求的 HTTP 响应，收到后继续任务 |
| Adapter 服务 | 执行 `_run_turn`，处理这一个模型请求 |

Adapter 服务运行在单独的服务线程，能在主线等待期间处理请求。**收到一次 HTTP 响应，只让 Claude 继续运行；不会让 run 立刻结束。** Claude 后续需要模型回复时，还可以再次请求 Adapter。

**6．等 Claude 整体退出，才沿原来的调用层层返回。**

正常结束时，启动脚本写下退出码，`_await_done_marker` 读到标记；`exec_and_wait` 返回退出码和输出，`run_agent` 取出退出码，再经 `launch_and_wait`、`run` 返回给 `generate`：

```python
agent_exit_code = await HARNESS_CLS().run(...)  # 到这时，这一行才拿到退出码；调用参数省略
diff_text = await swe.git_diff(...)            # generate 然后继续下一句；调用参数省略
```

可以沿这个具体过程回看：`run` 准备用户和配置，逐层调用到沙箱命令启动；Claude 在沙箱里执行任务并请求模型；Adapter 收到请求后处理；Claude 整体退出后，`run` 才交回结果。当前只展开到 HTTP 处理入口与返回方向，模型生成和 CLI 工具循环仍留待对应问题。

### 关键数据交接

| 交接 | 传递的关键内容 | 下一段为什么会执行 |
| --- | --- | --- |
| `run → launch_and_wait` | 运行上下文 `ctx`、任务提示 `prompt` 与时间预算 | `run` 调用具体 Harness 的启动方法；`ctx` 携带 Adapter 地址和会话标识 |
| `launch_and_wait → run_agent → exec_and_wait` | CLI 命令 `cmd`、环境变量 `env`、工作目录等 | 启动方法把命令交给沙箱执行；等待逻辑跟踪该命令的结束 |
| `Claude CLI → Adapter` | 发往 `/v1/messages` 的 HTTP 请求及 JSON 请求体 | CLI 使用配置的 API 地址；Adapter 已将该路径注册给 `self._run_turn` |

连接两端最关键的数据是地址和会话标识：

```text
adapter_url → ctx.adapter_url → env["ANTHROPIC_BASE_URL"]
session_id  → ctx.session_id  → env["ANTHROPIC_AUTH_TOKEN"]
```

这解释了 CLI 从哪里得到请求地址。接收端的 `app.router.add_post("/v1/messages", self._run_turn)` 决定请求进入哪个处理器；处理器再通过 `await request.json()` 取得请求体。

以上按默认环境配置关系说明；`SLIME_AGENT_CC_EXTRA_ENVS` 可以覆盖这些环境变量，实际使用额外配置时需要重新核对地址和会话值。

### 请求完成与 CLI 结束，是两次不同的交接

一次模型请求的 HTTP 响应交回 CLI，CLI 可以继续运行。响应的具体生成过程不在本步展开。

等 CLI 整体结束后，`exec_and_wait` 返回退出码和输出；`run_agent` 取出退出码，经 `launch_and_wait`、`run` 返回给 `generate` 的 `agent_exit_code`。此后外层才继续收集代码 diff。这里补充返回方向，用于区分“一次请求完成”和“Agent 整次运行结束”。

</details>

### 此前追到请求入口时补上的关系与边界

相对前一步的外层骨架，本步补上的是：**启动调用进入外部 CLI；运行中的 CLI 通过 HTTP 触发 Adapter 请求处理；CLI 结束后，退出码才返回外层任务。**

目前保留的展开边界：

- 运行用户和配置先交代作用与返回位置；沙箱已展开到写启动脚本、后台启动和等待退出标记，重试保护、进程隔离和轮询实现暂不展开。
- CLI 内部怎样组织多轮模型请求与工具执行，尚未追踪其内部实现。
- Adapter 的创建、监听与 HTTP 请求响应已定位；线程生命周期细节、会话匹配、超时和取消，按后续具体问题展开。
- `_run_turn` 内部的转换与模型生成不在本轮展开；本轮只补充其输入来自请求、输出通过 `_respond` 返回。需要理解转换时，可复用已有的 `_translate` 函数记录。

</details>

## 7. 复用记录与来源

函数自身的场景、输入输出和认识保留在对应记录中：

- [BaseAdapter._run_turn](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md)：请求编排器的总输入输出与子函数之间的交接；全部单函数入口见[本步索引](../02-short-term-memory/overview.md)。
- [BaseHarness.run](../02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md)：启动流程的单函数记录。
- [BaseAdapter._translate](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md)：此前积累的转换模型；具体 Anthropic 场景由该共同记录覆盖。
- [Step 1 的原始问题与澄清](../04-flow.md#从启动到请求入口)：保存问题和理解修正的过程。

<details>
<summary>固定版本、源码定位与验证边界</summary>

- 整理日期：2026-10-20；2026-10-21 按已读的 `_run_turn` 请求链补充交接与收束边界。
- 源码根目录：`/home/hongshi/projects/slime`。
- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- 本页为静态源码核对，没有运行 CLI、沙箱或模型服务。

| 核对内容 | 源码定位 |
| --- | --- |
| Harness / Adapter 的分支选择、调用入口 | `examples/coding_agent_rl/generate.py:45–52、205–213` |
| 已启动的 Adapter 服务及对外地址 | `examples/coding_agent_rl/generate.py:138–171` |
| 上下文、委派启动与退出码返回 | `slime/agent/harness/common.py:43–54、81–122` |
| CLI 命令、地址、会话与额外环境配置 | `slime/agent/harness/claude_code.py:15、57–71` |
| HTTP 路由与处理器读取请求体 | `slime/agent/adapters/anthropic.py:39–49`；`slime/agent/adapters/common.py:318–327` |
| 沙箱命令启动与结果返回 | `slime/agent/sandbox.py:82–145` |
| 本轮请求的真实调用与记录顺序 | [common.py:318–393](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L318-L393) |
| SGLang 请求与 TurnRecord 返回 | [common.py:442–514](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L442-L514) |
| 两个协议的路由与具体钩子 | [anthropic.py:39–75](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/anthropic.py#L39-L75)、[openai.py:38–73](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/openai.py#L38-L73) |
| manager 接收的数据与树节点 | [trajectory.py:283–305](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L283-L305)、[437–454](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/trajectory.py#L437-L454) |
| inflight 的后续使用方 | [common.py:225–243](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L225-L243) |

已有[源码核对记录](../../../../../../../../slime_photo/code-reading/chapters/01-task-execution/SOURCE-CHECK.md)与[完整连接讲解](../../../../../../../../slime_photo/code-reading/chapters/01-task-execution/walkthrough.md#harness-to-adapter)可供回查。函数间的关系来自上述调用、配置和路由；CLI 内部的请求组织未在本步验证。

</details>
