# RayTrainGroup.async_train

- 源码定位：[slime/ray/actor_group.py:148](/home/hongshi/projects/slime/slime/ray/actor_group.py:148)，固定版本 `18868a79`；调用方为 [train.py:67](/home/hongshi/projects/slime/train.py:67)。
- 首次接触：Step 017，2026-10-29；此前作为 train 卡的内部段落阅读，本轮独立成卡。
- 最近认识更新：2026-10-29，用户在区分结果引用与实际结果后明确表示“大概理解这里的async train了”，并要求继续。本函数记录为已有总体理解反馈；后端计算与未展开的失败细节不随之标记掌握。
- 导航：[scope 3.2 的①](../../../../../01-scope.md#core-skeleton) → **[当前问题：external_data 配对与返回列表](#external-data-pairing)** → [返回 train 的等待位置](../../../train.py/train.md#async-train-submission)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：driver 的 train 已取得本轮训练数据引用，通过本地 `actor_model`（一个 RayTrainGroup 对象）把本轮工作交给训练 worker。主线为 use_critic=False、external_data=None；本轮按用户问题对照 external_data 为列表的分支。

2. **具体内容**：遍历 `self._actor_handlers`，为每个 worker 提交一次 `actor.train.remote(...)`。external_data 为列表时，先核对与 worker 数量相等，再按位置将每项 ed 交给对应 worker；否则给所有 worker 传入同一个 external_data。两条分支都返回每次提交得到的任务结果引用列表，等待由调用方负责。

3. **建议构建的心智模型**：

   > 输入：本轮要训练的数据引用。动作：给训练组中的各 worker 提交工作。输出：这些工作的结果引用，交给上层等待。
   >
   > 数据引用告诉 worker 去哪里取训练材料；本函数产生的任务引用让调用方取得执行结果。

4. **调用代码**（train.py:67，真实调用）：

   ```python
   ray.get(actor_model.async_train(rollout_id, rollout_data_ref))
   ```

## 本场景的输入与输出

沿用 Step 016 的数据交付场景：Sample 已经整理成训练字段，按 DP 分配后进入 Ray 对象存储。下面说明结构，不是真实训练输出。

| 输入或已有状态 | 当前内容 |
| --- | --- |
| rollout_id | 当前外层循环的轮次编号 |
| rollout_data_ref | `list[Box]`；各 Box 的 inner 是一个 DP 分片训练数据的 ObjectRef |
| external_data | 主线为 None；对照分支是按 worker 顺序排列的额外输入列表 |
| self._actor_handlers | 本地持有的远程 worker 句柄列表；当前默认实现为 MegatronTrainRayActor。句柄让本地能够向相应 worker 提交调用 |

**输出**：一个任务结果引用列表，每个训练 worker 对应一项。当前 actor 训练路径中，各任务正常完成后的结果为 None；本函数本身返回这些引用，不等待训练全部结束。DP 数据分片数与 worker 数量不要求相等。

### 当前精读的核心骨架（163–166）

教学裁剪：保留真实签名与普通分支；省略 docstring 和 external_data 为列表时的分支。本例 external_data=None。

```python
def async_train(self, rollout_id, rollout_data_ref, external_data=None):
    return [
        actor.train.remote(rollout_id, rollout_data_ref, external_data=external_data)
        for actor in self._actor_handlers
    ]
```

1. **for 遍历 worker 句柄**：每次迭代向一个 worker 提交本轮训练任务。
2. **remote 传入训练材料**：每个调用都收到本轮编号与整个数据引用列表。worker 怎样选取所属 DP 数据留在后端实现，不在本段重新切分 Sample。
3. **return 交回任务结果引用列表**：每次 remote 提交返回一项 ObjectRef，列表推导式收集它们，交给调用方。

<a id="external-data-pairing"></a>

### 按需对照上面的分支：for actor, ed 与返回列表（157–162）

用户当前看到的是 external_data 为列表时的路径。主线传入 None 时跳过它；两条路最终都给各 worker 提交训练任务，区别在额外输入如何交付。

```python
if isinstance(external_data, list):
    assert len(external_data) == len(self._actor_handlers)
    return [
        actor.train.remote(rollout_id, rollout_data_ref, external_data=ed)
        for actor, ed in zip(self._actor_handlers, external_data, strict=False)
    ]
```

**先看数量检查。** if 判断是否为 list；assert 检查额外输入项数是否与 worker 数量一致。这里要求“每个 worker 一项额外输入”，不是要求样本数或 DP 分片数等于 worker 数。assert 只核对数量，输入顺序是否与 worker 对应仍由调用方保证。

**再看 zip 与解包。** 用两组位置符号说明，下面的 worker0 / worker1 代表句柄，extra0 / extra1 代表额外输入；不是实际运行的数据。

```text
self._actor_handlers = [worker0, worker1]
external_data        = [extra0,  extra1]

zip 按位置给出：       (worker0, extra0), (worker1, extra1)
for actor, ed：        actor=worker0, ed=extra0
                      actor=worker1, ed=extra1
```

每次循环拿到一对，再分别赋给 actor 与 ed。因此，本轮提交可以表示为：worker0 收到 extra0，worker1 收到 extra1；两者还都会收到 rollout_id 与 rollout_data_ref。zip 不依据 ID 查找或重新排序。strict=False 的 zip 会在较短的一侧结束，前面的 assert 用于先拦住长度不等的情况。

**两项公共输入相同，为何还用 zip？** 每次调用除了 rollout_id、rollout_data_ref，还有第三项 `external_data=ed`。zip 配对的是 worker 句柄与这一项额外输入；它不负责配对两项公共输入，也不从 rollout_data_ref 中选 DP 分片。下面两个调用正是这个配对的效果，worker0 / worker1 表示已有的远程句柄：

```python
ref0 = worker0.train.remote(rollout_id, rollout_data_ref, external_data=extra0)
ref1 = worker1.train.remote(rollout_id, rollout_data_ref, external_data=extra1)
```

**最后区分循环取出的元组与放进列表的元素。** zip 产生 `(actor, ed)` 元组，for 把每对拆到两个变量中。列表推导式放入结果的是 for 前面的表达式：这里是 `actor.train.remote(...)` 的返回值。可以把两部分对应起来看：

```python
return [
    actor.train.remote(rollout_id, rollout_data_ref, external_data=ed)  # 放进结果列表
    for actor, ed in zip(self._actor_handlers, external_data, strict=False)  # 本轮取谁
]
```

方括号 `[...]` 是列表推导式：构造列表时就调用 remote 提交任务，并将每次返回的任务结果引用放入列表。可在教学上展开成下面的普通 for 循环；refs 是解释用变量，原源码用的是列表推导式。

```python
refs = []
for actor, ed in zip(self._actor_handlers, external_data, strict=False):
    ref = actor.train.remote(rollout_id, rollout_data_ref, external_data=ed)
    refs.append(ref)
return refs
```

所以返回类型是普通 list，内容形如 `[任务结果引用0, 任务结果引用1]`。这些任务已经提交，但不保证已经执行完；列表中没有保存稍后才调用的函数。圆括号形式 `(表达式 for ...)` 才是生成器表达式；本段返回的不是 generator 对象。

**两条分支的差异是额外输入怎样分配；返回结构相同。** 以下假设两名 worker，rollout_id 与 rollout_data_ref 都作为共同输入传入。

| external_data 的形式 | worker0 收到的额外输入 | worker1 收到的额外输入 | 本次返回 |
| --- | --- | --- | --- |
| 列表 `[extra0, extra1]` | extra0 | extra1 | 两次 train.remote 返回的任务结果引用列表 |
| 非列表，例如 None 或字典 X | 同一个值：None 或 X | 同一个值：None 或 X | 两次 train.remote 返回的任务结果引用列表 |

每次调用产生各自的任务引用；两分支具有相同的返回类型，不表示不同调用返回相同引用对象。worker 数量为 N 时，正常返回列表有 N 项，列表元素都是该次提交返回的引用，不是 `(actor, ed)` 元组。外层 ray.get 再等待这些任务的实际结果。

在当前主线 external_data=None 时，下面的普通分支只遍历 actor，并给每个 worker 传入 None。需要额外输入的调用点可在 [train.py:61–63](/home/hongshi/projects/slime/train.py:61)定位：critic 提交后得到 value_refs，作为列表传入 actor 训练。本轮只解释配对，不展开 critic 如何计算。

**局部验证范围**：从固定源码提取原 async_train 方法，搭配只记录调用的 remote 替身，核对了列表配对、None 分支及长度不等三种情况。前两种情况在返回前已记录两次提交，返回类型均为 list；长度不等时报 AssertionError，提交记录为空。具体输出见 [局部验证记录](../../../../../references/async-train-pairing-local-output.json)。其中 mock-ObjectRef 是替身字符串，不是真实 Ray 对象；没有运行训练。

当前默认后端的选择在 [actor_group.py:105](/home/hongshi/projects/slime/slime/ray/actor_group.py:105)，执行入口为 [MegatronTrainRayActor.train:400](/home/hongshi/projects/slime/slime/backends/megatron_utils/actor.py:400)。这里只定位；不进入取数、模型计算或优化器内部。

<a id="task-result-reference"></a>

### 引用列表怎样被使用，读完返回哪里

这里的 actor 变量保存的是**本地持有的远程 worker 句柄**。调用 `actor.train.remote(...)` 向对应 worker 提交一次 train 调用；训练在 worker 进程执行，本地得到一个 ObjectRef，用来等待或取得这次调用的结果。已有 worker 句柄的创建与保存见 [actor_group.py:118–134](/home/hongshi/projects/slime/slime/ray/actor_group.py:118)，本轮只核对这一关系，不展开资源创建。

前面的“任务列表”是简称，精确说法是**远程训练调用的结果引用列表**。例如提交上面的两次调用后，返回 `[ref0, ref1]`；每项是一个 ObjectRef 对象，列表既不保存 worker 对象本身，也不保存训练代码或 Sample。拿到引用只表示有了这次调用的结果入口，不表示训练已经完成。

回到 [train.py:67](/home/hongshi/projects/slime/train.py:67) 的外层 ray.get。为显示交接，下例把原本一行调用在教学上拆成两句；train_refs 是说明用变量，原源码没有给中间值命名。

```python
train_refs = actor_model.async_train(rollout_id, rollout_data_ref)
ray.get(train_refs)
```

第一句返回任务引用，第二句等待。正常路径中等待成功后，主循环继续到 71 行的完成通知。任务失败可能抛出异常，此处不据此推断其他任务的清理行为。

以当前两名 actor worker 为例，`ray.get([ref0, ref1])` 等待两次训练调用的结果。当前 [actor 训练路径](/home/hongshi/projects/slime/slime/backends/megatron_utils/actor.py:410)正常返回 None，因此取回的值为 `[None, None]`；实际训练发生在 worker 内部。这里保存引用的作用是让主循环能够等本轮训练结束，并不需要返回模型本身。

<a id="execution-model-prerequisite"></a>

### 当前需要补哪一小块前置

用户明确表示拆包和列表推导式已理解，因此不再把这两个语法点当成本轮前置。根据反复追问“返回的是任务还是结果”“本地 actor 怎样调用”的表现，助手建议先区分下面两个关系；这是针对当前卡点的判断，不是对用户整体基础的结论。

| 待补关系 | 这一段需要能区分什么 |
| --- | --- |
| 异步结果对象与结果值 | 工作本身、用于等待/取得结果的对象、工作最终返回的值。拿到结果对象与工作执行结束是两件事 |
| 远程句柄与 worker 实例 | 本地 actor 变量持有句柄；目标 worker 在另一进程，remote 提交其方法调用。对象位置和实际执行位置需要一起考虑 |

建议先局部回查 [20.3：Future 与结果值](../../../../../../../../../../../../content/projects/python-async-concurrency/20-future-result/index.md)，再按需要看 [20.4：等待他处交付结果](../../../../../../../../../../../../content/projects/python-async-concurrency/20-await-future/index.md)。这里借用的是“通过一个对象等待和取得结果”的共同思路；Ray ObjectRef 不是 asyncio.Future，具体操作仍按各自 API。

也可用已读 [make_done_cb](../../../../../03-long-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._make_done_cb.md#phase-2) 唤起同一类区别：done_task 是任务对象，done_task.result() 得到任务返回的样本结果。这个旧例子是回查入口，不据此声称用户已掌握全部 Future 机制。

当前只确定前置缺口的候选与最小回查位置；没有切换独立异步课程进度、新开学习 Step，或自动开始完整 Ray 教程。

## 我的直接表述（原话）

此前对数据来路与本函数入口的表述：

> 好的 那么我们来看一下这里的内容吧
> 我们之前吧rollout manager 得到的sample变成了rayref 来传给这里的megatron对吧
> 然后我们目前需要看一下这里的actor_model.async_train
> 我是这么理解的对吗/

本轮对函数卡与骨架的要求：

> 好的 那么我第一个需要看的函数是哪一个呢？
> 是这里的哪一个函数卡片呢？
> 是否应该在3.2的部分给出这里需要我精读的核心骨架呢？

第一段表达了总体方向与入口选择；第二段要求清晰导航。两者不代表已理解任务分发或返回值。对应问答见下方来源。

本轮对数量、配对和返回类型的理解与疑问：

> 好的我来看一下这个属于actor group的python文件
> 我需要看的部分是这里的async train的内容对吧
> 我来看一下 我还需要知道那些内容
> 这里险些的判断是便利workder的句柄
> 是否和external data的数目相同
> 我的理解是需要数目相同之前的分配才意义对吗？
> 然后是直接给出来的是rollout的id和我们之前看的rollout部分的data ref
> 但是下面的这个for actor ed我有点没理解
>
> 这里应该返回的是一个list generator
> 这里更多的是返还一个acotr train remote的调用列表吗？
> 我不是特别理解

数量对应与入参识别是用户当前提出的理解；for 的配对解包以及列表中存放任务结果引用的区别由助手补充，尚未收到理解反馈。

用户随后确认术语并追问返回内容：

> 对的是列表推到是
> 所以这里是把actor 和ed 便成为一个tuple？
> 然后放在这里的list里面返回？
>
> 这里的两条路径有差异吗？
> 各自返回的是什么呢？

用户已把术语改为列表推导式；关于元组是否进入返回列表仍是待核对的理解。助手补充：zip 的元组供 for 解包，结果列表保存 remote 调用的返回引用；两分支只在每个 worker 接收的 external_data 上不同。这些补充尚待用户反馈。

用户再次连接调用关系并追问引用的含义：

> 返回的就是这里的train remote的任务对吗？
> 返回的任务列表到底什么 我还是没有特别能够理解这里
> 或者我可以理解的方式是
> 如果这里的extrernal data是一个list的话
> 就走第一个分支
> 如果不是的话主要是为什么要用这里的zip我还是没有特别理解？
> 都是拿到rollout id 还有这里的rollout data ref不是吗？
>
> 我的理解是这样子写是因为本来已经有了handler了
> 为了成对使用所以写了一个zip
> 所以能够一起被拆包？
> 然后通过actor train remote 的方式
> 直接使用本地的actor来直接使用这里传入的rollout id还有这里的rollout data ref？
> 创造了这样子的一个ref了之后保留这样子的一个list？

用户已经把配对、拆包与保存引用接成初步链条。尚待校准的是 actor 为本地持有的远程句柄、zip 针对第三项 ed 配对，以及返回列表保存结果引用而非任务本身；以上说明不自动写为已掌握。

用户对当前知识缺口的自述：

> 我感觉是不是我对于python的什么方面的知识不是特别理解导致的这里会有这些问题呢？
>
> 我目前对于这里的拆包还有list operator是理解的 别的似乎不是特别理解

按本轮语境，list operator 对应前面讨论的列表推导式。已理解的语法与待补的执行模型分别记录，未把用户的自我怀疑改写为整体 Python 基础不足。

用户进一步用 Future 解释当前返回值：

> 我理解future是什么 是异步的结果对吗？
> 所以这里返回的内容是actor train remotre之后可能返回的结果 、是我的理解

助手校准：Future 是代表一次异步结果、供等待和读取的对象，结果值本身是另一层；Ray ObjectRef 在本场景代表远程 train 调用的结果，async_train 返回的是这些引用的列表。当前 actor 训练正常完成后实际返回 None，ray.get 才取得这个值。此处沿已有说明进一步区分对象与值，不将 ObjectRef 和 asyncio.Future 视为同一类型。

用户在上述讨论后给出总体理解反馈：

> 好的 我现在大概理解这里的async train了 让我们继续吧

本轮据此回到 train.py 的下一项完成通知。没有新增针对后端实现或异常分支的掌握表述。

## 尚不清楚

- 数据引用列表与本函数返回的任务结果引用列表，用户的精确理解待反馈。
- worker 从输入中选择所属 DP 数据的方法，以及实际训练计算，当前未展开。
- 用户已明确表示拆包与列表推导式已理解；异步结果对象、结果值与远程句柄的关系仍需补清。critic 的计算、异常与取消不展开。
- 用户已提出 zip 为配对拆包、remote 之后保存 ref 的理解；第三项 ed 的差异、远程句柄及结果引用怎样供 ray.get 使用仍待反馈。
- 尚无真实 Ray、模型或训练运行；不以卡片建立推断运行结果。

<details>
<summary>来源、验证与完整例子</summary>

- [首次提交带读](../../../../../04-flow.md#async-train-submission-walkthrough) · [用户来路复述](../../../../../04-flow.md#sample-refs-to-megatron) · [本轮独立卡与 3.2 导航修正](../../../../../04-flow.md#async-train-independent-card)。
- [拆卡前的完整父卡](../../../../../references/history/train-before-async-train-card.md#async-train-submission)保留原有讲解、图、用户原话和未知。新卡承接其中的本函数内容；[当前父卡](../../../train.py/train.md#data-handoff)保留调用前后交接。
- 固定版本 18868a79：actor_group.py:148–166 为函数；105–108 选择默认 worker；train.py:67 为调用方；MegatronTrainRayActor.train:400 仅定位。哈希见 [源码证据](../../../../../references/source-evidence.json)。
- [Ray 官方 actor 调用说明](https://docs.ray.io/en/latest/ray-core/actors.html#calling-the-actor)已用于核对 remote / get。此前独立成卡时仅静态整理；本轮新增的局部替身运行与真实 Ray 调用分开记录。
- [本轮配对与列表疑问](../../../../../04-flow.md#external-data-pairing-and-list) · [原方法搭配 remote 替身的局部输出](../../../../../references/async-train-pairing-local-output.json)。该运行仅核对控制流与返回结构，未运行真实 Ray、模型或训练。
- [元组与两分支返回值的追问](../../../../../04-flow.md#paired-tuple-versus-returned-reference)：沿用上述三种局部结果，本轮没有重复执行。
- [本地句柄、第三项 ed 与等待引用](../../../../../04-flow.md#worker-handle-and-result-reference)：进一步明确“任务列表”简称的边界，沿用既有局部证据，无新增运行。

**书上怎么说（语法依据 A）**：Fluent Python 第 2 版第 2 章的 Generator Expressions 区分生成器表达式与列表推导式。英文原文：

> Genexps use the same syntax as listcomps, but are enclosed in parentheses rather than brackets.

官方中文对照：

> 生成器表达式的句法跟列表推导式几乎一样，只不过把方括号换成圆括号而已。

- 英文：[ch02.md:246–292](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/en/ch02.md:246)，anchor 为 generator-expressions。
- 中文：[ch02.md:231–277](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/zh/ch02.md:231)，相同 anchor，对应 2.3.4。
- 版本：本书基于 Python 3.10；局部核对环境为 Python 3.12.3。已按两侧小节边界核对原句；拆包另核对英文 474–518、中文 468–512 的 Unpacking Sequences and Iterables 小节。

**本函数的判断（本书未覆盖）**：worker 与 external_data 的业务对应、remote 提交和任务结果引用来自 Slime 固定源码、既有 Ray 文档核对及上述局部替身记录，不能归为本书对 Slime 的说明。

</details>
