---
id: doc-004
title: 消息 API Adapter 接口约定与测试案例
type: specification
created_date: '2026-11-17 10:06'
updated_date: '2026-11-17 11:34'
---
# 消息 API Adapter：接口约定与测试案例

2026-11-17。状态：**A 组 adapter 与 B 组本地接入验证已完成；真实 API 已验证；完整 Harbor Trial 待验证**，根据用户确认的“厂商 adapter + Dressage 接入层”分工整理。下文保留设计与后续验收范围，实际完成范围见第 8.3 节。端到端集成仍未完成；实际模型和账户端点需显式配置。

## 1. 这一份方案解决什么

让集成仓库能够把 Dressage 中尚未丢失的 messages/tools 交给厂商 API，并得到可交回 Agent 的结构化回复。首阶段不运行本地模型，不做权重更新，不伪造训练数据。

**停止边界**：先实现一个厂商 adapter 和明确的接入点；不重写整个 SGLang 后端、不引入通用插件平台、不新建任务执行器。记录与结果提交必须随后通过 MH-003 验证，才能声称整条路线可用。

## 2. 代码放在哪里，各自负责什么

```text
agent-api-integration/
├── src/agent_api_integration/
│   ├── contracts.py          # 下文的小型请求、结果类型
│   ├── minimax_adapter.py    # HTTP 请求、厂商响应与错误转换
│   └── dressage_bridge.py    # 消息交接、回复映射及记录兼容边界
├── tests/
│   ├── test_minimax_adapter.py
│   └── test_dressage_result_contract.py
└── third_party/dressage/     # 固定依赖；必要小补丁在 fork 单独提交
```

这是拟新增文件，不表示已存在。源码和测试在 `/home/hongshi/projects/agent-api-integration`；本方案、任务状态和调查证据继续保存在阅读仓库现有 Backlog。

| 部分 | 责任 | 不承担 |
| --- | --- | --- |
| MiniMax adapter | 请求映射、HTTP、响应解析、超时和错误传播 | session 注册、租约、Harbor reward、轨迹提交 |
| Dressage 接入层 | 选择 API 路径，传递消息，关联已有 session/turn，映射为 Agent 回复，将结果交给记录流程 | 厂商鉴权和协议细节 |
| 原框架 | Harbor 任务、工具执行、Verifier 与生命周期 | 不要求 API 模仿 SGLang 的训练元数据 |

方案比较：只更换 SGLang URL 不满足消息/结果合同；把 API 数据硬装进 PreemptibleGenerateResult 会掩盖缺失的训练字段；因此采用独立的消息结果类型和小接入层。先保留现有 SGLang 路径，不强迫它同时迁移到新类型。

## 3. Adapter 输入

建议公开调用为 `await adapter.generate(request)`，由构造参数提供端点、模型凭据和 HTTP client。以下名称是拟议接口，不是原仓库已有符号。

| 字段 | 约定 |
| --- | --- |
| messages | 有序消息列表，保留角色、内容、工具调用 ID 与工具结果对应关系；不得原地修改调用方列表 |
| tools | 可选工具定义；保持结构，不用普通文本拼接代替 |
| max_output_tokens | 本次输出上限；映射到选定厂商协议，不用本地其他模型的 token 数冒称厂商预算 |
| temperature / top_p | 可选；只传选定协议支持的参数，不偷偷忽略明确不支持的值 |
| tool_choice | 可选；当前支持 auto，其他约束效果尚未验证，明确报错；见 8.7 |
| stop | 可选字符串或字符串列表；Bridge 保留要求，None / [] 无约束；当前非空停止要求明确拒绝，见 8.7 |

session/turn/trial 身份留在接入层，与这次调用结果关联，不把它们自动当成模型消息或厂商请求字段。worker_url、SGLang routing_key 和本地权重版本不属于该消息 API 输入。

第一版建议使用非流式厂商调用，返回一份完整结果；这是实现范围，不是断言厂商没有流式能力。对 Agent 的 SSE 响应由接入层对齐现有行为，并需单独测试。

## 4. Adapter 输出：交互结果，不冒充训练结果

| 字段 | 含义与缺省行为 |
| --- | --- |
| content | 可选文本；纯工具调用可以没有文本，不能据此认定失败 |
| tool_calls | 结构化调用列表，含 ID、名称、JSON 参数字符串；没有调用时为空列表 |
| reasoning_content | 可选，仅在协议明确提供可公开字段时映射；不猜测或合成隐藏推理 |
| finish_reason | 规范化的 stop / tool_calls / length / other；未知原因不得静默改成 stop |
| provider_finish_reason | 保留厂商原始原因，供核对映射 |
| usage | 可选计数；缺失用 None，而不是 0；只有厂商提供或明确可计算的值才填写 |
| provider_request_id / model | 可选，保留响应提供的标识；不混同框架 session ID |
| provider_payload | 原始响应正文或无损的协议载荷，用于兼容核对与后续回合；不含请求鉴权 header，不默认写入日志 |

**第一版结果类型不定义伪造的 output_ids、logprob、full_versions。** 厂商将来若提供可信 token 信息，再明确扩展能力；本轮不可把本地重新编码结果当成厂商采样 token。

下面只是拟议的统一结果示例，不是 MiniMax 原始响应、没有真实执行证据：

```text
普通回复：
  content = "测试已通过"
  tool_calls = []
  finish_reason = "stop"
  usage = None                # 未提供，不能解释成零消耗

工具调用：
  content = None
  tool_calls = [{id: "call-1", name: "run_command",
                 arguments: '{"command":"pytest -q"}'}]
  finish_reason = "tool_calls"
```

工具 ID 与参数不能重新随意生成。若协议带有必须随下一回合原样返回的签名或专用内容块，adapter/bridge 必须保留它们；在完成选定协议的回合验证之前，不能声称多轮兼容。

## 5. 错误与资源行为

- 鉴权失败、限流和服务端失败应抛出可区分的错误，保留状态码及允许公开的请求 ID，不返回成功的生成结果。
- 错误消息必须脱敏，不能把 API key、Authorization 或完整敏感请求直接放进异常字符串。
- HTTP 正文不是 JSON、必要响应结构错误或超出首版支持范围时明确报错，不能丢掉工具调用后仅返回文本。工具参数中的字符串属于模型输出，即使不是有效 JSON 也原样保留；是否能执行由工具层解析并校验。
- 超时作为超时暴露；取消继续向调用方传播，不伪装成模型正常停止。
- 第一版不隐式自动重试生成请求，避免重复调用和不可见的费用；重试策略另行明确。
- 复用注入的异步 HTTP client；谁创建谁关闭。adapter 不关闭调用方传入的共享 client。

## 6. 怎样接回 Dressage

```text
pipeline 的 messages/tools 仍可用
  → 接入层选择 API 路径
  → adapter.generate(request)
  ← 上述交互结果
  → 映射 content / tool_calls / finish_reason 等
  ├─ 组织 Agent 响应（JSON 或 SSE）
  └─ 保留 session/turn 归属，进入评测记录流程（MH-003 待验证）
```

这里是拟议接入路径。不能直接把新结果传给现有第 4–5 段然后假设可用：原来读取的是 PreemptibleGenerateResult，且前面仍有本地 tokenizer、worker 租约等依赖。

必须明确隔离四处：启动组件构造；本地分词与 SGLang 调度；生成后的文本 parser；训练字段记录。API 提供结构化工具调用时可直接映射，不经过 SGLang 专属解析器；但必要的工具调用 hooks、会话锁和身份交接不能随 parser 一并删掉。

MH-003 已知限制：require_trainable_tokens=False 不取消 tokens/full_loss_mask/full_logprobs 的结构校验；跳过记录又会使没有 steps 的 finalize 失败。**本文不预先选定空数组、占位轨迹或新存储格式作为解法。**

## 7. 测试案例：先固定行为，再实现

测试放在集成仓库，用可控 HTTP transport 驱动真实 adapter；不 mock adapter.generate 本身。厂商协议选择后，从官方协议构造脱敏 fixture，断言实际发出的请求与解析结果。下表是待实现案例，不是测试报告。

| 案例 | 操作 | 必须断言 |
| --- | --- | --- |
| A1 普通请求与回复 | 输入消息、工具定义和采样参数，返回文本响应 | 发往配置的端点；模型/字段映射正确；不发送 input_ids；输入数据未被修改；输出文本正确 |
| A2 纯工具调用 | 响应有工具调用但无文本 | 保留 ID、名称和参数；不能误判为空响应；finish_reason 映射正确 |
| A3 工具回合 | 第一回合取调用，第二回合带工具结果 | ID 对应正确，历史顺序及协议要求的附加块不丢失 |
| A4 用量和结束原因 | 分别返回缺失 usage、明确零值、截断和未知原因 | 区分 None 与 0；截断为 length；未知原因保留原值且不映射为成功 stop |
| A5 非成功 HTTP | 返回 401、429、5xx | 可区分错误；没有成功结果；默认只请求一次；异常不泄漏凭据 |
| A6 异常正文与坏模型输出 | HTTP 正文非 JSON、缺少关键字段；另测参数字符串非 JSON | 前者明确协议错误；后者保留原始工具调用、assistant 消息与 payload，可交回 API，不修复或执行参数 |
| A7 超时与取消 | 受控 transport 超时或等待中取消 | 向外传播超时/取消；不产生成功记录，不做隐式重试 |
| A8 client 生命周期 | 多次调用注入的共享 client | 正确复用；adapter 关闭行为不误关外部 client |
| B1 现有记录合同 | 对真实 Dressage validate_attempt 输入合法基线、缺字段、关 flag、空数组的对照样例 | 分别断言接受或具体失败类型；通过校验不等于完成提交 |
| B2 最小接回 | 实际接入层接收模拟 API 回复并组织 Agent 响应 | JSON/SSE 和工具调用 ID 正确；必要 hooks 与归属仍在；不是只测独立 adapter |
| B3 结果提交 | 经实际记录方案完成 finalize/read/commit | 消息、归属、reward 可核对；无虚构训练字段；失败不被标记为成功 |

A 组验证 adapter；B 组验证框架衔接。B1 沿用 MH-003；B2/B3 在接入方案明确后实施，不把所有测试并入一次大改。付费 API 和真实 Harbor/沙箱的端到端验证另行记录，不能用 mock 测试替代。

## 8. 开始实现前还需定下的两件事

1. MiniMax 使用哪个协议、模型和账户 Base URL：影响工具回合及 response fixture，须核对对应官方文档；不要读取或展示用户密钥来推断。
2. MH-003 的真实校验结果：据此确定评测记录接缝。A 组可在协议确认后独立实现，但 B 组未通过前不宣布完整接入。

## 8.1 本轮审查与首版实现（2026-11-17）

结论：保留 doc-004 的职责划分，不推翻设计；先实现独立 adapter，bridge 仍待真实接口兼容性验证，不创建空壳冒充接通。

- 源码：`/home/hongshi/projects/agent-api-integration`，分支 `feat/minimax-message-adapter`。新增 contracts.py、minimax_adapter.py、test_minimax_adapter.py 和安装配置；USAGE.md 提供用法。尚未提交或推送本轮实现。
- 首版选 OpenAI 兼容非流式协议，匹配当前 Proxy 的 messages/tools；只接文本与 function 工具。支持显式模型与 HTTPS /v1 地址，不默认读取凭据。
- 官方核对：[MiniMax OpenAI 兼容文档](https://platform.minimax.cn/docs/api-reference/text-openai-api)。多轮保留完整 assistant 消息，输出上限映射 max_completion_tokens；现行 M3 的 temperature/top_p 不生效，因此首版明确拒绝这些显式参数。tool_choice 能力未核对，首版同样拒绝，不静默忽略。其他模型不可据此声称全部兼容。
- 细化输出：除 provider_payload 外增加 assistant_message，供调用方原样保留工具与推理字段。不以拆散后的 content 重建历史。没有定义假 token、logprob 或权重版本字段。
- 测试证据：先运行测试观察 30 项因缺少实现而失败；实现后 30 项通过，补充输入/URL/协议与生命周期边界后，完整项目测试 41 项通过。editable 安装成功。没有网络模型调用、GPU 或沙箱运行；Dressage submodule 未修改。
- A1–A8 按首版支持范围完成；B1–B3 未完成。MH-005 跟踪独立组件交付，MH-003 仍跟踪记录兼容性。模拟 HTTP 成功不代表真实模型/Harbor/Dressage 集成成功。

- src 整理（同日用户要求）：请求消息、工具定义与响应校验各自集中；_parse_response 只校验后组装结果，移除覆盖整个解析过程的异常捕获。错误给出字段路径，不输出原始值；保留网络超时/传输错误的边界转换。
- 历史截断约定（已由 8.2 更新）：finish_reason=length 时保留可能不完整的工具参数文本和完整原始响应，不修复 JSON、不执行工具；调用方先判断结束原因。非截断工具参数及历史消息仍要求有效 JSON 对象。已同步 contracts.py 与 USAGE.md。
- 整理后的完整验证：49 项测试通过（原 41 项 + 8 项字段定位/截断/历史校验案例），git diff --check 通过。新增案例先复现旧实现的错误定位缺失与截断拒绝；均为合成 HTTP 验证。仍未提交推送、未接通 bridge、未调用真实模型。

## 8.2 按 Slime 风格收窄 Adapter 职责（2026-11-17）

用户确认：精简校验职责，而不只是将校验搬进更多函数。保留现有 contracts / provider adapter / 后续 bridge 分工。

- 删除历史消息的角色枚举、工具关联、参数 JSON 与嵌套工具 schema 校验；仅检查消息列表、文本内容和 function 工具范围。供应商的校验失败作为 HTTP 错误传播，不声称任意历史都能被接受。
- 删除请求 JSON 的预序列化检查，交给 HTTPX 正常序列化；删除 usage 内部计数的语义检查，保留原始值，供统计消费方验证。
- 工具返回仅检查基本协议结构。arguments 必须是字符串，但无论 stop、tool_calls 还是 length，其中无效或不完整的 JSON 都不使整份响应失败。工具层负责参数解析、schema 校验和错误反馈；保留结果不代表批准执行。
- 保留 HTTP/超时/传输错误区分、必要响应结构检查、字段定位、client 所有权、原始 assistant 与 payload、缺失 usage 和未知结束原因。
- 删除 _validate_messages、_validate_tools、共享 _validate_tool_calls；响应检查与组装回到 _parse_response，工具结构留一个局部 helper。minimax_adapter.py 从 258 行变为 201 行；本次没有创建更多文件或依赖。
- 验证：先观察新行为的 10 项失败，再实现；完整项目 55 项测试通过。覆盖坏参数保留和后续历史重放、供应商拒绝历史的错误传播、usage 原样交付；原有网络、取消、资源和结构错误测试保持。fixture 为合成数据，不是线上 MiniMax 接受历史的证据。
- contracts.py、USAGE.md 与测试说明已同步；Dressage 子模块仍为 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。未调用真实 API、未接入 bridge，未提交或推送。

## 8.3 结果合同测试与消息分支接入（2026-11-17）

保留原设计并实现 B1–B3。实际落点为独立仓库 `src/agent_api_integration/dressage_bridge.py`、`serve.py`，以及 Dressage fork 的 `create_app(message_backend=...)` 与 `proxy/message_backend.py`。普通路径仍 tokenization → SGLang；消息路径在 tokenization 前进入 adapter。SessionManager、锁、hooks、finalize/read 和 HarborArtifactStore 使用原组件。

结果约定：记录 tokens/full_logprobs/full_loss_mask 为明确空数组，full_versions 为 None，不生成假训练数据。消息与标准化 API 回复放在 extra_info.api_turns，hooks 审计放在 extra_info.tool_call_hooks。身份、finalization_id、finalization_complete、reward 仍按原协议校验。require_trainable_tokens=False 只适用于评测；training guard 不改。

完成验证：自有 76 项测试通过（含原 token 路径最小回归），上游 ProxyClient/SessionManager 10 项通过；实际 Uvicorn 启动及能力 HTTP 接口通过，未调用模型。全量上游 test_proxy.py 因未安装 PyTorch 无法收集。独立复核后修复生成控制参数静默丢失及 hooks 审计丢失，均先失败再通过。

运行说明见独立仓库 USAGE.md；Harbor 插件配置 configs/harbor-api.json 已校验，但不是完整 Harbor Job 配置。尚未运行真实 MiniMax、Harbor Agent/Gateway/Verifier、Agent Sandbox、Slime 发起端。SSE 为现有心跳 + 完整回复后的伪流式，不是供应商逐 token 流式。未映射生成控制参数明确 400，后续真实 Agent 默认参数需要核对。

Dressage fork 独立本地提交：3820149ebfc0536b213ec120b43ec090f09b3fcd。本轮没有 push，适配仓库工作区改动尚未提交。MH-003 与 MH-006 已完成此处限定的验证范围；真实端到端运行另行记录，不把测试成功等同训练可用。

## 8.4 Bridge 的职责与代码阅读层次（2026-11-17）

用户反馈：contracts 和 MiniMax adapter 尚能理解，但不清楚 bridge 的职责；主要逻辑与防御代码交织，影响阅读。此为实际疑问，不记录为已经掌握。

核对：bridge 把 Proxy body 字典转换为 GenerationRequest，调用 adapter，再将 GenerationResult 整理为 Proxy 回复字典。请求参数别名、响应外壳与结束原因映射属于主流程；异常转换属于 HTTP 边界。会话、hooks 和轨迹仍在原 Proxy。

按反馈将 complete() 排为三段，直接保留输入/输出字段映射；参数检查提到文件下方 _check_supported_controls，异常映射集中于 _generate_with_http_errors，生命周期保留 aclose。没有新增文件、协议或装饰器，也没有扩大捕获范围或删除校验。此处两项辅助方法分别有明确职责，不为每几行字段映射继续拆函数。

源码：独立实施仓库 src/agent_api_integration/dressage_bridge.py；USAGE.md 新增“怎样读 DressageBridge”。既有完整 76 项测试通过，覆盖原正常/失败行为。未修改 Dressage submodule，未 commit 或 push 本轮整理。

## 8.5 将同样的阅读层次应用到 MiniMax adapter（2026-11-17）

用户确认 bridge 的主线与防御逻辑分开后更清楚，明确要求 MiniMax adapter 沿用。generate 现在按请求组装、HTTP 发送/JSON 读取、结果转换三步展示；_request_body 与 _parse_response 保留真实字段映射。HTTP 错误转换集中在 _post_json，参数与协议检查放入文件下方的 _validated_endpoint、_check_request、_check_response；错误类型也移到下方，打开文件先看到 adapter 主体。资源生命周期集中保留。

职责和公开接口不变，不新增字段级包装、不改变合同或删除校验；既有 76 项测试通过。未修改 Dressage 子模块，未 commit/push。源码仍为独立实施仓库 src/agent_api_integration/minimax_adapter.py，USAGE.md 同步阅读入口。

## 8.6 原协议转换层接入 API 后端（2026-11-17）

以下保留修订前历史；stop/tool_choice 当前支持范围以 8.7 为准。

2026-11-17 替换兼容性验证：新增 tests/test_rollout_proxy_api.py 的 9 个案例，使用真实 RolloutLLMProxy.app→真实中央 Proxy→adapter，仅供应商 HTTP 模拟。OpenAI/Anthropic × 普通/SSE 四条通过；Anthropic 工具调用→tool_result→第二次生成通过，身份、finalize/read 保留。temperature/top_p/stop_sequences（包括空列表）/tool_choice 四种显式参数仍得到400，未静默忽略。完整项目87项通过。
随后以本地.env发出一次真实请求：合成Anthropic /v1/messages→未改的RolloutLLMProxy→中央Proxy→MiniMax；HTTP200，返回OK，stop_reason=end_turn，1.50s，转换后的usage input_tokens=204/output_tokens=17，finalize1step/read1record。未输出密钥。此检查替换了HTTP传输为ASGI内存传输，未覆盖Gateway路由凭证分配、真实Agent CLI、Harbor Trial/Verifier/环境；不得冒称完整Trial通过。未改RolloutLLMProxy或其他生产逻辑。结论：支持范围内的模型后端替换已验证；任意Agent配置不能直接照搬，下一步按MH-001准备固定Harbor与单Trial配置。

## 8.7 保留控制意图，按参数取值适配（2026-11-17）

2026-11-17 参数兼容性修订：用户指出替换后端应保留原 Agent 的控制意图，不能因尚未核对就将整个可选字段拒绝。新 GenerationRequest.stop 保存字符串或字符串列表；Bridge 将 stop/tool_choice 交给 Adapter 决定能力。None/[] 不设置停止约束；auto 原值转发。非空 stop 及非 auto 选择模式仍明确拒绝，不静默降级；UnsupportedControlError 映射为包含字段和限制的安全 400。非法空字符串、非字符串列表元素及其他类型也拒绝。未改动 Dressage 子模块，未改变 temperature/top_p 范围。

证据分层：MiniMax Anthropic 兼容文档列出 auto 支持、stop_sequences 忽略；不能直接视为 OpenAI 接口同样支持。另向实际 api.minimax.cn/v1/chat/completions、MiniMax-M3 发三次探测：auto→200/READY；stop=[CUT_HERE]→200但返回 READY CUT_HERE AFTER.，证明该次并未执行停止约束；指定工具→length/无工具，输出预算512，该结果不充分，不能宣称支持或普遍不支持强制调用。

先加回归出现21项预期失败，再实施修订，完整109项通过。包含真实转换器 OpenAI/Anthropic × JSON/SSE、含auto的两轮工具消息交接、空stop、错误类型、约束失败以及不泄露参数值。修改后再发一次真实请求：合成Anthropic请求含空stop_sequences与auto→原转换器→中央Proxy→新Adapter→MiniMax，HTTP200/OK/end_turn，1.15s，finalize1step/read1record。内部HTTP为ASGI；未运行Harbor Trial、真实Agent CLI/Verifier/沙箱。USAGE与测试说明同步；未commit/push。

官方依据：[Anthropic 兼容接口](https://platform.minimax.cn/docs/api-reference/text-anthropic-api)、[OpenAI 兼容接口](https://platform.minimax.cn/docs/api-reference/text-openai-api)。

## 9. 来源与当前状态

- Dressage 基线：3e3142fe8ea07e4504c3b20a936a4c201a3de44c；集成骨架提交 cccd48ad92cf9893fa63939d6519b09e771a6bd7。
- [Step 006 pipeline 函数卡](../../../../topics/01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/dressage/proxy/server.py/create_app._chat_completions_pipeline.md)：现有 3–6 段和当前数据交接。
- [MH-002](../tasks/mh-002%20-%20核对-MiniMax-消息接入边界与初始化依赖.md)：输入与初始化边界。
- [MH-003](../tasks/mh-003%20-%20核对-API-缺少训练字段时的结果记录合同.md)：记录消费者调查与本地合同验证已完成，见 8.3。
- 原方案经 8.1、8.2、8.3 逐步实现；当前接入及验证边界结合 8.3、8.6、8.7 查看，前文保留当时记录。
