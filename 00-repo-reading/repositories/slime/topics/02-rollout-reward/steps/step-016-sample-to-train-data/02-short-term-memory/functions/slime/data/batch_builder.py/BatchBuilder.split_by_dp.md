# BatchBuilder.split_by_dp

- 源码定位：[slime/data/batch_builder.py:445](/home/hongshi/projects/slime/slime/data/batch_builder.py:445)，固定版本 `18868a79`，由助手核对。
- 首次接触：Step 016，2026-10-28；此前只定位交接，本轮按用户要求独立简读。
- 最近认识更新：用户已理解 convert 整理了训练字段，仍在追问 split_by_dp 解决什么问题，并提出“长度相近才放进同一 batch”的理解。本轮区分小批次组装与 DP 分工，以下校准尚待用户反馈。
- 导航：[前一环节 convert](BatchBuilder.convert.md#return-to-dp-handoff) · [本步 scope](../../../../../01-scope.md#split-by-dp-skeleton)。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据固定源码整理，作为理解参考。

1. **使用场合**：convert 返回的是全体样本的一份训练字段字典，而数据并行训练需要明确每个副本使用哪些样本、分成哪些小批次计算。split_by_dp 负责准备各个 DP rank 能使用的数据与安排。DP 是 Data Parallel（数据并行）；rank 是数据并行编号，不直接等同于一台机器或一张 GPU。训练并行配置已设置到 BatchBuilder。

2. **具体内容**：① 调用 build_dp_schedule 制定每个 rank 的样本分工和小批次安排；② 按计划选择 tokens、reward、mask 等配套字段；③ 附上安排、准备张量或存储视图，返回包装好的数据引用。长度和批次配置用于第一项决策；本函数组织这三项交接，具体分组与分配策略由调度函数实现。

3. **建议构建的心智模型**：

   > 核心问题：这一批训练样本，由各个训练副本分别处理哪一部分、分几次处理？
   >
   > 全体样本的训练字段 → 制定分工 → 取出各 rank 的完整样本字段 → 连同小批次安排交付。
   >
   > 分配的单位是完整样本，tokens、reward、mask 必须保持对应；一个 rank 拿到的数据还可以分为多个 micro-batch。小批次怎样组、再分给哪个 rank，是两层决策。

   当前误解的校准：**这份实现没有“样本 token 长度相近才能放入同一 batch”的条件。** 静态路径按样本数量切小批次；动态路径在 balance_by_flops=False 时按 token 总预算装箱，长、短样本可以放在一起。balance_data=True 时另外尝试平衡各 rank 的预计计算量。相关规则由 [build_dp_schedule](../../utils/dp_schedule.py/build_dp_schedule.md#batching-vs-dp-assignment)及其辅助函数执行，不要求各 rank 的总 token 数完全相同。

4. **调用代码**（RolloutManager._generate:385、390；当前选择 object-store、无恢复记录的正常路径）：

   ```python
   data = self.batch_builder.convert(data)
   return self.batch_builder.split_by_dp(data)
   ```

   两个方法由调用方先后调用，split_by_dp 不是 convert 内部的子调用。

## 本场景的输入与输出

<a id="data-before-after"></a>

### 先看实际数据怎样分给两个 rank

数据并行训练有多个模型副本，rank 是数据并行编号。这里为每个 rank 准备要使用的样本数据。先看源码 520 行的效果，再回查前面的分配表；下面原有的 ①②③ 仍按执行顺序保留。

沿用同一个两样本例子，只显示 tokens 和 rewards。两个 rank 各分一份；以下是字段选择的静态对照，局部 value 位于张量化之前，**不是函数的完整返回值**。

```python
# 调用前：两份样本放在同一份 data 中（字段节选）
data = {
    "tokens": [[101, 201, 202], [101, 301, 302, 303]],
    "rewards": [-1.0, 1.0],
}

# rank 0 的 value：第一份样本（字段节选）
{
    "tokens": [[101, 201, 202]],
    "rewards": [-1.0],
}

# rank 1 的 value：第二份样本（字段节选）
{
    "tokens": [[101, 301, 302, 303]],
    "rewards": [1.0],
}
```

本次先抓住一个关系：**按整份样本选择字段，tokens 与对应的 reward 一起进入同一 rank 的数据。** 其他按样本分片的字段也按相同位置取出。

源码 [520 行](/home/hongshi/projects/slime/slime/data/batch_builder.py:520)就是执行这个动作的地方：

```python
value = {key: [data[key][index] for index in partition] for key in fields if key in data}
```

例如为 rank 1 选择 rewards 时，key 是 `"rewards"`、partition 是 `[1]`，里面的取值相当于 `[data["rewards"][1]]`，结果就是 `[1.0]`。选择 tokens 时使用同一个位置 1，因此仍与奖励配对。

后续给这些局部数据附上处理安排，准备张量并返回包装引用。具体见下面的 ②③；需要追问“为什么 rank 1 分到第二份”时，再进入 ① 的 build_dp_schedule。这里先把它作为分配表来源。

<details>
<summary>同一场景的完整输入</summary>

### 输入：沿用刚才的两份 Sample 转换结果

本例选择 `rollout_data_transport="object-store"`，有两个 DP rank，global_batch_size=2。下面是前一张卡两份 Sample 的转换结果；仍是**构造数据与静态推导，未运行 Ray 或训练**。

```python
data = {
    "tokens": [[101, 201, 202], [101, 301, 302, 303]],
    "response_lengths": [2, 3],
    "rewards": [-1.0, 1.0],
    "raw_reward": [1.0, 3.0],
    "truncated": [0, 0],
    "sample_indices": [100, 101],
    "rollout_ids": [10, 20],
    "loss_masks": [[1, 1], [1, 1, 1]],
    "rollout_mask_sums": [2, 3],
    "source_names": ["unknown", "unknown"],
}
```

</details>

<a id="prepare-schedule"></a>

### ① 准备分配表：完整长度 → 调度函数（453–463）

```python
total_lengths = data.get("total_lengths")
if total_lengths is None:
    total_lengths = [len(tokens) for tokens in data["tokens"]]
data["total_lengths"] = total_lengths
partitions, micro_batch_indices, num_microbatches, global_batch_sizes = build_dp_schedule(
    self.args,
    self.train_parallel_config,
    total_lengths,
    global_batch_size=self.args.global_batch_size,
    rollout_indices=data["rollout_ids"],
)
```

- 本例完整 token 长度是 `[3, 4]`，它包括输入与响应部分，和 response_lengths 的 `[2, 3]` 不同。data 会新增 total_lengths 字段。
- build_dp_schedule 根据长度、并行与批次配置、rollout 归属，给出样本和小批次的安排。初读时保留为黑箱；本轮补充[两份样本的具体调度例子](../../utils/dp_schedule.py/build_dp_schedule.md#two-sample-example)，读完返回这里使用结果。
- partitions 决定每个 rank 取哪些**输入位置**；micro_batch_indices 决定 rank 内怎样组成 micro-batch；另外两项保存各训练步的小批次数和全局批次大小。

初读时为了看清下一段如何取字段，假设调度函数给出下面这个合法安排。本轮已在两个 rank、global_batch_size=2、micro_batch_size=1、关闭动态分批与负载均衡的配置下，隔离运行调度函数得到相同结果；[完整配置与实际输出](../../../../../references/dp-schedule-example-output.json)可回查。这不表示任意配置都会得到相同安排，也不表示已运行完整 split_by_dp。

```python
partitions = [[0], [1]]
micro_batch_indices = [[[0]], [[0]]]
num_microbatches = [1]
global_batch_sizes = [2]
```

第 0 个 rank 取输入位置 0，第 1 个 rank 取输入位置 1。`partition` 里的 0、1 是列表位置，不是 sample_indices 的 100、101，也不是 rollout_ids 的 10、20。每个 rank 分到一份样本，所以各自 micro-batch 中的本地下标都是 0。

<a id="select-rank-fields"></a>

### ② 按同一组下标取字段：每个 rank 得到什么（497–523）

下面摘取 object-store 路径；fields 是源码 464–485 的分片字段列表，包含 tokens、response_lengths、rewards、loss_masks、sample_indices、rollout_ids 等，完整清单先不背诵。

```python
for rank, partition in enumerate(partitions):
    schedule = {
        "partition": partition,
        "global_batch_sizes": global_batch_sizes,
        "num_microbatches": num_microbatches,
        "micro_batch_indices": micro_batch_indices[rank],
    }
    value = {key: [data[key][index] for index in partition] for key in fields if key in data}
    value.update({key: data[key] for key in ("raw_reward", "total_lengths") if key in data})
    value.update(schedule)
    tensorize_rollout_data_for_training(value)
```

张量化前的字段节选：

| 字段 | rank 0 的 value | rank 1 的 value |
| --- | --- | --- |
| sample_indices | `[100]` | `[101]` |
| tokens | `[[101, 201, 202]]` | `[[101, 301, 302, 303]]` |
| response_lengths | `[2]` | `[3]` |
| rewards | `[-1.0]` | `[1.0]` |
| loss_masks | `[[1, 1]]` | `[[1, 1, 1]]` |
| rollout_ids | `[10]` | `[20]` |
| rollout_mask_sums | `[2]` | `[3]` |
| partition | `[0]` | `[1]` |
| micro_batch_indices | `[[0]]` | `[[0]]` |

这里有一个明确的例外：**raw_reward 和 total_lengths 保留全局数组**，所以两个 rank 都携带 `[1.0, 3.0]` 和 `[3, 4]`，用于全局奖励统计与负载指标。它们不按 partition 切短。两个 rank 也都携带 global_batch_sizes=[2]、num_microbatches=[1]；其余已存在的分片字段继续按同一下标选择。

随后 tensorize_rollout_data_for_training 原地整理 value：例如 tokens 的每条序列成为 CPU Tensor，loss_masks 也转为 Tensor，rollout_mask_sums 转为浮点 Tensor；rewards 仍是对应的数值列表。本轮只认识这项类型变化，不展开张量化内部。

<a id="return-rank-refs"></a>

### ③ 返回：每个 rank 一份数据引用（527–530）

源码在进入上述循环前准备 result=[]，每个 rank 的 value 准备好后执行：

```python
result.append(Box(ray.put(value)))
# 全部 rank 处理完后：
return result
```

ray.put 将数据放进对象存储并返回 ObjectRef，Box 包住该引用。下面是**形状示意**，ref_rank0 / ref_rank1 不是实际运行取得的编号：

```text
result
├─ [0] Box → .inner: ObjectRef → rank 0 的数据与 schedule
└─ [1] Box → .inner: ObjectRef → rank 1 的数据与 schedule
```

因此本例返回列表有两项；每项不是一份 Sample，也不是直接返回普通字典。它交回调用方，后续由训练流程使用。此处没有开始训练或同步梯度。

<details>
<summary>其他传输分支：只保留分类，不作为当前展开内容</summary>

- object-store：本例。取出本 rank 的字段、张量化，再用 ray.put 发布引用。
- nixl：字段整理路径相同，在 ray.put 指定 tensor transport。
- straw：先从转换结果引用读取调度所需的长度和 rollout 归属，为每个 rank 构造 TrainBatchRef 的 selection 与 schedule；不在这里复制完整载荷。仍用 Box 包装 Ray 引用返回。
- 不支持的传输名称会报错。分配算法、引用生命周期和持久化不在本轮范围内。

</details>

## 我的直接表述（原话）

> 好的那么来看一下这里的split by dp吧
> dp是data parallel吗？
>
> 这里给出这里的short term memory了吗？
> 我需要你带着我简单看一下这里到底是怎么做的
> 我理解了刚才是把对应的训练字段都整理了
> 那么现在需要怎么做呢？

用户已确认继续本方法，并说明已理解前一环节整理训练字段。DP 含义、partition 位置索引、按字段取出和返回引用由助手解释，尚待用户具体反馈。

调度例子之后，用户反馈：

> 我不是特别能够理解这里的内容
> 我在想的问题是
> 有没有一个比较好理解的方式来帮助我理解这里的split by dp呢
> 之前是否有比较好的skill中的reference来处理这个问题呢？

此反馈说明前述讲法尚未解决当前困惑；本轮改用实际字段的分配前后作为观察入口，不推定用户的具体卡点已经确定。

本轮进一步表述与文档问题：

> 我在想得问题是这里的split by dp 是解决的什么问题
> 我的理解是 应该是需要让两个sample或者一个batch内部的token长度差不多才会放到一个batch的对吗？
> 这是我的理解
> 但是这里的split by dp 没有给我比较好的心智模型
> 作为一个资深的工程师你会看这个函数的那些部分？
> 作为一个认知学家 你会如何考虑构建这里的md文件来让我理解和掌握这个split by dp的核心呢？

## 尚不清楚

- 用户提出的“相近长度组 batch”与本函数目的之间的区别，已由助手校准；尚待反馈，不能记为用户已纠正。
- 用户是否已区分样本位置、sample index、rollout ID，以及普通数据字典与返回引用，尚待反馈。
- build_dp_schedule 的固定大小小批次例子已在[子卡](../../utils/dp_schedule.py/build_dp_schedule.md)展开，用户仍待反馈；动态装箱、长度/负载均衡等机制继续保留黑箱。
- 张量化、Ray / NIXL / straw 传输内部和后续训练消费方式尚未深入。
- 本卡用分配表理解字段数据流，没有实际执行本方法或运行训练；新增运行只覆盖子函数的固定配置。

<details>
<summary>来源、验证与完整例子</summary>

- [Step 016 本轮形成过程](../../../../../04-flow.md#split-by-dp-first-pass)。
- [本轮展示调整的依据与反馈](../../../../../04-flow.md#split-by-dp-concrete-data-first)：复用 BaseAdapter._translate 的输入输出对照及“先核心、后前置”的阅读方法。
- [目的、小批次与 DP 分工的区分](../../../../../04-flow.md#split-by-dp-purpose-and-batching)：保留本轮概念校准、长度反例与文档组织建议。
- 固定源码：batch_builder.py:445–530；调用方 rollout.py:385–390；训练配置写入 rollout.py:572–573。
- 辅助接口核对：[build_dp_schedule:82](/home/hongshi/projects/slime/slime/utils/dp_schedule.py:82)现有[独立子卡](../../utils/dp_schedule.py/build_dp_schedule.md)；[tensorize_rollout_data_for_training:35](/home/hongshi/projects/slime/slime/observability/rollout_data_utils.py:35)、[Box:143](/home/hongshi/projects/slime/slime/utils/misc.py:143)只确认接口和返回语义。
- [源码证据](../../../../../references/source-evidence.json)。两份输入承接 convert 的构造示例；调度表最初是假设输入，本轮补上固定配置的运行证据。字段分片仍为静态推导，没有真实 ObjectRef 或训练结果。

</details>
