# _generate_rollout_async

- 源码定位：[fully_async_rollout.py:278–378](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L278-L378)，由助手核对，固定版本 `18868a79`。
- 首次接触：Step 013，先定位为 get_completed_groups 的调用方；2026-10-26 用户确认建立父函数卡。
- 最近认识更新：2026-10-26，用户已说出从 worker.output_queue 获取完成组的来路，并询问接收、过滤、收集的记录方式。用户又追问过滤函数是否通过迭代生成 reward；已补充读取已有奖励统计与执行过滤判定的区别。相关修正及下述分支、计数仍为助手据源码整理。

## LLM 整理：使用场合、具体内容与心智模型

以下为 LLM 根据源码和当前场景整理的理解参考。

1. **使用场合**：外层 generate_rollout_fully_async 选择本地 AsyncRolloutWorker 后，通过 run 执行本协程；后台持续生成，本函数负责收集本次 rollout 所需的一批结果。
2. **具体内容**：取得并恢复 worker，设定目标组数；反复领取已完成的组，调用过滤接口，保留合格组、处理丢弃组；收够后把 collected 交给最终整理，再向外层返回本批结果。
3. **建议构建的心智模型**：

   > 从持续产出的完成结果中，凑出本次需要的合格组。
   >
   > ```text
   > _generate_rollout_async
   > ├─ ① 准备：取得 worker，设置 target 与 collected
   > ├─ ② 收集：接收组记录 → 过滤 → 决定去向【当前展开】
   > │  ├─ keep=True  → 加入 collected
   > │  ├─ keep=False → 交给丢弃处理，继续收集
   > │  └─ 本轮没取到组 → 短暂等待后再取
   > └─ ③ 交付：收够 target → 最终整理 → 返回本批结果
   > ```
   >
   > ②的分支依据是 verdict.keep；循环目标按 collected 中被保留的组计数。后台生成与本次收集分工不同。

4. **调用代码**（generate_rollout_fully_async:389，本地 worker 分支）：

   ```python
   return run(_generate_rollout_async(args, rollout_id, data_buffer))
   ```

## 本场景的输入与输出

沿用本步的本地、非 straw 路径。以下为**教学构造与静态推导**：假设配置了有效的动态过滤函数，该函数只作保留判定、不修改样本；未配置批次过滤 hook。具体过滤规则与后台生成过程先留白，例子不是一次真实运行。

| 输入或已有对象 | 本例内容 |
| --- | --- |
| args.rollout_batch_size | 2，即 target=2 个组，不是 2 个 Sample |
| args.dynamic_sampling_filter_path | 一个有效的已配置函数路径，由 load_function 得到 dynamic_filter |
| args.rollout_sample_filter_path | None；本例不执行批次过滤 hook |
| args.rollout_data_transport | 沿用已选定的非 straw 传输路径 |
| rollout_id | 12，本次 rollout 的编号 |
| data_buffer | 当前输入源；_get_worker 从中取得同一个本地 worker |
| worker.output_queue | 按入队顺序存着 (7, G7)、(8, G8)、(9, G9)；G7 等表示组，每组可有多个 Sample |
| 本例过滤判定 | G7 保留，G8 丢弃，G9 保留 |

为展示最终返回，另假设各组的首个样本 index 分别为 7、8、9，且没有队列凭证副作用需要展示。这个 index 与 gid 是两项独立数据，本例恰取相同数值。

**输出**：最终整理获得包含 G7、G9 的结果。由于本例启用了动态过滤，父函数返回 RolloutFnTrainOutput 对象，其中 samples 为整理后的组列表，metrics 为统计信息；字段结构来自源码，具体统计值未运行获取。

```text
output.samples = [G7, G9]
output.metrics = 本次收集与过滤的统计信息
```

返回前，G8 已交给丢弃处理，三条记录都已从完成队列移出。最终整理的排序、凭证处理等内部实现当前只保留接口。

<a id="preparation-boundary"></a>

### ① 准备：先认出进入循环时已有的数据（282–301）

```python
worker = _get_worker(args, data_buffer)
worker.resume()
target = args.rollout_batch_size
collected = []
dynamic_filter = (
    load_function(args.dynamic_sampling_filter_path)
    if getattr(args, "dynamic_sampling_filter_path", None) is not None
    else None
)
```

这是函数内的节选，省略日志、统计器和计时变量。这里先认出 worker、目标组数、收集列表和过滤函数；worker 的创建与恢复机制不在本卡继续下钻。

<a id="collect-filter-retain"></a>

### ② 接收、过滤与收集：当前重点（306–336）

下面是本地、非 straw 路径的教学裁剪：保留真实调用和控制流，省略 worker.error 检查、日志、统计更新及 straw 发布分支。变量来自上面的准备阶段；这是异步函数内的代码片段，不是独立运行脚本。

```python
while len(collected) < target:                         # [1] 保留的组还不够
    drained = 0
    for _gid, group in worker.get_completed_groups(    # [2] 只领还缺的数量
        limit=target - len(collected)
    ):
        drained += 1
        verdict = call_dynamic_filter(dynamic_filter, args, group)  # [3]
        if verdict.keep:
            collected.append(group)                   # [4] 本组被保留
            continue

        await asyncio.to_thread(                      # 本组被丢弃
            discard_rollout_group,
            group,
            args,
            verdict.reason or "dynamic_filter",
            controller=getattr(data_buffer, "controller", None),
        )

    if not drained:                                   # [5] 本轮一组也没取到
        await asyncio.sleep(0.05)
```

- **[1] 看被保留的数量。** len(collected) 达到 target 后结束这段循环；单次领取返回 [] 不会结束整个 rollout。
- **[2] 接收的是 (gid, group) 记录。** getter 已把这些记录从 output_queue 移出；for 将记录解包，当前过滤使用 group，_gid 不参与这里的保留判定。
- **[3] 过滤返回判定。** call_dynamic_filter 接收过滤函数、args 和当前组，交回 verdict；当前分支读取 keep，丢弃时使用 reason。
- **[4] 只有保留分支会扩大 collected。** continue 结束当前组的处理，转到下一条记录；拒绝的组交给 discard_rollout_group，具体清理保持黑箱。
- **[5] drained 表示这轮取到几组。** 它每取一组就增加，包括后来被丢弃的组。只有 drained 为 0 才在这里等待 0.05 秒；如果全被拒绝但确实取到了组，本轮不会因这项条件而等待。

同一例子的变化：

| 位置 | 本轮领取上限／判定 | collected | 完成队列剩余 |
| --- | --- | --- | --- |
| 进入循环 | target=2，当前缺 2 组 | [] | G7、G8、G9 |
| 第一次领取 | limit=2，取出 G7、G8；drained 最终为 2 | [] | G9 |
| 处理 G7 | keep=True | [G7] | G9 |
| 处理 G8 | keep=False，交给丢弃处理 | [G7] | G9 |
| 下一轮领取并处理 G9 | limit=1，keep=True | [G7, G9] | 空 |
| 再检查循环条件 | len(collected)==target，结束收集 | [G7, G9] | 空 |

表中“第一次领取”表示 getter 已返回两条记录，drained 随 for 遍历逐条增加；它不是提前一次加二。例子用于连起两种计数：**drained 统计取到的组；len(collected) 统计保留的组。**

<a id="dynamic-filter-interface"></a>

**call_dynamic_filter 的交接**：内部三段机制已放入[独立子卡](../filter_hub/base_types.py/call_dynamic_filter.md#function-body)，这里保留父函数需要的接口。

| 交接 | 本轮只记什么 |
| --- | --- |
| 输入 | dynamic_filter、args、当前 group |
| 输出 | DynamicFilterOutput；keep 决定是否保留，reason 可说明丢弃原因 |
| 没配置动态过滤函数 | dynamic_filter 为 None，这层默认给出 keep=True |
| 需要展开时 | 子卡说明奖励统计、调用规则与输出适配；具体 fn 策略和统计器内部仍留白 |

这里的 reward 代码是在**读取已有奖励并记录过滤前的总和、数量**；真正的过滤调用是 `fn(args, samples, **kwargs)`。推导式构造 rewards 列表，不等于重新评分。三段源码及语法依据见[过滤与奖励统计的最小说明](../../../../../../step-013-completed-group-handoff/references/dynamic-filter-reward-reading.md)。

| 需要进入哪里 | 看清后回到哪里 |
| --- | --- |
| [get_completed_groups 既有卡片](AsyncRolloutWorker.get_completed_groups.md) | 回到 [2]，逐项解包 getter 返回的记录 |
| [call_dynamic_filter 子卡](../filter_hub/base_types.py/call_dynamic_filter.md)，当前回查三段机制 | 回到 [3] 的 verdict，再看 [4] 的保留或丢弃分支 |
| [discard_rollout_group 的调用处](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L324-L330)，内部留白 | 清理调用正常结束后继续处理下一组，或回到 while 继续领取 |

<a id="finalization-boundary"></a>

### ③ 收够后的整理与返回：当前只认接口（360–378）

- collected 与统计信息交给 finalize_rollout_groups；本例没有批次过滤 hook，调用通过 asyncio.to_thread 执行。若配置了该 hook，源码直接在当前调用线程中执行最终整理，具体原因和内部实现留待后续。
- [finalize_rollout_groups](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/base_types.py#L52-L95)交回 RolloutFnTrainOutput。准备最终结果的代码与本卡②中的逐组动态判定是两处不同接口。
- 父函数根据模式选择返回值：启用任一种过滤或使用 straw 时返回 output 对象；未启用过滤且为非 straw 时返回 output.samples。本例属于前一种。

真实返回语句：

```python
return output if filters_enabled or args.rollout_data_transport == "straw" else output.samples
```

## 我的直接表述（原话）

2026-10-26，回到调用方时对数据来路的理解：

> 目前看到的这里有worker get completed groups
> 也就是在这里获取完成的groups
> 然后从之前翻入的worker outputuqueue里面得到记录？
> 这是我的理解？

随后询问函数较大时的阅读范围：

> 但是这里的generate rollout async好像内容还是比较多的？
> 需要展开别的部分吗？
> 还是只需要找到这个核心骨架就可以了呢？

随后追问过滤函数的职责：

> 那么这里需要需要单独看一下这里的call dynamic filter吗？这里的机制吗？
> 还是说简单理解为这里按照这里的数据质量可以简单做一个过滤方法吗？
> （不过这里里面看下来感觉耕读的偶尔就像是一个通过迭代器直接生成这里的reward部分？

用户已确认按“父函数卡保留整体骨架、当前展开收集阶段”的方式记录。对过滤、计数和最终返回的说明目前来自源码核对，不把同意建卡视为独立理解反馈。

## 尚不清楚

- 用户尚未独立表述 verdict.keep、drained 与 len(collected) 各自控制什么；本卡提供同一例子供继续阅读。
- 用户关于“迭代生成 reward”的疑问已补源码澄清，尚待反馈；奖励统计与输出适配机制已转入[子卡](../filter_hub/base_types.py/call_dynamic_filter.md)，具体业务过滤规则以及 discard_rollout_group 的清理过程仍未展开。
- 最终批次 hook、排序、传输与凭证处理的内部机制；统计收集和线程选择的详细原因。
- 当前真实运行配置与结果尚未取得；本卡条件与数值是明确标注的教学构造。

<details>
<summary>来源、验证与完整例子</summary>

- [父函数与外层入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L278-L389)；[_get_worker](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L58-L79)。
- [过滤输出与适配接口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/filter_hub/base_types.py#L5-L46)；[最终整理和输出类型](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/base_types.py#L13-L19)。
- [本步原始源码摘录](../../../../../../step-013-completed-group-handoff/references/source-excerpts.md)；[版本证据](../../../../../../step-013-completed-group-handoff/references/source-evidence.json)。
- [本轮建卡确认与记录](../../../../../../step-013-completed-group-handoff/04-flow.md#step013-collection-parent-card-created)；[此前粒度建议](../../../../../../step-013-completed-group-handoff/04-flow.md#step013-collection-memory-granularity)。
- 代码按当前固定源码裁剪，输入输出和分支表为静态推导；未运行真实 worker、过滤插件或训练。统计与清理分支的省略不表示它们已经读完。

</details>
