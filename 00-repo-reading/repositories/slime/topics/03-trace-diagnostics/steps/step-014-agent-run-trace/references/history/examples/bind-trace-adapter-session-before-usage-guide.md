> 历史版本：2026-10-27 用户反馈表格过碎、难以理解使用方式。本稿保留作回查，现行说明见[案例 C](../../../02-short-term-memory/examples/bind-trace/README.md)。

# 案例 C · bind_trace：取得样本的追踪句柄，再交给 Adapter

[案例目录](../../../02-short-term-memory/examples/README.md) · [对应函数卡](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md) · [完整输入](../../../02-short-term-memory/examples/bind-trace/input.json) · [完整预期结果](../../../02-short-term-memory/examples/bind-trace/expected.json)

覆盖：bind_trace + export_trace/import_trace；后续 bind_trace_carrier。本例固定源码 18868a79，**调用来自真实业务，数据是教学构造**。T/S/G/C/F 等编号及秒数用于固定观察，真实运行由系统生成；它们不是实际采集的日志。

**只想看清 bind_trace，直接看[① 调用前后对照](#bind-trace-step)。** 下表的编号对应本页小节；①–④是准备同一会话的顺序，⑤发生在后续模型请求中。

| 要看哪个调用 | 本页的具体位置 | 读完接到哪里 |
| --- | --- | --- |
| bind_trace(base_sample) | [① Sample → TraceHandle](#bind-trace-step) | 句柄交给 export_trace |
| export_trace(bound_handle) | [② 句柄 → 身份字典](#export-trace-step) | 字典交给 import_trace |
| import_trace(exported_context, base_sample.trace) | [③ 身份字典 → 会话句柄](#import-trace-step) | 句柄交给 open_session |
| adapter.open_session(...) | [④ 句柄存进 session-9](#open-session-step) | 后续请求从会话中取用 |
| bind_trace_carrier(s.trace.carrier) | [⑤ 后续请求：从容器再取句柄](#bind-carrier-step) | 作为 agent_tokenize 的追踪目标 |

## 1. 这段业务在做什么

Agent 运行前建立会话，把本任务已有的追踪目标交给 Adapter。之后 CLI 请求模型时，Adapter 可以通过会话找到同一份记录容器。

真实位置：[generate.py:269–279](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L269-L279)；[open_session:275–292](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L275-L292)；[Adapter 使用：412–414](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L412-L414)。下面保留真实名称与交接；省略的业务参数/代码不参与本例观察。

```python
adapter.open_session(
    session_id,
    trace=import_trace(export_trace(bind_trace(base_sample)), base_sample.trace),
    sampling_defaults=sampling_params,
    max_context_tokens=state.max_context_len,
    # 省略模板配置
)
```

## 2. 放入这一组具体数据

以下节选 input.json，trace 在这里仅展示编号；已有事件完整保留在数据文件中。

```json
{
  "base_sample": {
    "index": 9,
    "group_index": 3,
    "prompt": "计算 1 + 1。",
    "trace": {
      "trace_id": "T3"
    }
  },
  "active_context": {
    "trace_id": "T3",
    "span_id": "C0"
  },
  "session_id": "session-9",
  "sampling_defaults": {
    "temperature": 0.7
  },
  "max_context_tokens": 4096
}
```

完整 input.json 还包含进入前的 trace 和观察环境。sample/base_sample 是业务样本的字段节选；active_context、fixed_observation 与 assumed_* 是例子控制信息，不是 Sample 的新字段，也不是业务函数的新增参数。

## 3. 每次调用前后，并排看同一份数据

原调用把①–③嵌套在一个实参中。下面按相同的求值顺序展开与 Trace 相关的部分，其余会话配置省略；bound_handle、exported_context、session_trace 是为观察中间结果增加的教学变量名。

```python
bound_handle = bind_trace(base_sample)                              # ①
exported_context = export_trace(bound_handle)                       # ②
session_trace = import_trace(exported_context, base_sample.trace)   # ③
adapter.open_session(session_id, trace=session_trace)               # ④ 其余会话配置见原调用
```

<a id="bind-trace-step"></a>

### ① bind_trace：已有 Sample → 新的 TraceHandle

**真实位置**：调用在 [generate.py:272](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L272) 的最内层；实现是 [trace_utils.py:238–254](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L238-L254)。

```python
bound_handle = bind_trace(base_sample)
```

| 观察对象或字段 | 调用前 | 调用后 |
| --- | --- | --- |
| base_sample.trace | 已有 T3，含 1 条 C0 开始事件 | 复用同一字典，仍含原来的 1 条事件 |
| bound_handle | 尚未赋值 | 返回一个新的 TraceHandle |
| bound_handle 的身份字段 | — | trace_id="T3"、sample_id=9、group_id=3、attempt=0 |
| bound_handle.carrier | — | 指向 base_sample.trace；没有复制一份事件列表 |
| bound_handle.parent_span_id | — | None；本函数未设置父阶段编号 |

**这一行得到的是句柄。** 它让后续代码访问该样本的追踪字典。当前输入已经有 trace，因此这里复用；从空 Sample 准备 trace 的另一种输入见[函数卡](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md#usage)。下一行把 bound_handle 传给 export_trace。

<a id="export-trace-step"></a>

### ② export_trace：句柄 → 可交接的身份字典

实现：[trace_utils.py:289–308](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L289-L308)。

```python
exported_context = export_trace(bound_handle)
```

| 观察对象或字段 | 调用前 | 调用后 |
| --- | --- | --- |
| exported_context | 尚未赋值 | 新字典，包含 version、trace_id、sample_id、group_id、attempt、parent_span_id 六项 |
| 父阶段编号 | bound_handle.parent_span_id=None；当前活动阶段为 C0 | exported_context["parent_span_id"]="C0"；bound_handle 本身仍为 None |
| 事件 | 原容器中有 1 条 | 原容器仍有 1 条；exported_context 不包含 events |

**C0 是在这一步从当前追踪上下文取出的。** 它不是 bind_trace 给句柄补上的字段。完整六字段结果见下方[最终快照](#final-result)，下一步把这份字典连同原容器交给 import_trace。

<a id="import-trace-step"></a>

### ③ import_trace：身份字典 + 原容器 → 会话句柄

实现：[trace_utils.py:311–323](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py#L311-L323)。

```python
session_trace = import_trace(exported_context, base_sample.trace)
```

| 观察对象或字段 | 调用前 | 调用后 |
| --- | --- | --- |
| session_trace | 尚未赋值 | 另一个新的 TraceHandle，trace_id="T3" |
| session_trace.parent_span_id | — | "C0"，来自 exported_context |
| session_trace.carrier | 传入的接收容器为 base_sample.trace | 仍指向该字典，与 bound_handle.carrier 共享容器 |
| 原事件列表 | 1 条 C0 开始事件 | 仍是这 1 条；没有复制或新增事件 |

**两个句柄可以共享同一个容器。** import_trace 在这里创建会话句柄，不会把 bound_handle 本身改成 session_trace。

<a id="open-session-step"></a>

### ④ open_session：把句柄留在会话里

调用在 [generate.py:270–279](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L270-L279)，保存位置在 [BaseAdapter.open_session:287–292](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L287-L292)。下面只保留本次追踪交接的两个实参：

```python
adapter.open_session(session_id, trace=session_trace)
```

| 观察对象或字段 | 调用前 | 调用后 |
| --- | --- | --- |
| adapter.store["session-9"] | 尚未建立 | 已建立 Session |
| 该 Session 的 trace | — | 保存刚才的 session_trace 句柄 |
| 该句柄的 carrier | base_sample.trace | 仍指向 base_sample.trace |
| open_session 返回值 | — | None；结果保存在 adapter.store 中 |

<a id="bind-carrier-step"></a>

### ⑤ 后续模型请求：bind_trace_carrier 从会话容器取得目标

这是[另一处真实调用：_run_turn:413](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L413)。请求找到 session-9 后，s 表示这个会话：

```python
target = bind_trace_carrier(s.trace.carrier) if s.trace else None
```

| 观察对象或字段 | 这一行调用前 | 这一行调用后 |
| --- | --- | --- |
| s.trace.carrier | 指向原 base_sample.trace | 仍指向原容器 |
| target | 尚未赋值 | 新 TraceHandle，target.carrier 指向同一容器 |
| 容器中的事件 | 进入这一行时已有的事件 | 此函数不追加事件；随后 agent_tokenize 的 trace_span 才使用 target 记录阶段 |

实际请求外围还有 agent_model_turn 的 trace_span，不能把这里的“本函数不追加”误读为整次请求事件数不变。当前案例仅隔离核对绑定语句的共享引用，未执行模型请求。

<a id="final-result"></a>

## 4. 对照最终快照

下面是 expected.json 的结果摘录与观察摘要；本次交接不新增事件，已有记录仍保存在原 base_sample.trace["events"] 中。

```json
{
  "exported_context": {
    "version": 1,
    "trace_id": "T3",
    "sample_id": 9,
    "group_id": 3,
    "attempt": 0,
    "parent_span_id": "C0"
  },
  "session": {
    "session_id": "session-9",
    "sampling_defaults": {
      "temperature": 0.7
    },
    "max_context_tokens": 4096,
    "trace_handle": {
      "trace_id": "T3",
      "sample_id": 9,
      "group_id": 3,
      "attempt": 0,
      "parent_span_id": "C0"
    }
  },
  "new_event_count": 0,
  "identity": {
    "bound_carrier_is_sample_trace": true,
    "session_carrier_is_sample_trace": true,
    "adapter_target_carrier_is_sample_trace": true
  }
}
```

bind_trace 返回一个指向 base_sample.trace 的句柄；export_trace 带出当前父阶段 C0，但不包含 events；import_trace 接回同一个 carrier。会话保存该句柄后，三处访问仍指向同一份字典。此次接线没有新增事件，原 C0 开始记录保留。若 import_trace 改用新的接收字典，该字典的 events 起初为空，后续记录不会自动回到原样本；这个边界见 [bind_trace 卡的配套组合](../../../02-short-term-memory/functions/slime/observability/trace_utils.py/bind_trace.md#tool-import)，不属于本例已执行的共享容器路径。

完整 expected.json 保存结束快照；展示对象属性时使用 JSON 表示，Python 对象是否共享同一字典另用 identity 断言表达。JSON 里的相同内容不表示运行时复制了容器。

## 5. 验证边界与回到主线

核对时执行原绑定/导入导出函数、原 Session 类与 BaseAdapter.open_session，并核对后续 bind_trace_carrier 的共享引用。仅构造所需 store，不启动 Adapter HTTP 服务或模型请求；这些工具属于本地会话交接，不能据此推断跨进程共享字典。

验证方式与结果统一见[核对记录](../../../02-short-term-memory/examples/verification.json)。保存位置继续见[Trace 收集过程](../../trace-output-and-viewing.md)；这份案例的 expected.json 是教学快照，不是 Slime 自动保存的 rollout 文件。

<details>
<summary>来源与记录归属</summary>

- [真实调用证据](../../real-usage-evidence.json)。
- [本轮建立 examples 的讨论](../../../04-flow.md#step014-concrete-examples)。
- 本例是助手整理与核对的样本，尚无用户对这些具体数据的理解反馈。后续继承 02 时保留本目录、来源和验证边界。

</details>
