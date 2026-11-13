> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/paddock/blackbox/common/defaults.py/normalize_blackbox_type.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/paddock/blackbox/common/defaults.py/normalize_blackbox_type.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/paddock/blackbox/common/defaults.py/normalize_blackbox_type.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/paddock/blackbox/common/defaults.py/normalize_blackbox_type.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# normalize_blackbox_type

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/03-long-term-memory/functions/dressage/paddock/blackbox/common/defaults.py/normalize_blackbox_type.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/03-long-term-memory/functions/dressage/paddock/blackbox/common/defaults.py/normalize_blackbox_type.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

- 源码定位：[common/defaults.py:102](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/paddock/blackbox/common/defaults.py#L102)。
- 首次单独展开：Step 001，2026-11-06；最初内嵌于环境参数卡，本轮按用户要求拆分。
- 最近认识更新：Step 001，2026-11-06；用户理解为返回合适的 harness 名称，助手区分名称规范化与后端选择。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：generate 从 metadata 取得 Agent 后端类型后，先统一名称，再准备环境参数及后端配置。
2. **具体内容**：转为字符串、去掉首尾空白、转为小写；输入为假值或清理后为空时，采用默认类型 opencode。
3. **建议构建的心智模型**：

   > 把类型名称整理成统一写法。有名称就清理，没名称就用默认值；这里不查找或启动 Agent，也不验证该类型是否受支持。

4. **调用代码**（generate:142–144）：

   ```python
   blackbox_type = normalize_blackbox_type(
       metadata.get("blackbox_type") or DEFAULT_BLACKBOX_TYPE
   )
   ```

## 本场景的输入与输出

输入：metadata["blackbox_type"] 为 " Claude_Code "，调用时传入该字符串。

返回："claude_code"，由 generate 的局部变量 blackbox_type 接住；本函数不修改 metadata。

完整函数源码：

```python
def normalize_blackbox_type(blackbox_type: Any) -> str:
    """Return the canonical registry key for a blackbox backend."""
    value = str(blackbox_type or DEFAULT_BLACKBOX_TYPE).strip().lower()
    return value or DEFAULT_BLACKBOX_TYPE
```

1. 先用 or 处理假值输入。DEFAULT_BLACKBOX_TYPE 当前是 "opencode"；此调用方也已做一次默认值处理。
2. str、strip、lower 依次完成字符串转换、去首尾空白和转小写。
3. 清理后为空则再次回退到默认值。例如 "   " 起初不是空字符串，strip 后才为空，因此返回 "opencode"。

其他静态例子：None 和 "" 得到 "opencode"；" Unknown " 得到 "unknown"，说明它不验证类型是否存在。

**读完返回 generate:146–152**：调用者在 metadata 显式含 blackbox_type 或结果不是默认类型时，把规范化后的名称放入 extra_env_args。本例得到 {"blackbox_type": "claude_code"}，再交给 [paddock_env_args_from_metadata](../../../../rollout/generate/runtime.py/paddock_env_args_from_metadata.md) 合入环境参数。若未指定且结果为默认类型，extra_env_args 保持 None；显式指定 "opencode" 仍会加入该键。这些判断属于调用者，不是 normalize 的内部行为。

## 我的直接表述（原话）

此前用户确认阅读入口：

> 好的那么现在看一下normalize这个function对吗?
> 好的那么开始看一下吧

本轮对记录方式的反馈：

> 是否应该拆分一下
> 这里明显就不应该放在一起?

本轮理解：

> 简单来说这里的normalize blackbox type
> 更多的是一个比较能够返回合适的harness的名称是我的理解

助手校准：可以近似称为 harness／Agent 后端名称，但本函数仅统一名称格式、处理默认值，不判断后端是否适合任务，也不验证名称对应的后端存在。例如 " Claude_Code " 返回 "claude_code"，" Unknown " 仍返回 "unknown"。此校准尚待用户确认。

## 尚不清楚

- 类型是否受支持由下游哪处验证，本轮未展开。
- 用户已表达名称返回的理解；“合适”与“格式规范、缺省回退”的区别已由助手澄清，尚待确认。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 源码：paddock/blackbox/common/defaults.py:9、102–106；rollout/generate/blackbox_dispatch.py:142–152。
- 示例为静态推导，未运行后端或环境。
- 原记录位于环境参数卡的“调用前”段，现完整拆出并保留双向导航。
- [原始讨论与拆分过程](../../../../../../../../../../01-native-agent-rollout/steps/step-001-task-identity-and-parameters/04-flow.md)。

</details>
