# Step 007 · 本步短期记录

只索引本步实际使用的函数。前序资料完整保存在 03，本步只调取需要接续的部分。

| 函数 | 本步记录范围 |
| --- | --- |
| [blackbox_dispatch.generate](functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md) | 从前序调取；当前片段为 after_agent 与会话收尾，后续读取仅作定位 |
| [execute_blackbox_cmds_for_stage](functions/dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md) | 从前序调取；当前按用户指定逐步看 after_agent 的命令选择与执行 |
| [_execute_blackbox_cmd](functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md) | 从前序调取；当前只读一条命令的发送与等待，后续记录和失败判断保留 |
| [BlackboxAgentPaddock.execute_cmd](functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.execute_cmd.md) | 本轮单独建卡；定位已有沙箱、转交 shell 命令并返回结果 |
| [BlackboxServerClient.execute_cmd](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.execute_cmd.md) | 组织命令正文、发送 POST、解析回复，返回上层 cmd_result |
| [api.sessions.execute_cmd](functions/blackbox_server/api/sessions.py/execute_cmd.md) | 服务端接收命令、委派执行并补请求标识后回复 |
| [BlackboxServer.execute_cmd](functions/blackbox_server/core/server.py/BlackboxServer.execute_cmd.md) | 检查会话、锁内等待 shell 执行、封装结果返回路由 |
| [execute_shell_command](functions/blackbox_server/core/command.py/execute_shell_command.md) | 已看启动与等待；当前移除登记、解码输出并返回 ExecuteCmdResult |
| [ProxyClient.finalize_session](functions/dressage/proxy/proxy_client.py/ProxyClient.finalize_session.md) | 从备用材料调入；当前看收尾请求、会话标识与响应，服务端内部待展开 |
| [Proxy 服务端 create_app.finalize_session](functions/dressage/proxy/server.py/create_app.finalize_session.md) | 简读：构建并发布轨迹、结束活跃会话、清理上下文、返回收尾摘要 |
| [StepRecord](classes/dressage/proxy/session_manager.py/StepRecord.md) | 类卡：一次模型交互、拼接材料、归属与边界；附两次生成的简化示例 |
| [Session](classes/dressage/proxy/session_manager.py/Session.md) | 类卡：get_session 查回对象；分段输入的 steps、lineages 与路径归属 |
| [_split_session_into_lineage_segments](functions/dressage/proxy/server.py/_split_session_into_lineage_segments.md) | 按已有 lineage 分组，再按 boundary 标记切段；保留 StepRecord 引用 |
| [create_app._build_tito_lineage_segment_record](functions/dressage/proxy/server.py/create_app._build_tito_lineage_segment_record.md) | 一段 steps 的 token/mask/logprob 组合、归属信息与 record 返回；当前接清后半段 |
| [ProxyClient.read_trajectory](functions/dressage/proxy/proxy_client.py/ProxyClient.read_trajectory.md) | 按轨迹 ID 取回段列表；当前 drain=True，响应交给 trajectory_payload |
| [Proxy 服务端 create_app.trajectory_read](functions/dressage/proxy/server.py/create_app.trajectory_read.md) | 当前指定轨迹、drain=True 分支：委派存储取出并移除，回复段列表与状态 |

[scope](../01-scope.md#reading-navigation) · [前序累计](../03-long-term-memory/overview.md) · [Step 007 过程](../../step-007-proxy-finalization-and-trajectory/04-flow.md#start-step007)
