# 01 · Step 017 阅读范围

[本步入口](README.md) · [短期函数索引](02-short-term-memory/overview.md) · [前序模型](03-long-term-memory/overview.md) · [理解过程](04-flow.md)

> **此刻读哪里：Step 017 中的第三步——暂停接纳、更新权重、按需恢复。**
>
> 执行顺序是 [train.py:88](/home/hongshi/projects/slime/train.py:88) 先暂停接纳，再在 89 行更新权重。[RayTrainGroup.update_weights 卡片](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md#training-finished-before-sync)已整理两侧状态：训练计算结束后同步新权重，rollout 暂停新接纳。下一观察点为 [92–93 行的恢复条件](02-short-term-memory/functions/train.py/train.md#resume-after-weight-sync)，评估继续只定位。


- 范围确认：用户已确认上一轮提出的 train.py::train、一轮数据交接与训练闭环范围，原话为“好的那么开启这一个step吧”。已先展开 51 → 67 行；用户给出总体理解反馈后，随后按职责带过完成通知，当前接续 88–93 行权重交接，评估仍只定位。

## 1. 阅读目标

从前一步的训练数据引用出发，看清“拿到引用 → 提交训练并等待 → 通知完成 → 更新生成侧权重”的一轮编排。train 父函数卡保存调用顺序与等待边界；async_train 卡记录提交与返回，training_completed 卡记录完成通知，当前 update_weights 卡接续生成侧权重更新。评估只看它放在何处。

**第一步来路，按需回查：把 [train.py:51](/home/hongshi/projects/slime/train.py:51) 与 [67 行](/home/hongshi/projects/slime/train.py:67) 连起来读。** 先确认数据引用从哪里来、交给谁；需要看提交机制时，再进入 [RayTrainGroup.async_train:148](/home/hongshi/projects/slime/slime/ray/actor_group.py:148)，只看本例 external_data=None 的普通分支，随后返回 67 行理解等待。

对应本次 JD，重点是职责 2 中的任务执行封装，职责 4 与要求 1、5 的任务提交和完成边界，以及职责 5、要求 4 的训练闭环。详细依据见 [岗位对照](../../../../../../../slime_photo/code-reading/job-alignment.md#step017-jd-reading-focus)。本步不把阅读一个训练调用扩展成全部岗位能力已经覆盖。


停止位置：能够沿一个外层 rollout_id 说明这一轮交付什么、等待什么，以及下一轮生成怎样接上。此处的外层 rollout_id 表示循环轮次，与数据内部每份样本的 rollout 归属不能混用。

**本步的深度上限**：读清数据引用如何交给训练、如何等待完成、何时通知与更新生成侧权重，评估只定位。训练接口的分发与返回合同达到可说明程度后停止；loss、优化器、并行通信和 Ray 内部不列为本步必读。具体故障需要时再回查最小实现，完整边界见 [JD 对照](../../../../../../../slime_photo/code-reading/job-alignment.md#jd-required-depth-20261029)。

本步在 [综合审查](../../../../slime后续阅读顺序/2026-10-29-existing-foundation-and-remaining-scope.md)中对应剩余 A 单元：只读直接交接。training_completed 在默认路径中的短委派及不适用分支带过；update_weights 先读训练组接口，不进入权重传输实现。完成后转向已读 worker 的中断行为验证，不继续追加基础课程。

## 2. 找到指挥官函数

入口是 [train.py::train:13](/home/hongshi/projects/slime/train.py:13)，由 [main:110](/home/hongshi/projects/slime/train.py:110) 调用。它串起生成、训练和下一轮生成需要的控制；本步不用它的文件位置替代调用关系。

进入循环前，16 行通过 create_training_models 得到 actor_model 与可选 critic_model。当前 actor_model 是 [RayTrainGroup](/home/hongshi/projects/slime/slime/ray/actor_group.py:16)；rollout_manager 是传入的远程 RolloutManager 句柄。创建资源的内部细节先保留为前置。

## 3. 给出真正干活的核心骨架

### 3.1 整体位置

```text
main：取得本轮训练所需资源
└─ train                                      ← 本步指挥官
   ├─ 启动准备：建训练组、推送初始权重、通知 training_ready
   └─ 每个 rollout_id 的循环
      ├─ RolloutManager.generate
      │  └─ 已读生成 / 评分 / 收集 → convert → split_by_dp  [Step 016]
      │                                                  ↓ 数据引用列表
      ├─ actor_model.async_train                         [① 已初步理解]
      ├─ rollout_manager.training_completed                [② 职责层带过]
      ├─ 暂停生成接纳 → update_weights → 有下一轮时恢复接纳  [③ 当前]
      └─ 满足周期条件时 eval，再进入下一轮
```

<a id="core-skeleton"></a>

### 3.2 核心骨架与精读入口

**当前精读③ [RayTrainGroup.update_weights](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md)。** ①已有总体理解反馈，②按职责带过。实际执行先暂停接纳，再更新权重；暂停按接口理解，评估与启动准备暂不展开。

教学裁剪：选 use_critic=False、默认 object-store 传输的正常训练路径；保留启动权重交接及必要业务条件，参数通常省略，①保留当前交接需要的实参。配置检查、资源卸载、checkpoint 与外层清理折叠；源码仍完整保留这些行为。

```python
actor_model, critic_model = create_training_models(...)             # 16：训练组
actor_model.update_weights()                                       # 22：启动时推送权重
ray.get(rollout_manager.training_ready.remote())                    # 25：准备完成
for rollout_id in range(...):                                      # 47：逐轮组织
    rollout_data_ref = ray.get(rollout_manager.generate.remote(...)) # 51：接住数据引用
    ray.get(actor_model.async_train(rollout_id, rollout_data_ref))   # 67：① 已初步理解：提交训练并等待
    ray.get(rollout_manager.training_completed.remote(...))         # 71：② 完成通知
    was_paused = ray.get(rollout_manager.pause_rollout_admission.remote()) # 88：③a 暂停接纳
    actor_model.update_weights()                                   # 89：③b 当前精读：更新权重
    if rollout_id + 1 < args.num_rollout:                            # 92：还有下一轮
        ray.get(rollout_manager.resume_rollout_admission.remote(...))# 93：③c 按原状态恢复接纳
    if should_run_periodic_action(...):                            # 98：周期评估
        ray.get(rollout_manager.eval.remote(...))                    # 99：④ 周期评估
```

上述 67 行来自无 critic 分支；使用 critic 时会先取得 value_refs 并在需要时交给 actor 训练。eval-only 与训练前评估不在当前路径，先保留用途，不把裁剪看成源码不存在这些分支。

<a id="weight-handoff"></a>

**③ 的精读卡片：[RayTrainGroup.update_weights](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md)。** 88 行先暂停后台 rollout 的新任务接纳，89 行进入权重更新；was_paused 保存的是暂停前状态，供后面的恢复条件使用。暂停不等于终止全部在途请求。完整三行组合见 [train 父卡](02-short-term-memory/functions/train.py/train.md#weight-handoff)。

<a id="completion-notification"></a>

**② 的职责回顾卡片：[RolloutManager.training_completed](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md)。** 它的直接动作是把完成通知转交给 BatchBuilder：

```python
# slime/ray/rollout.py:430–431
self.batch_builder.training_completed(rollout_id)
```

当前 batch_id=None，BatchBuilder 直接结束；存在批次记录时才校验轮次并通知 controller。具体分支留在函数卡中，读完回到 train.py:71。这里把训练结束后的收尾与下一处权重更新分开。

finish_batch 已有队列侧实现，本轮只核对它兑现了完成登记的职责；“当前不调用”不等于“未实现”。用户现已明确不继续精读 lock、receipt、state，保留“收到完成通知后更新批次管理记录”的职责层模型。按当前简单心智模型的目标，不继续精读其辅助机制，见 [这一边界的说明](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md#implemented-but-not-triggered)。

<details>
<summary>① 已读的提交分支，按需回顾</summary>

**① 的精读卡片：[RayTrainGroup.async_train](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.async_train.md)。** 主线采用下面的普通分支，external_data=None；本轮提到的列表配对分支见同卡的 [for actor, ed 与返回列表](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.async_train.md#external-data-pairing)，不改变主线配置。

```python
# slime/ray/actor_group.py:163–166，async_train 的当前核心分支
return [
    actor.train.remote(rollout_id, rollout_data_ref, external_data=external_data)
    for actor in self._actor_handlers
]
```

读清“给谁提交任务、传入什么、返回什么”后，回到 [train 父卡的等待位置](02-short-term-memory/functions/train.py/train.md#async-train-submission)，再理解 67 行外层 ray.get。Megatron worker 的训练实现只定位，不作为此刻精读入口。


</details>

<a id="reading-order"></a>

### 3.3 阅读顺序与返回位置

| 阅读入口 | 本轮要弄清什么 | 回到哪里继续 |
| --- | --- | --- |
| **第一步：数据引用进入训练，51 → 67，已有总体理解反馈** | 先读 [RayTrainGroup.async_train 函数卡](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.async_train.md)，看清提交与返回；再回 [train 父卡](02-short-term-memory/functions/train.py/train.md#async-train-submission)理解外层 ray.get | 71 行完成通知 |
| **第二步：通知本轮完成，71** | 已按职责查看 [RolloutManager.training_completed 卡片](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md)：通知交给谁，默认分支是否产生额外动作；与训练等待、checkpoint 分开 | 88 行权重交接 |
| **第三步：更新权重并继续，88–93** | 先在 [train 父卡](02-short-term-memory/functions/train.py/train.md#weight-handoff)简读暂停，再进入 [update_weights 卡片](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md)；读完回看恢复条件 | 98 行评估或下一轮 |
| **第四步：评估放在哪里，98–99** | [eval 调用位置](/home/hongshi/projects/slime/train.py:98)：确认周期评估在这条循环中的位置；具体评估实现继续复用旧记录 | 下一次 rollout_id |

第一步需要提醒输入来路时，回看本步调取的 [split_by_dp 收尾](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-return-refs)。训练提交接口目前只核对 [RayTrainGroup.async_train:148](/home/hongshi/projects/slime/slime/ray/actor_group.py:148) 的返回合同；worker 如何取数与计算先留在边界外。

<details>
<summary>固定版本、前置和裁剪边界</summary>

- 本地版本 18868a79；官方 main 540ea919 与本地不同，本轮没有拉取或切换。固定行号与范围见 [源码证据](references/source-evidence.json)。
- 当前假定资源可用、训练模型已经创建；restore_plan 仍保留在 train 的真实签名中，本轮不展开恢复路径。
- 从 train 向下最多查看直接接口及必要的数据返回，不把 Ray API、训练 loss 或通信实现变成新的必读前置。
- ①至③已有对应卡片；当前③只查看更新组的非全量磁盘分支和直接委派，不进入权重通信；④只定位。②继续停在职责层，不进入 controller 辅助机制。

</details>
