# HarborArtifactStore.write_job_manifest

- 归属：Dressage，[artifacts.py:537–684](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/integrations/harbor/artifacts.py#L537)，固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`。
- 首次单独建卡：2026-11-16，Step 015；已讨论用途，内部代码待阅读，不标记掌握。
- [本步 scope](../../../../../../01-scope.md) · [返回 _run_partition](../rollout.py/_run_partition.md)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：各次尝试的 bundle 已保存，外层已经转换 Sample 并检查整组；现在传入成功组的尝试身份，登记最终选择。
2. **具体内容**：更新本 Job 各 bundle 的选用状态，组织最终结果索引；磁盘模式下写 bundle、最终指针和 manifest，最后标记该轮登记完成。
3. **建议构建的心智模型**：

   > 保存成功，不代表最终采用。这个函数接收上游给定的选择，将“哪些尝试最终采用”落实到结果状态和可查阅的清单里；它不重新按分数挑选结果。

4. **调用背景**：来自 `_run_partition` 的组检查之后；该函数已决定采用名单，当前函数负责落实状态与清单。具体调用见下方。

## 本场景的输入与输出

<a id="selection-input-context"></a>

**先接调用方的数据流**：下面属于 `_run_partition`；直到 `await` 才进入当前函数。组检查修改 outcome，随后计算名单和状态，最后交给 Store 登记。

```python
# 进入这里时：
# outcome.samples    = 这组转换好的 Sample
# outcome.final_keys = 这些结果对应的 (trial_name, trial_id)
# ArtifactStore      = 已保存各次尝试的 bundle

# 1. 检查整组；不通过就设置 error，并将 samples 置为 None。
#    检查轨迹数量与配置要求的权重版本；具体语句省略。

# 2. 从成功组中提取身份，得到“采用名单”；此处不修改 Store。
selected_keys = [
    key
    for outcome in outcomes_by_position.values()
    if outcome.succeeded
    for key in outcome.final_keys
]
# 例：A 成功、B 失败 → 这里只留下 A 的尝试身份。

manifest_state = (
    "completed"
    if all(outcome.succeeded for outcome in outcomes_by_position.values())
    else "partial"
)
# 同一个例子 → "partial"；不是根据 reward 高低判断。

# 3. 进入当前函数：把决定交给 Store，更新 bundle 的选用状态。
await artifact_store.write_job_manifest(
    result,                     # JobResult：指明哪份 Job。
    final_keys=selected_keys,    # 采用哪些尝试；内容没变，只是参数名不同。
    state=manifest_state,       # 所有组成功，还是部分失败。
    # 路由统计参数省略。
)

# 4. 回到调用方：成功组和失败组都按原位置返回。
#    原码在返回前还补充路由摘要，这里省略。
return [outcomes_by_position[item.position] for item in partition]
```

以上是正常路径的源码裁剪，A/B 为教学示意。`outcome.succeeded` 判断的是 `error is None and samples is not None`。名单计算不会删掉失败组，也不会把名单本身变成 Sample。

<details>
<summary>第 3 步内部：名单怎样更新 bundle，并写入 manifest？</summary>

```text
final_keys：调用方给出的采用名单
  → 对照 Store 已有的 bundle，更新选用状态
  → 组织最终清单 manifest
  → 磁盘模式下写入结果和清单，最后标记 committed
```

#### ① 对照名单：哪些已保存结果最终采用？

**本段要解决的问题**：Store 中 A、B 的 bundle 都在，但名单只有 A，怎样落实这份选择？

源码节选；keys 是输入名单规范化后的结果，job_bundles 是当前 Job 的已保存结果，generation 是本次登记的新编号。省略未选用原因的详细构造：

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

这是状态标记，不是删除未选用的文件。它也不是从多个结果中选最高分：选择已由调用方通过 final_keys 给出。



#### ② 形成索引：最终结果与全部尝试都能追溯

**本段要解决的问题**：之后怎样查到采用的结果在哪里，以及其他尝试为什么没有被采用？

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



#### ③ 写完这一轮结果登记，才标记 committed

**本段要解决的问题**：多个结果文件尚未全部更新时，怎样表示本轮登记还没有完成？

磁盘模式的顺序如下；这是流程示意，不是完整源码：

```text
写 manifest（committed=False）
    → 写更新后的 bundle
    → 写各 Trial 的 final.json 指针或标记
    → 重写 manifest（committed=True）
    → 返回 manifest 路径
```

这样登记尚未完成的状态有明确标志；不能把中途写出某一个文件当成整轮登记成功。它不是整个训练作业的事务或优化器 checkpoint。底层原子写入及读取者恢复协议本轮不展开。

若不是 disk/both 模式，前面的内存状态仍已更新，但不执行上述磁盘写入，返回 None。无法确定 Job 身份时更早返回 None。state 也支持中止分支的 aborted；本例沿 partial 路径阅读。

**读完回到 [_run_partition](../rollout.py/_run_partition.md)**：最终登记完成后，外层补上路由摘要，按原顺序返回各组 outcome。上例仍返回 A、B 两组：A 带 Sample，B 带错误，失败处理交给上层。本函数不再次生成或转换 Sample。

</details>

**返回边界**：磁盘模式返回 manifest 的 Path，内存模式返回 None；找不到 Job 身份也返回 None。当前调用方不接收这个返回值，继续返回的是原来的各组 outcome。选中的 bundle 保留原 trainable 值；未选中的标为 superseded，并设 trainable=False，不删除已有结果。

## 我的直接表述（原话）

用户强调此前解释中的“保存成功，不代表最后一定采用”，并表示：

> 主要是你说的这个点 我觉得 未来会非常重要？

用户随后要求把本函数加入 scope，并要求提供函数卡。以上表示阅读关注点，不代表已经掌握内部提交协议。

本次阅读卡点（原话）：

> 或者说其实我不知道为什么及iuturan从bundle变成了到了当前的这个这一步?
> 之前的部分还需要吗?
> 当时选择function的时候到底为什么阅读这些呢?

本次按用户确认补充调用前的数据关系与例子；这些为助手核对的解释，不预填为用户已掌握。

## 尚不清楚

- 当前重点是保存与采用的分离，以及对应字段怎样变化。
- 多文件写入中断后的读取/恢复细节未展开；不作为开始环境接入的前置。

<details>
<summary>来源与验证</summary>

- 源码：artifacts.py:537–684；调用方 rollout.py:853–878。固定版本见开头。
- 仅静态源码核对与教学示意，未执行结果文件写入或训练。
- [本步讨论](../../../../../../04-flow.md)。

</details>
