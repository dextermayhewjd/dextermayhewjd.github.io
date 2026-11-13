# Step 007 · 前序累计记录

合并 Step 006 的 32 份长期记录与 12 份短期记录，按源码路径合成 42 份；重合的 generate 和 _post_agent_with_retry 采用保留完整前序内容的较新短期版本。原话、认识时间和未知不因继承改变。

| 记录 | 本次继承来源 |
| --- | --- |
| [SandboxState](classes/dressage/paddock/blackbox/common/state.py/SandboxState.md) | Step 006 / 03-long-term-memory |
| [PrewarmHandle](classes/dressage/rollout/prewarm/store.py/PrewarmHandle.md) | Step 006 / 03-long-term-memory |
| [SandboxProvider](classes/dressage/sandbox/provider.py/SandboxProvider.md) | Step 006 / 03-long-term-memory |
| [SandboxLease](classes/dressage/sandbox/types.py/SandboxLease.md) | Step 006 / 03-long-term-memory |
| [SandboxServiceSpec](classes/dressage/sandbox/types.py/SandboxServiceSpec.md) | Step 006 / 03-long-term-memory |
| [SandboxSpec](classes/dressage/sandbox/types.py/SandboxSpec.md) | Step 006 / 03-long-term-memory |
| [ClaudeCodeAdapter._run_claude_turn](functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter._run_claude_turn.md) | Step 006 / 02-short-term-memory |
| [ClaudeCodeAdapter.initialize](functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.initialize.md) | Step 006 / 03-long-term-memory |
| [ClaudeCodeAdapter.send_message](functions/blackbox_server/adapters/claude_code.py/ClaudeCodeAdapter.send_message.md) | Step 006 / 02-short-term-memory |
| [register_rollout](functions/blackbox_server/api/rollout.py/register_rollout.md) | Step 006 / 03-long-term-memory |
| [api.sessions.send_message](functions/blackbox_server/api/sessions.py/send_message.md) | Step 006 / 02-short-term-memory |
| [BlackboxServer._run_turn](functions/blackbox_server/core/server.py/BlackboxServer._run_turn.md) | Step 006 / 02-short-term-memory |
| [BlackboxServer.register](functions/blackbox_server/core/server.py/BlackboxServer.register.md) | Step 006 / 03-long-term-memory |
| [BlackboxServer.submit_turn](functions/blackbox_server/core/server.py/BlackboxServer.submit_turn.md) | Step 006 / 02-short-term-memory |
| [BlackboxServerClient._committed_call_payload](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._committed_call_payload.md) | Step 006 / 02-short-term-memory |
| [BlackboxServerClient._get_turn_with_retry](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._get_turn_with_retry.md) | Step 006 / 02-short-term-memory |
| [BlackboxServerClient._poll_turn](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._poll_turn.md) | Step 006 / 02-short-term-memory |
| [BlackboxServerClient._post_agent_with_retry](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient._post_agent_with_retry.md) | Step 006 / 02-short-term-memory |
| [BlackboxServerClient.call_agent](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.call_agent.md) | Step 006 / 02-short-term-memory |
| [BlackboxServerClient.health](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.health.md) | Step 006 / 03-long-term-memory |
| [BlackboxServerClient.register_agent](functions/dressage/paddock/blackbox/client.py/BlackboxServerClient.register_agent.md) | Step 006 / 03-long-term-memory |
| [normalize_blackbox_type](functions/dressage/paddock/blackbox/common/defaults.py/normalize_blackbox_type.md) | Step 006 / 03-long-term-memory |
| [_execute_blackbox_cmd](functions/dressage/paddock/blackbox/execute_hooks.py/_execute_blackbox_cmd.md) | Step 006 / 03-long-term-memory |
| [execute_blackbox_cmds_for_stage](functions/dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md) | Step 006 / 03-long-term-memory |
| [parse_blackbox_execute_cmds](functions/dressage/paddock/blackbox/execute_hooks.py/parse_blackbox_execute_cmds.md) | Step 006 / 03-long-term-memory |
| [BlackboxAgentPaddock.call_agent](functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.call_agent.md) | Step 006 / 02-short-term-memory |
| [BlackboxAgentPaddock.init](functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.init.md) | Step 006 / 03-long-term-memory |
| [BlackboxAgentPaddock.register_agent](functions/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.register_agent.md) | Step 006 / 03-long-term-memory |
| [create_paddock_from_env](functions/dressage/paddock/factory.py/create_paddock_from_env.md) | Step 006 / 03-long-term-memory |
| [ProxyClient.register_session_context](functions/dressage/proxy/proxy_client.py/ProxyClient.register_session_context.md) | Step 006 / 03-long-term-memory |
| [instance_id（generate 中的别名 _instance_id）](functions/dressage/rollout/artifacts/samples.py/instance_id.md) | Step 006 / 03-long-term-memory |
| [_backend_options_for_register](functions/dressage/rollout/generate/blackbox_dispatch.py/_backend_options_for_register.md) | Step 006 / 03-long-term-memory |
| [blackbox_dispatch.generate](functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md) | Step 006 / 02-short-term-memory |
| [get_paddock_from_env](functions/dressage/rollout/generate/runtime.py/get_paddock_from_env.md) | Step 006 / 03-long-term-memory |
| [get_proxy_client](functions/dressage/rollout/generate/runtime.py/get_proxy_client.md) | Step 006 / 03-long-term-memory |
| [paddock_env_args_from_metadata](functions/dressage/rollout/generate/runtime.py/paddock_env_args_from_metadata.md) | Step 006 / 03-long-term-memory |
| [PrewarmStore.claim](functions/dressage/rollout/prewarm/store.py/PrewarmStore.claim.md) | Step 006 / 03-long-term-memory |
| [PrewarmStore.start](functions/dressage/rollout/prewarm/store.py/PrewarmStore.start.md) | Step 006 / 03-long-term-memory |
| [claim_prewarm](functions/dressage/rollout/prewarm/store.py/claim_prewarm.md) | Step 006 / 03-long-term-memory |
| [ensure_blackbox_session_id](functions/dressage/rollout/prewarm/store.py/ensure_blackbox_session_id.md) | Step 006 / 03-long-term-memory |
| [SandboxProvider.create](functions/dressage/sandbox/provider.py/SandboxProvider.create.md) | Step 006 / 03-long-term-memory |
| [SandboxProvider.get_public_url](functions/dressage/sandbox/provider.py/SandboxProvider.get_public_url.md) | Step 006 / 03-long-term-memory |

[前一步](../../step-006-agent-execution/README.md) · [本步 scope](../01-scope.md)
