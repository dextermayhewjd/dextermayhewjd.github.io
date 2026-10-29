# BatchBuilder.convert

- 源码定位：[slime/data/batch_builder.py:256](/home/hongshi/projects/slime/slime/data/batch_builder.py:256)，本轮固定版本 `18868a79`，由助手核对。
- 首次接触：Step 016，2026-10-28。
- 最近认识更新：Step 016，2026-10-28；用户已理解基础字段字典，并初步将 loss_mask 与 response 联系起来；要求简读、减少后续条件分支的展开。mask 的规则已据源码补充，具体理解待反馈。
- 导航：[本步 scope](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/01-scope.md#reading-order) · [输入 Sample 类卡](../../../../classes/slime/utils/types.py/Sample.md#step015-field-view)。
- 上层交接：[RolloutManager._generate 卡片](../../ray/rollout.py/RolloutManager._generate.md)，用于回看结果怎样到达 convert，以及 begin 当前分支为何继续转换。

## LLM 整理：使用场合、具体内容与心智模型

以下由 LLM 根据实际调用与固定源码整理，作为理解参考。

1. **使用场合**：`RolloutManager._generate` 已拿到生成、评分和收集后的结果，准备交给训练。默认路径的嵌套结果已由 `_get_rollout_data` 展开，本函数接收非空的 Sample 列表。

2. **具体内容**：默认转换先处理已有奖励、整理 rollout 编号，再按字段汇总 Sample；补齐或处理 loss_mask，按配置携带生成时 log-prob 等数据，返回 `train_data`。配置自定义转换时，直接委派给替换函数。默认路径会修改缺少 mask 或标记移除的 Sample 的 loss_mask。

3. **建议构建的心智模型**：

   > 输入是一份份 Sample，每份对象都装着自己的字段；输出把相同字段汇到同一列表中。它还补充和处理训练需要的数据，随后把结果交回调用方。

4. **调用代码**（[调用方 385–390](/home/hongshi/projects/slime/slime/ray/rollout.py:385)，教学裁剪：选择未命中缓存、非 straw、无恢复记录的路径）：

   ```python
   data = self.batch_builder.convert(data)
   return self.batch_builder.split_by_dp(data)
   ```

## 本场景的输入与输出

**构造一个小输入，隔离执行固定源码的原方法。** 本例没有配置转换或奖励后处理 hook，设置 `rewards_normalization=False`，已有标量奖励直接用于本例的两份奖励输出；SC、top-p 扩展与 routing replay 关闭。token ID 是示意数字，没有调用模型或 tokenizer。

输入：

```python
sample = Sample(
    index=7,
    rollout_id=7,
    tokens=[101, 102, 201, 202],
    response_length=2,
    reward=0.75,
    status=Sample.Status.COMPLETED,
)
samples = [sample]
# 其余字段使用 Sample 默认值，例如 loss_mask=None、metadata={}。
```

`convert(samples)` 返回值节选：

```python
{
    "tokens": [[101, 102, 201, 202]],
    "response_lengths": [2],
    "rewards": [0.75],
    "raw_reward": [0.75],
    "loss_masks": [[1, 1]],
}
```

这是同一次局部运行的输出；完整字典还带有 truncated、sample_indices、rollout_ids、rollout_mask_sums 和 source_names，见下方证据。返回字典之外，原对象的 `sample.loss_mask` 从 None 变为 `[1, 1]`，`sample.reward` 仍为 0.75。

<a id="conversion-entry"></a>

### 入口分支：convert 与自定义转换函数

`convert` 是当前真实方法名；`custom_convert_samples_to_train_data_func` 是构建器持有的可选函数对象。后者在构造时由配置路径加载（42–46 行），不是 convert 的另一个名称。

这里的配置属于当前 BatchBuilder：它根据 `args.custom_convert_samples_to_train_data_path` 加载转换函数，将整批 `samples` 传入。输入中的每份 Sample 不因此自带一个转换函数；此前生成阶段可读取 `sample.generate_function_path` 的规则，不能直接套到这个转换入口。

```python
if self.custom_convert_samples_to_train_data_func is not None:
    return self.custom_convert_samples_to_train_data_func(self.args, samples)
```

| 是否配置自定义转换 | 走哪条路 |
| --- | --- |
| 已配置 | 把 args 和 samples 交给自定义函数，立即返回它的结果 |
| 未配置，本轮例子 | 继续执行 convert 中的奖励后处理、字段组装、mask 等默认逻辑 |

本卡记录 convert 的完整入口与默认转换主线。自定义函数先作为替换分支保留；以后选定具体实现并需要阅读其行为时，再为那个真实函数单独建卡。

默认路径中的 `_post_process_rewards` 只返回原始奖励与处理后的奖励；算法及归一化配置在这里影响奖励数值。后面的 `convert` 才把这些奖励与 tokens、response_length、mask 等组装为 train_data。两层职责需要分开看。

### 本函数内的阶段位置

| 实际执行阶段 | 数据交接 | 本轮深度 |
| --- | --- | --- |
| 263–276：奖励与归属编号 | Sample 列表 → 原始与训练用奖励、rollout_ids | 奖励处理已在子卡展开，用户反馈大致理解；缺号补齐仍按需回查 |
| 278–288：组装基础字段 | Sample 字段 → train_data 的对应字段列表 | **从奖励子卡返回后，用两份 Sample 对照拼装结果** |
| 292–321：整理 mask 并聚合 | 原对象的 loss_mask → 输出 loss_masks、rollout_mask_sums | 本轮简读 292–304 的单份 mask；316–321 先保留按 rollout 汇总的用途 |
| 323–443：可选字段与返回 | 按数据和配置补充 → 返回 train_data | 简要定位生成信息、条件字段与返回；不逐个下钻配置分支 |

<a id="reward-preparation"></a>

### 默认转换的第一个动作：把已有 reward 接成两项返回值

未配置自定义转换时，执行 [263 行](/home/hongshi/projects/slime/slime/data/batch_builder.py:263)：

```python
raw_rewards, rewards = self._post_process_rewards(samples)
```

沿用本页同一个 Sample：`sample.reward=0.75`，没有自定义奖励后处理，`reward_key=None`、`rewards_normalization=False`。此时 `_post_process_rewards` 执行的核心是下面两行（211、254 行；裁剪掉本例不进入的分支）：

```python
raw_rewards = [sample.get_reward_value(self.args) for sample in samples]
return raw_rewards, raw_rewards
```

`get_reward_value` 在本例直接取 sample.reward；若 reward 是字典且配置了 reward_key，则按该 key 选出分数。返回后，convert 接住：

```text
samples[0].reward = 0.75
          ↓ 提取已有分数
raw_rewards = [0.75]     → train_data["raw_reward"]
rewards     = [0.75]     → train_data["rewards"]
```

两项返回值的职责不同：raw_rewards 保存提取出来的原始分数，rewards 保存经过所选后处理的训练用分数。本分支不做归一化，因此两个返回位置指向同一个列表；没有再次调用 reward model，也没有改写 sample.reward。各算法的处理条件、组内统计与输出对照已单独放在 [_post_process_rewards 方法卡](BatchBuilder._post_process_rewards.md#algorithm-outputs)，读完回到本段的两项返回值，再继续 train_data 组装。

随后 265–266 行检查两份奖励的长度与 samples 数量一致。268–276 行准备 rollout_ids；本例已有 sample.rollout_id=7，得到 `[7]`，先不展开缺失编号的补齐循环。现在输入样本、两项奖励和编号已经准备好，继续看下面的 train_data 组装。

<a id="field-assembly"></a>

### 第一观察点：从对象里的字段，到字典里的字段列表

入口已有 `samples=[sample]`；本例前面的奖励处理返回 `raw_rewards=[0.75]`、`rewards=[0.75]`，编号整理得到 `rollout_ids=[7]`。下面是 [278–288 行](/home/hongshi/projects/slime/slime/data/batch_builder.py:278) 的源码节选，仅省略两行说明性注释：

```python
train_data = {
    "tokens": [sample.tokens for sample in samples],
    "response_lengths": [sample.response_length for sample in samples],
    "rewards": rewards,
    "raw_reward": raw_rewards,
    "truncated": [1 if sample.status == Sample.Status.TRUNCATED else 0 for sample in samples],
    "sample_indices": [sample.index for sample in samples],
    "rollout_ids": rollout_ids,
}
```

先只对齐同一个位置：

```text
输入：samples[0]                        输出：train_data
  .tokens = [101,102,201,202]       →    ["tokens"][0] = [101,102,201,202]
  .response_length = 2             →    ["response_lengths"][0] = 2
  .reward = 0.75                   →    ["rewards"][0] = 0.75  （本例未归一化）
```

- 每个字段列表按 `samples` 的顺序组织；相同下标对应同一份输入样本。若有多份 Sample，同一字段就会有多项。
- `tokens` 本来就是一个列表，所以汇总后多了一层外层列表；`response_length` 本来是一个整数，所以汇总后是整数列表。本例的完整 token 序列长度为 4，响应段长度为 2，不把二者当成同一个量。
- 本段汇总没有深拷贝 token 内容；局部执行中 `train_data["tokens"][0] is sample.tokens` 为 True。这里也没有重新分词或重新生成回复。

<a id="rewards-to-field-lists"></a>

### 从奖励子卡返回：两份 Sample 怎样拼成字段字典

这次回到同一 Step 中的父函数 convert。沿用奖励子卡的同组两次 rollout，补上 token、长度和状态，观察 263 行接住奖励后，278–288 行如何使用它们。以下是**另一个构造例子的静态推导**，与前面 reward=0.75、关闭归一化的实际运行例子分开。

本例没有自定义转换或奖励后处理；reward_key=None，算法为 grpo，开启 rewards_normalization，关闭 grpo_std_normalization。输入如下，token ID 仍为示意数字：

```python
samples = [
    Sample(
        group_index=0, index=100, rollout_id=10,
        tokens=[101, 201, 202], response_length=2,
        reward=1.0, status=Sample.Status.COMPLETED,
    ),
    Sample(
        group_index=0, index=101, rollout_id=20,
        tokens=[101, 301, 302, 303], response_length=3,
        reward=3.0, status=Sample.Status.COMPLETED,
    ),
]
```

1. **263–266：接住两项奖励并检查数量。** 按子卡已解释的去均值分支，raw_rewards=[1.0, 3.0]，rewards=[-1.0, 1.0]；两个列表都必须与 samples 等长。
2. **268–276：准备每份 Sample 的 rollout 编号。** 优先取 rollout_id，缺失时取 index；两者都缺失时，才为输出列表补不冲突的临时编号。本例直接得到 rollout_ids=[10, 20]，不会把它们改成 sample 的 index，也不在这里重新分组评分。
3. **278–288：执行上面的字段拼装代码。** tokens、response_length、index 从各 Sample 按顺序收集；两项奖励使用刚才接住的列表；状态转换为是否截断的 0/1 标记。

此时的中间字典是：

```python
train_data = {
    "tokens": [[101, 201, 202], [101, 301, 302, 303]],
    "response_lengths": [2, 3],
    "rewards": [-1.0, 1.0],
    "raw_reward": [1.0, 3.0],
    "truncated": [0, 0],
    "sample_indices": [100, 101],
    "rollout_ids": [10, 20],
}
```

**对应关系由同一个下标维持**：每个列表的第 0 项都属于 samples[0]，第 1 项都属于 samples[1]。例如 `["tokens"][1]`、`["rewards"][1]` 和 `["rollout_ids"][1]` 对应第二份 Sample；不要按 reward 大小排序这些列表。truncated 仅在原状态为 Sample.Status.TRUNCATED 时取 1，本例两个状态均为 COMPLETED，因此都是 0。

这段代码完成“按 Sample 存放 → 按字段收集”的结构变化。它没有把 token 拉平成一条序列、补齐到相同长度或转换成 Tensor；上面的两个 token 列表仍可具有不同长度。group_index 已供奖励后处理使用，这个基础字典直接携带的是 sample_indices 与 rollout_ids。

这还不是 convert 的最终返回值：下一段从源码 292 行继续补充 loss_masks，并在 321 行放入 rollout_mask_sums。下面只展开每份 Sample 的 mask，后续条件字段先保留用途；不为这些连续语句另建函数卡。

<a id="response-loss-mask"></a>

### 响应段的 loss_mask：补齐、检查、屏蔽、收集

入口已有 samples 与基础 train_data。**mask 的每个位置对应一个响应 token，长度必须等于 response_length。** 它不按完整 tokens 的长度或 response 字符串的字符数来构造。0/1 掩码中，1 表示该位置参与 loss，0 表示屏蔽该位置。

下面节选 [292–304 行](/home/hongshi/projects/slime/slime/data/batch_builder.py:292)，仅压缩断行、移除断言的错误消息和原注释，保留实际处理顺序：

```python
loss_masks = []
for sample in samples:
    if sample.loss_mask is None:
        sample.loss_mask = [1] * sample.response_length

    assert len(sample.loss_mask) == sample.response_length

    if sample.remove_sample:
        sample.loss_mask = [0] * sample.response_length

    loss_masks.append(sample.loss_mask)
train_data["loss_masks"] = loss_masks
```

- **没有 mask 才补全 1**；已有合法 mask 时保留，例如 `[1, 0, 1]`。
- **长度必须与响应 token 数相同**。检查在 remove_sample 处理之前，长度不符会触发断言。
- **remove_sample 为 True 时改成全 0**。这里仍保留 Sample、tokens 和 reward，只屏蔽它的响应 loss；不会从 samples 列表删除对象。
- **收集回字典**。原 Sample 的 loss_mask 可能被修改，最后每份 mask 按原样本顺序进入 train_data["loss_masks"]。

承接前面的两份 Sample：response_length 分别是 2 和 3，原 loss_mask 都是 None、remove_sample 都是 False，静态推导得到：

```python
samples[0].loss_mask == [1, 1]
samples[1].loss_mask == [1, 1, 1]
train_data["loss_masks"] == [[1, 1], [1, 1, 1]]
```

若单独把第二份样本设为 remove_sample=True，它的 mask 就变为 `[0, 0, 0]`，token 内容不变。这是对前面构造例子的分支推导，不是新增运行结果。

### 后面的条件分支先按用途看

| 后续位置 | 本轮保留的认识 |
| --- | --- |
| 316–321：rollout_mask_sums | 按 rollout_id 汇总所属 Sample 的 mask 总和，再把各自 rollout 的总和带给每份 Sample；具体 loss 归约先留白 |
| 335–337：rollout_log_probs | 把已有的生成时 logprob 随训练数据带走，具体策略修正留给训练侧 |
| 其余条件字段，直到 443 返回 | 元数据可能覆盖原始奖励或补充信息；算法、路由、多模态等配置决定需要附带的字段。先知道职责与触发条件，不逐个展开内部机制 |

本轮的简读边界是看清 mask 与响应段的关系，后续按需回到汇总或生成信息的真实源码；不以条件分支较多为由宣称整个函数已经掌握。

<a id="return-to-dp-handoff"></a>

### 收尾：带走已有生成信息，把字典交回调用方

在 [335–337 行](/home/hongshi/projects/slime/slime/data/batch_builder.py:335)，生成时记录的 logprob 被携带到训练数据里，本段不重新计算概率：

```python
if samples[0].rollout_log_probs is not None:
    train_data["rollout_log_probs"] = [sample.rollout_log_probs for sample in samples]
```

其他条件字段按上面的用途表保留，443 行返回 train_data。随后由调用方继续交接；下面摘取 RolloutManager._generate 的正常路径，省略 straw 发布与恢复记录分支：

```python
data = self.batch_builder.convert(data)       # 385：接回字段字典
return self.batch_builder.split_by_dp(data)   # 390：分配到训练 DP rank
```

所以不是 convert 内部调用 split_by_dp，而是调用方先后使用两个方法。用户已确认继续同一文件的 [BatchBuilder.split_by_dp 方法卡](BatchBuilder.split_by_dp.md)：先看输入训练字段、各 rank 的分配与最终数据引用；build_dp_schedule、传输和持久化内部继续作为边界。此后按既定计划进入 train.py::train 的生成、训练、权重更新与评估闭环。

## 我的直接表述（原话）

范围确认，2026-10-28：

> 好的 那么继续吧 看一下这些结果到底是怎么整理成训练需要的数据的？

这是对本步问题的确认，尚无用户对字段转换机制的直接解释；不将助手的说明写成已掌握。

后续关于骨架与卡片对象的追问：

> 当前的scope 应该是正确的吧 我说的核心骨架图
>
> 那么我们来看一下吧
> 这里有一个convert
> 也就是这里的convert samples to train data function？
> 我们是要针对这个生成一个short term memory吗？

本轮补清 convert 与自定义替换函数的关系，用户对该区分的理解尚待反馈。

继续沿默认分支的请求：

> 好的 那么就按照按照这个来看一下这里到底是如何转换的吧

本轮据此展开已有奖励的提取与字段交接；这仍是阅读请求，尚未收到对转换机制的直接复述。

随后对分支与职责的初步理解：

> 也就是这里需要看清楚的是针对于一份samples 会有着 自己的如何convert samples to train data 的function 是我的理解
> 如果不是就会掉用这里的post process rewards？
> 然后根据这里的后训练算法生成需要的数据结构？
> 感觉这里的post process rewards 是否需要单独看一下呢？

用户已尝试区分自定义转换与默认路径。助手校准两处：自定义函数来自 BatchBuilder 配置并处理整批输入；奖励后处理与训练数据结构组装是不同职责。用户尚未确认这些校准，也未说明归一化内部如何执行。

奖励子卡讲解后的接续请求，2026-10-28：

> 好的 那么按照这个方式写入吧
> 我差不多理解了
> 那么请继续吧
> 我们是否需要回到上一步了呢？
> 看一下这里的后续是如何拼装的？

“差不多理解”承接奖励后处理的解释；本轮据此回到父函数，接上两项奖励到字段字典的变化。字段拼装的具体理解仍待后续反馈。

字段拼装后的明确反馈，2026-10-28：

> 好的我理解了 基本上还是token是什么 然后这里返回的长度啊
> reward啊
> 一系列对应的内容
> 那么下一步是什么呢？
>
> 跟多的像是一个简单字典记录基本的信息
> 然后呢
> 我们这个函数还需要看哪些部分呢？

用户已将 278–288 行概括为记录基本对应信息的字典。助手确认这适用于基础字段拼装，随后定位剩余的 mask、rollout 内汇总及生成信息携带；本轮给出阅读入口，不将这些后续机制登记为已理解。

对 mask 的初步理解与简读要求，2026-10-28：

> 好的那么简单看一下吧
> 我的理解是一般来说针对于这里response构建的？
> 线面的内容还是太多了 是否需要简单的看一下？
> 这里的if else 太多太多了

用户已经把 mask 与 response 联系起来。助手补清响应 token 数、保留已有 mask、remove_sample 清零与收集交接；后续复杂配置分支按用户要求只保留用途，未要求逐项深读。


## 尚不清楚

- 基础字段拼装已获“理解了”的反馈；mask 已简读，规则与数据变化的具体理解待用户反馈。
- 已出现自定义／默认两路的初步理解；转换函数的配置归属，以及 `_post_process_rewards` 只处理奖励的边界，仍待校准反馈。
- loss_mask 与 response_length 对齐、remove_sample 清零已解释；rollout 内汇总的具体例子及下游 loss 归约尚未深入。
- 奖励处理已在子卡展开算法与开关、rollout 去重和输出映射，用户反馈大致理解；生成时 log-prob 的后续使用与可选字段仍按 scope 中的固定编号推进。
- `split_by_dp` 已另建卡简读数据分配与返回；训练内部尚未展开。

<details>
<summary>来源、验证与完整例子</summary>

- [Step 016 形成过程](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#first-field-assembly)。
- [入口分支与卡片对象的澄清](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#convert-entry-memory-object)。
- [沿默认分支接上奖励与字段](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#default-reward-to-fields)。
- [配置归属与奖励后处理的下一入口](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#batch-config-and-reward-boundary)。
- [从奖励后处理返回字段拼装](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#return-from-rewards-to-assembly)。
- [基础字段理解反馈与剩余阅读入口](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#field-assembly-understood-next-mask)。
- [响应 mask 的简读与分支边界](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#response-mask-brief-reading)。
- [收尾与下一个函数的选择](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/04-flow.md#after-mask-next-function)。
- 固定源码：BatchBuilder.convert 256–443，_post_process_rewards 207–254；RolloutManager._get_rollout_data 545–570，_generate 385–390；Sample.get_reward_value 270–271。
- [完整运行结果](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/convert-example-output.json) · [可复跑脚本](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/run-convert-example.py) · [源码版本证据](../../../../../../../../02-rollout-reward/steps/step-016-sample-to-train-data/references/source-evidence.json)。
- 脚本从源码 AST 取出未改写的 Sample 类、get_source 和 BatchBuilder 的 convert / _post_process_rewards 两个方法；绕过依赖较多的模块导入及构造器，用明确配置构造当前分支。它验证的是本例的局部数据转换，不是完整训练、Ray 执行或前一步契约测试。
- 首个例子关闭归一化，是为单独观察字段对应；不能据此推断真实训练中 raw_reward 总与 rewards 相等。输出 raw_reward 还存在 metadata 覆盖分支，后续按需回查。
- 两份 Sample 的去均值与字段拼装例子为静态推导，未运行 PyTorch 归一化分支；所示字典停在 288 行，不冒充最终完整返回值。

</details>
