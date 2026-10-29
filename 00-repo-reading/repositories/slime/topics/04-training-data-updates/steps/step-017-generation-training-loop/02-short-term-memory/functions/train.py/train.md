# train

- 源码定位：[train.py:13](/home/hongshi/projects/slime/train.py:13)，固定版本 `18868a79`；调用方为 [main:110](/home/hongshi/projects/slime/train.py:110)。
- 首次接触：Step 017，2026-10-29。
- 最近认识更新：2026-10-29，用户明确表示大概理解 async_train，继续本轮训练后的完成通知；通知职责尚待反馈。此前数据来路与训练组/后端层次的个人表述继续保留。
- 导航：[本步 scope](../../../01-scope.md#reading-order) · [① 数据引用进入训练](#data-handoff) · [② 训练完成通知](#training-completion) · **[③ 当前：暂停接纳与权重更新](#weight-handoff)**。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：生成与训练资源已准备好，由 driver 组织多轮 rollout 和训练。rollout_manager 是生成侧远程句柄，actor_model 是 create_training_models 返回的策略模型训练组。

2. **具体内容**：启动时准备训练组并推送权重；每轮取得训练数据引用，提交并等待训练，通知生成侧本轮完成，再组织权重更新和后续生成。评估按周期安排，资源与 checkpoint 分支负责各自的运行管理。

3. **建议构建的心智模型**：

   > train 负责接起一轮的交接：生成得到数据引用 → 训练组使用这些引用 → 等训练完成 → 通知完成并更新生成侧权重。
   >
   > 数据引用指向要训练的样本；训练任务引用用于等 worker 完成工作，两者承担不同职责。

4. **调用代码**（main:110–112，真实调用；不展开 startup 的创建过程）：

   ```python
   train(
       startup.args, startup.placements, startup.manager, startup.num_rollout_per_epoch, startup.restore_plan
   )
   ```

## 本场景的输入与输出

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

上一行已经等待本轮训练成功结束，现在向管理器提交完成通知，并等通知处理完：

```python
ray.get(rollout_manager.training_completed.remote(rollout_id))
```

具体方法见 **[RolloutManager.training_completed 函数卡](../slime/ray/rollout.py/RolloutManager.training_completed.md)**。它转交给 BatchBuilder；当前默认路径的 batch_id=None，所以直接结束。存在批次记录时才核对轮次并通知 controller.finish_batch，让需要批次管理的数据路径收尾。

本行返回值在正常路径中为 None，调用方不保存它。这里完成的是通知处理；后面的 checkpoint、生成侧权重更新仍有各自的位置。

<a id="weight-handoff"></a>

### 第三段：先暂停接纳，再更新权重，按需恢复（88–93）

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

### 后面的阶段先定位

98–99 行按周期评估。完整顺序和裁剪边界放在 [scope](../../../01-scope.md#reading-order)，评估当前只定位。

## 我的直接表述（原话）

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

## 尚不清楚

- 用户已给出 async_train 的总体理解反馈；未逐项复述的细节继续保留在该函数卡，不据此扩大为后端实现已掌握。
- 已将数据引用与 Megatron 训练联系起来；训练组提交层与后端执行层、Sample 与整理后的训练数据的区分，已补充说明，理解待反馈。
- worker 怎样从整个引用列表选取所属 DP 数据，以及怎样执行微批，当前未展开。
- training_completed 按职责带过；暂停、更新、恢复的接口已展开，理解待反馈，评估继续只定位。创建对象、卸载、checkpoint、loss 与优化器仍为边界。
- 尚无真实 Ray、模型或训练运行；图示不能作为实际性能、运行成功或训练结果的证据。

<details>
<summary>来源、验证与完整例子</summary>

- [Step 017 范围确认](../../../04-flow.md#step-017-opened) · [首个交接的静态核对](../../../04-flow.md#first-reference-handoff)。
- [本轮训练提交带读](../../../04-flow.md#async-train-submission-walkthrough)：沿既定范围补充直接接口代码和两类引用的去向。
- [用户复述与 Megatron 层次校准](../../../04-flow.md#sample-refs-to-megatron)：数据来路、当前阅读入口与默认后端的关系。
- 固定源码：train.py:13–99；RayTrainGroup.async_train:148–167；RolloutManager.generate:317–333。具体文件哈希见 [源码证据](../../../references/source-evidence.json)。
- 数据结构承接 Step 016 的 A–H 例子及本步调取的 split_by_dp 卡。继承与调取记录见 [继承清单](../../../references/inheritance-manifest.json)、[调取清单](../../../references/active-retrieval.json)。
- [Ray 对象与引用说明](https://docs.ray.io/en/latest/ray-core/objects.html)用于区分远程调用返回、数据引用与读取值；不据文档推断本机安装版本。
- [Ray 官方 actor 方法调用](https://docs.ray.io/en/latest/ray-core/actors.html#calling-the-actor)说明 `.remote()` 返回引用、`ray.get()` 取得结果；2026-10-29 只读核对。示意图与拆开的两行代码没有作为运行实验执行。
- 本轮验证为静态读取源码及链接/继承完整性检查，没有运行 train 或创建虚拟的训练结果。

</details>
