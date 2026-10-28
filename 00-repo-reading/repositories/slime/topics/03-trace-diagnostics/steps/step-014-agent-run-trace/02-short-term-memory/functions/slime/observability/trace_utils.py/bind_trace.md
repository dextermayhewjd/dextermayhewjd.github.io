# bind_trace

> 使用角色：**官方明确列出的入口**。要先准备样本的追踪句柄时可直接调用；trace_span 接收 Sample 时也会在内部调用它。
>
> 当前调用链：[trace_span](trace_span.md#runtime-enter) → [_coerce_handles](_coerce_handles.md) → **bind_trace** → [_ensure_trace_carrier](_ensure_trace_carrier.md)。读完返回 _coerce_handles:621。

- 源码定位：[trace_utils.py:238–254](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L238-L254)，固定版本 18868a79。
- 首次接触：2026-10-27，Step 014 的 Sample 绑定回查。
- 最近认识更新：2026-10-27，用户已指出它返回 TraceHandle，并询问是否先初始化 Sample；当前围绕“准备 trace 字段，再创建句柄”继续核对。

## LLM 整理：使用场合、具体内容与心智模型

以下由助手核对源码后整理。

1. **使用场合**：官方指南用于在传递 Sample 给 helper 或任务前准备追踪句柄；本步内部调用则是 _coerce_handles 识别出 Sample 后取得这个句柄。
2. **具体内容**：委托 _ensure_trace_carrier 准备追踪字典，将返回值赋给 sample.trace；再创建 carrier 指向该字典的 TraceHandle。
3. **建议构建的心智模型**：

   > 为这个 Sample 绑定追踪字典，并交回访问该字典的句柄。句柄和样本关联同一份 trace 数据。

4. **调用代码**：业务侧见下面的“使用方法”；_coerce_handles 内部的绑定调用保留在后面的机制说明中。

<a id="usage-method"></a>

## 使用方法：Slime 中的真实调用

<a id="official-basic-usage"></a>

**官网的基础定位**：在 sample 交给其他 helper 或任务之前准备好追踪容器。[官方 Trace 指南](https://thudm.github.io/slime/developer_guide/trace.html#instrument-custom-code)将 bind_trace 单独列为入口，没有要求与 export_trace/import_trace 固定搭配。

```python
# 基础绑定：可独立使用，返回可用的 TraceHandle
handle = bind_trace(sample)
```

这行的[实际输入与输出左右对照](../../../../examples/bind-trace/README.md#bind-trace-input-output)放在案例 README 中：输入是 Sample，返回是完整六字段的 TraceHandle，两者共享同一个追踪字典。本次单独调用的结果已保存，未混入后续 export/import 或 span 的效果。

按实现，这一步已经完成 sample.trace 的准备并返回 TraceHandle。仓库测试还直接使用 `Session(sampling_defaults={"max_new_tokens": budget}, trace=bind_trace(sample))`，没有经过 export/import；见 [test_sampler_replay.py:353–359](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/test_agent/test_sampler_replay.py#L353-L359)。这是测试调用证据，与下面的业务组合场景区分。

### 当前业务案例：Coding Agent 会话的组合使用

**先看真实的使用方式**：[让 Adapter 会话接上样本的 Trace](../../../../examples/bind-trace/README.md)。同一份记录的前后结构图和连续代码，说明 bind_trace 怎样参与“共享记录、带上父阶段、交给会话”；具体函数作用与代码放在一起，完整 JSON 按需查看。

**这里在做什么**：为即将建立的 Adapter 会话接上当前任务的 Trace。这样 Agent CLI 后续发来的模型请求，可以在 Adapter 侧继续向本次任务的记录里写事件。

**真实调用位置**：[_generate，generate.py:270–279](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L270-L279)。以下保留 session 与 trace 的真实实参，省略其他会话配置，并加说明注释：

```python
# Coding Agent 的组合场景：export/import 额外携带当前父阶段
# 它们不是每次调用 bind_trace 都必须接上的步骤
adapter.open_session(
    session_id,
    trace=import_trace(export_trace(bind_trace(base_sample)), base_sample.trace),
)
```

**调用前**：沿外层 generate 的正常入口，229 行已经进入 coding_rollout，因此 base_sample 通常已经有 trace 和外层开始事件。这里的 bind_trace 会复用该容器，不应把真实场景说成“一定从空 events 开始”。

**调用后的交接**：

```text
bind_trace(base_sample)
    → 返回 h，h.carrier 与 base_sample.trace 是同一字典
export_trace(h)
    → 返回身份与当前父阶段的 payload，不含 events
import_trace(payload, base_sample.trace)
    → 返回给 Adapter 使用的句柄，仍指向同一容器
adapter.open_session(...)
    → 会话保存该句柄：adapter.store[session_id].trace
```

**本函数直接产生的结果**是 h，既有事件保留，没有新增事件；**整段组合的结果**是 Adapter 会话关联到当前任务的 Trace。会话字段的真实写入见 [BaseAdapter.open_session:275–292](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L292)，后续使用见 [_run_turn:412–423](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L412-L423)。具体数据见[案例 C](../../../../examples/bind-trace/README.md)；下方保留三个配套工具的交接边界。 后续 span 已另做[实际执行](../../../../examples/bind-trace/README.md#actual-agent-model-turn)：绑定本身新增 0 条，agent_model_turn 和 agent_tokenize 共新增 4 条。

本节以固定源码 18868a79 的外部业务调用为依据；结果是正常路径的静态推导，未取得本轮真实 Agent/模型运行日志。[调用证据](../../../../../references/real-usage-evidence.json) · [本轮补充](../../../../../../step-014-agent-run-trace/04-flow.md#step014-real-business-usage)。

### 配套组合：身份怎样传递，事件仍放在哪里

这些接口放在同一真实会话调用里理解，不另增必读函数卡。下面先后解释导出、导入，再看 Adapter 后续怎样取到写入目标。

<a id="tool-export"></a>

**export_trace(h)** 返回 version、trace_id、sample_id、group_id、attempt、parent_span_id 六项元数据；不包含 events，也不新增事件。它说明“属于哪条追踪、接在哪个阶段下”。[源码 289–308](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L289-L308)。

<a id="tool-import"></a>

**import_trace(payload, base_sample.trace)** 返回接收侧句柄。本次显式传入原字典，所以仍共享事件容器；调用本身不复制历史事件。若换成新的接收字典，行为如下（接口边界示意，不是另一处业务调用）：

```python
received_trace = {}
received_handle = import_trace(payload, received_trace)
```

received_trace 获得追踪身份与空 events，received_handle 带有传入的父阶段编号。此后对这个句柄写的事件只进入 received_trace，不会自动汇回原样本；省略接收字典时也会新建容器。[源码 311–323](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L311-L323)。

<a id="tool-bind-carrier"></a>

**bind_trace_carrier(s.trace.carrier)** 从会话已有的普通字典取得句柄。Adapter 的真实后续使用如下，裁剪自 [_run_turn:412–423](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L412-L423)，省略 tokenize 的具体实参：

```python
with trace_span(s.trace, "agent_model_turn", record_error=False) if s.trace else nullcontext():
    target = bind_trace_carrier(s.trace.carrier) if s.trace else None
    with trace_span(target, "agent_tokenize", record_error=False) if target else nullcontext():
        translated, tools_schema = self._translate(body)
        prompt_ids = _session_prompt_ids(...)
    turn = await call_sglang_generate(prompt_ids, s, body, adapter=self, session_id=sid)
```

target.carrier 仍是该会话的原容器，随后阶段事件写入它。独立使用时，这个函数也可准备空字典；但不会自动把字典挂到某个 Sample，也不写文件。[绑定源码 257–286](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L257-L286)。

以上边界从旧过程说明归回本卡，未增加网络传输或模型请求实验，也不表示用户已掌握。[本轮归并](../../../../../../step-014-agent-run-trace/04-flow.md#step014-procedures-retired)。

## 本场景的输入与输出

<a id="usage"></a>

<details>
<summary>旧的独立教学输入：从空样本准备句柄，不是上面的真实入口状态</summary>

### 直接使用：准备追踪句柄

以下是符合真实接口的独立教学样本；已导入 Sample 和 bind_trace。

```python
sample = Sample(index=7, group_index=2, prompt="demo")
handle = bind_trace(sample)
```

- **使用前**：新样本尚未绑定 trace，getattr(sample, "trace", None) 为 None。
- **使用后**：sample.trace 有 version、trace_id、sample_id、group_id、attempt、events 六个基础键，events=[]；返回 handle，且 handle.carrier is sample.trace。
- **留下在哪里**：容器在样本上；尚未追加任何事件。已有容器时复用，不清空旧事件。
- [源码 238–254](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L238-L254)。

trace_span 可直接接收 Sample，不要求业务总是先写这一行。这里的“准备”也不等于把事件保存到文件。

</details>

### 已有调用链：返回 _coerce_handles

输入：sample 是 _coerce_handles 传来的 base_sample，使用其 trace、index、group_index。

输出：本函数返回一个 TraceHandle。正常路径中，handle.carrier 与 sample.trace 指向同一个字典；返回列表是上一层 _coerce_handles 的工作。

**这次要收窄的理解**：传进来的 Sample 已经存在。本函数准备或复用的是它的 sample.trace 字典，再创建一个 TraceHandle；它没有创建新的 Sample。_coerce_handles 负责类型分派与列表遍历，bind_trace 负责其中 Sample 这一条路的追踪绑定。

### 本函数的两段处理

以下是 240–251 行的正常路径，省略外围异常处理：

```python
sample.trace = _ensure_trace_carrier(
    getattr(sample, "trace", None),
    sample_id=sample.index,
    group_id=sample.group_index,
)
return TraceHandle(
    trace_id=sample.trace["trace_id"],
    carrier=sample.trace,
    sample_id=sample.trace.get("sample_id"),
    group_id=sample.trace.get("group_id"),
    attempt=int(sample.trace.get("attempt", 0)),
)
```

1. **准备已有 Sample 的 trace 字段**：getattr(sample, "trace", None) 取得原有字典或 None；先执行等号右边的 _ensure_trace_carrier，再将其返回值赋给 sample.trace。已有字典会复用并补齐字段；没有时创建字典。具体字段准备若仍不清楚，进入[下一层卡片](_ensure_trace_carrier.md)，读完回到本卡的赋值处。
2. **创建句柄**：从准备好的字典读取标识字段，将整个字典作为 carrier 交给 TraceHandle。

```text
sample.trace ────┐
                ├── 同一份追踪字典
handle.carrier ──┘        └─ events
```

**返回上一层**：[_coerce_handles:621](_coerce_handles.md)接到这个 handle，再将它装进 [handle] 返回。

## 我的直接表述（原话）

本次初步理解：

> 简单来看好象是返回了一个tracehandle 这是我的理解
>
> 也就是如果是一个sample
> 那么就先初始化了这里的sample之后
> 返回了一个这里的tracehandle？

用户对返回值的判断成立；“初始化 sample”由助手进一步区分为准备 trace 字段，尚待确认。[本次过程](../../../../../04-flow.md#step014-bind-trace-reading)。

此前对这条调用链提出的要求：

> 否则在一个函数里面说完了这一系列的内容我觉得我并不是特别清楚这里的一系列的调用关系
> 会非常的模糊

## 尚不清楚

- 用户已指出返回 TraceHandle；准备的是已有 Sample 的 trace 字段、句柄与样本共享字典的关系，仍待用户反馈。
- 252–254 行异常时返回 _noop_handle 的降级路径，本轮未展开。

<details>
<summary>来源、验证与完整例子</summary>

- [官方指南](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/trace.md)；[官方角色核对](../../../../../references/official-trace-api-review.json)；[本轮记录分工](../../../../../../step-014-agent-run-trace/04-flow.md#step014-scope-summary-short-term-usage)。
- 固定源码：[bind_trace](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L238-L254)；[TraceHandle 字段](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L58-L65)。
- [本次分层整理](../../../../../04-flow.md#step014-function-layers)。静态源码核对，未运行真实 Agent。

</details>
