# HarborArtifactStore.write_job_manifest

- 归属：Dressage，[artifacts.py:537](/home/hongshi/projects/Dressage/dressage/integrations/harbor/artifacts.py:537)，固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独建卡：2026-11-16，Step 015；已讨论用途，内部代码待阅读，不标记掌握。
- [本步 scope](../../../../../../01-scope.md) · [返回 _run_partition](../rollout.py/_run_partition.md)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：各次尝试的 bundle 已保存，外层已经转换 Sample 并检查整组；现在传入成功组的尝试身份，登记最终选择。
2. **具体内容**：更新本 Job 各 bundle 的选用状态，组织最终结果索引；磁盘模式下写 bundle、最终指针和 manifest，最后标记该轮登记完成。
3. **建议构建的心智模型**：

   > 保存成功，不代表最终采用。这个函数接收上游给定的选择，将“哪些尝试最终采用”落实到结果状态和可查阅的清单里；它不重新按分数挑选结果。

4. **调用代码**（_run_partition 教学节选，省略路由统计参数）：

   ```python
   selected_keys = [
       key
       for outcome in outcomes_by_position.values()
       if outcome.succeeded
       for key in outcome.final_keys
   ]
   await artifact_store.write_job_manifest(
       result, final_keys=selected_keys, state=manifest_state, ...
   )
   # 外层随后补路由信息，按原顺序返回各组 outcome。
   ```

## 本场景的输入与输出

**输入**：JobResult 提供作业身份；final_keys 是上游决定采用的 `(trial_name, trial_id)`；state 表示 completed / partial / aborted；另有路由保证与任务网络统计。

**已有数据**：Store 的 `_bundles` 已登记各次尝试的结果。本函数先筛出属于当前 Job 的 bundle。

**输出和副作用**：修改 bundle 的选用状态；磁盘模式返回 manifest 的 Path，内存模式返回 None。无法确定 Job 身份时也提前返回 None。返回值不是 Sample 列表；当前调用方并不接收这个路径。

### ① 对照名单：哪些已保存结果最终采用？

源码节选，省略未选用原因的详细构造：

```python
final_key_set = set(keys)
for key, bundle in job_bundles.items():
    selected = key in final_key_set
    bundle.superseded = not selected
    bundle.reconciliation_generation = generation
    if not selected:
        # 源码还记录 ATTEMPT_NOT_SELECTED 或 JOB_ABORTED 失败原因。
        bundle.trainable = False
```

例如 A、B 两组的 bundle 都已保存，但只有 A 组通过检查：

| 已保存结果 | 是否在 final_keys | 更新后的 superseded | trainable |
| --- | --- | --- | --- |
| A 组的尝试 | 是 | False | 保留原值，不强制设 True |
| B 组的尝试 | 否 | True | False |

这是状态标记，不是删除未选用的文件。它也不是从多个结果中选最高分：选择已由调用方通过 final_keys 给出。

### ② 形成索引：最终结果与全部尝试都能追溯

构造 manifest 的字段节选：

```python
manifest = {
    # 源码另有 schema、作业身份、路由统计和时间等字段。
    "state": state,
    "generation": generation,
    "committed": False,
    "final_trials": finals,
    "attempts": [...],
}
```

- `final_trials`：最终结果的索引，包含 Trial 身份、bundle 路径和 trainable；找不到结果或某个 Trial 未选中时，也会留下相应标记。
- `attempts`：本 Job 已保存的全部尝试及选用状态，保留检查来路。
- `generation`：本轮结果登记的编号，不是模型生成次数或权重版本。

### ③ 写完这一轮结果登记，才标记 committed

磁盘模式的顺序如下；这是流程示意，不是完整源码：

```text
写 manifest（committed=False）
    → 写更新后的 bundle
    → 写各 Trial 的 final.json 指针或标记
    → 重写 manifest（committed=True）
    → 返回 manifest 路径
```

这样登记尚未完成的状态有明确标志；不能把中途写出某一个文件当成整轮登记成功。它不是整个训练作业的事务或优化器 checkpoint。底层原子写入及读取者恢复协议本轮不展开。

若不是 disk/both 模式，前面的内存状态仍已更新，但不执行上述磁盘写入，返回 None。

**读完回到 _run_partition**：最终登记完成后，外层返回各组 outcome；成功组带 Sample，失败组带错误信息。本函数不再次生成或转换 Sample。

## 我的直接表述（原话）

用户强调此前解释中的“保存成功，不代表最后一定采用”，并表示：

> 主要是你说的这个点 我觉得 未来会非常重要？

用户随后要求把本函数加入 scope，并要求提供函数卡。以上表示阅读关注点，不代表已经掌握内部提交协议。

## 尚不清楚

- 当前重点是保存与采用的分离，以及对应字段怎样变化。
- 多文件写入中断后的读取/恢复细节未展开；不作为开始环境接入的前置。

<details>
<summary>来源与验证</summary>

- 源码：artifacts.py:537–684；调用方 rollout.py:853–878。固定版本见开头。
- 仅静态源码核对与教学示意，未执行结果文件写入或训练。
- [本步讨论](../../../../../../04-flow.md)。

</details>
