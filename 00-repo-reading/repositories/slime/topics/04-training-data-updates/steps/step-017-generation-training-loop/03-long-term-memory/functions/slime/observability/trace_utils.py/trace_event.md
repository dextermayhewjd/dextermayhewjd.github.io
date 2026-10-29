# trace_event

> [返回 scope 的工具总览](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/01-scope.md#tool-catalog)。使用角色：**官方明确列出的入口**。

- 源码定位：[trace_utils.py:326–341](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L326-L341)，固定版本 18868a79。
- 首次接触：Step 014，2026-10-27 的完整工具用法核对；本轮从 scope 迁入函数卡。
- 最近认识更新：尚无针对本函数的直接理解表述。迁移与补充助手说明不计为用户新增认识。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手按官方指南及固定源码整理。

1. **使用场合**：需要留下某个瞬间，例如工具已经开始执行；不需要测量这一调用区间的持续时间。
2. **具体内容**：把目标规范成句柄，将一个带名字、时间和可选属性的 event 追加到每个目标的 carrier。
3. **建议构建的心智模型**：

   > 给样本时间线加一个点。持续多久要用 trace_span 的开始/结束配对来表示。

4. **调用代码**：当前未找到 trace_utils.py 外的真实 Python 调用；下面区分检索事实与已有教学例子。

<a id="usage-method"></a>

## 使用方法：Slime 中的真实调用

**检索结果：当前没有可展示的真实外部业务调用。** 在固定版本中，排除 trace_utils.py 后，对仓库 Python 与 Markdown 搜索 trace_event，找到的是中英文官方指南的接口说明，没有外部 Python 调用点；因此也没有可据此展示的业务运行结果。

官方说明它用于瞬时事件，这能证明接口的预期用途；实现能说明它会追加怎样的记录，但都不能替代用户要求的真实业务场景。

原卡的 tool_started / pytest 是助手构造的教学值，下面折叠保留，不再作为本卡的主用例。若只沿实际调用学习，当前先进入 trace_span、trace_function 或 SGLang 元信息组合即可。

本节记录固定源码 18868a79 的外部调用检索结果；没有找到实际调用，所以不填写真实业务结果。[调用证据](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/real-usage-evidence.json) · [本轮补充](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-real-business-usage)。

## 本场景的输入与输出

暂无真实业务场景的输入输出；只有接口说明和教学构造，不能标为本次真实使用结果。

<details>
<summary>原教学例子：展示接口行为，不作为真实业务证据</summary>

以下为教学样本，已导入 Sample 和 trace_event；不是仓库中一次真实工具运行的日志。

```python
sample = Sample(index=7, group_index=2, prompt="demo")
trace_event(sample, "tool_started", attrs={"tool": "pytest"})
```

- **使用前**：样本没有这条事件；不需要手动先调用 bind_trace。
- **使用后**：events 新增一条记录，关键内容为 type="event"、name="tool_started"、ts=当前时间、attrs={"tool": "pytest"}，并带目标身份；返回 None。
- **留下在哪里**：sample.trace["events"]。它不会自动生成一对开始/结束事件；有当前父阶段时记录父编号。
- [源码 326–341](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L326-L341)。

后续由调用方继续业务。事件已经在样本上，但落盘仍由[收集保存过程](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/trace-output-and-viewing.md)完成。

</details>

## 我的直接表述（原话）

尚无针对本函数用法的直接表述。用户本轮明确的是“scope 为总，short-term memory 具体描述”的记录分工，不能把该要求写成本函数已掌握。

## 尚不清楚

- 尚无用户对“瞬时事件”和“持续阶段”区别的独立复述。
- 自动目标推断、失败降级仅按需要回查，不在当前用法卡展开。

<details>
<summary>来源、验证与完整例子</summary>

- [官方指南](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/trace.md)；[官方角色核对](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/official-trace-api-review.json)；[本轮记录分工](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-scope-summary-short-term-usage)。
- 既有工具示例曾使用原 trace_utils 与从 types.py 提取的原 Sample 类隔离核对；本轮迁移既有说明，未执行真实 Agent 或模型请求。
- 原 scope 的完整正文保留在[迁移前快照](../../../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/scope-before-short-term-usage.md)。

</details>
