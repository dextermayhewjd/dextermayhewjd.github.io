# 按官方页面统计

**每格为：直接调用 / 有类型线索的方法调用 / 非调用引用。** 页面之间可能重叠，不可相加当成仓库总数。

API 数为 0 的目录、指南、语言规则或命令行工具页面不作使用率判断；Python AST 扫描也不统计 shell/notebook 中的工具命令。

## 1. 核心包（不含测试、示例）

| 官方页面 | 范围内 API 数 | slime | areal | verl |
| --- | ---: | --- | --- | --- |
| [asyncio — Asynchronous I/O — Python 3.16.0a1 documentation](topics/asyncio.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [High-level API Index — Python 3.16.0a1 documentation](topics/asyncio-api-index.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Developing with asyncio — Python 3.16.0a1 documentation](topics/asyncio-dev.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Event loop — Python 3.16.0a1 documentation](topics/asyncio-eventloop.md) | 79 | 12 / 14 / 1 | 27 / 16 / 11 | 14 / 9 / 4 |
| [Exceptions — Python 3.16.0a1 documentation](topics/asyncio-exceptions.md) | 9 | 0 / 0 / 9 | 0 / 0 / 13 | 0 / 0 / 9 |
| [Extending — Python 3.16.0a1 documentation](topics/asyncio-extending.md) | 6 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Futures — Python 3.16.0a1 documentation](topics/asyncio-future.md) | 14 | 5 / 0 / 0 | 4 / 1 / 10 | 13 / 5 / 1 |
| [Call graph introspection — Python 3.16.0a1 documentation](topics/asyncio-graph.md) | 5 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Low-level API Index — Python 3.16.0a1 documentation](topics/asyncio-llapi-index.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Platform Support — Python 3.16.0a1 documentation](topics/asyncio-platforms.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Transports and Protocols — Python 3.16.0a1 documentation](topics/asyncio-protocol.md) | 50 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Queues — Python 3.16.0a1 documentation](topics/asyncio-queue.md) | 17 | 1 / 0 / 0 | 1 / 6 / 2 | 3 / 0 / 0 |
| [Runners — Python 3.16.0a1 documentation](topics/asyncio-runner.md) | 5 | 1 / 0 / 0 | 3 / 0 / 1 | 8 / 0 / 1 |
| [Streams — Python 3.16.0a1 documentation](topics/asyncio-stream.md) | 23 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Subprocesses — Python 3.16.0a1 documentation](topics/asyncio-subprocess.md) | 16 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Synchronization Primitives — Python 3.16.0a1 documentation](topics/asyncio-sync.md) | 30 | 3 / 0 / 0 | 15 / 6 / 5 | 10 / 3 / 1 |
| [Coroutines and tasks — Python 3.16.0a1 documentation](topics/asyncio-task.md) | 42 | 69 / 7 / 6 | 157 / 9 / 3 | 120 / 7 / 11 |
| [asyncio and free-threaded Python — Python 3.16.0a1 documentation](topics/asyncio-threading.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Command-line introspection tools — Python 3.16.0a1 documentation](topics/asyncio-tools.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [asyncio-policy](topics/asyncio-policy.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [A conceptual overview of asyncio — Python 3.16.0a1 documentation](topics/howto-a-conceptual-overview-of-asyncio.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [8. Compound statements — Python 3.16.0a1 documentation](topics/reference-compound_stmts.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [3. Data model — Python 3.16.0a1 documentation](topics/reference-datamodel.md) | 8 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [6. Expressions — Python 3.16.0a1 documentation](topics/reference-expressions.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [_thread — Low-level threading API — Python 3.16.0a1 documentation](topics/_thread.md) | 13 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Built-in Exceptions — Python 3.16.0a1 documentation](topics/builtins-exceptions.md) | 12 | 7 / 0 / 1 | 32 / 0 / 46 | 7 / 0 / 9 |
| [Built-in functions — Python 3.16.0a1 documentation](topics/builtins-functions.md) | 2 | 0 / 0 / 0 | 0 / 0 / 0 | 1 / 0 / 0 |
| [collections.abc — Abstract Base Classes for Containers — Python 3.16.0a1 documentation](topics/collections.abc.md) | 5 | 0 / 0 / 2 | 0 / 0 / 25 | 0 / 0 / 0 |
| [concurrent.futures — Launching parallel tasks — Python 3.16.0a1 documentation](topics/concurrent.futures.md) | 32 | 3 / 4 / 2 | 26 / 23 / 50 | 15 / 8 / 2 |
| [contextlib — Utilities for with-statement contexts — Python 3.16.0a1 documentation](topics/contextlib.md) | 9 | 0 / 0 / 0 | 1 / 4 / 17 | 0 / 0 / 2 |
| [contextvars — Context Variables — Python 3.16.0a1 documentation](topics/contextvars.md) | 17 | 3 / 11 / 2 | 5 / 6 / 7 | 4 / 12 / 4 |
| [fcntl — The fcntl and ioctl system calls — Python 3.16.0a1 documentation](topics/fcntl.md) | 6 | 1 / 0 / 2 | 5 / 0 / 6 | 0 / 0 / 0 |
| [inspect — Inspect live objects — Python 3.16.0a1 documentation](topics/inspect.md) | 13 | 2 / 0 / 0 | 5 / 0 / 0 | 13 / 0 / 1 |
| [multiprocessing — Process-based parallelism — Python 3.16.0a1 documentation](topics/multiprocessing.md) | 141 | 5 / 4 / 1 | 0 / 0 / 0 | 10 / 26 / 3 |
| [multiprocessing.shared_memory — Shared memory for direct access across processes — Python 3.16.0a1 documentation](topics/multiprocessing.shared_memory.md) | 14 | 0 / 0 / 0 | 0 / 0 / 0 | 3 / 0 / 0 |
| [os — Miscellaneous operating system interfaces — Python 3.16.0a1 documentation](topics/os.md) | 43 | 13 / 0 / 0 | 18 / 0 / 0 | 14 / 0 / 5 |
| [queue — A synchronized queue class — Python 3.16.0a1 documentation](topics/queue.md) | 23 | 2 / 3 / 3 | 8 / 6 / 12 | 0 / 0 / 1 |
| [select — Waiting for I/O completion — Python 3.16.0a1 documentation](topics/select.md) | 38 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [selectors — High-level I/O multiplexing — Python 3.16.0a1 documentation](topics/selectors.md) | 24 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [signal — Set handlers for asynchronous events — Python 3.16.0a1 documentation](topics/signal.md) | 57 | 3 / 0 / 1 | 12 / 0 / 18 | 27 / 0 / 15 |
| [subprocess — Subprocess management — Python 3.16.0a1 documentation](topics/subprocess.md) | 68 | 4 / 0 / 3 | 26 / 0 / 39 | 6 / 0 / 9 |
| [threading — Thread-based parallelism — Python 3.16.0a1 documentation](topics/threading.md) | 68 | 24 / 12 / 2 | 105 / 25 / 13 | 11 / 4 / 6 |
| [time — Time access and conversions — Python 3.16.0a1 documentation](topics/time.md) | 5 | 16 / 0 / 0 | 200 / 0 / 1 | 24 / 0 / 0 |
| [types — Dynamic type creation and names for built-in types — Python 3.16.0a1 documentation](topics/types.md) | 3 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [typing — Support for type hints — Python 3.16.0a1 documentation](topics/typing.md) | 6 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 12 |
| [unittest — Unit testing framework — Python 3.16.0a1 documentation](topics/unittest.md) | 7 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [unittest.mock — mock object library — Python 3.16.0a1 documentation](topics/unittest.mock.md) | 12 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

## 2. 全部已跟踪 Python 文件（含测试、示例）

| 官方页面 | 范围内 API 数 | slime | areal | verl |
| --- | ---: | --- | --- | --- |
| [asyncio — Asynchronous I/O — Python 3.16.0a1 documentation](topics/asyncio.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [High-level API Index — Python 3.16.0a1 documentation](topics/asyncio-api-index.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Developing with asyncio — Python 3.16.0a1 documentation](topics/asyncio-dev.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Event loop — Python 3.16.0a1 documentation](topics/asyncio-eventloop.md) | 79 | 14 / 17 / 1 | 52 / 41 / 11 | 22 / 17 / 4 |
| [Exceptions — Python 3.16.0a1 documentation](topics/asyncio-exceptions.md) | 9 | 0 / 0 / 15 | 2 / 0 / 44 | 1 / 0 / 9 |
| [Extending — Python 3.16.0a1 documentation](topics/asyncio-extending.md) | 6 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Futures — Python 3.16.0a1 documentation](topics/asyncio-future.md) | 14 | 5 / 0 / 0 | 4 / 1 / 10 | 13 / 5 / 1 |
| [Call graph introspection — Python 3.16.0a1 documentation](topics/asyncio-graph.md) | 5 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Low-level API Index — Python 3.16.0a1 documentation](topics/asyncio-llapi-index.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Platform Support — Python 3.16.0a1 documentation](topics/asyncio-platforms.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Transports and Protocols — Python 3.16.0a1 documentation](topics/asyncio-protocol.md) | 50 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Queues — Python 3.16.0a1 documentation](topics/asyncio-queue.md) | 17 | 1 / 0 / 0 | 2 / 6 / 2 | 3 / 0 / 0 |
| [Runners — Python 3.16.0a1 documentation](topics/asyncio-runner.md) | 5 | 71 / 0 / 1 | 81 / 0 / 1 | 66 / 0 / 1 |
| [Streams — Python 3.16.0a1 documentation](topics/asyncio-stream.md) | 23 | 1 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Subprocesses — Python 3.16.0a1 documentation](topics/asyncio-subprocess.md) | 16 | 0 / 0 / 0 | 2 / 6 / 4 | 0 / 0 / 0 |
| [Synchronization Primitives — Python 3.16.0a1 documentation](topics/asyncio-sync.md) | 30 | 29 / 17 / 1 | 50 / 29 / 9 | 13 / 6 / 1 |
| [Coroutines and tasks — Python 3.16.0a1 documentation](topics/asyncio-task.md) | 42 | 125 / 12 / 9 | 369 / 35 / 6 | 160 / 10 / 13 |
| [asyncio and free-threaded Python — Python 3.16.0a1 documentation](topics/asyncio-threading.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Command-line introspection tools — Python 3.16.0a1 documentation](topics/asyncio-tools.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [asyncio-policy](topics/asyncio-policy.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [A conceptual overview of asyncio — Python 3.16.0a1 documentation](topics/howto-a-conceptual-overview-of-asyncio.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [8. Compound statements — Python 3.16.0a1 documentation](topics/reference-compound_stmts.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [3. Data model — Python 3.16.0a1 documentation](topics/reference-datamodel.md) | 8 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [6. Expressions — Python 3.16.0a1 documentation](topics/reference-expressions.md) | 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [_thread — Low-level threading API — Python 3.16.0a1 documentation](topics/_thread.md) | 13 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [Built-in Exceptions — Python 3.16.0a1 documentation](topics/builtins-exceptions.md) | 12 | 19 / 0 / 6 | 41 / 0 / 75 | 7 / 0 / 15 |
| [Built-in functions — Python 3.16.0a1 documentation](topics/builtins-functions.md) | 2 | 0 / 0 / 0 | 2 / 0 / 0 | 1 / 0 / 0 |
| [collections.abc — Abstract Base Classes for Containers — Python 3.16.0a1 documentation](topics/collections.abc.md) | 5 | 0 / 0 / 4 | 0 / 0 / 26 | 0 / 0 / 0 |
| [concurrent.futures — Launching parallel tasks — Python 3.16.0a1 documentation](topics/concurrent.futures.md) | 32 | 21 / 30 / 4 | 36 / 38 / 53 | 18 / 11 / 2 |
| [contextlib — Utilities for with-statement contexts — Python 3.16.0a1 documentation](topics/contextlib.md) | 9 | 0 / 0 / 3 | 2 / 5 / 19 | 0 / 0 / 2 |
| [contextvars — Context Variables — Python 3.16.0a1 documentation](topics/contextvars.md) | 17 | 3 / 11 / 2 | 8 / 6 / 10 | 4 / 12 / 4 |
| [fcntl — The fcntl and ioctl system calls — Python 3.16.0a1 documentation](topics/fcntl.md) | 6 | 3 / 0 / 5 | 5 / 0 / 6 | 0 / 0 / 0 |
| [inspect — Inspect live objects — Python 3.16.0a1 documentation](topics/inspect.md) | 13 | 2 / 0 / 0 | 5 / 0 / 0 | 13 / 0 / 1 |
| [multiprocessing — Process-based parallelism — Python 3.16.0a1 documentation](topics/multiprocessing.md) | 141 | 10 / 8 / 1 | 1 / 6 / 0 | 16 / 43 / 3 |
| [multiprocessing.shared_memory — Shared memory for direct access across processes — Python 3.16.0a1 documentation](topics/multiprocessing.shared_memory.md) | 14 | 0 / 0 / 0 | 0 / 0 / 0 | 4 / 0 / 0 |
| [os — Miscellaneous operating system interfaces — Python 3.16.0a1 documentation](topics/os.md) | 43 | 32 / 0 / 0 | 28 / 0 / 0 | 20 / 0 / 5 |
| [queue — A synchronized queue class — Python 3.16.0a1 documentation](topics/queue.md) | 23 | 2 / 3 / 3 | 9 / 6 / 14 | 0 / 0 / 1 |
| [select — Waiting for I/O completion — Python 3.16.0a1 documentation](topics/select.md) | 38 | 1 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [selectors — High-level I/O multiplexing — Python 3.16.0a1 documentation](topics/selectors.md) | 24 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [signal — Set handlers for asynchronous events — Python 3.16.0a1 documentation](topics/signal.md) | 57 | 6 / 0 / 7 | 14 / 0 / 33 | 27 / 0 / 15 |
| [subprocess — Subprocess management — Python 3.16.0a1 documentation](topics/subprocess.md) | 68 | 29 / 19 / 28 | 106 / 35 / 94 | 25 / 2 / 17 |
| [threading — Thread-based parallelism — Python 3.16.0a1 documentation](topics/threading.md) | 68 | 50 / 28 / 2 | 168 / 96 / 18 | 15 / 13 / 9 |
| [time — Time access and conversions — Python 3.16.0a1 documentation](topics/time.md) | 5 | 73 / 0 / 0 | 295 / 0 / 3 | 60 / 0 / 0 |
| [types — Dynamic type creation and names for built-in types — Python 3.16.0a1 documentation](topics/types.md) | 3 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| [typing — Support for type hints — Python 3.16.0a1 documentation](topics/typing.md) | 6 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 12 |
| [unittest — Unit testing framework — Python 3.16.0a1 documentation](topics/unittest.md) | 7 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 3 |
| [unittest.mock — mock object library — Python 3.16.0a1 documentation](topics/unittest.mock.md) | 12 | 0 / 0 / 0 | 193 / 22 / 103 | 28 / 0 / 5 |
