# Streams — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/asyncio-stream.html
- 抓取状态：ok
- 纳入理由：User-requested asyncio page.
- 范围：full_page

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`asyncio.StreamReader`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamReader) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamReader.at_eof`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamReader.at_eof) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamReader.feed_eof`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamReader.feed_eof) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamReader.read`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamReader.read) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamReader.readexactly`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamReader.readexactly) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamReader.readline`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamReader.readline) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamReader.readuntil`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamReader.readuntil) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.can_write_eof`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.can_write_eof) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.close`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.close) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.drain`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.drain) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.get_extra_info`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.get_extra_info) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.is_closing`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.is_closing) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.start_tls`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.start_tls) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.transport`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.transport) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.wait_closed`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.wait_closed) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.write`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.write) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.write_eof`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.write_eof) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.StreamWriter.writelines`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.StreamWriter.writelines) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.open_connection`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.open_connection) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.open_unix_connection`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.open_unix_connection) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.start_server`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.start_server) | 1 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.start_unix_server`](https://docs.python.org/3.16/library/asyncio-stream.html#asyncio.start_unix_server) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
| slime / tests | `asyncio.start_server` | api_call | [tests/test_server_control.py:261](../repositories/slime/source_snapshot/tests/test_server_control.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_server_control.py#L261) |         server = await asyncio.start_server(serve, "127.0.0.1", 0, backlog=2 * concurrency) |
