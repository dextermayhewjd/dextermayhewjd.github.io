# Step 006 · 本步短期记录

只保存本步实际展开的函数；后续调用先在 scope 中定位。

| 记录 | 本次范围 |
| --- | --- |
| [BlackboxAgentPaddock.call_agent](functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.call_agent.md) | 用户已概括 state 环境资料交给客户端使用；保留输入、返回与前序理解 |
| [BlackboxServerClient.call_agent](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.call_agent.md) | 当前展开：准备调用编号、提交消息、等待最终结果；尚待理解反馈 |
| [BlackboxServerClient._post_agent_with_retry](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._post_agent_with_retry.md) | 本步从 03 调取，主视图更新为发送题目消息；完整注册场景和原始来源保留在折叠区 |
| [api.sessions.send_message](functions/blackbox_server/api/sessions.py/send_message.md) | 当前服务端接收入口：委派 submit_turn 并返回 HTTP 202；尚待理解反馈 |
| [BlackboxServer.submit_turn](functions/blackbox_server/core/server.py/BlackboxServer.submit_turn.md) | 当前展开首次提交：登记调用、创建后台 Task、返回提交记录；与请求计数包装分开理解 |
| [BlackboxServer._run_turn](functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md) | 后台入口：标记执行、调用适配器、保存结果并通知；未知继续保留 |
| [ClaudeCodeAdapter.send_message](functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md) | 用户已概括会话、题目与等待的关系；细节和未知保留 |
| [ClaudeCodeAdapter._run_claude_turn](functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md) | 启动参数、进程、输出与退出结果；用户表示大概理解，具体未知保留在卡片 |
| [BlackboxServerClient._poll_turn](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md) | 已接回客户端提交后的查询位置；用户确认继续阅读，复用已有卡片，尚待理解反馈 |
| [BlackboxServerClient._get_turn_with_retry](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._get_turn_with_retry.md) | 本轮按用户指定展开：补重试设置、委派 GET、返回 HTTP 响应；区分请求重试与状态轮询 |
| [BlackboxServerClient._committed_call_payload](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md) | 已按用户请求建卡：选取查询回复字段，整理为上层调用结果字典；尚待理解反馈 |
| [blackbox_dispatch.generate](functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md) | 从 03 调入完整前序记录；当前只看调用返回、结果字符串整理与结构化失败检查 |
| [RolloutLLMProxy._build_app 内的 _proxy](functions/blackbox_server/proxy/rollout_llm_proxy.py/RolloutLLMProxy._build_app._proxy.md) | 2026-11-14 补读：CLI 的 HTTP 接收入口，委派 _handle_proxy；未展开转换内部 |
| [RolloutLLMProxy._handle_proxy](functions/blackbox_server/proxy/rollout_llm_proxy.py/RolloutLLMProxy._handle_proxy.md) | 2026-11-14 当前补读：沿 Claude 分支建立识别、转换、归属与转发主干 |
| [RolloutLLMProxy._stream_anthropic_messages_proxy](functions/blackbox_server/proxy/rollout_llm_proxy.py/RolloutLLMProxy._stream_anthropic_messages_proxy.md) | 2026-11-15 当前：只进入发送段；响应处理保留回程继续 |
| [create_app.chat_completions](functions/dressage/proxy/server.py/create_app.chat_completions.md) | 2026-11-15 当前：外部 Proxy 接收 JSON，并委派生成流水线 |
| [create_app._chat_completions_pipeline](functions/dressage/proxy/server.py/create_app._chat_completions_pipeline.md) | 2026-11-15 已按要求补齐选定正常路径六段；个人理解与辅助实现仍待后续核对 |

[scope](../01-scope.md#reading-navigation) · [前序累计](../03-long-term-memory/overview.md) · [Step 006 过程记录](../04-flow.md)

- [GenerationController.generate_preemptible](functions/dressage/proxy/generation_controller.py/GenerationController.generate_preemptible.md)：正常生成的登记、后端调用、收集和返回；已展开材料，待个人反馈。

- [GenerationController._generate_with_optional_request_id](functions/dressage/proxy/generation_controller.py/GenerationController._generate_with_optional_request_id.md)：已确认单独阅读；保留调用现场、输入与返回，完整函数体及参数兼容分支已补齐，待阅读反馈。

- [SGLangRouterClient.generate](functions/dressage/proxy/sglang_client.py/SGLangRouterClient.generate.md)：组装请求、选择目标、发送与返回；用户已概括发送职责并要求返回主线；响应解析内部未展开。
