# Step 017 · 生成数据怎样进入训练并更新生成侧权重

完整回顾参考：[主骨架、局部交接与结果去向](references/task-flow-reference.md)。默认突出数据、训练与权重发布；配套动作以短代码和旁注说明交接，内部机制按需展开。[原任务总结](05-task-flow.md)保留供比较。

[主题入口](../../README.md) · [前一步 Step 016](../../../02-rollout-reward/steps/step-016-sample-to-train-data/README.md) · [唯一进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

用户在上一轮看到具体范围后明确要求：“好的那么开启这一个step吧”。本步从 train.py::train 的一轮循环进入，承接 Step 016 返回的训练数据引用，跟踪训练调用、完成通知和生成侧权重更新；评估先只定位。

**前一步模型**：Sample 已整理为训练字段，按 DP 分成配套数据和微批安排，经 Ray 对象存储以引用交回。**本步问题**：主循环怎样把这些引用交给训练，以及训练完成后怎样准备下一轮生成？

本步投入按 [JD 的必需深度](../../../../../../../slime_photo/code-reading/job-alignment.md#jd-required-depth-20261029)控制：只接通一轮训练交接，不将其扩展为训练底层实现专题。框架接入验证、失败处理与容器实践继续按原计划保留。

结合现有 Agent、异步与强化学习基础后，本步只补剩余 A 单元的正常训练闭环；不用重学这些基础。后续 B/C 的范围见 [综合审查](../../../../slime后续阅读顺序/2026-10-29-existing-foundation-and-remaining-scope.md#remaining-slime-scope)。

<a id="original-start"></a>

## 本步最初从哪里开始

Step 017 一开始从 **train.py::train 的一轮主循环**进入，首个观察点是 51 → 67 行：前一步已经把 Sample 整理成训练字段，按 DP 分片后通过 Box 中的数据引用交付；本步接着问“这份数据怎样交给训练，训练完怎样开始下一轮生成”。

```python
rollout_data_ref = ray.get(rollout_manager.generate.remote(rollout_id))
ray.get(actor_model.async_train(rollout_id, rollout_data_ref))
```

这是真实语句节选，选 use_critic=False，省略两行间的资源管理分支。第一行接收训练数据引用，第二行提交本轮训练并等待完成。先读 [train 父卡的数据交接](02-short-term-memory/functions/train.py/train.md#data-handoff)，再进入第一个精读函数 [RayTrainGroup.async_train](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.async_train.md)。

本步随后依次读了完成通知、权重同步与暂停/恢复。update_weights 属于第三段，不是这一步最初的入口；回顾起点不清零之前的阅读事实。最初的范围确认与首个观察点见 [2026-10-29 记录](04-flow.md#first-reference-handoff)。

## 当前接续入口

完成通知的短期记忆已按用户确认采用[第二版正式函数卡](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md#mental-model)：分层伪代码、同行注释和段后整体逻辑。合并前的[定稿](references/training-completed-card-final-v2.md)、[第一版图示](references/training-completed-card-proposal.md#progressive-mental-model)与[旧卡快照](references/history/RolloutManager.training_completed-before-v2-2026-10-31.md)保留作历史回查。

**本步主线回顾：[05 · 一轮生成、训练、权重同步与评估怎样衔接](05-task-flow.md)。** 其中接回本步起点、各函数交接和剩余边界；具体学习状态与下一候选仍以唯一路线为准。末段职责见 [RolloutManager.eval](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.eval.md#mental-model)，内部评分和评估实现保留回查。

1. [01 · scope 3.2](01-scope.md#core-skeleton)：完整核心骨架；①已有总体理解反馈，②按职责带过，③标出当前精读函数与同名卡片。
2. [02 · 短期函数索引](02-short-term-memory/overview.md)：训练提交、数据完成登记、暂停、权重同步、恢复和评估的独立记录。
3. [03 · 前序累计记录](03-long-term-memory/overview.md)：完整合并 Step 016 的 03 + 02，共 83 份函数／类记录与 17 份配套文件，包含 2 份历史空白占位。
4. [04 · 理解形成过程](04-flow.md)：范围确认、源码证据和后续实际问答。
5. [05 · 任务链路总结](05-task-flow.md)：按本步范围收拢一轮正常交接，并列出后续边界。

本步的 02 已调取 [split_by_dp](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-return-refs)，用于回顾数据引用结构；调取保持原认识时间。train 父卡保存整体交接；此前按用户对精读入口的要求，将 async_train 从父卡拆成同名独立卡；随后新增完成通知卡，当前再建立权重更新卡。原话、未知及拆卡前完整版本均保留。

## 范围与证据

- 本步选取 use_critic=False、默认 object-store 传输的正常训练路径；资源创建先认用途，卸载、checkpoint、loss、优化器和通信内部按需回查。
- `train()` 在 driver 中同步编排，`actor_model.async_train()` 是训练组的提交接口。函数名含 async 不代表 asyncio 协程；当前只看提交与等待的交接。
- 本地 Slime 固定为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`。官方 main 核对为 `540ea919e45b8b929198abce008a103be9cfc779`，未切换版本。详见 [源码证据](references/source-evidence.json)。
- 前序初始化为静态源码核对和文档继承；此前为解释 zip 配对和返回列表，增加原 async_train 方法搭配 remote 记录替身的局部运行；本轮权重交接的接口仅作静态核对。没有启动真实 Ray、模型或训练；记录建立、局部运行与函数已掌握分别记录，见 [运行范围](references/async-train-pairing-local-output.json)。
