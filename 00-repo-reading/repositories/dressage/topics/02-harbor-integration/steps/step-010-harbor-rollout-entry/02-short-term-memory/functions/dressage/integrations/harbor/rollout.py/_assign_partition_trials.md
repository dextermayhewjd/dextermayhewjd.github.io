# _assign_partition_trials

- 源码：[dressage/integrations/harbor/rollout.py:581–621](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L581)。
- 首次单独建卡：Step 010，2026-11-10；此前在父函数中定位过职责。
- 最近认识更新：2026-11-11，用户将 bindings 理解为登记尝试序号的查询表；表与单条 TrialBinding 的区别由助手补充。

[来自 _run_partition 第 2 段](_run_partition.md#prepare-plugin) → **_assign_partition_trials** → [返回接收两个字典](_run_partition.md#assign-trials-call)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：父函数已用当前 `partition` 创建 Harbor `job`，现在需要把 Job 计划中的每个 Trial 对回原始模板和任务身份。
2. **具体内容**：给 Trial 指定名称并取得计划；按任务序号找到工作、按尝试序号找到模板，建立 `templates`、`bindings` 两个字典。
3. **建议构建的心智模型**：

   > 对照 Job 的执行计划与原始工作，记住“这个 Trial 用哪个模板、属于哪个任务和哪次尝试”。

4. **调用代码**（父函数 705–711 行）：

   ```python
   templates, bindings = _assign_partition_trials(
       job,
       partition,
       rollout_id=rollout_id,
       retry_round=retry_round,
       expected_weight_version=expected_weight_version,
   )
   ```

## 本场景的输入与输出

<a id="assign-mainline"></a>

**进入时**，Job 已有要执行的任务与尝试安排；`partition` 仍保留原始工作及 Sample 模板。这里连接这两份信息，不执行 Trial。

| 输入 | 此处用来做什么 |
| --- | --- |
| `job` | 取得其中的 Trial 计划，并为 Trial 配置设置名称 |
| `partition` | 按计划中的序号找回原工作、组内模板和任务身份 |
| `rollout_id`、`retry_round` | 参与生成 Trial 名称，区分批次和执行轮次 |
| `expected_weight_version` | 写入绑定，告诉插件期望的权重版本；可以为 None |

**这里的 template 就是之前 get_samples 创建的 Sample 对象，在此用作结果转换的基础；它不是一种新对象类型。** `templates` 只新建查找字典，不重新创建这些 Sample。`bindings` 是查询字典：键为 Trial 名称，值为一条新建的 `TrialBinding` 身份记录，记录 instance_id、attempt_ordinal 和 expected_weight_version，交给插件使用。

**输出为二元组 `(templates, bindings)`，两个元素都是字典**，使用同一个 `trial_name` 作为键。`templates` 指向已有 Sample 模板，不是新生成的训练结果；`bindings` 保存 `TrialBinding`。本函数还会通过辅助调用更新 Job 中的 Trial 名称。

### 先沿这一段连续主线读

正常路径节选：暂时省略名称回调 `name` 的实现及越界检查；它们完整保留在文末。`plan` 中每个 `entry` 是一条计划记录，不是执行结果。

```python
# 1. 给 Job 中的 Trial 指定名称，取得带名称的执行计划。
plan = assign_trial_names(job, name)
templates: dict[str, Any] = {}
bindings: dict[str, TrialBinding] = {}

for entry in plan:
    # 2. 先找到哪项工作，再找到这项工作中哪次尝试的模板。
    item = partition[entry.task_index]
    templates[entry.trial_name] = item.templates[entry.attempt_index]

    # 3. 用同一个 Trial 名称，记住任务身份和尝试序号。
    bindings[entry.trial_name] = TrialBinding(
        instance_id=item.instance_id,
        attempt_ordinal=entry.attempt_index,
        expected_weight_version=expected_weight_version,
    )

return templates, bindings
```

这里最关键的是两个索引：

- `entry.task_index`：这是 partition 中的哪项工作？
- `entry.attempt_index`：这是该工作中的第几次尝试，对应哪个模板？

### 用已有的 A、B 例子跟一条记录

静态示意：partition 中第 0 项是题目 A 的工作，第 1 项是题目 B 的工作，每题有一份模板。先观察 Job 计划中 B 的那条记录：`task_index=1`、`attempt_index=0`。

| 源码动作 | 本例发生什么 |
| --- | --- |
| `item = partition[1]` | 找到题目 B 的工作记录 |
| `item.templates[0]` | 取出 B 的第一份原始 Sample 模板 |
| `templates[entry.trial_name] = ...` | 将 B 的 Trial 名称关联到这份模板 |
| `bindings[entry.trial_name] = TrialBinding(...)` | 将同一名称关联到 B 的 instance_id、尝试序号 0 和期望版本 |

A 的计划记录也按同样方式处理。最终两个字典均包含 A、B 的条目。Trial 名称由代码生成，这里不假定名称就是字符串 A 或 B；序号从 0 开始。

### 返回父函数时停在哪里

回到 [_run_partition 的接收位置](_run_partition.md#assign-trials-call)，两个局部变量已得到值：

- `templates` 暂存在父函数中，等 Job 执行结束后，与轨迹 bundle 一起用于 Sample 转换。
- `bindings` 随后通过 `trial_bindings=bindings` 交给插件。

**本次读到这两个字典建立完成就停。** 父函数下一项是 `reward_key` 和 `HarborArtifactStore(...)`；此处尚未执行 Job，也没有新的模型输出。

<details>
<summary>按需回查：命名与检查边界</summary>

内部 `name(entry)` 使用批次、执行轮次、组序号、尝试序号和随机后缀组成名称；具体拼接无需作为当前主线记忆。

[assign_trial_names（compat.py:184）](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/compat.py#L184) 负责把名称写入 Job 的 Trial 配置，再返回更新后的计划。本轮只核对这个接口，不继续下潜兼容层。

原函数检查计划中的 Agent 序号、任务序号以及尝试序号能否与 partition 对齐；不匹配时抛出 HarborRolloutError，而不是返回半份映射。`TrialBinding` 的三个字段见 [plugin.py:95](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/plugin.py#L95)。

</details>

## 我的直接表述（原话）

此前用户提出的具体问题：

> 好的 那么我们在有了这个job和partition的情况下
> 为什么还需要这里的这个assign parttition trial呢?
> 并且产出这里的2部分的1,2,3 我其实没有特别理解

随后用户确认先单独建卡阅读：

> 好的那么先这么做吧

这是疑问与范围确认，尚无对两个索引及字典构造过程的完整复述。

本轮用户明确指出数据对象仍不清楚：

> 主要在这里我其实不是特别清楚这里 对于job和plan和partition的具体的定义
> 或者这里的这个bindings
> 我比较想要知道 一般作为资深的工程师
> 在上下文非常复杂
> 以及抽象层次非常多的情况下
> 当前应该怎么去读这里的代码?

助手将当前观察点收窄为变量的实际类型、生产位置、一条具体记录如何流动及使用位置；尚不继续进入更多子函数。

2026-11-11，用户仍不清楚两个返回对象的含义：

> 我其实没有明白这里的job和partition 为什么需要生成这里的这个template binding
> 我可以理解这里需要记录
> 但是我其实不理解这里的template还有这里的binding

助手将解释收窄到具体对象：template 是此前已有的 Sample；templates 用 Trial 名称索引它，供后面结合轨迹转换 Sample。binding 是只含 instance_id、attempt_ordinal、expected_weight_version 的新记录，供插件保留任务身份。两份字典分别交给结果转换与插件，并不表示创建了两份任务或执行结果。


2026-11-11，用户确认并要求记录：

> 好的 那么在这里写清楚吧
> 这里跟多的是给出这个binding 更多的是一个查询的表格是我的理解
> 挤出了这个尝试的序号在这里登记
> 好的那么我们继续吧

助手校准：`bindings` 整体是按 Trial 名称查身份的字典；单个 `TrialBinding` 是其中一条记录。除尝试序号外，记录还包含任务实例 ID 和期望权重版本。当前是内存中的记录，不代表已执行 Trial。


## 尚不清楚

- 用户明确表示 job、plan、partition、bindings 的具体含义仍不清楚；本轮先核对实际数据类型与来源，再跟随一条计划记录，理解效果待反馈。
- 命名兼容层的内部计划构造仅定位；不在本轮继续展开。
- 插件后续如何使用 bindings、结果如何结合模板转换，返回父函数后按阅读进度接续。

<details>
<summary>完整源码与验证依据</summary>

Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。本轮静态核对本地 rollout.py、compat.py 和 TrialBinding 字段；示例是静态构造，没有实际运行 Harbor Job 或模型。

```python
def _assign_partition_trials(
    job: Any,
    partition: Sequence[_GroupWork],
    *,
    rollout_id: int,
    retry_round: int,
    expected_weight_version: str | None,
) -> tuple[dict[str, Any], dict[str, TrialBinding]]:
    from dressage.integrations.harbor.compat import assign_trial_names

    nonce = uuid.uuid4().hex[:8]

    def name(entry: Any) -> str:
        item = partition[entry.task_index]
        return "__".join(
            (
                "dr",
                f"r{rollout_id}",
                f"q{retry_round}",
                f"g{item.group_index}",
                f"a{entry.attempt_index}",
                nonce,
            )
        )

    plan = assign_trial_names(job, name)
    templates: dict[str, Any] = {}
    bindings: dict[str, TrialBinding] = {}
    for entry in plan:
        if entry.agent_index != 0 or entry.task_index >= len(partition):
            raise HarborRolloutError("Harbor v0.18 trial plan no longer matches batching")
        item = partition[entry.task_index]
        if entry.attempt_index >= len(item.templates):
            raise HarborRolloutError("Harbor trial attempt exceeds source group size")
        templates[entry.trial_name] = item.templates[entry.attempt_index]
        bindings[entry.trial_name] = TrialBinding(
            instance_id=item.instance_id,
            attempt_ordinal=entry.attempt_index,
            expected_weight_version=expected_weight_version,
        )
    return templates, bindings
```

形成过程：[Step 010 单独阅读此函数](../../../../../../../step-010-harbor-rollout-entry/04-flow.md#assign-partition-trials-first-card)。父卡此前的 Job/partition 讨论仍保留在原位置。

</details>
