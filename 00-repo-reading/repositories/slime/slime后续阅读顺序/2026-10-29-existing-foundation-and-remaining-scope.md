# 2026-10-29 · 结合已有基础，确定剩余 Slime 阅读范围

[岗位与要求](../../../../slime_photo/code-reading/job-alignment.md#jd-required-depth-20261029) · [阅读计划](current-goal-slime-reading-order.md) · [唯一进度](../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

用户要求综合 Learn Claude Code、Python 异步与并发、Slime 阅读痕迹和已有强化学习理解，判断还缺什么，并确定剩余 Slime 范围。本次审查使用本地正文、明确学习反馈和已有验证记录；文章存在、本人已表达理解、实际系统运行分别判断。 Slime 源码核对固定在 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，其他专题保留各自版本；本轮未执行新测试、模型或训练。

## 1. 总判断

**不再增加一套 Agent、Asyncio 或强化学习基础课。Slime 剩余重点收为两段代码阅读，加一项已有接口的集成验证。** 当前主要补充“这些部件如何协同运行及如何证明行为正确”，而不是继续扩大算法或底层系统的清单。

这并不把现有全部章节标为已掌握。某个具体 API 或公式再次卡住当前任务时，回到既有教材局部复习；独立异步课程的既定范围不因本次审查被删改，也不作为继续 Slime 之前必须全部完成的前置。

## 2. 已有基础怎样计入

| 方向 | 本地证据与已覆盖的内容 | 对剩余范围的影响 |
| --- | --- | --- |
| Agent 框架理解 | [Learn Claude Code](../../../../content/projects/learn-claude-code/_index.md) 的 S01–S17 覆盖主循环、工具、权限/Hook、上下文、Memory、任务、后台任务、团队、MCP、Workflow 与 Goal；[S15 综合 Harness](../../../../content/projects/learn-claude-code/s15/_index.md#harness-understanding) 已明确模型、工具及结果回流的组合关系 | 不在 Slime 重讲整套 Agent Loop；只追框架接入合同和当前业务差异 |
| Python 异步与并发 | [异步课学习路线与记录](../../../../content/projects/python-async-concurrency/learning-route/index.md#reading-status) 与 98 项 API 的独立课程已有 Task、等待、取消、时间预算、队列、同步、ContextVar、线程/进程及回调材料；Slime 笔记也已有 semaphore、pacer、worker loop 和 callback | 不另开 Ray / Asyncio 底层课程；只在中断、回队、背压等业务行为上核对用法 |
| 强化学习原理 | [CS285 课程入口](../../../../content/courses/cs285/_index.md) 已有 BC/DAgger、策略梯度、Actor-Critic/GAE、PPO、TRPO 和奖励学习；[Lecture 14](../../../../content/courses/cs285/lecture-14/index.md#lecture-thread) 已接到 LLM 序列、组内优势、参考 KL 和策略更新 | 当前 JD 的一类训练基础已有内容支撑；不追加完整预训练/SFT 或再学一遍 PPO 数学，重点完成数据到训练的交接 |
| Slime 的真实组件 | 主题 01 的 Coding Agent 调用与评测、Step 010–013 的生成/评分/worker/收集，以及 [Step 015](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/README.md)、[Step 016](../topics/02-rollout-reward/steps/step-016-sample-to-train-data/README.md) 已建立场景记录 | 复用已有卡片，剩下按正常闭环和中断分支补缺，不重开整条调用链 |
| 部署基础 | [2026-10-25 的用户条件](../../../../slime_photo/code-reading/job-alignment.md#next-month-job-plan-20261025) 明确记录用户用过 kubectl、部署过简单服务 | 不按零基础部署安排；继续核实能否拿出完整的资源、网络或重启排查案例 |

**已有材料中的边界仍要保留。** [S15 综合 Harness](../../../../content/projects/learn-claude-code/s15/_index.md#harness-understanding) 明确 MCP 为 mock、部分 Skills / 隔离为教学实现；[S16 Workflow Runtime](../../../../content/projects/learn-claude-code/s16/_index.md#workflow-try) 的 demo 使用 MockAgentRunner。[Skills Lab 的验证边界](../../../../examples/s07-skills-lab/README.md) 的确定性脚本检查不等于真实模型的触发与行为评估。异步课明确记录 36.2 曾暂缓、ContextVar 与 RLock 没有全部标记掌握。这些信息用于避免夸大，不意味着要从头补读全部章节。

## 3. 当前最值得补的缺口

1. **生成与训练闭环**：目前 Step 017 刚建立，还要连上训练提交、等待、完成通知和生成侧权重更新。缺的是接口和运行顺序，不是新增训练理论。
2. **失败时业务语义是否正确**：已有取消、异常和队列知识；还要观察一次 Slime 中断后，哪些结果保留、哪些重新排队，完成结果是否错误地流进训练。
3. **真实接入与复跑的证据**：[Step 015](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/README.md) 明确记录尚未运行插件契约测试。已有讲解和模拟应复用，但仍要用一个小改动验证接口、评分/结果和失败行为，并保存可重复运行的输入、配置、版本与结果。
4. **部署排障案例待核实**：已有简单部署经验；未在本轮目录中找到完整故障诊断过程。如已有现成案例，整理它即可，无须重新学习基础或重复做项目。
5. **Trace 是应用验证缺口**：[Trace 主题](../topics/03-trace-diagnostics/README.md) 有工具用法、示例与部分真实函数运行输出。后续若恢复，目标是用现有 Trace 定位一次具体问题；仍遵守当前暂缓要求，不重新钻 trace_utils 全部内部。

阅读记录能够证明接触过什么、表达过什么理解；它不能单独证明线上经验或全部独立实施能力。上述缺口中，集成与排障项是目前未见足够证据，不断言用户在目录以外没有做过。

<a id="remaining-slime-scope"></a>

## 4. 剩余 Slime 范围就保留以下三项

| 单元 | 必须看的代码或已有记录 | 读到哪里就停 |
| --- | --- | --- |
| **A · 完成当前 Step 017：正常训练闭环** | [train.py:51–99](/home/hongshi/projects/slime/train.py:51)；[RayTrainGroup.async_train](/home/hongshi/projects/slime/slime/ray/actor_group.py:148) 与 [update_weights](/home/hongshi/projects/slime/slime/ray/actor_group.py:178) 的直接接口；[RolloutManager.training_completed](/home/hongshi/projects/slime/slime/ray/rollout.py:430) 及必要的一层委派 | 说清数据引用交给谁、何时等到训练完成、何时通知、权重怎样交回生成侧。默认 object-store 下只带过不适用的 batch 完成分支；不进入权重传输、模型 loss 或优化器实现 |
| **B · 复用已读 worker：中断结果与背压** | [AsyncRolloutWorker._make_done_cb](/home/hongshi/projects/slime/slime/rollout/fully_async_rollout.py:246) → [prepare_retry_group](/home/hongshi/projects/slime/slime/rollout/base_types.py:107)；回查 [_loop](/home/hongshi/projects/slime/slime/rollout/fully_async_rollout.py:178) 的接纳/报错条件及 [close](/home/hongshi/projects/slime/slime/rollout/fully_async_rollout.py:140) 的直接收尾 | 能对照完成组与 PENDING/ABORTED 组的去向；解释 flat partial 保留、分段失败回到原输入与已完成同伴保留；用一个中断用例验证，接清错误如何向外报告、停止时如何等待在途任务。背压只看已读条件，不再讲完整事件循环 |
| **C · 复用 Step 015 与评测链：做一个小接入验证** | 已读 generate_and_rm / 自定义 generate 或评分接口、[Step 015](../topics/02-rollout-reward/steps/step-015-custom-generate-contract/README.md) 和 [插件契约测试入口](/home/hongshi/projects/slime/tests/plugin_contracts/test_plugin_generate_contracts.py:148)；已有 run_evaluation / filter 按改动回查 | 完成一个策略或评分规则的小改动，对固定样本跑正常与错误/中断情形，核对 Sample 状态、奖励和输出，保存复跑方法。CPU 替身、真实模型调用、GPU 训练分别标记；不新增整份测试框架课程 |

A、B 是剩余新增阅读的两个核心单元；C 主要补执行与验证，不是再读一遍所有已读函数。先完成 A，再进入 B；C 可利用已有接口准备，实际展开时仍确认具体改动与运行条件，不自动新建一串后续 Step。

B 的首选证据是 [test_unfinished_flat_group_is_requeued_without_discarding_partial_response](/home/hongshi/projects/slime/tests/test_fully_async_rollout.py:307)；需要比较分段任务时再用 [test_interrupted_segmented_group_retains_successful_siblings](/home/hongshi/projects/slime/tests/test_fully_async_rollout.py:264)。背压已有对应 [测试](/home/hongshi/projects/slime/tests/test_fully_async_rollout.py:317)，只在这一具体行为需要验证时使用。本次仅核对源码位置，没有运行这些测试。

## 5. 不再扩成必读的内容

完整 Megatron、更多训练算法推导、CUDA/NCCL、全部 DP/PP/CP/VPP 实现、Ray 调度器内部、straw/WAL/pack/GC 与完整容灾恢复不在当前必读范围。Dressage 等额外框架、所有 grader、所有高级 Agent 机制和三门跨语言课程也不追加。

Kubernetes 是 JD 的独立实践要求，不能用读 Slime 代替；这里利用已有部署基础补排障证据。Trace 恢复时使用已有工具与记录做诊断，不再默认建立内部实现专题。

当前继续 [Step 017 scope](../topics/04-training-data-updates/steps/step-017-generation-training-loop/01-scope.md#reading-order) 的第一处交接。A 完成后按 B 的小范围确认下一步；本次审查不改写当前各函数的掌握状态，也不立即开启 B、C 或部署任务。
