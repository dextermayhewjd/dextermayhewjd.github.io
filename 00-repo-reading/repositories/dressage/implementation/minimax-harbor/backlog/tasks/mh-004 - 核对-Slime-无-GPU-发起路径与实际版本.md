---
id: MH-004
title: 核对 Slime 无 GPU 发起路径与实际版本
status: To Do
assignee: []
created_date: '2026-11-17 06:51'
labels:
  - phase-1
  - migrated
dependencies: []
documentation:
  - backlog/docs/doc-003 - 接口调查与待确认事项.md
  - backlog/docs/doc-002 - 总体路线与验收边界.md
  - backlog/docs/doc-001 - 迁移前原文快照.md
  - backlog/decisions/decision-001 - 先完成无-GPU-API-评测链路，再接-Agent-Sandbox.md
type: spike
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
原 Q03。此前独立 Slime 18868a79 的 train.py 在 eval-only 判断前涉及训练模型与权重同步；Dressage gitlink 实际是 aaf5c209 且当时尚未初始化。因此旧观察不能直接外推。需要核对实际选用版本与无 GPU 发起路径，不能随意下载模型凑齐初始化。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 明确采用的 Slime 路径和提交，以及它与 Dressage 固定子模块和旧阅读版本的关系。
- [ ] #2 在实际版本定位启动至 rollout 发起/接回的路径，列清训练模型、SGLang 与 GPU 的初始化触发条件。
- [ ] #3 给出无 GPU 的最小发起方案和验证命令；若现有配置不能满足，指出最小适配边界及阻碍，不把方案记成已跑通。
<!-- AC:END -->
