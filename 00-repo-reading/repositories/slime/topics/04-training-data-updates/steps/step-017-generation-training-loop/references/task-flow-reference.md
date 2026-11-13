# 05 · 一轮数据怎样完成训练，并交回生成侧

> **本页首先要建立的关系：本轮数据交给训练 → 训练侧得到新参数 → 新参数发布给生成侧，供后续生成使用。**
>
> 完成登记、暂停与恢复是这条主线上的配套动作；评估是满足条件才执行的分支。它们都保留在执行顺序中，内部机制按需展开。

[本步范围](../01-scope.md) · [函数记录](../02-short-term-memory/overview.md) · [形成过程](../04-flow.md#complete-task-flow-reference-20261031) · [原任务总结](../05-task-flow.md)

**先读什么**：沿用你认为清楚的 [scope 3.1 整体位置](../01-scope.md#31-整体位置)与 [3.2 核心骨架](../01-scope.md#core-skeleton)，再从本页 [2.1 主骨架](#loop-skeleton)按执行顺序读完一轮：每一步接住上一段的结果，再交给下一段。

**哪里需要再展开**：哪一步的交接不清楚，再进入对应小节；整轮串起来后，用[第 3 节](#results)核对结果。主次决定展开多深，主读顺序始终跟随 train，不跳过登记或暂停直接串接两个重点。

## 1. 本步接住什么，到哪里结束

数据来路承接 [Topic 02 的生成、评分与收集](../../../../02-rollout-reward/README.md)，以及其中 [Step 016 的训练数据整理](../../../../02-rollout-reward/steps/step-016-sample-to-train-data/README.md)：Sample 整理为训练字段并按 DP 分片后，交回 `rollout_data_ref: list[Box]`，每个 Box 包装一个分片的 Ray 数据引用。

指挥官是驱动进程中的 `train.py::train`。其中 `actor_model` 是本地的 RayTrainGroup 对象，持有远端训练 worker 的句柄；`rollout_manager` 是远端管理器的句柄。本步从 **51 行接住数据**走到**99 行之后进入下一轮或结束函数**。

本文沿无 critic、资源可用、直接同步权重的正常路径。暂停机制采用已读的**本地 AsyncRolloutWorker** 场景；完成登记分别说明有、无批次记录两种情况。后台实现的选择还取决于数据源，不由 object-store 这个传输名称单独决定。

<details>
<summary>背景回查：进入循环前，模型和后台怎样准备</summary>

循环前的 16–25 行只需保留背景：建立训练组 → 向生成侧推送载入的权重 → `training_ready` 通知准备完成，允许恢复场景中此前冻结的后台接续。循环内的权重发布则发生在本轮训练之后。

</details>

## 2. 一轮怎样完成交接

<a id="loop-skeleton"></a>

### 2.1 先看主骨架：只跟随 train 这一层

教学裁剪：保留真实接口、关键实参和业务条件；折叠 critic、训练前评估、checkpoint、资源处理与外层清理。省略号代表这些阅读中未展开的参数，不是可直接执行的完整脚本。

```python
# train.py::train；①②③④与下面的小节对应
actor_model, critic_model = create_training_models(...)  # 16：建立训练组
actor_model.update_weights()  # 22：先向生成侧发布已载入的权重
ray.get(rollout_manager.training_ready.remote())  # 25：通知启动准备完成

for rollout_id in range(args.start_rollout_id, args.num_rollout):
    rollout_data_ref = ray.get(rollout_manager.generate.remote(rollout_id))  # 51：接住数据

    ray.get(actor_model.async_train(rollout_id, rollout_data_ref))  # 67：① 提交训练并等待
    ray.get(rollout_manager.training_completed.remote(rollout_id))  # 71：② 登记本批已用过

    # 73–87：这里折叠 checkpoint 与资源处理，随后进入权重交接
    was_paused = ray.get(rollout_manager.pause_rollout_admission.remote())  # 88：③a 暂停新接纳
    actor_model.update_weights()  # 89：③b 发布新权重；等待在方法内部
    if rollout_id + 1 < args.num_rollout:  # 92：还有下一轮
        ray.get(rollout_manager.resume_rollout_admission.remote(was_paused))  # 93：③c 按旧状态恢复

    # 95–96：这里折叠生成侧 KV 资源恢复
    if should_run_periodic_action(...):  # 98：满足配置的评估条件
        ray.get(rollout_manager.eval.remote(rollout_id))  # 99：④ 评估并记录
```

**顺着这一轮读**：拿到数据引用 → ①交给训练并等完成 → ②通知数据侧本批已用过 → ③a暂停新接纳 → ③b发布已有新参数 → ③c有下一轮时按原状态恢复 → ④满足条件时评估。训练与发布改变的是两侧参数，登记和接纳控制则说明它们之间怎样交接。

主骨架仍保留所有这些动作，避免把“阅读时少展开”误读成“执行时可以跳过”。

局部入口：[① 训练](#train-handoff) · [② 登记](#completion-handoff) · [③ 暂停、发布、恢复](#weight-handoff) · [④ 评估](#eval-handoff)。

**代码读法**：标明所属函数的短代码是源码裁剪，保留真实调用和等待位置；带树线的块是调用关系图，不是 Python 程序。普通调用、Ray 调用与后台协作分别标明；`#` 旁注紧贴对应动作，具体高亮颜色由阅读器主题决定。

<a id="train-handoff"></a>

### 2.2 主线 · ①训练：交入数据引用，等待训练调用完成

**面包屑**：[主骨架](#loop-skeleton) → **① train.py:67** → RayTrainGroup.async_train。

进入时，主循环已经接住本轮 `rollout_data_ref` 和轮次 `rollout_id`。

```python
train.py:67  # 驱动进程在外层 ray.get 等待
└─ RayTrainGroup.async_train(...)  # 普通调用；分发训练任务
   └─ actor.train.remote(...) × 每个训练 worker  # Ray 提交；每个调用交回一个结果引用
```

每个训练 worker 收到的是**整份数据引用列表**。async_train 收集各次提交得到的 ObjectRef，返回一个**训练结果引用列表**；外层 ray.get 再等待这些引用对应的调用完成。

**结果与返回**：actor 的正常返回值是 None，训练得到的新参数留在训练 worker 中。驱动结束 67 行的等待，才能进入[② 完成登记](#completion-handoff)。

回查：[提交、数据与结果引用](../02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.async_train.md#remote-return-versus-train-return)。本节不展开 worker 内部的取数、loss 与优化器。

<a id="completion-handoff"></a>

### 2.3 配套 · ②完成登记：这批数据已经用过

**面包屑**：[主骨架](#loop-skeleton) → **② train.py:71** → RolloutManager.training_completed。

```python
# train.py:71；前提：本轮训练已经结束
ray.get(rollout_manager.training_completed.remote(rollout_id))  # 通知数据侧，并等处理结束
# 有登记批次：处理消费登记；没有登记批次：直接返回
# 接着经过保存和资源处理，再进入③a暂停接纳
```

**这一段的作用**：收尾本批的数据使用记录，然后回到主循环。

<details>
<summary>需要追踪通知经过谁时再展开：Manager → BatchBuilder → Controller</summary>

进入时，训练已经正常完成；这次通知交入的是轮次编号 `rollout_id`。

```python
train.py:71  # 驱动用 ray.get 等待完成通知处理结束
└─ RolloutManager.training_completed(rollout_id)  # Ray 调用；接收轮次
   └─ BatchBuilder.training_completed(rollout_id)  # 普通调用；查询当前批次登记
      ├─ batch_id is None  # 无登记批次，直接结束
      └─ 有批次且 rollout_id 匹配
         └─ RolloutQueueController.finish_batch(batch_id)  # Ray 调用；Builder 等待登记完成
```

**结果与返回**：有登记时，Controller 更新消费进度、移除本批未完成登记并保存状态；随后逐层返回，驱动结束 71 行的等待。物理存储回收受额外配置控制。轮次不匹配会报错，不进入正常返回路径。

这一段完成的是数据使用记录的收尾。返回主循环后，经骨架中折叠的保存与资源处理，接着才到[③a 暂停新接纳](#pause-admission)。

回查：[完成通知与消费登记](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md#mental-model)。登记完成不代表模型与数据已经形成共同的持久化 checkpoint。

</details>

<a id="weight-handoff"></a>

### 2.4 ③ 权重交接：暂停新接纳 → 发布 → 按旧状态恢复

这一组动作让生成引擎接收训练成果，并控制这段交接期间是否继续接入新任务。三个动作的完成条件不同，分别看下面的交接。

<a id="pause-admission"></a>

#### 2.4.1 配套 · ③a暂停：等后台确认停止新增接纳

**面包屑**：[主骨架](#loop-skeleton) → [③ 权重交接](#weight-handoff) → **③a train.py:88**。

```python
# train.py:88；当前采用已在正常运行的本地后台
was_paused = ray.get(rollout_manager.pause_rollout_admission.remote())  # 等后台确认暂停新接纳
# was_paused 保存暂停前状态，供③c判断是否恢复
# 在途任务可能仍在运行；接下来进入③b发布权重
```

**这一段的作用**：先关住新任务入口，再把控制权交给权重发布。

<details>
<summary>需要解释“暂停确认”时再展开：请求、后台响应与返回</summary>

```python
train.py:88  # 驱动等待调用结束，并接住 was_paused
└─ RolloutManager.pause_rollout_admission()  # Ray 调用
   └─ 已登记的 worker.pause(drain=False)  # 普通调用；本地主例等待暂停确认
```

管理器从自己的 `data_source.consumers["fully_async"]` 找到后台对象。**本地 worker 正常运行、无错误时**，这次协调发生在两侧：

```python
# 调用侧：worker.pause
保存原 paused → 写 paused=True → 等待后台确认

# 后台侧：已经在运行的 worker._loop；不是 pause 的子调用
观察 paused=True → 停止新增接纳 → 写 admission_paused=True → notify_all()

# 调用侧被唤醒后复查条件
确认已暂停 → 返回原状态 → 管理器返回 → 驱动的 ray.get 结束
```

paused 是暂停请求，admission_paused 是后台确认，was_paused 保存调用前状态。

**结果与返回**：本地主例暂停新增任务，已有在途任务仍可能运行；drain=False 不要求等待它们全部结束。`was_paused` 保存调用前的状态，供后续恢复判断。没有登记后台时，管理器返回 True，不执行暂停。

接回主循环 89 行，进入[③b 发布权重](#publish-weights)。回查：[暂停请求、确认和返回](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.pause_rollout_admission.md#mental-model)。

</details>

<a id="publish-weights"></a>

#### 2.4.2 主线 · ③b发布：让生成侧接收训练后的参数

**面包屑**：[主骨架](#loop-skeleton) → [③ 权重交接](#weight-handoff) → **③b train.py:89**。

```python
# train.py:89；本轮训练已完成，新增接纳已暂停
actor_model.update_weights()  # 进入训练组的发布方法，等它返回再继续
```

该调用进入 RayTrainGroup，当前直接同步分支的核心是：

```python
# RayTrainGroup.update_weights 内部；省略其他分支
ray.get([  # 等所有训练 worker 的发布调用完成
    actor.update_weights.remote()  # 将已有新参数发布给生成侧
    for actor in self._actor_handlers
])
return  # 返回 None，回到 train.py:92–93 的恢复判断
```

**这一段的作用**：训练组等发布完成后再返回，使后面的恢复判断发生在本次权重交接之后。这里不再进行训练计算。

<details>
<summary>需要定位具体发布者时再展开：训练组 → 训练 worker → updater</summary>

进入时，训练 worker 已有本轮的新参数。这里发布已有参数；训练计算已经在①完成。

```python
train.py:89  # 驱动等待这个普通方法返回
└─ RayTrainGroup.update_weights()  # 方法内部 ray.get 等所有发布调用完成
   └─ actor.update_weights.remote() × 每个训练 worker  # Ray 调用；worker 持有训练后的参数
      └─ weight_updater.update_weights()  # Megatron worker 委派；本主例发布到生成引擎
```

**结果与返回**：直接同步主例正常完成后，生成引擎接收新权重；组方法返回 None，主循环进入 92–93 行的[③c 恢复判断](#resume-admission)。权重怎样传输、安装时怎样协调在途请求，仍由具体 updater 的实现负责。

回查：[发布职责、内部等待与磁盘分支对照](../02-short-term-memory/functions/slime/ray/actor_group.py/RayTrainGroup.update_weights.md#mental-model)。磁盘写入、释放训练 worker、引擎 reload 是另一条分支，不接在本图后面顺序执行。

</details>

<a id="resume-admission"></a>

#### 2.4.3 配套 · ③c恢复：有下一轮时，按原状态接纳

**面包屑**：[主骨架](#loop-skeleton) → [③ 权重交接](#weight-handoff) → **③c train.py:92–93**。

```python
# train.py:92–93；权重发布已经正常返回
if rollout_id + 1 < args.num_rollout:  # 还有下一轮，才请求恢复
    ray.get(rollout_manager.resume_rollout_admission.remote(was_paused))  # 交入原暂停状态
# 管理器内部仅在 not was_paused 时真正恢复新接纳
# 返回后继续判断评估条件；不等待下一批生成完成
```

**这一段的作用**：有下一轮时，按原状态恢复接纳权限。

<details>
<summary>需要核对两个恢复条件时再展开</summary>

```python
还有下一轮 → RolloutManager.resume_rollout_admission(was_paused)  # Ray 调用
└─ not was_paused → worker.resume()  # 原先未暂停，才重新允许接纳
   └─ paused=False  # 本地 worker 的状态变化
```

**结果与返回**：后台可以重新按接纳条件领取任务，返回不表示下一批已经生成。原先已暂停或此前没有后台时，was_paused=True，不恢复；没有下一轮时，主循环也不发恢复请求。

接回主循环，经过折叠的资源安排，判断是否执行[④ 评估](#eval-handoff)。回查：[恢复条件与状态修改](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.resume_rollout_admission.md#mental-model)。

</details>

<a id="eval-handoff"></a>

### 2.5 条件分支 · ④评估：保存并记录评估结果

**面包屑**：[主骨架](#loop-skeleton) → **④ train.py:98–99** → RolloutManager.eval。

```python
# train.py:98–99
if should_run_periodic_action(rollout_id, args.eval_interval, num_rollout_per_epoch):
    ray.get(rollout_manager.eval.remote(rollout_id))  # 等待评估、保存和记录完成
# eval 使用独立配置的评估函数，正常返回 None
# 条件不满足就跳过；随后进入下一轮或结束 train
```

**这一段的作用**：在指定时点评估并留下结果，然后接回循环。

<details>
<summary>需要追踪评估输入、输出及保存位置时再展开</summary>

评估启用且满足配置间隔或 epoch 边界时，主循环在权重交接后进入这里。没有下一轮生成，也不妨碍满足条件时使用已同步的引擎评估；这不表示最后一轮一定强制评估。

```python
train.py:99  # 驱动用 ray.get 等待本次评估处理结束
└─ RolloutManager.eval(rollout_id)  # Ray 调用
   ├─ call_rollout_fn(self.eval_generate_rollout, ..., evaluation=True)  # 调用独立配置的评估函数
   ├─ data = result.data  # 取评估数据；共享服务收尾在本图折叠
   ├─ save_debug_rollout_data(...)  # 按配置保存调试数据
   └─ log_eval_rollout_data(..., data, result.metrics)  # 记录评估结果
```

**结果与返回**：data 和 metrics 供本次保存与记录使用，eval 正常返回 None。驱动结束等待后，当前循环体完成：还有轮次就回到[2.1 的下一轮](#loop-skeleton)，否则离开 train；不满足评估条件则直接进行同样的循环判断。

评估函数来自 `args.eval_function_path`，不能由前面的本地 fully_async 后台主例推断其实现。回查：[评估入口、条件与返回](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.eval.md#mental-model)。

</details>

<a id="results"></a>

## 3. 这一轮的结果留在哪里

### 3.1 沿同一轮，区分两侧参数

v0、v1 只是说明训练前后参数的教学标记，不是一次真实运行测量。

| 时点 | 训练侧 | 生成侧 |
| --- | --- | --- |
| 本轮训练前 | 持有 v0 | 持有 v0 |
| ①训练正常完成 | 已得到 v1 | 尚未因训练计算自动得到 v1 |
| ③b 直接同步正常完成 | 持有 v1 | 已接收 v1，供后续请求使用 |

已有在途任务可能跨越这些时点；本表不推断每份样本的权重版本，也不代替 updater 对在途请求的具体协调。

<details>
<summary>按需核对：引用、消费登记与控制状态分别交给谁</summary>

### 3.2 其余数据和控制状态的去向

| 内容 | 谁接住、用来做什么 |
| --- | --- |
| 数据引用列表 `rollout_data_ref` | 各训练 worker 收到，用于读取本轮训练数据 |
| 训练结果引用列表 | 驱动中的 ray.get 接住并等待；正常 actor 结果为 None，参数留在 worker 内 |
| 本批消费登记 | 有登记时由 Controller 保存；后续数据管理不再把该批列为等待完成确认 |
| `was_paused` | 驱动暂存，交给恢复接口，避免打开原先已经暂停的后台 |
| 评估 data / metrics | 管理器用于保存与记录；不作为新的训练批次返回驱动 |

**把这些结果接起来**：数据引用负责“把数据交给训练”；训练结果引用负责“等训练调用”；新参数通过③b 交给生成侧；消费登记和暂停状态分别服务于数据管理与生成接纳。

</details>

## 4. 本步在哪里收束

正常主线到**训练数据进入 worker、训练完成、适用的消费登记完成、权重发布、按条件恢复与评估**为止。这样就能从前一步的数据交付接回后续生成。

各函数记录中的未知继续保留：训练计算、具体权重传输与安装、在途请求协调、磁盘与完整恢复、存储回收和具体评分实现。遇到相关修改或故障再回查，不因编写本页增加必读范围。

本文整理已发生的阅读与讲解；完整机制掌握和真实运行验证分别记录，当前状态仍看[唯一路线](../../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。后续投入沿用[已有岗位复核](../../../../../slime后续阅读顺序/2026-10-29-existing-foundation-and-remaining-scope.md#jd-recheck-20261031)。

<details>
<summary>回顾时的三个可选观察点</summary>

可以先遮住说明，用自己的话连接这三个关系，再回对应位置核对；不作为继续阅读的验收门槛。

- 为什么①完成后，仍需要③b？
- ③a 返回时，什么已确认，什么可能仍在运行？
- ②没有 batch_id 时，为什么仍能返回主循环？

</details>

<details>
<summary>为什么这样组织：认知设计依据</summary>

本页以工作记忆、注意控制和学习研究为设计依据，把它们应用于源码回顾；不把某一种排版称为“最符合前额叶机制”的唯一最优形式。

用户指出阅读和认知需要主次后，本页不再平均展开所有环节：默认注意力集中在数据、训练与参数发布，以及决定它们何时完成的等待；配套动作仍在主骨架中可见，其内部实现折叠。主次体现为默认可见内容与展开条件，不以固定字数或函数数量代替。

- **把上下文留在页面上**：Baddeley（2012），[Working Memory: Theories, Models, and Controversies](https://www.annualreviews.org/content/journals/10.1146/annurev-psych-120710-100422)，讨论有限的暂时保持、操作与注意控制。本页用主骨架、明确对象和返回位置减少需要同时在脑中维持的关系。工作记忆不是单一的“前额叶缓存”，研究也不能推出每页应固定放几个函数。
- **按需分段，解释紧邻对象**：Mayer 与 Moreno（2003），[Nine Ways to Reduce Cognitive Load in Multimedia Learning](https://doi.org/10.1207/S15326985EP3801_6)，讨论学习者控制的分段、结构提示及邻近解释。本页用相同编号连接总览和局部，用旁注解释对应调用。这些研究主要针对多媒体科学过程解释；把方法用于 Markdown 调用图属于设计迁移，论文没有验证本页或绿色注释的最优性。
- **让回顾可以先尝试回忆**：Roediger 与 Karpicke（2006），[Test-Enhanced Learning](https://pubmed.ncbi.nlm.nih.gov/16507066/)，在散文学习实验中发现先前的回忆测试有助于延迟保持。本页提供可选回顾问题；不以强制复述作为继续阅读的门槛，也不把一次正确复述视为已具备工程能力。

实际要检验的是：隔天能否用主骨架找回这一轮，能否在局部章节准确指出数据、等待和返回关系。这里保留完整参考以供回查，并不要求一次阅读记住所有层次。

</details>

<details>
<summary>源码、旧例与验证范围</summary>

- 固定证据：`18868a79b0b083a093798a94ed0f8cb4f71b9c14`。本轮当前 checkout 为 `540ea919e45b8b929198abce008a103be9cfc779`；相关文件与固定版本的差异核对沿用本步记录，未重写旧版本来源。
- [train.py:47–99](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/train.py#L47-L99)：主循环、等待与业务条件。
- [actor_group.py:148–190](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/actor_group.py#L148-L190)：训练提交与发布等待；[Megatron 发布委派](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/backends/megatron_utils/actor.py#L629-L684)。
- [rollout.py:151–158](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L151-L158)：管理器暂停与恢复；[评估和完成通知](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L392-L431)。
- [batch_builder.py:144–148](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/batch_builder.py#L144-L148)：有无登记批次；[queue_data_source.py:814–827](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/queue_data_source.py#L814-L827)：消费登记。
- [本地 pause/resume](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L114-L126)、[独立后台的接纳与确认](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L202-L228)；本文不把这一实现替代为所有分布式后台的内部机制。
- [按主次修订前的完整快照](history/task-flow-reference-before-priority-2026-10-31.md)保留此前的平行展开结构；本次只调整展示优先级，执行顺序与阅读范围不变。
- [改为短代码前的完整快照](history/task-flow-reference-before-short-code-2026-10-31.md)保留上一版主次安排。本次只将 2.3–2.5 的默认讲解改为短代码与旁注，内部机制继续折叠。
- 结构参考：[Step 004 的数据变化](../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/05-task-flow.md)、[Step 008 的调用与返回](../../../../01-coding-agent-rl/steps/step-008-harness-communication/05-task-flow.md)、[Step 013 的后台交接](../../../../02-rollout-reward/steps/step-013-completed-group-handoff/05-task-flow.md)。[本次形式比较](task-flow-review-2026-10-31.md#recommended-two-level-flow)保留改稿依据。
- 历史局部验证仍以[原 async_train 替身实验](async-train-pairing-local-output.json)为准。本轮只做源码、文档和结构核对，没有运行真实 Ray、训练、权重发布或评估；不把 reference 写成实测运行报告。

</details>
