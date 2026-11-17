---
id: MH-005
title: 实现 MiniMax 消息 Adapter 与协议测试
status: Done
assignee:
  - '@codex'
created_date: '2026-11-17 10:22'
updated_date: '2026-11-17 11:44'
labels: []
dependencies: []
documentation:
  - backlog/docs/doc-004 - 消息-API-Adapter-接口约定与测试案例.md
type: feature
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
落实 doc-004 的独立 adapter 范围：OpenAI 兼容消息请求、结构化回复、错误与资源管理。保留完整 assistant 消息，不伪造训练字段；不声称接通 Dressage bridge 或完成 MH-003。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 消息与工具请求正确映射，保留完整 assistant 消息用于后续回合
- [x] #2 未知结束原因、缺失用量、错误、超时和取消有明确行为且不泄漏凭据
- [x] #3 模拟 HTTP 测试及整个独立项目测试通过，使用文档明确未验证的端到端边界
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. 固定 OpenAI 兼容非流式协议；模型与地址显式配置，不支持参数明确拒绝。2. 先写真实 adapter 的 MockTransport 测试并观察失败。3. 实现 contracts 和 minimax_adapter，不创建空 bridge。4. 运行完整测试并更新证据与使用说明。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
实现目录 /home/hongshi/projects/agent-api-integration；分支 feat/minimax-message-adapter。保留 doc-004 分工，首版 OpenAI 兼容非流式 MiniMaxAdapter + GenerationRequest/GenerationResult，不创建空 bridge，不修改 Dressage submodule。

实测：新增测试先有 30 项失败（缺实现）；实现后 30 项通过；边界测试补齐后完整 pytest 为 41 passed in 0.12s。pip install -e . --no-deps 构建并安装成功。git diff --check 通过。Python 3.12.3 / httpx 0.28.1 / pytest 9.2.0 / pytest-asyncio 1.5.0。

覆盖请求/工具回合保真、未知结束原因、缺失用量、HTTP 非成功无重试无重定向、错误脱敏、JSON/协议错误、超时取消、client 所有权和文本/URL边界。源码/测试未提交推送，具体文件见 USAGE.md。

剩余限制：无真实 API 验证；无 Dressage bridge、SSE 回程或轨迹提交验证；B 组/MH-003 未完成。模型/端点由使用者配置，显式 temperature/top_p 和未验证 tool_choice 会拒绝；不宣称任意模型兼容。

按用户对 try/raise 过多的反馈整理 src：请求/响应校验集中，移除整个解析过程的广泛捕获，报告安全字段路径。length 截断响应保留不完整工具参数并要求调用方先判断结束原因；非截断及历史参数仍严格校验。新案例复现后修复，完整 pytest 49 passed in 0.14s；git diff --check 通过。contracts/USAGE 同步说明；不改变公开接口，不修改 Dressage，不声称端到端完成。

用户确认参照 Slime 收窄校验职责，详见 doc-004 8.2：去掉历史语义/嵌套 schema/usage 计数和重复序列化检查；工具参数作为原始模型输出保留，工具层负责解析执行。必要协议结构、网络与资源管理不变。先复现 10 项新预期失败，实现后完整测试 55 项通过；adapter 258→201 行。文档同步，无真实 API 或 bridge 验证，未提交推送。

2026-11-17 用户确认 bridge 的可读性整理后，要求 MiniMax adapter 沿用：generate 保留请求组装→发送→结果转换主线，参数/协议检查及错误处理独立成块；实际映射可直接阅读。既有 76 项测试通过，说明见 doc-004 §8.5。

2026-11-17 任务审计：当前实现已提交至 agent-api-integration 53423621e2bb146638e9a187c52d67803def071d。重新运行 .venv/bin/python -m pytest -q：109 passed in 0.68s（整个项目，非独立 adapter 测试数量）。沿用此前已确认的沙箱外测试方式，供应商 HTTP 为模拟，未读取或提交凭据。三项验收保持通过。早期笔记中的未提交、无 bridge、MH-003 待验证为当时历史状态；当前 bridge 与真实 API 的后续证据见 MH-006，MH-003 已完成。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
独立 MiniMax 消息 adapter、完整 assistant/工具消息保留、错误及资源管理已完成。当前 stop=None/[] 与 tool_choice=auto 受支持，非空停止约束及未经验证的工具选择明确拒绝。源码已包含于 5342362；本轮全项目 109 项离线测试通过。后续 bridge 和有限真实 API 验证见 MH-006；真实 Agent/Verifier/Harbor Trial、Slime 和 K8s 不在本任务完成范围。
<!-- SECTION:FINAL_SUMMARY:END -->
