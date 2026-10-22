# shutdown_session：异步语义依据与局部验证

[返回函数卡片](../02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md) · [本轮讨论](../04-flow.md#shutdown-session-reading)

这里只保留主卡片所需的补充依据，不展开独立的 Python 异步课程。

## 书上怎么说

`Task.cancel` 通过让被控制的协程收到 `CancelledError` 来发起取消，书中用旋转指针协程说明这一点。[依据 A]

## 我的判断（本书未覆盖）

- 本轮术语索引和英文全文检索没有找到 `run_coroutine_threadsafe`、`wrap_future`、`asyncio.wait(` 的对应讲解；本函数的跨循环提交与等待流程依据本地 Python 3.12.3 实现和 Slime 源码，不归于书中结论。
- 当前 Python 的 `Task.cancel` 明确是请求取消：协程可以运行 `finally` 清理，也可能延迟或抑制取消。Slime 随后调用 `gather`，就是继续等待剩余 Task 结束；`wait_timeout` 没有限制这一段。[依据 B]
- `run_coroutine_threadsafe` 返回 `concurrent.futures.Future`；`wrap_future` 将其完成状态连接到调用方循环里的 `asyncio.Future`，使外层能够等待。Slime 用第一个请求 Task 的循环执行 `_drain`，没有将任意多个不同循环的 Task 分组处理。[依据 B、C]
- `except Exception` 记录的是收尾异常，不是成功标志；当前 Python 中 `asyncio.CancelledError` 属于 `BaseException`，调用方被取消的情况也不能当成已成功收尾。本轮没有对此进行故障实验。[依据 B、C]

## 依据

**A ·《Fluent Python》第 2 版，第 19 章，Spinner with Coroutines**

- 英文：`corpus/en/ch19.md:295–451`，锚点 `spinner-with-coroutines`。
- 中文：`corpus/zh/ch19.md:283–433`，同一锚点，19.4.3「使用协程实现旋转指针」。
- 版本：O'Reilly 2022，第 2 版，基于 Python 3.10；本轮验证环境为 Python 3.12.3。
- 本地镜像根目录：`/home/hongshi/.codex/plugins/cache/fluent-python-kb/fluent-python-kb/local/`。引用区间来自两侧章节映射，原句逐字核对。

原文：

> The `Task.cancel` method raises a `CancelledError` exception inside the `spin` coroutine, as we’ll see in Example 19-5.

对照：

> `Task.cancel` 方法在 `spin` 协程中抛出 `CancelledError` 异常，详见示例 19-5。

这里保留书中的机制概述；“请求取消后不一定立即结束”的精确边界按当前实现核对。

**B · 本地 CPython 3.12.3**

- `/usr/lib/python3.12/asyncio/tasks.py:210–228`：`Task.cancel` 的请求、清理及取消状态说明；运行时可能使用 C 实现，本轮同时以真实 Task 验证所用行为。
- 同文件 `435–465`：`wait` 默认 `ALL_COMPLETED`，返回 done、pending 两组；超时返回 pending，不自行取消。
- 同文件 `731` 起：`gather` 的 `return_exceptions` 与取消语义。
- 同文件 `931–951` 和 `/usr/lib/python3.12/asyncio/futures.py:409–419`：跨循环提交及 Future 包装。
- `/usr/lib/python3.12/asyncio/exceptions.py`：`CancelledError` 的 `BaseException` 基类。

**C · Slime 固定实现**

- 提交：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。
- [shutdown_session:225–243](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/adapters/common.py#L225-L243)：标记、取任务、定义收尾、选择循环和等待。
- [generate.py:161–170](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L161-L170) 与 [aiohttp_threaded.py:65–88](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/agent/aiohttp_threaded.py#L65-L88)：本场景的 Adapter 服务拥有专用线程和事件循环。

**D · 2026-10-22 针对本次复述的 API 核对**

- [Python 3.12：run_coroutine_threadsafe](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.run_coroutine_threadsafe)：将协程提交给指定循环，并返回 `concurrent.futures.Future`。Slime 提交的是完整的 `_drain()`，不是已经执行过的 cancel 结果。
- [Python 3.12：wrap_future](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.wrap_future)：将上述 Future 包装成 `asyncio.Future`，让调用方能 await 收尾结果；这次提交动作属于内层的 `run_coroutine_threadsafe`。
- [Python 3.12：wait](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.wait)：等待后返回 done、pending，超时本身不取消任务。Slime 随后明确取消 pending，再等待清理。
- 官网本次显示 Python 3.12.15 文档；本地核对环境仍为 Python 3.12.3。这里只对照上述 API 的职责，没有将文档版本写成新的运行环境。
- 重新查询本地书籍术语索引，并在中英全文中搜索 `run_coroutine_threadsafe`、`wrap_future`，均未找到对应讲解；相关结论仍归入“我的判断（本书未覆盖）”。A 中 `Task.cancel` 两侧原句及章节锚点再次核对通过，未添加新的书籍归因。
- [本次复述与校正](../04-flow.md#shutdown-restatement-after-split)区分个人表达和助手解释；本轮只做静态与文献核对，未新增 Task 执行实验。

## 2026-10-21 局部运行结果

从固定源码通过 AST 原样提取 `BaseAdapter.shutdown_session`，绑定到具有 `closed`、`inflight`、`store`、`manager` 和日志字段的本地对象。请求用构造的 `asyncio.Task` 替代；配置与轨迹树用对象标记验证身份保持。没有加载完整 Adapter、发送 HTTP 或运行模型。

| 输入情况 | 等待参数 | 实际结果 |
| --- | --- | --- |
| 任务集合为空 | `5.0` 秒 | 返回 `None`；留下关闭标记，移除该 sid 的 inflight 登记 |
| 集合中只有已完成 Task | `5.0` 秒 | 过滤掉已完成任务，直接返回；Task 未被取消 |
| 另一个线程循环中的 Task 约 0.01 秒后完成 | `5.0` 秒 | 实测约 0.0103 秒返回，Task 已完成、未取消，清理已执行 |
| 另一个线程循环中的 Task 持续等待；取消后的清理耗时约 0.03 秒 | `0.02` 秒 | 实测约 0.0505 秒返回，Task 已取消，清理已执行 |

四组都核对了返回值为 `None`、配置与轨迹标记仍在、另一会话登记保持。时间是一次运行的观察值，不是性能保证；最后一组说明总耗时会包含取消清理的时间。

验证范围是本地任务生命周期与跨循环等待，不证明真实远端生成已中止，也未覆盖停止的循环、拒绝取消的任务或收尾异常。临时复核脚本为 `/tmp/repo-reading-shutdown-check.py`，临时结构化输出为 `/tmp/repo-reading-shutdown-results.json`；本文件保留其条件与结果，不依赖临时文件长期存在。
