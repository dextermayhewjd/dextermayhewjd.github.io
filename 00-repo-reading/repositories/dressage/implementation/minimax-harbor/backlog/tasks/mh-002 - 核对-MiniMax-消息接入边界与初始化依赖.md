---
id: MH-002
title: 核对 MiniMax 消息接入边界与初始化依赖
status: Done
assignee:
  - '@codex'
created_date: '2026-11-17 06:51'
updated_date: '2026-11-17 08:08'
labels:
  - phase-1
  - migrated
dependencies: []
documentation:
  - backlog/docs/doc-003 - 接口调查与待确认事项.md
  - backlog/docs/doc-002 - 总体路线与验收边界.md
  - backlog/docs/doc-001 - 迁移前原文快照.md
  - backlog/decisions/decision-001 - 先完成无-GPU-API-评测链路，再接-Agent-Sandbox.md
  - >-
    ../../topics/02-harbor-integration/steps/step-014-model-routing-and-api-contract/01-scope.md
  - >-
    ../../topics/01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md
type: spike
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
原 Q01。Dressage 3e3142fe 的 server.py:1939,2087 从 messages/tools 构造 token 输入，默认 create_app 又涉及 tokenizer；SGLang 客户端接受 input_ids。需要确定消息 API 的最小适配位置，不能只替换 URL。此任务先给出可验证的接入结论，不预先认定必须改 GenerationController，也不自动包含完整实现。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 标出固定版本中 messages/tools 到生成调用的实际路径、关键输入输出及初始化依赖。
- [x] #2 比较可复用配置与候选接入点，明确是否需要避开 tokenizer 初始化，并列出结论依据和未验证部分。
- [x] #3 给出后续最小协议验证范围：消息、工具调用、响应和错误；不把静态核对记作真实 MiniMax 调用通过。
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. 从 Step 014 的 Gateway 交接位置回接 Step 006 的模型请求主线，复用已有函数卡。
2. 在固定 Dressage 提交核对消息到 token 的变化、真实发送点和初始化依赖。
3. 比较现有配置与候选适配边界，记录响应及结果保存需要联合核对的部分。
4. 给出最小后续协议验证范围；仅完成静态调查，不执行 API、训练或沙箱。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## 本轮结论：发送位置不等于适配位置

2026-11-17 静态调查。按已有 Step 014 → Step 006 回接源码，没有从搜索命中直接推断改造点。实际 checkout 为 `/home/hongshi/projects/Dressage`，HEAD `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`，本轮前后源码工作区未改动。

**推荐候选边界：Dressage Proxy 收到结构化 messages/tools 后、执行 `_build_prompt_tokens` 前。** 此处仍有完整请求语义，适合将外部消息 API 与既有 token/SGLang 路径分开。这个结论不是完整补丁设计：`create_app` 初始化和结果记录合同必须一并处理，不能只在 pipeline 中插入一次 HTTP 调用。

## 阅读入口与调用关系

- [Step 014：第 3.2 节第三部分，Gateway 请求分派](../../../../topics/02-harbor-integration/steps/step-014-model-routing-and-api-contract/01-scope.md#reading-part-3)。这里解释请求来自 Harbor Agent，而不是另启动原生 blackbox dispatch。
- [Step 006：第 9.2b–9.2e 项，共享模型请求流水线](../../../../topics/01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md#model-request-reading)。沿已有 pipeline 和 generate 函数卡回查；本轮不重建卡片、不宣称用户已掌握全部内部实现。

```text
Harbor Agent 运行期间发 HTTP 请求
  → _GatewayASGI._handle_http：token 找到本次 Trial 的 binding
  → binding.proxy.app：进入 RolloutLLMProxy
  → _handle_proxy：把选定的 Anthropic 请求转为 OpenAI messages/tools
  → _stream_anthropic_messages_proxy → _send_stream_request
  == HTTP ==> Dressage Proxy /chat/completions
               → _chat_completions_pipeline：接住 messages/tools
               → _build_prompt_tokens：变为 input_ids
               → generate_preemptible
               → _generate_with_optional_request_id
               → SGLangRouterClient.generate
               == POST /generate ==> 推理后端
               ← SGLangResponse（文本、token、概率等）
               → 解析回复 + 记录 StepRecord + 组织响应
  ← RolloutLLMProxy 转换响应给 Harbor Agent
```

这是当前选定的 Anthropic 流式请求路径示意；HTTP 边界不是同步 Python 子调用，流式响应也不等于后端逐 token 实时返回。其他 Agent 协议路径按需另查。

## 源码核对

| 位置 | 输入 → 行为 → 输出 |
| --- | --- |
| [dressage/integrations/harbor/plugin.py:1031](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L1031) | `_inject_agent_routing` 为 Agent 配置 OPENAI/ANTHROPIC 地址，指向 Gateway |
| [dressage/integrations/harbor/gateway.py:670](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L670) | `_create_proxy` 将 upstream_origin、trial/session 身份、model_override、upstream_headers 等交给 RolloutLLMProxy |
| [dressage/integrations/harbor/gateway.py:864](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/gateway.py#L864) | `_handle_http` 解析路由 token、查 binding、重写请求，随后调用 binding.proxy.app；不是直接调用模型客户端 |
| [blackbox_server/proxy/rollout_llm_proxy.py:421](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/proxy/rollout_llm_proxy.py#L421) | `_handle_proxy` 的 Anthropic 分支调用 `_anthropic_messages_to_openai_chat_completion`，结果仍为结构化消息 |
| [blackbox_server/proxy/rollout_llm_proxy.py:1445](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/blackbox_server/proxy/rollout_llm_proxy.py#L1445) | `_send_stream_request` 使用 httpx 构造 POST 并 send(stream=True)，这是转发到上游 Proxy 的发送点 |
| [dressage/proxy/server.py:1939](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L1939) | pipeline 读取 messages、model、tools、stream，确定 session/turn；保留身份与并发管理语义 |
| [dressage/proxy/server.py:2079](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L2079) | 调用 `_build_prompt_tokens`，随后取 prompt_payload['input_ids']；从消息语义进入本地模型 token 合同 |
| [dressage/proxy/server.py:2198](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L2198) | 将 input_ids/sampling_params/session/worker 等交给 generate_preemptible |
| [dressage/proxy/generation_controller.py:675](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/generation_controller.py#L675) | 只为客户端签名选择 request_id、worker_url 等兼容参数；并不恢复原始 messages/tools |
| [dressage/proxy/sglang_client.py:176](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/sglang_client.py#L176) | 组装 input_ids/sampling_params/return_logprob 等并 POST /generate，返回 `_coerce_response` 的 SGLangResponse |
| [dressage/proxy/server.py:2313](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L2313) 与 [dressage/proxy/server.py:2479](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L2479) | 消费生成文本、token、概率、版本，并写 StepRecord；说明只让 Agent 收到回复还不足以完成本路线 |

## 候选方案比较与初始化依赖

1. **只换 SGLangRouterClient 的 URL：不适合。** 当前请求和响应都是 SGLang/token 合同；MiniMax 消息接口不能据此视为兼容。不能用另一个 tokenizer 重新分词后冒称得到厂商真实训练 token。
2. **配置 RolloutLLMProxy 直接转发厂商：可以作为消息转发候选，不能宣称完整接通。** upstream_origin/upstream_headers/model_override 已可传入，但会绕过 Dressage Proxy 的 StepRecord 路径；会话管理、结果提交及敏感 header 的处理需要单独核对。配置可复用不等于 ArtifactStore 可用。
3. **在 Dressage Proxy 的消息边界分出厂商路径：优先调查的方案。** 可保留上游 Gateway/Agent 协议和身份交接；但应分开 token 输入、SGLang 专属解析/调度与厂商响应，不把两种合同混成虚假的 SGLangResponse。

`create_app` 的初始化在请求前已经发生：[dressage/proxy/server.py:881](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L881) 在未注入 tokenizer 时要求 tokenizer_path 并调用 AutoTokenizer.from_pretrained；891 起创建 SGLangClient、GenerationController 和 EngineRebalancer；TITO 路径要求支持的模型并配置模板，944 起创建依赖 tokenizer 的 mask_builder，以及模型结果解析器。

因此 **只给 pipeline 增加分支，不能避开已有初始化依赖**。已有 tokenizer/client 注入参数可辅助测试，但不是现成的无 tokenizer 厂商 API 运行模式。纯消息路径原则上不需要本地分词模型；具体怎样在启动阶段选择不同组件，留给实施方案，不预先新建完整 provider 框架。

## 后续最小验证合同（本轮未运行）

| 验证 | 需要观察的结果 |
| --- | --- |
| 文本请求 | messages 与采样参数正确传给选定厂商接口；收到可被上游识别的 assistant 回复 |
| 工具回合 | tool 名称、参数、call ID 和工具结果对应；下一次请求保留必要历史字段 |
| 协议回传 | 选定的 streaming/non-streaming 模式、结束原因、usage 和错误能回到 Agent；不默认两种模式均已兼容 |
| 故障 | 认证、限流、超时和取消不会被记成正常成功；敏感凭据不进入日志 |
| 身份与记录交接 | session/turn 归属正确；消息与现有真实返回字段可保存；缺失训练字段明确处理，不伪造 |

前三类可先用模拟响应验证本地合同，再真实调用验证厂商兼容性。最后一项需要 MH-003 继续核对记录消费者，不在本轮声称已解决。具体 MiniMax 模型、账户 Base URL 和实际参数支持尚未确定；因此方案是有依据的候选，不是已运行的集成结论。

## 验收证据边界

本任务三项验收是静态调查产物：调用链/初始化、候选比较、后续协议验证范围，均在上文给出。本轮没有安装依赖、发送 API、启动沙箱、执行集成测试或修改源码；MH-001 和 MH-003/MH-004 的工作没有因此完成。

## 2026-11-17 带读补充：消息在哪里变成 token，以及为何影响接入

- **源码事实（3e3142fe，首条请求分支）**：pipeline → `_build_prompt_tokens` → `_full_prompt_token_ids` → `mask_builder.tokenize_messages` → `_apply_chat_template(tokenize=True)` → `tokenizer.apply_chat_template`。`input_ids = prompt_payload["input_ids"]` 只是取结果，不是分词。
- **用途**：对话模板按模型约定表达角色、消息边界、工具定义和助手生成提示；tokenizer 再将其编码为整数 token IDs。它减少结构表达的歧义，并保持模型输入格式一致，不保证消除自然语言歧义或使模型遵守全部指令。
- **对实施的影响**：当前目标是厂商消息 API，应保留 messages/tools 作为适配输入，避免先用本地模型 tokenizer 编码后直接发送。具体 MiniMax 接口支持、参数与响应仍需验证；不据此认定已完成适配。
- **阅读位置**：[Step 006 scope 3.2 的 9.2b.1](../../../../topics/01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md) → [独立 _build_prompt_tokens 函数卡](../../../../topics/01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/dressage/proxy/server.py/create_app._build_prompt_tokens.md)。函数卡保存代码与理解过程，本任务保存影响实施的结论和待验证事项。
- **用户当前问题（原话）**：“主要是哪里从文字被tokenizer 变成token的是需要了解的对吗？”随后追问这样做的好处与歧义。不能将助手给出的解释当成用户已掌握全部实现。
- **状态说明**：本次补充静态调查证据，MH-002 的 Done 仅指调查交付完成；未调用真实 API、未运行 tokenizer、未改造源码。后续请求的 TITO 历史复用不属于本次首请求结论。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
完成固定提交 3e3142fe 的静态接入调查，沿 Step 014 → Step 006 核对请求链路、tokenizer 初始化及结果记录依赖。建议在 messages/tools 转 token 前调查厂商分支，不能只替换 SGLang URL。已记录候选比较与后续协议验证范围；未调用 MiniMax、未运行集成测试、未修改 Dressage 源码。
<!-- SECTION:FINAL_SUMMARY:END -->
