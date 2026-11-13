# RolloutManager.training_completed · 阅读版对照稿

这是本轮短期记忆审阅的具体候选，尚未覆盖[现有函数卡](../../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md)。它沿用现有四项说明、输入输出、个人原话、未知和来源栏目；本轮只重新组织阅读顺序。完整评审见[记录](../../../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/step-017-training-completion-memory-review.md)。

- 源码：[RolloutManager.training_completed](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L430)，调用方为 train.py:71；固定证据仍为 `18868a79`。
- 当前本机：[rollout.py:430](/home/fredkeira/projects/slime/slime/ray/rollout.py:430)。当前 checkout `540ea919` 中涉及的三个方法与固定版本相同。
- 首次接触：Step 017，2026-10-29。最近认识及原话沿用现有卡片；排版修改和本轮补充证据不算个人新增理解。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：主循环已经等本轮训练结束，现在通知数据管理侧：这一轮交给训练的数据已经使用完，可以做完成登记。

2. **具体内容**：RolloutManager 转交本轮编号；BatchBuilder 判断是否登记过队列批次，有记录时核对轮次，再让 controller 完成该批次的消费记账。没有批次记录时直接结束。

3. **建议构建的心智模型**：

   > 训练已经完成，这个入口负责通知数据侧收尾。若本轮登记过队列训练批次，就把它从“已交给训练、尚未完成登记”的批次中移除，并保存消费进度；未登记批次则直接返回。
   >
   > 完成的是这一批数据的登记，不是向训练进程发停止命令，也不取消其他还在生成的任务。

4. **调用代码**：两行真实调用节选；第二行外层的 ray.get 等待通知处理完。

   ```python
   ray.get(actor_model.async_train(rollout_id, rollout_data_ref))  # 先等训练结束
   ray.get(rollout_manager.training_completed.remote(rollout_id))  # 再通知数据侧收尾
   ```

## 本场景的输入与输出

输入是**已经训练完成的轮次编号**；正常返回值为 **None**。需要观察的主要结果是数据管理状态，不是函数返回一份训练数据。

### 先分清两种入口状态

| 调用前 | 本次行为 | 正常返回 |
| --- | --- | --- |
| **原有主例：batch_id=None** | 没有登记的队列批次需要收尾，直接结束 | None |
| **机制对照：有 batch_id，通知轮次与保存轮次一致** | 找到该批次，登记已消费，移除其未完成登记，保存状态 | None |

有 batch_id 但轮次不一致时抛错，不进入完成登记。下面只展开第二行，以便看到这个入口的实际用途；这是标明前提的对照场景，不把原有主例改成了实际运行的队列实验。

### 这三层分别负责什么

| 位置 | 只记住这一层的责任 |
| --- | --- |
| RolloutManager.training_completed(rollout_id) | 接收外层的完成通知并转交 |
| BatchBuilder.training_completed(rollout_id) | 判断有没有批次、轮次是否匹配；取出 batch_id |
| RolloutQueueController.finish_batch(batch_id) | 用 batch_id 找到当前批次，更新训练数据的消费状态 |

### 简单下潜：只验证哪份记录发生变化

先认识 `state`：它是**训练数据消费者的进度和未完成批次登记**，不是正在执行的 GPU 任务列表。`state["batches"]` 保存已交给训练、还需完成登记的批次引用。

构造场景：第 7 轮训练已经成功结束，通知编号和 BatchBuilder 保存的编号均为 7；当前 batch_id 指向批次 A，A 已就绪。ref_A、ref_B 仅表示两份真实类型的批次引用，未在本轮构造或执行；下表是源码推导。

| 观察对象 | 调用前 | 成功完成后 |
| --- | --- | --- |
| `state["batches"]` | `[ref_A, ref_B]` | `[ref_B]`；匹配 A 的引用被移除 |
| 消费进度 | 尚未在此次收尾中确认 A 的结果位置 | 将该位置纳入已处理状态，并按连续已处理位置更新进度 |
| 保存的训练数据状态 | 旧状态 | 保存更新后的进度与批次登记 |
| 另一个仍在生成的任务 C | 受生成调度管理 | 本方法没有向 C 提交停止或取消命令 |

取得并验证 A、找到它的结果位置后，实际改变状态的是以下三句（queue_data_source.py:823–825，连续源码节选）：

```python
self._advance(state, [receipt.position])
state["batches"] = [ref for ref in state["batches"] if asdict(ref.manifest) != batch["ready_ref"]]
self._save_training_state(state)
```

- 第一行：登记这一结果位置已被消费；更细的连续进度算法留在 `_advance`。
- 第二行：只保留不匹配当前 A 的批次引用，A 从未完成登记中移除。
- 第三行：保存这份新状态，供后续数据管理使用。

“释放对应队列额度”是消费完成后的管理效果；这三句直接能看到的是**确认消费位置、移除当前登记、保存状态**。它不等于立即删除所有数据文件、释放 GPU 或停止其他 rollout。完整方法还会在启用 online GC 时触发存储回收，未在这个例子中展开。

**本次下潜停止位置**：能把上述三句对应到表中的变化就返回。锁、租约、存储格式、进度算法和 GC 内部按具体问题再查。之后返回 BatchBuilder → RolloutManager → train.py:71 的外层等待，再接主循环下一项。

## 我的直接表述（原话）

以下保留现有卡片的全部个人表述与当时的助手校准。折叠只调整默认展示，不改写原话或将助手结论归为用户理解。

<details>
<summary>展开已有原话与当时反馈</summary>

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

</details>

## 尚不清楚

本轮新增的状态对照尚待用户反馈。前序未知完整保留在下面；此前停止下钻的决定属于历史，本轮只按用户当前请求轻量查看 finish_batch 的状态变化，不扩展其辅助机制。

- 当前“训练完成”与“完成通知”的职责区分，尚待用户反馈。
- 本轮已解释释放已训练批次的容量与停止在途生成任务的区别，尚待用户反馈。
- 用户复述的当前批次收尾与其他未完成 rollout 的关系，本轮以 A/B 场景区分，尚待反馈；不要求继续精读 controller。
- 参数 rollout_id、BatchBuilder.self.rollout_id 与 batch_id 的区别已说明，用户的精确理解待反馈。
- 用户明确停止精读 finish_batch 的 lock、receipt 和 state；这些辅助机制保留未知，不影响当前职责层模型。
- 没有运行真实 Ray 通知或训练；当前默认分支的效果来自固定源码判断。

<details>
<summary>来源、验证与完整例子</summary>

- 新增核对：固定版本的 [finish_batch:814](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/queue_data_source.py#L814)、`_training_state:713`、`_advance:730`、`_save_training_state:751`。后面三个只核对 state 的含义、进度与保存职责，没有扩展为逐行阅读。
- A/B/C 表是状态关系的教学构造，未运行真实 Ray、训练、队列或存储回收；消费进度不保证每次都能连续前移。
- 此稿重排前的正式卡片仍保留，个人最近认识时间与历史版本不因整理改变。

- [本轮完成通知带读](../../04-flow.md#training-completed-reading)。
- [轮次编号的来源与比较](../../04-flow.md#completion-id-matching)：第 7 轮例子是固定源码的静态推导，没有新增运行。
- [默认未触发与已有实现的区别](../../04-flow.md#implemented-but-not-triggered)：只读核对 controller 入口，未运行该分支。
- 固定源码：train.py:67–71；rollout.py:430–431、545–558；batch_builder.py:32–38、48–57、144–148。具体哈希与范围见 [源码证据](../source-evidence.json)。
- 当前分支 batch_id=None 来自初始化和 begin 的正常调用；仅静态核对，没有用构造运行结果替代真实训练，也未执行 controller.finish_batch。

</details>
