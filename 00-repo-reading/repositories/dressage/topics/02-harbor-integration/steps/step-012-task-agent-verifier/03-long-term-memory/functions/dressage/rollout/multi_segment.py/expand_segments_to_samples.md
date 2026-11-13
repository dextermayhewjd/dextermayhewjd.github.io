> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/rollout/multi_segment.py/expand_segments_to_samples.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/rollout/multi_segment.py/expand_segments_to_samples.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/rollout/multi_segment.py/expand_segments_to_samples.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/02-short-term-memory/functions/dressage/rollout/multi_segment.py/expand_segments_to_samples.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

# expand_segments_to_samples

- 源码：[dressage/rollout/multi_segment.py:118–192](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/multi_segment.py#L118)。
- 首次单独展开：Step 008，2026-11-08。
- 最近说明更新：2026-11-08；已接清逐段复制和字段写入的主线；本轮返回外层的归属、奖励字段与列表收集。

[来自 generate](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#extract-segments) → **本函数** → write_sample_from_segment → 返回本函数的段循环 → 返回 generate 的 result。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 已从 trajectory_payload.data 取得轨迹段，将它们和原任务 sample 一起传进来。
2. **具体内容**：确定身份信息，按段编号排序；每段深拷贝一份模板，委派填写训练字段，补原轨迹归属并设置非末段奖励，最后返回 Sample 列表。
3. **建议构建的心智模型**：

   > 一段轨迹生成一份 Sample：先复制原任务模板，再填入这一段的数据，并保留它属于哪次执行。

   输入已经是分好的段，不在这里重新切分轨迹或拼接 StepRecord。multi_segment 是模块名，当前入口是其中的 expand_segments_to_samples。

4. **调用代码**（generate:324–331）：

   ```python
   result = multi_segment.expand_segments_to_samples(
       sample,
       segments,
       args=args,
       agent_response=agent_response,
       session_id=session_id,
       instance_id=instance_id,
   )
   ```

## 本场景的输入与输出

输入：template_sample 是原任务的 Sample 模板；segments 是 Proxy 返回的轨迹段字典列表；args 是配置；agent_response 是此前 Agent 调用结果整理出的字符串，不能预设它一定是纯净最终回答；session_id/instance_id 指定本次会话和任务。

正常输出：按 segment_index 排序的 Sample 列表，一段对应一份。模板被深拷贝，本函数的字段写入落在各份副本上。无段或重复段编号时抛 ValueError，当前只保留这两个影响输入合同的边界，不展开失败处理链。

<a id="prepare-and-copy"></a>

### 1. 准备身份与段顺序（153–171）

```python
# 当前 generate 显式传了这两个 ID；否则才从模板中回退读取。
sid = session_id if session_id is not None else getattr(template_sample, "session_id", None)
template_metadata = getattr(template_sample, "metadata", None)
if instance_id is not None:
    iid = instance_id
elif isinstance(template_metadata, dict):
    iid = template_metadata.get("instance_id")
else:
    iid = None

# 让后面的逐段处理顺序稳定。
sorted_segments = sorted(segments, key=lambda s: int(s.get("segment_index", 0)))
seg_indices = [int(s.get("segment_index", 0)) for s in sorted_segments]
if len(set(seg_indices)) != len(seg_indices):
    raise ValueError(f"duplicate segment_index in segments: {seg_indices}")
last_idx = len(sorted_segments) - 1

# 各份新 Sample 将共享这个 rollout_id，取自原模板的 index。
rollout_id = getattr(template_sample, "index", None)
```

上述为原函数节选；导入与空列表检查见文末。当前先记住：按段编号排序，每段使用同一份任务/会话归属信息。rollout_id 和 session_id 的取值来源不同，不把它们当作同一个字段。

### 2. 每段复制一份模板，再委派填入段数据（173–185）

```python
out: list[Any] = []
for i, segment in enumerate(sorted_segments):
    sample = copy.deepcopy(template_sample)  # 为当前这一段准备独立副本。
    sample.rollout_id = rollout_id

    write_sample_from_segment(
        sample,                         # 要填写的副本。
        args=args,
        segment=segment,                # 当前这一段的数据。
        all_segments=sorted_segments,
        session_id=sid,
        instance_id=iid,
        agent_response=agent_response,
    )
```

template_sample 是 generate 传来的原任务 sample，通常已经带有题目和任务信息，并非专门新建的一份空模板。每段先复制这份对象，再把段的数据写进副本。write_sample_from_segment 是修改传入的 sample；调用处没有另接一个新返回值。本轮已进入 [write_sample_from_segment 函数卡](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/rollout/artifacts/samples.py/write_sample_from_segment.md#write-training-arrays)，先看 tokens、mask、logprob 的写入。

两段的形状示意：同一 template_sample 分别复制成 sample_A、sample_B，再分别写入段 A 和段 B。不是把两段全部塞进同一个 Sample，也不是把段字典直接改名为 Sample。

<a id="return-to-segment-loop"></a>

### 3. 返回段循环：归属、奖励字段与收集（186–192）

```python
    sample.metadata["parent_traj_id"] = sid  # 同一条原始轨迹的 Sample 共享归属。
    sample.metadata["segment_index"] = int(segment.get("segment_index", 0))  # 当前段号。
    if i != last_idx:
        sample.reward = 0.0  # 当前语句只给非末段设置 0。
    out.append(sample)
return out
```

这些语句发生在 write_sample_from_segment 返回之后。此时仍使用刚才那份已填写的 sample，依次补归属、调整奖励字段、追加到 out。

1. parent_traj_id 保存原始轨迹 ID；一个任务产生多段，不能仅因形成多个 Sample 就把它们当作多次独立答题。
2. segment_index 保存每份 Sample 的段位置；共同 rollout_id 已在本轮循环开头设置。
3. 非末段 reward 设为 0.0，末段在这里不被改写。常见模板 reward=None 时，末段保留 None，供后续奖励流程处理；这不是本函数已经评测出“前面几段做错了”。完整奖励计算/传播算法当前不下钻。
4. 每轮 out.append(sample) 收下该段的副本；全部完成后 return out，generate 的 result 接住列表。

两段正常例子，假设模板 index=7、reward=None，会话 ID 为 run-a：

| 返回样本 | rollout_id | parent_traj_id | segment_index | 当前 reward |
| --- | --- | --- | --- | --- |
| Sample A | 7 | run-a | 0 | 0.0 |
| Sample B | 7 | run-a | 1 | None |

这是静态数据形状示意，不是两次任务的评测结果。如果模板已有 reward，末段保留的就是该值，不能无条件声称末段一定是 None。

下一处返回 generate 的 result 赋值处，确认其为 Sample 列表；外层 return 交回之前仍需执行 finally，属于 Step 009 的后续范围。

| 下一处 | 读完返回 |
| --- | --- |
| write_sample_from_segment（artifacts/samples.py:291） | 回到当前段循环，接着 parent_traj_id 与 segment_index 的写入 |
| 本函数 return out | generate 的 result 接住列表；外层 finally 尚未执行 |

## 我的直接表述（原话）

> 好的 那么看一下这里的这个multi segment?
> 看一这个内部具体在做的内容吧

本轮进入模块中的转换入口。

后续用户复述：

> 我简单的理解
> 这里的write sample 从每一个segment 当中填写片段到这里这里的这个template?
> 是我的理解?
> 这里已经有了一个模板是我的理解?

助手核对：已有模板的理解正确，template_sample 就是 generate 传来的原任务 sample。每段先 deepcopy 得到独立的 sample，再由 write_sample_from_segment 原地填写这个副本；不是将所有段反复写入原模板。

本轮接续表述：

> 好的 我理解了这里是一段段处理segment
> 好的那么继续吧
> 这里的step008 还有什么需要看的吗 ?

用户已表达逐段处理的理解；本轮据此回到外层尾段，补充原轨迹归属、非末段奖励字段和列表返回，尚不以此认定完整奖励算法已掌握。

本轮收束表述：

> 好的 那么是否可以考虑继续了呢?
> 目前需要看的内容都结束了?
> 这里就是从trajectory那里那晚所有的trajectory
> 然后通过么我iyigesegments
> 一点点往template里面加入对应的内容
> 然后作为为sample返回给外面是我的理解
>
> 那么现在看一下吧
> 这里是否适合写一个task flow然后进入step009

助手校准：处理的是本次执行取回的轨迹段，并非系统中的所有轨迹；每段写入单独复制的模板副本，最终返回 Sample 列表。正常主线可收束，完整奖励算法与可选路径仍保留未知。

## 尚不清楚

- write_sample_from_segment 的训练字段和整体职责已展开，具体可选分支的未知仍保留在其函数卡。
- 非末段 reward=0 与后续奖励处理的配合，返回循环后再看。

<details>
<summary>完整源码与验证来源</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。仅静态源码核对，未执行样本转换或训练。下面的后续逻辑保留完整，不表示已逐项掌握。

```python
def expand_segments_to_samples(
    template_sample: Any,
    segments: list[dict],
    *,
    args: Any,
    agent_response: str = "",
    session_id: str | None = None,
    instance_id: str | None = None,
) -> list[Any]:
    """Emit one Sample per segment, all deep-copied from ``template_sample``.

    Reuses ``rollout.artifacts.samples.write_sample_from_segment`` for per-segment
    Sample construction (tokens, loss_mask, logprobs, metadata, status),
    then applies multi-segment-specific fields:

      * ``rollout_id``: all segments share ``template_sample.index`` so slime's
        ``build_dp_schedule`` keeps them in one training step.
      * ``parent_traj_id``: set to ``session_id`` for reward_post_process
        grouping and log_rollout_data trajectory-mean computation.
      * ``segment_index``: position within the trajectory.
      * ``reward``: only the last segment (anchor) keeps ``reward=None`` so
        slime runs reward_fn; earlier segments get ``reward=0.0``.
        ``reward_post_process`` broadcasts the anchor's reward back.

    Segments are sorted by ``segment_index`` ascending. Duplicate indices
    raise ``ValueError`` (would cause reward_post_process to pick wrong anchor).

    Returns:
      list[Sample] of length ``len(segments)``, sorted by segment_index.
    """
    from dressage.rollout.artifacts.samples import write_sample_from_segment

    if not segments:
        raise ValueError("expand_segments_to_samples: empty segments list")

    sid = session_id if session_id is not None else getattr(template_sample, "session_id", None)
    template_metadata = getattr(template_sample, "metadata", None)
    if instance_id is not None:
        iid = instance_id
    elif isinstance(template_metadata, dict):
        iid = template_metadata.get("instance_id")
    else:
        iid = None

    sorted_segments = sorted(segments, key=lambda s: int(s.get("segment_index", 0)))
    seg_indices = [int(s.get("segment_index", 0)) for s in sorted_segments]
    if len(set(seg_indices)) != len(seg_indices):
        raise ValueError(f"duplicate segment_index in segments: {seg_indices}")
    last_idx = len(sorted_segments) - 1

    rollout_id = getattr(template_sample, "index", None)

    out: list[Any] = []
    for i, segment in enumerate(sorted_segments):
        sample = copy.deepcopy(template_sample)
        sample.rollout_id = rollout_id

        write_sample_from_segment(
            sample,
            args=args,
            segment=segment,
            all_segments=sorted_segments,
            session_id=sid,
            instance_id=iid,
            agent_response=agent_response,
        )

        sample.metadata["parent_traj_id"] = sid
        sample.metadata["segment_index"] = int(segment.get("segment_index", 0))

        if i != last_idx:
            sample.reward = 0.0

        out.append(sample)
    return out

```

[Step 008 形成过程](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/04-flow.md#expand-segments-entry)。

</details>
