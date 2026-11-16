> Step 011 补充继承（2026-11-11）：来自 [Step 010 收束时的完整记录](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_resolve_work.md)。原话、日期、来源与未知保留；继承不表示本步新增理解。

- 本步继承：2026-11-16，由 [Step 014 来源](../../../../../../../step-014-model-routing-and-api-contract/03-long-term-memory/functions/dressage/integrations/harbor/rollout.py/_resolve_work.md) 完整继承；不改变原认识时间或掌握状态。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/functions/dressage/integrations/harbor/rollout.py/_resolve_work.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../../step-012-task-agent-verifier/03-long-term-memory/functions/dressage/integrations/harbor/rollout.py/_resolve_work.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/integrations/harbor/rollout.py/_resolve_work.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

# _resolve_work

- 源码：[dressage/integrations/harbor/rollout.py:361–410](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L361)。
- 首次单独建卡：Step 010，2026-11-10；此前只在父函数中定位用途。
- 最近认识更新：2026-11-10，用户将本函数理解为给原 group 补齐 spec；助手校准为包装成新的 _GroupWork，保留原模板。

[来自父函数第 2 段](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md#load-source-groups) → **_resolve_work** → 返回 `work`，接到父函数 `pending = list(work)`。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：父函数已从数据源取得 `source_groups` 并检查组数，现在将模板组整理成执行工作项。
2. **具体内容**：检查组内规格、尝试槽位、组号和实例身份的一致性；用 spec_id 找回数据源中的完整规格，将模板、规格和身份包装成 `_GroupWork`。
3. **建议构建的心智模型**：

   > 给每组原始模板配齐执行所需的规格和身份，形成一项可继续交给下游的工作。

4. **调用代码**：

   ```python
   work = _resolve_work(data_source, source_groups)
   # 父函数确认 work 非空、读取策略后：
   pending = list(work)
   ```

## 本场景的输入与输出

<a id="resolve-work-mainline"></a>

**输入**：`groups` 就是调用方的 `source_groups`，结构为 `list[list[Sample]]`；`data_source` 已按 spec_id 登记了任务与 Agent 规格，可通过 `resolve_spec` 找回。

**输出**：`list[_GroupWork]`，一组模板对应一个工作项。`templates=list(group)` 新建列表，但列表中的 Sample 仍是原对象；这里没有执行任务或生成新的回答。

**此处需要补齐的 data_source 知识只有一项：它还保存着 `spec_id → HarborPromptSpec` 的查询表。** `resolve_spec(spec_id)` 从 `self._spec_by_id` 查回已有规格，找不到会报错。get_samples 负责给出模板组；本函数再次使用同一个数据源，是为了根据模板中的 ID 找回完整规格。这里不读取 integration_config 或 job_config，也不重新加载配置文件。


### 看一组模板怎样成为一项工作

正常路径节选，省略检查失败时的报错正文；完整检查保留在文末。

```python
work: list[_GroupWork] = []
for position, group in enumerate(groups):
    # 从已有模板读出规格 ID、组号和任务实例身份。
    first_meta = _metadata(group[0])
    spec_id = str(first_meta.get("harbor_spec_id") or "")
    group_indices = {getattr(sample, "group_index", None) for sample in group}
    instance_ids = {
        str(_metadata(sample).get("harbor_instance_id") or "")
        for sample in group
    }
    # spec 向 data_source 查回；其余资料来自 group 或当前遍历。
    resolver = getattr(data_source, "resolve_spec", None)
    spec = resolver(spec_id)
    work.append(
        _GroupWork(
            position=position,
            templates=list(group),
            spec=spec,
            spec_id=spec_id,
            group_index=int(next(iter(group_indices))),
            instance_id=next(iter(instance_ids)),
        )
    )
return work
```

`spec` 是数据源原先登记的 `HarborPromptSpec`，含 task_config、agent_config 和用于后续分区的 runtime_fingerprint。Sample 中只带关联 ID；这里通过 ID 找回完整配置对象，避免把模板误认为已包含全部执行配置。

### 延续两组、每组两份模板的例子

| 输出字段 | 本函数从哪里取得 | work[0] | work[1] |
| --- | --- | --- | --- |
| position | enumerate(groups) 的当前位置 | 0 | 1 |
| templates | 当前 group 中的原 Sample 对象 | A 的两份原 Sample 模板 | B 的两份原 Sample 模板 |
| spec | data_source.resolve_spec(spec_id) | 数据源登记的 A 规格 | 数据源登记的 B 规格 |
| spec_id | group[0].metadata["harbor_spec_id"]，并检查组内一致 | A 模板中的 harbor_spec_id | B 模板中的 harbor_spec_id |
| group_index | 当前组各 Sample 的 group_index，检查一致后取值 | 10 | 11 |
| instance_id | 当前组各 Sample 的 metadata["harbor_instance_id"]，检查一致后取值 | A 模板共用的实例 ID | B 模板共用的实例 ID |

`position` 是本批列表中的位置，`group_index` 是数据源提供的组编号，二者在本例分别为 0/10、1/11，不能混用。

本次最重要的交接是：**原来的模板没有消失，仍能通过 `item.templates` 取得。** 下游将 work 放进 pending、按配置分为 partition；后来 `_assign_partition_trials` 仍会读到这些模板。

读完返回 [父函数第 2 段](../../../../../../../step-010-harbor-rollout-entry/02-short-term-memory/functions/dressage/integrations/harbor/rollout.py/_run_harbor_rollout.md#load-source-groups) 的 `work = ...`，随后进入第 3 段 `pending = list(work)`。本轮不继续追配置注册器。

<details>
<summary>必要检查：为什么不能随便把几份模板混成一组</summary>

原函数要求组非空、组内 spec_id 相同、尝试槽位恰好依次为 0 到组长度减一、group_index 与实例 ID 一致，且数据源能解析规格。违反要求会抛错，不生成混合身份的工作组。这些检查保护上面的索引和归属关系，首读知道其作用即可。

</details>

## 我的直接表述（原话）

本次建卡要求的节选：

> 但是这个函数卡片里别的内容就不需要东
> 然后分别生成这三个函数卡片吧

这是范围确认，不代表本函数已经读懂。

用户本轮希望先分清数据来源：

> 对于resolve work
> 这里是否需要考虑的内容是
> 我会idao这里的group的内容是这些的情况下
> 我到底需要了解哪些是原来的data source的内容?
> 否则这里在我阅读完了get sample之后
> 哪些内容是从这里的datasource来的 我觉得很重要
> 因为之前在get sample中我已经知道了每一个sample具体大概是怎么样子的

助手核对：本函数只有完整 spec 需要调用数据源查回；模板、规格 ID、组号和实例 ID 从已拿到的 group 读取，position 则由当前遍历产生。此处区分的是本次读取来源，不否认 group 最初也由数据源生成。

随后用户概括：

> 也就是说这里就是在 原来的group的基础上加入这里的一系列的spec是我的理解

助手校准：方向正确；每组查回一个对应的 spec，并把原模板列表、spec、身份和位置包装成新的 _GroupWork，不是给每个原始 Sample 直接增加 spec 字段。

## 尚不清楚

- 用户已表达给原组补齐 spec 的主干理解；group 保留原模板、_GroupWork 是新包装对象的细节由助手补充，后续结合使用处确认。
- 规格注册与每个检查的异常路径未展开；后续局部 templates 字典与这里 templates 列表的区别在 _assign_partition_trials 中继续对齐。

<details>
<summary>完整源码与验证依据</summary>

Dressage 固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`；源码 [rollout.py:361–410](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/rollout.py#L361)。仅静态核对；示例字段为教学构造，不是实际任务或运行结果。

```python
def _resolve_work(data_source: Any, groups: Sequence[list[Any]]) -> list[_GroupWork]:
    work: list[_GroupWork] = []
    for position, group in enumerate(groups):
        if not group:
            raise HarborRolloutError(f"Harbor source group {position} is empty")
        first_meta = _metadata(group[0])
        spec_id = str(first_meta.get("harbor_spec_id") or "")
        if not spec_id:
            raise HarborRolloutError(
                f"Harbor source group {position} has no harbor_spec_id"
            )
        if any(str(_metadata(sample).get("harbor_spec_id") or "") != spec_id for sample in group):
            raise HarborRolloutError(
                f"Harbor source group {position} mixes prompt specs"
            )
        slots = [
            _metadata(sample).get("harbor_attempt_slot") for sample in group
        ]
        if slots != list(range(len(group))):
            raise HarborRolloutError(
                f"Harbor source group {position} has invalid attempt slots {slots!r}"
            )
        group_indices = {getattr(sample, "group_index", None) for sample in group}
        if len(group_indices) != 1 or None in group_indices:
            raise HarborRolloutError(
                f"Harbor source group {position} has inconsistent group_index"
            )
        instance_ids = {
            str(_metadata(sample).get("harbor_instance_id") or "")
            for sample in group
        }
        if len(instance_ids) != 1 or "" in instance_ids:
            raise HarborRolloutError(
                f"Harbor source group {position} has inconsistent instance identity"
            )
        resolver = getattr(data_source, "resolve_spec", None)
        if not callable(resolver):
            raise HarborRolloutError("data source does not expose resolve_spec(spec_id)")
        spec = resolver(spec_id)
        work.append(
            _GroupWork(
                position=position,
                templates=list(group),
                spec=spec,
                spec_id=spec_id,
                group_index=int(next(iter(group_indices))),
                instance_id=next(iter(instance_ids)),
            )
        )
    return work
```

形成过程：[Step 010 数据形状补读](../../../../../../../step-010-harbor-rollout-entry/04-flow.md#data-shape-function-cards)。

</details>
