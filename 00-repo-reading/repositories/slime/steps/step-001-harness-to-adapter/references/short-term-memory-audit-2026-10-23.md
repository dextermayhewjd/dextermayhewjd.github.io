# Step 1 短期记忆清点：本轮主线、辅助记录与历史来路

2026-10-23 的清点快照。来源是本步 `02-short-term-memory/` 的实际文件、卡片中的来源与版本、`04-flow.md` 中的阅读经过；当前接续仍以[唯一路线](../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准。

用户提出：

> 那么看一下这个step里面整体的内容吧
> 我的意思是这里的short term memory部分
> 都是我们这一轮讨论的函数吗？
> 为什么感觉short term 里面还有很多别的函数呢？

## 1. 结论与计数

不是所有文件都代表这一轮新讨论的函数。当前目录除 `overview.md` 外共有 **20 个文件：16 张函数记录、1 张类记录、3 个实现引用入口**。其中 `BaseHarness.run` 使用早期卡片格式，但内容仍是一张完整函数记录，不能因缺少新版栏目标题而计为引用入口。

| 与当前问题的关系 | 数量 | 含义 |
| --- | --- | --- |
| `_run_turn` 主线及直接使用的记录 | 12 | 11 张函数记录与 PromptPrefix 类卡；包括沿用的旧卡，不等于全部已改为新版 |
| 从主线内部展开的辅助记录 | 4 | 模板与 HTTP 响应的已有子函数卡 |
| Anthropic 实现的引用入口 | 3 | 指向 common 下的共同记录，没有独立的一套心智模型 |
| 早期保存的上游来路 | 1 | BaseHarness.run，用来回答最初怎样走到 Adapter 的问题 |

`02` 的现行含义是“本 step 正在使用的记录”，可以包含本步早期记录和再次调用的旧卡。这轮是在原 Step 1 内校准新版，没有新建一个只收本轮聊天记录的 step。`03` 按前序步骤继承，不能只因同一步中的卡片较旧，就将它搬到 `03`。

## 2. 全部文件分别属于哪里

### 主线及直接使用的记录：12 项

| 记录 | 为什么出现在本步 | 本轮校准情况 |
| --- | --- | --- |
| [BaseAdapter._run_turn](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._run_turn.md) | 一次模型请求的锚点函数 | 逐段讨论过；整张卡主体仍为 `2f231865`，新增前缀保存入口已另标版本 |
| [BaseAdapter._translate](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._translate.md) | 转换消息与工具定义 | 已校准 `18868a79` |
| [_session_prompt_ids](../02-short-term-memory/functions/slime/agent/adapters/common.py/_session_prompt_ids.md) | 检查历史候选，准备模型输入 | 本轮新增并讨论 |
| [_render_token_ids](../02-short-term-memory/functions/slime/agent/adapters/common.py/_render_token_ids.md) | 为输入准备提供模板编码 | 已校准 `18868a79`；这是输入准备内部的函数，不是另一个外层阶段 |
| [call_sglang_generate](../02-short-term-memory/functions/slime/agent/adapters/common.py/call_sglang_generate.md) | 请求模型并收集本轮生成记录 | 已校准 `18868a79` |
| [trace_span](../02-short-term-memory/functions/slime/observability/trace_utils.py/trace_span.md) | 记录包围的执行阶段 | 本轮新增并讨论；完整追踪基础设施仍留作后续主题 |
| [PreTrainedTokenizerBase.decode](../02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.decode.md) | 把输出 token 还原为字符串 | 主线中继续使用；外部库卡片保留 Transformers `v4.57.1` 依据，未整卡重写 |
| [parse_model_output](../02-short-term-memory/functions/slime/agent/parsing.py/parse_model_output.md) | 拆出文本、思考与工具调用描述 | 已校准 `18868a79` |
| [BaseAdapter._build_reply](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._build_reply.md) | 形成协议材料与内部消息 | 已校准 `18868a79` |
| [BaseAdapter._respond](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter._respond.md) | 构造普通响应或写出流式响应 | 已校准 `18868a79` |
| [TrajectoryManager.record_turn](../02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.record_turn.md) | 记录本轮轨迹 | 已校准 `18868a79`，包含默认配置影响的说明 |
| [PromptPrefix（类）](../02-short-term-memory/classes/slime/agent/adapters/common.py/PromptPrefix.md) | 组织后续输入可检查的历史候选 | 本轮新增；用户已给出保存材料的初步概括 |

### 主线内部的辅助记录：4 项

| 记录 | 从哪里进入 | 为什么保留 |
| --- | --- | --- |
| [PreTrainedTokenizerBase.apply_chat_template](../02-short-term-memory/functions/src/transformers/tokenization_utils_base.py/PreTrainedTokenizerBase.apply_chat_template.md) | `_render_token_ids` | 2026-10-21 用户要求独立记录；解释模板与编码，当前卡片保留 Transformers `v4.57.1` 依据 |
| [_render_response](../02-short-term-memory/functions/slime/agent/adapters/anthropic.py/_render_response.md) | `_respond` 的普通响应分支 | 此前从 `_respond` 拆出，解释响应字典；本轮核对实现未变并更新源码定位 |
| [web.json_response](../02-short-term-memory/functions/aiohttp/web_response.py/json_response.md) | `_respond` 的普通响应分支 | 此前从 `_respond` 拆出，解释字典如何变成响应对象；保留 aiohttp `3.13.5` 的本地依据 |
| [_render_stream](../02-short-term-memory/functions/slime/agent/adapters/anthropic.py/_render_stream.md) | `_respond` 的流式响应分支 | 此前从 `_respond` 拆出，解释 SSE 写出；本轮核对实现未变并更新源码定位 |

这些文件有明确的调用来路。目录中的 `src/transformers/` 与 `aiohttp/` 对应已经展开过的外部依赖，没有表示本步还要从头通读这些库。

### 具体实现的引用入口：3 项

| 引用文件 | 实际阅读入口 |
| --- | --- |
| [AnthropicAdapter._translate](../02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._translate.md) | common 下的 BaseAdapter._translate 卡片 |
| [AnthropicAdapter._build_reply](../02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._build_reply.md) | common 下的 BaseAdapter._build_reply 卡片 |
| [AnthropicAdapter._respond](../02-short-term-memory/functions/slime/agent/adapters/anthropic.py/AnthropicAdapter._respond.md) | common 下的 BaseAdapter._respond 卡片 |

这三份文件保留继承与实现定位，正文已共用；它们不增加三个需要重新学习的完整模型。

### 早期上游来路：1 项

[BaseHarness.run](../02-short-term-memory/functions/slime/agent/harness/common.py/BaseHarness.run.md) 来自最初的“怎样从 Harness 走到 Adapter”问题，绑定旧版 `2f231865`，仍使用早期格式。当前局部主线已经明确从 `_run_turn` 处理一次请求开始，因此它应标为上游背景，不应与本轮模型处理函数并列成同一层阅读任务。Harness 的详细阅读已另有 [Step 7](../../step-008-harness-communication/README.md)，这也不意味着应该将旧卡的历史状态自动改成后续理解。

## 3. 真正需要整理的地方

- **索引没有清楚区分用途**：主线、辅助、实现引用与上游背景混在同一张表中，容易把所有文件都当成本轮待读清单。建议按上面四类展示，辅助、实现入口和历史来路可默认折叠。
- **源码版本与讨论状态需要分开**：出现在目录中不等于本轮重新展开；实现已核对不等于用户逐项掌握；`_run_turn` 整卡仍待统一校准。外部库卡片继续使用各自版本，不能统一改标为 Slime 提交。
- **不要用删文件掩盖层级问题**：四个辅助函数都有已经发生的阅读来源，三个引用入口承担定位职责。BaseHarness.run 首先应退出本轮主线的展示；是否另行归档，属于后续整理决定。

本轮只完成清点与建议，未移动、删除或重写这些卡片，也未变更 `02 / 03` 的继承规则。
