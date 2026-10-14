---
title: "22 · asyncio Streams：接收、分帧与连接收尾"
description: "跟随 Slime 的本地测试服务器，区分读取语义、写入背压和服务关闭。"
weight: 220
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="stream-route"></span>
## 这一次跟随一条 TCP 连接

本章输入是一串 TCP 字节，输出是处理函数写回的字节。主线是“监听 → 接受连接 → 按协议读取 → 写回 → 关闭该连接 → 关闭监听”。第 12 节的 `async with` 只说明进入和退出可以等待；这次把等待放到真实 I/O 边界上。


<span id="start-server"></span>
## 第一步：start_server 把连接交给 serve

`server = await asyncio.start_server(serve, "127.0.0.1", 0, ...)` 创建监听并返回 `asyncio.Server`。`0` 让系统选择空闲端口，`server.sockets[0].getsockname()[1]` 读取实际端口。默认在返回前开始接受连接；创建 server 本身不等于把某一条连接处理完。

每次新连接到达，回调得到 `StreamReader` 和 `StreamWriter`。如果回调是本章这种 `async def serve(reader, writer)`，asyncio 会把它安排成 Task。并发发生在多条连接处理任务之间；单个 `serve` 中的读取仍按书写顺序进行。

客户端的对称入口是 `reader, writer = await asyncio.open_connection(host, port)`。传入的端口必须来自这次 server 的实际监听，而不是硬编码一个可能被占用的端口。


<span id="stream-reader"></span>
## 第二步：TCP 没有消息边界，Reader 按协议取字节


| `asyncio.StreamReader` 方法 | 返回与 EOF 行为 | 适用边界 |
| --- | --- | --- |
| `await read(n)`，`n > 0` | 至多 n 字节，有数据即可返回；可能比 n 少，空缓冲遇 EOF 返回 `b""` | 消费目前可得到的一段，再由调用方累积 |
| `await read()` / `read(-1)` | 一直等到 EOF，再返回剩余全部字节 | 协议明确用关闭发送结束，不能用于仍保持连接的消息结尾 |
| `await readline()` | 一行，含 `\n`；EOF 前残留的半行也可返回 | 行协议；空缓冲遇 EOF 返回 `b""` |
| `await readuntil(separator)` | 返回值含分隔符；完整分隔符未到就继续等 | 头部或自定义结束标记 |
| `await readexactly(n)` | 恰好 n 字节，否则遇 EOF 抛 `asyncio.IncompleteReadError` | 已知长度的 body |

`read(0)` 立即给出 `b""`，因此不要仅凭这个返回值判断断线。`readuntil` 在 EOF 前未见完整分隔符也抛 `IncompleteReadError`；其 `partial` 包含已读取部分。超过 reader 的缓冲限制则可能抛 `asyncio.LimitOverrunError`，这是“边界过长”，与“对端提前结束”不同；不能靠无限增大缓冲替代协议长度校验。

<span id="incomplete-read"></span>
## 第三步：提前 EOF 是一个有数据的失败

`IncompleteReadError.partial` 保存不完整字节，`expected` 在 `readexactly(n)` 场景记录期待的长度。实验故意声明长度 5，只发 `b"xy"` 就关闭，服务端得到 `partial == b"xy"`、`expected == 5`。不能把这两个字节当作完整成功结果。


<span id="stream-writer"></span>
## 第四步：write 入队，drain 配合写入流量控制

`writer.write(data)` 是同步方法，尝试立即写出或把 bytes 留在底层缓冲；它不保证对端已经收到，也不能写成 `await writer.write(...)`。`await writer.drain()` 在缓冲压力高时等待恢复可写，压力低时可立即返回。它不是对端业务确认，也不承诺每次都切换任务。

连接收尾用 `writer.close()` 发起关闭，再 `await writer.wait_closed()` 等待本端关闭完成。读写或关闭过程中仍可能抛连接错误，所以资源收尾必须放在 `finally`。真实 `serve` 在这里先减少 active 计数，再关闭 writer，最后从 handler 集合移除当前 Task；监听器并不替每个连接做这些业务记账。

<span id="server-lifecycle"></span>
## 第五步：监听器和已接受的连接分开收尾

| `asyncio.Server` 操作 | 生命周期意义 |
| --- | --- |
| `is_serving()` | 观察是否正在接受连接，不统计已接受的 handler 是否结束 |
| `await serve_forever()` | 持续运行监听入口；取消该等待会触发服务关闭，已存在连接仍有独立生命周期 |
| `close()` | 停止监听新的连接；不是强制完成所有 handler |
| `await wait_closed()` | 等 server 与其连接关闭完成；handler 余下业务仍应显式等完或取消 |
| `async with server` | 为 server 的退出安排关闭和等待；同样不能替代管理业务任务 |


<span id="stream-lab"></span>
## 可运行实验：完整消息与截断消息

[下载 example.py](example.py)，执行 `python3 -W error example.py`。仅 Python 标准库，推荐 Python 3.12，最低 3.11；只在 `127.0.0.1` 上临时监听，不访问外部网络。

教学裁剪保留真实 `serve(reader, writer)`、`start_server`、读写和收尾接口。把 HTTP 头换成“十进制长度 + `\r\n\r\n`”，去掉 HTTPX 客户端、连接池压力测试和第三方 transport；额外一个字节用于展示 `read(1)`，响应首行展示 `readline()`。`Queue` 只把处理结果传回实验主任务，确保输出与 handler 关闭都已完成。

<details><summary>展开完整实验：example.py</summary>

```python
"""Cut down from tests/test_server_control.py: local TCP, no HTTP client."""
import asyncio


async def exercise():
    reports = asyncio.Queue()

    async def serve(reader, writer):
        report = None
        try:
            headers = await reader.readuntil(b'\r\n\r\n')
            length = int(headers.split(b'\r\n', 1)[0])
            body = await reader.readexactly(length)
            suffix = await reader.read(1)
            writer.write(b'echo\n' + body)
            await writer.drain()
            report = ('complete', body, suffix)
        except asyncio.IncompleteReadError as error:
            report = ('incomplete', error.partial, error.expected)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            finally:
                reports.put_nowait(report)

    server = await asyncio.start_server(serve, '127.0.0.1', 0)
    port = server.sockets[0].getsockname()[1]
    print('server listening', server.is_serving())
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        try:
            writer.write(b'3\r\n\r\nabc!')
            await writer.drain()
            print('reply line', (await reader.readline()).decode().strip())
            print('reply body', await reader.read())
        finally:
            writer.close()
            await writer.wait_closed()
        print('handler', await reports.get())

        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        writer.write(b'5\r\n\r\nxy')
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        print('handler', await reports.get())
    finally:
        server.close()
        await server.wait_closed()
    print('server listening', server.is_serving())


if __name__ == '__main__':
    asyncio.run(exercise())
```

</details>

```text
server listening True
reply line echo
reply body b'abc'
handler ('complete', b'abc', b'!')
handler ('incomplete', b'xy', 5)
server listening False
```

按实际调用追踪：第一个客户端发送完整消息 → server 先读分隔符再读固定 body → 写响应并关闭 → 客户端的 `read()` 因 EOF 返回 body。第二个客户端提前关闭 → server 在 `readexactly(5)` 抛错 → `finally` 关闭连接并上报残留字节。最后主任务关闭 server。

<details><summary>复述检查</summary>

如果把 `readexactly(5)` 换成 `read(5)`，为什么 `b"xy"` 可能成为一次正常返回？如果响应使用长连接，为什么客户端 `read()` 可能一直等待？为什么 `server.close()` 后还需要关心连接处理任务？

</details>

语义核对：[Streams 与读取/写入方法](https://docs.python.org/3.12/library/asyncio-stream.html)、[Server 生命周期](https://docs.python.org/3.12/library/asyncio-eventloop.html#server-objects)、[IncompleteReadError](https://docs.python.org/3.12/library/asyncio-exceptions.html#asyncio.IncompleteReadError)。

{{< python-async-slime >}}

固定源码来自 `tests/test_server_control.py`。测试用一个本地 TCP 服务器检查 Slime 的 HTTP transport；HTTPX 只是它的客户端，`reader` / `writer` 来自 Python 标准库 asyncio。我们只裁剪服务器职责，不把 HTTPX、Ray 或其他第三方同名方法当成原生 Streams API。

<details><summary>展开固定源码：监听入口与真实调用环境</summary>

{{< source-reference id="source-2" >}}

</details>

Slime 测试先 `await reader.readuntil(b"\r\n\r\n")` 取出完整 HTTP 头，再解析 `Content-Length`，最后 `await reader.readexactly(length)` 取 body。两个 await 分别对应两个协议边界。不能把“一次发送”推断成“一次 read 恰好返回完整消息”。

真实测试捕获 `(asyncio.IncompleteReadError, ConnectionError)` 后进入 `finally`，适合它的持久连接测试：客户端正常结束连接时，下一轮读头也会遇到 EOF。生产协议是否重试、返回错误还是记录截断，要结合当前处理阶段决定。

<details><summary>展开固定源码：按头/body 分帧与 EOF 分支</summary>

{{< source-reference id="source-1" >}}

</details>

Slime 测试最后先 `server.close()` / `await server.wait_closed()`，再 `await asyncio.gather(*tasks, return_exceptions=True)` 排空记录下来的处理任务。这需要客户端和 handler 配合结束连接；连接仍打开时 `wait_closed()` 也可能等待，handler 永远等不到协议输入时 gather 同样会一直等，实际服务需要自己的超时或取消策略。

<details><summary>展开固定源码：server 与 handlers 的两层收尾</summary>

{{< source-reference id="source-3" >}}

</details>

{{< python-async-coverage lesson="20-async-streams" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../19-signals-locks/) · [下一节：23 · 异步能力检查与协议边界](../21-async-inspection/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
