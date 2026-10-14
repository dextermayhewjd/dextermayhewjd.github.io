# Built-in functions — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/builtins/functions.html
- 抓取状态：ok
- 纳入理由：aiter and anext built-ins implement asynchronous iteration; full built-in reference retained.
- 范围：matched_sections

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`builtins.aiter`](https://docs.python.org/3.16/builtins/functions.html#aiter) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`builtins.anext`](https://docs.python.org/3.16/builtins/functions.html#anext) | 0 / 0 / 0 | 2 / 0 / 0 | 1 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
| areal / tests | `builtins.anext` | api_call | [tests/experimental/openai/test_streaming_chat_completions.py:558](../repositories/areal/source_snapshot/tests/experimental/openai/test_streaming_chat_completions.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/experimental/openai/test_streaming_chat_completions.py#L558) |         first = await asyncio.wait_for(anext(iterator), timeout=0.1) |
| areal / tests | `builtins.anext` | api_call | [tests/experimental/openai/test_streaming_chat_completions.py:562](../repositories/areal/source_snapshot/tests/experimental/openai/test_streaming_chat_completions.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/experimental/openai/test_streaming_chat_completions.py#L562) |         next_event = asyncio.create_task(anext(iterator)) |
| verl / core | `builtins.anext` | api_call | [verl/workers/rollout/vllm_rollout/vllm_rollout.py:270](../repositories/verl/source_snapshot/verl/workers/rollout/vllm_rollout/vllm_rollout.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/verl/workers/rollout/vllm_rollout/vllm_rollout.py#L270) |             first_item = await anext(flushes) |
