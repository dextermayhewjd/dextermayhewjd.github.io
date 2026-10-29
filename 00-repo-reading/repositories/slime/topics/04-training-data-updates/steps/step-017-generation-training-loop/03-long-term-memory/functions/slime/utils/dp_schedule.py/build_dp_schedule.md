# build_dp_schedule

- 卡片定位：Step 016 中单独保存的函数短期记忆。只解释调度计划怎样产生；实际字段选择与交付回到 [BatchBuilder.split_by_dp](../../data/batch_builder.py/BatchBuilder.split_by_dp.md#prepare-schedule)。
- 源码定位：[slime/utils/dp_schedule.py:82](/home/hongshi/projects/slime/slime/utils/dp_schedule.py:82)，固定版本 `18868a79`，由助手核对。
- 首次接触：Step 016，2026-10-28；先定位接口，本轮补充具体输入输出。
- 最近认识更新：2026-10-29，用户尝试将本函数概括为计算各训练 GPU 应得的样本，并询问之后还缺什么；助手校准为给各 DP 副本制定样本和微批计划，建议返回父函数接通取字段、附安排及返回引用。当前职责概括已出现，物理 GPU 与 DP 副本及此前计数的校准仍按后续反馈记录。
- 导航：**[当前定位：计划完成后返回哪里](#return-to-parent)** · [回看计数单位](#return-count-units) · [A–H 的完整主线](#schedule-flow) · [输入](#eight-sample-example) · [①约束](#parallel-config-preparation) · [②选样本](#step-sample-positions) · [③组微批](#pack-step-microbatches) · [④分微批](#assign-step-microbatches) · [⑤写索引](#encode-rank-plan) · [四项返回值](#schedule-return-values) · [并行概念参考](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md) · [返回 split_by_dp](../../data/batch_builder.py/BatchBuilder.split_by_dp.md#prepare-schedule)。

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


## 本场景的输入与输出

这里要解决的是：**八份样本已经准备好，怎样安排两个 DP rank 各自处理哪些微批？** 函数收到的是长度、rollout 归属和配置；它返回索引计划。实际 tokens、reward、mask 留在调用方，之后由 split_by_dp 按计划取出。

<a id="schedule-flow"></a>

### 核心骨架：跟着同一批 A–H 走一遍

```text
调用方已有 A–H 的训练字段
    ↓ 只传入长度、rollout ID 和训练配置
① 算约束         → 本例总微批数须为 4 的倍数         112–125
② 选本训练步样本 → 本例选择 A–H                      130–150
③ 组微批         → M0=[A,B]、M1=[C,D]、M2=[E,F]、M3=[G,H]  158–185
④ 分微批给 rank  → rank 0 得 M0/M2；rank 1 得 M1/M3  187–198
⑤ 写成索引计划   → 整批位置 + rank 内位置 + 数量      202–209
    ↓
调用方 split_by_dp 按计划取出实际训练字段
```

下面每段先放源码，再显示这段产生的数据。③–⑤位于②的训练步循环内部，节选时去掉一层缩进；当前只跟随静态分批、关闭负载均衡的路径。

<a id="eight-sample-example"></a>

### 输入：样本名字用于对照，函数实际收到长度和编号

```text
样本名字（用于说明）： A  B  C  D  E  F  G  H
在整批数据中的位置：  0  1  2  3  4  5  6  7
rollout_indices：     0  1  2  3  4  5  6  7
完整 token 长度：     4  4  4  4  4  4  4  4
```

本例一个 rollout 对应一个样本，rollout ID 恰好与位置相同；ID 表示归属，位置用来取列表里的数据，两者职责不同。

| 输入配置 | 本例取值与用途 |
| --- | --- |
| global_batch_size | 8：这个训练步使用八个 rollout |
| micro_batch_size | 2：一个微批放两份样本 |
| use_dynamic_batch_size / balance_data / balance_by_flops | 都为 False：按样本数分批，微批轮流分给 rank |
| dp_size / cp_size / vpp_size / microbatch_group_size_per_vp_stage | 2 / 1 / 2 / 2：沿用前面 VPP 与 mb_group 的例子 |

把最终计划翻成样本名字，应当读成：rank 0 先处理 A、B，再处理 E、F；rank 1 先处理 C、D，再处理 G、H。**下面跟踪代码怎样得到这张表。**

<a id="parallel-config-preparation"></a>

### ① 先算后面分批要满足的约束（112–125）

```python
dp_size = train_parallel_config["dp_size"]
cp_size = train_parallel_config["cp_size"]
vpp_size = train_parallel_config["vpp_size"]
mb_group = train_parallel_config["microbatch_group_size_per_vp_stage"]

max_per_bin = None
if args.use_dynamic_batch_size:
    assert args.max_tokens_per_gpu is not None
    max_per_bin = args.max_tokens_per_gpu * cp_size

align_to = dp_size * (mb_group if vpp_size > 1 else 1)
```

- 本例静态分批，所以 max_per_bin=None，不使用动态 token 预算。
- align_to=2×2=4，表示**总微批数须为 4 的倍数**：两个 rank 各自分到的微批数才能是 2 的倍数。
- 此时还没有微批，只算出约束。vpp_size 在这里判断是否大于 1，数值本身不参与乘法；PP 的实际执行由训练端负责。

<a id="step-sample-positions"></a>

### ② 确定这个训练步处理哪些样本（130–150）

下面省略容器初始化和检查，保留归属及取样关系：

```python
rollout_id_to_samples: dict[int, list[int]] = {}
for sample_pos, rid in enumerate(rollout_indices):
    rollout_id_to_samples.setdefault(rid, []).append(sample_pos)
rollout_ids = list(rollout_id_to_samples.keys())
num_steps = len(rollout_ids) // global_batch_size

for step_i in range(num_steps):
    step_rollouts = rollout_ids[step_i * global_batch_size : (step_i + 1) * global_batch_size]
    sample_indices = [pos for rid in step_rollouts for pos in rollout_id_to_samples[rid]]
    step_lengths = [total_lengths[i] for i in sample_indices]
    global_batch_sizes.append(global_batch_size)
```

这段执行后，本例只有一个训练步：

```text
num_steps = 1
sample_indices = [0,1,2,3,4,5,6,7]  → 选中 A–H
step_lengths = [4,4,4,4,4,4,4,4]
global_batch_sizes = [8]
```

sample_indices 保存**本训练步要用的样本在整批数据中的位置**；下一段按这些样本组微批。多个样本共用一个 rollout ID 时，这个映射会把它们放入同一个训练步，本例暂不展开那条情况。

<a id="pack-step-microbatches"></a>

### ③ 先把样本组成微批，再检查微批数量（158–185）

```python
step_mbs = _pack_step_into_mbs(
    step_lengths,
    args=args,
    use_dynamic_batch_size=args.use_dynamic_batch_size,
    max_per_bin=max_per_bin,
    micro_batch_size=getattr(args, "micro_batch_size", None),
    balance_by_flops=args.balance_by_flops,
)
target_K = max(((len(step_mbs) + align_to - 1) // align_to) * align_to, align_to)
```

本例走辅助函数的静态分支：每两份样本组成一个微批，得到：

```text
step_mbs = [[0,1], [2,3], [4,5], [6,7]]
微批编号：    0      1      2      3
样本名字：   A,B    C,D    E,F    G,H
```

列表内的数字是 sample_indices 中的位置。target_K 把微批数向上对齐到①要求的倍数；本例已经有四个微批，target_K=4，所以后面的调整分支不进入。数量不满足时，动态分支尝试拆分，静态分支报错；此处只继续本例正常路径。

<a id="assign-step-microbatches"></a>

### ④ 把微批编号分给两个 rank（187–198）

```python
K = len(step_mbs)
num_mbs_per_rank = K // dp_size
num_microbatches.append(num_mbs_per_rank)
# 节选 balance_data=False 的分支：
rank_mbs_idx = [list(range(r, K, dp_size)) for r in range(dp_size)]
```

本例 K=4，每个 rank 两个微批；range 从 rank 的编号开始，每隔 2 取一个：

```text
rank_mbs_idx = [[0,2], [1,3]]
                ↓      ↓
rank 0：微批 0、2 → M0=[A,B]、M2=[E,F]
rank 1：微批 1、3 → M1=[C,D]、M3=[G,H]
```

**这里的 `[0,2]` 是微批编号，不能直接当作样本 A、C 的位置。** 必须再通过 step_mbs 查出这两个微批包含哪些样本。

<a id="encode-rank-plan"></a>

### ⑤ 将微批安排写成样本位置（202–207）

partitions 和 micro_batch_indices 开始时都是 `[[], []]`，分别准备接住两个 rank 的结果。源码逐个微批写入：

```python
for r in range(dp_size):
    for mbs_idx in rank_mbs_idx[r]:
        mbs_locals = step_mbs[mbs_idx]
        local_start = len(partitions[r])
        partitions[r].extend(sample_indices[i] for i in mbs_locals)
        micro_batch_indices[r].append(list(range(local_start, local_start + len(mbs_locals))))
```

只放大 rank 0 的两次循环：

| 正在处理 | 从微批中取到的位置 | partitions[0] 写完后 | 本次追加到 micro_batch_indices[0] |
| --- | --- | --- | --- |
| M0，也就是 A、B | [0,1] | [0,1] | [0,1]：放在本 rank 的前两个位置 |
| M2，也就是 E、F | [4,5] | [0,1,4,5] | [2,3]：接在本 rank 已有数据后面 |

E、F 在整批数据里位于 4、5；进入 rank 0 的列表 `[A,B,E,F]` 后，位于 2、3。因此需要保存**整批位置**与 **rank 内位置**两套编号。rank 1 用同样的代码得到 `[C,D,G,H]` 的安排。

<a id="schedule-return-values"></a>

### 返回：四项数据分别解决什么问题（209）

训练步循环结束后，真正的返回语句只有这一行：

```python
return partitions, micro_batch_indices, num_microbatches, global_batch_sizes
```

下面是**本例返回值的展示**，四个位置依次对应上面的名字：

```python
(
    [[0, 1, 4, 5], [2, 3, 6, 7]],           # partitions
    [[[0, 1], [2, 3]], [[0, 1], [2, 3]]],   # micro_batch_indices
    [2],                                   # num_microbatches
    [8],                                   # global_batch_sizes
)
```

| 返回项 | 最外层列表按什么排列 | 本例怎样读 |
| --- | --- | --- |
| partitions | DP rank | rank 0 从整批取 0、1、4、5；rank 1 取 2、3、6、7 |
| micro_batch_indices | DP rank | 每个 rank 都先算自己列表的 0、1，再算 2、3 |
| num_microbatches | 训练步 | [2]：当前这一个训练步，每个 rank 都算两个微批 |
| global_batch_sizes | 训练步 | [8]：当前这一个训练步，全局共使用八个 rollout |

<a id="return-count-units"></a>

**这里的“两路”来自 DP。** DP 的两个副本分担不同样本；PP 划分模型层，让同一份样本经过不同阶段，不能再把这些阶段当成新增样本计数。

micro_batch_indices 表示在各自 partitions 中怎样按本地位置分批，这个理解是对的。代码顺序则是先组微批、分配微批，最后同时写出 partitions 与本地微批索引，并非拿到 partitions 后重新执行一次分批。

把本例的数量放在同一张图里：

```text
一个训练步：全局八个 rollout，本例就是 A–H 八份样本
├─ DP rank 0：四份样本 [A,B,E,F]
│  ├─ 第一个微批 [A,B]：两份样本
│  └─ 第二个微批 [E,F]：两份样本
└─ DP rank 1：四份样本 [C,D,G,H]
   ├─ 第一个微批 [C,D]：两份样本
   └─ 第二个微批 [G,H]：两份样本
```

- **micro_batch_size=2**：每个微批里有两份样本，是大小。
- **num_microbatches=[2]**：这个训练步每个 DP rank 有两个微批，是数量；两个 rank 合计四个微批。
- **global_batch_sizes=[8]**：这个训练步全局有八个 rollout，本例一份 rollout 对应一份样本。它记录的是这一批有多大，不是有八个 batch，也不是把 DP、PP、微批数量加起来。

因此本例可核算为 `2 个 DP rank × 每 rank 2 个微批 × 每微批 2 份样本 = 8 份样本`。这只适用于当前固定微批大小、每 rollout 一份样本的例子；有多片段 rollout 时，全局 rollout 数与训练样本数不能直接等同。

**[2] 与 [8] 都只有一项，是因为这次 schedule 只安排了一个训练步。** 一次调用可以安排多个完整训练步，那时这两份列表各自按训练步记录一个值；前两份列表的最外层仍按 DP rank 排列。

<a id="return-to-parent"></a>

**build_dp_schedule 的工作到“写好这张索引计划”结束。** 更准确地说，它为每个 DP 副本安排样本和微批；一个副本可以由多张 GPU 共同运行，因此返回列表的每项不能直接解释成一张物理 GPU 的数据。

已按用户要求接回 [split_by_dp 的 A–H 收尾](../../data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-eight-samples)：按 partitions 取 tokens、rewards、loss_masks，附上本 rank 的 schedule，再准备张量并返回引用。完整说明在父函数卡维护；本函数仍以索引计划为输出。

<details>
<summary>回查：此前两样本的完整函数解释和运行结果</summary>

<a id="historical-parallel-config"></a>

### ⓪ 先读懂输入的训练约束（112–125）

本折叠区保留此前的两样本调用与源码解释，输入配置和上方 A–H 例子不同。完整并行概念现集中在 [reference](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md)；当前函数入口是上方的 [核心骨架](#schedule-flow)。

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

针对长度误解的[四样本小例子](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#split-by-dp-purpose-and-batching)单独保留在本轮讨论中；下方继续沿用原有两样本主例，不混用两次配置。动态 FLOPs 分批分支、超长单样本和复杂对齐留待按需回查；token 预算不是所有路径都保证的显存上限。

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

以下是上述固定配置下，隔离执行真实函数体得到的结果；完整输入与输出见[运行记录](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/dp-schedule-example-output.json)。

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

partitions 保存整批位置；micro_batch_indices 从本 rank 已有数据的末尾继续编号。于是得到上面的四项结果。返回 [split_by_dp:498–523](../../data/batch_builder.py/BatchBuilder.split_by_dp.md#select-rank-fields)，它才执行字段选择并附上安排：

```python
value = {key: [data[key][index] for index in partition] for key in fields if key in data}
```

因此 rank 0 取回第一份样本的 tokens、reward、mask；rank 1 取回第二份对应字段。小批次安排随数据保留，实际训练在后续消费方发生。

</details>

<details>
<summary>并行概念回查（保留此前卡片锚点）</summary>

<a id="progressive-overview"></a>

完整的逐步例子、原配置标题与概念图现在只在 [并行概念参考](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md#progressive-overview)维护。下面保留旧链接入口。

<a id="batch-size-baseline"></a>

- [Batch](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md#baseline)

<a id="microbatch-one-gpu"></a>

- [Micro-batch](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md#sample-and-microbatch)

<a id="dp-two-gpus"></a>

- [DP](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md#data-parallel)

<a id="pp-two-stages"></a>

- [PP](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md#pp-two-stages)

<a id="vpp-model-chunks"></a>

- [VPP](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md#vpp-model-chunks)

<a id="microbatch-group"></a>

- [mb_group](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md#microbatch-group)

<a id="mb-group-tradeoff"></a>

- [mb_group 的性能权衡](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md#mb-group-tradeoff)

<a id="context-parallel"></a>

- [CP](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md#context-parallel)

<a id="cp-and-attention"></a>

- [CP 与 attention](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md#cp-and-attention)

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

助手的本轮校准见 [概念入门](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/parallelism-primer.md)：dp_size 数训练副本；vpp_size 数每个物理阶段持有的虚拟片段；mb_group 数一组调度中的小批次。先以 micro_batch_size=2 把 8 份样本组成 4 个小批次，再解释 DP 分配和一个副本内部的 PP/VPP。用户对这些校准尚未反馈。

随后对示例与起点的反馈：

> 我觉得例子 已经很不错了
> 但是在一开始我觉得是否应该都通过原始的例子来理解呢？
> 不能一开始直接这样给？
> 请从认知学专家的角度和科技大厂资深程序员的角度考虑应该如何设置这里的参数以及具体内容吧

用户认可例子，并要求重新考虑起点与参数安排，未明确表示已掌握各配置。助手将“原始例子”按无并行拆分的比较基准处理：固定原来 A–H、每份 4 个 token 和 8 层模型，先展示一个副本处理全部数据，再逐项比较；VPP 与配套 mb_group 的联动明确说明。详见 [本轮设计记录](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#parallelism-baseline-and-parameter-progression)。

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

用户对 CP 的前一段说明给出反馈，并要求返回函数：

> 好的 我差不多理解了
> 那么我们可以回到这里的build dp schedule的逻辑了吗？
> 为什么这里的build dp schedule和reference 的内容一样了呢？ 我不是特别理解

助手核对后确认，重复来自将整篇并行入门复制到函数卡并继续双份维护，使函数本体被压到折叠区。本轮将完整入门集中到 reference，函数卡恢复输入输出与源码步骤；保留旧版快照、全部原话及原两样本运行记录。用户的反馈对应前一段 CP 说明，不延伸为调度函数已掌握。

用户继续反馈当前函数卡还不清楚：

> 这里的dp schedule 的内容写清楚了吗？
> 我怎么觉得好像没有那么地清晰呢？
> 特别是这里的固定版本原始函数体这里显示的内容我觉得好像不是特别的合理？

助手将问题定位为：输入后直接给出结果数组，尚未接清同一组输入的中间步骤；“固定版本原始函数体”描述的是此前的验证方法，下面却是在展示返回值，容易混淆。此次将验证方法移到来源折叠区，并用同一组 A–H 补齐源码与中间数据。该定位是助手的分析，新版是否清楚仍待用户反馈。

用户进一步复述本地索引，并追问数量单位：

> h好的 我大概理解了
> 这里简单来说就是切换一下把原本的1234567
> 分给了两波 我的理解是通过pp
> 然后通过又因为是mircrobatch的远古是切成了 01 23 在已经获得的 partitions上面来得到在partitions中的index
> num of microbatches说的是这里的microbatches的大小还是这里的partitions之后microbatches的数量呢/
> 然后global batch是统计按照全量这样子计算
> 单次dp 加上pp和micro batch
> 一共会在这样子的一个schedule里面处理掉多少个batch？
> 这是我的理解
> 对应这里的内容
> (
>     [[0, 1, 4, 5], [2, 3, 6, 7]],           # partitions
>     [[[0, 1], [2, 3]], [[0, 1], [2, 3]]],   # micro_batch_indices
>     [2],                                   # num_microbatches
>     [8],                                   # global_batch_sizes
> )

助手保留“用 partitions 内的本地 index 表达微批”的认识，校准两路分配属于 DP；micro_batch_size 数每微批的样本，num_microbatches 按训练步记录每 rank 微批数，global_batch_sizes 按训练步记录全局 rollout 数。用户对这些校准尚未反馈，不将“大概理解”扩展为全部计数已掌握。

用户随后概括函数职责，并询问后续缺口：

> 好的 那么我们看一下这里我们还缺少什么吧
> 这里的内容更多的就是计算这里的应该给每一个训练的gpu对应的样本我可以简单这么理解吗？
> 做完了之后还需要做什么呢？

助手认可“规划样本分配”的职责方向，进一步明确返回项按 DP 副本组织，一个副本可能跨多张 GPU；计划还包含微批及数量信息。下一处推荐是短回顾已读 split_by_dp 的取字段、附安排、张量准备与引用返回，之后才进入既定的训练闭环阶段。推荐不等于已开始下一 Step，也不据职责概括将全部分支记为掌握。

## 尚不清楚

- 用户已理解 micro-batch 的分次计算动机；“一批样本分组而非把单个样本切碎”的区别、梯度累积与归一化尚待反馈。
- 用户已确认同一 GPU 在不同时间执行模型中不同层的表述；完整交错调度、层参数共享等进一步机制没有据此标为掌握。此前“层复用”的疑问及校准过程保留在原话记录中。
- 梯度同步、流水线通信与反向传播实现没有展开，不从布局图推断已经掌握。
- 用户已初步用 partitions 内的本地 index 描述微批安排，并能概括分配样本的职责；DP 副本与物理 GPU 的对应关系、此前 DP / PP 和各计数单位的校准仍需后续反馈。
- 用户对 mb_group 反馈“大概理解了”，对前一段 CP 说明反馈“差不多理解了”；完整交错调度、attention 通信实现和性能分析未展开。当前返回 build_dp_schedule，配置如何变成分配计划仍按后续反馈核对。
- 动态装箱、FLOPs 估算、负载均衡，以及 CP/VPP 的实际执行与通信细节暂留黑箱。
- 本例恰好组成完整训练步。源码只处理凑够 global_batch_size 个 rollout 的完整步；不足一个完整步会断言，末尾不完整部分不会进入返回安排。此边界未做运行演示。
- 原两样本与当前 A–H 八样本均只隔离执行静态调度路径；split_by_dp、张量化、Ray、CP/VPP 执行与训练没有运行。

<details>
<summary>来源、验证与完整例子</summary>

<a id="eight-sample-validation"></a>

**八样本的构造与验证方法**：2026-10-29 上一轮已对 Slime 18868a79 的 `_pack_step_into_mbs` 和 `build_dp_schedule` 提取未改写的函数体，执行下面这组输入。它是局部验证，不是整套 Slime 训练；输出保存在 [八样本运行记录](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/dp-schedule-eight-samples-output.json)。本轮沿用该结果，中间步骤据同版源码展开，未重新执行函数或训练。

```python
from types import SimpleNamespace

args = SimpleNamespace(
    use_dynamic_batch_size=False,  # 静态分批
    micro_batch_size=2,             # 每个微批两份样本
    balance_by_flops=False,
    balance_data=False,             # 微批轮流分给各 rank
)
train_parallel_config = {
    "dp_size": 2,
    "cp_size": 1,
    "vpp_size": 2,
    "microbatch_group_size_per_vp_stage": 2,
}
# 位置及 rollout ID 0–7，依次对应 A–H；每份完整长度为 4。
result = build_dp_schedule(
    args,
    train_parallel_config,
    total_lengths=[4] * 8,
    global_batch_size=8,
    rollout_indices=list(range(8)),
)
```

上方正文中的源码块是节选，数据块分别标为中间数据或返回值；并不声称每个数据块都是从源文件原样摘出的代码。


- [Step 016 本轮形成过程](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#build-dp-schedule-concrete-handoff)。
- [2026-10-29 配置前置与长度列表的澄清](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#build-dp-schedule-parallel-config)。
- [独立函数卡的明确确认](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#build-dp-schedule-independent-card)。
- [从并行概念到微批组的入门补充](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#parallelism-primer-and-microbatch-groups)。
- [固定原始场景与参数递进](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#parallelism-baseline-and-parameter-progression)。
- [用户纠正：开头只从 batch size 出发](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#batch-size-before-microbatch)。
- [基础版本直接显示在函数卡正文](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#baseline-inline-in-function-card)。
- [从单卡 micro-batch 到两个 DP 副本：标题配置与段末例子](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#microbatch-to-dp-examples)。
- [固定八层、四卡，对照 PP 与 VPP 的模型片段](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#vpp-fixed-model-and-device-layout)。
- [VPP 层复用疑问与下一处推荐](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#vpp-device-versus-layer-reuse)。
- [mb_group：样本数、模型片段数与调度组微批数](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#microbatch-group-versus-other-counts)。
- [mb_group：调度时机与通信量的区别](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#microbatch-group-tradeoff)。
- [CP：从 DP 例子分出序列内合作的对照](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#context-parallel-from-dp)。
- [CP 整体分工与 attention 跨卡实现的区别](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#cp-and-attention-scope)。
- [返回函数逻辑与取消重复维护](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#return-to-schedule-function)。
- [当前清晰度反馈：补齐从输入到返回值的中间变化](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#schedule-dataflow-clarification)。
- [返回值的列表维度与计数单位](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#schedule-return-count-units)。
- [职责概括与返回父函数的下一处推荐](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#schedule-role-and-parent-handoff)。
- [整理前的完整卡片快照](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/history/build-dp-schedule-before-function-focus-2026-10-29.md)。
- [A–H 八样本的本轮实际返回值](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/dp-schedule-eight-samples-output.json)：同样提取原始函数体，只执行静态分支；与原两样本的运行证据分别保留。
- 固定源码：dp_schedule.py:82–209；静态小批次辅助路径为 55–79；实际调用方 batch_builder.py:457–463，字段选择和安排交付为 498–523。
- [示例脚本](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/run-dp-schedule-example.py)通过 AST 提取上述两个函数的原始函数体，不改写实现；用固定配置执行，未导入整套训练依赖，未执行动态分支或负载均衡。
- [实际输出](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/dp-schedule-example-output.json) · [源码证据](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/source-evidence.json)。父卡最初采用假设分配表，本轮新增固定配置的独立运行证据，不将此前静态推导改写为实际执行。

</details>
