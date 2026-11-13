> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/rollout/artifacts/samples.py/instance_id.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/rollout/artifacts/samples.py/instance_id.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/rollout/artifacts/samples.py/instance_id.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/rollout/artifacts/samples.py/instance_id.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# instance_id（generate 中的别名 _instance_id）

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/03-long-term-memory/functions/dressage/rollout/artifacts/samples.py/instance_id.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/03-long-term-memory/functions/dressage/rollout/artifacts/samples.py/instance_id.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

- 源码定位：[samples.py:42](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/artifacts/samples.py#L42)。
- 首次单独展开：Step 001，2026-11-05。
- 最近认识更新：2026-11-06；用户询问 instance_id 是否为沙箱编号，助手据源码区分，尚待用户确认。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 确定 session_id 后，取得本次运行关联的题目/任务实例标识。
2. **具体内容**：优先返回 metadata.instance_id；否则用 sample.group_index；再没有则生成 UUID，最终返回字符串。本函数不写回 sample。
3. **建议构建的心智模型**：

   > session_id 用来标识执行会话，instance_id 用来关联任务实例。这里按已有字段取标识，缺失时兜底生成，不读取题目内容，也不创建环境。

4. **调用代码**（generate:138–141）：

   ```python
   session_id = ensure_blackbox_session_id(sample)
   instance_id = _instance_id(sample)
   metadata["session_id"] = session_id
   metadata["instance_id"] = instance_id
   ```

   导入语句使用 instance_id as _instance_id，因此是同一个函数。

## 本场景的输入与输出

教学输入：sample.metadata = {"instance_id": "repo__issue-17"}，sample.group_index = 3。

输出：字符串 "repo__issue-17"。若 metadata 无 instance_id，则返回 "3"；两处均为 None/缺失时返回新 UUID 的字符串。这些是静态推导，未实际执行训练。

完整函数：

```python
def instance_id(sample: Any) -> str:
    metadata = getattr(sample, "metadata", None)
    metadata = metadata if isinstance(metadata, dict) else {}
    value = metadata.get("instance_id")
    if value is not None:
        return str(value)
    group_index = getattr(sample, "group_index", None)
    return str(group_index if group_index is not None else uuid.uuid4())

```

1. 读取 metadata；它不是字典时，本函数用局部空字典查询，不修改 sample.metadata。
2. metadata 中 instance_id 非 None 时，转为字符串返回。
3. 否则读取 group_index；非 None 就用它，否则新建 UUID，再返回字符串。0 也可以是有效 group_index。
4. 返回 generate 后，调用者才将两个 ID 写入 metadata。

同一道题的多次执行可以关联相同 instance_id 和不同 session_id，但本函数不会自行验证这种对应；实际是否稳定取决于上游字段。尤其 UUID 兜底本身不能识别两份 sample 是否同题。

## 我的直接表述（原话）

2026-11-06 原话节选：

> instance id用来标记
> 这个sandbox的instance的id是什么?

助手澄清：它关联任务实例；沙箱资源编号另为 lease.sandbox_id。完整语境见本步 04-flow。

## 尚不清楚

- 任务实例 ID 与沙箱资源 ID 的区别已由助手解释，用户尚未确认理解。

- 上游具体怎样提供 instance_id 与 group_index，本轮未展开。
- 下游如何用两个标识关联轨迹与结果，随主线阅读。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 核对 samples.py:42–49，以及 blackbox_dispatch.py 的导入、139/141 行调用与写回。
- 静态源码阅读，没有运行 Agent、环境或训练。
- [本步过程](../../../../../../../../../01-native-agent-rollout/steps/step-001-task-identity-and-parameters/04-flow.md)。

</details>
