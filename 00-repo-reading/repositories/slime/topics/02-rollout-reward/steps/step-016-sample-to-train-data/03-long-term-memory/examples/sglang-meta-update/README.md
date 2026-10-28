# 案例 D · 将具体模型响应补进生成阶段

[案例目录](../README.md) · [对应函数卡](../../functions/slime/observability/trace_utils.py/build_sglang_meta_trace_attrs.md) · [完整输入](input.json) · [完整预期结果](expected.json)

覆盖：build_sglang_meta_trace_attrs + span.update + trace_span。本例固定源码 18868a79，**调用来自真实业务，数据是教学构造**。T/S/G/C/F 等编号及秒数用于固定观察，真实运行由系统生成；它们不是实际采集的日志。

## 1. 这段业务在做什么

SGLang 请求返回文本和 meta_info 后，先把适合追踪的元信息整理出来，再附到本次生成阶段。模型文本后续仍由原业务代码写回训练样本。

真实位置：[slime/rollout/sglang_rollout.py:219–230](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L219-L230)；[后续样本更新：240–255](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L240-L255)。下面保留真实名称与交接；省略的业务参数/代码不参与本例观察。

```python
with trace_span(sample, "sglang_generate", attrs={"max_new_tokens": sampling_params["max_new_tokens"]}) as span:
    output = await post(...)
    span.update(build_sglang_meta_trace_attrs(output["meta_info"]))
```

## 2. 放入这一组具体数据

以下节选 input.json，trace 在这里仅展示编号；已有事件完整保留在数据文件中。

```json
{
  "sample": {
    "index": 10,
    "group_index": 3,
    "prompt": "计算 1 + 1。",
    "trace": {
      "trace_id": "T4"
    }
  },
  "sampling_params": {
    "max_new_tokens": 16
  },
  "assumed_server_response": {
    "text": "2",
    "meta_info": {
      "prompt_tokens": 12,
      "completion_tokens": 1,
      "cached_tokens": 0,
      "e2e_latency": 0.2,
      "finish_reason": {
        "type": "stop"
      },
      "id": "req-10",
      "unused": 99
    }
  },
  "active_context": {
    "trace_id": "T4",
    "span_id": "F0"
  },
  "fixed_observation": {
    "span_id": "S4",
    "start_ts": 40.0,
    "end_ts": 40.2
  }
}
```

完整 input.json 还包含进入前的 trace 和观察环境。sample/base_sample 是业务样本的字段节选；active_context、fixed_observation 与 assumed_* 是例子控制信息，不是 Sample 的新字段，也不是业务函数的新增参数。

## 3. 调用之后得到什么

原调用把整理与更新写在同一行。为对照两个函数的效果，下面用教学变量 metadata_attrs 接住中间返回值。

<a id="meta-transform-step"></a>

### ① build_sglang_meta_trace_attrs：原始元信息 → 追踪属性

```python
metadata_attrs = build_sglang_meta_trace_attrs(output["meta_info"])
```

| 对应字段 | 调用前：output["meta_info"] | 调用后：metadata_attrs |
| --- | --- | --- |
| token 数与耗时 | prompt_tokens=12、completion_tokens=1、cached_tokens=0、e2e_latency=0.2 | 保留这些字段和值 |
| finish_reason | {"type": "stop"} | "stop" |
| 请求编号 | id="req-10" | sglang_request_id="req-10" |
| unused | 99 | 不包含该字段 |

本函数返回新的属性字典，原 output 仍保持原值。它还没有把这些值写进 span。

<a id="update-step"></a>

### ② span.update：把返回的属性交给本阶段

```python
span.update(metadata_attrs)
```

| 观察对象或字段 | update 前 | update 后 |
| --- | --- | --- |
| span.end_attrs | {} | 上一步的六项属性 |
| span.closed | False | False；业务仍在 with 内 |
| S4 的结束事件 | 尚未出现 | 尚未出现；此刻只更新阶段对象 |

<a id="span-exit-step"></a>

### ③ 离开 with：把属性写进结束事件

| 观察对象或字段 | 离开 with 前 | 离开 with 后 |
| --- | --- | --- |
| S4 的结束事件 | 尚未出现 | 新增 span_end，attrs 带上这六项属性 |
| span.closed | False | True |
| S4 的开始事件 attrs | {"max_new_tokens": 16} | 保留原值；不会自动并入结束属性 |

下面是 expected.json 的结果摘录与观察摘要；新增事件仍保存在原 sample.trace["events"] 中。

```json
{
  "metadata_attrs": {
    "prompt_tokens": 12,
    "completion_tokens": 1,
    "cached_tokens": 0,
    "e2e_latency": 0.2,
    "finish_reason": "stop",
    "sglang_request_id": "req-10"
  },
  "span_start_attrs": {
    "max_new_tokens": 16
  },
  "span_end_attrs": {
    "prompt_tokens": 12,
    "completion_tokens": 1,
    "cached_tokens": 0,
    "e2e_latency": 0.2,
    "finish_reason": "stop",
    "sglang_request_id": "req-10"
  }
}
```

finish_reason 从 {"type":"stop"} 变成 "stop"；id 改用 sglang_request_id 记录；unused 不保留。update 后这些普通属性先在 span.end_attrs，离开 with 后进入 S4 的结束事件。max_new_tokens 属于开始事件属性，不会自动合并到结束属性中。原 output 仍保持原值。

完整 expected.json 保存结束快照；展示对象属性时使用 JSON 表示，Python 对象是否共享同一字典另用 identity 断言表达。JSON 里的相同内容不表示运行时复制了容器。

## 4. 验证边界与回到主线

核对原业务 with、原元信息工具与 update。post 替身返回 input.json 的具体响应，不访问模型服务；固定时钟给出 40.0/40.2。没有执行随后 append_response_tokens；样本的 response 字段不在本例终点更新。本例没有 PD 子阶段数据。

验证方式与结果统一见[核对记录](../verification.json)。保存位置继续见[Trace 收集过程](../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/trace-output-and-viewing.md)；这份案例的 expected.json 是教学快照，不是 Slime 自动保存的 rollout 文件。

<details>
<summary>来源与记录归属</summary>

- [真实调用证据](../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/real-usage-evidence.json)。
- [本轮建立 examples 的讨论](../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-concrete-examples)。
- 本例是助手整理与核对的样本，尚无用户对这些具体数据的理解反馈。后续继承 02 时保留本目录、来源和验证边界。

</details>
