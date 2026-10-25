# 03 · Step 3 的长期函数记忆

[本步入口](../README.md) · [本步新记录](../02-short-term-memory/overview.md)

由 Step 1 的 `03 + 02` 完整合并而来：此前 `03` 没有函数卡片，本次继承 `02` 中全部 17 份记录，包含共用模型的引用入口。各卡片保留原话、场景、代码、输入输出、来源与未知，只补继承来源并重算链接。

原记录中的理解状态保持当时语境；最新反馈统一见[当前进度](../../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。用户已明确表示本次 `_run_turn` 阅读理解完了，这不自动代表所有子函数内部都已逐项掌握。

| 源码文件 | 继承的函数记录 | 来源 |
| --- | --- | --- |
| `aiohttp/web_response.py` | [aiohttp.web.json_response](functions/aiohttp/web_response.py/json_response.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/aiohttp/web_response.py/json_response.md) |
| `slime/agent/adapters/anthropic.py` | [AnthropicAdapter._build_reply](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._build_reply.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._build_reply.md) |
| `slime/agent/adapters/anthropic.py` | [AnthropicAdapter._respond](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._respond.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._respond.md) |
| `slime/agent/adapters/anthropic.py` | [AnthropicAdapter._translate](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md) |
| `slime/agent/adapters/anthropic.py` | [_render_response](functions/slime/agent/adapters/anthropic.py/_render_response.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/_render_response.md) |
| `slime/agent/adapters/anthropic.py` | [_render_stream](functions/slime/agent/adapters/anthropic.py/_render_stream.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/anthropic.py/_render_stream.md) |
| `slime/agent/adapters/common.py` | [BaseAdapter._build_reply](functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md) |
| `slime/agent/adapters/common.py` | [BaseAdapter._respond](functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) |
| `slime/agent/adapters/common.py` | [BaseAdapter._run_turn](functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) |
| `slime/agent/adapters/common.py` | [BaseAdapter._translate](functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) |
| `slime/agent/adapters/common.py` | [_render_token_ids](functions/slime/agent/adapters/common.py/_render_token_ids.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/_render_token_ids.md) |
| `slime/agent/adapters/common.py` | [call_sglang_generate](functions/slime/agent/adapters/common.py/call_sglang_generate.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/adapters/common.py/call_sglang_generate.md) |
| `slime/agent/harness/common.py` | [BaseHarness.run](functions/slime/agent/harness/common.py/BaseHarness.run.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md) |
| `slime/agent/parsing.py` | [parse_model_output](functions/slime/agent/parsing.py/parse_model_output.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/parsing.py/parse_model_output.md) |
| `slime/agent/trajectory.py` | [TrajectoryManager.record_turn](functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md) |
| `src/transformers/tokenization_utils_base.py` | [PreTrainedTokenizerBase.apply_chat_template](functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md) |
| `src/transformers/tokenization_utils_base.py` | [PreTrainedTokenizerBase.decode](functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) | [Step 1 原卡](../../step-001-harness-to-adapter/02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) |

形成过程仍指向产生相应认识的原步骤；同批继承的子函数互相链接到本目录。继承本身不改认识时间、不产生新的掌握结论。
