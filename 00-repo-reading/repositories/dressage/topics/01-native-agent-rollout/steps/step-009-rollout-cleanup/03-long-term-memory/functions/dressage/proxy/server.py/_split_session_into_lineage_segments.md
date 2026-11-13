> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../step-008-segments-to-samples/03-long-term-memory/functions/dressage/proxy/server.py/_split_session_into_lineage_segments.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../step-007-proxy-finalization-and-trajectory/02-short-term-memory/functions/dressage/proxy/server.py/_split_session_into_lineage_segments.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# _split_session_into_lineage_segments

- 源码：[server.py:670–706](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/server.py#L670)。
- 首次单独展开：Step 007，2026-11-08。
- 最近说明更新：2026-11-08；本轮开始按函数阅读，不据此标记个人已掌握。

[来自 finalize 的分段调用](create_app.finalize_session.md) → **本函数** → 返回 lineage_segments。输入背景：[Session](../../../../classes/dressage/proxy/session_manager.py/Session.md) · [StepRecord](../../../../classes/dressage/proxy/session_manager.py/StepRecord.md)。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：Proxy 收尾时已经取得 Session，TITO 路径需要先确定哪些模型交互记录属于同一个轨迹段。
2. **具体内容**：按 Lineage.index 顺序遍历路径，从 session.steps 筛选该路径的记录；遇到本条之前的分段标记，就保存旧段、从本条开始新段。返回每段的 steps、路径信息和切分原因。
3. **建议构建的心智模型**：

   > 先把同一路径的模型记录放在一起，再沿着已有的边界标记切成段。

   这里只分组和切段，不拼接 token，不重新识别分支或判断是否发生 compact。

   lineage 回答“属于哪条历史路径”，segment 回答“这条路径里的哪些记录放在同一段”。例如路径 A 的 s1、s2、s3 中，s3 前有边界，则得到 A 的 [s1, s2] 与 [s3] 两段；两段仍属于 A。

4. **调用代码**（finalize 的 TITO 分支节选）：

   ```python
   lineage_segments = _split_session_into_lineage_segments(session)
   # 后面遍历 lineage_segments，逐段交给 _build_tito_lineage_segment_record。
   ```

## 本场景的输入与输出

输入是已有 Session，主要读取 session.lineages、session.steps 和各 StepRecord 的归属/边界字段。输出为 list[dict]；每个字典表示一段，包含 steps、segment_reason、segment_reasons、turn_ids、lineage_id、lineage_index、branch_from_step_id。steps 中保留原 StepRecord 对象的引用，不复制或修改 token 数据。

<a id="group-and-split"></a>

### 1. 按历史路径取出记录（671–678）

```python
segments: list[dict[str, Any]] = []
# 只对路径排序；不是把每个 step 按编号重新排序。
sorted_lineages = sorted(session.lineages.values(), key=lambda item: item.index)
for lineage in sorted_lineages:
    # 保留 session.steps 中的相对顺序，筛出当前路径的记录。
    lineage_steps = [
        step for step in session.steps if step.lineage_id == lineage.id
    ]
    current_steps: list[StepRecord] = []  # 正在积累的这一段。
    current_segment_reasons: list[str] = ["initial"]
    # ... 后续在这个 for 循环内部处理当前路径。
```

例如当前处理路径 A，就只取 step.lineage_id 等于 A 的记录；A 处理完再处理下一条路径。Lineage 已由前面的请求处理建立，本函数只使用它。

### 2. 遇到边界，保存旧段，再把当前 step 放进新段（698–705）

```python
for step in lineage_steps:
    if step.lineage_segment_boundary_before and current_steps:
        flush_segment()  # 保存前面积累的旧段，并换一个空列表。
        current_segment_reasons = list(
            step.lineage_segment_reasons_before or ["initial"]
        )
    current_steps.append(step)  # 有边界时，这条 step 是新段的第一条。
flush_segment()  # 这条路径遍历完，把最后一段也保存起来。
```

flush_segment 是下面完整代码里的局部函数，不需要另开卡。它把 current_steps 与路径/原因资料一起 append 到 segments，再令 current_steps = []。这不是清空已保存的列表；旧列表仍由刚保存的段引用。

`and current_steps` 避免在当前段还是空的时候切出空段。首段原因初始为 initial，不能把它误解成一定会复制第一条 step 上的所有原因标记。

### 3. 用三个记录看一次切分

静态教学例子，A 为一条已存在的路径，三条记录顺序为 s1、s2、s3；仅 s3 的 boundary_before 为 True：

```text
lineage A:  s1  ->  s2  |  s3
segments:  [s1, s2]     [s3]
```

结果是两段，s3 属于第二段。两段的 lineage_id 相同，但 segment_reasons 可以不同。此时段内仍是 StepRecord 列表，不是拼好的 tokens。

如果有路径 B，它独立处理，不与 A 的最后一段合并；分支来源编号被保存在 branch_from_step_id 中，函数不因此复制祖先记录。

### 4. 返回哪里

return segments → finalize 的 lineage_segments。下一处才是 `_build_tito_lineage_segment_record`：把一段 steps 的 concat 数据组织成轨迹记录。后续已按主线进入[本步构建器函数卡](create_app._build_tito_lineage_segment_record.md#join-token-mask)，先只看 token/mask 拼接。

## 我的直接表述（原话）

> 好的 那么继续吧
> 看一下这里的这个split session into lineage segments吧

随后用户概括：

> 我可以理解为lineage代表的是 这里的这个在统一路径的记录
> 但是会有边界?
> 是我的理解?

助手核对：这个层级关系正确。lineage 表示历史续接路径，step.lineage_id 标明归属；同一条路径内部仍可由 lineage_segment_boundary_before 切成多段。切段不等于新建 lineage，边界原因的判定仍未深入。

## 尚不清楚

- 边界与路径如何在前面的请求处理中被判定，当前只使用已有标记。
- 每段 steps 的 token、mask、logprob 怎样组合，留到构建函数。

<details>
<summary>完整函数与验证来源</summary>

以下为固定版本原函数，仅补中文注释。版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c；静态核对，未运行真实会话。示例为静态推导。

```python
def _split_session_into_lineage_segments(session: Session) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    sorted_lineages = sorted(session.lineages.values(), key=lambda item: item.index)
    for lineage in sorted_lineages:
        lineage_steps = [
            step for step in session.steps if step.lineage_id == lineage.id
        ]
        current_steps: list[StepRecord] = []
        current_segment_reasons: list[str] = ["initial"]

        def flush_segment() -> None:
            nonlocal current_steps, current_segment_reasons
            if not current_steps:
                return
            segments.append(
                {
                    "steps": current_steps,
                    "segment_reason": current_segment_reasons[0],
                    "segment_reasons": list(current_segment_reasons),
                    "turn_ids": _ordered_turn_ids(current_steps),  # 按出现顺序去重。
                    "lineage_id": lineage.id,
                    "lineage_index": lineage.index,
                    "branch_from_step_id": lineage.branch_from_step_id,
                }
            )
            current_steps = []  # 换新列表，不清空已保存的那份列表。
            current_segment_reasons = ["initial"]

        for step in lineage_steps:
            if step.lineage_segment_boundary_before and current_steps:
                flush_segment()
                current_segment_reasons = list(
                    step.lineage_segment_reasons_before or ["initial"]
                )
            current_steps.append(step)
        flush_segment()
    return segments
```

_ordered_turn_ids（server.py:630）仅按首次出现顺序收集不重复的 turn_id，本轮不另展开。

[本轮形成过程](../../../../../../step-007-proxy-finalization-and-trajectory/04-flow.md#lineage-split)。

</details>
