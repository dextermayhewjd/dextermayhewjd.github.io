# fcntl

邻接机制：fcntl 文件锁同步。

固定源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。本表共 **10** 条静态出现记录；不是运行次数。

同一个直接 API 表达式只记为 `api_call` 或 `api_reference` 中的一类。实例候选不计入直接原生 API 总数。

[总览](../README.md) · [完整文件索引](../FILES.md) · [JSON](../inventory.json) · [TSV](../inventory.tsv)

| ID | 位置 / 快照 | 所属符号 | 种类 | API / 语法 | 来源判定 | 源码行 |
| --- | --- | --- | --- | --- | --- | --- |
| occ-000746 | [slime/data/queue_data_source.py:13](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L13) · [快照](../source_snapshot/slime/data/queue_data_source.py.txt) | &lt;module&gt; | import | fcntl | explicit_import | import fcntl |
| occ-000750 | [slime/data/queue_data_source.py:73](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L73) · [快照](../source_snapshot/slime/data/queue_data_source.py.txt) | RolloutQueueController.__init__ | api_call | fcntl.flock | lexical_import_resolution |                     fcntl.flock(self._checkpoint_lock.fileno(), fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| occ-000751 | [slime/data/queue_data_source.py:73](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L73) · [快照](../source_snapshot/slime/data/queue_data_source.py.txt) | RolloutQueueController.__init__ | api_reference | fcntl.LOCK_EX | lexical_import_resolution |                     fcntl.flock(self._checkpoint_lock.fileno(), fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| occ-000752 | [slime/data/queue_data_source.py:73](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L73) · [快照](../source_snapshot/slime/data/queue_data_source.py.txt) | RolloutQueueController.__init__ | api_reference | fcntl.LOCK_NB | lexical_import_resolution |                     fcntl.flock(self._checkpoint_lock.fileno(), fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| occ-001361 | [tests/ci/gpu_lock_exec.py:3](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/ci/gpu_lock_exec.py#L3) · [快照](../source_snapshot/tests/ci/gpu_lock_exec.py.txt) | &lt;module&gt; | import | fcntl | explicit_import | import fcntl |
| occ-001387 | [tests/ci/gpu_lock_exec.py:127](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/ci/gpu_lock_exec.py#L127) · [快照](../source_snapshot/tests/ci/gpu_lock_exec.py.txt) | _execute_print_only | api_call | fcntl.flock | lexical_import_resolution |                 fcntl.flock(fd_lock.fd, fcntl.LOCK_UN) |
| occ-001388 | [tests/ci/gpu_lock_exec.py:127](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/ci/gpu_lock_exec.py#L127) · [快照](../source_snapshot/tests/ci/gpu_lock_exec.py.txt) | _execute_print_only | api_reference | fcntl.LOCK_UN | lexical_import_resolution |                 fcntl.flock(fd_lock.fd, fcntl.LOCK_UN) |
| occ-001396 | [tests/ci/gpu_lock_exec.py:213](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/ci/gpu_lock_exec.py#L213) · [快照](../source_snapshot/tests/ci/gpu_lock_exec.py.txt) | FdLock.lock | api_call | fcntl.flock | lexical_import_resolution |         fcntl.flock(self.fd, fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| occ-001397 | [tests/ci/gpu_lock_exec.py:213](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/ci/gpu_lock_exec.py#L213) · [快照](../source_snapshot/tests/ci/gpu_lock_exec.py.txt) | FdLock.lock | api_reference | fcntl.LOCK_EX | lexical_import_resolution |         fcntl.flock(self.fd, fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
| occ-001398 | [tests/ci/gpu_lock_exec.py:213](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/ci/gpu_lock_exec.py#L213) · [快照](../source_snapshot/tests/ci/gpu_lock_exec.py.txt) | FdLock.lock | api_reference | fcntl.LOCK_NB | lexical_import_resolution |         fcntl.flock(self.fd, fcntl.LOCK_EX &#124; fcntl.LOCK_NB) |
