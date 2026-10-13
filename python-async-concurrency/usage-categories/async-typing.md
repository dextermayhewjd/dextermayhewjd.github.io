# async-typing

typing / collections.abc 异步类型标记。

固定源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。本表共 **7** 条静态出现记录；不是运行次数。

同一个直接 API 表达式只记为 `api_call` 或 `api_reference` 中的一类。实例候选不计入直接原生 API 总数。

[总览](../README.md) · [完整文件索引](../FILES.md) · [JSON](../inventory.json) · [TSV](../inventory.tsv)

| ID | 位置 / 快照 | 所属符号 | 种类 | API / 语法 | 来源判定 | 源码行 |
| --- | --- | --- | --- | --- | --- | --- |
| occ-000002 | [examples/coding_agent_rl/generate.py:27](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L27) · [快照](../source_snapshot/examples/coding_agent_rl/generate.py.txt) | &lt;module&gt; | import | collections.abc.AsyncIterator | explicit_import | from collections.abc import AsyncIterator |
| occ-000007 | [examples/coding_agent_rl/generate.py:96](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L96) · [快照](../source_snapshot/examples/coding_agent_rl/generate.py.txt) | &lt;module&gt; | api_reference | collections.abc.AsyncIterator | lexical_import_resolution | async def boot_agent_sandbox(image: str, instance_id: str) -&gt; AsyncIterator[E2BSandbox]: |
| occ-001116 | [slime/rollout/sglang_rollout.py:8](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L8) · [快照](../source_snapshot/slime/rollout/sglang_rollout.py.txt) | &lt;module&gt; | import | collections.abc.Awaitable | explicit_import | from collections.abc import Awaitable, Callable |
| occ-001124 | [slime/rollout/sglang_rollout.py:261](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L261) · [快照](../source_snapshot/slime/rollout/sglang_rollout.py.txt) | &lt;module&gt; | api_reference | collections.abc.Awaitable | lexical_import_resolution |     generate_call: Awaitable[Sample &#124; list[Sample]], |
| occ-001129 | [slime/rollout/sglang_rollout.py:279](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L279) · [快照](../source_snapshot/slime/rollout/sglang_rollout.py.txt) | &lt;module&gt; | api_reference | collections.abc.Awaitable | lexical_import_resolution |     generate_call: Awaitable[Sample &#124; list[Sample]], |
| occ-001448 | [tests/test_agent/_fakes.py:29](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/_fakes.py#L29) · [快照](../source_snapshot/tests/test_agent/_fakes.py.txt) | &lt;module&gt; | import | collections.abc.Awaitable | explicit_import | from collections.abc import Awaitable, Callable |
| occ-001470 | [tests/test_agent/_fakes.py:240](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_agent/_fakes.py#L240) · [快照](../source_snapshot/tests/test_agent/_fakes.py.txt) | FakeSandbox | api_reference | collections.abc.Awaitable | lexical_import_resolution |         on_launch: Callable[[dict], Awaitable[int]] &#124; None = None, |
