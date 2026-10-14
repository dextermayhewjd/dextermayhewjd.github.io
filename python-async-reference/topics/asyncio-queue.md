# Queues — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/asyncio-queue.html
- 抓取状态：ok
- 纳入理由：User-requested asyncio page.
- 范围：full_page

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`asyncio.LifoQueue`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.LifoQueue) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.PriorityQueue`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.PriorityQueue) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue) | 1 / 0 / 0 | 2 / 0 / 1 | 3 / 0 / 0 |
| [`asyncio.Queue.empty`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.empty) | 0 / 0 / 0 | 0 / 1 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue.full`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.full) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue.get`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.get) | 0 / 0 / 0 | 0 / 1 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue.get_nowait`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.get_nowait) | 0 / 0 / 0 | 0 / 1 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue.join`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.join) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue.maxsize`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.maxsize) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue.put`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.put) | 0 / 0 / 0 | 0 / 1 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue.put_nowait`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.put_nowait) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue.qsize`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.qsize) | 0 / 0 / 0 | 0 / 2 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue.shutdown`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.shutdown) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.Queue.task_done`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.Queue.task_done) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.QueueEmpty`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.QueueEmpty) | 0 / 0 / 0 | 0 / 0 / 1 | 0 / 0 / 0 |
| [`asyncio.QueueFull`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.QueueFull) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.QueueShutDown`](https://docs.python.org/3.16/library/asyncio-queue.html#asyncio.QueueShutDown) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
| slime / core | `asyncio.Queue` | api_call | [slime/rollout/fully_async_distributed.py:291](../repositories/slime/source_snapshot/slime/rollout/fully_async_distributed.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/slime/rollout/fully_async_distributed.py#L291) |             self.outputs = asyncio.Queue(maxsize=1) |
| areal / core | `asyncio.Queue` | api_reference | [areal/experimental/openai/proxy/proxy_gateway.py:169](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/proxy_gateway.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/proxy_gateway.py#L169) |     ready_workers: asyncio.Queue[_ReadyWorkerEntry] = asyncio.Queue() |
| areal / core | `asyncio.Queue` | api_call | [areal/experimental/openai/proxy/proxy_gateway.py:169](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/proxy_gateway.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/proxy_gateway.py#L169) |     ready_workers: asyncio.Queue[_ReadyWorkerEntry] = asyncio.Queue() |
| areal / core | `asyncio.Queue.qsize` | inferred_method | [areal/experimental/openai/proxy/proxy_gateway.py:242](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/proxy_gateway.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/proxy_gateway.py#L242) |         queued = ready_workers.qsize() |
| areal / core | `asyncio.Queue.get` | inferred_method | [areal/experimental/openai/proxy/proxy_gateway.py:405](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/proxy_gateway.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/proxy_gateway.py#L405) |                             ready_workers.get(), timeout=remaining |
| areal / core | `asyncio.Queue.empty` | inferred_method | [areal/experimental/openai/proxy/proxy_gateway.py:494](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/proxy_gateway.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/proxy_gateway.py#L494) |         while not ready_workers.empty(): |
| areal / core | `asyncio.Queue.get_nowait` | inferred_method | [areal/experimental/openai/proxy/proxy_gateway.py:496](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/proxy_gateway.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/proxy_gateway.py#L496) |                 candidate = ready_workers.get_nowait() |
| areal / core | `asyncio.QueueEmpty` | api_reference | [areal/experimental/openai/proxy/proxy_gateway.py:497](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/proxy_gateway.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/proxy_gateway.py#L497) |             except asyncio.QueueEmpty: |
| areal / core | `asyncio.Queue.put` | inferred_method | [areal/experimental/openai/proxy/proxy_gateway.py:700](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/proxy_gateway.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/proxy_gateway.py#L700) |         await ready_workers.put(entry) |
| areal / core | `asyncio.Queue.qsize` | inferred_method | [areal/experimental/openai/proxy/proxy_gateway.py:704](../repositories/areal/source_snapshot/areal/experimental/openai/proxy/proxy_gateway.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/areal/experimental/openai/proxy/proxy_gateway.py#L704) |             ready_workers.qsize(), |
| areal / examples | `asyncio.Queue` | api_call | [examples/scaffolding/core/scaffolding_llm.py:161](../repositories/areal/source_snapshot/examples/scaffolding/core/scaffolding_llm.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/examples/scaffolding/core/scaffolding_llm.py#L161) |             self.task_queue = asyncio.Queue() |
| verl / core | `asyncio.Queue` | api_call | [verl/experimental/fully_async_policy/fully_async_rollouter.py:461](../repositories/verl/source_snapshot/verl/experimental/fully_async_policy/fully_async_rollouter.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/fully_async_policy/fully_async_rollouter.py#L461) |         self.pending_queue = asyncio.Queue(maxsize=128) |
| verl / core | `asyncio.Queue` | api_call | [verl/experimental/fully_async_policy/unittest/simple_streaming_demo.py:25](../repositories/verl/source_snapshot/verl/experimental/fully_async_policy/unittest/simple_streaming_demo.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/fully_async_policy/unittest/simple_streaming_demo.py#L25) |         self.data_queue = asyncio.Queue() |
| verl / core | `asyncio.Queue` | api_call | [verl/experimental/fully_async_policy/unittest/simple_streaming_demo.py:26](../repositories/verl/source_snapshot/verl/experimental/fully_async_policy/unittest/simple_streaming_demo.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/experimental/fully_async_policy/unittest/simple_streaming_demo.py#L26) |         self.result_queue = asyncio.Queue() |
