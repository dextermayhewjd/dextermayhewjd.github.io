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

[scope](../01-scope.md#reading-navigation) · [前序累计](../03-long-term-memory/overview.md) · [Step 006 过程记录](../04-flow.md)
