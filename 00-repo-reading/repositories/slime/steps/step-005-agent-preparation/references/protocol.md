# protocol：选择题目整理与评测的约定

[返回参考目录](generate-input-context.md) · [查看整理结果 md](metadata.md)

**这里的 `protocol` 是字符串，表示本次任务采用哪套处理约定，如 `scaleswe` / `swebench`。** 它决定怎样解释题目数据，以及后续采用哪种评分分支。

## 从哪里取得

```python
protocol = CONFIG.eval_protocol if evaluation else CONFIG.train_protocol
md = swe.get_metadata(base_sample, protocol)
```

- `evaluation=True` 时使用评测路径的配置，否则使用训练路径的配置。
- `get_metadata` 按该约定选择题目信息的整理方式。
- 整理结果保留对应的 `md["protocol"]`。后续 `run_evaluation(md, ...)` 根据这个字段选择评分分支，所以它的作用会继续传递。

## 与 Adapter 的协议有什么区别

| 当前说的协议 | 解决什么问题 |
| --- | --- |
| `scaleswe` / `swebench` | 题目数据怎样解释、改动怎样评测 |
| Anthropic / OpenAI | 模型请求与响应怎样组织 |

> `protocol` 在这里选择的是题目整理和评测约定，与模型请求格式是不同层面的选择。

当前只需知道它的选择作用；两套任务实现的全部差异暂不展开。

<details>
<summary>源码与原始讨论</summary>

- 固定提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`；以上为静态源码说明。
- [选择 protocol](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L185-L186)；[按约定整理题目并保留字段](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L77-L137)；[根据字段选择评分](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/swe.py#L239-L247)。
- [原合并说明的讨论](../../step-005-agent-preparation/04-flow.md#shared-input-reference)；[本次拆分](../../step-005-agent-preparation/04-flow.md#split-input-references)。整理不表示新增掌握或运行证据。

</details>
