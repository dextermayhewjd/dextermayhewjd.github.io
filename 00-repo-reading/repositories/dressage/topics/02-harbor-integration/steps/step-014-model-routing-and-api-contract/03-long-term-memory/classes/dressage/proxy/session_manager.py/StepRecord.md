> Step 011 继承：来自 [Step 010 完整记录](../../../../../../step-010-harbor-rollout-entry/03-long-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md)。保留原话、来源、日期及未深入边界；继承不代表本步已读。

本步继承：2026-11-13，完整来源为 [Step 013 快照](../../../../../../step-013-harbor-kubernetes-environment/03-long-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md)。保留原话、源码版本、认识时间与未解问题；继承不表示已经掌握。


- 本步继承：2026-11-13，由 [Step 012 来源卡片](../../../../../../step-012-task-agent-verifier/03-long-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md) 完整继承；复制不改变原认识时间或已掌握状态。

本步继承：[Step 011 来源记录](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md)。保留原始版本、认识时间、原话与未知；继承不表示新增理解。

> Step 010 跨主题继承：来自 [Step 009 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-009-rollout-cleanup/03-long-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md)。保留既有原话、认识时间、来源与未知；不代表本步重复阅读或新增掌握。

> Step 009 前序继承：来自 [Step 008 完整记录](../../../../../../../../01-native-agent-rollout/steps/step-008-segments-to-samples/03-long-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md)。原话、来源、认识时间与未知继续保留；继承不表示本步已读。

> Step 008 前序继承：来自 [Step 007 的完整记录](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/02-short-term-memory/classes/dressage/proxy/session_manager.py/StepRecord.md)。保留原话、认识时间与未知；继承不表示本步已读或新增掌握。

# StepRecord

[从 Proxy finalize 回查原料](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/functions/dressage/proxy/server.py/create_app.finalize_session.md) · [本步阅读导航](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/01-scope.md#current-reading)

- 源码：[session_manager.py:95](https://github.com/Accio-Lab/Dressage/blob/3e3142fe8ea07e4504c3b20a936a4c201a3de44c/dressage/proxy/session_manager.py#L95)。
- 首次单独展开：Step 007，2026-11-08。
- 最近说明更新：2026-11-08；当前介绍数据结构，不表示个人已掌握。

## 1. 一句话理解

> StepRecord 是 Proxy 为一次模型生成保存的记录：既保存这次输入输出，也保存后续分段和拼接所需的数据。

这里的 step 不是阅读步骤，也不是完整的一次 Agent 任务。一次 Agent 执行通常可能多次调用模型，对应多个 StepRecord；turn_id 与 step_id 也不必一一对应。

它是 dataclass，用于装数据；类声明本身不执行采集、分段或拼接。SessionManager.record_step 创建记录，再追加到 session.steps。此处只确认来源，不展开整条 API 采集链。

### 先找回来源：不是把 session 传入 StepRecord

真实创建处是 `SessionManager.record_step`（session_manager.py:491）。它先按 session_id 找到 session，再将这次模型交互的数据构造成 StepRecord，最后放入该 session：

```python
# 来自 record_step 的教学节选，省略其他字段与检查。
session = self._sessions.get(session_id)
step = StepRecord(
    turn_id=turn_id,
    request_messages=request_messages,
    prompt_token_ids=prompt_token_ids,
    response_token_ids=response_token_ids,
    # ... 其余本次模型交互和拼接数据。
)
session.steps.append(step)
```

关系是 **session 包含多条 StepRecord**。StepRecord 的构造参数是一组字段，不是一个 session；后面的分段函数才会接收整个 session 并遍历 session.steps。

### turn、step、lineage 先怎么区分

- turn_id：当前是哪一次交给 Agent 执行的 turn，不是 Agent 的名字或身份。一轮 Agent 执行可能调用模型多次。
- step_id：Proxy 中一次模型生成记录的编号。当前代码以 session 级计数器产生 step-000001 等，不是每个 Agent turn 从头计数，也不是每次工具操作都单独生成一条。
- lineage_id：本次记录属于哪条历史续接路径；已有历史继续与从旧位置分支需要区分。当前先理解归属，不展开路由算法。
- lineage_segment_boundary_before：同一路径中，是否需要在本条之前切一个新段；不是“是否 compact”的专门标记。当前赋值代码中包括工具定义变化、TITO 路由渲染失败、增量 token 化失败等原因（server.py:2074–2107）。

## 2. 先看三组字段

以下是原类字段的教学节选，按用途重排，非完整可实例化定义。完整原定义保留在文末。

### 2.1 这次模型看到了什么、生成了什么

```python
prompt_token_ids: list[int]                    # 本次模型输入的 token IDs。
response_token_ids: list[int]                  # 本次模型生成的 token IDs。
response_logprobs: list[float] | TQFieldRef     # 本次输出对应的 logprob 数据或传输引用。
messages_snapshot: list[dict]                 # 保存到这一步的消息快照。
raw_response_text: str                        # 本次记录的响应文本。
```

先按内存中的列表理解 logprob；TQFieldRef 是另一种传输表示，当前不展开。消息快照与 token 数据不是同一份东西：前者保留对话结构，后者供后续训练数据构建使用。

### 2.2 这一条记录为轨迹拼接提供什么

```python
concat_token_ids: list[int] = field(default_factory=list)
concat_response_logprobs: list[float] | TQFieldRef = field(default_factory=list)
concat_response_mask: list[int] = field(default_factory=list)
```

这三项在正常内存路径按位置对应：

- concat_token_ids：这一条要贡献给轨迹段的 token。
- concat_response_mask：哪些位置是本次模型输出；上下文位置为 0，输出位置为 1。
- concat_response_logprobs：对应位置的 logprob；构建时上下文位置填 0.0，输出位置放模型输出的 logprob。

**concat 并不等于只保存回答，也不等于每次重复放入完整 prompt。** 在普通 TITO 连续追加路径中，它保存新增上下文加本次输出；段首或新分支可能需要完整上下文。这里的材料已经在请求处理期间准备，finalize 才按段组装。

### 2.3 这条记录属于哪里，能否和前面接起来

```python
turn_id: str                                  # 所属 Agent turn。
step_id: str = ""                             # 本次模型生成记录的标识。
lineage_id: str = ""                          # 属于哪条历史续接/分支路径。
lineage_segment_boundary_before: bool = False # 本条前面是否需要开始一个新段。
```

下一处的 lineage 分段函数使用 lineage_id 分组，再根据 boundary 标记切段；不会把整个 session 中所有 step 无条件拼成一段。

## 3. 一个小例子：完整输入和拼接材料为什么不同

`step1_fields` / `step2_fields` 是本笔记为了展示字段而命名的示例字典，**不是源码中的变量、函数或 StepRecord 的参数名**。也不表示另一个需要阅读的组件。看不懂示例时，先读上面的对象来源即可。

下面只展示两条记录的部分字段，是手工构造的 TITO 连续追加示意，不是真实 tokenizer 输出，也不是完整 StepRecord 构造调用。假定前缀可以正常复用、没有分支或分段边界，省略消息模板符号。

```python
# 第一次：输入 [10, 11]，模型生成 [20]。
step1_fields = {
    "prompt_token_ids": [10, 11],
    "response_token_ids": [20],
    "concat_token_ids": [10, 11, 20],
    "concat_response_mask": [0, 0, 1],
    "concat_response_logprobs": [0.0, 0.0, -0.2],
}

# 第二次：旧历史 [10, 11, 20] 后增加上下文 [30]，模型生成 [40]。
step2_fields = {
    "prompt_token_ids": [10, 11, 20, 30],
    "response_token_ids": [40],
    "concat_token_ids": [30, 40],       # 不重复贡献旧前缀。
    "concat_response_mask": [0, 1],
    "concat_response_logprobs": [0.0, -0.3],
}
```

因此后续把两份 concat 材料接起来，可以得到：

```python
tokens = [10, 11, 20, 30, 40]
full_loss_mask = [0, 0, 1, 0, 1]
full_logprobs = [0.0, 0.0, -0.2, 0.0, -0.3]
```

这只是说明字段用途；具体分段、拼接和校验在后面的函数卡阅读，不在此当作已完成。最终 Sample 的字段映射属于 Step 008。

## 4. 读完回哪里

当前先补 [Session 类卡](../../../../../../step-011-harbor-trial-lifecycle/03-long-term-memory/classes/dressage/proxy/session_manager.py/Session.md)，接清这批 StepRecord 由谁持有、怎样按 lineage_id 对应路径，再回到分段函数。

先回到 finalize 的 `_split_session_into_lineage_segments(session)` 调用，接着看它如何从 session.steps 选择同一路径并划分段；然后才进入 `_build_tito_lineage_segment_record` 看拼接。当前只生成这张类卡，不提前生成两个未读函数卡。

## 5. 我的直接表述（原话）

此前明确的学习问题：

> 那么先缺的其实是
> 这里的step的格式到底是什么
> 以及最后是怎么做到合起来的这件事情

本轮确认：

> 好的 那么继续吧
> 看一下这里的这个steprecord

本轮字段理解与疑问：

> 简单来说就是这个turn是哪一个turn 也就是agent?
> 然后这个step是这个agent的第几部
> lineage id我不清楚
> lineage segment boundary before我大概知道就是有没有compact过
> 但是下面的step1 field 我其实没有特别理解
>
> 我的理解是这里的输入是这样的一个session?
> 我其实有点忘了这里的这个step record是哪里来的了

上述为用户当前假设与未知；前文分别校准 turn/step 的层级、边界含义和构造来源，不将校准视为已获个人确认。

## 6. 尚不清楚

- lineage 和边界怎样影响具体分段，留到下一个函数。
- 每段的 concat 数据怎样组装、校验并写成 record，留到构建函数。
- 分支、上下文改写和回退路径怎样准备 concat 材料，本轮不展开。

<details>
<summary>完整类定义、来源与验证</summary>

固定版本：Dressage 3e3142fe8ea07e4504c3b20a936a4c201a3de44c。

```python
@dataclass
class StepRecord:
    """One assistant generation step captured by the proxy."""

    turn_id: str
    request_messages: list[dict]
    normalized_request_messages: list[dict]
    prompt_token_ids: list[int]
    prompt_token_logprobs: list[float] | TQFieldRef
    snapshot_token_ids: list[int]
    response_token_ids: list[int]
    response_logprobs: list[float] | TQFieldRef
    all_token_ids: list[int]
    all_logprobs: list[float] | TQFieldRef
    input_token_texts: list[str]
    output_token_texts: list[str]
    messages_snapshot: list[dict]
    raw_response_text: str
    step_id: str = ""
    lineage_id: str = ""
    lineage_index: int = 0
    route_type: RouteType = "create"
    route_base_step_id: str | None = None
    normalized_messages_snapshot: list[dict] = field(default_factory=list)
    snapshot_rendered: str = ""
    snapshot_rendered_len: int = 0
    snapshot_tools_hash: str | None = None
    lineage_segment_boundary_before: bool = False
    lineage_segment_reasons_before: list[str] = field(default_factory=list)
    prompt_versions: list[str] = field(default_factory=list)
    response_versions: list[str] = field(default_factory=list)
    all_versions: list[str] = field(default_factory=list)
    all_logprobs_invalid: bool = False
    concat_token_ids: list[int] = field(default_factory=list)
    concat_response_logprobs: list[float] | TQFieldRef = field(default_factory=list)
    concat_response_mask: list[int] = field(default_factory=list)
    concat_versions: list[str] = field(default_factory=list)
    concat_context_token_count: int = 0
    concat_output_token_count: int = 0
    concat_logprobs_invalid: bool = False
    concat_incremental_tokenization_failed: bool = False
    response_routed_experts_chunks: list[dict[str, Any]] | TQFieldRef = field(
        default_factory=list
    )
    tools: list[dict[str, Any]] | None = None
    segment_boundary_before: bool = False
    rewrite_reason: str | None = None
    segment_reason_before: str | None = None
    segment_reasons_before: list[str] = field(default_factory=list)
    finish_reason: str = "stop"
    request_version: str | None = None
    response_version: str | None = None
    tool_call_hook_metadata: dict[str, Any] = field(default_factory=dict)
    request_e2e_latency_seconds: float | None = None
    request_queue_seconds: float | None = None
    rebalancing_moved: bool = False
    timestamp: float = field(default_factory=time.time)

```

- session_manager.py:416 的 record_step 创建记录；:561 追加到 session.steps。
- server.py:1666 的 _build_prompt_tokens 准备 input_ids 与 context_delta_ids；:1734 附近的 _build_concat_step_payload 准备三组 concat 数组。
- server.py:670 的 lineage 分段；:1509 的 TITO 轨迹构建器消费 concat 字段。
- 静态核对，无模型/网络运行；示例只用于字段对应，不能代替真实 tokenizer 或分支正确性验证。
- [本轮形成过程](../../../../../../../../01-native-agent-rollout/steps/step-007-proxy-finalization-and-trajectory/04-flow.md#steprecord-class)。

</details>
