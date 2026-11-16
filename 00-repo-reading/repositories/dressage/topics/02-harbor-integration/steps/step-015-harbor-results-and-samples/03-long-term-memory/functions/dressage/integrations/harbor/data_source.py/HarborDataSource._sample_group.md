> Step 011 补充继承（2026-11-11）：来自 [Step 010 收束时的完整记录](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource._sample_group.md)。原话、日期、来源与未知保留；继承不表示本步新增理解。

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/03-long-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource._sample_group.md) 完整继承；不改变原认识时间或掌握状态。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource._sample_group.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource._sample_group.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource._sample_group.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

# HarborDataSource._sample_group

- 源码：[dressage/integrations/harbor/data_source.py:478–509](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L478)。
- 首次单独建卡：Step 010，2026-11-10；此前只在父函数中定位用途。
- 最近认识更新：2026-11-10，用户在组与编号的解释后表示大致理解；保留为初步理解，不等同于完整机制已掌握。

[来自 get_samples](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.get_samples.md#get-samples-mainline) → **_sample_group** → 返回 `group`；再回到父函数的 `source_groups`。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：`get_samples` 已为一组选择规格、编号和 instance_id，现在需要创建组内各次尝试的模板。
2. **具体内容**：按 `n_attempts` 循环创建 Sample，写入组/样本编号、任务 URI 和关联身份，收集为一个列表返回。
3. **建议构建的心智模型**：

   > 为同一任务与 Agent 规格的每次尝试，准备一份带编号和身份的 Sample 模板。

4. **调用代码**：

   ```python
   group = self._sample_group(
       spec,
       n_attempts=self.n_samples_per_prompt,
       group_index=group_index,
       first_sample_index=self.sample_index,
       instance_id=instance_id,
   )
   ```

## 本场景的输入与输出

<a id="sample-group-mainline"></a>

**输入已经由调用方给定**：`spec` 是一份 `HarborPromptSpec`，对应任务与 Agent 配置；本函数只读取其中的 ID 和任务 URI。`n_attempts` 决定组内模板数量，`group_index` 和 `instance_id` 在组内共用，`first_sample_index` 提供 Sample 编号起点。训练调用省略 `descending_indices`，使用默认 `False`。

**输出**：一组 `list[Sample]`，长度为 `n_attempts`。这里不调用模型、不构建轨迹；返回的 Sample 是后续执行和转换要用的模板。本函数不推进数据源游标，编号推进在调用者中完成。

### 先看每次循环实际写了什么

训练正常路径节选：这里只展示默认递增编号；原函数还支持 descending_indices=True 的递减编号，见文末完整源码。

```python
group: list[Sample] = []
for attempt_slot in range(n_attempts):
    index = first_sample_index + attempt_slot
    group.append(
        Sample(
            group_index=group_index,
            index=index,
            prompt=spec.task_uri,
            metadata={
                "harbor_spec_id": spec.spec_id,
                "harbor_task_id": spec.task_id,
                "harbor_agent_id": spec.agent_id,
                "harbor_attempt_slot": attempt_slot,
                "harbor_instance_id": instance_id,
            },
        )
    )
return group
```

关键是：`prompt` 此时保存任务 URI，**不是在这里拼接完整题面或生成回答**。metadata 让后续流程找回任务规格、实例与第几次尝试。

<a id="sample-numbering"></a>

### group 与三个编号怎样区分

当前训练路径中，一个 group 为同一任务、同一 Agent 规格准备多次尝试；不是把同一题型的不同题目放在一起。 同组的 Sample.index 不同不表示规格不同；不同 group 也未必是不同题目，可能对应同一题的其他 Agent 配置或再次取样。

- `group_index`：这份模板属于哪一组，同组模板共用。
- `Sample.index`：这份 Sample 模板的编号；调用方推进编号后，可跨组继续递增，不是组内题号。
- `metadata["harbor_attempt_slot"]`：本组的第几次尝试，从 0 开始。

> 一组准备同一道任务的多次尝试，每次尝试对应一份独立编号的 Sample 模板。当前只是准备模板，尚未执行任务。

### 一组两份模板的实际形状

延续 get_samples 的 A 组：`n_attempts=2`、`group_index=10`、`first_sample_index=20`、`descending_indices=False`。下表是返回对象的字段投影；A 的 ID/URI 和 instance_id 是调用方已提供的相同值，不代表这里重新生成。

| 字段 | group[0] | group[1] |
| --- | --- | --- |
| group_index | 10 | 10 |
| index | 20 | 21 |
| prompt | spec.task_uri | 同左 |
| metadata["harbor_spec_id"] | spec.spec_id | 同左 |
| metadata["harbor_task_id"] | spec.task_id | 同左 |
| metadata["harbor_agent_id"] | spec.agent_id | 同左 |
| metadata["harbor_attempt_slot"] | 0 | 1 |
| metadata["harbor_instance_id"] | instance_id | 同左 |

**两份模板的任务来源相同，尝试槽位和 Sample 编号不同。** 它们是两个 Sample 对象，收集在一个 group 中。

读完返回 [get_samples](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.get_samples.md#get-samples-mainline) 的 `group = self._sample_group(...)`。调用者推进编号，将 group 加入 groups；最后由 `_run_harbor_rollout` 接收整批 `source_groups`。

## 我的直接表述（原话）

本次建卡要求的节选：

> 但是这个函数卡片里别的内容就不需要东
> 然后分别生成这三个函数卡片吧

这是范围确认，不代表本函数已经读懂。

在 group、Sample.index 与尝试槽位的区别得到解释后，用户反馈（节选）：

> 好的 我差不多理解了

此前将 group 理解为题目类别、将 sample index 理解为组内题号的原话与校准保留在 [get_samples 卡片](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/data_source.py/HarborDataSource.get_samples.md)。本次按用户要求将字段说明放在实际填写 Sample 的本函数中。

## 尚不清楚

- 当前要核对的是模板中的字段与组结构，不要求先读完整 Sample 类。
- spec 的注册构建、任务 URI 的后续解析，以及实际模型执行留在对应流程。

<details>
<summary>完整源码与验证依据</summary>

Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`；源码 [data_source.py:478–509](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/data_source.py#L478)。仅静态核对；示例字段为教学构造，不是实际任务或运行结果。

```python
def _sample_group(
    self,
    spec: HarborPromptSpec,
    *,
    n_attempts: int,
    group_index: int,
    first_sample_index: int,
    instance_id: str,
    descending_indices: bool = False,
) -> list[Sample]:
    group: list[Sample] = []
    for attempt_slot in range(n_attempts):
        index = (
            first_sample_index - attempt_slot
            if descending_indices
            else first_sample_index + attempt_slot
        )
        group.append(
            Sample(
                group_index=group_index,
                index=index,
                prompt=spec.task_uri,
                metadata={
                    "harbor_spec_id": spec.spec_id,
                    "harbor_task_id": spec.task_id,
                    "harbor_agent_id": spec.agent_id,
                    "harbor_attempt_slot": attempt_slot,
                    "harbor_instance_id": instance_id,
                },
            )
        )
    return group
```

形成过程：[Step 010 数据形状补读](../../../../../../../step-010-harbor-rollout-entry/04-flow.md#data-shape-function-cards)。

</details>
