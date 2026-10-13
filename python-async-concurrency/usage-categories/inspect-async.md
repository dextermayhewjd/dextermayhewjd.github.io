# inspect-async

inspect 异步对象检查。

固定源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。本表共 **4** 条静态出现记录；不是运行次数。

同一个直接 API 表达式只记为 `api_call` 或 `api_reference` 中的一类。实例候选不计入直接原生 API 总数。

[总览](../README.md) · [完整文件索引](../FILES.md) · [JSON](../inventory.json) · [TSV](../inventory.tsv)

| ID | 位置 / 快照 | 所属符号 | 种类 | API / 语法 | 来源判定 | 源码行 |
| --- | --- | --- | --- | --- | --- | --- |
| occ-000857 | [slime/observability/trace_utils.py:5](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/observability/trace_utils.py#L5) · [快照](../source_snapshot/slime/observability/trace_utils.py.txt) | &lt;module&gt; | import | inspect | explicit_import | import inspect |
| occ-000884 | [slime/observability/trace_utils.py:460](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/observability/trace_utils.py#L460) · [快照](../source_snapshot/slime/observability/trace_utils.py.txt) | trace_function.decorator | api_call | inspect.iscoroutinefunction | lexical_import_resolution |         if inspect.iscoroutinefunction(fn): |
| occ-001103 | [slime/rollout/sample_hooks.py:3](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sample_hooks.py#L3) · [快照](../source_snapshot/slime/rollout/sample_hooks.py.txt) | &lt;module&gt; | import | inspect | explicit_import | import inspect |
| occ-001109 | [slime/rollout/sample_hooks.py:41](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sample_hooks.py#L41) · [快照](../source_snapshot/slime/rollout/sample_hooks.py.txt) | _apply_to_sample | api_call | inspect.isawaitable | lexical_import_resolution |         if inspect.isawaitable(result): |
