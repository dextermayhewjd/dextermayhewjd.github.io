# 第 0 章 全局职责与三种运行粒度

[阅读路线](../../repo-reading-route.md) · [总目录](../../README.md)

**目录 ID：** `00-overview`
**产物状态：** ready
**学习状态：** 未开始

**问题：** 一次任务、一次模型请求和一次训练迭代，分别由哪些模块组织？

**前置：** 无；从这里开始。

**图文对照：** 1.1、4、7.1。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 训练与生成总入口 | [train.py · main](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L103) | locate | 只定位启动、资源准备和训练循环；训练算法留到 07。 |
| 任务数据合同 | [slime/utils/types.py · Sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/types.py#L107) | locate | 先辨认 prompt、reward、token、mask、状态和身份字段；字段转换在 02、03、07 展开。 |
| 分布式生成与评测入口 | [slime/ray/rollout.py · RolloutManager](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L36) | locate | 类的角色与 generate/eval 入口；资源治理留到 06。 |
| 一个代码任务的组装 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | locate | 只读调用骨架；执行和清理在 01 展开。 |

**章内顺序：**

1. 先读本章 walkthrough 的职责表，按“任务服务、模型服务、执行环境、训练”定位模块。
2. 扫 Sample 的主要字段；一份输入样本可以经 Agent 任务分成多个训练片段，任务数、请求数与训练样本数不能混用。
3. 看 generate() 的 prepare → Harness → diff → evaluation → finish_session → finally 骨架。
4. 扫 train.main() 与 train()，认出生成、训练、checkpoint 和权重更新；第一遍不钻损失公式。

**验收问题：** 解释 agent/、rollout/、data/、ray/、backends/ 的职责，并指出工具循环、Kubernetes 和 tokenizer 实现的外部边界。

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，学习状态尚未由用户复述确认。
