# train

- 源码定位：[train.py:13](/home/hongshi/projects/slime/train.py:13)，固定版本 `18868a79`；调用方为 [main:110](/home/hongshi/projects/slime/train.py:110)。
- 首次接触：Step 017，2026-10-29。
- 最近认识更新：2026-11-01，用户已完整串述数据来路、训练、完成通知、暂停、权重更新、恢复与评估的顺序。本次对通知发起者与实参、发布含义和恢复条件补充精确措辞；不将整体复述扩展为全部后端机制已掌握。
- 导航：[本步 scope](../../../01-scope.md#reading-order) · [本次整体复述](#whole-loop-restatement-20261101) · [① 数据进入训练](#data-handoff) · [② 完成通知](#training-completion) · [③ 权重交接](#weight-handoff) · [④ 评估](#periodic-evaluation)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：生成与训练资源已准备好，由 driver 组织多轮 rollout 和训练。rollout_manager 是生成侧远程句柄，actor_model 是 create_training_models 返回的策略模型训练组。

2. **具体内容**：启动时准备训练组并推送权重；每轮取得训练数据引用，提交并等待训练，通知生成侧本轮完成，再组织权重更新和后续生成。评估按周期安排，资源与 checkpoint 分支负责各自的运行管理。

3. **建议构建的心智模型**：

   > train 负责接起一轮的交接：生成侧交回数据引用 → 提交训练并等待完成 → 通知数据侧处理本批完成登记 → 暂停新接纳 → 发布已有新参数给生成侧 → 有下一轮时按原状态恢复 → 满足条件时评估。
   >
   > 数据引用指向要训练的样本；训练任务引用用于等 worker 完成工作，两者承担不同职责。

4. **调用代码**（main:110–112，真实调用；不展开 startup 的创建过程）：

   ```python
   train(
       startup.args, startup.placements, startup.manager, startup.num_rollout_per_epoch, startup.restore_plan
   )
   ```

## 本场景的输入与输出

**整张卡要看懂什么**：按 scope 的[总体骨架学习目标](../../../01-scope.md#whole-train-card-learning-targets)，核心是接清 51 行数据输入、67 行训练与等待、71 行消费登记、88–93 行权重同步与恢复；启动和评估先保留作用与位置。下面的分段解释均服务于这一轮主线。

本轮沿 use_critic=False、默认 object-store 传输的正常路径。输入是 args、资源布局 pgs、rollout_manager、每 epoch 的轮次数和 restore_plan；循环开始前训练组已由 16 行创建。先只观察一个外层 rollout_id，生成侧的工作复用已读链路。

整个 train 没有显式返回值，正常结束返回 None。它的主要结果是完成若干轮训练和生成侧权重交接；当前前三段已展开到直接接口，周期评估仍只定位。

<a id="data-handoff"></a>

### 第一段：数据引用从生成侧交给训练侧（51 → 67）

**先观察 67 行的训练调用，51 行说明它的输入来源。** 本段围绕三个问题：传进去的是什么，训练组将工作交给谁，外层等待什么。需要看内部时，只沿 async_train 的直接提交接口展开，再回到当前两行。

真实语句节选。两行之间省略资源卸载与重建分支，并选中 use_critic=False 分支；后一行之后继续到 71 行的完成通知。

```python
rollout_data_ref = ray.get(rollout_manager.generate.remote(rollout_id))
# 当前无 critic，省略其他配置分支。
ray.get(actor_model.async_train(rollout_id, rollout_data_ref))
```

**进入这里时**，上一阶段的 [split_by_dp](../slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-eight-samples) 会返回按 DP rank 组织的引用列表。沿用 A–H 的结构说明如下；ObjectRef 不是本次真实运行取得的编号。

```text
rollout_data_ref：list
├─ Box.inner → 数据的 ObjectRef → DP rank 0：A、B、E、F 及字段、微批安排
└─ Box.inner → 数据的 ObjectRef → DP rank 1：C、D、G、H 及字段、微批安排
```

- **51 行：接住生成调用的返回值。** generate.remote 提交远程方法；外层 ray.get 等它返回，得到上述 list。里面指向各 rank 数据的引用仍保存在 Box 中。
- **67 行：把同一个列表传给训练组。** 本地 [RayTrainGroup.async_train](/home/hongshi/projects/slime/slime/ray/actor_group.py:148) 为训练 worker 提交 train.remote 调用，返回这些远程训练任务的引用列表。名字含 async，但这个接口是普通 def，当前不是 asyncio 协程调用。
- **67 行的外层 ray.get：等待训练任务结束。** 当前 actor 路径中，单个 worker 任务正常结束后返回 None；本行等待这一组任务完成，但没有保存对应结果列表，而是随后进入 training_completed 通知。怎样完成训练留给 worker，当前先看清交接。

<a id="async-train-submission"></a>

#### 当前精读交给哪张卡，读完回到哪里

**先读 [RayTrainGroup.async_train 独立函数卡](../slime/ray/actor_group.py/RayTrainGroup.async_train.md)。** 它接住 rollout_data_ref，给各 worker 提交训练任务，并返回任务结果引用列表；内部核心骨架与输入输出保存在该卡。

回到本函数 67 行后，由外层 `ray.get(...)` 等待这些任务。正常路径中等待成功，再进入 71 行完成通知。原有完整展开保存在 [拆卡前快照](../../../references/history/train-before-async-train-card.md#async-train-submission)，本函数继续负责说明数据来路、等待和后续交接。

<a id="wait-for-all-training-results"></a>

**2026-10-30 回顾：async_train 返回，不等于整行已经执行完。** 内层先提交调用、交回结果引用列表；外层 ray.get 再等待列表里所有引用对应的训练调用正常完成，才允许主循环继续到完成通知。部分 worker 已结束、仍有其他 worker 在训练时，正常路径继续等待。

下面把原来的嵌套调用拆开作教学说明，refs 是解释用变量，原源码没有这一赋值：

```python
refs = actor_model.async_train(rollout_id, rollout_data_ref)  # 提交训练，取得结果引用列表
ray.get(refs)  # 等待列表内所有训练调用正常完成
ray.get(rollout_manager.training_completed.remote(rollout_id))  # 随后通知本轮完成，并等通知处理完
```

这里等待的是实际远程调用的完成，不是只等引用对象生成。当前 actor 的正常结果为 None，仍然必须等它的训练调用执行结束才能取得这个 None。若远程调用失败，ray.get 可能抛异常，不会按正常成功路径继续发送完成通知。

| 在这段中出现的引用 | 指向什么 | 本层如何使用 |
| --- | --- | --- |
| rollout_data_ref 内部的数据 ObjectRef | 各 DP rank 的训练数据与安排 | 传给训练组，供训练侧取用 |
| async_train 返回的任务 ObjectRef 列表 | 各训练 worker 的运行结果 | 用 ray.get 等待全部完成 |

前一份列表按 DP rank 组织；后一份列表按训练 worker 组织。一个 DP 副本可能跨多个 worker，所以不能凭本例有两个数据分片就断言只提交两个训练任务。

**这段走完后**：训练调用已经结束，可以继续到 71 行通知生成侧本轮完成。此时还没有走到 89 行的生成侧权重更新。

| 需要回查时进入 | 看清什么后返回 |
| --- | --- |
| [split_by_dp 收尾](../slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-return-refs) | 看清 Box 包裹的数据引用后，回到 51 行接收这个列表 |
| [async_train 函数卡](../slime/ray/actor_group.py/RayTrainGroup.async_train.md) | 只核对提交 worker 调用及返回任务引用，回到 67 行的 ray.get |

<a id="training-completion"></a>

### 第二段：训练结束后通知管理侧（71）

<a id="completion-versus-admission-pause"></a>

**先分清主循环中的两个独立调用：**

| 调用位置 | 调用链 | 真正改变什么 |
| --- | --- | --- |
| 71 行 `training_completed(rollout_id)` | RolloutManager → BatchBuilder → 有批次时调用 controller.finish_batch | 更新这批训练数据的消费进度，移除其未完成登记并保存 |
| 88 行 `pause_rollout_admission()` | RolloutManager → 已注册的后台 worker / 调度器的 pause | 暂停领取和启动新的生成任务 |

同一个 RolloutManager 提供这两个入口，但它们操作不同对象。controller.finish_batch 完成后返回，不决定停止 rollout；主循环随后在 88 行另行发起暂停。71 行的外层 ray.get 等的是登记调用完成，不是只等消息发送出去。若没有登记批次，则 71 行通知直接正常返回。

上一行已经等待本轮训练成功结束，现在向管理器提交完成通知，并等通知处理完：

```python
ray.get(rollout_manager.training_completed.remote(rollout_id))
```

具体方法见 **[RolloutManager.training_completed 函数卡](../slime/ray/rollout.py/RolloutManager.training_completed.md)**。它转交给 BatchBuilder；当前默认路径的 batch_id=None，所以直接结束。存在批次记录时才核对轮次并通知 controller.finish_batch，让需要批次管理的数据路径收尾。

本行返回值在正常路径中为 None，调用方不保存它。这里完成的是通知处理；后面的 checkpoint、生成侧权重更新仍有各自的位置。

<a id="weight-handoff"></a>

### 第三段：先暂停接纳，再更新权重，按需恢复（88–93）

**从暂停接口返回后，进入 89 行的 [RayTrainGroup.update_weights](../slime/ray/actor_group.py/RayTrainGroup.update_weights.md#worker-update-submission)**，只看同步调用的提交与内部等待。需要回顾暂停时使用 [pause_rollout_admission 卡片](../slime/ray/rollout.py/RolloutManager.pause_rollout_admission.md#mental-model)，父卡继续保留完整组合。

**当前回看：训练与同步改变的是两处参数。** 67 行的 async_train 和外层 ray.get 已完成训练侧的参数更新；89 行再把这份训练结果同步给生成侧。先看[两次调用的区别](../slime/ray/actor_group.py/RayTrainGroup.update_weights.md#training-versus-weight-sync)，不要把后者理解为训练完成后才开始计算训练侧的新权重。

这里区分执行顺序与精读重点。执行时先进入 pause_rollout_admission；阅读时先把这一步的接口含义说清，再重点进入 update_weights。

```python
was_paused = ray.get(rollout_manager.pause_rollout_admission.remote())  # 88：暂停新任务接纳
actor_model.update_weights()                                        # 89：更新权重并等待
if rollout_id + 1 < args.num_rollout:                                 # 92：还有下一轮
    ray.get(rollout_manager.resume_rollout_admission.remote(was_paused)) # 93：按原状态恢复
```

- **暂停范围**：管理器找到已注册的 fully_async consumer，调用 pause(drain=False)，停止后台调度的新任务接纳；此处不会直接取消全部在途生成，也不表示将整个模型 HTTP 服务关掉。没有对应 consumer 时返回 True，没有额外暂停动作。
- **was_paused 是原状态**：记录调用前是否已暂停，不是暂停是否成功。后面只有原先未暂停时才恢复；原来暂停的 producer 保持原状态。
- **精读中间调用**：[RayTrainGroup.update_weights 卡片](../slime/ray/actor_group.py/RayTrainGroup.update_weights.md) 解释提交更新与内部等待。更新的通信机制留在下层。本轮训练计算已由 67 行等待结束；当前是把新权重同步给生成侧，训练 worker 仍参与同步，主循环尚未进入下一轮训练。
- **恢复的条件**：外层有下一轮才调用 resume；管理器再依据 was_paused 决定是否真正恢复。最后一轮不为新的训练 rollout 恢复接纳。

pause 的粒度与原状态返回依据是 rollout.py:151–158、AsyncRolloutWorker.pause:114–122 及分布式 producer 的 pause:209–226；本轮只核对接口，不重新阅读 worker 全部调度。

<a id="resume-after-weight-sync"></a>

**下一个观察点是上面 92–93 行的恢复接纳。** 从 update_weights 卡回来后，只需对照“还有没有下一轮”和“was_paused 记录的原状态”。必要时回查 [resume_rollout_admission:156–158](/home/hongshi/projects/slime/slime/ray/rollout.py:156)，不继续展开整个 worker 调度。

现在单独使用 [RolloutManager.resume_rollout_admission 卡片](../slime/ray/rollout.py/RolloutManager.resume_rollout_admission.md#mental-model)：先读外层是否还有下一轮，再看方法是否应该恢复原状态，最后只核对后台将 paused 设为 False 的效果。

<a id="resume-admission-meaning"></a>

#### 2026-10-30 回看：这里恢复的是什么

“接纳”指后台 rollout producer 继续领取、启动新的生成任务。它与前面的 training_completed 分属两项管理：后者登记已经训练完的批次；这里控制接下来是否还允许新任务进入生成流程。

先看用途：本轮 async_train 已在训练侧算出新参数；[update_weights](../slime/ray/actor_group.py/RayTrainGroup.update_weights.md#training-copy-to-generation-copy)将它们同步给生成引擎。同步前暂停新任务接纳，同步后再按条件放开，让后续生成可以使用更新后的参数。暂停新接纳不表示所有已有任务都被取消，恢复也不是重新训练、重启服务或重跑旧任务。

两个条件分在两层：

1. train.py:92 检查还存在下一轮，才调用恢复接口；最后一轮无需再为下一轮接入任务。
2. RolloutManager.resume_rollout_admission 检查 was_paused。它保存的是这次暂停之前的状态；原先未暂停才调用 producer.resume，原先已暂停则保持原状态。

| 暂停前 | 同步时 | 同步后还有下一轮 |
| --- | --- | --- |
| 可以接新任务，was_paused=False | 暂停接新任务 | 恢复接新任务 |
| 已经暂停，was_paused=True | 保持暂停 | 保持原来的暂停 |

这张表只说明正常路径中的接纳状态，不模拟真实运行或在途请求收束。用户本轮明确表示尚未理解，以上解释仍待反馈。

<a id="periodic-evaluation"></a>

### 第四段：按条件评估，随后进入下一轮（98–99，仅定位）

本方法的评估职责已单独整理在 [RolloutManager.eval 短期记忆](../slime/ray/rollout.py/RolloutManager.eval.md#mental-model)。父卡保留触发条件和主循环交接，子卡说明评估调用及结果去向。

本轮训练后的权重已同步，恢复接纳也已经按条件处理。主循环最后检查是否到达评估时点：

```python
if should_run_periodic_action(rollout_id, args.eval_interval, num_rollout_per_epoch):  # 判断是否到评估时点
    ray.get(rollout_manager.eval.remote(rollout_id))  # 提交评估，并等本次评估处理完成
```

这里只需接清三件事：

1. **什么时候评估**：eval_interval=None 时关闭这个周期评估；启用后，按 rollout_id+1 达到指定间隔或 epoch 边界时触发。这里只定位判断规则，不另展开调度工具。
2. **交给谁处理**：RolloutManager.eval 在正常路径中以 evaluation=True 调用评估生成实现，整理并记录评估结果；本处观察训练后模型的表现，不调用训练组做新的梯度训练。
3. **之后去哪里**：本次评估处理完成，或条件不满足跳过评估后，当前 for 循环体结束；还有下一轮就回到生成入口，所有轮次结束则离开 train。

源码依据：misc.py:119–140 的周期判断；rollout.py:392–412 的 eval 入口。当前只定位正常调用及返回位置，不进入评估数据集、评分和日志的内部实现，也没有运行评估。完整主线仍见 [scope](../../../01-scope.md#reading-order)。

## 我的直接表述（原话）

<a id="whole-loop-restatement-20261101"></a>

### 2026-11-01：从数据来路到周期评估的整体复述

以下节选本次完整消息的技术复述部分；关于 task flow 与 scope 的展示反馈见[完整原话与核对](../../../04-flow.md#whole-loop-restatement-20261101)。只采用用户最后完整发送的版本，不重复记录被中断的草稿。

> 我来简单说一下吧
> 这里其实在做的内容是
> 拿到rollout data部分的
> 然后通过之前应该是topics 02的部分
> 来说清楚这里到底应该如何得到这里的rollout
> 同时获得到对应的数据
> 然后这里把这些数据全部都交给选连的部分
> 然后希望的是通过这些训练的部分告知之列的roloout manager training completed 的部分
> 使用了哪些数据
> 然后让这里的rollout的部分
> 暂停这里的型的问题接受
> 然后赞确定不再接受新的rollout的部分的情况下
> 开始对于actor model的更新
> 之后如果这里还是在训练的情况下
> 那么就继续恢复接纳
> 如果到了评估的轮次
> 那么就开始周期性质的评估
> 是对于这里的04的完整理解
> 也就是step017的完整理解

用户已将 Topic 02 的生成数据来路与本步训练、完成通知、暂停、权重更新、恢复和周期评估的顺序连起来。这里的“完整理解”是用户对本轮职责主线的自述，不扩大为全部后端机制已掌握。

**本次源码校准，尚待用户对精确措辞反馈**：

- 完成通知由 train 主循环在等待训练结束后发出，传入 rollout_id；管理器通过已有批次记录处理本轮完成状态，不是训练函数再提交一份已用数据列表。
- 89 行 update_weights 由训练组组织，将已经训练好的参数发布给生成侧；本轮训练侧参数更新在 67 行等待结束前完成。
- “继续恢复”具体对应：还有下一轮，且 was_paused=False。用户对暂停新接纳的描述与当前主例一致；已有在途任务的边界继续保留。

用户确认开启本步：

> 好的那么开启这一个step吧

开启本步时尚无针对 train 内部交接的个人表述。前一步对数据交付的理解完整保留在调取的 split_by_dp 卡片及本步 03 中，不将范围确认当作本函数已理解；本轮新增表述见下方。

用户在本步开始后再次要求明确起点并对齐岗位：

> 好的 我们来看一下看一下 我们应该先从哪里开始读呢？
> 重点记得对齐一下这个job description

这次要求影响观察重点：先看组件之间传递什么及完成边界，再接训练闭环；不是对本函数内部已有理解的表述。用户附带的岗位正文另在岗位证据中保存与复核。

用户在综合审查剩余范围后要求继续：

> 好的那么继续看一下这里的几个steps吧

当时据此继续已有 Step 017 的第一段，展开训练提交与等待；当时尚无用户对上述两类引用或 worker 分发的直接解释，不将“继续”记作理解确认。

本轮用户对数据来路与当前入口的复述：

> 好的 那么我们来看一下这里的内容吧
> 我们之前吧rollout manager 得到的sample变成了rayref 来传给这里的megatron对吧
> 然后我们目前需要看一下这里的actor_model.async_train
> 我是这么理解的对吗/

这段表述已接上生成数据到训练的总体方向。助手补充 Sample → 训练字段 → DP 分片 → 数据引用的中间步骤，以及 RayTrainGroup 提交层和 Megatron worker 执行层的区别；这两项精确区分尚待用户后续反馈。

用户随后反馈并要求继续：

> 好的 我现在大概理解这里的async train了 让我们继续吧

据此记录第一段的总体理解反馈，并继续第二段完成通知；不把反馈扩展为所有后端与失败细节已掌握。

用户在第三段指出暂停操作先于更新：

> 然后下一步不是这里的paused吗？
> 虽然应该也很好理解
> 就是原有的rollout部分不再接受新的请求应该是这个意思对吧
> actor model 更新权重我们先看这一步吗？

执行顺序按用户指出的先 pause 后 update 保留；暂停的具体粒度和原状态字段由助手核对，精读重点为 update_weights，理解待反馈。

2026-10-30 用户明确反馈（节选，完整消息分存于三个子函数卡及 flow）：

> 然后这里的是下面的更新权重
> 但是这里我其实没有太过于看懂
> 或者说你说的恢复rollout接纳这里 其实我也没有特别理解

据此回看第三段的同步目的与后台接纳含义，不把此前“下一观察点”当作已理解。见[本轮回顾与校准](../../../04-flow.md#training-review-and-resume-20261030)。

2026-10-30 用户对等待位置的追问：

> 但是这个部分是需要等待的吗?
> 我的意思这里的train的部分是在提交训练并且完成之后
> 就直接到了下一步
> 还是会在这里等待直到返回了所有的结果呢?

本轮澄清内层 async_train 交回引用列表与外层 ray.get 等实际调用完成的区别；以上解释尚待用户反馈。此前对 async_train 的总体理解反馈继续保留，不因本次追问清零。见[本轮等待边界记录](../../../../step-017-generation-training-loop/04-flow.md#wait-for-training-before-notification-20261030)。

2026-10-30 用户对等待边界的反馈：

> 好的 我大概理解了
> 这里会在调用完成之后
> 才会到下面异步
> 也是我需要看的这个ray get rollout manager training completed remote对吗?

这段表述已接清先等训练调用完成，再进入完成通知的执行顺序。下一行的 `.remote()` 远程提交通知，外层 `ray.get` 仍会等通知处理完；这一补充尚未单独获得反馈，不将“下面异步”改写为主循环无需等待。见[本轮接续](../../../../step-017-generation-training-loop/04-flow.md#training-wait-understood-next-notification-20261030)。

## 尚不清楚

以下保留阅读形成过程中的未知；最新表述以对应子卡为准。[本步主线总结](../../../05-task-flow.md)只收束正常交接，不消除尚未展开的内部实现问题。

- 用户已给出 async_train 的总体理解反馈；未逐项复述的细节继续保留在该函数卡，不据此扩大为后端实现已掌握。
- 已将数据引用与 Megatron 训练联系起来；训练组提交层与后端执行层、Sample 与整理后的训练数据的区分，已补充说明，理解待反馈。
- worker 怎样从整个引用列表选取所属 DP 数据，以及怎样执行微批，当前未展开。
- training_completed、暂停、权重更新、恢复和评估的整体位置已有 2026-11-01 连贯复述；本次对通知发起者与实参、发布含义、恢复双条件的精确校准尚待反馈。创建对象、卸载、checkpoint、loss 与优化器仍为边界。
- 2026-10-30 曾明确反馈权重更新和恢复接纳仍不理解；后续逐步反馈及本次[整体复述](#whole-loop-restatement-20261101)已补充这一历史状态。具体传输、在途请求协调和异常恢复仍未展开。
- 尚无真实 Ray、模型或训练运行；图示不能作为实际性能、运行成功或训练结果的证据。

<details>
<summary>来源、验证与完整例子</summary>

- [2026-11-01 整体复述与源码校准](../../../04-flow.md#whole-loop-restatement-20261101)：沿用固定版本核对，没有新增真实运行。
- [Step 017 范围确认](../../../04-flow.md#step-017-opened) · [首个交接的静态核对](../../../04-flow.md#first-reference-handoff)。
- [本轮训练提交带读](../../../04-flow.md#async-train-submission-walkthrough)：沿既定范围补充直接接口代码和两类引用的去向。
- [用户复述与 Megatron 层次校准](../../../04-flow.md#sample-refs-to-megatron)：数据来路、当前阅读入口与默认后端的关系。
- 固定源码：train.py:13–99；RayTrainGroup.async_train:148–167；RolloutManager.generate:317–333。具体文件哈希见 [源码证据](../../../references/source-evidence.json)。
- 数据结构承接 Step 016 的 A–H 例子及本步调取的 split_by_dp 卡。继承与调取记录见 [继承清单](../../../references/inheritance-manifest.json)、[调取清单](../../../references/active-retrieval.json)。
- [Ray 对象与引用说明](https://docs.ray.io/en/latest/ray-core/objects.html)用于区分远程调用返回、数据引用与读取值；不据文档推断本机安装版本。
- [Ray 官方 actor 方法调用](https://docs.ray.io/en/latest/ray-core/actors.html#calling-the-actor)说明 `.remote()` 返回引用、`ray.get()` 取得结果；2026-10-29 只读核对。示意图与拆开的两行代码没有作为运行实验执行。
- 本轮验证为静态读取源码及链接/继承完整性检查，没有运行 train 或创建虚拟的训练结果。

</details>
