# bind_trace：为 Sample 取得追踪句柄

[案例目录](../README.md) · [bind_trace 函数卡](../../functions/slime/observability/trace_utils.py/bind_trace.md) · [场景输入](input.json) · [会话绑定预期结果](expected.json) · [后续 span 实际输出](agent-model-turn-actual.json)

<a id="official-basic-usage"></a>

**先明确基础用法：`bind_trace` 可以独立调用，export/import 不是必需搭配。** [官网的定义](https://thudm.github.io/slime/developer_guide/trace.html#instrument-custom-code)是：在 sample 传给其他 helper 或任务之前，确保它已绑定追踪容器。按真实接口写出这个动作就是：

```python
# 基础绑定：可以独立使用，这一行就返回可用的 TraceHandle
handle = bind_trace(sample)
```

这一行准备或复用 sample.trace，并返回指向该容器的 TraceHandle。官网没有为 bind_trace 单独展开完整代码示例，也没有要求后面必须调用 export_trace/import_trace。

<a id="bind-trace-input-output"></a>

**这一行的实际输入与输出**

沿用本页的 T3/C0 教学数据，实际执行原始 `bind_trace(sample)`。下面是对象结构对照：左侧节选 Sample 的相关字段，右侧列全返回句柄的六个字段；`D` 表示两侧共享的同一个字典，在下方展开一次。

```text
调用：handle = bind_trace(sample)

输入：sample（Sample，相关字段）        返回：handle（TraceHandle，完整字段）
index       = 9                        trace_id       = "T3"
group_index = 3                        carrier        = D
prompt      = "计算 1 + 1。"            sample_id      = 9
trace       = D                        group_id       = 3
                                      attempt        = 0
                                      parent_span_id = None

D = {
  "version": 1, "trace_id": "T3",
  "sample_id": 9, "group_id": 3, "attempt": 0,
  "events": [
    {
      "type": "span_start", "name": "coding_rollout", "ts": 30.0,
      "trace_id": "T3", "sample_id": 9, "group_id": 3,
      "attempt": 0, "span_id": "C0"
    }
  ]
}
```

**调用后的变化：多了一个 TraceHandle，原来的记录仍在 D 中。** 实际检查 `handle.carrier is sample.trace` 为 `True`，原事件列表也被复用，仍只有 1 条事件。本例的追踪字段原本已齐全且与样本编号一致，所以字典内容没有变化；缺少追踪字段时，bind_trace 会负责准备。

注意右侧 `parent_span_id=None`：已有事件中的 C0 不会被 bind_trace 自动填入这里。后文会话组合中的 `parent_span_id="C0"` 是随后 export/import 的交接结果。

[本次完整输入与返回值](bind-trace-actual.json)保存了调用前的 Sample 字段、返回句柄、调用后的 Sample 字段及共享引用检查。该记录只执行了 bind_trace；加载的是固定版本 18868a79 的原 Sample 类与完整 trace_utils，隔离了无关模型依赖。

官方仓库还有直接传给 Session 的用法，位于[测试 test_sampler_replay.py:353–359](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/tests/test_agent/test_sampler_replay.py#L353-L359)：

```python
# 仓库测试中的直接用法：把句柄交给 Session，无需 export/import
Session(
    sampling_defaults={"max_new_tokens": budget},
    trace=bind_trace(sample),
)
```

这是仓库测试中的真实调用，不是官网文档里的示例，也没有经过 export/import。下面保留的具体数据案例则是 **Coding Agent 的一种组合使用**：在基础绑定之外，再通过 export/import 显式带上当前父阶段；调用在 [generate.py:272](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L272)。后续的 input.json、expected.json 对应这条组合路径，不能把它推广成 bind_trace 的固定调用顺序。

Coding Agent 准备运行时，Sample 已有自己的 Trace。接下来，Agent CLI 会通过 Adapter 发起模型请求；这些请求也应当记到这个样本的 Trace 中。

**因此，创建会话时要交给它两样东西：往哪里写记录，以及接在哪个父阶段下面。** 本例的记录在 `base_sample.trace`，当前父阶段是 `C0`。会话 `session-9` 接住这些信息，后续请求就能继续记录。

下面沿用同一组教学数据：样本 `index=9`，追踪编号 `T3`，外层 `coding_rollout` 的阶段编号 `C0`。真实调用来自 Slime，编号和样本值是为说明而固定的。

## 1. 先看接好之后有什么不同

```text
调用前                              调用后

base_sample.trace ──► D             base_sample.trace ────────────┐
                                    session-9.trace.carrier ──────┴──► D
session-9 尚未建立                  session-9.trace.parent_span_id = "C0"

D：同一份追踪字典，trace_id="T3"，events 中已有 C0 的开始事件
```

调用后，会话保存了一个 `TraceHandle`：它的 `carrier` 指向原来的字典 D，它的 `parent_span_id` 记住 `C0`。样本和会话由此能访问同一份记录。

**这次建立联系没有新增事件。** D 中仍是原来的那一条；后续执行 `trace_span` 时才会继续追加。

<a id="bind-trace-step"></a>

## 2. 使用代码：取出 Trace，交给会话

真实调用位于 [generate.py:270–279](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L270-L279)。原码将三个函数嵌套在 `trace=` 中；这里按相同求值顺序展开，增加中间变量和说明注释，省略模板配置。**下面是这个会话场景的组合用法，不是 bind_trace 的固定调用步骤。**

```python
# 基础绑定：到这里已经得到可用的追踪句柄
bound_handle = bind_trace(base_sample)

# 本会话场景的额外交接：通过 export/import 带上当前父阶段 C0
exported_context = export_trace(bound_handle)
session_trace = import_trace(exported_context, base_sample.trace)

# 会话保存句柄，供后面的请求使用
adapter.open_session(
    session_id,
    trace=session_trace,
    sampling_defaults=sampling_params,
    max_context_tokens=state.max_context_len,
)
```

**先看 `bind_trace(base_sample)`。** 它返回 `bound_handle`，其中 `carrier` 指向 `base_sample.trace`。本例的字典已经存在，所以直接复用；返回的句柄本身是新对象，此时 `parent_span_id=None`。

<a id="export-trace-step"></a>

**`export_trace` 把当前身份与父阶段取出来。** 它返回一个小字典，包含 `trace_id="T3"`、`parent_span_id="C0"` 等信息。这里的 C0 来自调用时的活动上下文；字典里没有 events。

<a id="import-trace-step"></a>

**`import_trace` 将这份身份信息和记录容器放回一个句柄。** 第二个实参明确传入原来的 `base_sample.trace`，所以新得到的 `session_trace` 仍指向 D，同时携带 `parent_span_id="C0"`。

<a id="open-session-step"></a>

最后，`open_session` 把这个句柄保存到 `adapter.store["session-9"].trace`。它返回 `None`；后续要取用的是会话中的字段。

这组调用完成了两件相互配合的事：**保留对同一份记录的访问，同时把“当前父阶段 C0”明确带过去。** 后面的 HTTP 请求由 Adapter 的事件循环处理，源码选择显式传递这份上下文，供请求处理代码从会话中取得。

<a id="bind-carrier-step"></a>

## 3. 后续请求怎样留下实际记录

Adapter 收到 session-9 的请求后，从 self.store 找到会话 s。下面是 [_run_turn:412–423](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L412-L423) 的实际源码块：

```python
with trace_span(s.trace, "agent_model_turn", record_error=False) if s.trace else nullcontext():
    target = bind_trace_carrier(s.trace.carrier) if s.trace else None
    with trace_span(target, "agent_tokenize", record_error=False) if target else nullcontext():
        translated, tools_schema = self._translate(body)
        prompt_ids = _session_prompt_ids(
            translated,
            tok,
            tools=tools_schema,
            session=s,
        )

    turn = await call_sglang_generate(prompt_ids, s, body, adapter=self, session_id=sid)
```

<a id="actual-agent-model-turn"></a>

### 这一次真实执行后，events 从 1 条变成 5 条

本次实际调用了原 trace_utils 实现和上面的完整源码块。起点沿用 input.json 中已经存在的 T3/C0；新增 span_id 和时间戳由原函数现场生成，没有替换成固定值。翻译请求、token 化和模型请求三个业务依赖使用替身，因此这是 **真实 Trace 执行 + 业务替身** 的结果。

绑定完成时，sample.trace["events"] 中只有原来的 C0 开始事件。执行这段代码后，原事件保留，又追加了以下四条。为便于配对，下面只展示关键字段，并把实际 UUID 缩写为前八位：

```text
span_start  agent_model_turn  span_id=bc1ac40e…  parent_span_id=C0
span_start  agent_tokenize    span_id=924a8eed…  parent_span_id=bc1ac40e…
span_end    agent_tokenize    span_id=924a8eed…
span_end    agent_model_turn  span_id=bc1ac40e…
```

**agent_model_turn 自己留下两条记录，内部的 agent_tokenize 又留下两条。** bind_trace_carrier 只是取得写入目标，这里的新事件由两次 trace_span 的进入和退出产生。

完整输出保存在 [agent-model-turn-actual.json](agent-model-turn-actual.json)：after_binding 是绑定后的 trace，after_agent_model_turn 是这段代码执行后的 trace，new_events 是本次新增的四条。查看 after_agent_model_turn.events 就能看到完整的五条事件、原始 UUID 和时间戳。

这次还让请求在空的 Trace 上下文中运行：agent_model_turn 仍从 Session.trace 找到父阶段 C0；agent_tokenize 再接到当前 agent_model_turn 下面。退出后，活动上下文恢复为空，已经写入 sample.trace 的事件保留下来。

<details>
<summary>复现这次执行，以及哪些部分用了替身</summary>

在本目录运行：

```bash
python3 run_agent_model_turn.py --source-repo /home/hongshi/projects/slime
```

[复现脚本](run_agent_model_turn.py)读取固定版本源码，执行原 Sample、Session、open_session、真实会话调用表达式和两层 with。为了避开当前环境缺少的模型依赖，原类和源码块通过 AST 隔离加载；没有重写 Trace 的记录逻辑，也没有执行完整 _run_turn 的前后处理。

三个替身分别是：self._translate 返回输入消息；_session_prompt_ids 返回 [51]；call_sglang_generate 返回 output_ids=[52]、finish_reason="stop"。没有启动 HTTP 服务、真实 tokenizer、模型或 Agent CLI；本次时间间隔不代表模型性能。

脚本核对新增事件顺序、父子编号、开始结束配对、共享字典以及退出后的上下文恢复。重新运行会产生新的 UUID 和时间戳，覆盖当前目录中的 agent-model-turn-actual.json；可用 --output 指定别的输出路径。

</details>

之前 expected.json 的 new_event_count=0 只针对会话绑定阶段；本次实际运行记录中的 new_event_count=4 针对后续两个 span。两份结果的停止位置不同。保存出口继续见 [Trace 的保存与查看](../../../references/trace-output-and-viewing.md)。

<a id="final-result"></a>

<details>
<summary>展开：具体字段、原始调用与核对边界</summary>

本例 `exported_context` 的完整值：

```json
{
  "version": 1,
  "trace_id": "T3",
  "sample_id": 9,
  "group_id": 3,
  "attempt": 0,
  "parent_span_id": "C0"
}
```

`bound_handle` 和 `session_trace` 的 trace_id/sample_id/group_id/attempt 相同，carrier 都指向 D；前者的 parent_span_id 为 None，后者为 C0。它们是两个句柄，不是两份事件数据。`expected.json` 中的 identity 字段是对共享引用的观察结果。

本例的其他会话配置是 temperature=0.7、max_context_tokens=4096。下面保留原始嵌套调用，省略模板配置：

```python
adapter.open_session(
    session_id,
    trace=import_trace(export_trace(bind_trace(base_sample)), base_sample.trace),
    sampling_defaults=sampling_params,
    max_context_tokens=state.max_context_len,
)
```

如果把 import_trace 的第二个实参换成新的字典，句柄就会指向那个接收容器；export/import 不复制旧 events，也不自动合并两个容器的后续事件。当前源码显式传入原字典，因此本例共享 D。

- 固定源码：18868a79。[bind_trace:238–254](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L238-L254)、[export/import:289–323](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L289-L323)、[open_session:275–292](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L292)。
- 外层 C0 的场景依据：[generate:225–230](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L225-L230)；显式携带上下文的依据：[_run_turn:410–414](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L410-L414)。
- [早先绑定阶段的核对记录](../verification.json)对应 new_event_count=0；本轮另有[后续 span 的实际执行结果](agent-model-turn-actual.json)，新增事件数为 4。两次都区分了原 Trace 实现与业务替身。
- [完整输入](input.json)和[预期结果](expected.json)是教学数据，不是采集日志；本轮保留这些数据。中间变量是为阅读而引入的名称，不是新增生产接口。
- [本例建立记录](../../../../step-014-agent-run-trace/04-flow.md#step014-concrete-examples)与[本轮使用说明重组](../../../../step-014-agent-run-trace/04-flow.md#step014-session-usage-narrative)。用户反馈仍难读，尚未将这份说明记为已理解。
- [此前逐字段表格版](../../../references/history/examples/bind-trace-adapter-session-before-usage-guide.md)只作历史回查。

</details>
