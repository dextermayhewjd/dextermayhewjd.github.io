> 历史快照：2026-10-29 将 async_train 拆为独立函数卡之前的完整 train 卡。仅重算相对链接；原话、未知与当时的讲解保留。当前阅读入口见 [Step 017 scope](../../01-scope.md)。

# train

- 源码定位：[train.py:13](/home/hongshi/projects/slime/train.py:13)，固定版本 `18868a79`；调用方为 [main:110](/home/hongshi/projects/slime/train.py:110)。
- 首次接触：Step 017，2026-10-29。
- 最近认识更新：2026-10-29，用户首次将 RolloutManager 侧的样本、Ray 数据引用和 Megatron 训练联系起来，并确认当前入口为 actor_model.async_train。训练字段转换与训练组/后端层次的精确区分由助手补充，待反馈；任务返回引用尚无个人表述。
- 导航：[本步 scope](../../01-scope.md#reading-order) · [数据引用进入训练](#data-handoff) · **[当前：训练组怎样提交任务](#async-train-submission)** · [回顾 split_by_dp 返回结构](../../02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-return-refs)。

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

整个 train 没有显式返回值，正常结束返回 None。它的主要结果是完成若干轮训练和生成侧权重交接；本轮只展开下面第一段，不预填其他阶段已掌握。

<a id="data-handoff"></a>

### 第一段：数据引用从生成侧交给训练侧（51 → 67）

**先观察 67 行的训练调用，51 行说明它的输入来源。** 本段围绕三个问题：传进去的是什么，训练组将工作交给谁，外层等待什么。需要看内部时，只沿 async_train 的直接提交接口展开，再回到当前两行。

真实语句节选。两行之间省略资源卸载与重建分支，并选中 use_critic=False 分支；后一行之后继续到 71 行的完成通知。

```python
rollout_data_ref = ray.get(rollout_manager.generate.remote(rollout_id))
# 当前无 critic，省略其他配置分支。
ray.get(actor_model.async_train(rollout_id, rollout_data_ref))
```

**进入这里时**，上一阶段的 [split_by_dp](../../02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-eight-samples) 会返回按 DP rank 组织的引用列表。沿用 A–H 的结构说明如下；ObjectRef 不是本次真实运行取得的编号。

```text
rollout_data_ref：list
├─ Box.inner → 数据的 ObjectRef → DP rank 0：A、B、E、F 及字段、微批安排
└─ Box.inner → 数据的 ObjectRef → DP rank 1：C、D、G、H 及字段、微批安排
```

- **51 行：接住生成调用的返回值。** generate.remote 提交远程方法；外层 ray.get 等它返回，得到上述 list。里面指向各 rank 数据的引用仍保存在 Box 中。
- **67 行：把同一个列表传给训练组。** 本地 [RayTrainGroup.async_train](/home/hongshi/projects/slime/slime/ray/actor_group.py:148) 为训练 worker 提交 train.remote 调用，返回这些远程训练任务的引用列表。名字含 async，但这个接口是普通 def，当前不是 asyncio 协程调用。
- **67 行的外层 ray.get：等待训练任务结束。** 当前 actor 路径中，单个 worker 任务正常结束后返回 None；本行等待这一组任务完成，但没有保存对应结果列表，而是随后进入 training_completed 通知。怎样完成训练留给 worker，当前先看清交接。

<a id="async-train-submission"></a>

#### 训练组怎样提交任务（actor_group.py:148–166）

`actor_model` 是 driver 中的 `RayTrainGroup` 对象；`self._actor_handlers` 保存它管理的训练 worker 的 Ray 句柄。当前 `external_data=None`，沿下面的普通分支。教学裁剪仅省略 docstring 和 `external_data` 为列表时的分支，保留真实签名与提交语句。

**与前一步接起来**：生成得到的 Sample 先经 BatchBuilder.convert 整理成训练字段，再由 split_by_dp 分配并通过 `Box(ray.put(value))` 交回数据引用。当前默认 worker 实现是 [MegatronTrainRayActor](/home/hongshi/projects/slime/slime/ray/actor_group.py:105)，其 [train 入口](/home/hongshi/projects/slime/slime/backends/megatron_utils/actor.py:400)接收这些引用。因此，眼前的 async_train 属于训练组的提交层；真正取数和训练在 Megatron worker 中。本轮只定位这一层次，不展开训练计算。

```python
def async_train(self, rollout_id, rollout_data_ref, external_data=None):
    # 省略 external_data 为 list 时的分支；本例传入 None。
    return [
        actor.train.remote(rollout_id, rollout_data_ref, external_data=external_data)
        for actor in self._actor_handlers
    ]
```

1. **遍历训练 worker 句柄。** `for actor in self._actor_handlers` 给每个 worker 提交一次本轮训练任务；这里没有遍历或重新切分 Sample。
2. **把本轮编号和数据引用列表作为参数交出去。** 每次调用都传入 `rollout_id` 与整个 `rollout_data_ref`。worker 怎样选取自己所属的 DP 数据属于下一层实现，当前先保留这个接口边界。
3. **收集每次提交返回的任务引用。** `.remote(...)` 提交工作并返回用于取得结果的 ObjectRef。列表推导式收集的是这些新任务引用；训练数据引用继续作为输入被使用。

为看清外层 67 行，可以在教学上将同一句表达式拆成两句；`train_refs` 是说明用变量，原源码没有给中间值命名：

```python
train_refs = actor_model.async_train(rollout_id, rollout_data_ref)
ray.get(train_refs)
```

先提交所有 worker 的本轮训练，再由 `ray.get` 等待。正常 actor 路径中，各任务结果为 `None`；主循环不使用这份结果列表，而是在等待成功返回后接到 71 行。任务失败时可能抛出异常，这里只读正常路径，不据此推断失败后其他任务如何清理。

下面只表示参数和返回值的关系，不是真实执行输出；worker 数量由训练组决定，不根据 DP 数据分片数推算。

```text
rollout_data_ref：各 DP rank 的数据引用列表                 [已有输入]
        │
        ├─ 作为参数 → 训练 worker 0 的 train → 任务引用 0
        ├─ 作为参数 → 训练 worker 1 的 train → 任务引用 1
        └─ ……训练组中的其余 worker……
                                                │
                            async_train 返回任务引用列表   [本次产生]
                                                │
                                   train.py:67 的 ray.get
                                                │ 正常完成后
                                   train.py:71 的完成通知
```

这个方法是普通 `def`：本地方法组织提交，远程 worker 执行训练；方法名中的 `async` 对应提交后返回任务引用的接口行为。本段不引入 asyncio，也不展开 Ray 的调度内部。

| 在这段中出现的引用 | 指向什么 | 本层如何使用 |
| --- | --- | --- |
| rollout_data_ref 内部的数据 ObjectRef | 各 DP rank 的训练数据与安排 | 传给训练组，供训练侧取用 |
| async_train 返回的任务 ObjectRef 列表 | 各训练 worker 的运行结果 | 用 ray.get 等待全部完成 |

前一份列表按 DP rank 组织；后一份列表按训练 worker 组织。一个 DP 副本可能跨多个 worker，所以不能凭本例有两个数据分片就断言只提交两个训练任务。

**这段走完后**：训练调用已经结束，可以继续到 71 行通知生成侧本轮完成。此时还没有走到 89 行的生成侧权重更新。

| 需要回查时进入 | 看清什么后返回 |
| --- | --- |
| [split_by_dp 收尾](../../02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-return-refs) | 看清 Box 包裹的数据引用后，回到 51 行接收这个列表 |
| [async_train 的直接接口](/home/hongshi/projects/slime/slime/ray/actor_group.py:148) | 只核对提交 worker 调用及返回任务引用，回到 67 行的 ray.get |

### 后面的阶段先定位

71 行通知训练完成；88–93 行组织权重交接与是否恢复下一轮；98–99 行按周期评估。完整顺序和裁剪边界放在 [scope](../../01-scope.md#reading-order)，本轮尚未展开这些方法的内部。

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

## 尚不清楚

- 用户是否已分清数据引用与训练任务完成引用，尚待反馈。
- 已将数据引用与 Megatron 训练联系起来；训练组提交层与后端执行层、Sample 与整理后的训练数据的区分，已补充说明，理解待反馈。
- worker 怎样从整个引用列表选取所属 DP 数据，以及怎样执行微批，当前未展开。
- training_completed、权重更新、暂停与恢复接纳、评估的内部行为待按 scope 继续；创建对象、卸载、checkpoint、loss 与优化器仍为边界。
- 尚无真实 Ray、模型或训练运行；图示不能作为实际性能、运行成功或训练结果的证据。

<details>
<summary>来源、验证与完整例子</summary>

- [Step 017 范围确认](../../04-flow.md#step-017-opened) · [首个交接的静态核对](../../04-flow.md#first-reference-handoff)。
- [本轮训练提交带读](../../04-flow.md#async-train-submission-walkthrough)：沿既定范围补充直接接口代码和两类引用的去向。
- [用户复述与 Megatron 层次校准](../../04-flow.md#sample-refs-to-megatron)：数据来路、当前阅读入口与默认后端的关系。
- 固定源码：train.py:13–99；RayTrainGroup.async_train:148–167；RolloutManager.generate:317–333。具体文件哈希见 [源码证据](../source-evidence.json)。
- 数据结构承接 Step 016 的 A–H 例子及本步调取的 split_by_dp 卡。继承与调取记录见 [继承清单](../inheritance-manifest.json)、[调取清单](../active-retrieval.json)。
- [Ray 对象与引用说明](https://docs.ray.io/en/latest/ray-core/objects.html)用于区分远程调用返回、数据引用与读取值；不据文档推断本机安装版本。
- [Ray 官方 actor 方法调用](https://docs.ray.io/en/latest/ray-core/actors.html#calling-the-actor)说明 `.remote()` 返回引用、`ray.get()` 取得结果；2026-10-29 只读核对。示意图与拆开的两行代码没有作为运行实验执行。
- 本轮验证为静态读取源码及链接/继承完整性检查，没有运行 train 或创建虚拟的训练结果。

</details>
