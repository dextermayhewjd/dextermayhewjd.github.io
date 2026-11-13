# HarborDataSource.get_samples

- 源码：[dressage/integrations/harbor/data_source.py:277–296](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L277)。
- 首次单独建卡：Step 010，2026-11-10；此前只在父函数中定位用途。
- 最近认识更新：2026-11-10，用户开始表述 source_groups 的分组结构与编号含义；组的语义和 Sample 编号由助手校准，尚待后续确认。

[来自父函数第 2 段](../rollout.py/_run_harbor_rollout.md#load-source-groups) → **get_samples** → [_sample_group](HarborDataSource._sample_group.md#sample-group-mainline)

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`_run_harbor_rollout` 已有数据源，按 `target` 请求本批训练模板组，当前 `evaluation=False`。
2. **具体内容**：反复选择任务与 Agent 规格，生成该组的身份，委派 `_sample_group` 创建模板；推进训练游标和编号，返回这些组。
3. **建议构建的心智模型**：

   > 取指定数量的工作组，每组准备若干次尝试的 Sample 模板，交给后面的执行准备。

4. **调用代码**：

   ```python
   target = int(getattr(args, "rollout_batch_size", 1))
   source_groups = data_source.get_samples(target)
   # 父函数检查组数后，调用 _resolve_work(data_source, source_groups)。
   ```

## 本场景的输入与输出

<a id="get-samples-mainline"></a>

**进入时**：数据源已持有任务与 Agent 的规格、每组尝试数和训练游标。本函数创建模板组，尚未执行任务。

- 输入 `num_samples` 在这里指**组数**；组内模板数取自 `self.n_samples_per_prompt`，是另一个数量。
- 返回 `list[list[Sample]]`：外层每项是一组，内层每项是一份尝试模板。
- 副作用：取规格时推进训练游标；每生成一组，更新 `sample_group_index` 与 `sample_index`。不更新评估游标。

### 看清一组怎样生成，再看外层怎样收集

以下为函数体节选，保留实际调用和编号更新；`_next_training_spec` 的选择顺序与 `_instance_id` 的生成算法按需回查。

```python
count = _nonnegative_count(num_samples)
groups: list[list[Sample]] = []
for _ in range(count):
    # 为这一组选择规格、组编号和任务实例身份。
    spec = self._next_training_spec()
    group_index = self.sample_group_index
    instance_id = _instance_id(self.run_id, "train", group_index, spec.spec_id)
    group = self._sample_group(
        spec,
        n_attempts=self.n_samples_per_prompt,
        group_index=group_index,
        first_sample_index=self.sample_index,
        instance_id=instance_id,
    )
    # 收入本批，同时为下一组推进编号。
    self.sample_group_index += 1
    self.sample_index += len(group)
    groups.append(group)
return groups
```

静态例子：请求 2 组，每组 2 次尝试；假设本次依次选到规格 A、B，初始组编号为 10，Sample 编号为 20。

| 返回位置 | 对应规格 | Sample.group_index | Sample.index | metadata 中的 harbor_attempt_slot |
| --- | --- | --- | --- | --- |
| groups[0][0] | A | 10 | 20 | 0 |
| groups[0][1] | A | 10 | 21 | 1 |
| groups[1][0] | B | 11 | 22 | 0 |
| groups[1][1] | B | 11 | 23 | 1 |

`self.sample_index` 是给后续 Sample 分配编号的计数器：每收下一组便增加 `len(group)`。各字段的区别见 [_sample_group：group 与三个编号](HarborDataSource._sample_group.md#sample-numbering)。

返回的是 2 组、合计 4 份模板。数据源的 `sample_group_index` 变为 12，`sample_index` 变为 24。同组模板对应同一规格和 instance_id；实例 ID 由源码生成，此处省略具体字符串。

| 需要看清什么 | 进入哪里 | 读完回到哪里 |
| --- | --- | --- |
| 一份 Sample 和一个 group 的实际内容 | [_sample_group](HarborDataSource._sample_group.md#sample-group-mainline) | 回到 `group = ...`，接编号更新和 `groups.append(group)` |
| 模板组接下来怎样使用 | [父函数第 2 段](../rollout.py/_run_harbor_rollout.md#load-source-groups) | `source_groups` 接住结果，检查组数，然后进入 [_resolve_work](../rollout.py/_resolve_work.md#resolve-work-mainline) |

本轮读到返回的数据形状与编号变化即可；不下钻规格轮换、shuffle 或恢复游标机制。

## 我的直接表述（原话）

本次建卡要求的节选：

> 但是这个函数卡片里别的内容就不需要东
> 然后分别生成这三个函数卡片吧

这是范围确认，不代表本函数已经读懂。

随后用户表述：

> 简单来说这里的通过get sample的方式以及内部的这个方法
> 让我明白了这里的source groups里面的samples 就是每一个
> 规定类型的group (不同种类的题目或者sample)
> 然后这里的这个sample index是这个题目中的哪一个具体的题目
> 是我对于这里的理解

助手校准：当前训练路径的一组来自一个任务与 Agent 规格，组内模板对应多次尝试，不是一个题型下收集多道题。self.sample_index 是数据源为后续 Sample 分配编号的计数；Sample.index 是各模板的编号，可跨组递增。组内第几次尝试由 metadata["harbor_attempt_slot"] 表示，组号由 Sample.group_index 表示。以上是对用户表述的技术校准，不视为用户已经确认理解。

用户在上述校准后表示“好的 我差不多理解了”，并要求保存说明；本次将具体字段解释集中在 _sample_group，本卡保留组间计数的职责。

随后用户继续表述并询问下一处入口：

> 好的 我差不多理解了
> 也就是一个group里面题目是一样的
> 但是具体的index是具体运行的规格不一样
> 但是是同一个问题
> 只有不同问题的group才不一样
> 好的那么继续看吧
> 我们现在还有什么需要做的吗?
> 是看这里的这个data source 这里的内容吗?
> 你觉得? 我们之前是不是漏掉了data source是什么

助手校准：同组 index 不同表示不同 Sample 模板，当前对应同一任务/Agent 规格的多次尝试，不表示运行规格改变。不同 group 也不保证题目不同，同一题可因 Agent 配置或再次取样出现在另一组。接下来在 _resolve_work 中按使用点认识 data_source.resolve_spec 的查规格职责，暂不通读整个数据源类。

## 尚不清楚

- 用户表示大致理解，但后续仍将 index 差异解释为运行规格不同，并认为不同 group 必然对应不同题目；本轮已校准，需后续结合实际字段继续确认。
- 规格选择、实例 ID 算法和持久化暂不展开。

<details>
<summary>完整源码与验证依据</summary>

Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`；源码 [data_source.py:277–296](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L277)。仅静态核对；示例字段为教学构造，不是实际任务或运行结果。

```python
def get_samples(self, num_samples: int) -> list[list[Sample]]:
    """Return training groups and advance only the training cursor."""

    count = _nonnegative_count(num_samples)
    groups: list[list[Sample]] = []
    for _ in range(count):
        spec = self._next_training_spec()
        group_index = self.sample_group_index
        instance_id = _instance_id(self.run_id, "train", group_index, spec.spec_id)
        group = self._sample_group(
            spec,
            n_attempts=self.n_samples_per_prompt,
            group_index=group_index,
            first_sample_index=self.sample_index,
            instance_id=instance_id,
        )
        self.sample_group_index += 1
        self.sample_index += len(group)
        groups.append(group)
    return groups
```

形成过程：[Step 010 数据形状补读](../../../../../../../step-010-harbor-rollout-entry/04-flow.md#data-shape-function-cards)。

</details>
