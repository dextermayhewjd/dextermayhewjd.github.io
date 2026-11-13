> Step 011 继承：来自 [Step 010 完整记录](../../../../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/_backend_options_for_register.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/_backend_options_for_register.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/_backend_options_for_register.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/03-long-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/_backend_options_for_register.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# _backend_options_for_register

> Step 007 继承：来自 [Step 006 的 03-long-term-memory 记录](../../../../../../../../../../../01-native-agent-rollout/steps/step-006-agent-execution/03-long-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/_backend_options_for_register.md)；保留原话、来源与未知，继承不表示新增掌握。

> Step 006 继承：来自 [Step 005 的 03-long-term-memory 记录](../../../../../../../../../../../01-native-agent-rollout/steps/step-005-agent-registration/03-long-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/_backend_options_for_register.md)；保留前序原话、认识时间和未知，不表示本步新增掌握。

- 源码定位：[dressage/rollout/generate/blackbox_dispatch.py:61](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/rollout/generate/blackbox_dispatch.py#L61)。
- 首次单独展开：Step 001，2026-11-06。
- 最近认识更新：Step 001，2026-11-06；用户提出类型配置与默认配置合并的理解，助手补充类型选择与覆盖关系。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：命令计划之后，为本次 Agent 注册准备 backend_options。
2. **具体内容**：从 metadata 取 backend_options，委托 merge_backend_options 结合 Agent 类型、默认配置及 args 合并。
3. **建议构建的心智模型**：

   > 先按 Agent 类型找到默认配置，再把本次任务的覆盖选项合进去，得到供注册使用的 backend_options。
   >
   > 1. **类型决定选哪套默认值。** blackbox_type 是 opencode、claude_code 等类型名称，不是要合并的配置字典。
   > 2. **汇合默认值与本次任务选项。** 默认值包含该类型的内置配置、适用的环境变量配置，以及条件满足时从 args 推导的配置；metadata["backend_options"] 是本次任务提供的覆盖值。
   > 3. **本次任务的显式值优先。** 嵌套字典递归合并，指定的值覆盖默认值，未覆盖的默认字段保留；不修改原输入字典。
   > 4. **返回配置，尚未注册。** env_args 描述环境需求，backend_options 描述 Agent 后端选项；后续 paddock.register_agent 才接收这些选项。

4. **调用代码**：

   ```python
   backend_options = _backend_options_for_register(
       args=args,
       metadata=metadata,
       blackbox_type=blackbox_type,
   )
   ```

## 本场景的输入与输出

完整函数：

```python
def _backend_options_for_register(
    *,
    args: Any,
    metadata: dict[str, Any],
    blackbox_type: str,
) -> Any:
    backend_options = metadata.get("backend_options")
    return merge_backend_options(blackbox_type, backend_options, args=args)

```

1. metadata.backend_options 是调用者提供的覆盖选项。
2. blackbox_type 决定采用哪种 Agent 后端默认值；args 在适用条件下参与动态默认值，例如模型上下文/输出限制、温度等。
3. merge_backend_options 将用户字典覆盖到默认值上，嵌套字典递归合并，不修改原输入。若用户值非 None 且非字典，会原样返回，不能假设该函数永远返回字典。
4. 返回 generate，之后可补入采样种子，再通过 paddock.register_agent(..., backend_options=backend_options) 传下去。

### 为什么同一个选项会有不同的值

以 Claude Code 为例：

1. **框架提供通用默认值。** 源码中默认最多运行 20 轮：

   ```python
   {"max_turns": 20}
   ```

2. **本次任务有不同要求。** 假设只希望最多运行 8 轮，就提供：

   ```python
   metadata["backend_options"] = {"max_turns": 8}
   ```

3. **合并后，本次任务采用 8。** 其他未指定的配置沿用默认值，公共默认配置仍为 20。

这就是正常的配置覆盖：同一个选项，默认值与本次指定值不同。backend_options 还可以包含模型、权限、上下文压缩等配置，具体字段取决于 Agent 后端。

> 框架提供默认配置，每次任务只写需要调整的部分，再合成这次注册 Agent 要用的配置。

本轮只理解配置来源和覆盖关系。merge_backend_options 位于 paddock/blackbox/common/defaults.py:186；不展开每种 Agent 的全部默认字段。


## 我的直接表述（原话）

> 好的那么我们来看下一个部分吧
> 下一个函数是哪个?
> 是backend options for register对吗?
> 这里里面简单说了是blackbox的type的配置需要和默认配置融合?
> 所以这里需要写清楚?

助手澄清：blackbox_type 选择默认配置，真正与默认配置合并的是 metadata.backend_options；适用时还会从 args 形成动态默认值。此澄清不自动计为用户已掌握。

本轮追问：

> 好的
> 这里简单的把这里back end options改写了
> 也就是模型具体的id和名字?
> 我其实没有太大的理解为什么这里会产生冲突或者在什么情况下会出现不一样?

助手改用 max_turns 的默认值与任务覆盖值解释动机；配置范围与覆盖原因尚待用户反馈。

## 尚不清楚

- 为什么任务配置会与默认值不同、backend_options 的范围：已用轮数限制的例子补充，用户尚未确认。
- 后续执行与注册的内部机制，本轮仅定位交接，未继续下钻。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：3e3142fe8ea07e4504c3b20a936a4c201a3de44c。
- 基于本地源码静态核对，示例为教学构造；未启动 Agent、沙箱或训练。
- [本步过程](../../../../../../../../../../../01-native-agent-rollout/steps/step-001-task-identity-and-parameters/04-flow.md)。

</details>
