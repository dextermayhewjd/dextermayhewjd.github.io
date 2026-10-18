# 当前要学的 Python 原生异步与并发 API

依据 [current-api-plan.json](current-api-plan.json) 与四库固定清单生成。只处理 Python 原生异步与并发；课程安排及逐 API 单元映射见 [curriculum.md](curriculum.md)。

## 1. 结论与统计范围

当前清单为 **98 项调用/方法**：保留原 82 项，纳入 7 组共 12 项接口，以及 4 项必要配套操作。语法和异常类型另列。

**四库按调用量加权：1614/1899（85.0%）**；扩充前为 1528/1899（80.5%）。先把四库的调用位置数相加再相除，不取四个覆盖率的算术平均，也不按 API 种类数计算。

| 仓库 | 原 82 项覆盖 / 全部相关调用 | 当前 98 项覆盖 / 全部相关调用 | 新覆盖位置 |
| --- | ---: | ---: | ---: |
| verl | 295/377（78.2%） | 306/377（81.2%） | 11 |
| AReaL | 632/756（83.6%） | 662/756（87.6%） | 30 |
| Slime | 182/229（79.5%） | 201/229（87.8%） | 19 |
| Miles | 419/537（78.0%） | 445/537（82.9%） | 26 |

四库合计新增 86 个调用位置。70%–80% 是原先的选题目标，不是删去必要操作来维持的上限。

1. 分母沿用原统计：核心包中已识别的原生异步/并发及其配套标准库调用，含有类型线索的方法推断。测试、示例、导入、语法节点、单纯引用与未知类型候选不计入。
2. 分子以显式调用/方法名匹配 `report.json` 的 occurrence ID，与分母取交集并去重。类构造与各方法分开列出；继承方法沿用官方文档映射。
3. 这是静态调用位置覆盖，不是运行频率、实际场景覆盖率、全仓代码覆盖率或已经掌握的比例。四个框架的第三方 API 不在分母中。
4. 下表的零调用不表示不学：`async with` 的隐式获取/释放、装饰器引用等不算显式调用，必要配套仍列入。

## 2. 新增接口组与必要配套

按四库使用次数筛选范围，按概念依赖安排顺序；必要操作不因零调用而隐藏。这里是课程规划，不表示新增子课已经写完。

| 内容 | 新增接口 | verl | AReaL | Slime | Miles | 合计 | 占全部调用 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 创建和设置事件循环 | `asyncio.new_event_loop`、`asyncio.set_event_loop` | 6 | 7 | 4 | 4 | 21 | 1.11% |
| 管理多份异步资源与转移清理责任 | `contextlib.AsyncExitStack`、`contextlib.AsyncExitStack.enter_async_context`、`contextlib.AsyncExitStack.push_async_callback`、`contextlib.AsyncExitStack.aclose`、`contextlib.AsyncExitStack.pop_all` | 0 | 5 | 0 | 9 | 14 | 0.74% |
| 任务完成后的回调 | `asyncio.Task.add_done_callback` | 3 | 1 | 1 | 8 | 13 | 0.68% |
| 创建等待结果的 Future | `asyncio.AbstractEventLoop.create_future` | 0 | 5 | 3 | 1 | 9 | 0.47% |
| 在线程池中批量提交与取结果 | `concurrent.futures.Executor.map` | 0 | 7 | 0 | 2 | 9 | 0.47% |
| 读取循环的单调时钟 | `asyncio.AbstractEventLoop.time` | 0 | 2 | 4 | 2 | 8 | 0.42% |
| 同一线程嵌套加锁 | `threading.RLock` | 0 | 0 | 5 | 0 | 5 | 0.26% |
| 必要配套：运行、关闭循环与完成 Future | `asyncio.AbstractEventLoop.run_until_complete`、`asyncio.AbstractEventLoop.close`、`asyncio.Future.set_result`、`asyncio.Future.set_exception` | 2 | 3 | 2 | 0 | 7 | 0.37% |

7 组覆盖 79 个新增调用位置；4 项必要配套再覆盖 7 个，共新增 86 个。`AsyncExitStack.pop_all` 继承的接口说明位于 [ExitStack.pop_all](https://docs.python.org/3.16/library/contextlib.html#contextlib.ExitStack.pop_all)；从原始清单补回该映射，不改变原三库报告和四库调用总数。

## 3. 按概念依赖学习的完整调用/方法表

一行是概念组，不是一课；同组也按最小心智模型拆开。前三组中的 TaskGroup 先学正常退出，取消之后再回看失败路径。

| 学习内容 | 明确要学的调用/方法 | verl | AReaL | Slime | Miles | 官方页面 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 协程入口与暂停 | `asyncio.run`、`asyncio.sleep` | 41 | 25 | 14 | 40 | [文档 1](https://docs.python.org/3.16/library/asyncio-runner.html)、[文档 2](https://docs.python.org/3.16/library/asyncio-task.html#sleeping) |
| 任务安排与结果集合 | `asyncio.create_task`、`asyncio.TaskGroup`、`asyncio.TaskGroup.create_task`、`asyncio.gather`、`asyncio.wait`、`asyncio.as_completed` | 75 | 112 | 28 | 99 | [文档 1](https://docs.python.org/3.16/library/asyncio-task.html) |
| Task/Future 状态与结果 | `asyncio.Task.done`、`asyncio.Task.result`、`asyncio.Task.exception`、`asyncio.Task.cancel`、`asyncio.Future.done`、`asyncio.Future.result`、`asyncio.Future.exception`、`asyncio.Task.add_done_callback`、`asyncio.Future.set_result`、`asyncio.Future.set_exception` | 10 | 9 | 7 | 17 | [文档 1](https://docs.python.org/3.16/library/asyncio-task.html#task-object)、[文档 2](https://docs.python.org/3.16/library/asyncio-future.html#future-object) |
| 超时与取消边界 | `asyncio.wait_for`、`asyncio.timeout`、`asyncio.shield`、`builtins.TimeoutError` | 10 | 42 | 13 | 35 | [文档 1](https://docs.python.org/3.16/library/asyncio-task.html#timeouts)、[文档 2](https://docs.python.org/3.16/library/asyncio-exceptions.html) |
| 协程限流、同步与队列 | `asyncio.Semaphore`、`asyncio.Semaphore.acquire`、`asyncio.Semaphore.release`、`asyncio.Queue`、`asyncio.Queue.put`、`asyncio.Queue.get`、`asyncio.Lock`、`asyncio.Lock.acquire`、`asyncio.Lock.release`、`asyncio.Event`、`asyncio.Event.set`、`asyncio.Event.wait`、`asyncio.Event.clear` | 15 | 23 | 4 | 22 | [文档 1](https://docs.python.org/3.16/library/asyncio-sync.html)、[文档 2](https://docs.python.org/3.16/library/asyncio-queue.html) |
| 线程池与执行器 Future | `asyncio.to_thread`、`concurrent.futures.ThreadPoolExecutor`、`concurrent.futures.Executor.submit`、`concurrent.futures.Executor.shutdown`、`concurrent.futures.Future.result`、`concurrent.futures.Future.done`、`concurrent.futures.Future.exception`、`concurrent.futures.Future.cancel`、`concurrent.futures.Executor.map` | 26 | 40 | 20 | 15 | [文档 1](https://docs.python.org/3.16/library/asyncio-task.html#running-in-threads)、[文档 2](https://docs.python.org/3.16/library/concurrent.futures.html) |
| 线程生命周期、同步与交接 | `threading.Thread`、`threading.Thread.start`、`threading.Thread.join`、`threading.Thread.is_alive`、`threading.Lock`、`threading.Lock.acquire`、`threading.Lock.release`、`threading.RLock`、`threading.Event`、`threading.Event.set`、`threading.Event.wait`、`threading.Event.clear`、`queue.Queue`、`queue.Queue.put`、`queue.Queue.get`、`queue.Queue.get_nowait` | 12 | 135 | 39 | 63 | [文档 1](https://docs.python.org/3.16/library/threading.html)、[文档 2](https://docs.python.org/3.16/library/queue.html) |
| 任务上下文 | `contextvars.ContextVar`、`contextvars.ContextVar.get`、`contextvars.ContextVar.set`、`contextvars.ContextVar.reset` | 16 | 11 | 14 | 3 | [文档 1](https://docs.python.org/3.16/library/contextvars.html) |
| 异步资源、迭代与对象检查 | `contextlib.asynccontextmanager`、`contextlib.aclosing`、`inspect.isawaitable`、`inspect.iscoroutinefunction`、`contextlib.AsyncExitStack`、`contextlib.AsyncExitStack.enter_async_context`、`contextlib.AsyncExitStack.push_async_callback`、`contextlib.AsyncExitStack.aclose`、`contextlib.AsyncExitStack.pop_all` | 12 | 10 | 2 | 22 | [文档 1](https://docs.python.org/3.16/library/contextlib.html)、[文档 2](https://docs.python.org/3.16/library/inspect.html) |
| 事件循环与线程交接 | `asyncio.get_running_loop`、`asyncio.AbstractEventLoop.run_in_executor`、`asyncio.wrap_future`、`asyncio.run_coroutine_threadsafe`、`asyncio.new_event_loop`、`asyncio.set_event_loop`、`asyncio.AbstractEventLoop.run_until_complete`、`asyncio.AbstractEventLoop.close`、`asyncio.AbstractEventLoop.create_future`、`asyncio.AbstractEventLoop.time` | 34 | 44 | 34 | 21 | [文档 1](https://docs.python.org/3.16/library/asyncio-eventloop.html)、[文档 2](https://docs.python.org/3.16/library/asyncio-task.html#scheduling-from-other-threads)、[文档 3](https://docs.python.org/3.16/library/asyncio-future.html) |
| Python 子进程与外部命令 | `multiprocessing.Process`、`multiprocessing.Process.start`、`multiprocessing.Process.is_alive`、`multiprocessing.Process.join`、`multiprocessing.Process.terminate`、`multiprocessing.Process.kill`、`subprocess.run`、`subprocess.Popen`、`subprocess.Popen.communicate`、`subprocess.Popen.wait`、`subprocess.Popen.terminate`、`subprocess.Popen.kill` | 31 | 17 | 10 | 21 | [文档 1](https://docs.python.org/3.16/library/multiprocessing.html#process-and-exceptions)、[文档 2](https://docs.python.org/3.16/library/subprocess.html) |
| 阻塞等待与经过时间 | `time.sleep`、`time.monotonic`、`time.perf_counter` | 24 | 194 | 16 | 87 | [文档 1](https://docs.python.org/3.16/library/time.html) |

1. 98 项是完整写出的调用/方法名，不是 98 课。41 个主编号保留，新增关系使用子课逐步展开。
2. run_coroutine_threadsafe、as_completed、shield 均有正式教学单元，按前置分期展开；完成全课时必须覆盖，具体单元见 curriculum.json。
3. Lock/Semaphore 的 acquire/release 用来解释 async with 或 with 的进入退出，不要求所有主例子手动配对调用。
4. CancelledError 等异常按类型和异常传播学习；只出现于 except 或注解的引用不计入调用覆盖。ExceptionGroup 此处只要求读取和捕获，不据此覆盖显式构造调用。
5. 六组加权筛选新增 11 项，另加 run_until_complete、close、set_result、set_exception 四项必要配套；原 82 项范围保留为可复算基线。 另按 Slime 核心包 5 处构造补入 threading.RLock。
6. AsyncExitStack.pop_all 使用继承方法的真实名字，文档对应 ExitStack.pop_all；不因原报告缺少该映射而漏掉清理责任的转移。

## 4. 语法和异常类型另列

语法：`async def`、`await`、`async with`、`async for`、`异步生成器中的 yield`、`try/finally`、`except*`。

异常类型：`asyncio.CancelledError`、`asyncio.InvalidStateError`、`concurrent.futures.CancelledError`、`concurrent.futures.TimeoutError`、`queue.Empty`、`queue.Full`、`subprocess.TimeoutExpired`、`builtins.ExceptionGroup`。

这些必须能辨认和处理，但不把 `await`、`except` 等位置塞进 API 调用分子。`TimeoutError(...)` 的构造已在前表明确列出；其他类型不因为会捕获就自动算作会构造。

<details>
<summary>逐 API 核对：调用位置数</summary>

| API | verl | AReaL | Slime | Miles |
| --- | ---: | ---: | ---: | ---: |
| `asyncio.run` | 8 | 3 | 1 | 8 |
| `asyncio.sleep` | 33 | 22 | 13 | 32 |
| `asyncio.create_task` | 13 | 9 | 9 | 28 |
| `asyncio.TaskGroup` | 0 | 1 | 0 | 0 |
| `asyncio.TaskGroup.create_task` | 0 | 1 | 0 | 0 |
| `asyncio.gather` | 57 | 100 | 13 | 61 |
| `asyncio.wait` | 5 | 1 | 5 | 8 |
| `asyncio.as_completed` | 0 | 0 | 1 | 2 |
| `asyncio.Task.done` | 0 | 2 | 2 | 0 |
| `asyncio.Task.result` | 1 | 0 | 3 | 2 |
| `asyncio.Task.exception` | 0 | 0 | 0 | 3 |
| `asyncio.Task.cancel` | 2 | 5 | 1 | 4 |
| `asyncio.Future.done` | 3 | 0 | 0 | 0 |
| `asyncio.Future.result` | 0 | 0 | 0 | 0 |
| `asyncio.Future.exception` | 1 | 0 | 0 | 0 |
| `asyncio.Task.add_done_callback` | 3 | 1 | 1 | 8 |
| `asyncio.Future.set_result` | 0 | 1 | 0 | 0 |
| `asyncio.Future.set_exception` | 0 | 0 | 0 | 0 |
| `asyncio.wait_for` | 3 | 9 | 2 | 26 |
| `asyncio.timeout` | 0 | 0 | 0 | 0 |
| `asyncio.shield` | 0 | 3 | 4 | 0 |
| `builtins.TimeoutError` | 7 | 30 | 7 | 9 |
| `asyncio.Semaphore` | 1 | 0 | 2 | 2 |
| `asyncio.Semaphore.acquire` | 0 | 0 | 0 | 0 |
| `asyncio.Semaphore.release` | 0 | 0 | 0 | 0 |
| `asyncio.Queue` | 3 | 1 | 1 | 0 |
| `asyncio.Queue.put` | 0 | 1 | 0 | 0 |
| `asyncio.Queue.get` | 0 | 1 | 0 | 0 |
| `asyncio.Lock` | 4 | 13 | 1 | 5 |
| `asyncio.Lock.acquire` | 0 | 0 | 0 | 0 |
| `asyncio.Lock.release` | 0 | 0 | 0 | 0 |
| `asyncio.Event` | 4 | 2 | 0 | 10 |
| `asyncio.Event.set` | 3 | 3 | 0 | 2 |
| `asyncio.Event.wait` | 0 | 1 | 0 | 3 |
| `asyncio.Event.clear` | 0 | 1 | 0 | 0 |
| `asyncio.to_thread` | 8 | 10 | 13 | 7 |
| `concurrent.futures.ThreadPoolExecutor` | 10 | 13 | 3 | 5 |
| `concurrent.futures.Executor.submit` | 7 | 3 | 1 | 0 |
| `concurrent.futures.Executor.shutdown` | 0 | 1 | 1 | 0 |
| `concurrent.futures.Future.result` | 1 | 5 | 2 | 0 |
| `concurrent.futures.Future.done` | 0 | 0 | 0 | 0 |
| `concurrent.futures.Future.exception` | 0 | 0 | 0 | 1 |
| `concurrent.futures.Future.cancel` | 0 | 1 | 0 | 0 |
| `concurrent.futures.Executor.map` | 0 | 7 | 0 | 2 |
| `threading.Thread` | 2 | 19 | 8 | 20 |
| `threading.Thread.start` | 2 | 17 | 8 | 20 |
| `threading.Thread.join` | 0 | 1 | 0 | 1 |
| `threading.Thread.is_alive` | 0 | 1 | 0 | 1 |
| `threading.Lock` | 4 | 59 | 4 | 10 |
| `threading.Lock.acquire` | 0 | 0 | 0 | 0 |
| `threading.Lock.release` | 0 | 0 | 0 | 0 |
| `threading.RLock` | 0 | 0 | 5 | 0 |
| `threading.Event` | 2 | 18 | 5 | 6 |
| `threading.Event.set` | 1 | 4 | 3 | 1 |
| `threading.Event.wait` | 1 | 2 | 1 | 2 |
| `threading.Event.clear` | 0 | 0 | 0 | 0 |
| `queue.Queue` | 0 | 8 | 2 | 1 |
| `queue.Queue.put` | 0 | 3 | 2 | 1 |
| `queue.Queue.get` | 0 | 0 | 1 | 0 |
| `queue.Queue.get_nowait` | 0 | 3 | 0 | 0 |
| `contextvars.ContextVar` | 4 | 5 | 3 | 3 |
| `contextvars.ContextVar.get` | 4 | 3 | 5 | 0 |
| `contextvars.ContextVar.set` | 3 | 3 | 3 | 0 |
| `contextvars.ContextVar.reset` | 5 | 0 | 3 | 0 |
| `contextlib.asynccontextmanager` | 0 | 0 | 0 | 0 |
| `contextlib.aclosing` | 0 | 0 | 0 | 2 |
| `inspect.isawaitable` | 0 | 5 | 1 | 1 |
| `inspect.iscoroutinefunction` | 12 | 0 | 1 | 10 |
| `contextlib.AsyncExitStack` | 0 | 1 | 0 | 3 |
| `contextlib.AsyncExitStack.enter_async_context` | 0 | 0 | 0 | 2 |
| `contextlib.AsyncExitStack.push_async_callback` | 0 | 3 | 0 | 2 |
| `contextlib.AsyncExitStack.aclose` | 0 | 1 | 0 | 0 |
| `contextlib.AsyncExitStack.pop_all` | 0 | 0 | 0 | 2 |
| `asyncio.get_running_loop` | 7 | 19 | 8 | 8 |
| `asyncio.AbstractEventLoop.run_in_executor` | 6 | 5 | 1 | 1 |
| `asyncio.wrap_future` | 12 | 2 | 5 | 2 |
| `asyncio.run_coroutine_threadsafe` | 1 | 2 | 7 | 3 |
| `asyncio.new_event_loop` | 3 | 3 | 2 | 2 |
| `asyncio.set_event_loop` | 3 | 4 | 2 | 2 |
| `asyncio.AbstractEventLoop.run_until_complete` | 1 | 1 | 2 | 0 |
| `asyncio.AbstractEventLoop.close` | 1 | 1 | 0 | 0 |
| `asyncio.AbstractEventLoop.create_future` | 0 | 5 | 3 | 1 |
| `asyncio.AbstractEventLoop.time` | 0 | 2 | 4 | 2 |
| `multiprocessing.Process` | 5 | 0 | 2 | 0 |
| `multiprocessing.Process.start` | 5 | 0 | 2 | 0 |
| `multiprocessing.Process.is_alive` | 7 | 0 | 2 | 2 |
| `multiprocessing.Process.join` | 3 | 0 | 0 | 2 |
| `multiprocessing.Process.terminate` | 4 | 0 | 0 | 1 |
| `multiprocessing.Process.kill` | 1 | 0 | 0 | 1 |
| `subprocess.run` | 5 | 8 | 4 | 9 |
| `subprocess.Popen` | 1 | 9 | 0 | 2 |
| `subprocess.Popen.communicate` | 0 | 0 | 0 | 0 |
| `subprocess.Popen.wait` | 0 | 0 | 0 | 4 |
| `subprocess.Popen.terminate` | 0 | 0 | 0 | 0 |
| `subprocess.Popen.kill` | 0 | 0 | 0 | 0 |
| `time.sleep` | 13 | 69 | 10 | 18 |
| `time.monotonic` | 2 | 87 | 6 | 69 |
| `time.perf_counter` | 9 | 38 | 0 | 0 |

</details>

## 5. 未覆盖内容与后续边界

| 仓库 | 剩余位置 | 剩余调用最多的 8 项 |
| --- | ---: | --- |
| verl | 71 | `signal.alarm`（17）、`os.getpid`（10）、`signal.setitimer`（4）、`signal.signal`（4）、`concurrent.futures.as_completed`（3）、`multiprocessing.Queue.put`（3）、`multiprocessing.shared_memory.SharedMemory`（3）、`concurrent.futures.ProcessPoolExecutor`（2） |
| AReaL | 94 | `os.getpid`（12）、`signal.signal`（10）、`concurrent.futures.Future`（8）、`subprocess.check_output`（8）、`fcntl.flock`（5）、`time.perf_counter_ns`（5）、`asyncio.iscoroutinefunction`（4）、`concurrent.futures.Future.set_result`（4） |
| Slime | 28 | `os.getpid`（12）、`asyncio.current_task`（2）、`multiprocessing.active_children`（2）、`signal.alarm`（2）、`threading.Condition`（2）、`asyncio.AbstractEventLoop.call_later`（1）、`asyncio.AbstractEventLoop.call_soon`（1）、`asyncio.AbstractEventLoop.run_forever`（1） |
| Miles | 92 | `os.getpid`（22）、`os._exit`（16）、`signal.signal`（6）、`asyncio.Task.cancelled`（5）、`asyncio.current_task`（5）、`asyncio.ensure_future`（4）、`fcntl.flock`（3）、`os.getppid`（3） |

主要按需范围：Condition、进程间队列、进程池、信号/进程组、文件锁与更低层 I/O。RLock 已在 28.2 正式引入。`os.getpid` 等辅助调用仍在原分母中，不为了增加分子单独开课。

当前 98 项不声称列完标准库的每个 API。原 82 项范围保留在 [api-plan-82.json](api-plan-82.json)，原 53 项核算保留在 [learning-coverage.md](learning-coverage.md)。

## 6. 固定来源与复算

- verl：`1d367a4f459a43768f76312c0d3430a99ec46b8c`，[原始位置清单](repositories/verl/inventory.json)。
- AReaL：`298412a40f5b84ae6b2042987e81777e6dd0f284`，[原始位置清单](repositories/areal/inventory.json)。
- Slime：`22a89f96835969a47055a659c588f46151f8b07a`，[原始位置清单](repositories/slime/inventory.json)。
- Miles：`cf91d625b3074f480b31ddcfd6604298407899f3`，[原始位置清单](repositories/miles/inventory.json)。

```bash
python3 python-async-reference/tools/build_current_api_plan.py
python3 python-async-reference/tools/build_current_api_plan.py --check
```
