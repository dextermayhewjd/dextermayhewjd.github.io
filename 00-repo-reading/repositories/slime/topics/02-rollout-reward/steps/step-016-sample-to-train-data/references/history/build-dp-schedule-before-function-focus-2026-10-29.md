> 历史快照：2026-10-29 整理函数与 reference 分工之前的完整卡片。仅供回查，不继续同步更新。
>
> [当前函数卡](../../02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md) · [当前并行概念参考](../parallelism-primer.md)

# build_dp_schedule

<a id="progressive-overview"></a>

## 开头总览：每一步新增什么

始终沿用同一批 A–H；每次训练更新总共使用 8 份样本。

标题只列截至本节已经引入的配置；新概念出现时，再将对应参数加入括号。已引入的参数继续保留，数值与本节 example 一致。

- **[0. Batch：整批计算（GPU=1，batch size=8）](#batch-size-baseline)**：建立基准，一张 GPU 一次计算整批 8 份样本。
- **[1. Micro-batch：分四次计算（GPU=1，batch size=8，micro_batch_size=2）](#microbatch-one-gpu)**：在第 0 步上增加**分次计算**；仍用一张 GPU，每次计算 2 份，四次共同完成一次更新。
- **[2. DP：两个副本分担数据（GPU=2，batch size=8，micro_batch_size=2，DP=2）](#dp-two-gpus)**：在第 1 步上增加**第二个完整模型副本**；原来的四组分给两张 GPU，每张处理两组，共同完成这次更新。
- **[3. PP：同一模型按层分到两个阶段（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2）](#pp-two-stages)**：在第 2 步上增加**副本内部按层分工**；仍有两个 DP 副本，每个副本由两张 GPU 分别承担前后两段模型。
- **[4. VPP：每个物理阶段持有两个模型片段（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2，VPP=2）](#vpp-model-chunks)**：在第 3 步上增加**每个物理阶段的模型片段数**；沿用同一个 8 层模型和 4 张 GPU，对照每张卡持有哪些层。
- **[5. mb_group：同一个虚拟片段按几个小批次一组来安排（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2，VPP=2，mb_group=2）](#microbatch-group)**：接着第 4 步展开**微批的调度分组**；已有模型片段和样本保持不变，观察同一片段怎样按两个微批为一组安排。

- **[6. CP：同一条序列内部怎样合作（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=1，VPP=1，mb_group=1，CP=2）](#context-parallel)**：从第 2 段另作对照，增加**同一条序列内部的 token 分工**；每个 DP 副本由一张卡改为两张卡合作，总 GPU 从 2 变为 4。

---

- 卡片定位：Step 016 中单独保存的函数短期记忆。只解释调度计划怎样产生；实际字段选择与交付回到 [BatchBuilder.split_by_dp](../../02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#prepare-schedule)。
- 源码定位：[slime/utils/dp_schedule.py:82](/home/hongshi/projects/slime/slime/utils/dp_schedule.py:82)，固定版本 `18868a79`，由助手核对。
- 首次接触：Step 016，2026-10-28；先定位接口，本轮补充具体输入输出。
- 最近认识更新：2026-10-29，用户把 CP 与支持跨 GPU 的 attention 算法联系起来；助手进一步区分沿 token 的整体分工与 attention 的跨位置通信，MLP 等也分别处理各卡负责的位置。此范围校准尚待反馈，未据此标记具体通信算法已掌握。
- 导航：**[当前阅读：CP 与 attention 的关系](#cp-and-attention)** · [回看 CP 例子](#context-parallel) · [回看 mb_group 的调度权衡](#mb-group-tradeoff) · [回看分组含义](#microbatch-group) · [回看 VPP](#vpp-model-chunks) · [回看 PP](#pp-two-stages) · [回看 DP](#dp-two-gpus) · [回看基础版本](#batch-size-baseline) · [回看 micro-batch](#microbatch-one-gpu) · [返回 split_by_dp](../../02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#prepare-schedule) · [本步 scope](../../01-scope.md#split-by-dp-skeleton)。

<details>
<summary>函数总览与调用代码（需要定位源码时展开）</summary>

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：split_by_dp 已有完整训练字段，现在需要知道每个 DP rank 分到哪些样本，以及本地怎样按小批次处理。train_parallel_config 已由训练端提供；本函数使用现成的并行配置排数据。

2. **具体内容**：按 rollout 归属组织训练步；每步先组成 micro-batch（小批次），满足数量对齐要求后分给各 rank；返回四项索引与数量信息。相同 rollout 的片段归入同一训练步，但不保证落在同一 rank。

3. **建议构建的心智模型**：

   > build_dp_schedule 制定分配表；split_by_dp 按表取数据。
   >
   > partitions：去整批数据的哪些位置取样本。
   > micro_batch_indices：取回来后，在本 rank 的数据里怎样分小批次。
   > 两个数量列表说明每个训练步安排多少小批次、多少 rollout。

4. **调用代码**（batch_builder.py:457–463，真实调用）：

   ```python
   partitions, micro_batch_indices, num_microbatches, global_batch_sizes = build_dp_schedule(
       self.args,
       self.train_parallel_config,
       total_lengths,
       global_batch_size=self.args.global_batch_size,
       rollout_indices=data["rollout_ids"],
   )
   ```

</details>

## 本场景的输入与输出

<a id="batch-size-baseline"></a>

### 0. Batch：整批计算（GPU=1，batch size=8）

先用你已经知道的 **batch size** 建立一个完整例子。下面是用于理解训练流程的基础示意；本段尚未调用 build_dp_schedule。

我们有 8 份训练样本：

```text
一个 batch = [A, B, C, D, E, F, G, H]
batch size = 8
```

假设一张 GPU 放得下完整模型，也能一次计算这整批数据：

**Example · 一次计算整批数据**

```text
[A, B, C, D, E, F, G, H]   一整批 8 份样本
             ↓
        一张 GPU 上的完整模型
             ↓
        计算这批数据的 loss
             ↓
           反向传播
             ↓
         更新一次模型参数
```

**基础版本：一整批 8 份样本交给模型，用它们完成一次训练更新。** 起点先保留这个完整过程。

后续始终沿用 A–H，保持一次更新总共使用 8 份样本。标题末尾标出本段的 GPU 数量和关键配置；每段最后用这同一批数据展示实际安排。

<a id="microbatch-one-gpu"></a>

### 1. Micro-batch：分四次计算（GPU=1，batch size=8，micro_batch_size=2）

**相对基础版本新增的条件：整批 8 份放不下，一次只能计算 2 份。** 仍然用一张 GPU、同一个完整模型，把这一批数据分成四组，每组称为一个 micro-batch。

这里分的是一批样本：A、B 等每份样本仍然完整。一次显存放不下整批数据，是本例引入 micro-batch 的原因；它在流水线等训练安排中也会使用。

四组都为同一次参数更新提供梯度，计算过程中累积梯度，最后完成一次更新。梯度累积与归一化的具体实现暂不展开。

**Example · 同一个 batch，交给同一张 GPU 分四次计算**

```text
一批 8 份样本：[A,B,C,D,E,F,G,H]

M0=[A,B]   M1=[C,D]   M2=[E,F]   M3=[G,H]
每个 micro-batch 里有 2 份完整样本

GPU 0（完整模型）：M0 → M1 → M2 → M3
                  累积这些计算的梯度 → 更新一次参数

1 张 GPU × 每卡 4 个 micro-batch × 每组 2 份样本 = 8 份
```

总共仍是 8 份样本，改变的是一次计算的规模。固定分组对应 [_pack_step_into_mbs:77–79](/home/hongshi/projects/slime/slime/utils/dp_schedule.py:77)；梯度累积与更新由训练端执行，见 [PyTorch 梯度累积说明](https://docs.pytorch.org/docs/main/notes/amp_examples.html#gradient-accumulation)。

<a id="dp-two-gpus"></a>

### 2. DP：两个副本分担数据（GPU=2，batch size=8，micro_batch_size=2，DP=2）

**相对上一段只增加数据并行副本：让两张 GPU 共同分担这批数据。** GPU 0 和 GPU 1 各放一个完整模型副本；每个 micro-batch 仍有 2 份样本，一次更新使用的样本总数仍为 8。

因此，在当前只采用数据并行、每张 GPU 放一个完整模型的例子中，你可以把 DP 从 1 改为 2 理解成从一张 GPU 增加到两张。**DP 数的是数据并行副本，GPU 数的是设备。** 以后若一个副本又由多张 GPU 协作承载，这两个数量就不再相等。

两个副本分别计算自己负责的数据，并通过梯度同步共同完成本步训练更新。模型复制与梯度同步属于训练端的职责；[PyTorch DDP 官方教程](https://docs.pytorch.org/tutorials/intermediate/ddp_tutorial.html)展示了每个设备上的模型与梯度同步关系。

**Example · 保留原来的四组，把它们分给两张 GPU**

```text
同一个 batch：[A,B,C,D,E,F,G,H]
同样的分组： M0=[A,B]   M1=[C,D]   M2=[E,F]   M3=[G,H]

GPU 0（完整模型副本 0）：M0=[A,B] → M2=[E,F]
GPU 1（完整模型副本 1）：M1=[C,D] → M3=[G,H]

两边的训练贡献通过梯度同步汇合，两个副本完成同一步参数更新。

2 张 GPU × 每卡 2 个 micro-batch × 每组 2 份样本 = 8 份
```

这是数据分工的逻辑图，省略具体通信时机。对每张 GPU 而言，计算从四组变成两组；全体共同处理的仍是 A–H 这 8 份样本。

这个交错分配来自当前 Slime 在 `balance_data=False` 时的规则：[dp_schedule.py:198](/home/hongshi/projects/slime/slime/utils/dp_schedule.py:198)。本例固定分批、每份样本属于独立 rollout，global_batch_size=8，cp_size=vpp_size=mb_group=1；按源码静态推导得到 M0/M2 与 M1/M3，未运行两卡训练。

**三个版本对照：一次更新始终使用 8 份样本**

| 版本 | GPU 数量 | 每卡每次计算的样本数 | 每卡在本次更新前计算几组 | 全部样本数 |
| --- | --- | --- | --- | --- |
| 整批一次计算 | 1 | 8 | 1 | 8 |
| 一张 GPU 分四次 | 1 | 2 | 4 | 8 |
| 两个 DP 副本分担 | 2 | 2 | 2 | 8 |

<a id="pp-two-stages"></a>

### 3. PP：同一模型按层分到两个阶段（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2）

**相对第 2 部分新增的机制：把每个模型副本按层分开放置。** 保留原来的两个 DP 副本、同一批 A–H 和 micro_batch_size=2。为了标清各段，把这个模型具体画成 8 层；每个副本分为两个 PP 阶段，每阶段用一张 GPU。

**固定模型背景：每个副本都包含同样的 8 个 Transformer 层；下一节 VPP 继续使用这 8 层。** 示意只画这些层，省略词嵌入与输出头。模型层数用来标清如何切段，不是 build_dp_schedule 的新增参数。

这里拆分的是**同一个模型副本**：第一个阶段承担第 1–4 层，第二个阶段承担第 5–8 层。每张卡持有的是这个模型的一部分，具体为若干个完整层。它没有把单独一层内部再切成几块。[Megatron 的 PP 说明](https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/parallelism-guide.html)

因此，你说的“每张显卡只需存储较小的一部分模型”方向正确；更准确的说法是“只承担模型中的一段层”。PP 阶段可以包含一层或多层，本例每段包含四层。模型参数被分担后，单卡无需承载整个模型的参数；训练还会使用中间结果等显存。

**Example · 数据分工保留，每个副本内部变成两段模型**

```text
改变前：DP=2，PP=1，共 2 张 GPU
副本 0：M0、M2 → GPU 0 [第 1–8 层]
副本 1：M1、M3 → GPU 1 [第 1–8 层]

改变后：DP=2，PP=2，共 4 张 GPU
副本 0：M0、M2 → GPU 0 [第 1–4 层] → GPU 2 [第 5–8 层]
副本 1：M1、M3 → GPU 1 [第 1–4 层] → GPU 3 [第 5–8 层]

其中：M0=[A,B]，M1=[C,D]，M2=[E,F]，M3=[G,H]
```

图中的箭头传递前一阶段算出的中间结果；同一份样本仍然经过全部 8 层。GPU 编号是本例的设备标签，保留 GPU 0/1 的副本归属，再增加 GPU 2/3；不表示从真实训练作业读取了设备布局。图只展示前向路径，反向传播和梯度同步留待需要时再读。

只跟踪 M0，可以看得更具体：

```text
[A,B] → GPU 0 计算第 1–4 层 → 中间结果 → GPU 2 计算第 5–8 层
```

前一组数据进入后面的阶段后，前面的阶段可以接着处理另一组，形成流水线。这里的 **DP=2 数两个模型副本，PP=2 数每个副本的两个流水线阶段**；在本例每阶段一张卡的设定下，总计 2×2=4 张 GPU。

这段说明训练端的模型布局。build_dp_schedule 仍只安排样本和小批次，并不执行模型按层切分；它也没有直接读取 pp_size，实际读入的配置见 [dp_schedule.py:112–125](/home/hongshi/projects/slime/slime/utils/dp_schedule.py:112)。

<a id="vpp-model-chunks"></a>

### 4. VPP：每个物理阶段持有两个模型片段（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2，VPP=2）

**已确认的本例理解：**

> VPP 这里是同一张 GPU 在不同时间执行模型中的不同层

**相对第 3 部分新增的机制：同一个物理阶段持有多个模型片段，供流水线交错调度。** 这里的“片段”是一组连续层；普通 PP 中的一段也可以包含多层。你说的“一个 GPU 可能有模型的多个片段”对应本例的 VPP，关键是区分**层数**与**片段数**。

先把上节配置带过来，只比较 VPP 引入后的模型布局：

```text
模型：每个副本都是 8 层，沿用第 3 节的模型
设备：DP=2，PP=2，每个物理阶段 1 张 GPU，总共 4 张 GPU
数据：仍是 A–H；M0=[A,B]，M1=[C,D]，M2=[E,F]，M3=[G,H]
变化：每个物理阶段从 1 个模型片段变成 2 个，记为 VPP=1 → 2
```

**Example · 同一张 GPU，启用前后分别持有哪些层？**

| 模型副本与设备 | 上一节：PP=2，VPP=1 | 本节：PP=2，VPP=2 |
| --- | --- | --- |
| 副本 0 · GPU 0 | 一段：[1–4 层] | 两段：[1–2 层]、[5–6 层] |
| 副本 0 · GPU 2 | 一段：[5–8 层] | 两段：[3–4 层]、[7–8 层] |
| 副本 1 · GPU 1 | 一段：[1–4 层] | 两段：[1–2 层]、[5–6 层] |
| 副本 1 · GPU 3 | 一段：[5–8 层] | 两段：[3–4 层]、[7–8 层] |

每个副本有 `PP × VPP = 2 × 2 = 4` 个模型片段；均分 8 层后，每片段 2 层。每张 GPU 持有 2 个片段，**合计仍是 4 层**。物理 GPU 数仍为 `DP × PP = 2 × 2 = 4`，VPP 没有增加物理设备。这组数量关系针对本例每阶段一张卡、层数均分的设定。[Megatron 官方 VPP 层分布示例](https://docs.nvidia.com/megatron-core/developer-guide/latest/apidocs/core/core.parallel_state.html#core.parallel_state.initialize_model_parallel)

再只跟踪副本 0 的 M0，看模型布局怎样影响数据路径：

```text
上一节：M0 → GPU 0 [1–4 层] → GPU 2 [5–8 层]

本节：  M0 → GPU 0 [1–2 层] → GPU 2 [3–4 层]
                            → GPU 0 [5–6 层] → GPU 2 [7–8 层]
```

沿箭头传递的是各段计算后的中间结果。**同一份数据仍按第 1 到第 8 层的顺序计算**，现在会再次回到 GPU 0 上的另一段模型。M2 走相同路径；副本 1 的 M1、M3 对应 GPU 1、GPU 3。

**这里再次使用的是同一张 GPU；两次执行的是不同的层。** 在上例中，GPU 0 第一次执行第 1–2 层，再次接到中间结果时执行第 5–6 层。第 5–6 层仍是另外两层，VPP 不会把它们替换成第 1–2 层，也不要求这两段共享参数。

一个模型原本就可以包含多层；层内部采用 MLP、Attention 等结构，与这些层怎样分配到设备是不同的问题。这里先把模型看成已有的第 1 到第 8 层：VPP 调整片段的放置和交错执行安排，模型的这条层次顺序保持不变。

这样切分后，调度器可以把不同小批次在各片段上的工作交错安排，争取减少流水线空闲。上图只说明一个小批次的前向路径；实际收益取决于调度和通信，并不由片段数单独保证。

接回当前函数：build_dp_schedule 读取 `vpp_size`，据此决定是否用 `mb_group` 约束小批次数；模型切层由训练端负责。这里先读清布局，微批组的安排后续再展开。本例完整配置在启用 VPP 时还配套选用 `mb_group=2`；Slime 未启用时传 1，启用时读取训练模型配置，见 [actor.py:107–119](/home/hongshi/projects/slime/slime/backends/megatron_utils/actor.py:107)。本节是教学示意，没有执行多卡训练。

<a id="microbatch-group"></a>

### 5. mb_group：同一个虚拟片段按几个小批次一组来安排（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2，VPP=2，mb_group=2）

**mb_group 数的是：给同一个虚拟模型片段安排计算时，每组包含多少个 micro-batch。** 它在源码中是 `microbatch_group_size_per_vp_stage` 的局部简称。这一段把已有例子的调度组展开，模型、GPU 和样本分组都继续沿用上节。

先只看 DP 副本 0 已经拿到的两种东西：

```text
数据：M0=[A,B]，M2=[E,F]                 每个 micro-batch 有 2 份样本
模型：GPU 0 持有片段 0=[第 1–2 层]
                  片段 1=[第 5–6 层]     每个物理阶段有 2 个片段
```

现在需要安排“哪一个模型片段处理哪一个微批”。`mb_group=2` 表示在一个片段上，按两个微批为一组安排计算。[官方参数定义](https://docs.nvidia.com/megatron-core/developer-guide/0.18.1/apidocs/core/core.model_parallel_config.html#core.model_parallel_config.ModelParallelConfig.microbatch_group_size_per_vp_stage)

**三个参数都等于 2，但数的是不同对象：**

| 参数 | 数的对象 | 本例对应什么 |
| --- | --- | --- |
| micro_batch_size=2 | 每个微批中的样本 | M0 有 A、B；M2 有 E、F |
| VPP=2 | 每个物理阶段持有的模型片段 | GPU 0 持有第 1–2 层、第 5–6 层两个片段 |
| mb_group=2 | 每个调度组中的微批 | 同一片段按 M0、M2 两个微批为一组安排 |

**Example · 给 GPU 0 的两个模型片段安排前向计算**

```text
片段 0：第 1–2 层
    处理 M0=[A,B]           ┐
    处理 M2=[E,F]           ┘ 两个微批为一组：mb_group=2

片段 1：第 5–6 层
    处理 M0 对应的中间结果  ┐
    处理 M2 对应的中间结果  ┘ 同一组微批在另一个片段上的计算
```

**一个片段处理这组数据时，仍是两次计算，每次处理一个微批。** M0 和 M2 没有被拼成一个四样本的微批；micro_batch_size 仍是 2。VPP 决定本例每阶段有两个模型片段，mb_group 则参与决定这些片段与微批的计算安排。

这里只列 GPU 0 的前向计算项，省略了 GPU 2 的工作、通信等待和反向传播。片段 1 使用的中间结果必须先经过 GPU 2 的第 3–4 层；图中上下顺序不表示省略这些依赖。该前向顺序可由上游 [get_schedule_table](https://github.com/NVIDIA/Megatron-LM/blob/core_v0.18.0/megatron/core/pipeline_parallel/schedules.py#L882)核对；实际参数也用于反向安排。

本例每个 DP 副本总共正好有两个微批，所以能组成一组；mb_group 描述组大小。微批更多时，还会继续安排后续组。前面的 VPP 例子已经配套取了 mb_group=2，这里是在解释它，没有把“尚未讲到”当成“此前没有此配置”。

<a id="mb-group-tradeoff"></a>

**它在权衡什么：先推进多少微批，以及何时让其他片段继续工作。**

可以把 mb_group 看成调度粒度的性能权衡。它直接改变微批与模型片段的执行安排，进而影响通信等待、流水线空闲和需要保留的中间结果。这里“切换片段”是 GPU 0 从已有的第 1–2 层改为执行已有的第 5–6 层；本例两段都由这张卡持有。

先看当前例子中不会被分组消除的交接：

```text
GPU 0 的同一个片段：第 1–2 层
    计算 M0 → M0 的中间结果仍要交给 GPU 2 的第 3–4 层
    计算 M2 → M2 的中间结果仍要交给 GPU 2 的第 3–4 层
```

这两条是必须完成的数据交接，不是一条同步执行时间线。**把两个微批分成一组，不会自动把它们合并成一次通信。** 在样本、张量形状和模型切分固定时，每个微批仍需经过相同的设备边界；不能从“切换片段更少”推出“传输的数据更少”。通信能否与其他计算同时进行，还取决于实际调度和通信重叠配置。[上游逐项前向与通信代码](https://github.com/NVIDIA/Megatron-LM/blob/core_v0.18.0/megatron/core/pipeline_parallel/schedules.py#L1529)

在微批足够多、配置合法的情况下，可以这样观察两种方向：

- **组较小**：同一片段先处理较少微批，前向列表更早转到其他片段。某个微批有机会更早继续走后面的层；如果所需中间结果尚未到达，就仍然需要等待。
- **组较大**：同一片段先处理更多微批，前向列表中的片段切换通常减少；部分后续片段的工作会排得更晚。上游调度中，组大小还影响开始反向计算前的前向任务数，因此可能需要保留更多等待反向使用的中间结果，占用更多显存。

上述是从执行顺序与预热逻辑得到的定性解释，不是本例的性能测量。实际吞吐取决于各段计算、通信和显存条件，不能单凭 mb_group 越大就判断越快。[顺序与预热逻辑](https://github.com/NVIDIA/Megatron-LM/blob/core_v0.18.0/megatron/core/pipeline_parallel/schedules.py#L822)

<details>
<summary>当前小例子的边界与参数约束</summary>

本例每个 DP 副本只有两个微批，PP=2。所核对的上游版本要求组大小位于 PP 与每副本微批数之间，所以此例只能取 2；它用于理解交接，不做 1 对 2 或 2 对 4 的调参实验。要比较组大小，需要另设足够多微批的场景。[上游约束](https://github.com/NVIDIA/Megatron-LM/blob/core_v0.18.0/megatron/core/pipeline_parallel/schedules.py#L1068)

</details>

接回当前函数，只先认出这两处使用：

```python
mb_group = train_parallel_config["microbatch_group_size_per_vp_stage"]  # 115
align_to = dp_size * (mb_group if vpp_size > 1 else 1)                   # 125
```

当前 Slime 用该值约束每个 DP 副本分到的微批数量：本例 DP=2、mb_group=2，总微批数按 4 对齐。M0–M3 共四个微批，分给两个副本后各两个，恰好满足要求。build_dp_schedule 生成数据分配计划，实际片段执行由训练端负责。这里先分清三个参数数什么；对齐分支的细节继续留在下方原有源码说明中。

<a id="context-parallel"></a>

### 6. CP：同一条序列内部怎样合作（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=1，VPP=1，mb_group=1，CP=2）

**这次的问题：即使一次只处理少量样本，其中一条序列太长，中间计算结果仍可能占用很多显存。** Micro-batch 控制每次处理几份样本；CP（Context Parallelism，上下文并行）进一步让多张 GPU 分担同一条序列中不同 token 位置的计算和中间结果存储。[NVIDIA 的 CP 说明](https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/features/context_parallel.html)

**本节从第 2 段的 DP 例子单独分出一条对照。** 使用同一个 8 层模型，将 PP、VPP、mb_group 都设为 1；然后只比较 CP=1 与 CP=2。这样能单独看清 CP 引入的变化。

```text
共同条件：batch size=8，micro_batch_size=2，DP=2，模型层数=8
          PP=1，VPP=1，mb_group=1

样本分组及归属                 CP=1：共 2 张 GPU     CP=2：共 4 张 GPU
副本 0：M0=[A,B]，M2=[E,F]     GPU 0                 GPU 0 + GPU 2
副本 1：M1=[C,D]，M3=[G,H]     GPU 1                 GPU 1 + GPU 3
```

两个 DP 副本仍各自处理分到的样本。改变的是每个副本内部：现在由两张卡共同处理这些样本。图中 GPU 编号用于延续前例，不规定实际进程 rank 的排列。

**放大副本 0 的 M0=[A,B]：每份样本暂用 4 个 token 表示。** 真实长序列使用同一种分工关系，4 个 token 只是便于看清位置。

```text
进入 CP 切分前：A=[a1,a2,a3,a4]，B=[b1,b2,b3,b4]

CP=1
  GPU 0：A 的 [a1,a2,a3,a4]，B 的 [b1,b2,b3,b4]

CP=2
  GPU 0（CP rank 0）：A 的 [a1,a4]，B 的 [b1,b4]
          ↕ 交换同一条序列的 attention 所需信息
  GPU 2（CP rank 1）：A 的 [a2,a3]，B 的 [b2,b3]

合作处理的样本仍是 M0=[A,B]，每份样本仍有原来的 4 个 token。
```

上面的 token 位置按本地 [slice_with_cp](/home/hongshi/projects/slime/slime/backends/megatron_utils/cp_utils.py:194) 的公式静态推导：CP=2 时分成四段，各 rank 取首尾对称的两段，用于平衡因果 attention 的工作量。本轮先观察“一份 A 的位置分给两卡”。这是 [get_batch 中 allgather_cp=False 的路径](/home/hongshi/projects/slime/slime/backends/megatron_utils/data.py:88)，只展示序列切分，省略后续拼接、补齐和其他 CP 路径；没有执行 GPU 训练。

**两张卡在这个例子里都持有第 1–8 层的参数。** 每经过一层，各自处理所负责的 token 位置；计算 attention 时协作取得其他位置所需的信息。例如 a4 需要前面的上下文，其中 a2、a3 的相关信息来自另一张卡。因此 A 仍作为一条完整序列参与训练，CP 分担的是序列内部的工作。

<a id="cp-and-attention"></a>

**CP 的整体分工，与 attention 的实现是什么关系？** 你提出的“需要能跨 GPU 并行的 attention 算法”抓住了关键实现环节。再补清范围：CP 沿 token 位置分配输入和中间表示，这个分工延续到模型各层；MLP 等计算也分别处理各卡负责的位置。

沿用 A 的例子，下面只对照同一层中两类计算，省略残差等步骤；a1 等表示对应 token 位置的中间表示：

```text
                     GPU 0：a1、a4             GPU 2：a2、a3
Attention            ← 交换所需信息，计算各自位置的输出 →
MLP                  本地处理 a1、a4          本地处理 a2、a3
```

MLP 可以逐 token 处理，当前卡已有自己的输入，就能计算对应输出。Attention 则需要同一序列其他位置的信息：例如 a4 的因果 attention 需要 a1、a2、a3，其中 a2、a3 在另一张卡。支持 CP 的 attention 实现负责安排所需信息的交换和计算，使分布在多卡上的计算仍遵守原来的 attention 关系。[NVIDIA 官方对序列切分与 attention 通信的说明](https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/features/context_parallel.html)

因此可以把两层关系连起来：**CP 决定各卡负责哪些 token 位置；支持 CP 的 attention 实现解决这些位置之间如何跨卡协作。** 具体通信算法留作实现细节，当前 build_dp_schedule 只使用训练配置，不在这里实现分布式 attention。

| 对照已有概念 | 分担的对象 | 用当前例子辨认 |
| --- | --- | --- |
| DP | 不同样本 | 副本 0 处理 A、B，副本 1 处理 C、D |
| PP | 模型的不同层 | 前例的一卡处理第 1–4 层，另一卡处理第 5–8 层 |
| CP | 同一条序列的 token 位置 | 本例的两卡都参与处理 A，各负责部分位置 |

**接回 build_dp_schedule：它只使用 CP 配置制定数据计划。** [113–120 行](/home/hongshi/projects/slime/slime/utils/dp_schedule.py:113)的相关语句是：

```python
cp_size = train_parallel_config["cp_size"]          # 113
# 省略此处其他配置读取；摘录 CP 相关语句
if args.use_dynamic_batch_size:                    # 118
    assert args.max_tokens_per_gpu is not None
    max_per_bin = args.max_tokens_per_gpu * cp_size # 120
```

当前 A–H 例子使用静态分批并关闭负载均衡，单独改变 CP 不改变 M0–M3 或它们的 DP 归属。动态分批时，上面的公式才把多路 CP 的能力计入每个微批的 token 预算。实际切分由训练端完成，build_dp_schedule 的返回值仍是索引和数量计划。

读到这里的观察点是：**样本归哪个 DP 副本，与同一份样本内部由几路 CP 合作，是两个不同的问题。** 接下来可回到本函数的配置和返回值；完整 attention 通信与训练实现继续按需回查。

<details>
<summary>后续怎样继续构建（回到配置与数据计划）</summary>

| 在已有例子上增加的条件 | 接着观察什么 |
| --- | --- |
| 对照微批、DP、PP/VPP、微批组和 CP 的含义 | 回到配置、数量对齐与 DP 分配，解释最终计划 |

这些是后续讲解的递进位置，不表示已经理解。每个环节继续在本卡中展示改变前后，最后接回 build_dp_schedule 的配置和返回值。

</details>

<details>
<summary>已保存的函数细节：配置、调度过程与两样本运行例子（后续回查）</summary>

<a id="parallel-config-preparation"></a>

### ⓪ 先读懂输入的训练约束（112–125）

基础例子已直接显示在本卡[上方正文](#batch-size-baseline)。这里保留此前的源码对照和完整调用场景；[并行概念的扩展参考](../parallelism-primer.md)供需要时查阅。

父函数传入的 `total_lengths=[3,4]` 表示第一份样本有 3 个 token、第二份有 4 个。它保存每份样本的完整长度，**还没有求和成 7**；这里的 total 指每份样本包含输入与响应的完整长度。

函数开头读取四项已有配置：

```python
dp_size = train_parallel_config["dp_size"]
cp_size = train_parallel_config["cp_size"]
vpp_size = train_parallel_config["vpp_size"]
mb_group = train_parallel_config["microbatch_group_size_per_vp_stage"]
```

| 变量 | 先理解到什么程度 | 在这个函数里影响什么 |
| --- | --- | --- |
| dp_size | Data Parallel Size，数据并行副本数量；不同副本处理不同样本 | 最终生成多少份 rank 分配；每个训练步的小批次要能分给这些 rank |
| cp_size | Context Parallel Size，同一条序列沿 token 维度由多少路协同处理；1 表示不启用此拆分 | 动态路径计算 `max_tokens_per_gpu * cp_size`，作为小批次的 token 预算 |
| vpp_size | Virtual Pipeline Parallel Size，每个物理流水线阶段持有多少个虚拟模型片段；片段可以交错执行 | 本函数检查它是否大于 1，以决定是否加入 mb_group 的数量约束 |
| mb_group | 一个虚拟流水线阶段按一组多少个 micro-batch 来调度，单位是“小批次数” | VPP 启用时，本实现要求每个 DP rank 的小批次数是它的倍数 |

DP 与 CP 的概念见 [Megatron 并行指南](https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/parallelism-guide.html)；VPP 的模型片段含义见 [parallel_state 官方说明](https://docs.nvidia.com/megatron-core/developer-guide/latest/apidocs/core/core.parallel_state.html#core.parallel_state.initialize_model_parallel)，微批分组含义见 [ModelParallelConfig](https://docs.nvidia.com/megatron-core/developer-guide/0.18.1/apidocs/core/core.model_parallel_config.html#core.model_parallel_config.ModelParallelConfig.microbatch_group_size_per_vp_stage)。表中本函数的具体约束以本地 Slime `18868a79` 为准。

理解 VPP 所需的最少前置：流水线并行把模型层分到不同阶段；VPP 让一个物理阶段持有多个模型片段并交错安排计算。本轮只认识这个配置含义，完整流水线时序仍留白。

**mb_group 与 micro_batch_size 的单位不同：** micro_batch_size=4 表示一个小批次有 4 份样本；mb_group=2 表示以 2 个小批次为一组安排虚拟阶段。

这些数在当前函数先落到两个计算中。下面节选 117–125，省略 max_tokens_per_gpu 的非空断言：

```python
max_per_bin = None
if args.use_dynamic_batch_size:
    max_per_bin = args.max_tokens_per_gpu * cp_size

align_to = dp_size * (mb_group if vpp_size > 1 else 1)
```

- max_per_bin 的单位是 **token**，用于动态小批次的打包。后面的具体打包分支决定怎样使用预算；不能据此宣称所有路径都严格限制显存。
- align_to 的单位是 **小批次数**。当前训练步的总小批次数 K 必须是这个基数的整数倍，之后每个 DP rank 得到 `K // dp_size` 个小批次。
- vpp_size 在这里起条件开关的作用，并不直接乘进 align_to。

下方原有主例仍用 `dp_size=2, cp_size=1, vpp_size=1, mb_group=1`：只有两个 DP 接收方，align_to=2；静态分批时不计算动态 token 预算。先读通这个场景，再按需要考虑额外并行约束。

<details>
<summary>需要时对照：两个独立的配置变化例子，以及配置从哪里来</summary>

- 动态分批例：max_tokens_per_gpu=8、cp_size=2 时，max_per_bin=16。这是调度时使用的预算计算，CP 的实际序列分工发生在训练实现中。
- 对齐例：dp_size=2、vpp_size=2、mb_group=2 时，align_to=4。总计 4 个小批次可以让每个 rank 分到 2 个；总计 6 个虽能均分为每人 3 个，却不满足本实现每人按 2 个一组的约束。后续动态分支尝试拆分小批次来对齐，静态分支不满足时会报错，不通过复制样本补齐。
- 这两个例子只解释公式，不是下方两样本主例的运行输出，也未执行 CP/VPP 训练。
- 配置来源：[训练端 actor.py:107–119](/home/hongshi/projects/slime/slime/backends/megatron_utils/actor.py:107)从 Megatron 取得并行规模，未启用 VPP 时将 vpp_size 与微批组大小视为 1；[set_rollout_manager:123](/home/hongshi/projects/slime/slime/ray/train_actor.py:123)传给 RolloutManager，再由 [set_train_parallel_config:572](/home/hongshi/projects/slime/slime/ray/rollout.py:572)放到 BatchBuilder 上。

</details>

<a id="batching-vs-dp-assignment"></a>

### 当前问题：组小批次和分给 rank 分别决定什么

| 决策 | 本实现的依据 | 源码 |
| --- | --- | --- |
| 哪些样本组成一个 micro-batch | 静态路径按 micro_batch_size 个样本切；动态且 balance_by_flops=False 时按 token 总预算 first-fit 装箱 | dp_schedule.py:55–79；seqlen_balancing.py:159–177 |
| 已组成的小批次分给哪个 DP rank | balance_data=False 时轮流分配；开启时按预计 FLOPs 尝试均衡负载 | dp_schedule.py:187–198 |

因此“长度相近”不是这里组 batch 的必要条件。各 rank 在同一个训练步得到相同**数量的小批次**，也不意味着得到完全相同数量的 token。调度先组小批次，再分给 rank；split_by_dp 根据结果选择实际字段并交付。

针对长度误解的[四样本小例子](../../04-flow.md#split-by-dp-purpose-and-batching)单独保留在本轮讨论中；下方继续沿用原有两样本主例，不混用两次配置。动态 FLOPs 分批分支、超长单样本和复杂对齐留待按需回查；token 预算不是所有路径都保证的显存上限。

<a id="two-sample-example"></a>

### 输入：接着前一张卡的两份样本

| 在整批数据中的位置 | rollout ID | 完整 token 长度 |
| --- | --- | --- |
| 0 | 10 | 3 |
| 1 | 20 | 4 |

本函数只需要长度与归属，不接收实际的 tokens、reward 或 mask。为看清分配，明确选择**固定大小的小批次、关闭负载均衡**；不将它当作所有作业的默认配置。

```python
from types import SimpleNamespace

args = SimpleNamespace(
    use_dynamic_batch_size=False,
    micro_batch_size=1,       # 一个小批次放一份样本
    balance_by_flops=False,
    balance_data=False,
)
train_parallel_config = {
    "dp_size": 2,             # 两个 DP rank
    "cp_size": 1,
    "vpp_size": 1,
    "microbatch_group_size_per_vp_stage": 1,
}
total_lengths = [3, 4]
global_batch_size = 2         # 一个训练步使用两个不同的 rollout
rollout_indices = [10, 20]
```

### 输出：四项一起返回

以下是上述固定配置下，隔离执行真实函数体得到的结果；完整输入与输出见[运行记录](../dp-schedule-example-output.json)。

```python
partitions = [[0], [1]]
micro_batch_indices = [[[0]], [[0]]]
num_microbatches = [1]
global_batch_sizes = [2]
```

| 返回项 | 本例怎样读 | split_by_dp 怎样使用 |
| --- | --- | --- |
| partitions | rank 0 取整批位置 0；rank 1 取整批位置 1 | 按这些位置取 tokens、rewards、loss_masks 等字段 |
| micro_batch_indices | 每个 rank 都只有一个小批次，其中包含本 rank 的位置 0 | 各取 `micro_batch_indices[rank]`，随该 rank 的数据交付 |
| num_microbatches | 这里只有一个训练步；该步每个 rank 都处理 1 个小批次 | 把同一份数量列表附到各 rank 的数据上 |
| global_batch_sizes | 这个训练步一共使用 2 个 rollout | 同样附到各 rank 的数据上；不是“每个 rank 有 2 份” |

**为什么 rank 1 的两处下标不同？** 它从整批数据的位置 1 取回一份样本；取回后，这份样本在自己的列表里位于 0。所以它的 partition 是 `[1]`，本地小批次是 `[[0]]`。

### ① 按 rollout 组织一个训练步（130–150）

下面是主干节选，省略检查、结果列表初始化和本段不涉及的语句。

```python
rollout_id_to_samples = {}
for sample_pos, rid in enumerate(rollout_indices):
    rollout_id_to_samples.setdefault(rid, []).append(sample_pos)
rollout_ids = list(rollout_id_to_samples.keys())
num_steps = len(rollout_ids) // global_batch_size
for step_i in range(num_steps):
    step_rollouts = rollout_ids[step_i * global_batch_size : (step_i + 1) * global_batch_size]
    sample_indices = [pos for rid in step_rollouts for pos in rollout_id_to_samples[rid]]
    step_lengths = [total_lengths[i] for i in sample_indices]
```

本例得到 `{10: [0], 20: [1]}`，只需一个训练步，使用位置 `[0, 1]`，长度为 `[3, 4]`。这里的训练步是模型更新流程的分批单位，不是阅读记录的 Step 编号。

### ② 先组成小批次，再分给 rank（158–198）

```python
step_mbs = _pack_step_into_mbs(
    step_lengths,
    args=args,
    use_dynamic_batch_size=args.use_dynamic_batch_size,
    max_per_bin=max_per_bin,
    micro_batch_size=getattr(args, "micro_batch_size", None),
    balance_by_flops=args.balance_by_flops,
)
# 此处经过小批次数量对齐检查；本例已有两个，无需改变。
K = len(step_mbs)
num_mbs_per_rank = K // dp_size
num_microbatches.append(num_mbs_per_rank)
# 本例 balance_data=False，摘取该分支：
rank_mbs_idx = [list(range(r, K, dp_size)) for r in range(dp_size)]
```

本例每个小批次装一份样本，得到 `step_mbs=[[0],[1]]`。两个小批次正好分给两个 rank：rank 0 分到第一个，rank 1 分到第二个。`rank_mbs_idx=[[0],[1]]` 此时表示**小批次编号**；随后还要转换为样本位置。

### ③ 写成分配表，返回父函数（202–209）

```python
for r in range(dp_size):
    for mbs_idx in rank_mbs_idx[r]:
        mbs_locals = step_mbs[mbs_idx]
        local_start = len(partitions[r])
        partitions[r].extend(sample_indices[i] for i in mbs_locals)
        micro_batch_indices[r].append(list(range(local_start, local_start + len(mbs_locals))))
return partitions, micro_batch_indices, num_microbatches, global_batch_sizes
```

partitions 保存整批位置；micro_batch_indices 从本 rank 已有数据的末尾继续编号。于是得到上面的四项结果。返回 [split_by_dp:498–523](../../02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#select-rank-fields)，它才执行字段选择并附上安排：

```python
value = {key: [data[key][index] for index in partition] for key in fields if key in data}
```

因此 rank 0 取回第一份样本的 tokens、reward、mask；rank 1 取回第二份对应字段。小批次安排随数据保留，实际训练在后续消费方发生。

</details>

## 我的直接表述（原话）

此前询问阅读深度：

> 我知道
> 那么这里是否需要简单理解一下这里关于build dp schedule部分的方法呢？
> 是否需要具体考虑一下呢？

本轮进一步要求具体内容：

> 我需要能够简单的理解 这里生成对应的split by dp的内容了吗？
> 我不是特别理解
> 给出这里需要的内容吧

目前明确的是用户需要接清调度结果与 split_by_dp 的关系；不能据“我知道”推定已理解索引结构。

2026-10-29，父函数带读之后：

> 好的先拿到总token
> 然后使用build dp schedule
> 那么是否需要看一下这里的build dp schedule呢？
> 也就是这里的dp size cp size vpp size 还有mb group 大概是什么意思呢？
> 是否需要了解一下这里的dp schedule部分应该怎么做呢？
> 否则我感觉对于这一块不了解 好像不太好？
> 是否需要按照这个先构造一个short term 函数来理解呢？

本轮沿用已有函数卡，补充输入配置阶段；用户的“总token”由助手校准为每份样本的完整长度列表，而非整个 batch 的长度总和，尚待反馈。

随后明确要求独立记录：

> 我觉得需要单独创建一个build dp schedule的short term memory 可以吗？

本卡沿用已建立的独立文件，保留前述原话与内容；确认记录形式不代表用户已经理解调度机制。

2026-10-29，尝试区分几种并行后，继续要求概念入门：

> 好的 我大概知道了这里的dp的意思
> 这里的dp 说的内容是 有多少条消息是并行进入的 说的是不同的样本
> cp说的是 同一条序列 沿着token由多少路协同处理 也就是同时处理一条序列
> vpp说的是虚拟流水线并行， 说的是model本身由多少个虚拟片段持有？
> mb group是什么我就不清楚了
> 我觉得这里这里应该有一个比较简单的概念入门讲解？
> 否则我这里根本就看不清楚并且不理解
> 这里的build dp schedule到底是如何实现的
> 我会觉得很困惑
>
> 我知道这是并行的时候考虑的不同的优化的方案
> 但是具体怎么做我觉得还是非常的模糊？

助手的本轮校准见 [概念入门](../parallelism-primer.md)：dp_size 数训练副本；vpp_size 数每个物理阶段持有的虚拟片段；mb_group 数一组调度中的小批次。先以 micro_batch_size=2 把 8 份样本组成 4 个小批次，再解释 DP 分配和一个副本内部的 PP/VPP。用户对这些校准尚未反馈。

随后对示例与起点的反馈：

> 我觉得例子 已经很不错了
> 但是在一开始我觉得是否应该都通过原始的例子来理解呢？
> 不能一开始直接这样给？
> 请从认知学专家的角度和科技大厂资深程序员的角度考虑应该如何设置这里的参数以及具体内容吧

用户认可例子，并要求重新考虑起点与参数安排，未明确表示已掌握各配置。助手将“原始例子”按无并行拆分的比较基准处理：固定原来 A–H、每份 4 个 token 和 8 层模型，先展示一个副本处理全部数据，再逐项比较；VPP 与配套 mb_group 的联动明确说明。详见 [本轮设计记录](../../04-flow.md#parallelism-baseline-and-parameter-progression)。

用户进一步纠正起点：

> 我觉得一开始应该连小批次这个概念都不包含？
> 毕竟我学习深度学习只是知道batch size 什么是小批次就很迷惑

明确的前置是用户知道 batch size，micro-batch 尚不清楚。此前把“每次两份”直接放入开头，已经预设了要讲解的拆分。入门第 0 节改为 batch size=8、整批一次交给模型；第 1 节才用显存限制引出分次计算。该调整不表示用户已理解梯度累积或后续并行配置。

用户随后指出找不到本地内容；助手核实完整说明此前位于 references/parallelism-primer.md，函数卡仅保存跳转链接。用户明确要求：

> 请直接在这里的markdown里面显示最基础的版本
> 我们需要的是
> 如何在这个基础之上一点点构建
> 否则根本就描述不清楚
> 就会出现问题

本轮把 batch size=8 的完整基础例子直接写入本卡“本场景的输入与输出”，默认显示；函数总览与已保存的深入内容折叠保留。后续在同一张卡、同一组 A–H 样本上逐次增加条件，不再将外部 reference 作为看到基础例子的必经入口。

随后用户理解 micro-batch 的动机，继续追问 DP 和展示方式：

> 好的我理解了
> 这里的micro batch 就是为了处理一次样本放不下的情况必须拆分成为不同的批次
> 我理解了
> 那么我们继续吧
> 那么现在的假设就是
> 我们目前已经使用了micro 对于一次性放不的样本
> 在这里的会需要通过分成多个小的样本
> 那么这里的dp呢
> 我可以理解为
> 之前都是通过一个gpu来训练的
> 现在dp就是变成两个gpu？
>
> 我们要不要在每一个标题这里给出这里的p的数量
> 放在最后或者怎么样
> 然后如果每次修改的话
> 或者了解了数据是怎么处理的情况
> 就在最后加上examples 到底是如何通过不同的批次来理解
> 这样子也能够对应上去你觉得呢？

本轮记录用户已理解分次计算的动机；助手进一步区分一批数据分组与单个样本被切碎。在本例每 GPU 一份完整模型、仅采用 DP 的前提下，DP=2 对应两张 GPU。三个可见标题标注 GPU 数量及当前配置，段末 Example 沿用 A–H；同步和副本概念仍待用户进一步反馈。

随后用户指出三组配置没有集中出现在 DP 结尾：

> 这里你是不是没写清楚呢？
> - 0. 整批计算（GPU=1，batch size=8）
> - 1. 分四次计算（GPU=1，micro_batch_size=2）
> - 2. 两个副本分担数据（GPU=2，DP=2，micro_batch_size=2）
>
> 我没有在dp的皆为看到这个

助手核对后，将完整三行配置集中补到本卡 DP 段末；原参考页的 DP 段末也同步补上。原来各节标题和数量表保留，本次是呈现位置修正，不代表新增理解。

用户随后澄清希望保留标题配置，并在开头列出增量：

> 不是 我觉得你放在 标题上面也很好 最好在开头给一个列表
> 这样子就能非常清楚每一步到底加入了什么内容 我觉得这个比较重要

本轮在 Markdown 开头加入三项可跳转总览，分别标明基准、增加分次计算、增加第二个完整模型副本；全程保持同一批 A–H 和一次更新共 8 份样本。各节配置标题与段末例子继续保留。

用户随后确认已大致理解，并要求移除段末重复回顾：

> 好的我大概理解了
> 这里也就是说明这里的数据是data parallel的
> 所以一个副本并不需要都在一个gpu上跑是这个意思吗？
>
> 把dp部分段落结尾的部分去掉吧
> 我觉得这里理解的差不多了？

用户已初步区分数据并行副本与 GPU 数量。助手确认：DP 决定不同副本如何分担数据，一个副本内部可以借助其他并行方式由多张 GPU 协作承载；前面的例子特意采用每张 GPU 一份完整副本。按要求删除段末“三个版本的配置回顾”，开头增量列表、正文标题、Example 和数量表保留。

继续阅读第 3 部分时，用户尝试理解按层划分并要求标题点明概念：

> 那么3这里尝试在讲什么
> 这里是按照模型按照层数
> 把不同的模型按照层封给不同的物理阶段？
> 这样子单块gpu上方的模型就可以只是某一个层的一个部分了对吗？
> 我是这么理解的
> 也就是这样每一个显卡就可以只是存储比较小的一个层我是这么理解的
>
> 同时这里的第二各讲述的是dp 起码出现dp吧
> 以及第一个标题讲述的是batch 起码把batch 写上吧？

助手校准：PP 按层划分的是同一个模型副本，本例每张卡承担四个完整层，而不是把一个层内部切小。标题和开头目录改为显式标明 Batch、Micro-batch、DP、PP；在同一函数卡内继续 A–H 的例子，展示 DP=2、PP=2、每阶段一张卡时的四卡布局。用户对这次校准尚未反馈。

随后，用户尝试区分 VPP 的模型片段，并要求把配置和模型总层数放在同一个例子里：

> vpp感觉就像是一个数据在不同的层上面进行处理
> 本来会觉得这里具体的物理阶段持有多端虚拟模型片段我觉得这里就很好理解了
> vpp 应该说的是一个gpu里面可能不只是有模型的一个层？
> （如果单纯只是通过pp来切分）
> 更多的是一个gpu可能有模型的多个片段？
> 要不要在这里vpp上写清楚这里的配置呢？
> 也就是关于gpu和dp和pp的数字以及和上面的具体的关系之类
>
> 或者引入模型总层数这个参数？
> 我不是特别清楚
> 请你从认知学家和资深llm工程师的角度来判断吧

助手据此在 PP 节固定模型为 8 层，在 VPP 节保持 GPU=4、DP=2、PP=2 和数据分组，用同设备前后对照展示一段四层如何变成两段各两层，再追踪 M0 的路径。普通 PP 的单个阶段已经可以持有多层；VPP 进一步让每个物理阶段持有多个模型片段。用户对这次具体区别尚未反馈。

用户进一步纠正标题的配置不能省略：

> 这里的标题怎么就变回去了呢？
> 我的意思是这里的标题必须要有对应的设置才行 关于dp pp batch gpu数量

按这次明确要求，所有场景标题保留 GPU、DP、PP、整批 batch size；从分次计算起写出 micro_batch_size，PP/VPP 段写出模型层数与 VPP。开头列表与正文使用同一标题。此次是展示修正，未新增技术理解或改变例子配置。

用户随后明确参数应随概念逐次出现：

> 只有在每一次怎加一个新的概念的时候才会出现对应的（）里的内容
> 这样子能够将内容和example清晰对应起来

上一轮在开头就写出 DP=1、PP=1，是助手将配置要求展开得过早。本轮改为：Batch 只列 GPU 与 batch size；Micro-batch 加入 micro_batch_size；DP 加入 DP；PP 加入模型层数和 PP；VPP 再加入 VPP。已经引入的配置继续保留，并对应当前例子的数值。此次仍是展示规则澄清，阅读位置和技术理解状态不变。

用户回顾当前位置，并提出“层复用”的理解：

> 好的 那么 我们目前说到哪里了呢？
> 我们现在说清楚了pp 也知道了 vpp大概是干嘛的？
> vpp的概念大概就是一个模型可能同时拥有不同的层？
> 例如一个mlp 但是因为transformer的原因需要按照这样子来复用造出来的？
> 我是这么理解的
> 见来说要么model层复用了
> 那么看完了vpp我们应该看什么了呢？

助手继续用同一个八层模型校准：GPU 0 在一份数据的前向过程中先执行第 1–2 层，稍后执行第 5–6 层；同一设备被再次使用，模型中的不同层保持各自身份，VPP 不要求它们共享参数。建议下一处关注 mb_group 所描述的微批组安排，再回到 build_dp_schedule 的对齐约束；目前是推荐，尚未开始该段带读。

<a id="vpp-confirmed-statement"></a>

2026-10-29，用户明确要求原样记录上一轮确认的表述：

> 好的 把这句话精准的记录下来吧
> VPP 这里是同一张 GPU 在不同时间执行模型中的不同层

这里记录用户确认的这一句话；完整交错调度的理解状态保持原样。

用户接着确认继续阅读 mb_group，并说明当前问题：

> 好的 我们继续吧
> 这里mb group 又是什么呢？
> 我的意思是和别的部分有什么区别呢？
> 我不是特别理解了？这里的内容

助手沿用同一批 A–H、两个 DP 副本和八层模型，区分 micro_batch_size 数样本、VPP 数模型片段、mb_group 数调度组里的微批。当前只展开 GPU 0 对 M0、M2 的前向计算项；完整通信与反向时间线保留边界。用户对这一解释尚未反馈。

用户表示理解前一段，并进一步追问调度的目的：

> 好的 我理解了 那么 我们继续吧
> 我可以理解为这里是在切换的过程中能够在通信和切换之间达到权衡的一种方式吗？
> 这里的mb group？
> 我不是特别理解了

助手认可“调度粒度存在性能权衡”的方向，补清分组直接改变执行次序与时机；每个微批仍有跨设备的数据交接，片段切换减少不能直接推出通信量减少。前向预热和中间结果占用也参与权衡。这个作用层面的理解尚待用户反馈，前一段“已理解”的反馈保留。

用户随后反馈并明确指定继续 CP：

> 好的 我大概理解了 那么继续推进这里的cp部分吧

这里把前一段 mb_group 的反馈记为“大概理解”，不扩展为完整性能分析能力。助手从第 2 段的 DP 例子另作对照，固定 PP=1、VPP=1、mb_group=1，展示 CP=1 → 2 后同一份样本的 token 分工。CP 的具体理解尚待用户反馈。

用户进一步将 CP 的实现与 attention 联系起来：

> 简单来说这里的cp的内容说的是这里的在cp的条件下是一个attention中需要处理的内容是我的理解
> 内部应该是根据attention开发的能够在不同gpu上这样并行的算法是我的理解？

助手保留其中“需要支持跨 GPU 协作的 attention 实现”的方向，并补清 CP 的范围：各卡负责的 token 位置也贯穿 MLP 等计算，attention 需要特别处理位置之间的信息依赖。这一范围校准尚待用户反馈，具体通信算法未展开。

## 尚不清楚

- 用户已理解 micro-batch 的分次计算动机；“一批样本分组而非把单个样本切碎”的区别、梯度累积与归一化尚待反馈。
- 用户已确认同一 GPU 在不同时间执行模型中不同层的表述；完整交错调度、层参数共享等进一步机制没有据此标为掌握。此前“层复用”的疑问及校准过程保留在原话记录中。
- 梯度同步、流水线通信与反向传播实现没有展开，不从布局图推断已经掌握。
- 用户是否已分清整批位置、rank 内位置和两个数量列表，仍待反馈。
- 用户对前一段 mb_group 讲解反馈“大概理解了”；完整交错调度及性能分析未展开。用户已把 CP 与 attention 的跨 GPU 实现联系起来；CP 分工也贯穿 MLP 等计算的范围校准，以及计划与实际切分的区别仍待反馈。未进行性能测试。
- 动态装箱、FLOPs 估算、负载均衡，以及 CP/VPP 的实际执行与通信细节暂留黑箱。
- 本例恰好组成完整训练步。源码只处理凑够 global_batch_size 个 rollout 的完整步；不足一个完整步会断言，末尾不完整部分不会进入返回安排。此边界未做运行演示。
- 隔离运行只覆盖上述静态调度路径；split_by_dp、张量化、Ray 和训练没有在本例执行。

<details>
<summary>来源、验证与完整例子</summary>

- [Step 016 本轮形成过程](../../04-flow.md#build-dp-schedule-concrete-handoff)。
- [2026-10-29 配置前置与长度列表的澄清](../../04-flow.md#build-dp-schedule-parallel-config)。
- [独立函数卡的明确确认](../../04-flow.md#build-dp-schedule-independent-card)。
- [从并行概念到微批组的入门补充](../../04-flow.md#parallelism-primer-and-microbatch-groups)。
- [固定原始场景与参数递进](../../04-flow.md#parallelism-baseline-and-parameter-progression)。
- [用户纠正：开头只从 batch size 出发](../../04-flow.md#batch-size-before-microbatch)。
- [基础版本直接显示在函数卡正文](../../04-flow.md#baseline-inline-in-function-card)。
- [从单卡 micro-batch 到两个 DP 副本：标题配置与段末例子](../../04-flow.md#microbatch-to-dp-examples)。
- [固定八层、四卡，对照 PP 与 VPP 的模型片段](../../04-flow.md#vpp-fixed-model-and-device-layout)。
- [VPP 层复用疑问与下一处推荐](../../04-flow.md#vpp-device-versus-layer-reuse)。
- [mb_group：样本数、模型片段数与调度组微批数](../../04-flow.md#microbatch-group-versus-other-counts)。
- [mb_group：调度时机与通信量的区别](../../04-flow.md#microbatch-group-tradeoff)。
- [CP：从 DP 例子分出序列内合作的对照](../../04-flow.md#context-parallel-from-dp)。
- [CP 整体分工与 attention 跨卡实现的区别](../../04-flow.md#cp-and-attention-scope)。
- 固定源码：dp_schedule.py:82–209；静态小批次辅助路径为 55–79；实际调用方 batch_builder.py:457–463，字段选择和安排交付为 498–523。
- [示例脚本](../run-dp-schedule-example.py)通过 AST 提取上述两个函数的原始函数体，不改写实现；用固定配置执行，未导入整套训练依赖，未执行动态分支或负载均衡。
- [实际输出](../dp-schedule-example-output.json) · [源码证据](../source-evidence.json)。父卡最初采用假设分配表，本轮新增固定配置的独立运行证据，不将此前静态推导改写为实际执行。

</details>
