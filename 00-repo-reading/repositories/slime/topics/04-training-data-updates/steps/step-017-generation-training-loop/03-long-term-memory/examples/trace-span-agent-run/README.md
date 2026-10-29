# 案例 A · Agent 运行后，退出码怎样进入 Trace

[案例目录](../README.md) · [对应函数卡](../../functions/slime/observability/trace_utils.py/trace_span.md) · [完整输入](input.json) · [完整预期结果](expected.json)

覆盖：trace_span + span.set。本例固定源码 18868a79，**调用来自真实业务，数据是教学构造**。T/S/G/C/F 等编号及秒数用于固定观察，真实运行由系统生成；它们不是实际采集的日志。

## 1. 这段业务在做什么

Coding Agent 已有沙箱和会话，接下来运行 CLI。Trace 记录这次运行的起止时间，再把进程退出码附在结束记录上；业务随后继续收集运行统计。

真实位置：[examples/coding_agent_rl/generate.py:286–296](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L286-L296)。下面保留真实名称与交接；省略的业务参数/代码不参与本例观察。

```python
with trace_span(base_sample, "agent_run", record_error=False) as span:
    agent_exit_code = await harness.run(...)
    span.set("exit_code", agent_exit_code)
agent_metrics = await harness.collect_metrics(...)
```

## 2. 放入这一组具体数据

以下节选 input.json，trace 在这里仅展示编号；已有事件完整保留在数据文件中。

```json
{
  "base_sample": {
    "index": 7,
    "group_index": 2,
    "prompt": "修复仓库中失败的单元测试。",
    "trace": {
      "trace_id": "T1"
    }
  },
  "active_context": {
    "trace_id": "T1",
    "span_id": "S0"
  },
  "fixed_observation": {
    "span_id": "S1",
    "start_ts": 10.0,
    "end_ts": 12.0
  },
  "assumed_agent_exit_code": 0
}
```

完整 input.json 还包含进入前的 trace 和观察环境。sample/base_sample 是业务样本的字段节选；active_context、fixed_observation 与 assumed_* 是例子控制信息，不是 Sample 的新字段，也不是业务函数的新增参数。

## 3. 同一组数据怎样变化

下面沿用 input.json 的 T1/S0/S1、固定时间和退出码 0。只观察本例的 agent_run；业务替身没有另外写入子阶段事件。

<a id="use-enter"></a>

**① 进入**：执行 `with trace_span(base_sample, "agent_run", record_error=False) as span:`。

| 观察对象或字段 | 进入前 | 进入后 |
| --- | --- | --- |
| sample.trace["events"] | 1 条 S0 开始事件 | 保留原事件，新增 S1 的 span_start，父编号为 S0 |
| 当前阶段 | S0 | S1 |
| 业务取得的 span | 尚未取得 | end_attrs={}、closed=False |

<a id="use-run"></a>

**② 业务**：执行 `agent_exit_code = await harness.run(...)`。

| 观察对象或字段 | 调用前 | 调用后 |
| --- | --- | --- |
| agent_exit_code | 尚未赋值 | 0，由本例的业务替身返回 |
| span.end_attrs | {} | {}；退出码尚未写入 |
| S1 的结束事件 | 尚未出现 | 尚未出现 |

<a id="use-attrs"></a>

**③ 属性**：执行 `span.set("exit_code", agent_exit_code)`。

| 观察对象或字段 | 调用前 | 调用后 |
| --- | --- | --- |
| span.end_attrs | {} | {"exit_code": 0} |
| sample.trace["events"] | S0、S1 的开始事件 | 仍是这两条；本次 set 没有追加事件 |

<a id="use-exit"></a>

**④ 退出**：离开 with，再继续 `agent_metrics = await harness.collect_metrics(...)`。

| 观察对象或字段 | 离开 with 前 | 离开 with 后 |
| --- | --- | --- |
| S1 的结束事件 | 尚未出现 | 新增 span_end，attrs={"exit_code": 0} |
| span.closed | False | True |
| 当前阶段 | S1 | 恢复为 S0 |

异常路径的区别见 [trace_span 卡](../../functions/slime/observability/trace_utils.py/trace_span.md#exception-boundary)。

### 最终新增的两条记录

下面是 expected.json 的结果摘录与观察摘要；新增事件仍保存在原 sample.trace["events"] 中。

```json
{
  "new_events": [
    {
      "type": "span_start",
      "name": "agent_run",
      "ts": 10.0,
      "trace_id": "T1",
      "sample_id": 7,
      "group_id": 2,
      "attempt": 0,
      "span_id": "S1",
      "parent_span_id": "S0"
    },
    {
      "type": "span_end",
      "name": "agent_run",
      "ts": 12.0,
      "trace_id": "T1",
      "sample_id": 7,
      "group_id": 2,
      "attempt": 0,
      "span_id": "S1",
      "attrs": {
        "exit_code": 0
      }
    }
  ],
  "span_end_attrs": {
    "exit_code": 0
  }
}
```

本次 S1 持续 2 秒，结束事件的 exit_code 为 0。原 S0 开始记录保留，退出时活动上下文恢复到 S0；本例停在 agent_run 退出后，外层 coding_rollout 尚未结束。业务结果仍是退出码 0，Trace 本身不会生成修复代码。

完整 expected.json 保存结束快照；展示对象属性时使用 JSON 表示，Python 对象是否共享同一字典另用 identity 断言表达。JSON 里的相同内容不表示运行时复制了容器。

## 4. 验证边界与回到主线

核对时执行原 trace_span/set 和原业务 with 语句，harness.run 由预设返回 0 的替身提供；没有启动 CLI、沙箱或 collect_metrics。外层已开始、内层正常完成是本例的固定路径。

验证方式与结果统一见[核对记录](../verification.json)。保存位置继续见[Trace 收集过程](../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/trace-output-and-viewing.md)；这份案例的 expected.json 是教学快照，不是 Slime 自动保存的 rollout 文件。

<details>
<summary>来源与记录归属</summary>

- [真实调用证据](../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/real-usage-evidence.json)。
- [本轮建立 examples 的讨论](../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-concrete-examples)。
- 本例是助手整理与核对的样本，尚无用户对这些具体数据的理解反馈。后续继承 02 时保留本目录、来源和验证边界。

</details>
