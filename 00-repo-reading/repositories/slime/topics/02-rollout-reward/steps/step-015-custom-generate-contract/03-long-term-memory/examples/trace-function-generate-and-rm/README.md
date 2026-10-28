# 案例 B · 已完成样本直接返回，也留下函数阶段记录

[案例目录](../README.md) · [对应函数卡](../../functions/slime/observability/trace_utils.py/trace_function.md) · [完整输入](input.json) · [完整预期结果](expected.json)

覆盖：trace_function。本例固定源码 18868a79，**调用来自真实业务，数据是教学构造**。T/S/G/C/F 等编号及秒数用于固定观察，真实运行由系统生成；它们不是实际采集的日志。

## 1. 这段业务在做什么

generate_and_rm_group 将样本交给 generate_and_rm。这个例子选用源码已有的“样本已完成，已有 response 和 reward，直接返回”路径，只观察装饰器给整个函数调用留下什么。

真实位置：[声明及真实提前返回分支：sglang_rollout.py:288–304](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L288-L304)；[组内提交及回填：425–430](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L425-L430)。下面保留真实名称与交接；省略的业务参数/代码不参与本例观察。

```python
@trace_function("generate_and_rm", target="sample")
async def generate_and_rm(args, sample, sampling_params, evaluation=False):
    # 省略前面的 partial_rollout 分支；本例该开关为 False
    if sample.status == Sample.Status.COMPLETED or sample.status == Sample.Status.TRUNCATED:
        assert sample.response is not None
        if not args.group_rm:
            assert sample.reward is not None
        return sample
    # 后续生成和评分分支本例不会进入
```

## 2. 放入这一组具体数据

以下节选 input.json，trace 在这里仅展示编号；已有事件完整保留在数据文件中。

```json
{
  "sample": {
    "index": 8,
    "group_index": 2,
    "prompt": "计算 1 + 1。",
    "trace": {
      "trace_id": "T2"
    },
    "status": "completed",
    "response": "2",
    "reward": 1.0
  },
  "args": {
    "partial_rollout": false,
    "group_rm": false
  },
  "sampling_params": {
    "temperature": 0.8,
    "max_new_tokens": 16
  },
  "evaluation": false,
  "active_context": {
    "trace_id": "T2",
    "span_id": "G0"
  },
  "fixed_observation": {
    "span_id": "F1",
    "start_ts": 20.0,
    "end_ts": 20.01
  }
}
```

完整 input.json 还包含进入前的 trace 和观察环境。sample/base_sample 是业务样本的字段节选；active_context、fixed_observation 与 assumed_* 是例子控制信息，不是 Sample 的新字段，也不是业务函数的新增参数。

## 3. 调用之后得到什么

<a id="trace-function-step"></a>

### trace_function 包住的调用：业务结果与 Trace 分别看

下面 result 是用于观察返回值的教学变量；被调用的仍是原来的装饰后函数：

```python
result = await generate_and_rm(args, sample, sampling_params, evaluation=False)
```

| 观察对象或字段 | 调用前 | 调用后 |
| --- | --- | --- |
| sample 的业务字段 | status="completed"、response="2"、reward=1.0 | 同样的值；本分支直接返回 |
| result | 尚未赋值 | 原 sample，result is sample 为 True |
| sample.trace["events"] | 已有 G0 开始事件 | 保留原事件，新增 F1 的 span_start 与 span_end |
| 当前阶段 | G0 | 函数执行期间进入 F1，返回后恢复 G0 |

下方 JSON 展示这次调用留下的具体事件；10 毫秒是本例的固定时钟结果。

下面是 expected.json 的结果摘录与观察摘要；新增事件仍保存在原 sample.trace["events"] 中。

```json
{
  "returned_sample": {
    "index": 8,
    "group_index": 2,
    "status": "completed",
    "response": "2",
    "reward": 1.0
  },
  "same_object": true,
  "new_events": [
    {
      "type": "span_start",
      "name": "generate_and_rm",
      "ts": 20.0,
      "trace_id": "T2",
      "sample_id": 8,
      "group_id": 2,
      "attempt": 0,
      "span_id": "F1",
      "parent_span_id": "G0"
    },
    {
      "type": "span_end",
      "name": "generate_and_rm",
      "ts": 20.01,
      "trace_id": "T2",
      "sample_id": 8,
      "group_id": 2,
      "attempt": 0,
      "span_id": "F1"
    }
  ]
}
```

返回值仍是原样本，response="2"、reward=1.0 都保留。额外多出 F1 的一对函数阶段事件；reward 没有自动进入事件 attrs。本分支没有再次生成或评分，也不会出现对应子阶段。组级调用方可像原来一样把返回样本写回 group[idx]。

完整 expected.json 保存结束快照；展示对象属性时使用 JSON 表示，Python 对象是否共享同一字典另用 identity 断言表达。JSON 里的相同内容不表示运行时复制了容器。

## 4. 验证边界与回到主线

核对时加载原 generate_and_rm 函数及原装饰器，输入使其走真实的 299–304 行提前返回分支；函数体没有改成演示用 score()。没有运行其他生成、评分或组级调度分支。10 毫秒来自固定时钟，仅用于展示配对，不是性能测量。

验证方式与结果统一见[核对记录](../verification.json)。保存位置继续见[Trace 收集过程](../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/trace-output-and-viewing.md)；这份案例的 expected.json 是教学快照，不是 Slime 自动保存的 rollout 文件。

<details>
<summary>来源与记录归属</summary>

- [真实调用证据](../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/references/real-usage-evidence.json)。
- [本轮建立 examples 的讨论](../../../../../../03-trace-diagnostics/steps/step-014-agent-run-trace/04-flow.md#step014-concrete-examples)。
- 本例是助手整理与核对的样本，尚无用户对这些具体数据的理解反馈。后续继承 02 时保留本目录、来源和验证边界。

</details>
