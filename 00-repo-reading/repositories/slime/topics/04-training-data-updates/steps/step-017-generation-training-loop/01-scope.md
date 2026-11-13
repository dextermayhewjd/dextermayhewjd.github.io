# 01 · Step 017 阅读范围

[本步入口](README.md) · [短期函数索引](02-short-term-memory/overview.md) · [前序模型](03-long-term-memory/overview.md) · [理解过程](04-flow.md)

> **本步范围的整体交接见 [05-task-flow](05-task-flow.md)。** 周期评估已接到主循环末尾；实际理解、运行状态与下一候选仍由唯一路线维护。
>
> 本步止于正常训练闭环的职责和交接。下面的 backend 小窗口保留为按需源码证据，具体训练与传输实现不因主线收束而成为已掌握。

2026-10-30 用户此前对对象身份、磁盘 release/reload 的问题继续保存在[函数卡](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md#training-worker-versus-rollout-engine)和 flow 中。此前曾将 backend 小窗口列为下一入口；用户再次质疑岗位必要性后，已将它降为按需证据。当前回到主循环的运行边界，不能因已准备材料就扩大必读范围。


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
      ├─ actor_model.async_train                         [① 训练并等待]
      ├─ rollout_manager.training_completed                [② 完成登记]
      ├─ 暂停生成接纳 → update_weights → 有下一轮时恢复接纳  [③ 权重交接]
      └─ 满足周期条件时 eval，再进入下一轮
```

<a id="core-skeleton"></a>

### 3.2 核心骨架与精读入口

**下面保留一轮连续的编排，按执行顺序回顾。** [2026-11-01 的整体复述与校准](02-short-term-memory/functions/train.py/train.md#whole-loop-restatement-20261101)已保存；本节不再用“当前精读”标记代替唯一路线中的进度。周期评估仍只看触发、交接和返回，具体评分实现不展开。

教学裁剪：选 use_critic=False、默认 object-store 传输的正常训练路径；保留启动权重交接及必要业务条件，参数通常省略，①保留当前交接需要的实参。配置检查、资源卸载、checkpoint 与外层清理折叠；源码仍完整保留这些行为。

```python
actor_model, critic_model = create_training_models(...)             # 16：训练组
actor_model.update_weights()                                       # 22：启动时推送权重
ray.get(rollout_manager.training_ready.remote())                    # 25：准备完成
for rollout_id in range(...):                                      # 47：逐轮组织
    rollout_data_ref = ray.get(rollout_manager.generate.remote(...)) # 51：接住数据引用
    ray.get(actor_model.async_train(rollout_id, rollout_data_ref))   # 67：① 提交训练并等待
    ray.get(rollout_manager.training_completed.remote(...))         # 71：② 完成通知
    was_paused = ray.get(rollout_manager.pause_rollout_admission.remote()) # 88：③a 暂停接纳
    actor_model.update_weights()                                   # 89：③b 发布权重给生成侧
    if rollout_id + 1 < args.num_rollout:                            # 92：还有下一轮
        ray.get(rollout_manager.resume_rollout_admission.remote(...))# 93：③c 按原状态恢复接纳
    if should_run_periodic_action(...):                            # 98：周期评估
        ray.get(rollout_manager.eval.remote(...))                    # 99：④ 周期评估
```

上述 67 行来自无 critic 分支；使用 critic 时会先取得 value_refs 并在需要时交给 actor 训练。eval-only 与训练前评估不在当前路径，先保留用途，不把裁剪看成源码不存在这些分支。

<a id="whole-train-card-learning-targets"></a>

#### 3.2.1 这张总体卡需要看懂哪些内容

**整张卡的目标**：沿一轮外层 rollout_id，说清数据从哪里来、交给谁训练、在哪里等待，以及训练结果怎样让后续生成用上。它是主流程卡，不要求把每个被调用函数内部全部展开。

| 骨架位置 | 本步要能说明的关系 | 阅读深度 |
| --- | --- | --- |
| 16–25：启动准备 | create_training_models 得到训练组；22 行把载入的模型权重先交给生成侧；training_ready 通知管理器训练侧已准备好，有恢复暂停记录时按原状态恢复后台 | 先知道对象、作用和顺序；不展开资源分配与恢复实现 |
| 47：外层循环 | rollout_id 标识这一轮生成/训练迭代；不把它等同于一个样本编号或一次内部优化器 step | 知道这一轮包住哪些动作 |
| 51：接住生成数据 | 上游生成、评分、整理和分片后，交回训练数据引用；rollout_data_ref 是后续训练的输入 | 接回 Step 016 的已有数据模型 |
| 67：提交训练并等待 | async_train 通过 worker 句柄提交 train.remote，返回结果引用列表；外层 ray.get 等这些调用正常完成后再继续 | 本步核心交接；区分数据引用、任务结果引用与实际返回值 |
| 71：完成登记 | 本批训练已结束，通知数据侧登记已消费；有对应批次时更新消费进度、移除未完成登记，不是停止所有生成任务 | 本步核心交接；知道通知链及状态变化即可 |
| 88–93：同步并继续生成 | 暂停新任务接纳 → 将训练后的权重同步给生成侧 → 若还有下一轮，按暂停前状态决定是否恢复 | 本步核心交接；区分暂停、同步与恢复，不展开全部传输器 |
| 98–99：周期评估 | 按配置周期执行评估；在所示正常路径中，它位于本轮权重同步之后 | 先知道何时调用、使用什么阶段的模型；不重读评测内部 |

**两次同名 update_weights 的区别是调用时机**：22 行位于循环前，发布启动时已载入的权重；89 行位于本轮训练之后，发布训练得到的新权重。两处的接收目标都是生成侧，不能把函数名理解为再次执行训练。

**本步停止标准**：能把“生成数据 → 提交训练 → 等待训练完成 → 登记消费完成 → 暂停新接纳 → 同步权重 → 按条件继续生成”连起来，并区分训练完成、数据登记完成、生成侧权重同步完成。具体理解状态继续以[唯一路线](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)为准；这张表不另维护学习进度。

<a id="weight-handoff"></a>

**③ 先进入 [pause_rollout_admission 卡片](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.pause_rollout_admission.md#mental-model)，再回 [update_weights 卡片](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md)。** 88 行先暂停后台 rollout 的新任务接纳，89 行进入权重更新；was_paused 保存的是暂停前状态，供后面的恢复条件使用。暂停不等于终止全部在途请求。完整三行组合见 [train 父卡](02-short-term-memory/functions/train.py/train.md#weight-handoff)。

随后使用 [resume_rollout_admission 卡片](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.resume_rollout_admission.md#mental-model)，只接清外层还有下一轮、方法内原先未暂停以及后台恢复接纳权限三项关系。恢复不等于已经生成完下一批。

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
| **第三步：更新权重并继续，88–93** | 先读 [pause_rollout_admission 卡片](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.pause_rollout_admission.md#mental-model)，回 [train 父卡](02-short-term-memory/functions/train.py/train.md#weight-handoff)接 89 行，再进入 [update_weights 卡片](02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md)；最后回看恢复条件 | 98 行评估或下一轮 |
| **第四步：评估放在哪里，98–99** | [train 父卡中的周期条件](02-short-term-memory/functions/train.py/train.md#periodic-evaluation) → [RolloutManager.eval 卡片](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.eval.md#mental-model)：评估调用、结果记录与返回；具体评分实现不展开 | 下一次 rollout_id 或离开 train |

第一步需要提醒输入来路时，回看本步调取的 [split_by_dp 收尾](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-return-refs)。训练提交接口目前只核对 [RayTrainGroup.async_train:148](/home/hongshi/projects/slime/slime/ray/actor_group.py:148) 的返回合同；worker 如何取数与计算先留在边界外。

<a id="worker-weight-sync-window"></a>

### 3.4 按需回查：worker 的权重交接（非必读）

2026-10-30 用户再次质疑岗位必要性后，撤回将此片段设为下一项必读的建议。这几行能支撑同步方向的解释，但岗位目标要求接清训练与生成的交接，不要求专门掌握取得句柄的实现。当前先回主循环；只有仍缺源码依据或实际改动需要时，才使用本节。

**整体位置**：train.py:89 → RayTrainGroup.update_weights:181 → MegatronTrainRayActor.update_weights:629。前一层已经把调用交给训练 worker；这一层只需确认它如何找到生成引擎，以及谁实际承接同步工作。

**当前职责问题**：训练后的参数怎样交到生成侧？输入是 worker 已有的模型、rollout_manager 和 weight_updater；结果是完成本次同步委派。本函数正常返回 None，调用方的 ray.get 等待它完成。

下面从固定版本方法中作教学裁剪，继续沿直接同步路径（例如 full + nccl）说明，不套用全量磁盘先写文件、后由训练组 reload 的路径。假定已有可用生成引擎，offload_train=False，无需故障恢复；因此 reconnect_rollout_engines 为 False，从条件中折叠。保留真实返回项与函数名，connect 的参数按导航约定省略；暂时折叠日志、统计、健康恢复、跨 rank 屏障和显存管理。它是阅读骨架，不是独立可运行实现。

```python
(
    rollout_engines,
    rollout_engine_lock,
    num_new_engines,
    engine_gpu_counts,
    engine_gpu_offsets,
    engine_parallel_configs,
) = ray.get(self.rollout_manager.get_updatable_engines_and_lock.remote())

if num_new_engines > 0:  # 当前配置不需重连；原条件还有 or reconnect_rollout_engines
    self.weight_updater.connect_rollout_engines(...)

self.weight_updater.update_weights()
```

| 观察处 | 只需要弄清什么 | 到哪里就停 |
| --- | --- | --- |
| [actor.py:640–647](/home/fredkeira/projects/slime/slime/backends/megatron_utils/actor.py:640) | 向管理器取得生成引擎、锁和配置；rollout_engines 是接收权重的一侧 | 不继续展开管理器内部和 GPU 布局算法 |
| [actor.py:661–674](/home/fredkeira/projects/slime/slime/backends/megatron_utils/actor.py:661) | 有新引擎或需要重连时，让 updater 连接到这些对象；原条件不是每轮无条件建连接 | 知道 updater 接到哪些对象，连接、屏障内部留白 |
| [actor.py:676–678](/home/fredkeira/projects/slime/slime/backends/megatron_utils/actor.py:676) | worker 委派 updater 完成本轮权重更新 | 不进入 tensor、distributed、disk 等具体 updater |

**本函数停止点**：能够沿“训练 worker → 取得生成引擎 → 按需连接 → 委派同步”定位实际代码，就返回 RayTrainGroup 的等待处，再回 train.py:92–93。读到这里的目的不是重写 updater，也不将每个辅助方法都设为必须理解。

**Step 017 的停止点**：把数据引用、训练提交与等待、完成通知、权重同步、按条件恢复生成、周期评估的位置接成一轮。复习现有配置与输入输出即可，不把本步延长为完整 Megatron 学习。

岗位依据与整轮 Slime 的收尾条件见[本次范围复核](../../../../slime后续阅读顺序/2026-10-29-existing-foundation-and-remaining-scope.md#backend-depth-review-20261030)。当前只落实阅读材料和边界，不表示用户已经读懂、运行或通过本步。

<details>
<summary>固定版本、前置和裁剪边界</summary>

- 本步固定证据使用 18868a79。2026-10-30 当前环境的 checkout 位于 /home/fredkeira/projects/slime，HEAD 为 540ea919；当前相关方法与固定版本一致，版本迁移与比较范围见 [本轮记录](04-flow.md#training-review-and-resume-20261030)。未切换源码，也未把历史官方 main 查询当作当天状态；原始行号与范围见 [源码证据](references/source-evidence.json)。
- 当前假定资源可用、训练模型已经创建；restore_plan 仍保留在 train 的真实签名中，本轮不展开恢复路径。
- 从 train 向下最多查看直接接口及必要的数据返回，不把 Ray API、训练 loss 或通信实现变成新的必读前置。
- ①至③已有对应卡片；③沿更新组的非全量磁盘主例，加上本节 worker 的直接交接，不进入权重通信。此前用户提问触发的磁盘分支对照保留为参考，不增加必读；④只定位。②继续停在职责层，不进入 controller 辅助机制。

</details>
