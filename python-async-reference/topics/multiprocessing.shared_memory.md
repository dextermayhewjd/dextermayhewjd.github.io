# multiprocessing.shared_memory — Shared memory for direct access across processes — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/multiprocessing.shared_memory.html
- 抓取状态：ok
- 纳入理由：Shared memory is an adjacent interprocess data-sharing mechanism used alongside worker and executor processes.
- 范围：full_page

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`multiprocessing.managers.SharedMemoryManager`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.managers.SharedMemoryManager) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.managers.SharedMemoryManager.ShareableList`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.managers.SharedMemoryManager.ShareableList) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.managers.SharedMemoryManager.SharedMemory`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.managers.SharedMemoryManager.SharedMemory) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.shared_memory.ShareableList`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.ShareableList) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.shared_memory.ShareableList.count`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.ShareableList.count) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.shared_memory.ShareableList.format`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.ShareableList.format) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.shared_memory.ShareableList.index`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.ShareableList.index) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.shared_memory.ShareableList.shm`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.ShareableList.shm) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.shared_memory.SharedMemory`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.SharedMemory) | 0 / 0 / 0 | 0 / 0 / 0 | 4 / 0 / 0 |
| [`multiprocessing.shared_memory.SharedMemory.buf`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.SharedMemory.buf) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.shared_memory.SharedMemory.close`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.SharedMemory.close) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.shared_memory.SharedMemory.name`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.SharedMemory.name) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.shared_memory.SharedMemory.size`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.SharedMemory.size) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`multiprocessing.shared_memory.SharedMemory.unlink`](https://docs.python.org/3.16/library/multiprocessing.shared_memory.html#multiprocessing.shared_memory.SharedMemory.unlink) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
| verl / tests | `multiprocessing.shared_memory.SharedMemory` | api_call | [tests/utils/test_shared_memory.py:210](../repositories/verl/source_snapshot/tests/utils/test_shared_memory.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/tests/utils/test_shared_memory.py#L210) |         shm = shared_memory.SharedMemory(name=name) |
| verl / core | `multiprocessing.shared_memory.SharedMemory` | api_call | [verl/workers/rollout/vllm_rollout/bucketed_weight_transfer.py:58](../repositories/verl/source_snapshot/verl/workers/rollout/vllm_rollout/bucketed_weight_transfer.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/workers/rollout/vllm_rollout/bucketed_weight_transfer.py#L58) |         shm = shared_memory.SharedMemory(name=name, create=True, size=size) |
| verl / core | `multiprocessing.shared_memory.SharedMemory` | api_call | [verl/workers/rollout/vllm_rollout/bucketed_weight_transfer.py:60](../repositories/verl/source_snapshot/verl/workers/rollout/vllm_rollout/bucketed_weight_transfer.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/workers/rollout/vllm_rollout/bucketed_weight_transfer.py#L60) |         shm = shared_memory.SharedMemory(name=name) |
| verl / core | `multiprocessing.shared_memory.SharedMemory` | api_call | [verl/workers/rollout/vllm_rollout/bucketed_weight_transfer.py:67](../repositories/verl/source_snapshot/verl/workers/rollout/vllm_rollout/bucketed_weight_transfer.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/workers/rollout/vllm_rollout/bucketed_weight_transfer.py#L67) |     shm = shared_memory.SharedMemory(name=name) |
