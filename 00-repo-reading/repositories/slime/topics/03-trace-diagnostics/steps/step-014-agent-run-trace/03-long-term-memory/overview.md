# 03 · Step 014 的前序累计记录

跨主题完整继承 [Step 013](../../../../02-rollout-reward/steps/step-013-completed-group-handoff/README.md) 的 03 + 02，共 66 份记录，包含 3 份历史空白占位。认识时间、原话、未知与来源均保留。

[继承清单](../references/inheritance-manifest.json) · [本步范围](../01-scope.md)

此前的 trace_span 卡另从 Step 001 调取到本步 02；它不是本次 66 份继承记录之一，来源见本步索引。

| 记录 | 源码目录映射 | 状态 |
| --- | --- | --- |
| [_AdapterService](classes/examples/coding_agent_rl/generate.py/_AdapterService.md) | `classes/examples/coding_agent_rl/generate.py/_AdapterService.md` | 保留原记录及认识状态 |
| [Session](classes/slime/agent/adapters/common.py/Session.md) | `classes/slime/agent/adapters/common.py/Session.md` | 保留原记录及认识状态 |
| [HarnessContext](classes/slime/agent/harness/common.py/HarnessContext.md) | `classes/slime/agent/harness/common.py/HarnessContext.md` | 保留原记录及认识状态 |
| [E2BSandbox](classes/slime/agent/sandbox.py/E2BSandbox.md) | `classes/slime/agent/sandbox.py/E2BSandbox.md` | 保留原记录及认识状态 |
| [AsyncRolloutWorker](classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md) | `classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md` | 保留原记录及认识状态 |
| [GenerateState](classes/slime/rollout/sglang_rollout.py/GenerateState.md) | `classes/slime/rollout/sglang_rollout.py/GenerateState.md` | 保留原记录及认识状态 |
| [Sample](classes/slime/utils/types.py/Sample.md) | `classes/slime/utils/types.py/Sample.md` | 保留原记录及认识状态 |
| [Semaphore.acquire](functions/Lib/asyncio/locks.py/Semaphore.acquire.md) | `functions/Lib/asyncio/locks.py/Semaphore.acquire.md` | 保留原记录及认识状态 |
| [Semaphore.release](functions/Lib/asyncio/locks.py/Semaphore.release.md) | `functions/Lib/asyncio/locks.py/Semaphore.release.md` | 历史空白占位 |
| [json_response](functions/aiohttp/web_response.py/json_response.md) | `functions/aiohttp/web_response.py/json_response.md` | 保留原记录及认识状态 |
| [_AdapterService.__init__](functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md) | `functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md` | 保留原记录及认识状态 |
| [_session_id](functions/examples/coding_agent_rl/generate.py/_session_id.md) | `functions/examples/coding_agent_rl/generate.py/_session_id.md` | 保留原记录及认识状态 |
| [boot_agent_sandbox](functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md) | `functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md` | 保留原记录及认识状态 |
| [generate](functions/examples/coding_agent_rl/generate.py/generate.md) | `functions/examples/coding_agent_rl/generate.py/generate.md` | 历史空白占位 |
| [_apply_diff](functions/examples/coding_agent_rl/swe.py/_apply_diff.md) | `functions/examples/coding_agent_rl/swe.py/_apply_diff.md` | 保留原记录及认识状态 |
| [_grade_scaleswe](functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md) | `functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md` | 保留原记录及认识状态 |
| [_run_eval_cmd](functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md) | `functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md` | 保留原记录及认识状态 |
| [apply_before_repo_set_cmd](functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md) | `functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md` | 保留原记录及认识状态 |
| [apply_pre_commands](functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md) | `functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md` | 保留原记录及认识状态 |
| [prepare_workspace](functions/examples/coding_agent_rl/swe.py/prepare_workspace.md) | `functions/examples/coding_agent_rl/swe.py/prepare_workspace.md` | 保留原记录及认识状态 |
| [run_evaluation](functions/examples/coding_agent_rl/swe.py/run_evaluation.md) | `functions/examples/coding_agent_rl/swe.py/run_evaluation.md` | 保留原记录及认识状态 |
| [AnthropicAdapter._build_reply](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._build_reply.md) | `functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._build_reply.md` | 保留原记录及认识状态 |
| [AnthropicAdapter._register_routes](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._register_routes.md) | `functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._register_routes.md` | 保留原记录及认识状态 |
| [AnthropicAdapter._respond](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._respond.md) | `functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._respond.md` | 保留原记录及认识状态 |
| [AnthropicAdapter._translate](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md) | `functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md` | 保留原记录及认识状态 |
| [_render_response](functions/slime/agent/adapters/anthropic.py/_render_response.md) | `functions/slime/agent/adapters/anthropic.py/_render_response.md` | 保留原记录及认识状态 |
| [_render_stream](functions/slime/agent/adapters/anthropic.py/_render_stream.md) | `functions/slime/agent/adapters/anthropic.py/_render_stream.md` | 保留原记录及认识状态 |
| [BaseAdapter._build_reply](functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md) | `functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md` | 保留原记录及认识状态 |
| [BaseAdapter._respond](functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) | `functions/slime/agent/adapters/common.py/BaseAdapter._respond.md` | 保留原记录及认识状态 |
| [BaseAdapter._run_turn](functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | `functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md` | 保留原记录及认识状态 |
| [BaseAdapter._translate](functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | `functions/slime/agent/adapters/common.py/BaseAdapter._translate.md` | 保留原记录及认识状态 |
| [BaseAdapter.finish_session](functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md) | `functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md` | 保留原记录及认识状态 |
| [BaseAdapter.open_session](functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md) | `functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md` | 保留原记录及认识状态 |
| [BaseAdapter.shutdown_session](functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md) | `functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md` | 保留原记录及认识状态 |
| [_render_token_ids](functions/slime/agent/adapters/common.py/_render_token_ids.md) | `functions/slime/agent/adapters/common.py/_render_token_ids.md` | 保留原记录及认识状态 |
| [call_sglang_generate](functions/slime/agent/adapters/common.py/call_sglang_generate.md) | `functions/slime/agent/adapters/common.py/call_sglang_generate.md` | 保留原记录及认识状态 |
| [run_app_in_thread](functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md) | `functions/slime/agent/aiohttp_threaded.py/run_app_in_thread.md` | 保留原记录及认识状态 |
| [ClaudeCodeHarness.install_cli](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md) | `functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md` | 保留原记录及认识状态 |
| [ClaudeCodeHarness.launch_and_wait](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | `functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md` | 保留原记录及认识状态 |
| [ClaudeCodeHarness.write_config](functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) | `functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md` | 保留原记录及认识状态 |
| [BaseHarness.run](functions/slime/agent/harness/common.py/BaseHarness.run.md) | `functions/slime/agent/harness/common.py/BaseHarness.run.md` | 保留原记录及认识状态 |
| [install_npm_cli](functions/slime/agent/harness/common.py/install_npm_cli.md) | `functions/slime/agent/harness/common.py/install_npm_cli.md` | 保留原记录及认识状态 |
| [run_agent](functions/slime/agent/harness/common.py/run_agent.md) | `functions/slime/agent/harness/common.py/run_agent.md` | 保留原记录及认识状态 |
| [parse_model_output](functions/slime/agent/parsing.py/parse_model_output.md) | `functions/slime/agent/parsing.py/parse_model_output.md` | 保留原记录及认识状态 |
| [E2BSandbox.__aenter__](functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md) | `functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md` | 保留原记录及认识状态 |
| [E2BSandbox.__aexit__](functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md) | `functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md` | 保留原记录及认识状态 |
| [ensure_agent_user](functions/slime/agent/sandbox.py/ensure_agent_user.md) | `functions/slime/agent/sandbox.py/ensure_agent_user.md` | 保留原记录及认识状态 |
| [exec_and_wait](functions/slime/agent/sandbox.py/exec_and_wait.md) | `functions/slime/agent/sandbox.py/exec_and_wait.md` | 保留原记录及认识状态 |
| [TrajectoryManager.get_trajectory](functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md) | `functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md` | 保留原记录及认识状态 |
| [TrajectoryManager.record_turn](functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md) | `functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md` | 保留原记录及认识状态 |
| [inherit_queue_context](functions/slime/data/transport.py/inherit_queue_context.md) | `functions/slime/data/transport.py/inherit_queue_context.md` | 保留原记录及认识状态 |
| [call_dynamic_filter](functions/slime/rollout/filter_hub/base_types.py/call_dynamic_filter.md) | `functions/slime/rollout/filter_hub/base_types.py/call_dynamic_filter.md` | 保留原记录及认识状态 |
| [AsyncRolloutWorker._loop](functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md) | `functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md` | 保留原记录及认识状态 |
| [AsyncRolloutWorker._make_done_cb](functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._make_done_cb.md) | `functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._make_done_cb.md` | 保留原记录及认识状态 |
| [AsyncRolloutWorker.get_completed_groups](functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.get_completed_groups.md) | `functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.get_completed_groups.md` | 保留原记录及认识状态 |
| [_generate_rollout_async](functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md) | `functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md` | 保留原记录及认识状态 |
| [batched_async_rm](functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md) | `functions/slime/rollout/rm_hub/__init__.py/batched_async_rm.md` | 保留原记录及认识状态 |
| [apply_rollout_sample_hooks](functions/slime/rollout/sample_hooks.py/apply_rollout_sample_hooks.md) | `functions/slime/rollout/sample_hooks.py/apply_rollout_sample_hooks.md` | 保留原记录及认识状态 |
| [GenerateState.dp_rank_context](functions/slime/rollout/sglang_rollout.py/GenerateState.dp_rank_context.md) | `functions/slime/rollout/sglang_rollout.py/GenerateState.dp_rank_context.md` | 保留原记录及认识状态 |
| [_run_server_abort_generate](functions/slime/rollout/sglang_rollout.py/_run_server_abort_generate.md) | `functions/slime/rollout/sglang_rollout.py/_run_server_abort_generate.md` | 保留原记录及认识状态 |
| [generate_and_rm](functions/slime/rollout/sglang_rollout.py/generate_and_rm.md) | `functions/slime/rollout/sglang_rollout.py/generate_and_rm.md` | 保留原记录及认识状态 |
| [generate_and_rm_group](functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md) | `functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md` | 保留原记录及认识状态 |
| [AsyncPacer.wait](functions/slime/utils/async_utils.py/AsyncPacer.wait.md) | `functions/slime/utils/async_utils.py/AsyncPacer.wait.md` | 保留原记录及认识状态 |
| [load_function](functions/slime/utils/misc.py/load_function.md) | `functions/slime/utils/misc.py/load_function.md` | 历史空白占位 |
| [PreTrainedTokenizerBase.apply_chat_template](functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md) | `functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md` | 保留原记录及认识状态 |
| [PreTrainedTokenizerBase.decode](functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) | `functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md` | 保留原记录及认识状态 |
