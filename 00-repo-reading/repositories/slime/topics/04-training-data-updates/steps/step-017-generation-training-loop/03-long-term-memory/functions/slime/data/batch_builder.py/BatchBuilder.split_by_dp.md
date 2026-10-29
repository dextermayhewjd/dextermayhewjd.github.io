# BatchBuilder.split_by_dp

- 源码定位：[slime/data/batch_builder.py:445](/home/hongshi/projects/slime/slime/data/batch_builder.py:445)，固定版本 `18868a79`，由助手核对。
- 首次接触：Step 016，2026-10-28；此前只定位交接，本轮按用户要求独立简读。
- 最近认识更新：2026-10-29，用户明确表示大概理解，并概括为将样本、配套字段和对应安排一起交给 Ray。本次确认数据交付职责；对象存储与返回引用的边界由助手补充，未据此标记 Ray 内部或训练消费已掌握。
- 导航：**[当前收尾：A–H 的字段与引用交付](#closing-eight-samples)** · [①取字段](#closing-select-fields) · [②附安排](#closing-attach-schedule) · [③返回引用](#closing-return-refs) · [调度函数返回值](../../utils/dp_schedule.py/build_dp_schedule.md#schedule-return-values) · [本步 scope](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/01-scope.md#split-by-dp-skeleton)。

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

<a id="closing-eight-samples"></a>

### 收尾位置：把刚才的 A–H 分配计划变成可交付的数据

我们已从 [build_dp_schedule](../../utils/dp_schedule.py/build_dp_schedule.md#schedule-return-values) 拿到同一组八样本计划。现在回到调用它的 split_by_dp，沿默认 object-store 路径收尾：

```text
已有训练字段 data + 刚算好的索引计划
  → ① 按 partition 取配套字段         520–521
  → ② 附上本 rank 的安排，准备张量     499–504、522–523
  → ③ 发布并返回两份数据引用           527–530
```

这次例子的输入仍是 A–H、每份完整长度 4、每个微批 2 份样本；为展示实际字段选择，给每份样本补充下面这些构造值。每行 tokens 的前两项表示输入，后两项表示响应，因此 loss_mask 的长度为 2。这里只展示当前要观察的字段。

```python
data["tokens"] = [
    [101, 201, 301, 401],  # A
    [101, 202, 302, 402],  # B
    [101, 203, 303, 403],  # C
    [101, 204, 304, 404],  # D
    [101, 205, 305, 405],  # E
    [101, 206, 306, 406],  # F
    [101, 207, 307, 407],  # G
    [101, 208, 308, 408],  # H
]
data["rewards"] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
data["response_lengths"] = [2] * 8
data["loss_masks"] = [[1, 1] for _ in range(8)]
```

已有的计划不变：

```python
partitions = [[0, 1, 4, 5], [2, 3, 6, 7]]
micro_batch_indices = [[[0, 1], [2, 3]], [[0, 1], [2, 3]]]
num_microbatches = [2]
global_batch_sizes = [8]
```

<a id="closing-select-fields"></a>

### ① 同一组位置取出 tokens、reward、mask

在 `for rank, partition in enumerate(partitions)` 的每一轮，源码 520–521 执行：

```python
value = {key: [data[key][index] for index in partition] for key in fields if key in data}
value.update({key: data[key] for key in ("raw_reward", "total_lengths") if key in data})
```

fields 是此前准备的按样本选择的字段清单。每个字段使用同一个 partition，所以一份样本的 tokens、reward、mask 一起交给同一 rank。放大 rank 0 的结果，下面是张量化前的字段节选：

```python
value["tokens"] = [
    [101, 201, 301, 401],  # A
    [101, 202, 302, 402],  # B
    [101, 205, 305, 405],  # E
    [101, 206, 306, 406],  # F
]
value["rewards"] = [1.0, 2.0, 5.0, 6.0]
value["loss_masks"] = [[1, 1], [1, 1], [1, 1], [1, 1]]
```

| 这一轮 | 使用的 partition | 取出的样本 | 取出的 rewards |
| --- | --- | --- | --- |
| rank 0 | [0,1,4,5] | A、B、E、F | [1.0,2.0,5.0,6.0] |
| rank 1 | [2,3,6,7] | C、D、G、H | [3.0,4.0,7.0,8.0] |

raw_reward 和 total_lengths 有单独用途：它们保留全局数组，供全局统计及负载指标使用。其余列入 fields 的字段按 partition 选取；原 data 中的样本并未被删除。

<a id="closing-attach-schedule"></a>

### ② 附上本 rank 的微批安排，再整理字段类型

**所在函数：[BatchBuilder.split_by_dp](/home/hongshi/projects/slime/slime/data/batch_builder.py:498)。** ①②③都是它内部的处理阶段；本段的附加与类型整理对应 [522–523 行入口](/home/hongshi/projects/slime/slime/data/batch_builder.py:522)。这里添加函数引用，是为了标明当前仍在父函数中。

循环开始时已经为本 rank 建好 schedule（499–504）；取完字段后将它附到 value 并整理张量（522–523）：

```python
schedule = {
    "partition": partition,
    "global_batch_sizes": global_batch_sizes,
    "num_microbatches": num_microbatches,
    "micro_batch_indices": micro_batch_indices[rank],
}
# 中间的字段选择见①。
value.update(schedule)
tensorize_rollout_data_for_training(value)
```

以 rank 0 为例，value 中现在既有 A、B、E、F 的字段，也有下面的安排：

```python
{
    "partition": [0, 1, 4, 5],
    "micro_batch_indices": [[0, 1], [2, 3]],
    "num_microbatches": [2],
    "global_batch_sizes": [8],
}
```

这里的 `[[0,1],[2,3]]` 正好作用于局部样本顺序 `[A,B,E,F]`：先算 A、B，再算 E、F。后两项计数仍按训练步排列，所以两份 rank 数据都携带 [2] 与 [8]。

tensorize_rollout_data_for_training 原地整理字段类型。例如每条 tokens 变成 CPU 上的整数 Tensor，loss_masks 也转换为整数 Tensor；rewards 在这个函数中仍是数值列表。**样本顺序和刚才的微批索引保持对应**，这里开始具备训练端接收所需的数据形式。

<a id="closing-return-refs"></a>

### ③ 返回两个 DP 副本各自的数据引用

**所在函数：[BatchBuilder.split_by_dp](/home/hongshi/projects/slime/slime/data/batch_builder.py:527)。** 最外层的 result 是一个 list，里面的每一项是一个 Box；Box 里面保存 ObjectRef，ObjectRef 指向已经准备好的 value。

默认路径在每轮末尾发布该 rank 的 value；循环结束后返回列表：

```python
result.append(Box(ray.put(value)))
# 全部 rank 处理结束后：
return result
```

为了看清执行顺序，把上面一行等价展开成三个动作；下面变量名是讲解时引入的，源码保持上面的单行写法：

```python
data_ref = ray.put(value)     # 先存放数据，得到 ObjectRef
boxed_ref = Box(data_ref)     # 再用 Box 保存这个引用
result.append(boxed_ref)      # 最后向 list 追加这一项
```

Ray 在这里提供数据存储与跨进程传递能力。[ray.put 的官方说明](https://docs.ray.io/en/latest/ray-core/api/doc/ray.put.html)明确：它接收一个对象，将其放入对象存储，返回该对象的引用。**引用用于后续取到数据，实际 value 保存在对象存储中。**

[Box 的本地实现](/home/hongshi/projects/slime/slime/utils/misc.py:143)只是把传入对象保存在 `_inner`，并提供 `inner` 属性读取它。因此这里先调用 Ray，再构造 Box；Box 的构造函数没有调用 Ray。

```text
result：list
├─ 第 0 项：Box
│   └─ inner：ObjectRef → DP rank 0 的 value
│                         样本 A、B、E、F + 配套字段 + 微批安排
└─ 第 1 项：Box
    └─ inner：ObjectRef → DP rank 1 的 value
                          样本 C、D、G、H + 配套字段 + 微批安排
```

**把“这个节点的数据”理解为“这个 DP rank 分到的数据”更准确。** DP rank 与物理节点、GPU 的对应关系由训练部署决定。当前每项引用关联该 rank 分到的样本及其训练字段和安排；一个 list 收集两个 rank 的两项包装引用。这里展示的是源码关系，未实际调用 Ray 获取引用编号。

到这里，当前数据准备链已接起来：

```text
Sample 列表
  → convert：整理成全体训练字段
  → build_dp_schedule：计算样本与微批的索引计划
  → split_by_dp：按计划准备各 rank 数据并交回引用
```

训练端怎样取用这些数据、完成训练并更新生成侧权重，属于下一阶段的训练闭环。本段先以“数据和安排已经一起交付”为停止位置；不把收尾说明当作训练已实际执行或用户已掌握的证据。

<details>
<summary>回查：原两样本输入与分配过程（不同于上面的 A–H 场景）</summary>

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

- 本例完整 token 长度是 `[3, 4]`，它包括每份样本的输入与响应部分，和 response_lengths 的 `[2, 3]` 不同。这里保存长度列表，没有求和成 7；data 会新增 total_lengths 字段。
- build_dp_schedule 根据长度、并行与批次配置、rollout 归属，给出样本和小批次的安排。初读时保留为黑箱；已有[两份样本的具体调度例子](../../utils/dp_schedule.py/build_dp_schedule.md#two-sample-example)。2026-10-29 按用户问题补充[四项并行配置的准备阶段](../../utils/dp_schedule.py/build_dp_schedule.md#parallel-config-preparation)，读完返回这里使用结果。
- partitions 决定每个 rank 取哪些**输入位置**；micro_batch_indices 决定 rank 内怎样组成 micro-batch；另外两项保存各训练步的小批次数和全局批次大小。

初读时为了看清下一段如何取字段，假设调度函数给出下面这个合法安排。本轮已在两个 rank、global_batch_size=2、micro_batch_size=1、关闭动态分批与负载均衡的配置下，隔离运行调度函数得到相同结果；[完整配置与实际输出](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/dp-schedule-example-output.json)可回查。这不表示任意配置都会得到相同安排，也不表示已运行完整 split_by_dp。

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

<a id="follow-one-rank"></a>

**2026-10-29 带读：跟踪一次循环。** 本例的 partitions 是 `[[0], [1]]`。循环第一轮得到 `rank=0, partition=[0]`；第二轮得到 `rank=1, partition=[1]`。rank 表示这份数据准备给谁；partition 列出要从完整 data 中取哪些样本位置；value 是本轮新建的数据字典。

只看第二轮，并把取值表达式中的变量代入：

```python
# 原 data 仍然包含两份样本。这里是原表达式的代入说明。
data["tokens"][1]   # [101, 301, 302, 303]
data["rewards"][1]  # 1.0

# 列表推导仍返回列表，因此本轮 value 的字段节选为：
{
    "tokens": [[101, 301, 302, 303]],
    "rewards": [1.0],
}
```

这轮取得第二份样本的配套字段，原 data 中的样本没有因此被删除。随后附上本 rank 的小批次安排，整理张量类型并保存引用。下一轮或返回的位置都由同一个父函数控制；此处不进入调度算法或训练内部。

下面将两轮并排，列出张量化前的字段节选：

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

2026-10-29 再次要求带读：

> 请带着我看一下这里的split by dp是在做什么吧
> 我绝需要看一下这个 否则感觉很混乱

用户在调度函数之后明确要求收尾：

> 好的 那么给出这里的收尾的内容吧

本轮按已确认范围，在同一张父函数卡补充 A–H 的字段、微批安排和返回引用，不另开 Step。当前新增的 tokens、reward 等是与原八样本长度一致的教学构造值；原两样本例子单独保留。讲解已补充不代表用户已经确认理解这段交接。

用户要求补函数引用，并复述第③段：

> 这里的第二步骤是不是应该考虑一下加入这里的split by dp的引用？
> 同时考虑一下这里的第三个部分
> 我来复述一下
> 这里更多的是把这里的得到的更新的部分
> 放入这个列表里面也就是一个list
> 然后每一个list 都是这样子的box
> box中调用了ray
> 我不知道这里是什么
> 但是应该给出了这一个节点需要的所有的样本和对应的数据是我的理解

助手保留“用列表收集准备好的各份数据”的方向，区分 list、其中的 Box、Box 保存的 ObjectRef，以及对象存储中的 value。源码先调用 ray.put，再构造 Box；分配项对应 DP rank，不能直接按物理节点解释。第②段新增父函数及源码位置链接；这些澄清是否理解仍待反馈。

用户随后确认数据交付这一层的理解：

> 好的 这里 我大概理解了
> 这里可以立即为得到了这样子批次之后把对应的数据交给ray
> ray这里只是获得样本和配套字段 以及对应的安排 是我的理解

这次明确反馈确认的是样本、配套字段和微批安排一同交付。助手将“交给 Ray”具体说明为存入对象存储并取得引用，供训练侧之后取用；不扩展为用户已经掌握 Ray 内部、Box 的后续消费或训练执行。

## 尚不清楚

- 用户提出的“相近长度组 batch”与本函数目的之间的区别，已由助手校准；尚待反馈，不能记为用户已纠正。
- 用户已确认将样本、配套字段和安排交给 Ray 的职责理解；Box 与 ObjectRef 的进一步使用、DP rank 与物理节点的区别仍按后续反馈核对。样本位置、sample index 与 rollout ID 的进一步区别保留回查。
- 从调度计划到配套数据交付的职责已获得用户“大概理解”的反馈；后续训练如何取出和使用这些数据尚未展开。动态装箱与负载均衡继续保留黑箱。
- 张量化、Ray / NIXL / straw 传输内部和后续训练消费方式尚未深入。
- 本卡仍未执行完整 split_by_dp、张量化或 Ray。八样本调度结果已在子卡独立运行；本轮另核对原始字段选择和字典更新语句，执行到张量化之前，返回引用仍为源码结构说明。

<details>
<summary>来源、验证与完整例子</summary>

- [第②段函数引用及第③段的 list / Box / ObjectRef 澄清](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#split-by-dp-box-objectref)。
- [Ray put 官方接口](https://docs.ray.io/en/latest/ray-core/api/doc/ray.put.html)仅用于核对存储与返回引用的含义，不据此推断本机已安装或运行的 Ray 版本。
- [A–H 字段选择与安排拼装结果](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/split-by-dp-eight-samples-fields.json)：使用原字段清单及 499–503、520–522 行语句，构造与上一环节匹配的八份数据；实际执行至张量化之前。完整父函数、torch、Ray 与训练未执行。
- [调度计划的既有运行结果](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/dp-schedule-eight-samples-output.json)保持不变；[本次收尾过程](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#split-by-dp-eight-sample-closing)区分教学输入、运行范围和源码推导。

- [Step 016 本轮形成过程](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#split-by-dp-first-pass)。
- [本轮展示调整的依据与反馈](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#split-by-dp-concrete-data-first)：复用 BaseAdapter._translate 的输入输出对照及“先核心、后前置”的阅读方法。
- [目的、小批次与 DP 分工的区分](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#split-by-dp-purpose-and-batching)：保留本轮概念校准、长度反例与文档组织建议。
- [2026-10-29 主干带读](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#split-by-dp-guided-rank-loop)：沿同一份 data 跟踪 rank、partition、value 与返回引用；本轮为静态解释，没有新增运行。
- 固定源码：batch_builder.py:445–530；调用方 rollout.py:385–390；训练配置写入 rollout.py:572–573。
- 辅助接口核对：[build_dp_schedule:82](/home/hongshi/projects/slime/slime/utils/dp_schedule.py:82)现有[独立子卡](../../utils/dp_schedule.py/build_dp_schedule.md)；[tensorize_rollout_data_for_training:35](/home/hongshi/projects/slime/slime/observability/rollout_data_utils.py:35)、[Box:143](/home/hongshi/projects/slime/slime/utils/misc.py:143)只确认接口和返回语义。
- [源码证据](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/source-evidence.json)。两份输入承接 convert 的构造示例；调度表最初是假设输入，本轮补上固定配置的运行证据。字段分片仍为静态推导，没有真实 ObjectRef 或训练结果。

</details>
