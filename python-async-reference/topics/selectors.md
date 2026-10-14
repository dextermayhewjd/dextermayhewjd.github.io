# selectors — High-level I/O multiplexing — Python 3.16.0a1 documentation

- 官方页面：https://docs.python.org/3.16/library/selectors.html
- 抓取状态：ok
- 纳入理由：High-level I/O readiness multiplexing underlies selector event loops.
- 范围：full_page

[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)

## 1. 条目与调用位置数

**每格为：直接调用 / 推断方法 / 非调用引用。**

| API / 协议条目 | slime | areal | verl |
| --- | --- | --- | --- |
| [`selectors.BaseSelector`](https://docs.python.org/3.16/library/selectors.html#selectors.BaseSelector) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.BaseSelector.close`](https://docs.python.org/3.16/library/selectors.html#selectors.BaseSelector.close) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.BaseSelector.get_key`](https://docs.python.org/3.16/library/selectors.html#selectors.BaseSelector.get_key) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.BaseSelector.get_map`](https://docs.python.org/3.16/library/selectors.html#selectors.BaseSelector.get_map) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.BaseSelector.modify`](https://docs.python.org/3.16/library/selectors.html#selectors.BaseSelector.modify) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.BaseSelector.register`](https://docs.python.org/3.16/library/selectors.html#selectors.BaseSelector.register) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.BaseSelector.select`](https://docs.python.org/3.16/library/selectors.html#selectors.BaseSelector.select) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.BaseSelector.unregister`](https://docs.python.org/3.16/library/selectors.html#selectors.BaseSelector.unregister) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.DefaultSelector`](https://docs.python.org/3.16/library/selectors.html#selectors.DefaultSelector) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.DevpollSelector`](https://docs.python.org/3.16/library/selectors.html#selectors.DevpollSelector) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.DevpollSelector.fileno`](https://docs.python.org/3.16/library/selectors.html#selectors.DevpollSelector.fileno) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.EVENT_READ`](https://docs.python.org/3.16/library/selectors.html#selectors.EVENT_READ) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.EVENT_WRITE`](https://docs.python.org/3.16/library/selectors.html#selectors.EVENT_WRITE) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.EpollSelector`](https://docs.python.org/3.16/library/selectors.html#selectors.EpollSelector) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.EpollSelector.fileno`](https://docs.python.org/3.16/library/selectors.html#selectors.EpollSelector.fileno) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.KqueueSelector`](https://docs.python.org/3.16/library/selectors.html#selectors.KqueueSelector) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.KqueueSelector.fileno`](https://docs.python.org/3.16/library/selectors.html#selectors.KqueueSelector.fileno) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.PollSelector`](https://docs.python.org/3.16/library/selectors.html#selectors.PollSelector) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.SelectSelector`](https://docs.python.org/3.16/library/selectors.html#selectors.SelectSelector) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.SelectorKey`](https://docs.python.org/3.16/library/selectors.html#selectors.SelectorKey) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.SelectorKey.data`](https://docs.python.org/3.16/library/selectors.html#selectors.SelectorKey.data) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.SelectorKey.events`](https://docs.python.org/3.16/library/selectors.html#selectors.SelectorKey.events) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.SelectorKey.fd`](https://docs.python.org/3.16/library/selectors.html#selectors.SelectorKey.fd) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [`selectors.SelectorKey.fileobj`](https://docs.python.org/3.16/library/selectors.html#selectors.SelectorKey.fileobj) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 本地源码位置

| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |
| --- | --- | --- | --- | --- |
