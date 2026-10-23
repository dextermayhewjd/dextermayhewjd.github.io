# 03 · 前序累计函数与类记录

[本步入口](../README.md) · [本步短期记忆](../02-short-term-memory/overview.md) · [来源：Step 1](../../step-001-harness-to-adapter/02-short-term-memory/overview.md)

由 Step 1 的 `03 + 02` 合并继承，共 20 份记录：16 张函数卡、1 张类卡和 3 个实现引用入口。Step 1 的原 `03` 没有函数，本次内容来自其 `02`。

完整保留原话、输入输出、心智模型、未知、首次接触和认识更新时间，只调整复制后的相对链接。各卡片仍以自身注明的源码或依赖版本为准；本次继承不表示全部掌握，也不把旧证据统一标成新版。表格中的状态继承自来源步骤。

| 源码文件 | 函数或类记录 | 来源与状态 |
| --- | --- | --- |
| `slime/agent/adapters/common.py` | [BaseAdapter._run_turn](functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | 用户已初步串联请求处理链；2026-10-23 整卡校准到 `18868a79`，三段按真实执行组织，补齐输入接续、追踪嵌套与前缀保存；原话和认识时间保留，[inflight 说明](functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md#inflight-cleanup)继续折叠 |
| `slime/agent/adapters/common.py` | [BaseAdapter._translate](functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | 从 Step 0 移入的原话、输入输出与来源保留；在新版 `_run_turn:415` 处复用；2026-10-23 已核对新版：原样例不变；用户已复述按调用顺序整理工具结果，具体实现与异常 ID 分支未展开 |
| `slime/agent/adapters/anthropic.py` | [AnthropicAdapter._translate → BaseAdapter._translate](functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | 继续共用转换模型；[实现定位与原始来源](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md)；2026-10-23 已核对新版：原样例不变；用户已复述按调用顺序整理工具结果，具体实现与异常 ID 分支未展开 |
| `slime/agent/adapters/common.py` | [_session_prompt_ids](functions/slime/agent/adapters/common.py/_session_prompt_ids.md) | 2026-10-23 新版新增函数：普通编码、匹配历史和回退；已做局部验证；已补分支图；用户已认可 anchor 连续检查与回退不生成摘要的两项解释比较清楚，简短心智模型与完整解释默认展示，源码细节和验证按需展开；具体条件未逐项确认 |
| `slime/agent/adapters/common.py` | [PromptPrefix（类）](classes/slime/agent/adapters/common.py/PromptPrefix.md) | 2026-10-23 建立类卡，绑定 `18868a79`；用户已初步概括保存本轮信息，助手补充消息、工具定义复制而 turn 保留引用的区别，细化尚待反馈 |
| `slime/agent/adapters/common.py` | [_render_token_ids](functions/slime/agent/adapters/common.py/_render_token_ids.md) | 用户已提出“翻译／转换”的初步理解，仍不清楚 `apply_chat_template`；已补套模板与编码的区分；2026-10-23 校准当前调用者与模板参数透传，个人理解状态保留 |
| Transformers：`src/transformers/tokenization_utils_base.py` | [PreTrainedTokenizerBase.apply_chat_template](functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md) | 按用户要求单独保存简短记录；套模板与编码的区分由助手说明，尚待用户反馈 |
| `slime/agent/adapters/common.py` | [call_sglang_generate](functions/slime/agent/adapters/common.py/call_sglang_generate.md) | 用户曾反馈内部黑盒，已保存六段执行地图；后续对生成 token 的 logprob 与全词表概率的区别反馈“大概理解了”，其余内部细节未逐项确认；本次校准到 `18868a79`，保留正常场景并补续生成分支及返回字段，旧稿归档 |
| `slime/observability/trace_utils.py` | [trace_span](functions/slime/observability/trace_utils.py/trace_span.md) | 2026-10-23 按确认顺序回看追踪包装；已做局部实验；补对象关系图与事件追加示例后，用户提出“类似 logger”的职责概括；已补清当前使用已有 handle，细化尚待反馈，嵌套机制仍按需展开 |
| Transformers：`src/transformers/tokenization_utils_base.py` | [PreTrainedTokenizerBase.decode](functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) | 已有函数记录补入索引；用户表达了用 tokenizer 还原输出 token 的职责理解，内部实现尚未展开 |
| `slime/agent/parsing.py` | [parse_model_output](functions/slime/agent/parsing.py/parse_model_output.md) | 用户已表述将原始输出拆成 reasoning、text 与工具字段，具体分支未逐项确认；2026-10-23 校准：Slime 解析代码和调用实参相同，新版依赖的四组局部结果一致，依赖扩展与旧证据另列 |
| `slime/agent/adapters/common.py` | [BaseAdapter._build_reply](functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md) | 用户提出将 parsed 组织为对应 Adapter 待发送内容的理解，内部字段未逐项确认；2026-10-23 校准：实现及五种场景输出不变，补入新版前缀保存的调用方用途 |
| `slime/agent/adapters/common.py` | [BaseAdapter._respond](functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) | Step 1，2026-10-21；用户对整体响应职责反馈“大概理解了”，保留总输入输出、结构示意与调用树；内部细节未逐项确认  2026-10-23 已校准：响应实现不变，保留普通/流式发送时机的区别 |
| `slime/agent/adapters/anthropic.py` | [_render_response](functions/slime/agent/adapters/anthropic.py/_render_response.md) | 从 `_respond` 记录拆出；保存响应正文字典的组装，原场景与来源不变  2026-10-23 已核对函数体不变并更新定位 |
| aiohttp：`aiohttp/web_response.py` | [web.json_response](functions/aiohttp/web_response.py/json_response.md) | 从 `_respond` 记录拆出；保存序列化与响应对象构造，尚无直接复述 |
| `slime/agent/adapters/anthropic.py` | [_render_stream](functions/slime/agent/adapters/anthropic.py/_render_stream.md) | 从 `_respond` 记录拆出；保存 SSE 事件与写出行为，沿用原局部运行证据  2026-10-23 已核对函数体不变并更新定位 |
| `slime/agent/trajectory.py` | [TrajectoryManager.record_turn](functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md) | Step 1，2026-10-21；用户提出存入树与复用的初步理解，并由分叉联想到按成功率剪枝；已区分当前记录职责与搜索决策，尚待反馈  2026-10-23 已校准：补充 TurnRecord 新字段及默认关闭历史改写合并 |
| `slime/agent/harness/common.py` | [BaseHarness.run](functions/slime/agent/harness/common.py/BaseHarness.run.md) | 用户已提出启动到请求入口的问题；职责与输入输出由助手静态核对，尚无用户职责复述 |

此外继承两份共用模型的实现定位入口：

- [AnthropicAdapter._build_reply](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._build_reply.md)
- [AnthropicAdapter._respond](functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._respond.md)

本步实际需要回顾某张卡片时，再按短期记忆规则调入 `02`；任务范围和阅读顺序由本步 scope 负责。
