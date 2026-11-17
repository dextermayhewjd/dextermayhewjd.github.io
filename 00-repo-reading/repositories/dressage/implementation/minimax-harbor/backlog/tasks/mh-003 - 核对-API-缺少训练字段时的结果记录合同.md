---
id: MH-003
title: 核对 API 缺少训练字段时的结果记录合同
status: Done
assignee:
  - '@codex'
created_date: '2026-11-17 06:51'
updated_date: '2026-11-17 11:44'
labels:
  - phase-1
  - migrated
dependencies: []
documentation:
  - backlog/docs/doc-003 - 接口调查与待确认事项.md
  - backlog/docs/doc-002 - 总体路线与验收边界.md
  - backlog/docs/doc-001 - 迁移前原文快照.md
  - backlog/decisions/decision-001 - 先完成无-GPU-API-评测链路，再接-Agent-Sandbox.md
  - backlog/docs/doc-004 - 消息-API-Adapter-接口约定与测试案例.md
type: spike
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
原 Q02。Dressage pipeline server.py:2479 和 Harbor artifacts.py 处理 token/logprob/版本及会话轨迹。静态记录表明 config.py 有 require_trainable_tokens，training 强制开启，rollout 没有相同强制。仍需核对完整 finalize/read/commit 路径；这不代表现有配置已验证可用。此任务确定评测结果应怎样保留，不伪造训练字段。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 列清 API 响应缺少 token ID、logprob、权重版本时，相关记录和消费者各自要求哪些字段。
- [x] #2 核对 rollout 模式现有配置能否贯通结果提交，区分静态判断、最小本地验证与尚待真实 API 的部分。
- [x] #3 保存缺失字段样例的接受/拒绝行为或明确验证阻碍，并形成保留现有配置或需要适配的结论。
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. 从 Step 006 第 5 段区分评测必需信息与现有 token 依赖。
2. 沿记录、finalize/read、commit 校验关键消费者。
3. 后续以最小缺失字段样例验证兼容性，保留静态与运行证据的区别。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## 2026-11-17 第 5 段必要性核对（静态调查，未完成整任务验证）

用户要求先由助手核对必要内容，并将不必深入的部分写入任务。阅读入口为 Step 006 的 pipeline 第 4→5 段，固定 Dressage 提交 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。本轮不新增阅读步骤或实现任务。

### 对当前目标的分类

| 内容 | 无 GPU、厂商 API 评测是否需要 | 当前代码约束 / 处理原则 |
| --- | --- | --- |
| 请求/回复消息、工具调用、结束状态 | 需要保留，支持继续执行与复盘 | 第 5 段保存 request_messages/messages/raw_response_text/tools/finish_reason；API 原始返回与整理后的结构应能对照 |
| session/instance/turn/attempt 归属与完成标记 | 需要，避免交互和结果错配 | 原调用链在不同层保存这些身份；ArtifactStore 校验 segment 身份与原子完成快照，不只看 reward |
| Verifier 的 reward 与失败信息 | 需要 | reward 来自 Harbor TrialResult，不是模型 API 必须返回；validate_attempt 校验指定 reward_key 的有限数值 |
| API 提供的 usage、模型名、耗时与错误 | 对评测分析有用，保留真实可得值 | 不等于每项都是当前 validate_attempt 的必填字段；具体缺省表示还需协议验证 |
| 生成 token IDs、逐 token logprob、loss mask | 不作为本次评测目标的必需产物，但当前代码依赖它们 | 不能直接删除或用伪造概率冒充真实采样数据；需决定评测记录如何兼容或分开 |
| 每 token 权重版本 | 本次不做训练/权重同步，无须复刻训练语义 | require_token_versions 及 expected_weight_version 的约束要一起检查；不能只关一个 flag |
| TITO 增量拼接、snapshot token、routed experts、训练 mask 构造算法 | 当前不要求学习者深入 | 后续改造仍要识别引用并隔离；“不精读”不表示可不检查就删掉 |

### 已核对的硬约束

1. server.py:2479 的 `_record_step_atomically` 传入 token、logprob、快照、版本、消息及归属；该包装经 `_record_step`（:1106）进入 SessionManager.record_step。session_manager.py:416 的签名要求多个 token/logprob 实参；因此“业务目标不需要”不等于当前函数允许省略。
2. server.py:2751 的 finalize_session 在没有 session.steps 时返回 400；后续构建轨迹段。因此不能简单跳过第 5 段，又假设原来的 finalize/read/commit 会照常通过。
3. artifacts.py:307 `_commit_attempt_once` 先 finalize、再 read_trajectory、提取 segments，并从 TrialResult 提取 reward，随后调用 validate_attempt。
4. artifacts.py:847 附近的 validate_attempt 无条件拒绝空 segments；无条件检查每段 tokens/full_loss_mask/full_logprobs 为 list 且长度一致，并检查类型与数值。`require_trainable_tokens=False` 只放宽末尾的“至少有一个可训练 token”检查，不关闭这些结构检查。
5. `full_versions` 的强制存在受 require_token_versions 或 expected_weight_version 控制；提供了非空版本数组仍须长度匹配。版本开关不能改变 token 数组的其他校验。
6. artifacts.py:722 的 `_trajectory_finalization_failures` 校验 segment 序号/数量、trajectory_id、instance_id、segment_view、finalization_id 和 finalization_complete。消息有无 token 与结果是否属于同一个完成快照，是两种不同要求。
7. config.py:217 起 training 模式强制 require_trainable_tokens=True；rollout 未施加同样限制，但“配置允许”不能证明整条记录路径可用。

### 当前结论与停止点

- 学习者当前只需理解“保存消息与归属”和“原系统还依赖训练数组”两层，不必精读 TITO、loss mask、专家路由或原子提交包装内部。
- 接入工作必须验证记录链兼容性；仅关闭 require_trainable_tokens，或仅让 Agent 收到 API 回复，都不足以证明集成完成。
- 本轮不选定实现方案，不宣称空数组、占位 segment 或新增消息记录格式已经可用。不复制旧项目填 0.0 概率的做法来宣称取得真实 logprob。
- 待验证：最小缺失字段样例的实际接受/拒绝、Proxy finalize 轨迹构建及最终 rollout 消费路径，之后才能判断现有配置是否够用或必须改记录接口。现有三项验收暂不勾选，任务保持 In Progress。

阅读卡：[pipeline 第 5 段](../../../../topics/01-native-agent-rollout/steps/step-006-agent-execution/02-short-term-memory/functions/dressage/proxy/server.py/create_app._chat_completions_pipeline.md#pipeline-record)。本轮仅静态源码核对，没有调用真实 API、启动沙箱或修改 Dressage 源码。

2026-11-17 实际验证与接入：
- B1：真实 validate_attempt 的 4 个测试，确认缺少 tokens/full_loss_mask/full_logprobs 仍被拒绝；明确的空数组 + 正确身份/完成标记 + require_trainable_tokens=False 接受为非训练评测记录，训练要求仍拒绝。
- B2/B3：新增 DressageBridge、固定 fork create_app(message_backend=...) 与 message_backend.py。分支在 tokenization 之前，复用 SessionManager/request_lock/hooks/finalize/TrajectoryStore；真实 ProxyClient 和 HarborArtifactStore 完成模拟 HTTP 两轮回复、finalize/read/commit、重复提交、磁盘保存与 manifest。reward 由最小 TrialResult fixture 提供，没有运行 Verifier。
- 自有测试 76 passed；固定上游 test_proxy_client.py + test_session_manager_cleanup.py 10 passed；原 token 路径另有最小生成/finalize/关闭回归（包含在 76 项中）。完整上游 test_proxy.py 因缺少 PyTorch 无法收集，不宣称全套 SGLang 回归完成。
- 实际启动 Uvicorn factory 并通过 localhost HTTP 读取 integration/capabilities，确认 messages 模式、trainable=false；随后正常停止。使用虚构凭据和 provider.invalid，未调用供应商。
- 新增 configs/harbor-api.json 并通过真实 HarborIntegrationConfig 校验；USAGE.md 给出安装、启动与配置交接。没有安装/运行 Harbor runtime、Agent CLI、真实 Gateway、Verifier、Agent Sandbox 或 Slime 发起端。
- 独立复核发现未映射生成控制参数静默丢失、hooks 审计丢失；新增 6 个失败测试后修复，完整套件通过。另修复 X-Dressage-Expected-Version 检查并测试。
- 决定：沿用明确空数组的现有评测校验语义，不伪造 IDs/logprobs/versions；保留 training guard，因此仍不能从 Slime 训练入口直接使用非训练 bundle。若误把本验证等同端到端训练，会跳过必要前置，文档已明确区分。
- 独立 fork 补丁提交 3820149ebfc0536b213ec120b43ec090f09b3fcd（feat/message-api-backend），上游基线 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。本轮不推送远端；适配仓库代码仍为本地改动。

2026-11-17 任务审计：在实施仓库 5342362 / Dressage 3820149 重新运行 .venv/bin/python -m pytest -q，109 passed；结果合同与真实 finalize/read/HarborArtifactStore 测试包含在其中。供应商 HTTP 为模拟，TrialResult 的 reward 是测试输入，没有运行真实 Verifier。三项验收仍有证据支撑，保持 Done；真实 Trial 由 MH-007 承接。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
已核对缺失训练字段的消费者约束，并验证缺字段拒绝、显式空数组评测记录接受、训练模式拒绝。真实 Proxy finalize/read 与 HarborArtifactStore 提交在模拟供应商 HTTP、测试 TrialResult 下通过，未验证真实 Verifier。2026-11-17 当前 5342362 / Dressage 3820149 全套 109 项测试通过；真实 Harbor Trial 另由 MH-007 验收。
<!-- SECTION:FINAL_SUMMARY:END -->
