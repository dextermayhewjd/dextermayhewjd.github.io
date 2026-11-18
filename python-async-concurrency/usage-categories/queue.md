# queue

queue 标准库队列。

固定源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。本表共 **7** 条静态出现记录；不是运行次数。

同一个直接 API 表达式只记为 `api_call` 或 `api_reference` 中的一类。实例候选不计入直接原生 API 总数。

[总览](../README.md) · [完整文件索引](../FILES.md) · [JSON](../inventory.json) · [TSV](../inventory.tsv)

| ID | 位置 / 快照 | 所属符号 | 种类 | API / 语法 | 来源判定 | 源码行 |
| --- | --- | --- | --- | --- | --- | --- |
| occ-000642 | [slime/backends/megatron_utils/update_weight/update_weight_from_disk_delta.py:6](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/backends/megatron_utils/update_weight/update_weight_from_disk_delta.py#L6) · [快照](../source_snapshot/slime/backends/megatron_utils/update_weight/update_weight_from_disk_delta.py.txt) | &lt;module&gt; | import | queue | explicit_import | import queue |
| occ-000646 | [slime/backends/megatron_utils/update_weight/update_weight_from_disk_delta.py:234](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/backends/megatron_utils/update_weight/update_weight_from_disk_delta.py#L234) · [快照](../source_snapshot/slime/backends/megatron_utils/update_weight/update_weight_from_disk_delta.py.txt) | UpdateWeightFromDiskDelta._encode_delta | api_reference | queue.Queue | lexical_import_resolution |         free_q: queue.Queue = queue.Queue() |
| occ-000647 | [slime/backends/megatron_utils/update_weight/update_weight_from_disk_delta.py:234](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/backends/megatron_utils/update_weight/update_weight_from_disk_delta.py#L234) · [快照](../source_snapshot/slime/backends/megatron_utils/update_weight/update_weight_from_disk_delta.py.txt) | UpdateWeightFromDiskDelta._encode_delta | api_call | queue.Queue | lexical_import_resolution |         free_q: queue.Queue = queue.Queue() |
| occ-001023 | [slime/rollout/fully_async_rollout.py:33](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_rollout.py#L33) · [快照](../source_snapshot/slime/rollout/fully_async_rollout.py.txt) | &lt;module&gt; | import | queue | explicit_import | import queue |
| occ-001028 | [slime/rollout/fully_async_rollout.py:97](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_rollout.py#L97) · [快照](../source_snapshot/slime/rollout/fully_async_rollout.py.txt) | AsyncRolloutWorker.__init__ | api_reference | queue.Queue | lexical_import_resolution |         self.output_queue: queue.Queue[tuple[int, list[Sample]]] = queue.Queue() |
| occ-001029 | [slime/rollout/fully_async_rollout.py:97](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_rollout.py#L97) · [快照](../source_snapshot/slime/rollout/fully_async_rollout.py.txt) | AsyncRolloutWorker.__init__ | api_call | queue.Queue | lexical_import_resolution |         self.output_queue: queue.Queue[tuple[int, list[Sample]]] = queue.Queue() |
| occ-001039 | [slime/rollout/fully_async_rollout.py:154](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_rollout.py#L154) · [快照](../source_snapshot/slime/rollout/fully_async_rollout.py.txt) | AsyncRolloutWorker.get_completed_groups | api_reference | queue.Empty | lexical_import_resolution |             except queue.Empty: |
