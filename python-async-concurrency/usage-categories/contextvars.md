# contextvars

contextvars 上下文变量与上下文传播。

固定源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。本表共 **7** 条静态出现记录；不是运行次数。

同一个直接 API 表达式只记为 `api_call` 或 `api_reference` 中的一类。实例候选不计入直接原生 API 总数。

[总览](../README.md) · [完整文件索引](../FILES.md) · [JSON](../inventory.json) · [TSV](../inventory.tsv)

| ID | 位置 / 快照 | 所属符号 | 种类 | API / 语法 | 来源判定 | 源码行 |
| --- | --- | --- | --- | --- | --- | --- |
| occ-000856 | [slime/observability/trace_utils.py:3](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/observability/trace_utils.py#L3) · [快照](../source_snapshot/slime/observability/trace_utils.py.txt) | &lt;module&gt; | import | contextvars | explicit_import | import contextvars |
| occ-000858 | [slime/observability/trace_utils.py:47](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/observability/trace_utils.py#L47) · [快照](../source_snapshot/slime/observability/trace_utils.py.txt) | &lt;module&gt; | api_reference | contextvars.ContextVar | lexical_import_resolution | _TRACE_STACK: contextvars.ContextVar[tuple[tuple[str, str], ...]] = contextvars.ContextVar( |
| occ-000859 | [slime/observability/trace_utils.py:47](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/observability/trace_utils.py#L47) · [快照](../source_snapshot/slime/observability/trace_utils.py.txt) | &lt;module&gt; | api_call | contextvars.ContextVar | lexical_import_resolution | _TRACE_STACK: contextvars.ContextVar[tuple[tuple[str, str], ...]] = contextvars.ContextVar( |
| occ-000860 | [slime/observability/trace_utils.py:51](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/observability/trace_utils.py#L51) · [快照](../source_snapshot/slime/observability/trace_utils.py.txt) | &lt;module&gt; | api_reference | contextvars.ContextVar | lexical_import_resolution | _TRACE_HANDLE_STACK: contextvars.ContextVar[tuple[tuple[TraceHandle, ...], ...]] = contextvars.ContextVar( |
| occ-000861 | [slime/observability/trace_utils.py:51](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/observability/trace_utils.py#L51) · [快照](../source_snapshot/slime/observability/trace_utils.py.txt) | &lt;module&gt; | api_call | contextvars.ContextVar | lexical_import_resolution | _TRACE_HANDLE_STACK: contextvars.ContextVar[tuple[tuple[TraceHandle, ...], ...]] = contextvars.ContextVar( |
| occ-001104 | [slime/rollout/sample_hooks.py:5](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sample_hooks.py#L5) · [快照](../source_snapshot/slime/rollout/sample_hooks.py.txt) | &lt;module&gt; | import | contextvars.ContextVar | explicit_import | from contextvars import ContextVar |
| occ-001105 | [slime/rollout/sample_hooks.py:12](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sample_hooks.py#L12) · [快照](../source_snapshot/slime/rollout/sample_hooks.py.txt) | &lt;module&gt; | api_call | contextvars.ContextVar | lexical_import_resolution | _task_rollout_id = ContextVar("rollout_sample_hook_id", default=None) |
