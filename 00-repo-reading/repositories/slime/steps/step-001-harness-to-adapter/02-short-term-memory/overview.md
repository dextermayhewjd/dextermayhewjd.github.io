# 02 · Step 1 的短期函数记录

[本步主线](../README.md) · [前序函数记忆](../03-long-term-memory/overview.md)

| 源码文件 | 函数记录 | 来源与状态 |
| --- | --- | --- |
| `slime/agent/adapters/common.py` | [BaseAdapter._run_turn](functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | 用户已初步串联请求处理链；现按完整函数的输入输出、内部处理和局部跳转重排，[inflight 说明](functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#inflight-cleanup)折叠保留；重排不计为新增理解 |
| `slime/agent/adapters/common.py` | [BaseAdapter._translate](functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | 从 Step 0 移入，原话、输入输出、认识时间和来源不变；在 `_run_turn:341` 处复用 |
| `slime/agent/adapters/anthropic.py` | [AnthropicAdapter._translate → BaseAdapter._translate](functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | 继续共用转换模型；[实现定位与原始来源](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md) |
| `slime/agent/adapters/common.py` | [_render_token_ids](functions/slime/agent/adapters/common.py/_render_token_ids.md) | 用户已提出“翻译／转换”的初步理解，仍不清楚 `apply_chat_template`；已补套模板与编码的区分，等待后续反馈 |
| Transformers：`src/transformers/tokenization_utils_base.py` | [PreTrainedTokenizerBase.apply_chat_template](functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md) | 按用户要求单独保存简短记录；套模板与编码的区分由助手说明，尚待用户反馈 |
| `slime/agent/adapters/common.py` | [call_sglang_generate](functions/slime/agent/adapters/common.py/call_sglang_generate.md) | 用户曾反馈内部黑盒，已保存六段执行地图；后续对生成 token 的 logprob 与全词表概率的区别反馈“大概理解了”，其余内部细节未逐项确认 |
| Transformers：`src/transformers/tokenization_utils_base.py` | [PreTrainedTokenizerBase.decode](functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) | 已有函数记录补入索引；用户表达了用 tokenizer 还原输出 token 的职责理解，内部实现尚未展开 |
| `slime/agent/parsing.py` | [parse_model_output](functions/slime/agent/parsing.py/parse_model_output.md) | 已有函数记录补入索引；用户表述了将原始输出拆成 reasoning、text 与工具字段，具体分支未逐项确认 |
| `slime/agent/adapters/common.py` | [BaseAdapter._build_reply](functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md) | 已有函数记录补入索引；用户提出将 parsed 组织为对应 Adapter 待发送内容的理解，保留内部消息与协议材料的区别 |
| `slime/agent/adapters/common.py` | [BaseAdapter._respond](functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) | Step 1，2026-10-21；用户对整体响应职责反馈“大概理解了”，保留总输入输出、结构示意与调用树；内部细节未逐项确认 |
| `slime/agent/adapters/anthropic.py` | [_render_response](functions/slime/agent/adapters/anthropic.py/_render_response.md) | 从 `_respond` 记录拆出；保存响应正文字典的组装，原场景与来源不变 |
| aiohttp：`aiohttp/web_response.py` | [web.json_response](functions/aiohttp/web_response.py/json_response.md) | 从 `_respond` 记录拆出；保存序列化与响应对象构造，尚无直接复述 |
| `slime/agent/adapters/anthropic.py` | [_render_stream](functions/slime/agent/adapters/anthropic.py/_render_stream.md) | 从 `_respond` 记录拆出；保存 SSE 事件与写出行为，沿用原局部运行证据 |
| `slime/agent/trajectory.py` | [TrajectoryManager.record_turn](functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md) | Step 1，2026-10-21；用户提出存入树与复用的初步理解，并由分叉联想到按成功率剪枝；已区分当前记录职责与搜索决策，尚待反馈 |
| `slime/agent/harness/common.py` | [BaseHarness.run](functions/slime/agent/harness/common.py/BaseHarness.run.md) | 用户已提出启动到请求入口的问题；职责与输入输出由助手静态核对，尚无用户职责复述 |

`BaseHarness.run` 用来恢复上游来路；`launch_and_wait`、`run_agent`、`_register_routes` 只用于定位。任务主线与阅读接续见[步骤入口](../README.md)，本页只索引函数记录。
