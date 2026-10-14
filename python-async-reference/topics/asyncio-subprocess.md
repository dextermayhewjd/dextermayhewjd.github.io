# Subprocesses — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/asyncio-subprocess.html
- 抓取状态：ok
- 纳入理由：User-requested asyncio page.
- 范围：full_page

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`asyncio.create_subprocess_exec`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.create_subprocess_exec) | 0 / 0 / 0 | 2 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.create_subprocess_shell`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.create_subprocess_shell) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.DEVNULL`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.DEVNULL) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.PIPE`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.PIPE) | 0 / 0 / 0 | 0 / 0 / 2 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process.communicate`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process.communicate) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process.kill`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process.kill) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process.pid`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process.pid) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process.returncode`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process.returncode) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process.send_signal`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process.send_signal) | 0 / 0 / 0 | 0 / 4 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process.stderr`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process.stderr) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process.stdin`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process.stdin) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process.stdout`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process.stdout) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process.terminate`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process.terminate) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.Process.wait`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.Process.wait) | 0 / 0 / 0 | 0 / 2 / 0 | 0 / 0 / 0 |
| [`asyncio.subprocess.STDOUT`](https://docs.python.org/3.16/library/asyncio-subprocess.html#asyncio.subprocess.STDOUT) | 0 / 0 / 0 | 0 / 0 / 2 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
| areal / tests | `asyncio.create_subprocess_exec` | api_call | [tests/test_examples.py:59](../repositories/areal/source_snapshot/tests/test_examples.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_examples.py#L59) |     process = await asyncio.create_subprocess_exec( |
| areal / tests | `asyncio.subprocess.PIPE` | api_reference | [tests/test_examples.py:61](../repositories/areal/source_snapshot/tests/test_examples.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_examples.py#L61) |         stdout=asyncio.subprocess.PIPE, |
| areal / tests | `asyncio.subprocess.STDOUT` | api_reference | [tests/test_examples.py:62](../repositories/areal/source_snapshot/tests/test_examples.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_examples.py#L62) |         stderr=asyncio.subprocess.STDOUT, |
| areal / tests | `asyncio.subprocess.Process.send_signal` | inferred_method | [tests/test_examples.py:87](../repositories/areal/source_snapshot/tests/test_examples.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_examples.py#L87) |             process.send_signal(signal.SIGINT)  # Gracefully terminate the process |
| areal / tests | `asyncio.subprocess.Process.wait` | inferred_method | [tests/test_examples.py:92](../repositories/areal/source_snapshot/tests/test_examples.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_examples.py#L92) |             return_code = await asyncio.wait_for(process.wait(), timeout=0.01) |
| areal / tests | `asyncio.subprocess.Process.send_signal` | inferred_method | [tests/test_examples.py:101](../repositories/areal/source_snapshot/tests/test_examples.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_examples.py#L101) |             process.send_signal(signal.SIGINT)  # Gracefully terminate the process |
| areal / tests | `asyncio.create_subprocess_exec` | api_call | [tests/test_sglang_pp_distributed.py:102](../repositories/areal/source_snapshot/tests/test_sglang_pp_distributed.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_sglang_pp_distributed.py#L102) |     process = await asyncio.create_subprocess_exec( |
| areal / tests | `asyncio.subprocess.PIPE` | api_reference | [tests/test_sglang_pp_distributed.py:104](../repositories/areal/source_snapshot/tests/test_sglang_pp_distributed.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_sglang_pp_distributed.py#L104) |         stdout=asyncio.subprocess.PIPE, |
| areal / tests | `asyncio.subprocess.STDOUT` | api_reference | [tests/test_sglang_pp_distributed.py:105](../repositories/areal/source_snapshot/tests/test_sglang_pp_distributed.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_sglang_pp_distributed.py#L105) |         stderr=asyncio.subprocess.STDOUT, |
| areal / tests | `asyncio.subprocess.Process.send_signal` | inferred_method | [tests/test_sglang_pp_distributed.py:126](../repositories/areal/source_snapshot/tests/test_sglang_pp_distributed.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_sglang_pp_distributed.py#L126) |             process.send_signal(signal.SIGINT) |
| areal / tests | `asyncio.subprocess.Process.wait` | inferred_method | [tests/test_sglang_pp_distributed.py:130](../repositories/areal/source_snapshot/tests/test_sglang_pp_distributed.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_sglang_pp_distributed.py#L130) |             return_code = await asyncio.wait_for(process.wait(), timeout=0.01) |
| areal / tests | `asyncio.subprocess.Process.send_signal` | inferred_method | [tests/test_sglang_pp_distributed.py:138](../repositories/areal/source_snapshot/tests/test_sglang_pp_distributed.py.txt) · [固定版本](https://github.com/areal-project/AReaL/blob/298412a40f5b84ae6b2042987e81777e6dd0f284/tests/test_sglang_pp_distributed.py#L138) |             process.send_signal(signal.SIGINT) |
