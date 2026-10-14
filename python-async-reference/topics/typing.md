# typing — Support for type hints — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/typing.html
- 抓取状态：ok
- 纳入理由：Awaitable, Coroutine, AsyncIterable, AsyncIterator, AsyncGenerator and AsyncContextManager annotations; full page retained.
- 范围：matched_sections

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`typing.AsyncContextManager`](https://docs.python.org/3.16/library/typing.html#typing.AsyncContextManager) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`typing.AsyncGenerator`](https://docs.python.org/3.16/library/typing.html#typing.AsyncGenerator) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 12 |
| [`typing.AsyncIterable`](https://docs.python.org/3.16/library/typing.html#typing.AsyncIterable) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`typing.AsyncIterator`](https://docs.python.org/3.16/library/typing.html#typing.AsyncIterator) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`typing.Awaitable`](https://docs.python.org/3.16/library/typing.html#typing.Awaitable) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`typing.Coroutine`](https://docs.python.org/3.16/library/typing.html#typing.Coroutine) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/base.py:567](../repositories/verl/source_snapshot/verl/checkpoint_engine/base.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/base.py#L567) | ) -&gt; AsyncGenerator[tuple[TensorMeta, torch.Tensor &#124; None], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/base.py:596](../repositories/verl/source_snapshot/verl/checkpoint_engine/base.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/base.py#L596) | ) -&gt; AsyncGenerator[tuple[str, torch.Tensor], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/hccl_checkpoint_engine.py:318](../repositories/verl/source_snapshot/verl/checkpoint_engine/hccl_checkpoint_engine.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/hccl_checkpoint_engine.py#L318) |     ) -&gt; AsyncGenerator[tuple[str, torch.Tensor], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/hccl_checkpoint_engine.py:327](../repositories/verl/source_snapshot/verl/checkpoint_engine/hccl_checkpoint_engine.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/hccl_checkpoint_engine.py#L327) |     async def _receive_weight_chunks(self) -&gt; AsyncGenerator[tuple[str, torch.Tensor], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/kimi_checkpoint_engine.py:73](../repositories/verl/source_snapshot/verl/checkpoint_engine/kimi_checkpoint_engine.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/kimi_checkpoint_engine.py#L73) | ) -&gt; AsyncGenerator[tuple[str, torch.Tensor], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/kimi_checkpoint_engine.py:369](../repositories/verl/source_snapshot/verl/checkpoint_engine/kimi_checkpoint_engine.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/kimi_checkpoint_engine.py#L369) |     ) -&gt; AsyncGenerator[tuple[str, torch.Tensor], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/mooncake_checkpoint_engine.py:242](../repositories/verl/source_snapshot/verl/checkpoint_engine/mooncake_checkpoint_engine.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/mooncake_checkpoint_engine.py#L242) |     ) -&gt; AsyncGenerator[tuple[str, torch.Tensor], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/nccl_checkpoint_engine.py:440](../repositories/verl/source_snapshot/verl/checkpoint_engine/nccl_checkpoint_engine.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/nccl_checkpoint_engine.py#L440) |     ) -&gt; AsyncGenerator[tuple[str, torch.Tensor], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/nccl_checkpoint_engine.py:449](../repositories/verl/source_snapshot/verl/checkpoint_engine/nccl_checkpoint_engine.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/nccl_checkpoint_engine.py#L449) |     async def _receive_weight_chunks(self) -&gt; AsyncGenerator[tuple[str, torch.Tensor], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/nixl_checkpoint_engine.py:443](../repositories/verl/source_snapshot/verl/checkpoint_engine/nixl_checkpoint_engine.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/nixl_checkpoint_engine.py#L443) |     ) -&gt; AsyncGenerator[tuple[str, torch.Tensor], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/checkpoint_engine/nixl_checkpoint_engine.py:452](../repositories/verl/source_snapshot/verl/checkpoint_engine/nixl_checkpoint_engine.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/checkpoint_engine/nixl_checkpoint_engine.py#L452) |     async def _receive_weight_chunks(self) -&gt; AsyncGenerator[tuple[TensorMeta, torch.Tensor], None]: |
| verl / core | `typing.AsyncGenerator` | api_reference | [verl/workers/rollout/trtllm_rollout/trtllm_rollout.py:452](../repositories/verl/source_snapshot/verl/workers/rollout/trtllm_rollout/trtllm_rollout.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/workers/rollout/trtllm_rollout/trtllm_rollout.py#L452) |         weights: AsyncGenerator[tuple[str, torch.Tensor], None], |
