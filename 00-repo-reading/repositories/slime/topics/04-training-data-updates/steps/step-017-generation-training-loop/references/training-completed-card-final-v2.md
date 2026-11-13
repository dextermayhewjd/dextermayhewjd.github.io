# RolloutManager.training_completed · 最终候选（第二版）

> **状态**：已于 2026-10-31 按用户确认合并到[正式函数卡](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md#mental-model)。本文件保留合并前定稿。
>
> **面包屑**：[Step 017](../01-scope.md#completion-notification) → [train.py 的完成通知](../02-short-term-memory/functions/train.py/train.md#training-completion) → **本函数** → [2.3 分层伪代码](#mental-model) → [3 输入输出](#input-output)。

- 源码定位：[slime/ray/rollout.py:430](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L430)；调用方为 train.py:71；固定证据沿用 `18868a79`。
- 首次接触：Step 017，2026-10-29。
- 最近认识更新：2026-10-31，用户再次把完成通知与登记联系起来，但仍询问 controller 是否会在通知后决定停止 rollout。本轮明确 controller 完成数据记账，暂停另由主循环的 88 行发起；此前关于准备、训练、登记三个时点的未知继续保留。
- 本次整理：采用第二版的分层伪代码、同行注释和段后整体说明；保留全部原话、未知与来源。选择表达形式不计为新的技术掌握。

## 1. 定位：本轮训练已结束，接着处理数据侧登记

调用前，train.py:67 的 `ray.get` 已经等本轮训练完成。现在进入第 71 行，通知数据管理侧“这批已经使用完”，并等待这次完成登记处理结束。

本卡只展开完成通知这一条链。后面的暂停新任务接纳、权重同步分别属于主循环的其他调用。

## 2. LLM 整理：使用场合、具体内容与心智模型

### 2.1 使用场合

训练完成后，让数据管理侧更新本轮数据的消费状态，知道哪些批次已处理、哪些仍等待完成登记。

### 2.2 具体内容

RolloutManager 转交 `rollout_id`；BatchBuilder 检查是否有登记批次、轮次是否匹配；有批次时委派 Controller 更新消费进度、移除该批未完成登记并保存状态。没有登记批次时直接结束。

<a id="mental-model"></a>

### 2.3 建议构建的心智模型：分层伪代码

以下是阅读用伪代码，`python` 代码块用于注释高亮。箭头表示调用下潜，自然语言语句概括具体动作；整段不作为可运行程序。

> 训练已结束，通知数据侧处理本轮完成登记；有登记批次时标记已消费并收尾，没有则直接返回。调用方等待这次处理完成，再继续主循环。

<a id="layer-purpose"></a>
<a id="call-and-notification-boundary"></a>

#### 2.3.1 第一层：先看整体职责

```python
# 前提：本轮训练已结束
ray.get(  # 等待这次完成登记处理结束
    rollout_manager.training_completed.remote(rollout_id)  # 发送本轮完成通知
)
```

**这一段完成什么**：训练主循环通知数据侧“这一轮训练已经结束”，并等整个完成登记调用处理完，再继续下面的流程。

<a id="layer-delegation"></a>

#### 2.3.2 第二层：展开通知经过的对象

```python
RolloutManager.training_completed(rollout_id)  # 接收本轮训练完成的通知
  → BatchBuilder.training_completed(rollout_id)  # 转交；下面的 self 指 BatchBuilder
      if self.batch_id is None: return None  # 没有登记批次，直接结束
      if rollout_id != self.rollout_id: raise ValueError(...)  # 轮次不符，报错
      ray.get(  # 等 Controller 真正处理完
          self.controller.finish_batch.remote(self.batch_id)  # 交出要收尾的批次编号
      )
```

**这一段完成什么**：Manager 转交通知，BatchBuilder 确认当前有没有需要登记的批次、轮次是否匹配，然后把具体批次交给 Controller，并等待它处理完成。

[源码：RolloutManager.training_completed](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L430) · [BatchBuilder.training_completed](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/batch_builder.py#L144)。

<a id="layer-state"></a>

#### 2.3.3 第三层：只展开 Controller 的状态变化

```python
RolloutQueueController.finish_batch(batch_id)  # 只处理指定的这一批
    batch = self.batch(batch_id)  # 取得批次登记
    if not batch or not batch["ready"]: 报错  # 批次需存在且准备就绪
    receipt = 该批结果的回执  # 提供结果所在位置 receipt.position
    state = self._training_state()  # 读取消费进度和待完成登记
    self._advance(state, [receipt.position])  # 登记该结果位置已消费
    state["batches"] = 去掉当前 batch 对应的引用  # 例：[A, B] → [B]
    self._save_training_state(state)  # 保存更新后的进度与批次登记
    return None  # 本层处理结束，逐层返回到 train.py:71
```

<a id="controller-whole-logic"></a>

**这一段完成什么**：为这批已经训练完的数据做完成登记。找到该批次及其结果位置，把对应数据记为已消费，从未完成批次列表中移除它的引用，并保存新的状态。这样，数据管理侧就不再把这一批记作“还等训练完成确认”。返回表示本次登记处理结束。

[源码：RolloutQueueController.finish_batch](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/queue_data_source.py#L814)。A、B 是批次引用的示意名称。

**边界**：本次处理的是已训练数据的登记；暂停新任务是主循环第 88 行的另一条调用。

### 2.4 调用代码与返回位置

真实调用已在 2.3.1 展示：`train.py:71` 的外层 `ray.get` 等待通知调用处理完。正常路径返回后，主循环才继续后面的保存、资源管理及权重同步安排。

<a id="input-output"></a>

## 3. 本场景的输入与输出

<a id="completion-id-matching"></a>

### 3.1 输入：哪一轮，以及管理侧已有的批次记录

| 输入或已有状态 | 作用 |
| --- | --- |
| `rollout_id` | 已经训练完成的本轮编号 |
| `BatchBuilder.rollout_id` | 管理侧保存的轮次，用于有批次时核对 |
| `BatchBuilder.batch_id` | 本轮需要收尾的批次编号；也可能为 None |
| Controller 的训练消费状态 | 有批次时，记录消费进度与仍待完成登记的批次引用 |

<a id="implemented-but-not-triggered"></a>

### 3.2 输出：返回 None，按入口状态决定是否更新登记

| 调用前的情况 | 本次结果 |
| --- | --- |
| **原有主例：batch_id=None** | 正常返回 None，不调用 Controller，也不更新批次登记 |
| 有 batch_id，轮次一致，批次存在且 ready | 完成该批消费登记，正常返回 None |
| 有 batch_id，但轮次不符 | 抛出 ValueError，不执行该批完成登记 |
| Controller 找不到批次或批次尚未 ready | 抛出 ValueError，不走正常完成返回 |

<a id="finished-batch-versus-pending-rollout"></a>

**一组具体变化（教学构造，未运行）**：第 7 轮训练完成，通知编号与管理侧保存编号均为 7；batch_id 指向已就绪的 A，原来待完成登记为 `[ref_A, ref_B]`。完成登记后变为 `[ref_B]`，并保存消费进度。其他仍在生成的任务不因这一调用被取消。

<a id="queue-completed-versus-trained"></a>

这里的 ready 指批次准备/转换结果已经就绪；训练完成由调用前的等待保证。消费游标能否连续前移取决于已处理位置，不把它简化为每次加一。

### 3.3 等待与逐层返回

有登记批次时，返回链为 **Controller → BatchBuilder → RolloutManager → train.py:71 的 ray.get**。只有这些调用正常结束后，主循环才执行下一行。无登记批次时从 BatchBuilder 直接返回，不进入 Controller。

## 4. 我的直接表述（原话）

以下完整保留现有正式卡片中的个人表述与当时的助手校准。折叠只调整展示，不改变引文、认识时间或其证据状态。

<details>
<summary>展开全部既有原话与反馈</summary>

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

传入轮次编号的方向已被用户识别；“释放目前还在跑的 queue”仍需按上面的批次容量与运行任务区别校准，不记为已理解。见[本轮完整回顾](../04-flow.md#training-review-and-resume-20261030)。

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

用户已观察到两层转交与条件检查；已训练批次需要收尾的方向正确。停止正在运行的 batch、停止考虑其他未完成 rollout 并非此方法的职责。本轮仅补明这项边界，具体控制器实现继续留白；解释效果待反馈。见[本轮记录](../04-flow.md#finished-batch-versus-pending-rollout-20261030)。

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

用户已接上本批消费登记和正常逐层返回到 train.py:71 的方向。queue task completed 表示批次准备/转换完成，不等同于训练结束或已做消费登记；这项校准尚待反馈。见[本轮记录](../04-flow.md#batch-ready-training-finished-consumed-20261030)。

2026-10-31 用户对通知结束后的动作继续追问（节选）：

> 我是否可以理解为这里只是负责同志
> 但是batch builder这里controller在做什么我不清楚
> 但是这里的同志结束了之后
> controller部分会决定停止rollout什么的对吗?
> 当前的心智模型是不是没有说清楚
> 请具体看一下?

本轮区分当前 Manager 方法的转交职责和整个调用链的效果：下游 controller 在这次通知调用内部完成消费登记，外层 ray.get 会等它结束；停止新任务接纳由主循环随后另一条 pause 调用安排，不是 controller 的后续决策。完整原话及两份材料的 3.2 区分见[本轮记录](../04-flow.md#completion-versus-pause-20261031)。解释尚待反馈。

</details>

## 5. 尚不清楚

采用第二版只确定呈现形式；以下原有未知继续保留，不因合并候选整理而变成已理解。

- 用户已复述消费登记和正常返回链；批次控制任务 completed、模型训练完成与消费登记三个时点的精确区分尚待反馈。
- 完成登记的调用链与暂停新任务的调用链仍需区分；当前已补充明确的 71 行/88 行对照，尚待反馈。
- 本轮已解释释放已训练批次的容量与停止在途生成任务的区别，尚待用户反馈。
- 用户复述的当前批次收尾与其他未完成 rollout 的关系，本轮以 A/B 场景区分，尚待反馈；不要求继续精读 controller。
- 参数 rollout_id、BatchBuilder.self.rollout_id 与 batch_id 的区别已说明，用户的精确理解待反馈。
- 用户明确停止精读 finish_batch 的 lock、receipt 和 state；这些辅助机制保留未知，不影响当前职责层模型。
- 没有运行真实 Ray 通知或训练；当前默认分支的效果来自固定源码判断。

<a id="sources"></a>

## 6. 来源、验证与完整例子

<details>
<summary>展开源码、裁剪边界与历史来源</summary>

- 最终候选保留了第二版的三个模型层次、同行注释及每段后的整体逻辑说明；没有再次嵌入第一版的大图或重复整套实现讲解。
- 第二层把无 batch_id 的隐式正常结束写成显式早返回。第三层的回执读取、过滤表达式用自然语言概括；`return None` 表示原方法的正常隐式返回。关键源码名称保持不变。
- 锁、完整回执读取、具体消费游标算法及可选 GC 未展开；状态变化来自固定源码推导，没有执行真实队列、Ray 或训练。
- [第一版图示与完整源码下潜](training-completed-card-proposal.md) · [第二版原型](training-completed-mental-model-v2.md) · [原正式卡片](../02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager.training_completed.md)。

- [本轮完成通知带读](../04-flow.md#training-completed-reading)。
- [轮次编号的来源与比较](../04-flow.md#completion-id-matching)：第 7 轮例子是固定源码的静态推导，没有新增运行。
- [默认未触发与已有实现的区别](../04-flow.md#implemented-but-not-triggered)：只读核对 controller 入口，未运行该分支。
- 固定源码：train.py:67–71；rollout.py:430–431、545–558；batch_builder.py:32–38、48–57、144–148。具体哈希与范围见 [源码证据](source-evidence.json)。
- 当前分支 batch_id=None 来自初始化和 begin 的正常调用；仅静态核对，没有用构造运行结果替代真实训练，也未执行 controller.finish_batch。

</details>
