# build_dp_schedule

- 源码定位：[slime/utils/dp_schedule.py:82](/home/hongshi/projects/slime/slime/utils/dp_schedule.py:82)，固定版本 `18868a79`，由助手核对。
- 首次接触：Step 016，2026-10-28；先定位接口，本轮补充具体输入输出。
- 最近认识更新：用户明确表示仍不理解，要求给出简单理解所需的内容；以下是助手讲解，尚无用户对调度机制的确认。
- 导航：[返回 split_by_dp 的调用处](../../data/batch_builder.py/BatchBuilder.split_by_dp.md#prepare-schedule) · [本步 scope](../../../../../01-scope.md#split-by-dp-skeleton)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：split_by_dp 已有完整训练字段，现在需要知道每个 DP rank 分到哪些样本，以及分到后怎样组成小批次。

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

<a id="batching-vs-dp-assignment"></a>

### 当前问题：组小批次和分给 rank 分别决定什么

| 决策 | 本实现的依据 | 源码 |
| --- | --- | --- |
| 哪些样本组成一个 micro-batch | 静态路径按 micro_batch_size 个样本切；动态且 balance_by_flops=False 时按 token 总预算 first-fit 装箱 | dp_schedule.py:55–79；seqlen_balancing.py:159–177 |
| 已组成的小批次分给哪个 DP rank | balance_data=False 时轮流分配；开启时按预计 FLOPs 尝试均衡负载 | dp_schedule.py:187–198 |

因此“长度相近”不是这里组 batch 的必要条件。各 rank 在同一个训练步得到相同**数量的小批次**，也不意味着得到完全相同数量的 token。调度先组小批次，再分给 rank；split_by_dp 根据结果选择实际字段并交付。

针对长度误解的[四样本小例子](../../../../../04-flow.md#split-by-dp-purpose-and-batching)单独保留在本轮讨论中；下方继续沿用原有两样本主例，不混用两次配置。动态 FLOPs 分批分支、超长单样本和复杂对齐留待按需回查；token 预算不是所有路径都保证的显存上限。

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

以下是上述固定配置下，隔离执行真实函数体得到的结果；完整输入与输出见[运行记录](../../../../../references/dp-schedule-example-output.json)。

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

## 尚不清楚

- 用户是否已分清整批位置、rank 内位置和两个数量列表，仍待反馈。
- 动态装箱、FLOPs 估算、负载均衡和 CP/VPP 对齐细节暂留黑箱。
- 本例恰好组成完整训练步。源码只处理凑够 global_batch_size 个 rollout 的完整步；不足一个完整步会断言，末尾不完整部分不会进入返回安排。此边界未做运行演示。
- 隔离运行只覆盖上述静态调度路径；split_by_dp、张量化、Ray 和训练没有在本例执行。

<details>
<summary>来源、验证与完整例子</summary>

- [Step 016 本轮形成过程](../../../../../04-flow.md#build-dp-schedule-concrete-handoff)。
- 固定源码：dp_schedule.py:82–209；静态小批次辅助路径为 55–79；实际调用方 batch_builder.py:457–463，字段选择和安排交付为 498–523。
- [示例脚本](../../../../../references/run-dp-schedule-example.py)通过 AST 提取上述两个函数的原始函数体，不改写实现；用固定配置执行，未导入整套训练依赖，未执行动态分支或负载均衡。
- [实际输出](../../../../../references/dp-schedule-example-output.json) · [源码证据](../../../../../references/source-evidence.json)。父卡最初采用假设分配表，本轮新增固定配置的独立运行证据，不将此前静态推导改写为实际执行。

</details>
