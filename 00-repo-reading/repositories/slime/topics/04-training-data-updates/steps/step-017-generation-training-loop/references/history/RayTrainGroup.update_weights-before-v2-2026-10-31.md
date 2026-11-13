# RayTrainGroup.update_weights

- 源码定位：[slime/ray/actor_group.py:178](/home/hongshi/projects/slime/slime/ray/actor_group.py:178)，固定版本 `18868a79`；调用方为 [train.py:89](/home/hongshi/projects/slime/train.py:89)。
- 首次接触：Step 017，2026-10-29。
- 最近认识更新：2026-10-30，用户明确指出 update_weights 更新的应是生成侧权重，并质疑此前“训练侧”的说法。更新目标已由用户正确指出；助手区分发起同步的训练 worker 与被更新的生成引擎，句柄身份和磁盘分支的理解不随之视为完成。
- 导航：[scope 的③](../../01-scope.md#weight-handoff) → **本卡：提交权重更新并等待** → [返回 train 的暂停/恢复组合](../../02-short-term-memory/functions/train.py/train.md#weight-handoff)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：一轮训练与完成通知已经结束，调用方先暂停后台 rollout 的新任务接纳，再让生成侧使用训练更新后的权重。假定训练和生成服务可用，主例沿用非全量磁盘更新分支；按用户本轮复述补充全量磁盘分支的职责对照。

2. **具体内容**：遍历训练 worker 句柄，提交每个 worker 的 update_weights.remote，并在本方法内部通过 ray.get 等待。全量磁盘分支先让 worker 写好权重文件，再登记版本，按配置释放训练 worker，最后通知生成引擎从磁盘加载。连接、写文件与服务端处理的具体实现继续作为下层边界。

3. **建议构建的心智模型**：

   > 训练已改动训练侧参数；这个入口组织把相应权重提供给生成侧，并等各 worker 的更新调用结束。
   >
   > 先完成训练计算，再同步已有新权重。暂停与恢复接纳由外层 train 编排，本方法负责中间的权重同步；训练进程仍参与这次同步。

   **执行者与更新目标分开读**：`actor.update_weights.remote()` 向训练 worker 提交同步工作；这项工作的目标是让生成引擎使用训练后的权重。称 actor 为训练 worker，并不表示这个调用再次通过训练数据改变训练侧参数。

4. **调用代码**（train.py:89）：

   ```python
   actor_model.update_weights()
   ```

## 本场景的输入与输出

本次没有显式业务参数；self 是已经创建的 RayTrainGroup，内部持有 `_actor_handlers` 和权重更新配置。当前训练 worker 已持有本轮训练后的模型，生成侧服务已经就绪；选择非全量磁盘更新分支，不把 object-store 数据传输与权重传输方式混为一个配置。

**输出**：正常返回 None；在本方法返回前，ray.get 已经等待这些 worker 的更新调用结束。具体权重传输不在此处展开。

<a id="training-finished-before-sync"></a>

### 到这里时，训练侧和生成侧各在做什么

沿当前 train.py 正常路径，67 行已等待本轮训练结束，训练 worker 已有本轮的新权重。随后 88 行暂停新的 rollout 接纳，89 行把新权重同步到已有生成引擎。这里需要分开看两侧：

| 一侧 | 更新权重期间的状态 |
| --- | --- |
| 训练侧 | 本轮训练计算已结束，新参数已经算好；训练 worker 参与权重同步，主循环等待同步返回，尚未进入下一轮训练 |
| rollout 侧 | 后台调度暂停接纳新的生成任务；已有生成引擎接收训练侧的新权重。当前没有据此断言所有在途请求都已结束 |

因此，“训练已经完成，现在同步给生成侧”是当前时序；训练进程仍在执行同步工作，不能把它概括成两侧进程都停掉了。

```text
本轮训练计算完成，新权重已在训练侧
    → 暂停新的 rollout 任务接纳
    → 训练 worker 向生成侧同步权重，主循环等待
    → 有下一轮且原先未暂停时，恢复接纳
```

pause_rollout_admission 使用 drain=False，只由这一调用不能推断全部在途生成已经结束或取消。生成引擎在实际安装权重时如何协调在途请求属于下层同步机制，本轮继续留白；不以“暂停新接纳”替代该机制的解释。

<a id="training-copy-to-generation-copy"></a>

### 先区分：训练得到新参数，生成侧还需要接收它们

<a id="training-versus-weight-sync"></a>

**2026-10-30 当前问题：async_train 已经训练了，为什么还要 update_weights？** 同一个策略模型在训练侧和生成侧各有一份参数。训练过程本身就会改变训练侧的参数；后面的 update_weights 把已经训练好的参数交给生成侧，不是等到此时才通过样本算出新参数。

下面是 train.py:67、89 的两次真实调用，省略中间完成通知和资源管理语句，仅对照它们的作用：

```python
ray.get(actor_model.async_train(rollout_id, rollout_data_ref))
actor_model.update_weights()
```

- 第一行：提交本轮训练并等它完成；返回后，训练侧已经得到新参数。
- 第二行：组织把这些新参数交给 rollout 的生成引擎；正常同步完成后，生成侧才能使用这一份训练结果。

数据是否已组成可交付的一批，由前面的生成与组批环节负责。当前的 update_weights 没有拿到 rollout_data_ref，也不负责再检查样本数量或重新训练。本轮只澄清“先训练，再同步”的两次状态变化，暂不同时展开 actor 身份、磁盘分支与恢复接纳。

训练 worker 执行学习计算，生成引擎执行模型生成；两侧各自持有用于计算的模型参数。训练侧算出新参数，不表示生成引擎里的参数已经自动改变。下面用 v0、v1 表示前后两份权重，仅为静态教学标记，不是真实运行版本号：

| 时点 | 训练侧 | 生成侧 |
| --- | --- | --- |
| 本轮训练前 | 将基于数据训练 | 用 v0 生成过数据 |
| 本轮训练结束、尚未同步 | 已得到 v1 | 尚未因训练侧的计算而自动获得 v1 |
| update_weights 正常完成同步 | 提供 v1，等待更新调用完成 | 可更新的生成引擎获得 v1，供后续生成使用 |

因此，这里的 `actor_model.update_weights()` 组织的是把**已经算好的权重交给生成侧**。本轮学习计算在前面的 async_train 及外层等待处已经结束；这里不重新用样本训练一遍。

主循环先暂停后台领取、启动新的 rollout 任务，再组织同步。同步完成后，若还有下一轮且这次暂停前原本可以接任务，就允许后台继续接新任务；这就是父卡中的[恢复 rollout 接纳](../../02-short-term-memory/functions/train.py/train.md#resume-admission-meaning)。它不等于重启模型服务，也不自动重跑旧任务。已有在途请求怎样完成或等待，仍属于未展开的同步机制。

<a id="worker-update-submission"></a>

### 当前精读骨架（178–182）

真实源码节选，只保留本轮分支；后面的全量磁盘保存和重载分支暂时折叠。

```python
def update_weights(self) -> None:
    if not self._full_disk_weight_update_enabled():
        ray.get([actor.update_weights.remote() for actor in self._actor_handlers])
        return
```

1. 遍历的是已有训练 worker 句柄；各 worker 的更新调用产生结果引用。
2. 本方法内部的 ray.get 等待这些调用结束，随后返回 None。
3. 下层 [MegatronTrainRayActor.update_weights:629](/home/hongshi/projects/slime/slime/backends/megatron_utils/actor.py:629) 取得可更新的生成引擎，并最终委派 weight_updater.update_weights；这里只定位，不追通信实现。

和刚读过的 async_train 对照：async_train 先交回引用列表，由 train 的外层等待；这里 update_weights 把等待包在自身内部，所以调用方直接调用它。

<a id="training-worker-versus-rollout-engine"></a>

### actor 是执行同步的训练 worker，生成引擎是接收方

用户把“这次要更新生成侧”与“循环变量属于生成侧”联系在一起。这里需要分别定位对象和操作结果。`self` 仍然是同一个 RayTrainGroup，`_actor_handlers` 也与 async_train 使用的是同一份训练 worker 句柄列表；训练结束没有把这份列表替换成生成引擎。

创建处的直接依据是 actor_group.py:105–134：默认 actor_impl 为 MegatronTrainRayActor，经 ray.remote 创建实例后，把返回的句柄 append 到 `_actor_handlers`。本场景未配置自定义 actor_cls。

| 本段对象 | 归属与职责 |
| --- | --- |
| RayTrainGroup | driver 中的训练组对象，持有训练 worker 的远程句柄 |
| 循环变量 actor | 训练 worker 的句柄；先可提交 train，训练完成后还可提交 update_weights |
| rollout_engines | 生成引擎的句柄；由训练 worker 经 rollout_manager 取得，作为后续权重同步的接收方 |

本轮的数据方向是：训练组调用训练 worker 的 update_weights，由训练侧将已有新权重交给生成引擎。训练计算结束后，训练 worker 仍能执行同步或保存工作；操作的接收方不决定循环变量的身份。

<a id="full-disk-branch-review"></a>

### 按本轮复述对照：版本号、release 和磁盘 reload（184–190）

只有 role=actor、update_weight_mode=full、update_weight_transport=disk 同时成立才进入下面的分支。前面的非全量磁盘分支在 182 行已 return，不会随后再执行这里。

```python
weight_version = self._disk_weight_version + 1
disk_weight_dir = Path(self.args.update_weight_disk_dir) / f"weight_v{weight_version:06d}"
ray.get([actor.update_weights.remote() for actor in self._actor_handlers])
self._disk_weight_version = weight_version
if self._release_train_enabled():
    self.release()
self._reload_rollout_weights_from_disk(disk_weight_dir, str(weight_version))
```

| 顺序 | 本段实际做什么 |
| --- | --- |
| 184–185 | 算出下一次发布的版本号和目录，例如 weight_v000003。构造 Path 本身尚未保存权重 |
| 186 | 调用训练 worker 并等待。在此磁盘配置下，下层 UpdateWeightFromDisk.update_weights 将模型写到对应版本目录，完成各 rank 的保存与必要的发布处理 |
| 187 | 写完后，训练组登记当前已发布的磁盘权重版本 |
| 188–189 | 按 release_train 配置决定是否释放训练 worker。release 清空 `_actor_handlers`，并对原有句柄调用 ray.kill；这是资源生命周期操作，不是允许继续训练或恢复 rollout 接纳 |
| 190 | 把目录和版本交给 `_reload_rollout_weights_from_disk`，让 rollout 引擎真正加载已写好的模型文件，不只是改一项路径记录 |

reload 内部在 actor_group.py:254–286 取得生成引擎，必要时拉取本机文件，再调用各引擎的 update_weights_from_disk。这里仅核对“谁读取什么”，不展开缓存、暂停方式、文件发布或通信协议。磁盘路径承担训练侧与生成侧之间的交接；没有把已有生成模型搬到磁盘、也没有在本函数中开放下一轮训练。

### 读完回到哪里

<a id="worker-handoff-next-reading"></a>

**2026-10-30 当前入口：返回 [train 的暂停、同步与恢复](../../02-short-term-memory/functions/train.py/train.md#weight-handoff)。** 用户再次核对岗位必要性后，撤回把 worker 的 641–647 行单列为必读的建议。此前准备的 [worker 权重交接小窗口](../../01-scope.md#worker-weight-sync-window)保留作按需证据；原始源码 [MegatronTrainRayActor.update_weights:629](/home/fredkeira/projects/slime/slime/backends/megatron_utils/actor.py:629)可用于核对，但不要求读完所有 backend 或 updater。未将该方法标记已理解或已运行。

回到 [train 父卡](../../02-short-term-memory/functions/train.py/train.md#weight-handoff)：88 行暂停新接纳，89 行完成更新；有下一轮时，92–93 行按原暂停状态决定是否恢复。不是无条件打开原本已暂停的 producer。

**下一观察点：更新完后，什么时候恢复生成？** 进入 [train.py:92–93](/home/hongshi/projects/slime/train.py:92)，必要时只回查 [RolloutManager.resume_rollout_admission:156–158](/home/hongshi/projects/slime/slime/ray/rollout.py:156)。下一次只需弄清两个条件：是否还有下一轮、暂停前是否已经暂停。暂停与恢复先保留在父卡的 [恢复接纳入口](../../02-short-term-memory/functions/train.py/train.md#resume-after-weight-sync)，不新建完整调度专题。

## 我的直接表述（原话）

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

本轮据此回看更新目的与“接纳”的具体对象，不直接推进周期评估。上面新增的两侧参数说明是助手讲解，理解状态待用户反馈。见[本轮完整回顾](../../04-flow.md#training-review-and-resume-20261030)。

2026-10-30 用户回答 actor 身份并对照磁盘分支（采用中断后重新发送的完整版本，不重复收录前一稿）：

> 这里肯定是rollout侧的生成引擎啊
> 因为train的部分已经更新完整了
> 只需要吧actor部分的权重 更新更新完整就可以了
> 但是我们也可以看到这里的还有一个更新权重版本的内容
>
> 更新完整了之后这里就开始释放 是否可以训练了
> 同时吧reload可以reload的版本在磁盘中的位置 更新一下 是我对于这里的update weights的理解

用户已把动作目的联系到生成侧新权重，并观察到磁盘分支的版本和目录；循环对象、释放对象及 reload 的实际动作仍需按上文校准。原话不改写为正确结论，校准效果等待后续反馈。见[本轮形成过程](../../04-flow.md#training-worker-and-disk-review-20261030)。

2026-10-30 用户进一步追问（完整原文）：

> 我其实有点没动
> 这里的更新权重是rollout部分的数据已经足够的情况下更新的是actor部分的权重?
> 但是上面的actor model async train不是已经是在训练的部分了吗?
> 我的理解是需要训练完了之后才会考虑更新这里的权重啊?

用户已经提出“训练完再调用后续权重更新”的执行顺序；训练侧参数已在训练中改变、后续更新指生成侧接收这份参数，是本轮助手补充的关系，尚待反馈。见[本轮讨论](../../04-flow.md#train-versus-weight-sync-20261030)。

2026-10-30 用户纠正更新目标（完整原文）：

> 对岸 那么你为什么说这里的update weights 还是在更新训练侧的权重呢?
> 我觉得这里的actor update weights 应该是生成侧的权重才对吧

用户对“更新目标是生成侧”的判断正确。此前助手反复强调循环中的 actor 是训练 worker，没有足够突出其执行的是向生成侧发布权重的工作，导致执行者与更新对象仍混淆。本轮明确：训练侧持有新参数并发起同步，生成侧接收并使用它们；这不是再次执行训练。变量 actor 的身份是否已区分，仍等待用户反馈。见[本轮纠正](../../04-flow.md#weight-update-executor-versus-target-20261030)。

## 尚不清楚

- 用户明确表示权重更新和恢复接纳未理解；本轮补充两侧参数与新任务接纳的说明，尚待反馈。
- 用户已明确指出 update_weights 的更新目标是生成侧；执行此方法的 actor 句柄仍属于训练 worker，这项身份区别尚待反馈。
- weight_updater 的权重传输、引擎同步和在途生成收束方式未展开。
- 循环中的训练 worker 与权重接收方 rollout 引擎的身份区分，本轮已提供创建处证据，尚待用户反馈。
- 全量磁盘分支已按本轮问题作职责对照；release 终止训练 worker 与恢复接纳不同，reload 真正加载文件而非仅改路径，这两项校准尚待反馈。写文件、缓存和传输内部未精读。
- 没有运行真实权重更新、生成或训练。

<details>
<summary>来源、验证与完整例子</summary>

- [本轮进入第三段的讨论](../../04-flow.md#pause-before-weight-update)。
- [两侧状态与下一入口的整理](../../04-flow.md#weight-sync-state-card-and-next)：保存请求、状态对照与恢复条件的候选入口。
- [训练 worker 身份与磁盘分支复述](../../04-flow.md#training-worker-and-disk-review-20261030)：当前 checkout 540ea919 与原固定版本 18868a79 的七个相关方法文本相同。创建处 105–134、release 198–203、配置检查 238–246、reload 248–295 及 UpdateWeightFromDisk.update_weights:66–96 用于静态核对；未执行同步、写文件或释放进程。
- 固定源码：train.py:88–93；actor_group.py:178–190、241–246；rollout.py:151–158；MegatronTrainRayActor.update_weights:629–678。
- _full_disk_weight_update_enabled 检查 role=actor、update_weight_mode=full、update_weight_transport=disk 三者。主例选择其返回 False 的路径，本轮额外对照 True 分支的职责，不深入传输。
- 仅静态核对，没有新运行。哈希与阅读范围见 [源码证据](../source-evidence.json)。

</details>
