# select — Waiting for I/O completion — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/select.html
- 抓取状态：ok
- 纳入理由：OS readiness polling is a low-level event-loop dependency.
- 范围：full_page

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`select.PIPE_BUF`](https://docs.python.org/3.16/library/select.html#select.PIPE_BUF) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.devpoll`](https://docs.python.org/3.16/library/select.html#select.devpoll) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.devpoll.close`](https://docs.python.org/3.16/library/select.html#select.devpoll.close) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.devpoll.closed`](https://docs.python.org/3.16/library/select.html#select.devpoll.closed) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.devpoll.fileno`](https://docs.python.org/3.16/library/select.html#select.devpoll.fileno) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.devpoll.modify`](https://docs.python.org/3.16/library/select.html#select.devpoll.modify) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.devpoll.poll`](https://docs.python.org/3.16/library/select.html#select.devpoll.poll) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.devpoll.register`](https://docs.python.org/3.16/library/select.html#select.devpoll.register) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.devpoll.unregister`](https://docs.python.org/3.16/library/select.html#select.devpoll.unregister) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.epoll`](https://docs.python.org/3.16/library/select.html#select.epoll) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.epoll.close`](https://docs.python.org/3.16/library/select.html#select.epoll.close) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.epoll.closed`](https://docs.python.org/3.16/library/select.html#select.epoll.closed) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.epoll.fileno`](https://docs.python.org/3.16/library/select.html#select.epoll.fileno) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.epoll.fromfd`](https://docs.python.org/3.16/library/select.html#select.epoll.fromfd) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.epoll.modify`](https://docs.python.org/3.16/library/select.html#select.epoll.modify) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.epoll.poll`](https://docs.python.org/3.16/library/select.html#select.epoll.poll) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.epoll.register`](https://docs.python.org/3.16/library/select.html#select.epoll.register) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.epoll.unregister`](https://docs.python.org/3.16/library/select.html#select.epoll.unregister) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.error`](https://docs.python.org/3.16/library/select.html#select.error) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kevent`](https://docs.python.org/3.16/library/select.html#select.kevent) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kevent.data`](https://docs.python.org/3.16/library/select.html#select.kevent.data) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kevent.fflags`](https://docs.python.org/3.16/library/select.html#select.kevent.fflags) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kevent.filter`](https://docs.python.org/3.16/library/select.html#select.kevent.filter) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kevent.flags`](https://docs.python.org/3.16/library/select.html#select.kevent.flags) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kevent.ident`](https://docs.python.org/3.16/library/select.html#select.kevent.ident) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kevent.udata`](https://docs.python.org/3.16/library/select.html#select.kevent.udata) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kqueue`](https://docs.python.org/3.16/library/select.html#select.kqueue) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kqueue.close`](https://docs.python.org/3.16/library/select.html#select.kqueue.close) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kqueue.closed`](https://docs.python.org/3.16/library/select.html#select.kqueue.closed) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kqueue.control`](https://docs.python.org/3.16/library/select.html#select.kqueue.control) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kqueue.fileno`](https://docs.python.org/3.16/library/select.html#select.kqueue.fileno) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.kqueue.fromfd`](https://docs.python.org/3.16/library/select.html#select.kqueue.fromfd) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.poll`](https://docs.python.org/3.16/library/select.html#select.poll) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.poll.modify`](https://docs.python.org/3.16/library/select.html#select.poll.modify) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.poll.poll`](https://docs.python.org/3.16/library/select.html#select.poll.poll) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.poll.register`](https://docs.python.org/3.16/library/select.html#select.poll.register) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.poll.unregister`](https://docs.python.org/3.16/library/select.html#select.poll.unregister) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`select.select`](https://docs.python.org/3.16/library/select.html#select.select) | 1 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
| slime / tests | `select.select` | api_call | [tests/test_rollout_straw_transport.py:1445](../repositories/slime/source_snapshot/tests/test_rollout_straw_transport.py.txt) · [固定版本](https://github.com/THUDM/slime/blob/22a89f96835969a47055a659c588f46151f8b07a/tests/test_rollout_straw_transport.py#L1445) |         assert select.select([process.stdout], [], [], 60)[0], "Controller did not start" |
