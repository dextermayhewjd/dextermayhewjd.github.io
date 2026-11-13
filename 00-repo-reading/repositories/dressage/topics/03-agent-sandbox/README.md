# Agent Sandbox：Kubernetes 环境分支与接入导航

[Dressage 项目入口](../../README.md) · [Harbor 接入主题](../02-harbor-integration/README.md) · [Agent Sandbox 正文与步骤](../../../agent-sandbox/topics/kubernetes-sandbox-control/README.md) · [K8s 唯一进度](../../../agent-sandbox/README.md#current-reading)

这里是整条 Dressage / Harbor / Agent Sandbox 路线的第三个可见入口，**只负责导航**。K8s scope、函数记忆和过程记录仍唯一保存在 Agent Sandbox 项目，不在这里复制，也不另建一套进度。

## 什么时候转到这里

不用等 Dressage Step 017 结束才读 Agent Sandbox。读到 [Step 013：Harbor Environment 接入](../02-harbor-integration/steps/step-013-harbor-kubernetes-environment/01-scope.md) 时，在明确上层需要哪些环境能力之后，转到本分支核对下层怎样兑现。

```python
# 阅读路线示意，不是运行时调用栈。
Dressage Step 007-009  # 收尾原生任务的轨迹、样本与清理。
Dressage Step 010-012 # 定位 Harbor 入口、Trial、Agent 与评测。
Dressage Step 013     # 写清 Environment 的接口和待补行为。
  -> Agent Sandbox 的 K8s 步骤  # 对照资源创建、Ready、领取、执行与回收。
  -> 返回 Dressage Step 013    # 完成接口映射，确定已有代码的复用与改动。
Dressage Step 014-016 # 接模型、结果、取消与重试。
Dressage Step 017     # 在现有项目中完成整合与验收。
```

## Agent Sandbox 的具体入口

以下编号属于 Agent Sandbox 的 Kubernetes 主题，不是 Dressage 的 Step 编号。已有记录按当前问题回顾，不从零重读；实际接续以 K8s 项目进度为准。

| K8s 步骤 | 要带回 Environment 接入的问题 | scope |
| --- | --- | --- |
| 000 · 协调入口 | 一份 Sandbox 需求怎样进入控制器？ | [原步骤](../../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-000-sandbox-reconcile/01-scope.md) |
| 001 · Pod 创建 | 对应 Pod 如何创建，谁拥有它？ | [原步骤](../../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-001-pod-creation/01-scope.md) |
| 002 · Ready | 哪些观察结果足以让上层使用环境？ | [原步骤](../../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-002-sandbox-readiness/01-scope.md) |
| 003 · 状态写回 | 状态怎样保存，版本冲突怎样处理？ | [原步骤](../../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-003-status-writeback/01-scope.md) |
| 004 · WarmPool | 备用数量怎样维持？创建与就绪怎样区分？ | [原步骤](../../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-004-warmpool-reconcile/01-scope.md) |
| 005 · Claim | 每个尝试怎样领取独立环境，未命中与删除怎样处理？ | [原步骤](../../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-005-claim-ownership/01-scope.md) |
| 006 · 执行与访问 | 上层如何执行命令、传输文件、识别权限或连接失败？ | [原步骤](../../../agent-sandbox/topics/kubernetes-sandbox-control/steps/step-006-access-and-isolation/01-scope.md) |

## 读完后具体做什么

1. 回到 Dressage Step 013，形成一张可实施的映射表：Harbor 的 start/stop/exec/upload/download，分别对应已有项目和 Agent Sandbox 的哪些能力，哪些仍需补齐。版本与缺失适配模块见[兼容性核对](../../references/agent-sandbox-harbor-compatibility.md)。
2. 在 slime_api_data_collecting 中选择最小改动范围，保留当前 Runner 为基线；先把一题冷创建、命令、文件、Verifier 与删除跑通。旧 K8s 能力优先复用，不重写控制器。
3. 按 Dressage Step 014–016 接好模型、结果和失败行为。WarmPool 的真实热领取在对应能力具备后加入，不将全部 K8s 内部源码当作首次冷创建的前置。
4. Step 017 是整合与验证范围，包含固定任务集、一次真实 Agent、换一种 Agent、少量并发、一次取消/失败和结果汇总。它不是读完后还要继续增加理论章节的入口。

上述实现与验证尚未在本次执行；这里仅补清三个主题的导航和实际交付去向。
