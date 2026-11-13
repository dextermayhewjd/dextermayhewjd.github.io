# Step 005 · 重新阅读的短期记录

旧卡按用户要求移出当前目录；这里只收录本轮重新展开的记录。

本步首轮总结见 [task flow](../05-task-flow.md)。单个函数的原话、未确认细节及深入边界继续保留，不因本步收束而统一标成已掌握。

| 当前记录 | 范围与状态 |
| --- | --- |
| [BlackboxAgentPaddock.register_agent](functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md) | 保留完整函数，本轮展开 state → lease → endpoint，并补充两个 URL 的方向；待用户反馈 |
| [BlackboxServerClient.register_agent](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md) | 本轮新建，组装请求、发送并接收回复；待用户反馈 |
| [BlackboxServerClient._post_agent_with_retry](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._post_agent_with_retry.md) | 短读 URL、正文、请求头与 HTTP 响应交接；重试内部暂不展开 |
| [register_rollout](functions/blackbox_server/api/rollout.py/register_rollout.md) | 接收 HTTP 注册请求，委派服务对象并返回；下一处为 BlackboxServer.register |
| [BlackboxServer.register](functions/blackbox_server/core/server.py/BlackboxServer.register.md) | 已补 initialize 返回后的保存、会话准备与响应，接回 generate |
| [ClaudeCodeAdapter.initialize](functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.initialize.md) | 已对应 Context 字段与目录、配置文件、本地代理的准备；原话和未知保留 |
| [execute_blackbox_cmds_for_stage](functions/dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md) | 本轮新建，按阶段顺序执行已有命令计划；尚待理解反馈 |
| [_execute_blackbox_cmd](functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md) | 已按发送、记录、失败判断说明一条命令；保留用户表述与未确认细节 |
| [ProxyClient.register_session_context](functions/dressage/proxy/proxy_client.py/ProxyClient.register_session_context.md) | 向外部 Proxy 登记会话；用户已认可简洁模型并表示差不多理解，路由内部保留为按需内容 |

[scope 3.2](../01-scope.md#reading-navigation) · [前序长期记忆](../03-long-term-memory/overview.md) · [旧卡历史](../references/history/restart-from-callsite-2026-11-06/README.md)。未恢复其他旧卡。
