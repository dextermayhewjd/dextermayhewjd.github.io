# 静态出现次数统计

源码版本：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。

扫描全部 **381** 个 Git 跟踪 Python 文件，**90** 个文件含目标记录；解析错误 **0** 个。

计数单位是源码中的静态出现位置，不是执行次数。导入、直接调用、非调用引用、语法、实例候选五组分别计数。调用的函数表达式不再重复记为非调用引用。

[总览](README.md) · [全部文件](FILES.md) · [机器可读统计](summary.json)

## 按记录种类

| 种类 | 次数 |
| --- | ---: |
| import | 147 |
| async_def | 281 |
| async_generator_def | 7 |
| async_protocol_def | 0 |
| await | 409 |
| async_with | 42 |
| async_for | 1 |
| async_comprehension | 0 |
| async_yield | 7 |
| api_call | 433 |
| api_reference | 85 |
| instance_candidate | 876 |
| **全部记录** | **2288** |

`async def` 总数为 **288** = 普通协程函数 **281** + 异步生成器函数 **7**。`async_yield` 另记生成器内部的 yield 位置。

直接目标标准库 API 合计 **518** = 调用 **433** + 非调用引用 **85**，包含下表明确标出的邻接机制。**876** 条实例候选不并入此数。

## 按类别

| 类别（完整位置表） | 导入 | 调用 | 非调用引用 | 语法 | 候选 | 全部记录 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [syntax](usage-categories/syntax.md) | 0 | 0 | 0 | 747 | 0 | 747 |
| [asyncio](usage-categories/asyncio.md) | 39 | 246 | 28 | 0 | 0 | 313 |
| [threading](usage-categories/threading.md) | 23 | 46 | 2 | 0 | 0 | 71 |
| [queue](usage-categories/queue.md) | 2 | 2 | 3 | 0 | 0 | 7 |
| [executors](usage-categories/executors.md) | 13 | 20 | 3 | 0 | 0 | 36 |
| [multiprocessing](usage-categories/multiprocessing.md) | 6 | 10 | 1 | 0 | 0 | 17 |
| [subprocess](usage-categories/subprocess.md) | 15 | 27 | 27 | 0 | 0 | 69 |
| [signal](usage-categories/signal.md) | 4 | 6 | 7 | 0 | 0 | 17 |
| [contextvars](usage-categories/contextvars.md) | 2 | 3 | 2 | 0 | 0 | 7 |
| [contextlib-async](usage-categories/contextlib-async.md) | 3 | 0 | 3 | 0 | 0 | 6 |
| [inspect-async](usage-categories/inspect-async.md) | 2 | 2 | 0 | 0 | 0 | 4 |
| [async-builtins](usage-categories/async-builtins.md) | 0 | 0 | 0 | 0 | 0 | 0 |
| [async-typing](usage-categories/async-typing.md) | 3 | 0 | 4 | 0 | 0 | 7 |
| [time-sleep](usage-categories/time-sleep.md) | 23 | 35 | 0 | 0 | 0 | 58 |
| [os-process](usage-categories/os-process.md) | 9 | 32 | 0 | 0 | 0 | 41 |
| [fcntl](usage-categories/fcntl.md) | 2 | 3 | 5 | 0 | 0 | 10 |
| [select](usage-categories/select.md) | 1 | 1 | 0 | 0 | 0 | 2 |
| [coroutine-helpers](usage-categories/coroutine-helpers.md) | 0 | 0 | 0 | 0 | 0 | 0 |
| [candidates](usage-categories/candidates.md) | 0 | 0 | 0 | 0 | 876 | 876 |

## 按直接 API

只包含 `api_call` 与 `api_reference`；导入和实例候选不在此表。

| API | 类别 | 调用 | 非调用引用 | 合计 |
| --- | --- | ---: | ---: | ---: |
| asyncio | [asyncio](usage-categories/asyncio.md) | 0 | 1 | 1 |
| asyncio.AbstractEventLoop | [asyncio](usage-categories/asyncio.md) | 0 | 1 | 1 |
| asyncio.CancelledError | [asyncio](usage-categories/asyncio.md) | 0 | 11 | 11 |
| asyncio.Event | [asyncio](usage-categories/asyncio.md) | 18 | 0 | 18 |
| asyncio.FIRST_COMPLETED | [asyncio](usage-categories/asyncio.md) | 0 | 3 | 3 |
| asyncio.IncompleteReadError | [asyncio](usage-categories/asyncio.md) | 0 | 1 | 1 |
| asyncio.Lock | [asyncio](usage-categories/asyncio.md) | 1 | 0 | 1 |
| asyncio.Queue | [asyncio](usage-categories/asyncio.md) | 1 | 0 | 1 |
| asyncio.Semaphore | [asyncio](usage-categories/asyncio.md) | 10 | 1 | 11 |
| asyncio.Task | [asyncio](usage-categories/asyncio.md) | 0 | 3 | 3 |
| asyncio.TimeoutError | [asyncio](usage-categories/asyncio.md) | 0 | 3 | 3 |
| asyncio.all_tasks | [asyncio](usage-categories/asyncio.md) | 1 | 0 | 1 |
| asyncio.as_completed | [asyncio](usage-categories/asyncio.md) | 1 | 0 | 1 |
| asyncio.create_task | [asyncio](usage-categories/asyncio.md) | 21 | 0 | 21 |
| asyncio.current_task | [asyncio](usage-categories/asyncio.md) | 3 | 0 | 3 |
| asyncio.gather | [asyncio](usage-categories/asyncio.md) | 27 | 0 | 27 |
| asyncio.get_running_loop | [asyncio](usage-categories/asyncio.md) | 10 | 0 | 10 |
| asyncio.new_event_loop | [asyncio](usage-categories/asyncio.md) | 2 | 0 | 2 |
| asyncio.run | [asyncio](usage-categories/asyncio.md) | 71 | 1 | 72 |
| asyncio.run_coroutine_threadsafe | [asyncio](usage-categories/asyncio.md) | 9 | 0 | 9 |
| asyncio.set_event_loop | [asyncio](usage-categories/asyncio.md) | 2 | 0 | 2 |
| asyncio.shield | [asyncio](usage-categories/asyncio.md) | 4 | 0 | 4 |
| asyncio.sleep | [asyncio](usage-categories/asyncio.md) | 30 | 2 | 32 |
| asyncio.start_server | [asyncio](usage-categories/asyncio.md) | 1 | 0 | 1 |
| asyncio.timeout | [asyncio](usage-categories/asyncio.md) | 1 | 1 | 2 |
| asyncio.to_thread | [asyncio](usage-categories/asyncio.md) | 14 | 0 | 14 |
| asyncio.wait | [asyncio](usage-categories/asyncio.md) | 5 | 0 | 5 |
| asyncio.wait_for | [asyncio](usage-categories/asyncio.md) | 9 | 0 | 9 |
| asyncio.wrap_future | [asyncio](usage-categories/asyncio.md) | 5 | 0 | 5 |
| collections.abc.AsyncIterator | [async-typing](usage-categories/async-typing.md) | 0 | 1 | 1 |
| collections.abc.Awaitable | [async-typing](usage-categories/async-typing.md) | 0 | 3 | 3 |
| concurrent.futures.FIRST_COMPLETED | [executors](usage-categories/executors.md) | 0 | 1 | 1 |
| concurrent.futures.Future | [executors](usage-categories/executors.md) | 1 | 1 | 2 |
| concurrent.futures.ThreadPoolExecutor | [executors](usage-categories/executors.md) | 15 | 1 | 16 |
| concurrent.futures.as_completed | [executors](usage-categories/executors.md) | 3 | 0 | 3 |
| concurrent.futures.wait | [executors](usage-categories/executors.md) | 1 | 0 | 1 |
| contextlib.asynccontextmanager | [contextlib-async](usage-categories/contextlib-async.md) | 0 | 3 | 3 |
| contextvars.ContextVar | [contextvars](usage-categories/contextvars.md) | 3 | 2 | 5 |
| fcntl.LOCK_EX | [fcntl](usage-categories/fcntl.md) | 0 | 2 | 2 |
| fcntl.LOCK_NB | [fcntl](usage-categories/fcntl.md) | 0 | 2 | 2 |
| fcntl.LOCK_UN | [fcntl](usage-categories/fcntl.md) | 0 | 1 | 1 |
| fcntl.flock | [fcntl](usage-categories/fcntl.md) | 3 | 0 | 3 |
| inspect.isawaitable | [inspect-async](usage-categories/inspect-async.md) | 1 | 0 | 1 |
| inspect.iscoroutinefunction | [inspect-async](usage-categories/inspect-async.md) | 1 | 0 | 1 |
| multiprocessing.Process | [multiprocessing](usage-categories/multiprocessing.md) | 4 | 1 | 5 |
| multiprocessing.Queue | [multiprocessing](usage-categories/multiprocessing.md) | 2 | 0 | 2 |
| multiprocessing.active_children | [multiprocessing](usage-categories/multiprocessing.md) | 2 | 0 | 2 |
| multiprocessing.get_context | [multiprocessing](usage-categories/multiprocessing.md) | 1 | 0 | 1 |
| multiprocessing.set_start_method | [multiprocessing](usage-categories/multiprocessing.md) | 1 | 0 | 1 |
| os.getpid | [os-process](usage-categories/os-process.md) | 24 | 0 | 24 |
| os.getppid | [os-process](usage-categories/os-process.md) | 1 | 0 | 1 |
| os.kill | [os-process](usage-categories/os-process.md) | 1 | 0 | 1 |
| os.killpg | [os-process](usage-categories/os-process.md) | 2 | 0 | 2 |
| os.system | [os-process](usage-categories/os-process.md) | 4 | 0 | 4 |
| queue.Empty | [queue](usage-categories/queue.md) | 0 | 1 | 1 |
| queue.Queue | [queue](usage-categories/queue.md) | 2 | 2 | 4 |
| select.select | [select](usage-categories/select.md) | 1 | 0 | 1 |
| signal.SIGALRM | [signal](usage-categories/signal.md) | 0 | 1 | 1 |
| signal.SIGHUP | [signal](usage-categories/signal.md) | 0 | 1 | 1 |
| signal.SIGINT | [signal](usage-categories/signal.md) | 0 | 1 | 1 |
| signal.SIGKILL | [signal](usage-categories/signal.md) | 0 | 3 | 3 |
| signal.SIGTERM | [signal](usage-categories/signal.md) | 0 | 1 | 1 |
| signal.alarm | [signal](usage-categories/signal.md) | 2 | 0 | 2 |
| signal.getsignal | [signal](usage-categories/signal.md) | 1 | 0 | 1 |
| signal.signal | [signal](usage-categories/signal.md) | 3 | 0 | 3 |
| subprocess | [subprocess](usage-categories/subprocess.md) | 0 | 1 | 1 |
| subprocess.CalledProcessError | [subprocess](usage-categories/subprocess.md) | 0 | 4 | 4 |
| subprocess.DEVNULL | [subprocess](usage-categories/subprocess.md) | 0 | 2 | 2 |
| subprocess.PIPE | [subprocess](usage-categories/subprocess.md) | 0 | 10 | 10 |
| subprocess.Popen | [subprocess](usage-categories/subprocess.md) | 9 | 2 | 11 |
| subprocess.STDOUT | [subprocess](usage-categories/subprocess.md) | 0 | 4 | 4 |
| subprocess.TimeoutExpired | [subprocess](usage-categories/subprocess.md) | 0 | 4 | 4 |
| subprocess.check_call | [subprocess](usage-categories/subprocess.md) | 2 | 0 | 2 |
| subprocess.check_output | [subprocess](usage-categories/subprocess.md) | 1 | 0 | 1 |
| subprocess.run | [subprocess](usage-categories/subprocess.md) | 15 | 0 | 15 |
| threading.Condition | [threading](usage-categories/threading.md) | 4 | 0 | 4 |
| threading.Event | [threading](usage-categories/threading.md) | 12 | 0 | 12 |
| threading.Lock | [threading](usage-categories/threading.md) | 8 | 0 | 8 |
| threading.RLock | [threading](usage-categories/threading.md) | 6 | 0 | 6 |
| threading.Thread | [threading](usage-categories/threading.md) | 13 | 2 | 15 |
| threading.Timer | [threading](usage-categories/threading.md) | 1 | 0 | 1 |
| threading.get_ident | [threading](usage-categories/threading.md) | 2 | 0 | 2 |
| time.sleep | [time-sleep](usage-categories/time-sleep.md) | 35 | 0 | 35 |

## 实例候选：证据分组

以下仅是简单构造、已知工厂或注解给出的接收者线索，不等于运行时类型证明。未获得线索的方法也完整保留在候选表。

| 接收者线索 | 候选数 |
| --- | ---: |
| asyncio.AbstractEventLoop | 12 |
| asyncio.Event | 17 |
| asyncio.Future | 2 |
| asyncio.Queue | 3 |
| asyncio.Task | 13 |
| concurrent.futures.Future | 12 |
| concurrent.futures.ThreadPoolExecutor | 17 |
| contextvars.ContextVar | 11 |
| multiprocessing.Pool | 1 |
| multiprocessing.Process | 6 |
| multiprocessing.context.BaseContext | 1 |
| queue.Queue | 8 |
| subprocess.Popen | 21 |
| threading.Condition | 20 |
| threading.Event | 30 |
| threading.Lock | 2 |
| threading.Thread | 28 |
| threading.Timer | 2 |
| 未获得接收者线索 | 670 |
| **候选合计** | **876** |
