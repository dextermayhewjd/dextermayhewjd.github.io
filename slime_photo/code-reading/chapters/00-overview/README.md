# 第 0 章 全局职责与三种运行粒度

[阅读路线](../../repo-reading-route.md) · [总目录](../../README.md)

**目录 ID：** `00-overview`
**产物状态：** ready
**学习状态：** 统一见[阅读路线的当前接续](../../repo-reading-route.md#当前接续)。

**问题：** 一次任务、一次模型请求和一次训练迭代，分别由哪些模块组织？

**前置：** 无；从这里开始。

**连续正文：** [本地 00 全景 Walkthrough](http://localhost:1313/projects/slime/framework-walkthrough/) 直接渲染本目录的 [walkthrough.md](walkthrough.md)，不另存一份博客正文。从基本工作流建立整体模型，每步继承并展开一个关系；遇到已读任务时短回顾。认知步骤在[根目录的 Slime 记录](../../../../00-repo-reading/repositories/slime/README.md)。

**图文对照：** 1.1、4、7.1。

| 部件 | 源码入口 | 目标深度 | 接缝与边界 |
| --- | --- | --- | --- |
| 训练与生成总入口 | [train.py · main](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/train.py#L103) | locate | 只定位启动、资源准备和训练循环；训练算法留到 07。 |
| 任务数据合同 | [slime/utils/types.py · Sample](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/utils/types.py#L107) | locate | 先辨认 prompt、reward、token、mask、状态和身份字段；字段转换在 02、03、07 展开。 |
| 分布式生成与评测入口 | [slime/ray/rollout.py · RolloutManager](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/ray/rollout.py#L36) | locate | 类的角色与 generate/eval 入口；资源治理留到 06。 |
| 一个代码任务的组装 | [examples/coding_agent_rl/generate.py · generate](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/examples/coding_agent_rl/generate.py#L182) | locate | 只读调用骨架；执行和清理在 01 展开。 |

**章内顺序：**

1. 从本章 walkthrough 的基本工作流建立最小整体模型，先分清任务数据、生成评分、样本批次、训练和权重返回。
2. 以“谁启动并进入循环”为第一个展开问题，沿 train.main() 的真实交接定位服务准备与 train()；每步保留整体轮廓，第一遍不钻损失公式。
3. 到生成数据的交接再看 Sample 的主要字段；区分任务、请求和训练样本，具体字段按问题展开。
4. 主线进入具体 Agent 任务时，再定位 generate() 的 prepare → Harness → diff → evaluation → finish_session → finally；已读部分短提醒后返回调用方。

**验收问题：** 解释 agent/、rollout/、data/、ray/、backends/ 的职责，并指出工具循环、Kubernetes 和 tokenizer 实现的外部边界。

**证据状态：** 文件与符号已静态定位；建议的行为验证尚未执行，阅读反馈与运行证据统一见[当前接续](../../repo-reading-route.md#当前接续)。
