# RayTrainGroup.update_weights

> **采用格式**：参照已采用的 training_completed 和 pause_rollout_admission，使用分层伪代码、同行注释和段后整体说明。
>
> **面包屑**：[Step 017](../../../../../01-scope.md#weight-handoff) → [train.py:89](../../../train.py/train.md#weight-handoff) → **本函数** → [2.3 分层心智模型](#mental-model) → [3 输入输出](#input-output)。

- 源码定位：[slime/ray/actor_group.py:178](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/actor_group.py#L178)，调用方为 train.py:89；固定证据沿用 `18868a79`。
- 当前本机：[actor_group.py:178](/home/fredkeira/projects/slime/slime/ray/actor_group.py:178)，checkout 为 `540ea919`；本轮涉及的方法与固定证据一致。
- 首次接触：Step 017，2026-10-29。
- 最近认识更新：2026-10-31，用户明确概括为 Megatron 将自身训练后的权重同步给生成侧。发送端、接收端与主要职责已有表述；本轮补充内部等待、正常返回及恢复属于外层，精确接口边界待反馈。
- 本次整理：2026-10-31 按用户要求对齐既有卡片格式，不增加个人已掌握结论。

<a id="training-finished-before-sync"></a>

## 1. 定位：训练已结束，现在把新权重交给生成侧

主循环在 67 行等本轮训练结束，在 71 行处理数据完成登记，再在 88 行暂停后台新任务接纳。现在执行 89 行的 `actor_model.update_weights()`，将训练结果发布给生成侧。

本卡主例是直接同步的正常路径（例如 full + nccl）：训练 worker 和可更新的生成引擎已准备好，不走 debug 跳过或无引擎早返回。全量磁盘发布在 3.3 作为既有对照保留，具体传输实现按需回查。

## 2. LLM 整理：使用场合、具体内容与心智模型

### 2.1 使用场合

训练侧已经得到本轮的新参数，生成侧需要接收这些参数，后续生成才能使用本轮训练结果。

### 2.2 具体内容

训练组遍历自己持有的训练 worker 句柄，提交每个 worker 的 update_weights 远程调用，并在本方法内部用 ray.get 等待。worker 通过已配置的 weight_updater 发布参数，生成引擎是接收方。

<a id="mental-model"></a>

### 2.3 建议构建的心智模型：分层伪代码

> 训练组组织各个训练 worker，把已经算好的新权重同步给生成侧，并等待本轮发布完成。
>
> 训练参数的学习更新在前面的 async_train 中完成；本函数负责发布已有训练结果。正常返回 None 后，主循环才继续判断是否恢复新任务接纳。

下文为阅读用伪代码，python 代码块用于注释高亮。省略号折叠未展开的分支；保留真实方法名与等待位置，不作为独立可运行程序。

#### 2.3.1 第一层：主循环调用同步入口

```python
# 前提：本轮训练已完成，新增 rollout 接纳已暂停
actor_model.update_weights()  # 将训练结果交给生成侧；方法内部会等待
# 正常返回后，再进入第 92–93 行的恢复判断
```

**这一段完成什么**：主循环在这里完成一次权重发布交接。调用处没有另包 ray.get，是因为等待已经放在训练组方法内部。

<a id="worker-update-submission"></a>

#### 2.3.2 第二层：训练组提交各 worker 的更新调用，并等待

```python
RayTrainGroup.update_weights()  # self 是本地的训练组对象
    if not self._full_disk_weight_update_enabled():  # 主例走这一支
        ray.get([  # 等待所有 worker 的更新调用正常完成
            actor.update_weights.remote()  # 给一个训练 worker 提交发布工作
            for actor in self._actor_handlers  # 遍历训练 worker 的句柄
        ])
        return None  # 主例到此结束；原源码这里写 return
    ...  # 全量磁盘分支另见 3.3，不会与上面的返回路径接着执行
```

**这一段完成什么**：将一次组级更新请求分发给各训练 worker，再用结果引用等待它们完成。这里没有重新切分样本，也没有重新运行训练。

<a id="training-worker-versus-rollout-engine"></a>

#### 2.3.3 第三层：训练 worker 通过 updater 把参数提供给生成侧

```python
MegatronTrainRayActor.update_weights()  # 在远端的训练 worker 中执行
    ...  # 获取生成引擎，按需连接并准备资源；本例假定均已就绪
    self.weight_updater.update_weights()  # 将已有新参数发布给生成侧
    ...  # 按配置收尾资源，不在此处展开
    return None  # 此 worker 的调用结束；原方法为隐式返回
```

**这一段完成什么**：训练 worker 持有训练后的参数，由已有 updater 完成具体发布；本例中生成引擎接收并使用新权重。训练组的 ray.get 等待这些调用返回后，本函数才返回主循环。这里仅定位 updater 的职责，不把全部 backend 变为新的必读内容。

| 这里的名字 | 指向谁 |
| --- | --- |
| actor_model / self（第二层） | 组织训练 worker 的 RayTrainGroup |
| actor / self（第三层） | 持有新权重、执行发布工作的训练 worker |
| rollout_engines | 接收新权重的生成引擎 |

<a id="worker-handoff-next-reading"></a>

### 2.4 调用代码与返回位置

调用方是 train.py:89。主例成功返回后，回到 92–93 行：还有下一轮时调用恢复接口，再由先前的 was_paused 决定是否真正恢复。

本函数不改变调用方的 was_paused，也不负责恢复接纳。已有暂停确认并不证明全部在途生成已结束，安装权重时怎样处理在途请求仍属于具体 updater 的机制边界。

<a id="input-output"></a>

## 3. 本场景的输入与输出

### 3.1 输入与输出：已有模型参数，不是训练数据引用

- **输入**：没有显式业务参数；训练组持有 worker 句柄和发布配置，worker 已持有训练后的模型参数。
- **正常输出**：None。主例返回前已等待各 worker 的更新调用结束。
- **主要副作用**：在上述可更新引擎存在、正常同步的前提下，生成侧安装本轮新权重。
- **失败边界**：远程调用失败可能使 ray.get 抛错；不能把异常返回当作所有引擎均已更新，也不能据此推断其他调用已取消。

<a id="training-copy-to-generation-copy"></a>
<a id="training-versus-weight-sync"></a>

### 3.2 用同一个例子区分训练与发布

v0/v1 是教学标记，表示训练前后两份参数，未运行真实模型：

| 时点 | 训练侧 | 生成侧 |
| --- | --- | --- |
| async_train 之前 | v0 | v0 |
| 本轮训练完成，尚未发布 | 已得到 v1 | 尚未因训练计算而自动得到 v1 |
| 本例 update_weights 正常完成 | 持有 v1 | 已接收 v1，供后续生成使用 |

| 接口 | 向调用者返回什么 | 谁等待远程工作 |
| --- | --- | --- |
| async_train | 训练调用的结果引用列表 | train.py 外层的 ray.get |
| update_weights（本例） | None | update_weights 内部的 ray.get |

<a id="full-disk-branch-review"></a>

### 3.3 按需对照：全量磁盘发布是另一条分支

<details>
<summary>展开已有磁盘分支：版本、写入、可选释放、加载</summary>

只有 role=actor、update_weight_mode=full、update_weight_transport=disk 同时成立才进入这里。上面的主例在 return 处已经结束，不会再顺序执行这个分支。

```python
weight_version = self._disk_weight_version + 1  # 计算下一次发布的版本
# 对应目录为 weight_v000001 等；这里还没有写出文件
disk_weight_dir = Path(self.args.update_weight_disk_dir) / f"weight_v{weight_version:06d}"
ray.get([actor.update_weights.remote() for actor in self._actor_handlers])  # 等各 rank 写好权重
self._disk_weight_version = weight_version  # 保存训练组侧的发布版本
if self._release_train_enabled():
    self.release()  # 按配置终止训练 worker 并释放其资源
self._reload_rollout_weights_from_disk(disk_weight_dir, str(weight_version))  # 让生成侧加载
```

**这一段完成什么**：通过磁盘文件交接权重。这里 worker 的 updater 负责写文件，训练组等写完之后再组织生成引擎加载；与主例中 worker 直接完成同步的边界不同。release 是训练 worker 的资源释放，不是恢复生成接纳；reload 会实际调用引擎加载文件，不只是修改路径。

无可更新引擎等情况有自己的返回分支，具体加载、缓存、文件拉取和回收协议继续留白。

</details>

## 4. 我的直接表述（原话）

2026-10-31 用户对同步职责的复述：

> 好的 我的理解就是
> 这里让megatron的部分开始将自身的权充同步给生成侧是我的理解
> 也就是这一步在做什么
> 还iyoushenme是我需要了解的吗?

这段已正确连接训练侧发送权重与生成侧接收。当前正常路径还需保留两个接口事实：本方法内部等待各 worker 的同步调用完成，正常返回 None；恢复新任务接纳由外层 train 随后判断。本轮提醒不表示这些细节已经逐项确认。见[本轮记录](../../../../../../step-017-generation-training-loop/04-flow.md#weight-sync-purpose-understanding-20261031)。

本轮用户要求：

> 能否按照之前处理其他function的格式来看一下这里的update weight

这次要求确定的是记录形式，未新增对内部机制的理解结论。已有原话与当时校准完整保留：

<details>
<summary>展开已有个人表述与反馈</summary>

用户指出真实执行顺序，并询问精读重点：

> 然后下一步不是这里的paused吗？
> 虽然应该也很好理解
> 就是原有的rollout部分不再接受新的请求应该是这个意思对吧
> actor model 更新权重我们先看这一步吗？

其中暂停新接纳的理解由用户提出；具体暂停粒度、was_paused 的含义及权重更新内部等待由助手补充，尚待反馈。

用户对当前动作的初步理解：

> 我的简单理解就是 现在所有的actor都开始更新当前的权重我可以这么理解吗？

其中“所有 actor”按源码限定为当前训练组 self._actor_handlers 中的训练 worker。这里的更新是发布/同步已有的训练后权重，让生成侧使用新参数；参数的训练更新已在前一阶段完成。列表推导式提交每个 worker 的更新调用，外层 ray.get 等它们结束。该校准不等于用户已确认全部同步细节。

用户对训练结束与同步时序的追问：

> 好的 那么继续吧
> 这里是在当前已经有的rollout侧用上了这些新的参数
> 是训练侧和rollout侧都停下来吗？
> 还是训练侧已经更新完整了权重
> 现在只需要actor这里同步权重就可以了？

助手按 train.py 的实际先后关系回应：本轮训练计算先完成，随后进入同步；训练进程参与同步而不启动下一轮训练，rollout 暂停新接纳。具体在途生成如何处理没有据此推断或标记为理解。

用户要求保存上述解释并考虑下一步：

> 记得把这里的内容写清楚放在这个函数卡片里面吧
> 然后考虑下一步

本次将两侧状态整理为对照表，并明确下一观察点是恢复条件。保存说明和提出下一入口不表示用户已确认全部时序或恢复机制。

2026-10-30 用户的明确反馈（消息末段原文）：

> 然后这里的是下面的更新权重
> 但是这里我其实没有太过于看懂
> 或者说你说的恢复rollout接纳这里 其实我也没有特别理解

本轮据此回看更新目的与“接纳”的具体对象，不直接推进周期评估。上面新增的两侧参数说明是助手讲解，理解状态待用户反馈。见[本轮完整回顾](../../../../../04-flow.md#training-review-and-resume-20261030)。

2026-10-30 用户回答 actor 身份并对照磁盘分支（采用中断后重新发送的完整版本，不重复收录前一稿）：

> 这里肯定是rollout侧的生成引擎啊
> 因为train的部分已经更新完整了
> 只需要吧actor部分的权重 更新更新完整就可以了
> 但是我们也可以看到这里的还有一个更新权重版本的内容
>
> 更新完整了之后这里就开始释放 是否可以训练了
> 同时吧reload可以reload的版本在磁盘中的位置 更新一下 是我对于这里的update weights的理解

用户已把动作目的联系到生成侧新权重，并观察到磁盘分支的版本和目录；循环对象、释放对象及 reload 的实际动作仍需按上文校准。原话不改写为正确结论，校准效果等待后续反馈。见[本轮形成过程](../../../../../04-flow.md#training-worker-and-disk-review-20261030)。

2026-10-30 用户进一步追问（完整原文）：

> 我其实有点没动
> 这里的更新权重是rollout部分的数据已经足够的情况下更新的是actor部分的权重?
> 但是上面的actor model async train不是已经是在训练的部分了吗?
> 我的理解是需要训练完了之后才会考虑更新这里的权重啊?

用户已经提出“训练完再调用后续权重更新”的执行顺序；训练侧参数已在训练中改变、后续更新指生成侧接收这份参数，是本轮助手补充的关系，尚待反馈。见[本轮讨论](../../../../../04-flow.md#train-versus-weight-sync-20261030)。

2026-10-30 用户纠正更新目标（完整原文）：

> 对岸 那么你为什么说这里的update weights 还是在更新训练侧的权重呢?
> 我觉得这里的actor update weights 应该是生成侧的权重才对吧

用户对“更新目标是生成侧”的判断正确。此前助手反复强调循环中的 actor 是训练 worker，没有足够突出其执行的是向生成侧发布权重的工作，导致执行者与更新对象仍混淆。本轮明确：训练侧持有新参数并发起同步，生成侧接收并使用它们；这不是再次执行训练。变量 actor 的身份是否已区分，仍等待用户反馈。见[本轮纠正](../../../../../04-flow.md#weight-update-executor-versus-target-20261030)。

</details>

## 5. 尚不清楚

本轮已复述 Megatron 将训练后参数同步给生成侧的主要职责。当前待核对或尚未展开的是：

- 内部 ray.get 的完成等待、正常返回 None，以及恢复由外层判断的接口边界，本轮已提醒，待反馈。
- 具体权重传输、引擎安装时怎样处理在途请求、异常与部分失败，未展开。
- 全量磁盘配置、文件写入与加载细节，保留为按需回查。
- 没有运行真实权重更新、生成或训练。

<details>
<summary>之前的疑问记录</summary>

下列是本轮职责复述前的记录，保留其形成过程；不再据此把用户已说清的发送方向标为不理解。

- 用户明确表示权重更新和恢复接纳未理解；本轮补充两侧参数与新任务接纳的说明，尚待反馈。
- 用户已明确指出 update_weights 的更新目标是生成侧；执行此方法的 actor 句柄仍属于训练 worker，这项身份区别尚待反馈。
- weight_updater 的权重传输、引擎同步和在途生成收束方式未展开。
- 循环中的训练 worker 与权重接收方 rollout 引擎的身份区分，本轮已提供创建处证据，尚待用户反馈。
- 全量磁盘分支已按本轮问题作职责对照；release 终止训练 worker 与恢复接纳不同，reload 真正加载文件而非仅改路径，这两项校准尚待反馈。写文件、缓存和传输内部未精读。
- 没有运行真实权重更新、生成或训练。

</details>

## 6. 来源、验证与完整例子

<details>
<summary>展开源码定位、裁剪边界与历史来源</summary>

- 主函数 RayTrainGroup.update_weights:178–190；worker 的 MegatronTrainRayActor.update_weights:629–684。第三层只定位获取引擎、连接、委派 updater 与资源收尾，不展开传输算法。
- _full_disk_weight_update_enabled:241–246 决定组级分支；release:198–203 终止训练 worker；_reload_rollout_weights_from_disk:248–295 组织生成引擎加载。
- 磁盘写入由 UpdateWeightFromDisk.update_weights:66–96 执行；本卡保持写入和生成侧加载是两个阶段的区别。
- [本轮格式整理](../../../../../../step-017-generation-training-loop/04-flow.md#update-weights-card-v2-20261031) · [整理前全文](../../../../../references/history/RayTrainGroup.update_weights-before-v2-2026-10-31.md)。
- 所有 v0/v1 状态是固定源码的教学推导，没有运行真实 Ray、训练或权重发布。

- [本轮进入第三段的讨论](../../../../../04-flow.md#pause-before-weight-update)。
- [两侧状态与下一入口的整理](../../../../../04-flow.md#weight-sync-state-card-and-next)：保存请求、状态对照与恢复条件的候选入口。
- [训练 worker 身份与磁盘分支复述](../../../../../04-flow.md#training-worker-and-disk-review-20261030)：当前 checkout 540ea919 与原固定版本 18868a79 的七个相关方法文本相同。创建处 105–134、release 198–203、配置检查 238–246、reload 248–295 及 UpdateWeightFromDisk.update_weights:66–96 用于静态核对；未执行同步、写文件或释放进程。
- 固定源码：train.py:88–93；actor_group.py:178–190、241–246；rollout.py:151–158；MegatronTrainRayActor.update_weights:629–678。
- _full_disk_weight_update_enabled 检查 role=actor、update_weight_mode=full、update_weight_transport=disk 三者。主例选择其返回 False 的路径，本轮额外对照 True 分支的职责，不深入传输。
- 仅静态核对，没有新运行。哈希与阅读范围见 [源码证据](../../../../../references/source-evidence.json)。

</details>
