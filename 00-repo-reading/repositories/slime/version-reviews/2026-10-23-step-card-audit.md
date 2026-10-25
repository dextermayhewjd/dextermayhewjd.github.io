# Step 0–8 的函数卡片版本盘点

> 用户要求每个 step 都重新校准。本页先列出检查覆盖范围和明确的间接变化；函数本体相同仍需核对调用方、配置、全局常量和下游实现，不能直接判为“认识无需修改”。

[版本影响评估](2026-10-23-2f231865-to-18868a79.md) · [唯一进度](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

比较范围：Slime `2f2318653f6f794dddd321eff7c9d4b7b174643f` → `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。这是 2026-10-23 的静态盘点快照，后续具体推进只在唯一路线记录。

共 49 份短期卡片，对应 43 个不同目标；同一目标在多步调取会重复计入卡片数。49 份中：22 份本体变化、24 份本体相同、3 份属于外部依赖。此数量不代表学习完成度，也不代表全部记录只需按本体差异修改。

## 按步骤检查

### [step-000-coding-agent](../topics/01-coding-agent-rl/steps/step-000-coding-agent/01-scope.md)

本步没有函数卡；校准公开入口与实际编排、整体骨架和步骤位置。

### [step-001-harness-to-adapter](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md)

共同接口或协议包装不变，不代表转换实现和调用现场不变；需追查 _translate_messages、_session_prompt_ids 以及扩展后的 TurnRecord。三个外部库记录独立保留 aiohttp 3.13.5 / Transformers v4.57.1 的原依据，尚未核实新的运行环境。

<details>
<summary>本步 17 份短期卡片：本体与来源核对</summary>

| 卡片 | 比较结果 | 旧定义行 → 新定义行 |
| --- | --- | --- |
| [json_response](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/aiohttp/web_response.py/json_response.md) | 外部依赖，单独核对 | 不属于本次 Slime 提交比较 |
| [AnthropicAdapter._build_reply](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._build_reply.md) | 本体相同，依赖待核对 | 63 → 63 |
| [AnthropicAdapter._respond](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._respond.md) | 本体相同，依赖待核对 | 71 → 71 |
| [AnthropicAdapter._translate](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md) | 本体相同，依赖待核对 | 58 → 58 |
| [_render_response](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/_render_response.md) | 本体相同，依赖待核对 | 198 → 221 |
| [_render_stream](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/_render_stream.md) | 本体相同，依赖待核对 | 211 → 234 |
| [BaseAdapter._build_reply](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md) | 本体相同，依赖待核对 | 193 → 258 |
| [BaseAdapter._respond](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) | 本体相同，依赖待核对 | 197 → 262 |
| [BaseAdapter._run_turn](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | 本体变化 | 318 → 387 |
| [BaseAdapter._translate](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | 本体相同，依赖待核对 | 189 → 254 |
| [_render_token_ids](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/_render_token_ids.md) | 本体变化 | 58 → 73 |
| [call_sglang_generate](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/call_sglang_generate.md) | 本体变化 | 442 → 524 |
| [BaseHarness.run](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md) | 本体相同，依赖待核对 | 81 → 81 |
| [parse_model_output](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/parsing.py/parse_model_output.md) | 本体相同，依赖待核对 | 25 → 25 |
| [TrajectoryManager.record_turn](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md) | 本体相同，依赖待核对 | 283 → 381 |
| [PreTrainedTokenizerBase.apply_chat_template](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md) | 外部依赖，单独核对 | 不属于本次 Slime 提交比较 |
| [PreTrainedTokenizerBase.decode](../topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) | 外部依赖，单独核对 | 不属于本次 Slime 提交比较 |

</details>

### [step-003-swe-evaluation](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/01-scope.md)

校准沙箱选择、临时文件路径、补丁策略和评测用户。E2B 方法保留不能证明它仍是当前默认后端。

<details>
<summary>本步 7 份短期卡片：本体与来源核对</summary>

| 卡片 | 比较结果 | 旧定义行 → 新定义行 |
| --- | --- | --- |
| [_apply_diff](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_apply_diff.md) | 本体变化 | 299 → 352 |
| [_grade_scaleswe](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_grade_scaleswe.md) | 本体变化 | 253 → 304 |
| [_run_eval_cmd](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/_run_eval_cmd.md) | 本体变化 | 341 → 394 |
| [run_evaluation](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/run_evaluation.md) | 本体变化 | 239 → 290 |
| [E2BSandbox.__aenter__](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aenter__.md) | 本体相同，依赖待核对 | 281 → 298 |
| [E2BSandbox.__aexit__](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/slime/agent/sandbox.py/E2BSandbox.__aexit__.md) | 本体相同，依赖待核对 | 302 → 319 |
| [ensure_agent_user](../topics/01-coding-agent-rl/steps/step-003-swe-evaluation/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) | 本体变化 | 390 → 409 |

</details>

### [step-004-trajectory-to-samples](../topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/01-scope.md)

三个入口本体相同，但 _SampleBuilder、TurnRecord 和调用处的配置变化。特别是 fork_merge_threshold 默认从 None 变成 0；原 None 经 manager 转成 1024，不能把旧默认阈值沿用到当前配置。

<details>
<summary>本步 3 份短期卡片：本体与来源核对</summary>

| 卡片 | 比较结果 | 旧定义行 → 新定义行 |
| --- | --- | --- |
| [BaseAdapter.finish_session](../topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md) | 本体相同，依赖待核对 | 245 → 314 |
| [BaseAdapter.shutdown_session](../topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md) | 本体相同，依赖待核对 | 225 → 294 |
| [TrajectoryManager.get_trajectory](../topics/01-coding-agent-rl/steps/step-004-trajectory-to-samples/02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md) | 本体相同，依赖待核对 | 307 → 405 |

</details>

### [step-005-agent-preparation](../topics/01-coding-agent-rl/steps/step-005-agent-preparation/01-scope.md)

校准按 agent 选择 endpoint、Session 新状态以及新的调用现场；sid 的生成规则仍需结合当前调用处确认。

<details>
<summary>本步 4 份短期卡片：本体与来源核对</summary>

| 卡片 | 比较结果 | 旧定义行 → 新定义行 |
| --- | --- | --- |
| [_AdapterService.__init__](../topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md) | 本体变化 | 138 → 168 |
| [_session_id](../topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_session_id.md) | 本体相同，依赖待核对 | 308 → 438 |
| [BaseAdapter.open_session](../topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.open_session.md) | 本体变化 | 210 → 275 |
| [Session](../topics/01-coding-agent-rl/steps/step-005-agent-preparation/02-short-term-memory/classes/slime/agent/adapters/common.py/Session.md) | 本体变化 | 34 → 46 |

</details>

### [step-006-agent-sandbox](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/01-scope.md)

校准 create_sandbox 的默认 provider、CLI 安装分支、E2B 的异常约定；生命周期和具体后端分开检查。

<details>
<summary>本步 4 份短期卡片：本体与来源核对</summary>

| 卡片 | 比较结果 | 旧定义行 → 新定义行 |
| --- | --- | --- |
| [boot_agent_sandbox](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/boot_agent_sandbox.md) | 本体变化 | 96 → 111 |
| [ClaudeCodeHarness.install_cli](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.install_cli.md) | 本体变化 | 36 → 38 |
| [install_npm_cli](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/functions/slime/agent/harness/common.py/install_npm_cli.md) | 本体相同，依赖待核对 | 125 → 129 |
| [E2BSandbox](../topics/01-coding-agent-rl/steps/step-006-agent-sandbox/02-short-term-memory/classes/slime/agent/sandbox.py/E2BSandbox.md) | 本体变化 | 160 → 177 |

</details>

### [step-007-prepare-workspace](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/01-scope.md)

apply_pre_commands 本体相同，但 _PRE 从 /workspace/__cagent_pre__.sh 变为 /tmp/__cagent_pre__.sh；旧卡中的路径需修正。同时检查 prepare_workspace 的 baseline 返回值及 git_diff 接收方。

<details>
<summary>本步 4 份短期卡片：本体与来源核对</summary>

| 卡片 | 比较结果 | 旧定义行 → 新定义行 |
| --- | --- | --- |
| [apply_before_repo_set_cmd](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_before_repo_set_cmd.md) | 本体相同，依赖待核对 | 201 → 212 |
| [apply_pre_commands](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/apply_pre_commands.md) | 本体相同，依赖待核对 | 214 → 225 |
| [prepare_workspace](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/examples/coding_agent_rl/swe.py/prepare_workspace.md) | 本体变化 | 177 → 187 |
| [ensure_agent_user](../topics/01-coding-agent-rl/steps/step-007-prepare-workspace/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) | 本体变化 | 390 → 409 |

</details>

### [step-008-harness-communication](../topics/01-coding-agent-rl/steps/step-008-harness-communication/01-scope.md)

BaseHarness.run、run_agent、exec_and_wait 本体相同，但具体配置/启动以及 _await_done_marker 已变化；不能直接沿用旧调用树的叶节点。

<details>
<summary>本步 8 份短期卡片：本体与来源核对</summary>

| 卡片 | 比较结果 | 旧定义行 → 新定义行 |
| --- | --- | --- |
| [BaseAdapter._run_turn](../topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | 本体变化 | 318 → 387 |
| [ClaudeCodeHarness.launch_and_wait](../topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.launch_and_wait.md) | 本体变化 | 57 → 86 |
| [ClaudeCodeHarness.write_config](../topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/claude_code.py/ClaudeCodeHarness.write_config.md) | 本体变化 | 44 → 57 |
| [BaseHarness.run](../topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md) | 本体相同，依赖待核对 | 81 → 81 |
| [run_agent](../topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/harness/common.py/run_agent.md) | 本体相同，依赖待核对 | 107 → 111 |
| [ensure_agent_user](../topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/ensure_agent_user.md) | 本体变化 | 390 → 409 |
| [exec_and_wait](../topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/functions/slime/agent/sandbox.py/exec_and_wait.md) | 本体相同，依赖待核对 | 82 → 99 |
| [HarnessContext](../topics/01-coding-agent-rl/steps/step-008-harness-communication/02-short-term-memory/classes/slime/agent/harness/common.py/HarnessContext.md) | 本体相同，依赖待核对 | 43 → 43 |

</details>

### [step-009-adapter-request-entry](../topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/01-scope.md)

接入 endpoint 后重新核对 app、监听、路由、Request/body 的交接；现有两张旧卡是调取记录，不代表新接收机制已理解。

<details>
<summary>本步 2 份短期卡片：本体与来源核对</summary>

| 卡片 | 比较结果 | 旧定义行 → 新定义行 |
| --- | --- | --- |
| [_AdapterService.__init__](../topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/02-short-term-memory/functions/examples/coding_agent_rl/generate.py/_AdapterService.__init__.md) | 本体变化 | 138 → 168 |
| [BaseAdapter._run_turn](../topics/01-coding-agent-rl/steps/step-009-adapter-request-entry/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | 本体变化 | 318 → 387 |

</details>

## 后续每步需要完成的校准

1. 核对旧解释是否准确描述当时源码；有旧误解时明确纠正，不能全归因为版本更新。
2. 对照新版的入口、输入输出、副作用、默认配置与调用关系，区分继续成立、需要修正和待核实。
3. 先保存旧版，再更新本步实际使用的正文与导航；原话、首次接触、历史未知和旧源码依据保留。
4. 新增机制可以先写明职责与未展开边界；助手静态核对不自动成为用户已经理解。

验证方式：遍历各步 02-short-term-memory 下 functions/classes；按源码路径和完整符号比较 Python AST，另回查相关常量与调用处。AST 比较忽略排版和行号，但不覆盖传递依赖、外部环境或真实运行结果；本页没有将其当成行为等价证明。
