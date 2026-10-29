# 从 batch size 开始理解并行配置

<a id="progressive-overview"></a>

## 开头总览：每一步新增什么

始终沿用同一批 A–H；每次训练更新总共使用 8 份样本。

标题只列截至本节已经引入的配置；新概念出现时，再将对应参数加入括号。已引入的参数继续保留，数值与本节 example 一致。

- **[0. Batch：整批计算（GPU=1，batch size=8）](#baseline)**：建立基准，一张 GPU 一次计算整批 8 份样本。
- **[1. Micro-batch：分四次计算（GPU=1，batch size=8，micro_batch_size=2）](#sample-and-microbatch)**：在第 0 步上增加**分次计算**；仍用一张 GPU，每次计算 2 份，四次共同完成一次更新。
- **[2. DP：两个副本分担数据（GPU=2，batch size=8，micro_batch_size=2，DP=2）](#data-parallel)**：在第 1 步上增加**第二个完整模型副本**；原来的四组分给两张 GPU，每张处理两组，共同完成这次更新。
- **[3. PP：同一模型按层分到两个阶段（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2）](#pp-two-stages)**：在第 2 步上增加**副本内部按层分工**；仍有两个 DP 副本，每个副本由两张 GPU 分别承担前后两段模型。
- **[4. VPP：每个物理阶段持有两个模型片段（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2，VPP=2）](#vpp-model-chunks)**：在第 3 步上增加**每个物理阶段的模型片段数**；沿用同一个 8 层模型和 4 张 GPU，对照每张卡持有哪些层。
- **[5. mb_group：同一个虚拟片段按几个小批次一组来安排（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2，VPP=2，mb_group=2）](#microbatch-group)**：接着第 4 步展开**微批的调度分组**；已有模型片段和样本保持不变，观察同一片段怎样按两个微批为一组安排。

- **[6. CP：同一条序列内部怎样合作（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=1，VPP=1，mb_group=1，CP=2）](#context-parallel)**：从第 2 段另作对照，增加**同一条序列内部的 token 分工**；每个 DP 副本由一张卡改为两张卡合作，总 GPU 从 2 变为 4。

---

本文件集中保存并行概念的完整入门例子，供回查参数含义；[build_dp_schedule 函数卡](../02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md#schedule-flow)保存实际源码步骤和输入输出。**先从熟悉的 batch size 开始，每次引入一个新概念；回到函数时沿源码骨架阅读。**

<a id="baseline"></a>

## 0. Batch：整批计算（GPU=1，batch size=8）

我们有 8 份训练样本 A、B、C、D、E、F、G、H，把它们组成一个 batch。**batch size = 8，就是这一批有 8 份样本。**

先假设一张 GPU 放得下完整模型，也能一次计算这整批数据：

```text
[A,B,C,D,E,F,G,H]   一个 batch，batch size = 8
        ↓
     完整模型
        ↓
   计算这批数据的 loss
        ↓
  反向传播，更新一次参数
```

**第一处停点：先看清这一个 batch 怎样交给模型。** 这里没有把 A–H 分成几组，也不要求先认识后面的并行参数。下一节才提出显存容量带来的新问题。

<a id="sample-and-microbatch"></a>

## 1. Micro-batch：分四次计算（GPU=1，batch size=8，micro_batch_size=2）

现在改变一个条件：一次只能计算 2 份样本，但仍希望用这 8 份样本共同完成一次参数更新。可以先把同一个 batch 分成四组，分次计算：

```text
原来：一次计算 [A,B,C,D,E,F,G,H]，然后更新一次

现在：计算 [A,B] → [C,D] → [E,F] → [G,H]
      累积各组的梯度，最后再更新一次
```

分次计算共同服务于一次更新，需要梯度累积；累积与归一化的具体实现后续再读。这里保留的是“这次更新使用 8 份样本”，并非把四组分别当成四次参数更新。[PyTorch 梯度累积说明](https://docs.pytorch.org/docs/main/notes/amp_examples.html#gradient-accumulation)

**看到这个需求之后，才引入名称：每次计算的一组叫 micro-batch（小批次）。** 本例每组有 2 份样本，因此 `micro_batch_size=2`；为后续跟踪方便，把这四组标成 M0–M3：

```text
一个训练步的样本：A  B  C  D  E  F  G  H

小批次 M0 = [A, B]       小批次 M1 = [C, D]
小批次 M2 = [E, F]       小批次 M3 = [G, H]

8 份样本 → 4 个小批次；每个小批次含 2 份样本。
```

固定分批对应 [_pack_step_into_mbs:77–79](/home/hongshi/projects/slime/slime/utils/dp_schedule.py:77)；动态分批则按另一个打包规则组织样本，不要求每个小批次都有固定样本数。**本函数只生成分批计划，梯度计算、累积与参数更新发生在训练端。**

<a id="data-parallel"></a>

## 2. DP：两个副本分担数据（GPU=2，batch size=8，micro_batch_size=2，DP=2）

接着上一节的四组数据：它们目前都由同一个训练副本处理，记作 `dp_size=1`。**本段将它改为 2：增加一个数据并行训练副本。** 样本、模型和每个小批次的组成保持相同。每个副本负责完整模型的计算，分担不同的数据，再通过梯度同步协同训练同一个模型。一个副本也可以由多张 GPU 合作承载。

在这个例子中，关闭负载均衡后，Slime 轮流分配已经组成的小批次：

```text
改变前 dp_size=1：
  副本 0：M0 → M1 → M2 → M3

改变后 dp_size=2：
  副本 0：M0=[A,B] → M2=[E,F]
  副本 1：M1=[C,D] → M3=[G,H]

每个副本有自己的数据；每份样本仍需经过完整模型。
```

这里有 **2 个副本、8 份样本、4 个小批次**。dp_size 数的是副本；具体一批有多少样本、同时处于计算中的数据量，还由批次和流水线安排决定。[DP 官方说明](https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/parallelism-guide.html)

<a id="pp-and-vpp"></a>
<a id="pp-two-stages"></a>

## 3. PP：同一模型按层分到两个阶段（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2）

保留上一段的两个 DP 副本和各自的小批次，先只放大副本 0。现在要追踪模型的内部划分，为方便标注，把同一个模型具体画成 8 层。每个物理阶段用一张 GPU，CP 仍为 1。

**固定模型背景：每个副本都包含同样的 8 个 Transformer 层；下一节 VPP 继续使用这 8 层。** 示意只画这些层，省略词嵌入与输出头。模型层数用来标清如何切段，不是 build_dp_schedule 的新增参数。

**PP（Pipeline Parallel）把同一个模型副本按层分给不同物理阶段。** 本例每阶段持有四个完整层，是模型的一部分，不是单层内部的一部分。本段先将 `PP=1` 改为 2：

```text
改变前 PP=1：M0 → P0[第 1–8 层]
改变后 PP=2：M0 → P0[第 1–4 层] → P1[第 5–8 层]

M2 经过相同路径；M0、M2 仍属于 DP 副本 0。
```

M0 进入 P1 后，P0 有机会处理后续的小批次，让不同阶段同时有工作。一个副本仍包含完整模型，只是分开放置；另一个 DP 副本有相同布局。PP 用来分担模型的计算和存储，流水线安排则利用不同小批次填充各阶段。[PP 官方说明](https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/parallelism-guide.html)

**Example · 放回两个 DP 副本的完整布局**

```text
副本 0：M0、M2 → GPU 0 [第 1–4 层] → GPU 2 [第 5–8 层]
副本 1：M1、M3 → GPU 1 [第 1–4 层] → GPU 3 [第 5–8 层]

DP=2：两个模型副本，处理不同数据。
PP=2：每个副本分成两个阶段，同一组数据依次经过两段。
每阶段一张 GPU，因此总共 4 张 GPU。
```

箭头传递前一阶段的中间结果，每份样本仍经过全部 8 层。GPU 编号只是教学标签；模型的一段可能包含一层或多层，本例选择四层方便对照。这里只画前向路径，不展开反向和通信实现。这一完整布局在本节维护，函数卡按需链接回来。

<a id="vpp-model-chunks"></a>

## 4. VPP：每个物理阶段持有两个模型片段（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2，VPP=2）

**VPP 增加的是每个物理阶段持有的模型片段数。** 一个片段可以包含多层；普通 PP 中一张 GPU 已经可以持有多层。要观察变化，固定上一节的模型、设备和数据：

```text
模型：每个副本都是 8 层
设备：DP=2，PP=2，每个物理阶段 1 张 GPU，总共 4 张 GPU
数据：副本 0 处理 M0、M2；副本 1 处理 M1、M3
变化：每个物理阶段从 1 个模型片段变成 2 个，记为 VPP=1 → 2
```

**Example · 同一设备在两种配置下持有的层**

| 模型副本与设备 | 上一节：PP=2，VPP=1 | 本节：PP=2，VPP=2 |
| --- | --- | --- |
| 副本 0 · GPU 0 | 一段：[1–4 层] | 两段：[1–2 层]、[5–6 层] |
| 副本 0 · GPU 2 | 一段：[5–8 层] | 两段：[3–4 层]、[7–8 层] |
| 副本 1 · GPU 1 | 一段：[1–4 层] | 两段：[1–2 层]、[5–6 层] |
| 副本 1 · GPU 3 | 一段：[5–8 层] | 两段：[3–4 层]、[7–8 层] |

每个副本有 `PP × VPP = 2 × 2 = 4` 个片段，本例每段 `8 ÷ 4 = 2` 层。每张卡持有两段，合计仍是四层；每个副本仍由两张卡承载，两个副本总计四张 GPU。这个布局由 [Megatron 官方 VPP 层分布示例](https://docs.nvidia.com/megatron-core/developer-guide/latest/apidocs/core/core.parallel_state.html#core.parallel_state.initialize_model_parallel)缩小得到。

只看 M0=[A,B] 的前向路径，层的计算顺序保持 1→8：

```text
上一节：M0 → GPU 0 [1–4 层] → GPU 2 [5–8 层]

本节：  M0 → GPU 0 [1–2 层] → GPU 2 [3–4 层]
                            → GPU 0 [5–6 层] → GPU 2 [7–8 层]
```

GPU 0 第二次接到的是中间结果，接着执行第 5–6 层。VPP 为不同小批次在各片段上的交错调度提供更细的单位，以减少流水线空闲；具体收益仍取决于调度和通信。这里没有画多批次时间线或反向传播，也没有运行训练。这一完整例子在本节维护，函数卡只保留配置用途和回查入口。

**这里再次使用的是同一张 GPU；两次执行的是不同的层。** 在上例中，GPU 0 第一次执行第 1–2 层，再次接到中间结果时执行第 5–6 层。第 5–6 层仍是另外两层，VPP 不会把它们替换成第 1–2 层，也不要求这两段共享参数。

一个模型原本就可以包含多层；层内部采用 MLP、Attention 等结构，与这些层怎样分配到设备是不同的问题。这里先把模型看成已有的第 1 到第 8 层：VPP 调整片段的放置和交错执行安排，模型的这条层次顺序保持不变。

本例进入 VPP 场景时，配套明确采用 `mb_group=2`，含义在下一段观察。这里一次新增的是 VPP 机制，完整配置存在联动：Slime 未启用 VPP 时给调度函数的 mb_group 为 1，启用后读取训练模型配置，见 [actor.py:107–119](/home/hongshi/projects/slime/slime/backends/megatron_utils/actor.py:107)。不把这两种完整配置描述成严格只改了一行参数。

<a id="microbatch-group"></a>

## 5. mb_group：同一个虚拟片段按几个小批次一组来安排（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=2，VPP=2，mb_group=2）

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

当前 Slime 的数量对齐用途见[函数卡的数量约束](../02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md#parallel-config-preparation)；这里保存概念对照，不将局部前向安排视为完整训练时间线。

<a id="context-parallel"></a>

## 6. CP：同一条序列内部怎样合作（GPU=4，batch size=8，micro_batch_size=2，DP=2，模型层数=8，PP=1，VPP=1，mb_group=1，CP=2）

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

CP 在调度函数中具体怎样参与预算，见 [build_dp_schedule 的配置约束](../02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md#parallel-config-preparation)。本节保留序列内分工的概念，函数源码与实际返回值集中在函数卡。

<a id="back-to-schedule"></a>

## 7. 回到 build_dp_schedule：配置怎样约束数据计划

**训练端已经决定模型的分布与执行方式；build_dp_schedule 根据这些既定配置，为数据制定分批与分配计划。**

到这里才把各个场景翻译为完整参数。表里的 PP 是模型布局背景；其他参数对应分批或本函数收到的配置。所有行使用同一批 8 份样本、静态分批和关闭负载均衡。第一行是用已经学到的术语回看第 0 节，后续才把一次计算的样本数从 8 改为 2。

| 场景 | micro_batch_size | dp_size | cp_size | PP | vpp_size | mb_group | 每个 DP 副本的小批次数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 原始基准：整批一次计算 | 8 | 1 | 1 | 1 | 1 | 1 | 1 |
| 同一批数据分四次计算 | 2 | 1 | 1 | 1 | 1 | 1 | 4 |
| 增加 DP 副本 | 2 | 2 | 1 | 1 | 1 | 1 | 2 |
| 每个副本内启用 PP | 2 | 2 | 1 | 2 | 1 | 1 | 2 |
| PP 上启用 VPP，明确配套微批组 | 2 | 2 | 1 | 2 | 2 | 2 | 2 |
| CP 独立对照：从 DP 场景分出 | 2 | 2 | 2 | 1 | 1 | 1 | 2 |

PP 那行的 mb_group=1 是 Slime 未启用 VPP 时传给调度函数的值；不据此推断 Megatron 模型配置对象也使用 1。CP 行是独立对照，不是接在 VPP 场景之后累加。

接下来回到 [build_dp_schedule 的核心骨架](../02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md#schedule-flow)，依次看配置约束、训练步归属、组微批、分给 rank、写出索引。函数卡沿用 A–H，并采用上表 VPP / mb_group 一行的配置；其 [实际输入与返回值](../02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md#eight-sample-example)已经隔离运行核对。

本 reference 解释“这些配置是什么意思”；函数卡解释“源码怎样用这些配置算出结果”。同一段函数流程不再两处维护。

<details>
<summary>证据与本轮边界</summary>

- A–H、每份 4 个 token 和 8 层模型是整篇沿用的教学设定。8 份样本便于后续按 2 份分组、再交给两个副本；8 层便于展示 PP/VPP，统一长度暂时避开负载差异。开头只展示 batch size，其他设定到实际使用时才展开。
- 原始基准现在是整批 8 份一次计算；此前每次处理 2 份的场景保留在后续第 1 节。这里的“原始”指教学比较基准，不表示 Slime 的历史版本或实际任务的默认配置。
- 这些教学示意与函数卡原有的两样本运行例子分别保留。一次更新共同使用 8 份样本不等于已经验证两种实现的数值结果相同；本轮没有运行训练或梯度累积。
- 展示方式依据：先稳定具体对象，再将参数名、图和变化对应起来。[IES 学习与教学指南](https://ies.ed.gov/ncee/wwc/PracticeGuide/1)建议结合具体与抽象表达、图示与文字。将这些原则落实为本例的固定基准和逐项对照，是针对当前困惑的教学设计。
- 8/4/8 的数字与静态分批是为了便于观察的教学选择；完整配置表不等于集群启动配置，不用于证明性能提升。模型能否装入设备、通信与训练结果均未在本例实测。
- 术语对照上文链接的 NVIDIA 官方文档；层分布和任务顺序为缩小后的教学示意。
- Slime 固定版本：18868a79b0b083a093798a94ed0f8cb4f71b9c14；本轮核对 dp_schedule.py:55–209。
- 上文模型布局与训练过程为教学示意。2026-10-29 返回函数逻辑时，A–H 的静态调度已单独执行原始函数体核对，结果见 [八样本运行记录](dp-schedule-eight-samples-output.json)；未执行 CP、PP、VPP 或多卡训练。原两样本局部运行证据继续保留。
- [CP 序列内合作的本轮讨论](../04-flow.md#context-parallel-from-dp)；token 位置静态核对本地 get_batch 与 slice_with_cp，未运行 GPU 或 attention。
- [本轮讨论](../04-flow.md#parallelism-primer-and-microbatch-groups)保存用户的困惑与讲法调整；[源码证据](source-evidence.json)记录核对范围。本文由助手整理，不代表用户已经掌握。
- [VPP 的固定模型与设备对照](../04-flow.md#vpp-fixed-model-and-device-layout)保存本次增补理由：在 PP 处具体标注 8 层，在 VPP 处固定 GPU/DP/PP，按同一设备对齐前后层分布；层数均分与 GPU 标签均为教学设定。

</details>
