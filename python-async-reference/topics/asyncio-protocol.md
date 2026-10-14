# Transports and Protocols — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/asyncio-protocol.html
- 抓取状态：ok
- 纳入理由：User-requested asyncio page.
- 范围：full_page

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`asyncio.BaseProtocol`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseProtocol) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BaseProtocol.connection_lost`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseProtocol.connection_lost) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BaseProtocol.connection_made`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseProtocol.connection_made) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BaseProtocol.pause_writing`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseProtocol.pause_writing) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BaseProtocol.resume_writing`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseProtocol.resume_writing) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BaseTransport`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseTransport) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BaseTransport.close`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseTransport.close) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BaseTransport.get_extra_info`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseTransport.get_extra_info) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BaseTransport.get_protocol`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseTransport.get_protocol) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BaseTransport.is_closing`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseTransport.is_closing) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BaseTransport.set_protocol`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BaseTransport.set_protocol) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BufferedProtocol`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BufferedProtocol) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BufferedProtocol.buffer_updated`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BufferedProtocol.buffer_updated) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BufferedProtocol.eof_received`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BufferedProtocol.eof_received) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.BufferedProtocol.get_buffer`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.BufferedProtocol.get_buffer) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.DatagramProtocol`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.DatagramProtocol) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.DatagramProtocol.datagram_received`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.DatagramProtocol.datagram_received) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.DatagramProtocol.error_received`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.DatagramProtocol.error_received) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.DatagramTransport`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.DatagramTransport) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.DatagramTransport.abort`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.DatagramTransport.abort) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.DatagramTransport.sendto`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.DatagramTransport.sendto) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.Protocol`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.Protocol) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.Protocol.data_received`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.Protocol.data_received) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.Protocol.eof_received`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.Protocol.eof_received) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.ReadTransport`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.ReadTransport) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.ReadTransport.is_reading`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.ReadTransport.is_reading) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.ReadTransport.pause_reading`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.ReadTransport.pause_reading) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.ReadTransport.resume_reading`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.ReadTransport.resume_reading) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessProtocol`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessProtocol) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessProtocol.pipe_connection_lost`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessProtocol.pipe_connection_lost) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessProtocol.pipe_data_received`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessProtocol.pipe_data_received) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessProtocol.process_exited`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessProtocol.process_exited) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessTransport`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessTransport) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessTransport.close`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessTransport.close) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessTransport.get_pid`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessTransport.get_pid) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessTransport.get_pipe_transport`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessTransport.get_pipe_transport) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessTransport.get_returncode`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessTransport.get_returncode) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessTransport.kill`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessTransport.kill) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessTransport.send_signal`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessTransport.send_signal) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.SubprocessTransport.terminate`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.SubprocessTransport.terminate) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.Transport`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.Transport) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.WriteTransport`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.WriteTransport) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.WriteTransport.abort`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.WriteTransport.abort) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.WriteTransport.can_write_eof`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.WriteTransport.can_write_eof) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.WriteTransport.get_write_buffer_limits`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.WriteTransport.get_write_buffer_limits) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.WriteTransport.get_write_buffer_size`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.WriteTransport.get_write_buffer_size) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.WriteTransport.set_write_buffer_limits`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.WriteTransport.set_write_buffer_limits) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.WriteTransport.write`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.WriteTransport.write) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.WriteTransport.write_eof`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.WriteTransport.write_eof) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`asyncio.WriteTransport.writelines`](https://docs.python.org/3.16/library/asyncio-protocol.html#asyncio.WriteTransport.writelines) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
