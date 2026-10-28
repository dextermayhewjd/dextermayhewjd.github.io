# Slime 后续阅读入口

现行安排统一见 **[2026-10-28 阅读计划与约定](current-goal-slime-reading-order.md#reading-agreement-20261028)**。按生成接入验证、训练数据、训练闭环、关键失败处理的顺序推进；Trace 继续暂缓，Kubernetes 单列实践，队列与底层恢复按需选读。

本目录保存计划与选题依据；实际开始、暂缓和运行状态只维护在[唯一阅读路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。已读 Agent、generate_and_rm、worker loop 与结果交付记录继续复用，不重开整条主线。

- [岗位依据](../../../../slime_photo/code-reading/job-evidence/2026-10-28-user-provided-jd.md)与[能力对照](../../../../slime_photo/code-reading/job-alignment.md)。
- [队列案例的关联与阅读边界](straw-queue-jd-assessment-2026-10-28.md)：可选参考，其曾被排为下一步的建议已修正。
- [返回 Slime 项目入口](../README.md)。

<details>
<summary>此前索引与候选顺序（历史原文）</summary>

# Slime 后续阅读顺序

最新选题评估：[straw 队列调度与混元岗位的对应及第一轮边界](straw-queue-jd-assessment-2026-10-28.md)。先评估跨 worker 的任务领取、归还与续跑，不将存储引擎与完整恢复机制整体列为必读；实际状态见唯一路线。

记录日期：2026-10-22（2026-10-24 增补 Dressage 抽象与评测路线入口）。

目标：对齐腾讯混元 Agent 强化学习框架工程师岗位，按岗位工作需要选读源码。以下安排以当前 Coding Agent RL 主线读完为前提，保存具体阅读文件、先后顺序、必须弄清的问题和停止位置。

本文件记录后续选读计划；实际阅读进度继续以[唯一阅读路线](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准。保存计划不表示已经开始或完成这些阅读。

2026-10-25 用户补充计划一个月内投递或面试，已有 kubectl 和简单服务部署经验；针对这一时限的[岗位逐项复核与四周建议](../../../../slime_photo/code-reading/job-alignment.md#next-month-job-plan-20261025)已另行补充。下表继续作为模块入口导航，具体下一步尚待确认。

新增记录：[Slime 后续阅读顺序与腾讯混元岗位：逐项评估](hunyuan-jd-reading-order-assessment-2026-10-25.md)。保存四项主题的岗位对应、三处调整建议与下一入口；原阅读顺序保留。

简明方案：[按完整 JD 复核的阅读范围](current-goal-slime-reading-order.md#full-jd-review-20261028)。复用已读 Agent 主线，明确组件替换、策略/评估接入与复跑、并发治理和训练数据交接的检验目标；Trace 保持暂缓，Kubernetes 单列实践。此前“两块重点与一块概览”及六模块路线保留为历史快照。

[返回 Slime 阅读入口](../README.md) · [岗位对照](../../../../slime_photo/code-reading/job-alignment.md) · [generate() 生命周期阅读结论](generate-lifecycle-reading-conclusion.md) · [Slime 到 Dressage 阅读顺序](slime-to-dressage-reading-order.md) · [切入 Dressage：提炼抽象层级与评测方式](dressage-abstraction-and-evaluation-route.md) · [混元岗位对齐与评测抽象分析](hunyuan-jd-and-eval-abstraction-analysis.md)

## 阅读顺序

| 阅读顺序 | 文件与函数 | 本轮必须弄清的问题 | 停止位置 |
|---|---|---|---|
| 1．策略与评测接入 | `slime/rollout/sglang_rollout.py`：`generate_and_rm`；随后看 `slime/rollout/rm_hub/__init__.py`：`async_rm`、`batched_async_rm` | 算法同事给出一种新的 Agent 策略或评分方法，应该接在哪里？返回什么？ | 能说明接口、结果形状、评分责任和扩展方式。具体评分器只选一个，不逐个通读 |
| 2．批量任务与并发控制 | 回到 `sglang_rollout.py`：`generate_and_rm_group` → `generate_rollout_async`；按需回查 `GenerateState`、`abort` | 怎样同时运行很多 Agent 任务？如何限制并发、接收结果、处理剩余任务？ | 走通正常路径，再解释一种慢任务或取消情形 |
| 3．Trace 与故障定位 | `slime/observability/trace_utils.py`：先看前两步用到的 `trace_span`、`trace_function` | 一批任务变慢或出错，怎样知道发生在哪个任务、哪个阶段？ | 能根据记录区分生成、评分、等待和异常；先不通读整个观测模块 |
| 4．训练数据交接 | `slime/data/batch_builder.py`：`BatchBuilder.convert`；接着短读 `slime/ray/rollout.py` 的转换交接，以及 `train.py::train` 的主循环 | Agent 返回的 token、reward、logprob、mask 怎样被训练使用？生成、训练和权重更新如何连接？ | 先把数据含义和调用边界讲清楚，具体 loss、并行和通信实现由实际问题再引出 |

## 配套测试

测试应从第一轮就配套阅读。先看：

- `tests/plugin_contracts/test_plugin_generate_contracts.py`
- `tests/plugin_contracts/test_plugin_path_loading_contracts.py`

它们帮助你判断“接口怎样才算接对”，官方也提供了 CPU 环境下的接口验证方式，适合目前的条件。[官方接口测试说明](https://thudm.github.io/slime/get_started/customization.html#testing-custom-function-paths)

## 这样安排的理由

1. **先学会接入。** 这是岗位中承接算法需求最直接的工作，也能复用你已经读过的 Coding Agent。
2. **再学会批量运行。** 单个任务成立以后，才有明确对象去理解并发、取消和资源占用。
3. **紧接着学会定位问题。** 能运行还需要能解释失败、验证修改。
4. **最后补齐训练接口。** 保证知道 Agent 数据为何必须保存这些字段，并理解它们的下游用途。

## Kubernetes 实践

Kubernetes 要单独安排实践，从第二轮附近就可以开始，不必等上述源码全部读完。它需要部署、资源限制、网络、日志和故障排查的实际证据；继续深入 Slime 的 Ray 实现不能替代这部分。

## 暂时后置的源码

暂时后置的源码包括：完整的 `fully_async_rollout.py`、整个 `serving.py`、Megatron 内部并行和底层通信。分别遇到长尾任务、服务恢复或训练性能问题时，再选取相关部分。

## 第一处阅读入口

`slime/rollout/sglang_rollout.py::generate_and_rm`。

本轮问题限定为：

> Coding Agent 的实现如何通过统一接口接入框架；如果换一种策略或评分逻辑，哪些地方需要改，怎样验证？

</details>
