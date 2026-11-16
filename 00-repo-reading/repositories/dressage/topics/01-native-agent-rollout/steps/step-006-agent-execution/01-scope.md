# 01 · Dressage Step 006：题目怎样交给 Agent，结果怎样返回

[本步入口](README.md) · [前一步总结](../step-005-agent-registration/05-task-flow.md) · [短期记录](02-short-term-memory/overview.md) · [项目进度](../../../../README.md)

## 1. 阅读目标

**看清一次 call_agent 怎样使用已有环境与会话，把题目消息交给 Agent，并将结果交回 generate。**

1. 先区分发送题目、服务端接受任务、最终执行完成这几个时刻。
2. 追踪 messages → 客户端请求 → 服务端执行 → call_payload 的交接。
3. 回到 generate，定位 agent_response 怎样由 call_payload 得到。
4. 2026-11-14 新增补读：在 CLI 运行期间追一条模型请求的协议转换、生成、单步记录与响应回程，入口仍在第 9 项内部。

这一步继续原生 blackbox generate 的收尾，不切换到 Harbor，也不重读前一步的安装、注册与前置命令。

## 2. 当前入口与停止位置

从 [generate:259](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L259) 的调用进入 **BlackboxAgentPaddock.call_agent**。本步以 generate 的执行段组织主线，call_agent 是第一处具体入口。

前一步已经给出 paddock、state、session_id，完成 Agent 注册、before_agent 与 Proxy 会话登记。sample.prompt 仍是本次题目的来源。

选择首次调用、正常成功返回的路径，Agent 以 Claude Code 为例。客户端默认 `DRESSAGE_BLACKBOX_AGENT_CALL_MODE=async`，先提交再查询完成结果；sync 分支先只作定位。

**停止在 generate:283–291 的成功结果处理，进入 after_agent:293 之前。** 这里取得的是调用结果，不是最终训练 Sample。后续失败分类、轨迹收尾与资源释放保留位置，按实际问题再展开。

原首轮已按当时范围收束，交接关系见[任务链路总结](05-task-flow.md)；下面保留旧路径与停止位置。2026-11-14 的模型请求补读是新增范围，目前未完成，未知继续留在对应记录中。

## 3. 整体位置与本步阅读

<a id="whole-flow"></a>

### 3.1 本步在 generate 中的位置

下面是正常路径的教学骨架，保留完整主线。省略配置、异常包装和检查；环境部分只示意预热未命中路径。编号只标正式 Step 范围，不把本步内部阅读顺序混进来。

```python
session_id = ensure_blackbox_session_id(...)
instance_id = _instance_id(...)
env_args = paddock_env_args_from_metadata(...)
initialized = False
paddock = None
try:
    proxy_client = get_proxy_client(...)
    handle = await claim_prewarm(...)
    ...  # 此图选择未命中路径；省略身份更新等处理。
    paddock = get_paddock_from_env(...)
    state = await maybe_await(paddock.init(...))
    initialized = True

    # Step 005：注册和执行前准备，首轮已收束。
    await maybe_await(paddock.register_agent(...))
    await execute_blackbox_cmds_for_stage(...)  # before_agent
    register_session_context = getattr(proxy_client, "register_session_context", None)
    if callable(register_session_context):
        context_owned = True
        await maybe_await(register_session_context(...))

    # Step 006：当前，把题目交给 Agent，等待并取得结果。
    call_payload = await maybe_await(paddock.call_agent(...))
    agent_response = agent_response_text(call_payload)

    # 后续：执行后处理、导出轨迹和构造 Sample。
    await execute_blackbox_cmds_for_stage(...)  # after_agent
    await proxy_client.finalize_session(...)
    trajectory_payload = await proxy_client.read_trajectory(...)
    segments = trajectory_payload.get("data") or []
    result = multi_segment.expand_segments_to_samples(...)
    return result
finally:
    if initialized and paddock is not None:
        schedule_terminate_paddock(...)
```

模型请求发生在 Agent 执行期间；后面的 read_trajectory 是取回记录。本步先定位这项关系，不在此展开 Proxy 的全部轨迹实现。

<a id="reading-navigation"></a>

### 3.2 本步调用骨架与阅读顺序

<a id="model-request-reading"></a>

**2026-11-14 补读接续**：保留原首轮记录，从第 8 项 [send_message 的 CLI Task 调用](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md#launch-cli-task)进入第 9 项；在 [_run_claude_turn 第 2 段后](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#model-request-during-cli)跨 HTTP 进入 9.1–9.2。当前已讨论 _handle_proxy 的转换/归属主干；2026-11-15 已定位实际发送语句，当前进入 9.2b 的 _chat_completions_pipeline，先看请求内容与 session/turn 归属，后续阶段待逐段展开。

本轮选一个**有效的 Anthropic 请求、stream=True、正常生成成功**的阅读场景；这是选定分支，不是已抓取到真实 CLI 请求。只追一次请求的去程、单步记录和响应回程，不通读全部协议、抢占、版本恢复或上下文重写算法。

**先看调用处已有的材料。** 以下来自 generate 的正常成功路径，省略中间的异常分支：

```python
call_payload = await maybe_await(
    paddock.call_agent(                            # 本步第一处入口
        state,                                    # 前一步交回的环境访问资料
        session_id=session_id,                    # 本次会话
        messages=_chat_messages_from_prompt(sample.prompt),  # 题目整理成消息
        metadata={"source": "dressage", **metadata},
    )
)
call_succeeded = True

if call_succeeded:
    agent_response = agent_response_text(call_payload)  # 返回后的结果整理
    ...  # 原函数还检查结构化失败状态。
```

**从 paddock.call_agent 进入 Paddock。**

```python
state = self._resolve_state(state)                  # 使用已有 state
return await self._client.call_agent(               # 委派给客户端
    self._endpoint_for_state(state, self._leases.get(state.trajectory_id)),
    trajectory_id=state.trajectory_id,
    session_id=session_id,
    messages=messages,
    metadata=metadata,
    turn_id=turn_id,
)
```

下面分开画客户端提交链与服务端后台链，使用 Python 高亮显示注释，并非可执行程序。create_task 安排后台执行；HTTP 202 的返回不需要等待后台任务完成。

```python
# 客户端提交链：先收到提交回复，再通过查询等待结果。
BlackboxAgentPaddock.call_agent  # 确定沙箱入口，转交题目资料
  -> BlackboxServerClient.call_agent
       -> BlackboxServerClient._post_agent_with_retry  # 组合地址，交给公共函数发送
            -> POST /v1/sessions/{session_id}/messages  # 默认 mode=async
       == HTTP ==> api.sessions.send_message
                    -> BlackboxServer.submit_turn
                         -> create_task(server._run_turn(...))  # 安排下面的后台链，不在此等待它结束。
                    <- submission
       <== HTTP 202 ==  # _post_agent_with_retry 把 HTTP 响应交回 call_agent。
       -> BlackboxServerClient._poll_turn  # call_agent 接着查询；可与后台执行同时进行。
            -> BlackboxServerClient._get_turn_with_retry  # 补上重试设置。
                 -> get_json_with_retry  # 公共 HTTP 层执行 GET 和重试。
                      -> GET /v1/sessions/{session_id}/turns/{turn_id}
            # queued/inflight 继续等待；committed 取回后台保存的结果。
       <- call_payload  # 这里才是执行结果，不是最初的 HTTP 202。
  <- call_payload  # 逐层返回 generate
agent_response_text(call_payload)  # 将结果整理成字符串
```

```python
# 服务端后台链：在自己的 Task 中执行，结果保存在服务端记录里。
BlackboxServer._run_turn
  -> ClaudeCodeAdapter.send_message
       -> [9] ClaudeCodeAdapter._run_claude_turn
            -> create_subprocess_exec(...)  # 第 2 段：启动 CLI。
            # 运行期间的两项工作可以交错进行：
            # 外部 CLI == HTTP ==> [9.1] _build_app 内的 _proxy -> [9.2] _handle_proxy
            # 响应先回 CLI；[9.3] 本 Python 协程同时读取 stdout，最后等待进程退出。
       <- outputs, trace_events, usage  # 经等待器交回 send_message。
  <- AdapterResponse  # send_message 收尾后，经等待器交回 _run_turn。
  # _run_turn 保存结果、设置 Event、移除活跃登记，后台 Task 结束。
  # 它返回 None；执行结果不会沿最初的 POST 请求返回。
```

`async` 指这里的提交协议，不表示 Python 调用方发出任务就结束。外层 await call_agent 仍要等待客户端返回调用结果。

<a id="reading-sequence"></a>

**上方图表达执行关系，下表数字只表示阅读顺序。** 数字不表示调用深度，也不表示并发代码的运行先后。进入、返回、跨 HTTP 和切换后台任务的关系写在“从哪里进入”一列；同一函数在不同位置出现时，分别列为阅读步骤，通过函数名和链接对应源码。

| 阅读顺序与入口 | 从哪里进入 | 读到哪里停、返回哪里 |
| --- | --- | --- |
| 1. BlackboxAgentPaddock.call_agent | generate:259；[本步函数卡](02-short-term-memory/functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.call_agent.md) | 看清 state/endpoint、messages 和返回字典；下一行进入客户端 call_agent |
| 2. BlackboxServerClient.call_agent | 直接调用：Paddock.call_agent 的委派；[本步函数卡](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.call_agent.md) | 看清先提交、再查询两个动作；从 _post_agent_with_retry 调用处进入下一行，提交后的代码留待切回客户端时续读 |
| 3. BlackboxServerClient._post_agent_with_retry | call_agent:117；[本步调取的函数卡](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._post_agent_with_retry.md) | 对齐 messages 路径、请求正文和 HTTP 响应；下一行沿 HTTP 请求找到服务端接收函数 |
| 4. api.sessions.send_message | 跨 HTTP：POST messages 对应的 [api.sessions.send_message 函数卡](02-short-term-memory/functions/blackbox_server/api/sessions.py/send_message.md) | request_scope 的请求计数作最小前置，随后进入 submit_turn |
| 5. BlackboxServer.submit_turn | 路由委派的 [BlackboxServer.submit_turn 函数卡](02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer.submit_turn.md) | 先看首次提交如何登记、创建 Task 和返回，再回到路由的 submission；重复/冲突保留必要边界 |
| 6. 返回客户端：提交回复 | 路由根据 submission 返回 HTTP 202；_post_agent_with_retry 将响应交回 [客户端 call_agent](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.call_agent.md) | 确认提交链在此收到回复，不需要等待 Agent 做完。记住客户端下一行要读 submit_response；为弄清结果来源，阅读先切到下面的后台链 |
| 7. 切到后台：BlackboxServer._run_turn | 切到后台 Task：submit_turn 创建的任务运行 [BlackboxServer._run_turn](02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md) | 看第 1 段标记执行中，第 2 段调用适配器；从 send_message 调用处进入下一行 |
| 8. ClaudeCodeAdapter.send_message | 直接调用：_run_turn 委派给 [ClaudeCodeAdapter.send_message](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md#launch-cli-task) | 取题目、准备会话；到第 3 段创建 CLI Task 时进入下一行 |
| 9. ClaudeCodeAdapter._run_claude_turn：先到启动位置 | 从 [send_message 的 Task 调用](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md#launch-cli-task) 进入 [_run_claude_turn 第 1–2 段](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#prepare-process) | 接清参数、代理地址和进程启动；从第 2 段后的补读入口进入 9.1，输出收集与最终返回在 9.3 接回 |
| 9.1. 跨 HTTP：Proxy 接收入口 · 补读定位 | 从 [_run_claude_turn 的 CLI 运行位置](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#model-request-during-cli) 切到 [_build_app 内的 _proxy](02-short-term-memory/functions/blackbox_server/proxy/rollout_llm_proxy.py/RolloutLLMProxy._build_app._proxy.md#proxy-http-entry)；当前已建卡 | 看接收函数如何委派 _handle_proxy；这是外部 CLI 发出的请求，不是 Python 直接子调用 |
| 9.2. RolloutLLMProxy._handle_proxy · 已讨论主干 | [_handle_proxy 函数卡](02-short-term-memory/functions/blackbox_server/proxy/rollout_llm_proxy.py/RolloutLLMProxy._handle_proxy.md#handle-proxy-map)，由上一行 HTTP 入口委派 | 先确认 Anthropic → OpenAI 请求转换与直接上游；在第 3 段进入下面的发送路径，不能直接跳过上游生成回到 9.3 |
| 9.2a. 转发出口 · 只认发送职责 | 从 [_handle_proxy 第 3 段](02-short-term-memory/functions/blackbox_server/proxy/rollout_llm_proxy.py/RolloutLLMProxy._handle_proxy.md#handle-proxy-forward) 进入 [_stream_anthropic_messages_proxy 发送段](02-short-term-memory/functions/blackbox_server/proxy/rollout_llm_proxy.py/RolloutLLMProxy._stream_anthropic_messages_proxy.md#send-upstream)；其下一层 _send_stream_request:1445 尚未建卡 | 按用户最新深度要求，只认这层发出已整理的 HTTP 请求，不再单独深入 _send_stream_request；接到 9.2b 的外部 Proxy 处理主线 |
| 9.2b. 上游接收与处理主线 · 当前 | [chat_completions 接收入口](02-short-term-memory/functions/dressage/proxy/server.py/create_app.chat_completions.md#chat-completions-entry)（[响应模式对照](02-short-term-memory/functions/dressage/proxy/server.py/create_app.chat_completions.md#response-modes)）→ [_chat_completions_pipeline 完整主线](02-short-term-memory/functions/dressage/proxy/server.py/create_app._chat_completions_pipeline.md#pipeline-overview) | 接同一份 OpenAI 请求，定位 session/turn、messages 到 input_ids 的准备与生成委派；完整卡已按选定正常路径补齐六段；先理解全程，再按需深入辅助函数 |
| 9.2c. 模型后端调用 · 当前 | [GenerationController.generate_preemptible：正常生成](02-short-term-memory/functions/dressage/proxy/generation_controller.py/GenerationController.generate_preemptible.md#generation-mainline) → _generate_with_optional_request_id:675 → SGLangRouterClient.generate:176；后两者在主卡中定位，不另建卡 | 保留真实委派，先只看一次正常生成，确认 input_ids/sampling_params、/generate 与返回对象；抢占恢复、兼容参数枚举暂缓 |
| 9.2d. 回流水线：记录这一次交互 · 待读 | 回 _chat_completions_pipeline:2198 接生成结果，再到 :2479 的 _record_step_atomically（定义 :1137）；待建卡 | 看生成结果怎样进入本次 StepRecord，以及如何组织 OpenAI 响应；单步记录写入按必要深度回查，不进入会话 finalize 或 Sample 转换 |
| 9.2e. 回本地 Proxy：响应交回 CLI · 待读 | 回 [_stream_anthropic_messages_proxy 的响应段](02-short-term-memory/functions/blackbox_server/proxy/rollout_llm_proxy.py/RolloutLLMProxy._stream_anthropic_messages_proxy.md#response-return)，再回 _handle_proxy / _proxy | 接上游响应流，读选定 Anthropic 响应转换与返回；流式 Response 的数据由生成器后续发送，不把返回响应对象当成流已读完。响应回 CLI 后再进入 9.3 |
| 9.3. 返回 _run_claude_turn：输出与结果 | 接回 [第 3 段](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#read-stdout)与[第 4 段](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md#return-result) | 继续理解读取 stdout、等待退出和整理三项结果，再回第 10 项 send_message。实际读取与 CLI 请求可交错，本行表示阅读返回 |
| 10. 返回 send_message：适配器收尾 | 从 CLI 返回 [ClaudeCodeAdapter.send_message 第 3 段下半部分](02-short-term-memory/functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md#receive-cli-result) | await 接住三项结果 → 第 4 段代理收尾、组织 AdapterResponse → finally 完成后返回下一行的 _run_turn 第 2 段末尾 |
| 11. 返回 _run_turn：接住结果 | 从 send_message 回到 [BlackboxServer._run_turn 的 await 赋值处](02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md#receive-adapter-result) | adapter_response 接住返回对象，outcome 暂存成功结果；沿正常路径继续同一函数的第 3 段，即下一行 |
| 12. 继续 _run_turn：保存与收尾 | 接着读 [BlackboxServer._run_turn 第 3 段](02-short-term-memory/functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md#save-result-and-notify)，从 async with session_lock 开始 | 锁内取得 record、保存结果并标记 COMMITTED → 锁外 Event 通知 → 确认仍是当前 Task 后移除活跃登记。后台链在这里结束，不把结果返回最初的 POST |
| 13. 切回客户端 call_agent：提交之后 | 回到 [BlackboxServerClient.call_agent](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.call_agent.md) 的 submit_data = submit_response.json() | 接回前面记住的提交回复位置，读取重复提交标记，再调用下一行的 _poll_turn。这是阅读切换，不是 _run_turn 调用客户端 |
| 14. BlackboxServerClient._poll_turn | 直接调用：[BlackboxServerClient._poll_turn](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md)；从上一行客户端 call_agent 的委派进入 | 准备同一次调用的查询地址；从循环里的 _get_turn_with_retry 进入下一行 |
| 15. BlackboxServerClient._get_turn_with_retry | 直接调用：从 _poll_turn 的 GET 查询进入[本函数卡](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._get_turn_with_retry.md) | 补上重试配置，委派公共 GET 函数，返回 HTTP 响应；区分请求失败重试与 Agent 未完成后继续轮询，然后返回下一行 |
| 16. 返回 _poll_turn：读取状态 | 从 GET 方法返回 [_poll_turn 的 response.json()](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md#parse-query-response) | 读取 status；未完成继续查询，失败报错。当前沿 committed 成功分支进入下一行 |
| 17. BlackboxServerClient._committed_call_payload | 直接调用：_poll_turn 成功分支进入[本函数卡](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md) | 从查询回复中选取标识、输出、后端和用量字段，加上重复提交标记；返回结果字典 |
| 18. 返回 _poll_turn 与 call_agent | 回到 [_poll_turn 成功分支的 return](02-short-term-memory/functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md#return-call-payload) | 轮询结束，结果经客户端 call_agent、Paddock.call_agent 返回；generate 的 call_payload 接住字典 |
| <a id="current-reading"></a>**19. 回到 generate：本步停止位置** | 返回 [generate 本步卡的调用结果段](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#return-agent-result)，对应源码 283–291 行 | call_payload 已接住结果；看 agent_response_text 的实际取值及结构化失败检查。当前返回结构会转成整个字典的字符串；读到 after_agent 之前停 |

<a id="model-request-route"></a>

**第 9 项内部的补读主线**（阅读次序，不是每一行都直接调用下一行）：

```text
_handle_proxy：转换请求
  → 9.2a 本地 Proxy 的 HTTP 发送点
  == HTTP ==> 9.2b Dressage Proxy 接收、准备本次生成
                → 9.2c 生成控制器 → SGLang 客户端 → 模型后端
                ← 9.2d 接生成结果，记录一步交互并组织响应
  <== 响应 == 9.2e 本地 Proxy 转成 Anthropic 响应，交回 CLI
  → 9.3 阅读回到 _run_claude_turn 的输出收集与退出
```

流式请求中，响应头或心跳可能在模型生成完成前到达；上图按模型结果的去程和回程组织阅读，不承诺所有动作按图串行阻塞。

**补读停止边界**：一条正常请求已从 CLI 经两层 Proxy 到模型后端，本次交互记录的位置可定位，响应回到 CLI。Proxy 启动仍按 Step 005 回查；会话结束后的分段、发布与读取仍属 Step 007；Sample 转换属 Step 008；资源回收与完整失败恢复保持原有边界。未读函数只列源码位置，不预建卡或写成已掌握。

[补读展开前的 scope](references/history/2026-11-14-before-model-request-expansion.md)保留原表；原第 10–19 项及首轮记录不重新编号。

返回同一函数的不同段落会占用新的阅读序号，但仍链接原函数卡，不新增一份函数。后台 Task 的结束与客户端 HTTP 回复属于不同的交接。

本步已展开的函数见 [02 索引](02-short-term-memory/overview.md)，其中 _post_agent_with_retry 由前序调取，其余随实际阅读建立。未展开的调用只保留源码导航，不据此登记为已读或已掌握。前序 03 完整保留，当前 02 只调入实际用到的旧记录。

<details>
<summary>源码与证据边界</summary>

- 固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 默认提交模式由 client.py 的 _DEFAULT_CALL_MODE 定义为 async；环境变量可选择 sync，后者本轮暂不展开。
- 32 份前序函数/类记录的来源保存在 [03 索引](03-long-term-memory/overview.md)及各卡片中；继承不改变认识时间。
- 仅静态源码与阅读记录核对，未发送请求、运行 Agent 或验证性能。

</details>
