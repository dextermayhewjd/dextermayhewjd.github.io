# RolloutManager.pause_rollout_admission

> **采用格式**：参照本步已采用的 training_completed，使用分层伪代码、同行注释和段后整体说明。
>
> **面包屑**：[Step 017](../../../../../01-scope.md#weight-handoff) → [train.py:88](../../../train.py/train.md#weight-handoff) → **本函数** → [2.3 分层心智模型](#mental-model) → [3 输入输出](#input-output)。

- 源码定位：[slime/ray/rollout.py:151](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L151)，调用方为 train.py:88；固定证据为 `18868a79`。
- 当前本机：[rollout.py:151](/home/fredkeira/projects/slime/slime/ray/rollout.py:151)。当前 checkout `540ea919` 的相关方法与固定版本一致。
- 首次接触：Step 017，2026-10-29，先在 train 父卡中说明；2026-10-30 按用户要求独立成卡。
- 最近个人认识：2026-10-31，用户在上述解释与模型整理后明确表示“这里的心智模型我理解了”，要求继续。当前暂停请求、后台确认和返回原状态的模型已有理解反馈；条件变量深层机制、分布式实现与实际运行另行保留边界。
- 本次整理：2026-10-31 按用户要求对齐既有卡片；格式调整不代表新增个人理解。

## 1. 定位：完成登记之后，为同步权重暂停新增生成

本轮训练及数据侧完成登记已结束，主循环走到 train.py:88。fully_async 后台可能还会继续准备样本，因此先暂停新任务接纳，再进入 89 行的权重同步。

本卡解释 88 行的暂停入口；71 行的 training_completed 处理已用数据的登记。两者通过 RolloutManager 的不同方法进入，分别操作数据记录与后台接纳状态。

## 2. LLM 整理：使用场合、具体内容与心智模型

### 2.1 使用场合

主循环准备发布新权重，需要先让生成后台暂时不再领取、启动新的 rollout 任务。

### 2.2 具体内容

查找 data_source 中登记为 fully_async 的后台对象；有对象时调用 pause(drain=False)，返回它原先的暂停状态。没有对象时返回 True，让后续恢复接口跳过它。下面的状态读写示例沿用 Step 012 读过的本地 AsyncRolloutWorker，分布式实现保留在来源中对照。

<a id="mental-model"></a>

### 2.3 建议构建的心智模型：分层伪代码

> 在同步新权重前，找到本次作业已登记的生成后台，要求它暂停领取和启动新的生成任务。后台正常运行时，等待它确认暂停已经落实，再返回主循环。
>
> 返回的是调用前的暂停状态，供权重同步后决定是否恢复；没有登记后台时，直接返回 True，表示后面无需恢复。
>
> 本次使用 drain=False：已经启动的生成任务仍可能继续执行，这里不等待它们全部结束。

三个状态名各有一个用途：`paused` 表达暂停请求，`admission_paused` 表达后台确认，调用方的 `was_paused` 保存暂停前状态。`notify_all()` 只负责唤醒等待方，让它重新检查确认状态。

以下是阅读用伪代码，使用 python 代码块显示注释。自然语言和省略号概括未展开部分，不作为独立可运行程序。

#### 2.3.1 第一层：主循环请求暂停，并保存原状态

```python
was_paused = ray.get(  # 等暂停接口返回，把原状态保存下来
    rollout_manager.pause_rollout_admission.remote()  # 远程请求暂停新任务接纳
)
```

**这一段完成什么**：主循环在同步权重前，等待生成侧的暂停接纳接口处理完。返回值留给后面的恢复逻辑使用。

<a id="manager-pause"></a>

#### 2.3.2 第二层：管理器找到后台，把暂停请求交给它

```python
RolloutManager.pause_rollout_admission()  # 主循环进入的管理接口
    worker = getattr(self.data_source, "consumers", {}).get("fully_async")  # 找后台
    if worker is None: return True  # 无后台可暂停，后面也不必恢复
    return worker.pause(drain=False)  # 执行暂停，带回暂停前的状态
```

**这一段完成什么**：管理器负责定位本次作业的后台并委派操作。真正控制新任务接纳的是后台对象；此处将它的原状态返回给调用者。

<a id="data-source-worker-ownership"></a>

**对象关系**：在已登记后台的情况下，查找路径是 `rollout_manager.data_source.consumers["fully_async"] → worker`。这里不是遍历每个 worker 寻找它的数据源，也不是给 data_source 设置暂停状态；管理器从自己的数据源登记表取得后台对象，再调用该对象的方法。

第二层伪代码里的 self 指 RolloutManager；下面第三层 pause 和 _loop 中的 self 指同一个 AsyncRolloutWorker。被设置的是 worker 自己的 paused 字段。

<a id="pause-worker"></a>

#### 2.3.3 第三层：后台通过共享状态停止新增任务，确认后返回

这里有两个执行位置：管理器调用 pause，已经运行的后台循环 _loop 响应状态变化。下面按一次请求的因果顺序展开，**不是 pause 依次调用 _loop 的函数链**。

<a id="pause-write-read-evidence"></a>

##### 2.3.3.1 pause 写入请求

```python
# AsyncRolloutWorker.pause 中，在 condition 保护下
previous = self.paused  # 记住调用前的暂停状态
self.paused = True  # 请求暂时不再接纳新任务
```

##### 2.3.3.2 已在运行的 _loop 读取请求并报告状态

```python
# AsyncRolloutWorker._loop 的任务补充部分
while ... and not self.paused:  # 还需满足名额、积压等条件；暂停时不再进入
    groups = self.data_buffer.get_samples(1)  # 领取新组
    ...  # 为新组创建生成 Task；暂停时不会继续从这里补充
with self.condition:  # 检查完接纳条件后报告状态
    self.admission_paused = self.paused  # 告知等待方：已观察到暂停状态
    self.condition.notify_all()  # 唤醒等待检查的调用方
```

先由 admission_paused 保存“后台已观察到暂停”的状态，notify_all 再唤醒等待方去重新检查它。通知本身不携带模型权重，也不替代条件检查；此处确认的是接纳暂停，模型权重同步在返回主循环后才开始。

##### 2.3.3.3 pause 等到确认，返回旧状态

```python
# 回到 pause 的等待逻辑，仍在 condition 保护下；本次 drain=False
# not self.admission_paused：后台尚未确认暂停，才需要等待
while self.running and self.error is None and not self.admission_paused:
    self.condition.wait()  # 暂时放开锁并等待通知，醒来后重新检查条件
if self.error is not None: raise self.error  # 运行异常向上抛出
return previous  # 交回原状态，不是交回当前已设为 True 的状态
```

<a id="pause-request-and-acknowledgment"></a>

**等待的方向**：admission_paused=False 表示后台尚未确认暂停，因此进入 wait；admission_paused=True 时，`not self.admission_paused` 为 False，正常路径就退出等待并返回。它等待“后台确认已暂停接纳”，不等待后台恢复接纳。

以下只看后台正常运行、无错误、初始未暂停的情况：

| 时点 | paused：暂停请求 | admission_paused：后台确认 | 此次 pause 调用 |
| --- | --- | --- | --- |
| 请求前 | False | False | 尚未调用 |
| 请求已发出，后台尚未处理 | True | False | wait，等后台确认 |
| 后台检查状态并报告暂停 | True | True | 被通知后重新检查，退出等待 |
| 返回主循环 | True | True | 返回之前保存的 False，随后才进入权重同步 |

`condition` 是 threading.Condition 对象，wait 是它的方法；并不是 condition 自己变成某种“wait 状态”。调用 wait 的这一侧会暂时释放锁，让后台线程能取得锁、写入确认并调用 notify_all。醒来重新取得锁后，还要再次检查 while 条件。主循环的 ray.get 则在外层等待整个管理器调用返回。

**这一段完成什么**：pause 发出暂停请求，后台循环据此停止补充新任务并报告状态；正常确认后，pause 返回原暂停状态。已有生成任务可以继续运行，本次不负责逐个取消它们。若后台已经不运行，则不需要等待它再报告一次暂停。

<a id="return-to-train"></a>

### 2.4 调用代码与返回位置

真实调用已在 2.3.1 展示：返回后，train.py:88 的 was_paused 接到布尔值，主循环继续到 89 行的 actor_model.update_weights()。

同步之后，只有还有下一轮时才调用恢复接口；恢复接口又只在 was_paused=False 时恢复。对应组合见 [train 父卡](../../../train.py/train.md#resume-admission-meaning)。

<a id="input-output"></a>

## 3. 本场景的输入与输出

### 3.1 输入：已有的后台对象及其暂停状态

没有显式业务参数。管理器用已有的 data_source 找后台；本调用不接收 rollout_id、样本或训练数据。主例选择本地 worker 存在、正在运行且没有异常的情况。

### 3.2 返回值：区分当前状态与原状态

| 调用前 | 暂停接口正常处理后 | 返回给 was_paused | 对后续恢复的意义 |
| --- | --- | --- | --- |
| 后台存在，原先未暂停 | 不再补充新生成任务 | False | 同步后可按外层条件恢复 |
| 后台存在，原先已暂停 | 保持暂停 | True | 保留原来的暂停状态 |
| 后台不存在 | 没有 pause 操作 | True | 跳过恢复；不是说曾有一个已暂停后台 |

三个名字分别表示：paused 是控制请求；admission_paused 是后台报告的确认状态；was_paused 是交回主循环的原状态。

### 3.3 一个具体变化与当前边界

假设暂停前 A、B 正在生成，C、D 尚未启动。暂停接口正常完成后，后台不再新启动 C、D；A、B 仍可能在运行。若原先未暂停，当前 paused 已是 True，但返回的 was_paused 是 False。

这是一份源码推导的教学场景，未运行真实生成。作用是权重同步前协调新增工作，不表示后台进程已退出、GPU 已释放或所有在途任务都已结束。

## 4. 我的直接表述（原话）

2026-10-31 对当前心智模型的理解反馈：

> 好的 我觉得 我这里的心智模型我理解了
> 那么我们如果要继续吧
> 下一步需要看什么呢?

据此接回主循环第 89 行的权重同步；不再把当前模型重复列为等待反馈，也不由此推断未展开的条件变量或分布式机制已掌握。见[本轮接续](../../../../../../step-017-generation-training-loop/04-flow.md#pause-model-understood-next-weights-20261031)。

2026-10-31 对请求、确认和通知的最新复述：

> 好的 我饿得理解是
> 一开始这里的是设置状态了之后
> 这里开始不再接受新的samples
> 同时这里在把自己的admission pause的这二个状态更新了之后
> 通过notify all的方式告诉调用方这里已经接受到了信息并且同步了?

用户已连接暂停请求、后台停止新接纳、确认字段与通知动作。助手校准为先更新共享的确认状态，再唤醒等待方复查；“同步”在这里指暂停状态的协调，不表示模型权重已经更新。见[本轮记录](../../../../../../step-017-generation-training-loop/04-flow.md#pause-acknowledgment-understanding-20261031)。

本轮对对象和等待条件的复述：

> 我这里不是特别清楚得点在于
> 这里到底做什么?
> 说着我觉得需要一个比较整体的框架才能够清楚这里的到底做了什么?
> 我来复述一下
> 1.首先主要的循环要求停止接纳新的任务
> 2. 具体的实现在与这里的pause rollout admission
> 这里rolloutmanager做的内容是找到每一个worker的data source?
> 然后让这里的rolloutmanager的data sauce(worker)的状态为pause?
> 也就是暂时不需要再rollout了?
> 然后这里就会通过这里的pause
> 来做到这里的rolloutworker不再能够拿到任务?
> 然后2.3.3.3的内容我其实没有特别理解
>
> 我目前的理解是这里因为admission paused了
> 所以这里的condition变成了wait?
> 是我的理解

用户已表达主循环要求停止新接纳；对象归属以及“尚未确认才等待、确认后退出”的方向仍由助手校准，不写为已掌握。见[本轮记录](../../../../../../step-017-generation-training-loop/04-flow.md#pause-ownership-and-ack-wait-20261031)。

本轮用户要求：

> 那么按照之前方式完成对于这里的apuserollout admission的short term memory的构建吧
> 可以参考一下这里的training completed的部分

这次确认的是记录的构建方式，尚无对新稿的机制理解反馈。此前原话和当时的说明完整保留如下。

<details>
<summary>展开既有个人表述与反馈</summary>

此前在本步第三段提出：

> 然后下一步不是这里的paused吗？
> 虽然应该也很好理解
> 就是原有的rollout部分不再接受新的请求应该是这个意思对吧
> actor model 更新权重我们先看这一步吗？

这段已表达暂停接纳新请求的初步认识；具体粒度和 was_paused 的含义由助手核对，不能自动记为已掌握。

2026-10-30 用户要求独立看这一函数：

> 那么看一下这里是否需要单独建立一个卡片吧
> 我觉得还是需要单独看一下?

本次确认了单独阅读和记录的范围，尚无针对返回布尔值或 drain=False 等待边界的新增复述。

2026-10-30 用户对该层职责的反馈：

> 我其实没有看懂这一步具体在做什么 或者这个抽象层级到底完成了什么事情这件事

本轮先补“生成后台独立运行”的背景，再用 A/B 已运行、C/D 尚未启动的场景说明暂停新任务的效果。上层发出请求、管理器定位并委派、后台控制任务启动三层分工属于助手解释，尚未收到理解反馈。见[本轮记录](../../../../../../step-017-generation-training-loop/04-flow.md#pause-layer-responsibility-20261030)。

2026-10-30 用户继续追问结论的来源：

> 我在哪里能够的到这个结论的呢?
> 我们之前看的几个步骤能够得到怎样的结论

本轮用写入 paused、循环检查 paused、创建任务与暂停确认的源码位置建立证据链，并接回 Step 012、013、016 和当前 Step 017。此处新增的是助手的交叉核对，理解仍待反馈。见[本轮证据记录](../../../../../../step-017-generation-training-loop/04-flow.md#pause-evidence-from-earlier-steps-20261030)。

2026-10-31 用户对暂停的理解与卡点（节选）：

> 好的 我的理解是 这里的是单独同志一下这里的rolloutworker 不用再领取新的任务了
> 是我的理解 对吗?
> 也就是这里需要通过这种方式通过停止领取任务的方式来暂停闲置的消耗是我的理解
> 然后这里你说的停止又是哪一行呢?
> 我的意思是这里的这里的3.2  到底要读什么这件事情

停止领取新任务的方向正确；本轮将目的校准为权重同步前的接纳协调，并将 3.2 改成写入 paused、循环检查 paused、回填确认三个直接观察点。完整问题还涉及将 controller 完成登记误接到暂停，见[本轮记录](../../../../../../step-017-generation-training-loop/04-flow.md#completion-versus-pause-20261031)。尚无对这些校准的新反馈。

</details>

## 5. 尚不清楚

当前暂停请求、后台确认和返回原状态的心智模型，已获得用户“我理解了”的反馈。以下仍保留实现与验证边界：

- Condition 内部的锁、调度和通知竞争细节，未系统展开。
- 分布式 RolloutScheduler 的控制消息、异常与关闭并发路径，未逐项阅读。
- 没有执行真实 Ray、后台暂停或权重同步。

<details>
<summary>此前待反馈的接口问题，保留为理解过程历史</summary>

下面是本轮明确理解反馈之前的问题记录；当前接口层面的模型按上述反馈接续，不再作为继续阅读的门槛。

- 管理器的数据源登记表与后台 worker 的对象归属、不同方法中 self 指向谁，本轮已补说明，待反馈。
- admission_paused=False 才在正常路径等待、True 后退出等待，以及 Condition 对象与布尔条件的区别，本轮已补说明，待反馈。
- `was_paused` 表示原状态，尤其是无后台对象时返回 True 的约定，仍待用户反馈。
- 已能表述暂停领取新任务；暂停的目的、它与消费登记的不同调用链及在途任务边界仍待反馈。
- 主循环、当前管理器方法和后台循环各自的职责，以及本次主要状态变化，已补充场景说明，尚待反馈。
- 条件变量、调度循环确认暂停以及分布式控制消息的细节，本次未展开。
- 没有执行真实 Ray、后台暂停或权重同步。

</details>

## 6. 来源、验证与完整例子

<details>
<summary>当前整理的源码依据与范围</summary>

- 主入口：RolloutManager.pause_rollout_admission:151–154；调用方 train.py:88；恢复接口 resume_rollout_admission:156–158。
- 本地示例：AsyncRolloutWorker.pause:114–122；_loop:202–228。2.3.3.2 折叠了其他接纳条件和任务创建细节；2.3.3.3 按本次 drain=False 去掉了恒不成立的 active 等待分支。
- pause 与 _loop 通过同一个对象的状态和 condition 配合；图文排列顺序不等于同一个线程顺序调用所有片段。
- [本轮整理过程](../../../../../../step-017-generation-training-loop/04-flow.md#pause-card-v2-adopted-20261031) · [整理前完整卡片](../../../../../references/history/RolloutManager.pause_rollout_admission-before-v2-2026-10-31.md)。
- 以下保留旧版的补充来源与回查入口；没有新增真实 Ray、后台或权重同步运行。

- 固定版本 `18868a79`：RolloutManager.pause_rollout_admission:151–154、resume_rollout_admission:156–158；AsyncRolloutWorker.pause:114–122；RolloutScheduler.pause:209–226。
- 创建卡片时，前三个方法与当前本机 `540ea919` 的 AST 对比一致；没有执行这些方法。分布式暂停接口仅作同一约定的静态对照。
- [最初暂停与更新的讨论](../../../../../../step-017-generation-training-loop/04-flow.md#pause-before-weight-update) · [本轮独立建卡](../../../../../../step-017-generation-training-loop/04-flow.md#pause-admission-independent-card-20261030)。
- 表格由源码直接推导；正常运行的等待条件与实际调用耗时不由该表验证。

</details>

<details>
<summary>展开来源对照与旧步骤关系</summary>

这里复用 Step 012 已选择的本地 AsyncRolloutWorker 分支。`_get_worker` 会把该对象登记为 `data_buffer.consumers["fully_async"]`；管理器通过同名登记找到它。默认 straw 可使用另一种分布式实现，不能把下面的本地行号当成所有后端的实现。

| 源码证据 | 直接支持的结论 |
| --- | --- |
| [pause:116–117](/home/fredkeira/projects/slime/slime/rollout/fully_async_rollout.py:116)：保存 previous，设置 `self.paused = True` | 请求将这个后台改为暂停状态，并保留旧状态 |
| [_loop:202–208](/home/fredkeira/projects/slime/slime/rollout/fully_async_rollout.py:202)：补充新任务的 while 包含 `and not self.paused`，内部才调用 get_samples | 暂停后，不再进入取新组的这段循环 |
| [_loop:214–223](/home/fredkeira/projects/slime/slime/rollout/fully_async_rollout.py:214)：create_task 与 active_tasks.add 在同一补充循环内 | 这条路径不会继续创建新生成任务；已经存在的 Task 不因该条件被取消 |
| [_loop:225–228](/home/fredkeira/projects/slime/slime/rollout/fully_async_rollout.py:225)：回填 admission_paused 并 notify_all | 后台报告已观察到暂停状态，供 pause 的等待条件确认 |
| [train.py:88–89](/home/fredkeira/projects/slime/train.py:88)：先等待 pause，再调用 update_weights | 主循环把这次暂停安排在权重同步之前 |

因此，“停止新增生成任务”来自 **pause 写入状态 + 旧循环读取状态并限制任务创建**，不是只根据 pause 的名称推断。主循环的先后顺序说明为什么此刻调用它；并不证明所有在途生成已完成。

**之前步骤的回查入口**

| 既有阅读 | 可用于这次推理的关系 |
| --- | --- |
| [Step 012 的 _loop](../../rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md#phase-3) | 后台在条件满足时取新组、创建任务；paused 是其中一个接纳条件 |
| [Step 013：完成结果交付](../../../../../../../../02-rollout-reward/steps/step-013-completed-group-handoff/README.md) | 已完成结果先入队，再由上层按需取走；取走一批结果与关闭整个后台是两件事 |
| [Step 016：Sample 到训练数据](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/README.md) | 训练端接到的是整理和分片后的数据引用 |
| [Step 017 的 train 父卡](../../../train.py/train.md#weight-handoff) | 先等这批数据训练完成，再通知消费完成，随后显式暂停接纳并同步权重 |

这些是已读材料提供的关系，不表示本轮已经确认用户能独立复述每项细节。现在新增的连接是：主循环通过这个暂停接口，控制以前读过的后台补充任务循环。旧 `_loop` 卡已从 03 调入本步 02，原日期、原话和未知保留。

</details>

<details>
<summary>按需核对：AsyncRolloutWorker.pause 的完整短实现</summary>

```python
def pause(self, *, drain=True):
    with self.condition:
        previous = self.paused
        self.paused = True
        while self.running and self.error is None and (not self.admission_paused or (drain and self.active)):
            self.condition.wait()
        if self.error is not None:
            raise self.error
        return previous
```

调用者传入 `drain=False`，所以 `drain and self.active` 不会要求等待 active 归零。`not self.admission_paused` 仍可以使调用等待接纳暂停被确认。已有 error 时会抛错，而不是返回一个“失败布尔值”。

分布式实现 [RolloutScheduler.pause:209](/home/fredkeira/projects/slime/slime/rollout/fully_async_distributed.py:209)同样返回原暂停状态，`drain=False` 时不额外要求 pending 和 running_workers 全部清空；具体控制消息与条件变量机制暂不展开。

</details>
