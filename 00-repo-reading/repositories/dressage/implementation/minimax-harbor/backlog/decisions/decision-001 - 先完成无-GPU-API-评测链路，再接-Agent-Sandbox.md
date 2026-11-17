---
id: decision-001
title: 先完成无 GPU API 评测链路，再接 Agent Sandbox
date: '2026-11-17 06:51'
status: accepted
---
## Context

用户希望以腾讯混元 Agent 强化学习框架岗位为目标，将已读的 Slime、Dressage、Harbor 串成实际可运行的评测链路；本地没有 GPU，使用 MiniMax API。为避免继续无边界扩大学习范围，需要明确交付和停止位置。

2026-11-17 用户确认：“好的 那么就以这个为目标吧 否则我觉得日后会不清楚这里到底在做什么”。

## Decision

1. 从 Slime 发起，沿固定版本 Dressage fork 的 Harbor 路线调用 MiniMax，先在可用环境完成执行、评分、结果保存和清理。
2. 再将环境换成 kubernetes-sigs/agent-sandbox，验证代表性任务、少量并发、预热命中/耗尽、故障定位和资源回收。
3. 学习与任务记录保存在当前学习仓库，实际代码与测试在 Dressage 等对应源码仓库；保留已有函数卡。
4. 小幅改动是目标，不承诺只改一个函数或完全无需 Slime 启动适配。
5. 不要求自研调度器、镜像存储、任意状态快照、千级并发或全部 benchmark；SDK 最后评估，不是本轮完成条件。

**明确采用 Agent Sandbox 作为目标沙箱后端**

**本项目希望实际用上 [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)，并通过它承接 Harbor 的任务执行环境，而不只停留在阅读或接口设计。**

- **接入位置：**沿 Dressage → Harbor 路线，在 Harbor 的 Environment 后端适配环境创建/领取、命令执行、文件上传下载和停止清理。沿用原有 Agent、Verifier 与结果收集链路，具体适配以选定版本的接口为准。
- **学习目的：**通过真实任务理解 Kubernetes 中环境的部署、资源生命周期与排障，并练习将可复用沙箱能力接入 Agent 评测框架。
- **验证范围：**先跑通冷创建，再验证 SandboxWarmPool 的预热领取、池耗尽行为及少量并发；选择最小任务、具有环境依赖的代码任务与失败/超时用例，检查评分、日志、产物和资源释放。
- **实施顺序：**先完成 MiniMax API 与原有可用后端的基线，再替换为 Agent Sandbox；它是已确认的第二阶段目标，不是可忽略的附带选项。
- **边界：**使用并适配现有项目，不自研完整沙箱平台；不默认兼容 Harbor 全部任务，也不预先承诺吞吐或启动延迟。具体镜像、运行时、版本及部署方式在实施时核实。

2026-11-17 补充依据：用户明确要求将“希望用上 Agent Sandbox”写入 decision-001。本项记录目标选择，不表示接入或集群验证已经完成。

## Consequences

完成的是无 GPU 的 Agent 执行与评测验证，不能声称验证了策略训练或权重更新。需要固定版本、任务、模型及运行配置，保留真实证据；不伪造缺失的 token/logprob/权重版本。候选接口设计仍需按任务验证，不能以本决策代替技术结论。

## Alternatives

历史讨论中曾出现完整自建沙箱平台、先开发通用 SDK、迁移原生 PrewarmStore 等方向；它们不是本轮必需前置。这里记录的是已确认边界，不声称所有候选都做过实验比较。
