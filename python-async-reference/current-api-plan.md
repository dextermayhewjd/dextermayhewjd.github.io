# 当前要学的 Python 原生异步与并发 API

依据 [current-api-plan.json](current-api-plan.json) 与固定三库清单生成；重算命令见末尾。只处理 Python 原生异步与并发，测试、日志和业务框架不作为独立选题。完整课程安排及逐 API 单元映射见 [curriculum.md](curriculum.md)。

## 1. 结论与统计范围

原来的 53 项调用/方法清单已达到每库至少 70%，但漏列队列、通知、执行器退出等必要操作。当前补齐为 **82 项调用/方法**，另列异常类型和语言语法。该范围足以作为本轮学习清单；剩余机制在读到相应源码时再补。

| 仓库 | 原 53 项覆盖 / 全部相关调用 | 当前 82 项覆盖 / 全部相关调用 | 新覆盖位置 |
| --- | ---: | ---: | ---: |
| Slime | 174/229（76.0%） | 182/229（79.5%） | 8 |
| AReaL | 595/756（78.7%） | 632/756（83.6%） | 37 |
| verl | 279/377（74.0%） | 295/377（78.2%） | 16 |

Slime 与 verl 位于 70%–80% 区间，AReaL 为 83.6%，略高于目标；不为把比例压回 80% 而删掉必要方法。这里满足的是“至少 70%、大约 80%”的选题覆盖目标。

1. 分母沿用原统计：核心包中已识别的原生异步/并发及其配套标准库调用，含有类型线索的方法推断。测试、示例、导入、语法节点、单纯引用与未知类型候选不计入。
2. 分子以显式调用/方法名匹配 `report.json` 的 occurrence ID，与分母取交集并去重。类构造与各方法分开列出；继承方法沿用官方文档映射。
3. 这是静态调用位置覆盖，不是运行频率、实际场景覆盖率、全仓代码覆盖率或已经掌握的比例。三个框架的第三方 API 不在分母中。
4. 下表的零调用不表示不学：`async with` 的隐式获取/释放、装饰器引用等不算显式调用，必要配套仍列入。

## 2. 按概念依赖学习的完整调用/方法表

一行是概念组，不是一课；同组也按最小心智模型拆开。前三组中的 TaskGroup 先学正常退出，取消之后再回看失败路径。

| 学习内容 | 明确要学的调用/方法 | Slime | AReaL | verl | 官方页面 |
| --- | --- | ---: | ---: | ---: | --- |
| 协程入口与暂停 | `asyncio.run`、`asyncio.sleep` | 14 | 25 | 41 | [文档 1](https://docs.python.org/3.16/library/asyncio-runner.html)、[文档 2](https://docs.python.org/3.16/library/asyncio-task.html#sleeping) |
| 任务安排与结果集合 | `asyncio.create_task`、`asyncio.TaskGroup`、`asyncio.TaskGroup.create_task`、`asyncio.gather`、`asyncio.wait`、`asyncio.as_completed` | 28 | 112 | 75 | [文档 1](https://docs.python.org/3.16/library/asyncio-task.html) |
| Task/Future 状态与结果 | `asyncio.Task.done`、`asyncio.Task.result`、`asyncio.Task.exception`、`asyncio.Task.cancel`、`asyncio.Future.done`、`asyncio.Future.result`、`asyncio.Future.exception` | 6 | 7 | 7 | [文档 1](https://docs.python.org/3.16/library/asyncio-task.html#task-object)、[文档 2](https://docs.python.org/3.16/library/asyncio-future.html#future-object) |
| 超时与取消边界 | `asyncio.wait_for`、`asyncio.timeout`、`asyncio.shield`、`builtins.TimeoutError` | 13 | 42 | 10 | [文档 1](https://docs.python.org/3.16/library/asyncio-task.html#timeouts)、[文档 2](https://docs.python.org/3.16/library/asyncio-exceptions.html) |
| 协程限流、同步与队列 | `asyncio.Semaphore`、`asyncio.Semaphore.acquire`、`asyncio.Semaphore.release`、`asyncio.Queue`、`asyncio.Queue.put`、`asyncio.Queue.get`、`asyncio.Lock`、`asyncio.Lock.acquire`、`asyncio.Lock.release`、`asyncio.Event`、`asyncio.Event.set`、`asyncio.Event.wait`、`asyncio.Event.clear` | 4 | 23 | 15 | [文档 1](https://docs.python.org/3.16/library/asyncio-sync.html)、[文档 2](https://docs.python.org/3.16/library/asyncio-queue.html) |
| 线程池与执行器 Future | `asyncio.to_thread`、`concurrent.futures.ThreadPoolExecutor`、`concurrent.futures.Executor.submit`、`concurrent.futures.Executor.shutdown`、`concurrent.futures.Future.result`、`concurrent.futures.Future.done`、`concurrent.futures.Future.exception`、`concurrent.futures.Future.cancel` | 20 | 33 | 26 | [文档 1](https://docs.python.org/3.16/library/asyncio-task.html#running-in-threads)、[文档 2](https://docs.python.org/3.16/library/concurrent.futures.html) |
| 线程生命周期、同步与交接 | `threading.Thread`、`threading.Thread.start`、`threading.Thread.join`、`threading.Thread.is_alive`、`threading.Lock`、`threading.Lock.acquire`、`threading.Lock.release`、`threading.Event`、`threading.Event.set`、`threading.Event.wait`、`threading.Event.clear`、`queue.Queue`、`queue.Queue.put`、`queue.Queue.get`、`queue.Queue.get_nowait` | 34 | 135 | 12 | [文档 1](https://docs.python.org/3.16/library/threading.html)、[文档 2](https://docs.python.org/3.16/library/queue.html) |
| 任务上下文 | `contextvars.ContextVar`、`contextvars.ContextVar.get`、`contextvars.ContextVar.set`、`contextvars.ContextVar.reset` | 14 | 11 | 16 | [文档 1](https://docs.python.org/3.16/library/contextvars.html) |
| 异步资源、迭代与对象检查 | `contextlib.asynccontextmanager`、`contextlib.aclosing`、`inspect.isawaitable`、`inspect.iscoroutinefunction` | 2 | 5 | 12 | [文档 1](https://docs.python.org/3.16/library/contextlib.html)、[文档 2](https://docs.python.org/3.16/library/inspect.html) |
| 事件循环与线程交接 | `asyncio.get_running_loop`、`asyncio.AbstractEventLoop.run_in_executor`、`asyncio.wrap_future`、`asyncio.run_coroutine_threadsafe` | 21 | 28 | 26 | [文档 1](https://docs.python.org/3.16/library/asyncio-eventloop.html)、[文档 2](https://docs.python.org/3.16/library/asyncio-task.html#scheduling-from-other-threads)、[文档 3](https://docs.python.org/3.16/library/asyncio-future.html) |
| Python 子进程与外部命令 | `multiprocessing.Process`、`multiprocessing.Process.start`、`multiprocessing.Process.is_alive`、`multiprocessing.Process.join`、`multiprocessing.Process.terminate`、`multiprocessing.Process.kill`、`subprocess.run`、`subprocess.Popen`、`subprocess.Popen.communicate`、`subprocess.Popen.wait`、`subprocess.Popen.terminate`、`subprocess.Popen.kill` | 10 | 17 | 31 | [文档 1](https://docs.python.org/3.16/library/multiprocessing.html#process-and-exceptions)、[文档 2](https://docs.python.org/3.16/library/subprocess.html) |
| 阻塞等待与经过时间 | `time.sleep`、`time.monotonic`、`time.perf_counter` | 16 | 194 | 24 | [文档 1](https://docs.python.org/3.16/library/time.html) |

1. 82 项是完整写出的调用/方法名，不是 82 课。相同类的操作按最小概念组织。
2. run_coroutine_threadsafe、as_completed、shield 均有正式教学单元，按前置分期展开；完成全课时必须覆盖，具体单元见 curriculum.json。
3. Lock/Semaphore 的 acquire/release 用来解释 async with 或 with 的进入退出，不要求所有主例子手动配对调用。
4. CancelledError 等异常按类型和异常传播学习；只出现于 except 或注解的引用不计入调用覆盖。ExceptionGroup 此处只要求读取和捕获，不据此覆盖显式构造调用。

## 3. 语法和异常类型另列

语法：`async def`、`await`、`async with`、`async for`、`异步生成器中的 yield`、`try/finally`、`except*`。

异常类型：`asyncio.CancelledError`、`asyncio.InvalidStateError`、`concurrent.futures.CancelledError`、`concurrent.futures.TimeoutError`、`queue.Empty`、`queue.Full`、`subprocess.TimeoutExpired`、`builtins.ExceptionGroup`。

这些必须能辨认和处理，但不把 `await`、`except` 等位置塞进 API 调用分子。`TimeoutError(...)` 的构造已在前表明确列出；其他类型不因为会捕获就自动算作会构造。

<details>
<summary>逐 API 核对：调用位置数</summary>

| API | Slime | AReaL | verl |
| --- | ---: | ---: | ---: |
| `asyncio.run` | 1 | 3 | 8 |
| `asyncio.sleep` | 13 | 22 | 33 |
| `asyncio.create_task` | 9 | 9 | 13 |
| `asyncio.TaskGroup` | 0 | 1 | 0 |
| `asyncio.TaskGroup.create_task` | 0 | 1 | 0 |
| `asyncio.gather` | 13 | 100 | 57 |
| `asyncio.wait` | 5 | 1 | 5 |
| `asyncio.as_completed` | 1 | 0 | 0 |
| `asyncio.Task.done` | 2 | 2 | 0 |
| `asyncio.Task.result` | 3 | 0 | 1 |
| `asyncio.Task.exception` | 0 | 0 | 0 |
| `asyncio.Task.cancel` | 1 | 5 | 2 |
| `asyncio.Future.done` | 0 | 0 | 3 |
| `asyncio.Future.result` | 0 | 0 | 0 |
| `asyncio.Future.exception` | 0 | 0 | 1 |
| `asyncio.wait_for` | 2 | 9 | 3 |
| `asyncio.timeout` | 0 | 0 | 0 |
| `asyncio.shield` | 4 | 3 | 0 |
| `builtins.TimeoutError` | 7 | 30 | 7 |
| `asyncio.Semaphore` | 2 | 0 | 1 |
| `asyncio.Semaphore.acquire` | 0 | 0 | 0 |
| `asyncio.Semaphore.release` | 0 | 0 | 0 |
| `asyncio.Queue` | 1 | 1 | 3 |
| `asyncio.Queue.put` | 0 | 1 | 0 |
| `asyncio.Queue.get` | 0 | 1 | 0 |
| `asyncio.Lock` | 1 | 13 | 4 |
| `asyncio.Lock.acquire` | 0 | 0 | 0 |
| `asyncio.Lock.release` | 0 | 0 | 0 |
| `asyncio.Event` | 0 | 2 | 4 |
| `asyncio.Event.set` | 0 | 3 | 3 |
| `asyncio.Event.wait` | 0 | 1 | 0 |
| `asyncio.Event.clear` | 0 | 1 | 0 |
| `asyncio.to_thread` | 13 | 10 | 8 |
| `concurrent.futures.ThreadPoolExecutor` | 3 | 13 | 10 |
| `concurrent.futures.Executor.submit` | 1 | 3 | 7 |
| `concurrent.futures.Executor.shutdown` | 1 | 1 | 0 |
| `concurrent.futures.Future.result` | 2 | 5 | 1 |
| `concurrent.futures.Future.done` | 0 | 0 | 0 |
| `concurrent.futures.Future.exception` | 0 | 0 | 0 |
| `concurrent.futures.Future.cancel` | 0 | 1 | 0 |
| `threading.Thread` | 8 | 19 | 2 |
| `threading.Thread.start` | 8 | 17 | 2 |
| `threading.Thread.join` | 0 | 1 | 0 |
| `threading.Thread.is_alive` | 0 | 1 | 0 |
| `threading.Lock` | 4 | 59 | 4 |
| `threading.Lock.acquire` | 0 | 0 | 0 |
| `threading.Lock.release` | 0 | 0 | 0 |
| `threading.Event` | 5 | 18 | 2 |
| `threading.Event.set` | 3 | 4 | 1 |
| `threading.Event.wait` | 1 | 2 | 1 |
| `threading.Event.clear` | 0 | 0 | 0 |
| `queue.Queue` | 2 | 8 | 0 |
| `queue.Queue.put` | 2 | 3 | 0 |
| `queue.Queue.get` | 1 | 0 | 0 |
| `queue.Queue.get_nowait` | 0 | 3 | 0 |
| `contextvars.ContextVar` | 3 | 5 | 4 |
| `contextvars.ContextVar.get` | 5 | 3 | 4 |
| `contextvars.ContextVar.set` | 3 | 3 | 3 |
| `contextvars.ContextVar.reset` | 3 | 0 | 5 |
| `contextlib.asynccontextmanager` | 0 | 0 | 0 |
| `contextlib.aclosing` | 0 | 0 | 0 |
| `inspect.isawaitable` | 1 | 5 | 0 |
| `inspect.iscoroutinefunction` | 1 | 0 | 12 |
| `asyncio.get_running_loop` | 8 | 19 | 7 |
| `asyncio.AbstractEventLoop.run_in_executor` | 1 | 5 | 6 |
| `asyncio.wrap_future` | 5 | 2 | 12 |
| `asyncio.run_coroutine_threadsafe` | 7 | 2 | 1 |
| `multiprocessing.Process` | 2 | 0 | 5 |
| `multiprocessing.Process.start` | 2 | 0 | 5 |
| `multiprocessing.Process.is_alive` | 2 | 0 | 7 |
| `multiprocessing.Process.join` | 0 | 0 | 3 |
| `multiprocessing.Process.terminate` | 0 | 0 | 4 |
| `multiprocessing.Process.kill` | 0 | 0 | 1 |
| `subprocess.run` | 4 | 8 | 5 |
| `subprocess.Popen` | 0 | 9 | 1 |
| `subprocess.Popen.communicate` | 0 | 0 | 0 |
| `subprocess.Popen.wait` | 0 | 0 | 0 |
| `subprocess.Popen.terminate` | 0 | 0 | 0 |
| `subprocess.Popen.kill` | 0 | 0 | 0 |
| `time.sleep` | 10 | 69 | 13 |
| `time.monotonic` | 6 | 87 | 2 |
| `time.perf_counter` | 0 | 38 | 9 |

</details>

## 4. 未覆盖内容与后续边界

| 仓库 | 剩余位置 | 剩余调用最多的 8 项 |
| --- | ---: | --- |
| Slime | 47 | `os.getpid`（12）、`threading.RLock`（5）、`asyncio.AbstractEventLoop.time`（4）、`asyncio.AbstractEventLoop.create_future`（3）、`asyncio.AbstractEventLoop.run_until_complete`（2）、`asyncio.current_task`（2）、`asyncio.new_event_loop`（2）、`asyncio.set_event_loop`（2） |
| AReaL | 124 | `os.getpid`（12）、`signal.signal`（10）、`concurrent.futures.Future`（8）、`subprocess.check_output`（8）、`concurrent.futures.ThreadPoolExecutor.map`（7）、`asyncio.AbstractEventLoop.create_future`（5）、`fcntl.flock`（5）、`time.perf_counter_ns`（5） |
| verl | 82 | `signal.alarm`（17）、`os.getpid`（10）、`signal.setitimer`（4）、`signal.signal`（4）、`asyncio.Task.add_done_callback`（3）、`asyncio.new_event_loop`（3）、`asyncio.set_event_loop`（3）、`concurrent.futures.as_completed`（3） |

主要按需范围：手动事件循环生命周期、Condition/RLock、进程间队列、进程池、信号/进程组、文件锁与更低层 I/O。`os.getpid` 等辅助调用仍在原分母中，不为了增加分子单独开课。

当前 82 项是本轮原生基础清单，不声称列完标准库的每个 API。源码中遇到上述剩余机制时再展开；基础语法与方法的解释仍需包括结果、异常、取消和退出边界。

## 5. 固定来源与复算

- Slime：`22a89f96835969a47055a659c588f46151f8b07a`，[原始位置清单](repositories/slime/inventory.json)。
- AReaL：`298412a40f5b84ae6b2042987e81777e6dd0f284`，[原始位置清单](repositories/areal/inventory.json)。
- verl：`1d367a4f459a43768f76312c0d3430a99ec46b8c`，[原始位置清单](repositories/verl/inventory.json)。

```bash
python3 python-async-reference/tools/build_current_api_plan.py
python3 python-async-reference/tools/build_current_api_plan.py --check
```
