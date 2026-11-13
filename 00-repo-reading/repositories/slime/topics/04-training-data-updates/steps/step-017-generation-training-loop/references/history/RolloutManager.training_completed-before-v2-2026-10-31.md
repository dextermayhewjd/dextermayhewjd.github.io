# RolloutManager.training_completed

- 源码定位：[slime/ray/rollout.py:430](/home/hongshi/projects/slime/slime/ray/rollout.py:430)，固定版本 `18868a79`；调用方为 [train.py:71](/home/hongshi/projects/slime/train.py:71)。
- 首次接触：Step 017，2026-10-29。
- 最近认识更新：2026-10-31，用户再次把完成通知与登记联系起来，但仍询问 controller 是否会在通知后决定停止 rollout。本轮明确 controller 完成数据记账，暂停另由主循环的 88 行发起；此前关于准备、训练、登记三个时点的未知继续保留。
- 导航：[scope 的②](../../01-scope.md#completion-notification) → **本卡：完成通知** → [返回 train 父卡](../../02-short-term-memory/functions/train.py/train.md#training-completion)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：主循环已经在 67 行等待本轮训练成功结束，现在把本轮编号交回生成侧管理器，执行训练后的批次收尾。

2. **具体内容**：转交 `rollout_id` 给 `self.batch_builder.training_completed`。下游只有在存在 batch_id 时才校验轮次并调用 controller.finish_batch；当前默认 object-store 正常路径没有这个批次记录，直接结束。

3. **建议构建的心智模型**：

   > 本轮训练已结束，主循环通过这个入口让数据管理侧完成“这批数据已用过”的登记。
   >
   > RolloutManager 转交轮次编号；BatchBuilder 有登记批次时核对轮次，交给 controller 更新消费进度、移除该批未完成登记并保存。没有登记批次时直接返回。
   >
   > 外层 ray.get 等这次处理完成后继续主循环。controller 不决定停止生成；后续暂停新任务，是主循环另外调用 pause_rollout_admission 的动作。

   [用三层图读这个模型](../training-completed-card-proposal.md#progressive-mental-model)：先看“训练已完成 → 数据侧登记”，再打开 Manager / BatchBuilder / Controller，最后看当前批次从待完成登记中移除。图是同一调用的逐层展开，不是三次不同操作。

   [第二版：用伪代码与同行注释表达相同三层](../training-completed-mental-model-v2.md#layer-purpose)，保留职责、分支与状态变化，每句作用紧贴代码。

4. **调用代码**（train.py:67、71，省略无关空行和注释）：

   ```python
   ray.get(actor_model.async_train(rollout_id, rollout_data_ref))
   ray.get(rollout_manager.training_completed.remote(rollout_id))
   ```

## 本场景的输入与输出

<a id="call-and-notification-boundary"></a>

### 先看调用方这一行做什么

本卡解释 train.py:71 的完成登记；[暂停卡的 3.2](../../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.pause_rollout_admission.md#pause-worker)解释 train.py:88 的后台接纳控制。两条调用链的并排对照见 [train 父卡](../../02-short-term-memory/functions/train.py/train.md#completion-versus-admission-pause)。

`ray.get(rollout_manager.training_completed.remote(rollout_id))` 包含两层：remote 将本轮编号交给管理器，通知它“训练已经完成”；外层 ray.get 等这次通知处理完。上一行已经等待训练结束，所以本方法处理的是数据侧收尾，不负责探测训练进度。

教学上把这一行拆开，notification_ref 是说明用变量，原源码没有单独命名：

```python
notification_ref = rollout_manager.training_completed.remote(rollout_id)  # 提交本轮完成通知
ray.get(notification_ref)  # 等管理器处理完通知，再执行下一行
```

当前已有独立函数卡，回顾只需读下面的管理器转交与 BatchBuilder 条件分支；不新建 Step，不把 controller 的锁、状态存储和清理实现作为本次必读。没有批次记录时也会完成这次调用，正常返回 None。

沿用本步 use_critic=False、默认 object-store、无恢复分支的正常路径。输入是刚训练完成的外层 rollout_id，管理器持有 BatchBuilder；本例 BatchBuilder.batch_id=None。

**输出**：方法正常返回 None；调用方的 ray.get 等待这次通知处理完。在当前分支中，没有批次状态更新，也不调用 finish_batch。

### 管理器转交通知（rollout.py:430–431）

```python
def training_completed(self, rollout_id):
    self.batch_builder.training_completed(rollout_id)
```

这里没有重新提交训练。实际批次收尾判断由 BatchBuilder 完成，下面只回查这一层。

### BatchBuilder 判断是否有批次要收尾（batch_builder.py:144–148）

```python
def training_completed(self, rollout_id):
    if self.batch_id is not None:
        if rollout_id != self.rollout_id:
            raise ValueError("Training completion does not match the current batch")
        ray.get(self.controller.finish_batch.remote(self.batch_id))
```

<a id="finished-batch-versus-pending-rollout"></a>

**两个同名方法属于不同对象。** RolloutManager 提供外层可远程调用的入口，BatchBuilder 根据自己记录的当前批次和轮次决定是否交给 controller；这是逐层转交通知，不是完成回调。传给最后一层的参数是 batch_id，rollout_id 用于前面的轮次核对。

**这里确认已经完成的训练批次，不负责终止其他生成任务。** 外层已经等本轮训练调用完成，才来到此处。有对应记录时，finish_batch 处理该批次的消费状态和未完成登记、释放相关额度；不能将它理解为向正在运行的 batch 发停止命令，也不能从本轮训练完成推断所有 rollout 任务均已完成。

用一个仅说明边界的构造场景：训练批次 A 已用完，另一个 rollout 任务 B 仍在生成。此处完成 A 的登记；B 继续受原来的生成调度、暂停或取消机制管理，不因 finish_batch(A) 而被取消。本例只适用于有批次记录的分支；当前默认 batch_id=None 的主例仍直接返回。

<a id="queue-completed-versus-trained"></a>

**queue task 的 completed 与模型训练结束是不同的时点。** `batch()` 的 task_status 查询的是批次准备/转换这个控制任务；它完成并有结果回执，才表示批次 `ready`。模型训练是否结束，由上层 train.py:67 的 `ray.get(async_train(...))` 保证。随后到 71 行发出完成通知，finish_batch 才将这批数据登记为已被训练消费。因此，不是从 task_status 的 completed 推断训练完成，而是收到训练完成通知后，核对批次并更新消费记录。正常逐层返回后，train.py:71 的外层 ray.get 结束。

<a id="completion-id-matching"></a>

### 两个 rollout_id 从哪里来，比较的是谁

上面的 self 属于 **BatchBuilder 对象**。传入参数 rollout_id 表示调用方通知“哪一轮训练完成了”；self.rollout_id 是这个对象此前保存的当前轮次。后者在 [RolloutManager.generate:319–320](/home/hongshi/projects/slime/slime/ray/rollout.py:319) 中设置：

```python
self.rollout_id = rollout_id                # 管理器记录当前生成轮次
self.batch_builder.rollout_id = rollout_id  # BatchBuilder 同时记录该轮次
```

假设正在生成第 7 轮：生成时保存 self.batch_builder.rollout_id=7；同一轮训练结束后，主循环把 7 交给 training_completed。进入 BatchBuilder 后，比较的就是传入的 7 与对象保存的 7。

| 名字 | 用途 |
| --- | --- |
| rollout_id 参数 | 这次通知声称完成了哪一轮 |
| BatchBuilder.self.rollout_id | 管理侧当前记录的是哪一轮 |
| BatchBuilder.self.batch_id | 要提交给 finish_batch 收尾的批次记录编号 |

**只有 batch_id 不为 None 才做编号比较。** 在这一前提下，通知 7、记录 7 时继续完成该批次；通知 6、记录 7 时抛错，避免把另一轮的完成消息算到当前批次。这个检查核对的是轮次，不是本机/远端机器身份或 GPU 编号。

rollout_id 用于防止完成通知对应错轮；真正传给 finish_batch 的是 self.batch_id，用它定位要收尾的批次记录。

| 进入时的状态 | 本次行为 | 返回 |
| --- | --- | --- |
| **batch_id=None，当前路径** | 最外层 if 条件不成立，不进行编号比较，走到函数末尾 | None |
| 存在 batch_id | 先核对 rollout_id；一致时通知 controller 完成该批次 | 成功时 None；轮次不符时抛错 |

当前为何没有 batch_id：默认 object-store 正常生成不设置持久化 raw_ref；[BatchBuilder.begin:48–53](/home/hongshi/projects/slime/slime/data/batch_builder.py:48) 在 raw_ref=None 时将 batch_id 清为 None。这里回查其结论，不展开持久化批次实现。

存在批次时，finish_batch 用于运行时完成登记和相关队列容量释放；train.py:69–70 的注释明确区分它与模型/优化器及数据进度的联合持久化 checkpoint。保存 checkpoint 位于后面的独立分支；生成侧权重更新则在 89 行。

**2026-10-30 回顾：“释放”针对已训练批次占用的容量。** 外层已经等训练结束，才用 rollout_id 通知“这一轮用完了”。有批次记录时，数据管理侧将对应批次从未完成记录中移除并更新消费状态，让它不再占着未完成批次的额度；这里没有向正在运行的生成任务发出停止或取消命令，也没有销毁整条 queue。当前默认 batch_id=None 路径仍直接返回，不实际执行该队列分支。

<a id="implemented-but-not-triggered"></a>

**已实现与当前未触发要分开。** 为核对是否只是占位，本轮只查看了 [RolloutQueueController.finish_batch:814–827](/home/hongshi/projects/slime/slime/data/queue_data_source.py:814) 的短入口：它检查批次已就绪，推进消费记录，从 state["batches"] 移除该批次并保存状态。实现存在于队列数据路径；当前默认路径的 batch_id=None，因此不会调用它。

**“从未完成批次列表移除并保存”的直接依据是 824–825 行：**

```python
state["batches"] = [ref for ref in state["batches"] if asdict(ref.manifest) != batch["ready_ref"]]
self._save_training_state(state)
```

第一行仅保留 manifest 不等于当前 batch ready_ref 的项，因此当前批次从这份训练管理列表中移除；第二行保存修改后的训练状态。815 行的 docstring 也说明只保留未完成批次。这里描述的是管理记录，不据此推断样本文件被立即删除。

按当前“简单建立心智模型”的目标，知道上述入口职责即可。_advance、状态持久化与存储回收等辅助机制没有继续精读，也没有为其开启新步骤；需要研究队列消费进度或恢复时再进入。

### 读完返回哪里

回到 train.py:71，等待通知成功返回后继续后续编排。下一处阅读是 88–93 行的暂停接纳、更新权重与按条件恢复；资源卸载、checkpoint 和传输内部继续按本步边界折叠。

## 我的直接表述（原话）

用户承接上一函数并要求继续：

> 好的 我现在大概理解这里的async train了 让我们继续吧

这是对上一函数的总体理解反馈与继续指令，尚无对当前 training_completed 的直接表述。

用户随后对完成通知中的编号提出理解：

> 好的
> 那么我们看一下下一个部分吧
> 之前看的是ray actor model async train对吧
> 那么后续的内容是什么呢？
> 后续是这里的rollout manager training completed remote id
> 也就是这里的rollout部分的代码
> 这里是给一个rollout id
> 这里具体的代码是在做什么呢？
>
> 根据这里的rollout id来判断这里是否和本地的是一个？
> 我没有特别理解这里的内容了

用户已观察到编号比较。助手补充比较对象的来源、batch_id 对检查的前置条件，以及 rollout_id 校验与 batch_id 定位收尾记录的不同用途；这些精确关系尚待反馈。

用户要求收敛为简单心智模型：

> 也就是在判断当前是在哪一个轮次？
> 那么之后呢？
> 我没有特别理解 我目前只是希望简单的构建一下这里的心智模型

助手据此用“训练已用完这批数据 → 通知数据管理侧收尾”概括职责，并说明轮次检查只是防止确认错批次；默认无批次记录时直接返回。该简化模型尚待反馈，不再展开 controller 内部。

用户继续要求明确当前应保留的模型：

> 所以这里根据我们目前看到的内容 应该保留怎样的心智模型呢？
> 我不是特别理解
> 因为你说的当前的代码好像还没有实现？
> 我们需要继续读这里的的controller 的finish batch吗？

本轮校准的是“代码已实现，但当前默认分支不触发”。助手只核对 finish_batch 的短入口职责，不将整套队列实现加入精读范围；该模型效果待后续反馈。

用户最终选择保留职责层理解，停止下钻：

> 要不还是简单读一下？
> 这里就是访问了training lock 我简单猜测一下是在这个lock里面拿到当前batch的id
> 同时考虑是否ready了
> 如果ready了
> 就拿到这个具体的tsk
> 并且得到这里的result的receipt？
> state什么呢
>
> 算了还是不继续精读了吧
> 我需要了解的是 他就是知道这批数据完成了然后修改这里的运行状态？ 知道他负责的这一批数据完成了？

本轮只核对其职责表述：训练方已等本轮训练结束，再通知 finish_batch 更新相应批次的管理记录，使它不再列在未完成批次中。它不是在内部探测 GPU 的训练进度。lock、receipt、state 的前述猜测不写为已掌握知识，遵守用户停止精读的决定。

用户要求结论的源码依据，并暂按这一职责继续主线：

> 具体效果是：把这批从“未完成批次”列表中移除，并保存更新后的状态。 这是从哪里知道的呢？
> （好的 我现在先假设这里的更新状态完成了
> 那么然后我们应该如何考虑下一步呢？

助手补出 824–825 行的直接依据，并推荐下一处权重交接。用户表达的是暂按职责继续，不是完整掌握 controller 内部。

2026-10-30 用户回顾（节选）：

> 之后这里的rollout manager training completed remote的部分获得的内容是这里的rollout id
> 应该标志的内容是释放这里的目前还在跑的queue
> 是我的理解

传入轮次编号的方向已被用户识别；“释放目前还在跑的 queue”仍需按上面的批次容量与运行任务区别校准，不记为已理解。见[本轮完整回顾](../../04-flow.md#training-review-and-resume-20261030)。

2026-10-30 用户复述与边界疑问（完整原文）：

> 这里看到写的是batch builder 的 training completed
> 然后这里又回调到batchbuilder的ray get controller finish batch?
> 如果有这个batch 并且这个rollout id是这个rollout id的话
> 那么这里就让controller 停掉这里的batch是我对于这里的理解
>
> 但为什么这俩的我在点击rolloutmanager 的training completion
> 我不升入看这内容
> 但是我大概理解是
> 如果完成了训练
> 那么目前登记的训练内容就应该释放了对吗?
> 也就是不应该再考虑继续还没有完成的rollout侧的任务?
> 是我的理解

用户已观察到两层转交与条件检查；已训练批次需要收尾的方向正确。停止正在运行的 batch、停止考虑其他未完成 rollout 并非此方法的职责。本轮仅补明这项边界，具体控制器实现继续留白；解释效果待反馈。见[本轮记录](../../04-flow.md#finished-batch-versus-pending-rollout-20261030)。

2026-10-30 用户对消费登记与返回链的复述：

> 好的 我大概理解了 也就是这里的的batch 是在通过一个queue task status的部分来确定
> 这里的task 已经完成了
> 确认数据已经被消费了
> 所以就可以吧使用的数据做一个标记 确定一下这一部分的内容已经被消费了
> 我可以这么理解吗?
> 这里并没涉及别的内容
> 那么返还到上面一层 training completed 也是为了 让这里登记一下这一部分数据使用过了
> 以及回到最上方
> 这里告诉这里的batch builder 这里的训练内容训练结束了
> 那么也就是train的71步这里结束了对吗?

用户已接上本批消费登记和正常逐层返回到 train.py:71 的方向。queue task completed 表示批次准备/转换完成，不等同于训练结束或已做消费登记；这项校准尚待反馈。见[本轮记录](../../04-flow.md#batch-ready-training-finished-consumed-20261030)。

2026-10-31 用户对通知结束后的动作继续追问（节选）：

> 我是否可以理解为这里只是负责同志
> 但是batch builder这里controller在做什么我不清楚
> 但是这里的同志结束了之后
> controller部分会决定停止rollout什么的对吗?
> 当前的心智模型是不是没有说清楚
> 请具体看一下?

本轮区分当前 Manager 方法的转交职责和整个调用链的效果：下游 controller 在这次通知调用内部完成消费登记，外层 ray.get 会等它结束；停止新任务接纳由主循环随后另一条 pause 调用安排，不是 controller 的后续决策。完整原话及两份材料的 3.2 区分见[本轮记录](../../04-flow.md#completion-versus-pause-20261031)。解释尚待反馈。

## 尚不清楚

- 用户已复述消费登记和正常返回链；批次控制任务 completed、模型训练完成与消费登记三个时点的精确区分尚待反馈。
- 完成登记的调用链与暂停新任务的调用链仍需区分；当前已补充明确的 71 行/88 行对照，尚待反馈。
- 本轮已解释释放已训练批次的容量与停止在途生成任务的区别，尚待用户反馈。
- 用户复述的当前批次收尾与其他未完成 rollout 的关系，本轮以 A/B 场景区分，尚待反馈；不要求继续精读 controller。
- 参数 rollout_id、BatchBuilder.self.rollout_id 与 batch_id 的区别已说明，用户的精确理解待反馈。
- 用户明确停止精读 finish_batch 的 lock、receipt 和 state；这些辅助机制保留未知，不影响当前职责层模型。
- 没有运行真实 Ray 通知或训练；当前默认分支的效果来自固定源码判断。

<details>
<summary>来源、验证与完整例子</summary>

- [本轮完成通知带读](../../04-flow.md#training-completed-reading)。
- [轮次编号的来源与比较](../../04-flow.md#completion-id-matching)：第 7 轮例子是固定源码的静态推导，没有新增运行。
- [默认未触发与已有实现的区别](../../04-flow.md#implemented-but-not-triggered)：只读核对 controller 入口，未运行该分支。
- 固定源码：train.py:67–71；rollout.py:430–431、545–558；batch_builder.py:32–38、48–57、144–148。具体哈希与范围见 [源码证据](../source-evidence.json)。
- 当前分支 batch_id=None 来自初始化和 begin 的正常调用；仅静态核对，没有用构造运行结果替代真实训练，也未执行 controller.finish_batch。

</details>
