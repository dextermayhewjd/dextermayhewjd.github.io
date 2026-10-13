# contextlib-async

contextlib 异步上下文管理辅助接口。

固定源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。本表共 **6** 条静态出现记录；不是运行次数。

同一个直接 API 表达式只记为 `api_call` 或 `api_reference` 中的一类。实例候选不计入直接原生 API 总数。

[总览](../README.md) · [完整文件索引](../FILES.md) · [JSON](../inventory.json) · [TSV](../inventory.tsv)

| ID | 位置 / 快照 | 所属符号 | 种类 | API / 语法 | 来源判定 | 源码行 |
| --- | --- | --- | --- | --- | --- | --- |
| occ-000003 | [examples/coding_agent_rl/generate.py:28](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L28) · [快照](../source_snapshot/examples/coding_agent_rl/generate.py.txt) | &lt;module&gt; | import | contextlib.asynccontextmanager | explicit_import | from contextlib import asynccontextmanager |
| occ-000005 | [examples/coding_agent_rl/generate.py:95](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L95) · [快照](../source_snapshot/examples/coding_agent_rl/generate.py.txt) | &lt;module&gt; | api_reference | contextlib.asynccontextmanager | lexical_import_resolution | @asynccontextmanager |
| occ-001541 | [tests/test_agent/test_agent_rollout_cpu.py:27](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/test_agent_rollout_cpu.py#L27) · [快照](../source_snapshot/tests/test_agent/test_agent_rollout_cpu.py.txt) | &lt;module&gt; | import | contextlib | explicit_import | import contextlib |
| occ-001543 | [tests/test_agent/test_agent_rollout_cpu.py:58](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/test_agent_rollout_cpu.py#L58) · [快照](../source_snapshot/tests/test_agent/test_agent_rollout_cpu.py.txt) | &lt;module&gt; | api_reference | contextlib.asynccontextmanager | lexical_import_resolution |     @contextlib.asynccontextmanager |
| occ-002118 | [tests/test_streaming_rollout.py:6](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_streaming_rollout.py#L6) · [快照](../source_snapshot/tests/test_streaming_rollout.py.txt) | &lt;module&gt; | import | contextlib.asynccontextmanager | explicit_import | from contextlib import asynccontextmanager, nullcontext |
| occ-002124 | [tests/test_streaming_rollout.py:176](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_streaming_rollout.py#L176) · [快照](../source_snapshot/tests/test_streaming_rollout.py.txt) | _http_stream | api_reference | contextlib.asynccontextmanager | lexical_import_resolution |     @asynccontextmanager |
