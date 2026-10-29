# Step 016 scope · Sample 怎样成为训练数据

[步骤入口](README.md) · [前一步](../step-015-custom-generate-contract/README.md) · [唯一进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

## 1. 阅读目标

**跟着同一份生成结果，说明 Sample 的字段怎样进入 `train_data`，以及奖励和 mask 为什么还需要处理。** 前一步讨论“生成函数应该交回什么”，这一步接着看这些数据的使用方。

首轮直接选择默认转换、非空且已经展开的 `list[Sample]`。第一个构造例子关闭奖励归一化，只观察字段对应；之后按阅读编号回查奖励分支。只需沿用 [Sample 的已有字段记录](02-short-term-memory/classes/slime/utils/types.py/Sample.md#step015-field-view)，无需先重读完整类或重新学习 await。

停止位置：能解释 `tokens`、`response_length`、奖励、`loss_mask` 和生成时 log-prob 的交接；用户进一步确认简读 `split_by_dp`，接清完整字典到各 DP rank 数据引用的变化。本轮补充 `build_dp_schedule` 的固定小例子，说明四项返回值如何产生与使用。动态装箱与负载均衡、训练 loss、优化器、并行通信、straw 存储或 Trace 内部仍不展开。

## 2. 找到指挥官函数

本步直接阅读 `slime/data/batch_builder.py` 中的 [BatchBuilder.convert:256](/home/hongshi/projects/slime/slime/data/batch_builder.py:256)，关注 Sample 怎样变成训练数据。`RolloutManager` 位于 `slime/ray/rollout.py`，是它的调用方；此前的 [Manager 回查](#manager-handoff)保留为背景，本轮从 convert 继续。

转换后的交接入口为同一文件的 [BatchBuilder.split_by_dp:445](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md)。两者由调用方先后调用；本轮只沿 object-store 路径简读 DP 数据分配与返回，不回头展开 Manager。

输入来路：`_get_rollout_data` 取得配置的 rollout 函数返回的数据，在 [567–568 行](/home/hongshi/projects/slime/slime/ray/rollout.py:567)将嵌套列表展开，再返回给 `_generate`。因此本轮看到的是一组 Sample；不把 `convert` 的联合类型注解误读成默认实现会自动展开任意嵌套输入。

## 3. 核心骨架与阅读导航

<a id="overall-position"></a>

### 3.1 整体位置：前面各 Step 在哪里接到本步

**此前围绕“产生并收集 Sample”展开，Step 016 接着看“把收集到的 Sample 整理成训练数据”。** 图旁的 Step 标注用于回看对应记录，执行关系仍按调用、后台运行和结果交接表示。

为接上此前的 worker 阅读，图中展开配置为 `generate_rollout_fully_async` 且选择本地 worker 的路径。其他 rollout 配置也会把结果交回 Manager，但不一定经过这里的本地 worker。

```text
RolloutManager.generate → RolloutManager._generate     # 外层 317 → 调用 328 → 定义 335
  ├─ _get_rollout_data
  │    ├─ call_rollout_fn → generate_rollout_fully_async
  │    │    │
  │    │    ├─ 后台生成：AsyncRolloutWorker._loop       # Step 012：持续调度
  │    │    │    ├─ Task → generate_and_rm_group        # Step 011：组织一组任务
  │    │    │    │    └─ generate_and_rm                # Step 010：单任务控制与补分
  │    │    │    │         └─ 选择并等待自定义 generate  # Step 015：接入约定
  │    │    │    │              └─ Coding Agent 实现    # 主题 01 · Step 000–009
  │    │    │    └─ 登记 _make_done_cb 返回的 _cb
  │    │    │         └─ 任务完成后入 output_queue      # Step 013：完成结果入队
  │    │    │
  │    │    └─ 上层收集：_generate_rollout_async        # Step 013：领取、过滤、收集
  │    │         ├─ get_completed_groups ← output_queue
  │    │         └─ call_dynamic_filter → collected → 返回本批结果
  │    │
  │    └─ 展开嵌套结果 → list[Sample]                  # rollout.py:567–570，本步衔接
  ├─ batch_builder.begin → 准备／复用转换计划           # 当前 raw_ref=None，返回 None
  ├─ batch_builder.convert(data)                       # Step 016：字段整理，调用处 385
  │    └─ train_data 字典
  └─ batch_builder.split_by_dp(data)                    # Step 016【本轮简读】调用处 390
       └─ 每个 DP rank 的数据与调度引用
```

后台生成与上层收集通过同一个 `output_queue` 交接，可以交错运行。Step 015 回看的是 Step 010 中调用自定义生成函数的同一位置；它补充实现者的接口视角，没有增加一道运行阶段。

| 图中的位置 | 回看哪一步 | 接给后面的内容 |
| --- | --- | --- |
| 具体 Coding Agent 实现 | [主题 01 · Step 000–009](../../../01-coding-agent-rl/README.md) | 一份任务怎样运行 Agent、评测并导出 Sample；需要实现细节时回查 |
| 单任务生成控制与奖励判断 | [Step 010](../step-010-generate-and-rm/01-scope.md) | 生成及后处理后的 Sample 或 Sample 列表，返回组级函数 |
| 一组任务的组织与结果汇总 | [Step 011](../step-011-generate-and-rm-group/01-scope.md) | 组级结果；group_rm 决定是否在这一层评分 |
| 持续发起并管理组任务 | [Step 012](../step-012-async-rollout-worker-loop/01-scope.md) | 运行中的组级 Task，以及后续完成回调的注册 |
| 完成回调 → 队列 → 领取、过滤和收集 | [Step 013](../step-013-completed-group-handoff/01-scope.md) | 通过筛选并收集到本批的结果，沿 rollout 返回给 Manager |
| 自定义 generate 的接入位置 | [Step 015](../step-015-custom-generate-contract/01-scope.md#reading-order) | 接收什么参数、交回什么结果、如何由框架接住；与 Step 010 的调用位置相连 |
| Sample → train_data | [Step 016 · 本步阅读入口](#reading-order) | 对齐的字段列表、奖励、mask 等数据，接给后续 DP 分配 |

Step 014 的 Trace 属于执行过程中的追踪能力，继续暂缓；本图不把它列为 Sample 交付链上的独立阶段。`begin` 只回看 raw_ref=None 的短分支。split_by_dp 简读字段选择与返回，调度函数用固定配置补清索引；复杂分配算法、持久化计划和传输实现继续作为边界。

### 3.2 本步局部骨架

#### 数据转换：BatchBuilder.convert

教学裁剪，按真实执行顺序保留默认路径的主要动作；省略编号补齐细节、检查、mask 聚合细节和可选扩展字段。下面的省略号只表示代码已折叠，不是新增接口。

```python
def convert(self, samples):
    if self.custom_convert_samples_to_train_data_func is not None:
        return self.custom_convert_samples_to_train_data_func(...)  # 260–261：替换整个转换

    raw_rewards, rewards = self._post_process_rewards(samples)     # 263：奖励后处理
    rollout_ids = ...                                             # 268–276：整理 rollout 归属编号

    train_data = {                                                # 278–288：按字段汇总
        "tokens": [sample.tokens for sample in samples],
        "response_lengths": [sample.response_length for sample in samples],
        "rewards": rewards,
        "raw_reward": raw_rewards,
        "truncated": [1 if sample.status == Sample.Status.TRUNCATED else 0 for sample in samples],
        "sample_indices": [sample.index for sample in samples],
        "rollout_ids": rollout_ids,
    }

    loss_masks = []
    for sample in samples:                                        # 292–304：整理响应段的 mask
        if sample.loss_mask is None:
            sample.loss_mask = [1] * sample.response_length
        if sample.remove_sample:
            sample.loss_mask = [0] * sample.response_length
        loss_masks.append(sample.loss_mask)
    train_data["loss_masks"] = loss_masks
    train_data["rollout_mask_sums"] = ...                          # 316–321：按 rollout 汇总 mask

    if samples[0].rollout_log_probs is not None:                    # 335–337：保留生成时 log-prob
        train_data["rollout_log_probs"] = [sample.rollout_log_probs for sample in samples]

    ...                                                          # 可选 metadata、R3/SC、多模态等字段
    return train_data                                            # 443
```

骨架属于 **BatchBuilder.convert**；开头的 `custom_convert_samples_to_train_data_func` 是可选的替换函数。配置了它，就调用并直接返回；没有配置才继续执行下面的默认转换。本轮沿默认分支，使用已有的 [convert 父函数卡](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md#conversion-entry)，不为尚未选定实现的替换入口另建卡。

这里的奖励后处理消费已经产生的评分，不能直接等同于再调用一次 reward model。沿默认分支阅读时，可先看 [263 行的短路径输入输出](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md#reward-preparation)，接上后面的字段组装；完整归一化等规则仍在第三个阅读入口按需展开。

<a id="split-by-dp-skeleton"></a>

#### 转换后的交接：BatchBuilder.split_by_dp

本轮沿 object-store 路径。下面是教学裁剪：省略 straw / nixl 分支、完整 fields 与 schedule 字段、调度实参；真实字段与例子见 [split_by_dp 方法卡](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md)。

```python
def split_by_dp(self, data):
    total_lengths = data.get("total_lengths")
    if total_lengths is None:
        total_lengths = [len(tokens) for tokens in data["tokens"]]
    data["total_lengths"] = total_lengths
    partitions, micro_batch_indices, num_microbatches, global_batch_sizes = build_dp_schedule(...)  # 457：四项安排
    fields = ...                                  # 464–485：按样本分片的字段清单
    result = []
    for rank, partition in enumerate(partitions):  # 498：逐个准备 rank 的数据
        schedule = ...                            # 499–504：该 rank 的处理安排
        value = {key: [data[key][index] for index in partition] for key in fields if key in data}
        value.update({key: data[key] for key in ("raw_reward", "total_lengths") if key in data})
        value.update(schedule)
        tensorize_rollout_data_for_training(value) # 523：整理训练字段的张量类型
        result.append(Box(ray.put(value)))        # 527：保存数据，返回引用
    return result                                 # 530：每个 rank 一项
```

骨架按实际执行顺序排列。阅读时，先看 [520 行对应的实际数据前后](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#data-before-after)，明确各 rank 得到哪些 tokens 和 reward；457 行的子调用单独保存在 [build_dp_schedule 函数卡](02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md)，包含配置准备、输入输出与调度主干。调度函数返回后接回 498–523 行选择字段、附上安排，最后确认包装引用的交付；动态装箱、负载均衡和传输实现继续保留黑箱。

<details>
<summary>调用方背景：此前的 Manager / begin 回查，本轮不展开</summary>

<a id="manager-handoff"></a>

#### 已有调用方背景：generate → _generate → convert

以下保留此前已发生的 Manager 回查。外层 `generate` 登记本轮编号并调用 `_generate`；当前阅读已经回到 data 目录中的 convert。下面选择无恢复、object-store、debug_rollout_only=False 的正常路径，省略日志与服务管理：

```python
data, metrics = self._get_rollout_data(rollout_id=rollout_id)  # 355：Sample 列表
cached = self.batch_builder.begin(
    data, replay=self.recovery is not None and rollout_id in self.recovery.batches
)
if cached is not None:
    return cached
data = self.batch_builder.convert(data)                      # 385：变为训练字段字典
return self.batch_builder.split_by_dp(data)                  # 390：分配并返回
```

当前 `raw_ref=None` 时，begin 在 50–53 行清空 batch_id、_plan 后返回 None；调用方继续走 convert。先看清这一条即可。完整 begin 还管理持久化转换计划与 ready 结果复用，留到相关问题再展开。[Manager 卡片与 begin 局部](02-short-term-memory/functions/slime/ray/rollout.py/RolloutManager._generate.md)。

</details>

<a id="reading-order"></a>

### 3.3 固定阅读顺序

**阅读顺序先看结构变化，再补必要机制；实际执行顺序仍以上面的骨架为准。** 编号保留，不因当前停在哪里而删除此前入口。

前四项继续对应 BatchBuilder.convert；用户确认后追加第五项的 DP 交接，原有编号不变。此前的 [调用方背景](#manager-handoff)折叠保留，不作为继续阅读的前置。

| 阅读编号 | 具体入口 | 看清什么、读到哪里停 |
| --- | --- | --- |
| **第一步：Sample → 字段字典** | [convert 卡：字段组装](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md#field-assembly)，源码 278–288 | 同一份样本如何对应到各字段列表的同一位置；用一份具体输入观察输出。这是本步开始的观察点。 |
| **第二步：响应段的 loss_mask** | [convert 卡：响应 mask 简读](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md#response-loss-mask)，源码 292–304，再定位至 321 | 先看补齐、长度检查、remove_sample 清零与收集；按用户的简读要求，rollout 内汇总先保留用途，读后回到 `train_data`。 |
| **第三步：已有奖励怎样后处理** | [调用处 263](/home/hongshi/projects/slime/slime/data/batch_builder.py:263) → [_post_process_rewards 方法卡](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder._post_process_rewards.md#algorithm-outputs) | 本轮按用户问题展开算法与开关的输出对照，解释 rollout 去重、组内处理与映射回 Sample；读完返回字典的 rewards / raw_reward。不扩展完整 RL loss。 |
| **第四步：补充生成信息并返回** | [源码 335](/home/hongshi/projects/slime/slime/data/batch_builder.py:335)与 [443](/home/hongshi/projects/slime/slime/data/batch_builder.py:443) | 定位 rollout_log_probs 的携带用途和可选字段边界；回到调用方 385，再定位 390 的 split_by_dp。 |
| **第五步：把数据交给各 DP rank** | [split_by_dp 的 A–H 收尾](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.split_by_dp.md#closing-eight-samples)：按计划取字段、附安排、返回引用；此前 457 行的子调用已在 [build_dp_schedule 核心骨架](02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md#schedule-flow)及[四项返回值](02-short-term-memory/functions/slime/utils/dp_schedule.py/build_dp_schedule.md#schedule-return-values)展开；概念按需回查 [reference](references/parallelism-primer.md) | 接清索引计划如何成为各 rank 的配套数据和引用。张量化先认识用途与类型变化，传输和训练内部不展开。 |

连续语句按各自父函数的阶段组织。奖励后处理、split_by_dp 和本轮询问的 build_dp_schedule 已按独立问题建立方法卡；其余辅助调用先保留接口，不继续拆卡。调度子卡属于第五个阅读入口，不另开 Step。源码入口不代表已经全部读过。

阅读接续保留为第三个入口的奖励处理 → [父卡的两份 Sample 拼装例子](02-short-term-memory/functions/slime/data/batch_builder.py/BatchBuilder.convert.md#rewards-to-field-lists) → 第二个入口的响应 mask。本轮按用户要求简读 mask，第四个入口的大量条件分支先保留用途，不逐个下钻；不新开 Step。具体理解与运行状态仍以唯一路线为准。

<details>
<summary>版本、例子与折叠分支</summary>

- 本地源码：`/home/hongshi/projects/slime`，提交 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，本轮工作区无改动。
- 本轮查询官方 main 为 `540ea919e45b8b929198abce008a103be9cfc779`，与本地不同；未拉取或更新。当前代码事实绑定本地版本。
- 主例子是构造 token ID 和标量奖励，使用默认转换、关闭奖励归一化；它不代表真实模型生成或完整训练配置。
- `metadata.raw_reward` 可以覆盖输出的 raw_reward；SC/top-p、routing replay、训练 metadata、多模态和 teacher_log_probs 等字段在首轮只定位。默认输出规则不替代自定义转换函数的约定。
- [源码证据](references/source-evidence.json) · [完整运行输出与边界](references/convert-example-output.json)。

</details>
