# trace_function

> [返回 scope 的工具总览](../../../../../01-scope.md#tool-catalog)。使用角色：**官方明确列出的入口**。

- 源码定位：[trace_utils.py:451–496](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L451-L496)，固定版本 18868a79。
- 首次接触：Step 014，2026-10-27 的完整工具用法核对；本轮从 scope 迁入函数卡。
- 最近认识更新：尚无针对本函数的直接理解表述。迁移与补充助手说明不计为用户新增认识。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手按官方指南及固定源码整理。

1. **使用场合**：整个函数调用都应对应一个阶段；本仓库 generate_and_rm 按 sample 打点，generate_and_rm_group 按 group 打点。
2. **具体内容**：装饰器产生包装函数，在每次调用时解析目标，再用 trace_span 包住原同步或异步函数；保留业务返回值。
3. **建议构建的心智模型**：

   > 把“进入函数到退出函数”作为一个 span。不是先调用本函数，再要求业务手动调用一次同级 trace_span。

4. **调用代码**（官方指南与 sglang_rollout.py:288 起的真实声明；省略注解和函数体）：

```python
@trace_function("generate_and_rm", target="sample")
async def generate_and_rm(args, sample, sampling_params, evaluation=False):
    ...
```

<a id="usage-method"></a>

## 使用方法：Slime 中的真实调用

**具体数据案例**：[已完成样本及 reward=1.0 的真实返回分支](../../../../examples/trace-function-generate-and-rm/README.md)，含 input.json、expected.json 与隔离核对结果。

**这里在做什么**：组级 rollout 把每个样本交给 generate_and_rm，等待生成和可能的评分。装饰器为这个完整函数调用记录一个阶段，方便将整体耗时与其内部等待、生成、评分阶段联系起来。

**真实声明**：[sglang_rollout.py:288–294](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L288-L294)。仅省略注解和函数体：

```python
@trace_function("generate_and_rm", target="sample")
async def generate_and_rm(args, sample, sampling_params, evaluation=False):
    ...
```

**谁实际调用它**：同文件 generate_and_rm_group 的 [425–430 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L425-L430)。下列保留提交、等待与回填，省略循环外壳及参数准备：

```python
tasks[idx] = asyncio.create_task(generate_and_rm(args, sample, current_sampling_params, evaluation=evaluation))
results = await asyncio.gather(*tasks.values())
group = list(group)
for idx, result in zip(tasks, results, strict=True):
    group[idx] = result
```

**输入与结果**：target="sample" 指被调函数的参数名。开始执行包装函数时，用该参数确定记录目标；正常完成后，目标的事件列表有一对名为 generate_and_rm、span_id 相同的开始/结束记录。与此同时，业务返回的 Sample 或 list[Sample] 仍经 gather 进入 results，再写回 group[idx]。

**重要边界**：装饰器记录的是传入的目标，不会因为业务返回了新 Sample 就自动改换记录目标。当前调用未提供 attrs_getter，因此业务 reward 不会自动变成事件属性。此处使用 record_error 的默认 True，与 agent_run 主例的 False 不同。

如果需要观察函数内部某段，源码已经在 admission wait、pause wait 和 reward 等局部使用 trace_span；函数级和局部阶段可以同时存在。

本节以固定源码 18868a79 的外部业务调用为依据；结果是正常路径的静态推导，未取得本轮真实 Agent/模型运行日志。[调用证据](../../../../../references/real-usage-evidence.json) · [本轮补充](../../../../../../step-014-agent-run-trace/04-flow.md#step014-real-business-usage)。

## 本场景的输入与输出

上面的真实调用有两份不同产物：业务的 Sample 或列表交还 generate_and_rm_group；Trace 的开始/结束事件保留在输入目标的 carrier。本轮没有取得真实样本内容、时间戳或 reward 数值，不使用一个构造分数代替该调用的结果。

<details>
<summary>历史教学对照：score 返回 0.8，不是 Slime 的真实调用案例</summary>

真实声明中的 target="sample" 指该参数的名字，传入的 Sample 就是记录落点。下面沿用原 scope 的独立教学函数，让返回值可直接比较；已导入 Sample 和 trace_function。

score 是演示用的业务函数，不是 Slime 新增的工具接口：

```python
@trace_function("score", target="sample", record_error=False)
def score(sample):
    return 0.8

sample = Sample(index=7, group_index=2, prompt="demo")
value = score(sample)
```

- **使用前**：定义/装饰函数本身还没有运行业务，不会因此为样本追加事件。
- **使用后**：value=0.8；sample.trace["events"] 新增 name="score" 的 span_start 与 span_end，二者的 span_id 相同。
- **留下在哪里**：参数 sample 对应的容器。target="sample" 指参数名，不是固定要求所有业务都叫 sample。异步函数也有对应的 await 包装。
- **配套参数**：attrs_getter 可提供开始属性；目标需从多个参数组合取得时可用 target_getter。优先明确指定目标，找不到有效目标时可能只执行业务、不产生追踪。
- [源码 451–496](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L451-L496)。

### 如何与 trace_span 组合

官方建议：只有函数内部还要观察某个子阶段，或补充执行到一半才得到的属性时，再在函数内部使用 trace_span。外层表示整个调用，内层表示选中的子阶段，两者承担不同粒度。

本例没有设置 attrs_getter，因此返回的 0.8 不会自动成为事件的 reward 属性。业务返回值与追踪属性是两条交接。

</details>

## 我的直接表述（原话）

尚无针对本函数用法的直接表述。用户本轮明确的是“scope 为总，short-term memory 具体描述”的记录分工，不能把该要求写成本函数已掌握。

## 尚不清楚

- 同步/异步包装的实现细节未在本轮展开；官方支持两种形式。
- target_getter 与隐式目标推断留作回查；官方建议优先显式指定目标。

<details>
<summary>来源、验证与完整例子</summary>

- [官方指南](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/trace.md)；[官方角色核对](../../../../../references/official-trace-api-review.json)；[本轮记录分工](../../../../../../step-014-agent-run-trace/04-flow.md#step014-scope-summary-short-term-usage)。
- 既有工具示例曾使用原 trace_utils 与从 types.py 提取的原 Sample 类隔离核对；本轮迁移既有说明，未执行真实 Agent 或模型请求。
- 原 scope 的完整正文保留在[迁移前快照](../../../../../references/scope-before-short-term-usage.md)。

</details>
