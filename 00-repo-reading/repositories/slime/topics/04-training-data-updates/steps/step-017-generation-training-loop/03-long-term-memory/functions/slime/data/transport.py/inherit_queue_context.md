# inherit_queue_context

- Step 012 继承：来自 [Step 011 完整记录](../../../../../../../../02-rollout-reward/steps/step-011-generate-and-rm-group/03-long-term-memory/functions/slime/data/transport.py/inherit_queue_context.md)；保留原话、未知、版本与认识日期，仅重算链接。

- Step 011 继承：来自 [Step 010 · 02-short-term-memory](../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/02-short-term-memory/functions/slime/data/transport.py/inherit_queue_context.md)，完整保留原话、未知、来源和认识时间；路径重算不代表新增理解。

- 源码定位：[slime/data/transport.py:207–230](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L207-L230)。
- 首次接触：Step 010 骨架已出现；2026-10-26 按用户追问展开独立函数记录。
- 最近认识更新：2026-10-26，用户已表达队列凭证与生成结果归属的关系，理解冲突时会报错；当前追问为什么看似检查的操作属于正常主线，补全与检查的区别尚待反馈。

[generate_and_rm 第三部分](../../rollout/sglang_rollout.py/generate_and_rm.md#sample-postprocessing) → **本函数** → 第一次返回后进入 hook；第二次返回后进入评分判断。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：队列交出一份任务后，生成器或 hook 可能创建新的 Sample 来保存回答。新对象可能没有原任务的队列凭据，后续就无法按原凭据登记这份结果。
2. **具体内容**：遍历输出中的 Sample，将源对象里存在的六种队列字段按规则深拷贝到输出；已有任务身份冲突时抛错。返回原来的 output。
3. **建议构建的心智模型**：

   > 新对象装着生成结果，旧输入带着任务凭据。这个函数将旧输入的队列凭据等信息复制到新结果上，让后续仍能按原任务提交结果；回答内容保留。

4. **调用代码**：

   ```python
   # queue_input 在生成前由 copy.copy(sample) 保存
   sample = inherit_queue_context(queue_input, sample)  # 生成器返回后
   sample = await apply_rollout_sample_hooks(args, sample, evaluation=evaluation)
   sample = inherit_queue_context(queue_input, sample)  # hook 返回后
   ```

## 本场景的输入与输出

**输入**：source 对应生成前保存的 queue_input；output 对应当前生成结果，当前 Coding Agent 路径为 list[Sample]。第二次调用时，output 是 hook 处理后的结果。

**输出**：返回同一个 output 对象。函数修改其中的 Sample 字段，不新建结果列表，也不覆盖 response、tokens、reward 等生成内容。

### 先补输入对象是怎样得到这些字段的

当前最大的前置缺口是“Sample 类没有字段，source 为什么会有”。现在先看[字段附加的运行时阶段](../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/references/queue-context-fields.md)：QueueReader.get_samples 在返回任务前给实例写入领取凭据等字段，generate_and_rm 再给 queue_input 追加请求记录。只有 source 已有的值才会被本函数继承。此前把继承方法归为 QueueDataSource.get_samples 的说法，现精确为 QueueReader 定义、QueueDataSource 继承使用。

### 先看一份结果前后发生了什么

这里的 queue 是任务队列，context 是随这份队列任务携带的信息；inherit 指把这些信息传给结果，不是 Python 的类继承。先只观察 `_queue_lease` 这一项，它保存的是任务领取凭据。

下面用“任务 A / 凭据 A”代称真实凭据，只展示职责，不伪造完整 Lease 或实际运行值：

| 对象 | 调用前 | 调用后 |
| --- | --- | --- |
| `queue_input`：原输入快照 | 题目 A，以及队列发放的凭据 A | 仍保存原信息 |
| `output` 里的新 Sample | 生成出来的回答/轨迹，尚无凭据 A | 回答/轨迹不变，补上凭据 A |

```text
原输入 queue_input：题目 A + 凭据 A
新结果 output：     回答/轨迹
                         ↓ inherit_queue_context
新结果 output：     回答/轨迹 + 凭据 A
```

**它解决的是“这份新结果按哪份已领取任务的凭据交回去”，不解决“怎样生成或修改回答”。** 如果一次生成返回两个新 Sample，两者都可以继承同一原任务的信息。

这个用途有真实上下游：队列读取处 `queue_data_source.py:1095` 给输入 Sample 写入 `_queue_lease`；后面的 `pack_rollout_group:239–248` 从结果中读取这份凭据，用它调用 `controller.complete` 提交结果。凭据不只是题目编号，还关系到这次任务领取；本轮暂不展开其内部字段。

生成器若新建对象，这些动态附加字段不会仅凭“它也是 Sample”就自动存在。函数因此显式复制列出的字段。反过来，原输入没有队列字段时，它就没有这些信息可继承，相关循环会跳过。

### 1. 先看它处理哪些字段

| 字段 | 本轮先按什么职责理解 | 已有字段怎么处理 |
| --- | --- | --- |
| `_queue_lease`、`_queue_receipt` | 队列任务身份与回执 | 输出已存在且不同于 source 时抛错；否则从 source 深拷贝 |
| `queue_generation_requests` | 该任务记录的生成请求信息 | source 存在时，用其深拷贝更新输出 |
| `_queue_source_positions` | 依赖的已有队列结果记录位置，来自任务 metadata | 仅输出缺少时补入 |
| `_queue_original_input` | 最初任务输入的存储引用，恢复重新生成时可以加载 | 仅输出缺少时补入 |
| `_queue_resume_origin` | 当前只确认兼容透传/归档清理；未找到实际写入处，具体用途待查 | 仅输出缺少时补入 |

这些是允许继承的附加字段名单，不是每个 Sample 一开始都具备的六个属性。所有规则先检查 source 是否有字段；没有就跳过。queue_input 是输入的浅拷贝，因此接住了上游已经附加的字段；generate_and_rm 还会在这个快照上追加生成请求记录。

**读取与写入要区分**：getattr(source, name) 从源对象读取字段值，setattr(sample, name, copy.deepcopy(value)) 将值的副本写到输出 Sample。源里存在不等于无条件覆盖：身份字段先检查冲突，其余字段也分强制更新和仅缺失时补入。

逐项写入位置、用途和使用方见[六字段来源参考](../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/references/queue-context-fields.md)。其中 _queue_resume_origin 之前仅按名称概括为“恢复来源”过于肯定，现已明确标为实际来源待查；queue_generation_requests 是记录，不是执行任务的队列。

### 2. 按字段规则继承，保留输出本身

真实方法：

```python
def inherit_queue_context(source, output):
    """Carry the input authorization across hooks that construct new trajectories."""
    import copy

    from slime.rollout.base_types import iter_samples

    fields = (
        "_queue_lease",
        "_queue_receipt",
        "_queue_source_positions",
        "_queue_resume_origin",
        "_queue_original_input",
        "queue_generation_requests",
    )
    for sample in iter_samples(output):
        for name in fields:
            if not hasattr(source, name):
                continue
            value = getattr(source, name)
            if name in {"_queue_lease", "_queue_receipt"} and getattr(sample, name, value) != value:
                raise ValueError("A generation hook returned a different queue task authorization")
            if name in {"_queue_lease", "_queue_receipt", "queue_generation_requests"} or not hasattr(sample, name):
                setattr(sample, name, copy.deepcopy(value))
    return output
```

`iter_samples` 在这里只按接口理解：遍历单个 Sample 或嵌套列表中的 Sample 叶子，不改变列表形状。每个叶子使用同一个 source 继承字段。

深拷贝意味着输出得到独立的字段副本；例如修改输出的请求记录列表，不会顺带修改源对象的那份列表。身份不同会报错，而不是强行将另一份任务的结果归到当前任务。

### 字段不存在，是否说明出错

这里先问的是 **source 是否有字段**，随后才决定怎样处理 output 中的 Sample：

| 条件 | 本函数的行为 |
| --- | --- |
| source 没有这个字段 | 直接跳过，不报错，也不生成字段值 |
| source 有，输出 Sample 没有 | 从 source 深拷贝到输出 Sample |
| 两边都有 | 按字段规则保留或复制；lease/receipt 值冲突才抛错 |

“逐渐加上去”可以描述整条流程中不同阶段附加信息，但本函数只转交 source 已有的值，不负责产生六项业务信息。六项不是每份 Sample 在每个阶段都必须有：例如新领取任务时写入 lease，并移除旧 receipt；此时没有 receipt 是正常状态。

只有先确认“这条实际路径在这个阶段必须有某字段”，缺失才构成需要回查上游的线索。不能仅凭六项中缺了一项就断言程序出错。当前未取得实际运行对象，以上是固定源码的条件规则。

### 为什么它属于正常流程：先完成交接，再阻止身份冲突

生成器或 hook 返回新 Sample 是被允许的正常行为，新对象未必携带队列字段。因此本函数在正常路径上需要把原输入已有的上下文补到结果里；只检查而不复制，不能完成这次交接。

| 原输入 | 新结果原先携带 | 本函数行为 |
| --- | --- | --- |
| 凭据 A | 没有凭据 | 复制 A，属于正常补全 |
| 凭据 A | 相同的凭据 A | 允许继续，按规则复制 |
| 凭据 A | 不同的凭据 B | 抛 ValueError，阻止带着冲突身份继续 |

此处的 A/B 只是凭据的示意值。报错说明生成器或 hook 交回的身份与当前输入冲突，具体责任需按发生在 353 还是 355 以及上游代码定位，不能仅从报错断言一定是 hook。它核对的是字段身份，不检查回答内容是否真的解答了原题，也不负责完成服务器端提交或授权验证。

正常骨架保留此函数的理由是上下文传递属于结果交接必需的工作；内部的冲突检查与这次传递相邻，保护该交接。读取骨架时先记“生成结果 → 补回输入上下文”，再按需展开检查。

### 3. 为什么 hook 前后各执行一次

```text
queue_input（原任务上下文）
   ├─ 第一次 → 生成器交回的 Sample
   └─ 第二次 → hook 处理后最终保留的 Sample
```

生成器可能新建对象，第一次保证进入 hook 前有任务上下文；hook 又可能返回替换对象，所以第二次重新检查并继承。两次都使用同一个 queue_input。

第一次返回后，父函数到 354 调用 hook；第二次返回后，到 358 判断评分责任。这里和后续内容修改属于同一个后处理阶段，但职责不同。

### 局部验证

2026-10-26，使用固定源码的真实 Sample 类、iter_samples 和本函数，在隔离命名空间验证；仅注入模块入口满足内部导入，未连接队列服务：

```text
No queue fields: same output, no queue identity added
Nested output: identities inherited, source fields deep-copied, existing non-identity field preserved
Conflicting task identity: ValueError
Replacement Sample: same task receipt restored, generated response preserved
```

验证数据是本地构造，task_id、位置和生成请求字段不代表真实作业。未验证队列提交、回执确认或模型训练。

## 我的直接表述（原话）

> 简单来说就是获取sample之后二次处理对吗？
> 那么现在是否需要重新看一下这里的inherit queue context的部分呢？

这是对第三部分整体位置的概括和本函数的阅读请求，不作为已理解六个字段拷贝规则的证据。

用户进一步反馈：

> 我这里其实不是特别清楚
> 这里的这个inherit queue context到底在做什么这件事情

已补“原输入凭据 → 新结果补上凭据”的对照和真实上下游证据；这些仍是助手解释，未写成个人理解。

用户进一步区分了拷贝操作与字段语义：

> 我这里有一点没有理解
> 这里只是把这个queue context的部分也就是这里fields的六个部分？
> 如果有这个field的话就直接把这个部分通过setattr的方式直接放在这里的sample里面？
> 这是我简单的理解？
>
> 但是这六个部分是干什么的呢/
> 或者说这六个field是哪里来的呢？
> 我十分的不理解

已表达按字段读取并 setattr 的初步关系；来源、用途以及“存在并非一律覆盖”的规则由助手补充，尚待反馈。

用户进一步强调仍缺少实际添加时机：

> 这里的内容我就都不是很理解了
> 我很难理解这些内容具体是在哪里被提交的时候加上去的
> 以及是用来干什么的
> 以及心智模型是怎样的
> 整体我觉得都很模糊
>
> 我觉得我起码需要知道这里的每一个字段是在什么情况上被加上去的吧？
> 因为当前的sample里面并没有这个字段

本轮将字段参考改为“普通实例 → 队列读取中附加 → 生成前快照追加 → 结果继承 → 已接受结果回执”的顺序，区分类定义缺少字段与某个运行实例缺少字段；新说明尚待反馈。

用户进一步提出字段缺失的判断：

> 好的我差不多知道了
> 那么这里我简单的理解一下
> 这里的inherit queue context的部分
> 就是检查这些字段有没有
> 我的理解是如果一开始就有这些字段的话
> 那么之后在运行的过程中会逐渐加上去？
> 如果这里没有
> 因为之前在queue里面处理这些信息的时候应该会需要加上去
> 如果没有加上去那么说明这里出问题了
>
> 这是我对于这里的理解

已表达“上游附加、下游继续传递”的联系。助手校准 source 缺失时主动跳过，以及不同路径和阶段并不要求六项齐全；该校准尚待用户反馈。

用户进一步表达任务归属与检查的关系：

> 这里我对于inherit queue context的理解就是 这里每一个queue输入的时候会有一个凭证
> 这里是多加了一步
> 这样子就能够做到确保generate返还的sample是能够对应上的是我的理解
> 如果不对的话 这一步就会报错
> 说明hook弄错了（怎么看都像是检查的步骤 为什么会出现在标准流程里面？）

已表达凭证随结果保持任务归属，以及冲突时停止的关系；助手补充正常补全与冲突检查的区别、生成器与 hook 两个返回边界，并限制“对应上”为队列身份而非回答语义。新解释尚待反馈。

## 尚不清楚

- 用户已表达上游附加与下游传递的联系；source/output 的区分、字段缺失不必然出错的校准及具体覆盖条件仍待反馈。
- 五项字段已查到主要来源或记录位置，仍待用户反馈；_queue_resume_origin 未找到生产方，完整协议不作已知处理。
- 用户已提出身份冲突检查，但尚需区分正常补全、冲突来源定位与回答语义正确性；为何保留在正常主线的解释尚待反馈。

<details>
<summary>来源与本轮范围</summary>

- 固定提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；[本函数](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L207-L230)、[iter_samples:98–104](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/base_types.py#L98-L104)。
- [领取任务时写入凭据:1079–1099](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/queue_data_source.py#L1079-L1099)、[提交结果时读取凭据:233–249](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L233-L249)。
- [输入快照:312–325](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L312-L325)、[两次调用:353–355](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L353-L355)。
- [本轮过程](../../../../../../../../02-rollout-reward/steps/step-010-generate-and-rm/04-flow.md#inherit-queue-context-reading)；本地验证不等于队列协议或训练运行。

</details>
