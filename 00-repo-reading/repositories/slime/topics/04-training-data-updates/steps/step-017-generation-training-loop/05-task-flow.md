# 05 · 一轮生成、训练、权重同步与评估怎样衔接

> 接住上一阶段整理好的训练数据引用，交给训练组并等待完成，再登记数据已消费；随后暂停新增生成、同步新权重、按原状态恢复接纳，并在指定时点评估。正常返回主循环，继续下一轮或结束 train。

[本步 scope](01-scope.md) · [函数索引](02-short-term-memory/overview.md) · [形成过程](04-flow.md#normal-loop-reading-closure-20261031) · [唯一进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

## 1. 本步从哪里进入，到哪里结束

Step 016 已把 Sample 整理成训练字段，按 DP 分片，并通过 Box 中的 Ray 数据引用交付。Step 017 从 train.py:51 接收这些引用开始，首个精读入口是 RayTrainGroup.async_train。

本次沿 use_critic=False、已有可用生成引擎的正常路径阅读；权重更新以直接同步主例说明，磁盘分支保留为对照。启动初始化、checkpoint 和资源分支只定位用途；评估读到入口、结果去向和返回位置。

本页总结的是已确认范围内的正常闭环，不把它扩大为训练后端、所有恢复分支或真实集群运行均已完成。

## 2. 已读部分怎样交接

下面是调用归属图，省略参数和外围资源分支；缩进表示直接调用关系，方括号表示条件路径。后台循环与主循环独立运行，不画成 pause 调用 _loop。

```text
train
|-- create_training_models(...)
|-- actor_model.update_weights()
|-- ray.get(rollout_manager.training_ready.remote())
`-- for rollout_id in range(...)
    |-- ray.get(rollout_manager.generate.remote(...))
    |-- ray.get(actor_model.async_train(...))
    |   `-- actor.train.remote(...) for each training worker
    |-- ray.get(rollout_manager.training_completed.remote(...))
    |   `-- BatchBuilder.training_completed(...)
    |       `-- [batch_id is not None] ray.get(controller.finish_batch.remote(...))
    |-- ray.get(rollout_manager.pause_rollout_admission.remote())
    |   `-- registered rollout worker.pause(drain=False)
    |-- actor_model.update_weights()
    |   `-- training worker.update_weights.remote() -> weight_updater
    |-- [another rollout] ray.get(rollout_manager.resume_rollout_admission.remote(...))
    |   `-- [not was_paused] registered rollout worker.resume()
    `-- [periodic evaluation] ray.get(rollout_manager.eval.remote(...))
        |-- call_rollout_fn(..., evaluation=True)
        `-- record evaluation data and metrics
```

| 位置与卡片 | 进入时有什么，发生什么变化 | 之后交给谁 |
| --- | --- | --- |
| 51 → 67：[train](02-short-term-memory/functions/train.py/train.md#data-handoff)、[async_train](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.async_train.md#remote-return-versus-train-return) | 数据引用交给各训练 worker；async_train 返回结果引用列表，外层 ray.get 等调用完成 | 71 行完成通知 |
| 71：[training_completed](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md#mental-model) | 通知这批已训练完；有登记批次时更新消费进度、移除未完成登记，默认无批次时直接返回 | 回主循环后续编排 |
| 88：[pause_rollout_admission](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.pause_rollout_admission.md#mental-model) | 后台暂停接纳新任务，返回原暂停状态 was_paused；不要求全部在途任务结束 | 89 行权重同步 |
| 89：[update_weights](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md#mental-model) | 训练侧已有新参数，组织发布到生成侧；本方法内部等待更新调用 | 92–93 行恢复判断 |
| 92–93：[resume_rollout_admission](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.resume_rollout_admission.md#mental-model) | 还有下一轮且原先未暂停时，清除暂停标志，重新允许后台接纳新任务 | 95–99 行资源安排与评估条件 |
| 98–99：[eval](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.eval.md#mental-model) | 按周期运行评估，取得 data/metrics，按配置保存调试数据并记录结果 | 当前循环体结束，进入下一轮或离开 train |

启动时的 update_weights 用于推送已载入的参数；每轮训练后的同名调用用于推送新训练结果。两个调用目标都是生成侧，时机不同。

## 3. 本步留下了哪些结果

| 内容 | 含义与边界 |
| --- | --- |
| 训练数据引用 | 告诉训练侧从哪里取本轮数据；与训练任务的结果引用分开 |
| 训练调用的结果引用列表 | 让主循环等待各 worker 完成，正常 actor 路径实际返回值为 None；模型变化保存在 worker 内 |
| 消费登记 | 有对应批次时，确认数据已使用、更新进度和未完成登记；不等于立即删除全部文件或取消其他生成 |
| 生成侧新权重 | 在本次正常同步主例中，生成引擎接收训练后的参数；具体传输与在途请求处理不在本步展开 |
| was_paused | 保存暂停前状态，保证恢复不会擅自打开原本已暂停的后台 |
| 评估数据和指标 | 用于保存和日志记录；eval 正常返回 None，不返回新的训练批次 |

几个“完成”各有含义：训练调用完成、数据完成登记、权重发布完成、评估处理完成，分别由相应调用及等待确定。它们不能互相代替，也不自动证明完整模型与数据 checkpoint 已持久提交。

## 4. 本步收束与后续边界

用户已对训练提交、数据消费登记、暂停确认、向生成侧同步权重、恢复接纳以及评估职责给出相应的概括性表述。本轮按 Step 017 原定深度收束正常主线，保留各函数卡中的精确未知，不要求为结束本步而继续通读后端。

尚未展开的内部机制包括训练计算、权重传输与安装、完整存储回收、并行方案、恢复协议和详细评分实现。它们按实际改动或故障需要回查。

本次最初收束时保留了 A/B/C；用户随后要求再次对照岗位原文。按[最新复核建议](../../../../slime后续阅读顺序/2026-10-29-existing-foundation-and-remaining-scope.md#jd-recheck-20261031)，后续调整为：

1. **A：当前正常训练闭环阅读**，本次完成限定深度的收束。
2. **优先小接入验证**，复用 Step 015 的生成或评分接口，或已有同等项目实例，检查正常与错误情况并保留可复跑步骤。
3. **中断实现按需回查**，将异常/中断作为上述实例的一种行为验证，不再预先安排独立的逐函数阅读章节。

后续实践尚未在本次展开；不能把本页总结当作它们已经执行。部署排障是岗位的独立实践要求；Trace 保持此前暂缓，不因本步收束自动恢复。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定源码证据：18868a79；当前机器 checkout 540ea919 的相关方法已经逐项核对相同。各方法来源仍由函数卡和 [source-evidence.json](references/source-evidence.json)保存，不批量重写历史版本。
- 本页依据既有 Step 017 讨论、各次实际用户复述和本轮 eval 的表述整理；完整过程见 [04-flow](04-flow.md)。
- 历史验证含 Step 016 的局部转换/调度示例和 Step 017 的 async_train 记录替身实验。后者不是实际 Ray 训练，范围见 [局部输出](references/async-train-pairing-local-output.json)。
- 本次未运行真实模型、Ray、训练、权重同步、评估或插件契约测试；正常主线的阅读收束与系统运行证据分别记录。

</details>
