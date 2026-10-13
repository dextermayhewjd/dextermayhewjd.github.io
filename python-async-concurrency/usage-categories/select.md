# select

邻接机制：select I/O 就绪检查。

固定源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。本表共 **2** 条静态出现记录；不是运行次数。

同一个直接 API 表达式只记为 `api_call` 或 `api_reference` 中的一类。实例候选不计入直接原生 API 总数。

[总览](../README.md) · [完整文件索引](../FILES.md) · [JSON](../inventory.json) · [TSV](../inventory.tsv)

| ID | 位置 / 快照 | 所属符号 | 种类 | API / 语法 | 来源判定 | 源码行 |
| --- | --- | --- | --- | --- | --- | --- |
| occ-001971 | [tests/test_rollout_straw_transport.py:1411](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_rollout_straw_transport.py#L1411) · [快照](../source_snapshot/tests/test_rollout_straw_transport.py.txt) | test_checkpoint_lock_released_when_controller_process_is_killed | import | select | explicit_import |     import select |
| occ-001976 | [tests/test_rollout_straw_transport.py:1439](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_rollout_straw_transport.py#L1439) · [快照](../source_snapshot/tests/test_rollout_straw_transport.py.txt) | test_checkpoint_lock_released_when_controller_process_is_killed | api_call | select.select | lexical_import_resolution |         assert select.select([process.stdout], [], [], 60)[0], "Controller did not start" |
