# 按需参考：返回函数、登记回调与非阻塞领取

本页只支撑当前源码中的三处语义，不开启独立 Python 课程。主读仍是 [Step 013 scope](../01-scope.md)。

## 书上怎么说

外层函数可以返回内层函数对象；书中 make_averager 返回 averager，得到函数后还要另行调用它。[依据 A]

## 我的判断（本书未覆盖的 Slime 场景）

- 在 Slime 中，对应的两层是 _make_done_cb 与 _cb。外层执行 return _cb，把函数交出；它不等价于执行 _cb(done_task)。该函数以后仍可使用外层的 self、gid、retry_group，完整闭包内部结构本步不展开。
- 完成调度的具体 API 依据是本机 Python 3.12 标准库参考实现 [asyncio/futures.py:222](/usr/lib/python3.12/asyncio/futures.py:222)：add_done_callback 登记函数，调用时传入 Future/Task 本身；已结束时也经 call_soon 调度。此 API 说明不是把 Slime 行为归给书中的例子。
- [queue.py:193](/usr/lib/python3.12/queue.py:193)的 get_nowait 移出并返回一个立即可用的元素，没有元素时抛出 Empty。Slime 捕获该异常后结束本次领取。

## 依据

A　《Fluent Python》第 2 版，第 9 章《装饰器和闭包》› Closures。

- 英文：[corpus/en/ch09.md:356](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/en/ch09.md:356)，小节范围 356–476，锚点 closures。
- 中文：[corpus/zh/ch09.md:341](/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/corpus/zh/ch09.md:341)，小节范围 341–461，9.6 闭包，锚点 closures。
- 版本：本书基于 Python 3.10；本次记录环境 Python 3.12.3。本页不涉及后续版本新增 API。
- 原文：When invoked, `make_averager` returns an `averager` function object.
- 对照：调用 `make_averager`，返回一个 `averager` 函数对象。

小节锚点与区间由插件 anchors.py 的两侧 map 核对，引用逐字匹配区间。以上参考不表示已运行真实 Slime worker。
