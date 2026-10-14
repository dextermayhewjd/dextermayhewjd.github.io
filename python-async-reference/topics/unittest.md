# unittest — Unit testing framework — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/unittest.html
- 抓取状态：ok
- 纳入理由：IsolatedAsyncioTestCase and asynchronous setup/cleanup support async tests; full framework reference retained.
- 范围：matched_sections

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`unittest.IsolatedAsyncioTestCase`](https://docs.python.org/3.16/library/unittest.html#unittest.IsolatedAsyncioTestCase) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 3 |
| [`unittest.IsolatedAsyncioTestCase.addAsyncCleanup`](https://docs.python.org/3.16/library/unittest.html#unittest.IsolatedAsyncioTestCase.addAsyncCleanup) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`unittest.IsolatedAsyncioTestCase.asyncSetUp`](https://docs.python.org/3.16/library/unittest.html#unittest.IsolatedAsyncioTestCase.asyncSetUp) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`unittest.IsolatedAsyncioTestCase.asyncTearDown`](https://docs.python.org/3.16/library/unittest.html#unittest.IsolatedAsyncioTestCase.asyncTearDown) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`unittest.IsolatedAsyncioTestCase.enterAsyncContext`](https://docs.python.org/3.16/library/unittest.html#unittest.IsolatedAsyncioTestCase.enterAsyncContext) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`unittest.IsolatedAsyncioTestCase.loop_factory`](https://docs.python.org/3.16/library/unittest.html#unittest.IsolatedAsyncioTestCase.loop_factory) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`unittest.IsolatedAsyncioTestCase.run`](https://docs.python.org/3.16/library/unittest.html#unittest.IsolatedAsyncioTestCase.run) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
| verl / tests | `unittest.IsolatedAsyncioTestCase` | api_reference | [tests/experimental/agent_loop/test_call_tool_on_cpu.py:95](../repositories/verl/source_snapshot/tests/experimental/agent_loop/test_call_tool_on_cpu.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/tests/experimental/agent_loop/test_call_tool_on_cpu.py#L95) | class TestCallToolErrorHandling(unittest.IsolatedAsyncioTestCase): |
| verl / tests | `unittest.IsolatedAsyncioTestCase` | api_reference | [tests/experimental/agent_loop/test_tool_call_id_on_cpu.py:58](../repositories/verl/source_snapshot/tests/experimental/agent_loop/test_tool_call_id_on_cpu.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/tests/experimental/agent_loop/test_tool_call_id_on_cpu.py#L58) | class TestToolCallIdOnCpu(unittest.IsolatedAsyncioTestCase): |
| verl / tests | `unittest.IsolatedAsyncioTestCase` | api_reference | [tests/utils/test_server_profiler.py:491](../repositories/verl/source_snapshot/tests/utils/test_server_profiler.py.txt) · [固定版本](https://github.com/verl-project/verl/blob/1d367a4f459a43768f76312c0d3430a99ec46b8c/tests/utils/test_server_profiler.py#L491) | class TestServerProfilerFunctionality(unittest.IsolatedAsyncioTestCase): |
