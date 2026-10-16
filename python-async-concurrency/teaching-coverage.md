# 源码用法与教程对照

固定源码：`2f2318653f6f794dddd321eff7c9d4b7b174643f`。

2288 条静态位置均有教程去向；518 个直接 API 位置和 747 个语法位置逐项映射。

对象方法的 inferred/candidate 标记保留原扫描器的证据强度，不能把有讲解入口等同于运行时类型证明。

| 讲解 | API / 实例方法 / 语法 | 源码位置数 |
| --- | --- | ---: |
| [定义协程函数与创建协程对象](/projects/python-async-concurrency/01-async-def/#coroutine-definition) | `async_def` | 281 |
| [运行顶层协程与事件循环入口](/projects/python-async-concurrency/01-async-def/#run-entry) | `asyncio`, `asyncio.run` | 112 |
| [沿当前调用链等待与恢复](/projects/python-async-concurrency/02-await/#await-execution) | `asyncio.sleep`, `await` | 442 |
| [阻塞线程与挂起任务的区别](/projects/python-async-concurrency/03-tasks/#sleep-key-point) | `time.sleep` | 57 |
| [创建任务与保留引用](/projects/python-async-concurrency/03-tasks/#task-creation) | `asyncio.create_task`, `asyncio.Task` | 24 |
| [收集整组结果与异常边界](/projects/python-async-concurrency/05-gather/#gather-results) | `asyncio.gather` | 27 |
| [等待条件与完成集合](/projects/python-async-concurrency/04-results/#wait-results) | `asyncio.wait`, `asyncio.FIRST_COMPLETED` | 8 |
| [按完成顺序消费结果](/projects/python-async-concurrency/08-as-completed/#as-completed-results) | `asyncio.as_completed` | 1 |
| [请求取消与等待清理](/projects/python-async-concurrency/09-task-cancellation/#task-cancellation) | `asyncio.CancelledError`, `asyncio.Task.cancel` | 16 |
| [wait_for 等待时限与超时报告](/projects/python-async-concurrency/10-wait-for/#wait-for) | `asyncio.wait_for`, `builtins.TimeoutError` | 9 |
| [经过时间与剩余预算](/projects/python-async-concurrency/11-time-budget/#elapsed-time) | `time.monotonic`, `time.perf_counter` | 0 |
| [多个等待共享超时预算](/projects/python-async-concurrency/12-timeout-scope/#shared-timeout) | `asyncio.timeout` | 2 |
| [取消等待者与内部工作的责任边界](/projects/python-async-concurrency/13-shield/#shield-cancellation) | `asyncio.shield` | 4 |
| [超时异常别名](/projects/python-async-concurrency/05-cancellation/#timeouts-and-shield) | `asyncio.TimeoutError` | 3 |
| [许可区域、限流与归还](/projects/python-async-concurrency/06-semaphore/#semaphore-permits) | `asyncio.Semaphore`, `asyncio.Semaphore.acquire`, `asyncio.Semaphore.release` | 11 |
| [异步队列的生产消费与背压](/projects/python-async-concurrency/07-queues/#async-queue) | `asyncio.Queue`, `asyncio.Queue.put`, `asyncio.Queue.get`, `asyncio.Queue.empty` | 4 |
| [同步队列与立刻尝试取结果](/projects/python-async-concurrency/07-queues/#thread-queue) | `queue.Queue`, `queue.Empty`, `queue.Queue.put`, `queue.Queue.get`, `queue.Queue.get_nowait`, `queue.Queue.qsize`, `queue.Queue.empty` | 15 |
| [把同步函数交给工作线程](/projects/python-async-concurrency/08-executors/#thread-offload) | `asyncio.to_thread` | 14 |
| [线程启动、互斥、通知与退出](/projects/python-async-concurrency/09-thread-synchronization/#thread-basics) | `threading.Thread`, `threading.Lock`, `threading.Event`, `threading.get_ident`, `threading.Thread.start`, `threading.Thread.join`, `threading.Thread.is_alive`, `threading.Lock.acquire`, `threading.Lock.release`, `threading.Event.wait`, `threading.Event.set`, `threading.Event.clear`, `threading.Event.is_set` | 120 |
| [异步进入、退出与资源回收](/projects/python-async-concurrency/21-async-contextmanager/#async-context) | `contextlib.asynccontextmanager`, `async_with` | 48 |
| [异步迭代与异步生成器](/projects/python-async-concurrency/22-async-iteration/#async-iteration) | `async_for`, `async_generator_def`, `async_yield` | 15 |
| [任务上下文与 token 恢复](/projects/python-async-concurrency/11-contextvars/#task-context) | `contextvars.ContextVar`, `contextvars.ContextVar.get`, `contextvars.ContextVar.set`, `contextvars.ContextVar.reset` | 18 |
| [进程池分配与收集工作](/projects/python-async-concurrency/12-processes/#process-intro) | `multiprocessing.Pool.starmap`, `multiprocessing.context.BaseContext.Pool` | 2 |
| [回到 Slime 的创建、交接与清理](/projects/python-async-concurrency/14-slime-walkthrough/#slime-lifecycle) | 源码类型与第三方边界 | 0 |
| [Event 的等待、通知、状态与清零](/projects/python-async-concurrency/20-async-event/#event-notification) | `asyncio.Event`, `asyncio.Event.wait`, `asyncio.Event.set`, `asyncio.Event.clear`, `asyncio.Event.is_set` | 35 |
| [asyncio.Lock 保护任务共享状态](/projects/python-async-concurrency/19-async-lock/#async-lock) | `asyncio.Lock`, `asyncio.Lock.acquire`, `asyncio.Lock.release`, `asyncio.Lock.locked` | 1 |
| [Condition 谓词循环、锁交接与通知](/projects/python-async-concurrency/16-thread-coordination/#condition-predicate) | `threading.Condition`, `threading.Condition.wait`, `threading.Condition.wait_for`, `threading.Condition.notify_all` | 24 |
| [同一线程重入 RLock](/projects/python-async-concurrency/16-thread-coordination/#rlock-reentrancy) | `threading.RLock`, `threading.RLock.acquire`, `threading.RLock.release` | 6 |
| [Timer 启动、取消与退出](/projects/python-async-concurrency/16-thread-coordination/#timer-lifecycle) | `threading.Timer`, `threading.Timer.start`, `threading.Timer.cancel`, `threading.Timer.join` | 3 |
| [线程池 submit 与 map 的结果组织](/projects/python-async-concurrency/17-executor-results/#executor-submit-map) | `concurrent.futures.ThreadPoolExecutor`, `concurrent.futures.ThreadPoolExecutor.submit`, `concurrent.futures.ThreadPoolExecutor.map`, `concurrent.futures.Executor.submit`, `concurrent.futures.Executor.map` | 39 |
| [同步 Future 的结果、异常与完成状态](/projects/python-async-concurrency/17-executor-results/#future-result-state) | `concurrent.futures.CancelledError`, `concurrent.futures.Future.result`, `concurrent.futures.Future.exception`, `concurrent.futures.Future.done` | 11 |
| [Future 取消边界与完成回调](/projects/python-async-concurrency/17-executor-results/#future-cancel-callback) | `concurrent.futures.Future.cancel`, `concurrent.futures.Future.cancelled`, `concurrent.futures.Future.running`, `concurrent.futures.Future.add_done_callback` | 0 |
| [同步 wait 与 FIRST_COMPLETED](/projects/python-async-concurrency/17-executor-results/#executor-wait-completed) | `concurrent.futures.wait`, `concurrent.futures.FIRST_COMPLETED` | 4 |
| [按完成次序消费线程池结果](/projects/python-async-concurrency/17-executor-results/#executor-as-completed) | `concurrent.futures.as_completed` | 4 |
| [线程池关闭与在途工作清理](/projects/python-async-concurrency/17-executor-results/#executor-shutdown) | `concurrent.futures.ThreadPoolExecutor.shutdown`, `concurrent.futures.Executor.shutdown` | 2 |
| [测试替身直接构造 Future 并设置结果](/projects/python-async-concurrency/17-executor-results/#future-test-double) | `concurrent.futures.Future`, `concurrent.futures.Future.set_result`, `concurrent.futures.Future.set_exception` | 5 |
| [创建进程、启动上下文与所有权](/projects/python-async-concurrency/18-process-lifecycle/#process-start) | `multiprocessing.Process`, `multiprocessing.get_context`, `multiprocessing.set_start_method`, `multiprocessing.active_children`, `multiprocessing.Process.start`, `multiprocessing.Process.is_alive`, `multiprocessing.context.BaseContext.Process`, `multiprocessing.context.BaseContext.Queue` | 20 |
| [跨进程生产消费与结束协议](/projects/python-async-concurrency/18-process-lifecycle/#process-queue) | `multiprocessing.Queue`, `queue.Empty`, `multiprocessing.Queue.put`, `multiprocessing.Queue.get`, `multiprocessing.Queue.empty`, `multiprocessing.Queue.qsize` | 3 |
| [等待、终止、回收与队列关闭](/projects/python-async-concurrency/18-process-lifecycle/#process-join) | `multiprocessing.Process.join`, `multiprocessing.Process.terminate`, `multiprocessing.Process.kill`, `multiprocessing.Process.close`, `multiprocessing.Queue.close`, `multiprocessing.Queue.join_thread` | 0 |
| [进程池分派与退出](/projects/python-async-concurrency/18-process-lifecycle/#process-pool) | `multiprocessing.Pool`, `multiprocessing.context.BaseContext.Pool`, `multiprocessing.Pool.starmap`, `multiprocessing.Pool.close`, `multiprocessing.Pool.terminate`, `multiprocessing.Pool.join`, `multiprocessing.Pool.__enter__`, `multiprocessing.Pool.__exit__` | 0 |
| [子进程通信、超时与回收](/projects/python-async-concurrency/18-process-lifecycle/#subprocess-communicate) | `subprocess.TimeoutExpired`, `subprocess`, `subprocess.Popen.poll`, `subprocess.Popen.wait`, `subprocess.Popen.kill`, `subprocess.Popen.terminate` | 37 |
| [捕获、合并与丢弃输出](/projects/python-async-concurrency/18-process-lifecycle/#subprocess-output) | `subprocess.PIPE`, `subprocess.STDOUT`, `subprocess.DEVNULL` | 16 |
| [同步命令检查与失败状态](/projects/python-async-concurrency/18-process-lifecycle/#subprocess-failure) | `subprocess.check_call`, `subprocess.check_output`, `subprocess.CalledProcessError` | 7 |
| [跨进程文件锁与目录所有权](/projects/python-async-concurrency/19-signals-locks/#lock-readiness) | `fcntl.flock`, `fcntl.LOCK_EX`, `fcntl.LOCK_NB`, `fcntl.LOCK_SH` | 9 |
| [管道可读等待与就绪协议](/projects/python-async-concurrency/19-signals-locks/#lock-readiness) | `select.select` | 2 |
| [进程退出与解锁](/projects/python-async-concurrency/19-signals-locks/#lock-release) | `fcntl.LOCK_UN` | 1 |
| [父子身份与定向信号](/projects/python-async-concurrency/19-signals-locks/#process-identity) | `os.getpid`, `os.getppid`, `os.kill` | 35 |
| [保存、安装与恢复信号处理器](/projects/python-async-concurrency/19-signals-locks/#signal-handlers) | `signal.signal`, `signal.getsignal`, `signal.SIGINT`, `signal.SIGTERM`, `signal.SIGHUP`, `signal.SIGKILL` | 14 |
| [进程组信号与清理范围](/projects/python-async-concurrency/19-signals-locks/#process-group) | `os.killpg`, `signal.SIG_IGN` | 2 |
| [同步工作闹钟与恢复边界](/projects/python-async-concurrency/19-signals-locks/#signal-alarm) | `signal.alarm`, `signal.SIGALRM` | 3 |
| [同步 shell 调用与退出状态](/projects/python-async-concurrency/19-signals-locks/#shell-boundary) | `os.system` | 4 |
| [Task、线程、进程和进程组的不同停止责任](/projects/python-async-concurrency/19-signals-locks/#cancellation-boundary) | 源码类型与第三方边界 | 0 |
| [Future：待完成结果与所属 loop](/projects/python-async-concurrency/13-event-loop/#future-basics) | `asyncio.Future`, `asyncio.InvalidStateError` | 0 |
| [Future 完成、取消与分批回调](/projects/python-async-concurrency/13-event-loop/#pacer-callbacks) | `asyncio.AbstractEventLoop.call_soon`, `asyncio.AbstractEventLoop.call_later`, `asyncio.Future.cancel`, `asyncio.Future.cancelled`, `asyncio.Future.add_done_callback` | 2 |
| [创建、登记、运行与跨线程提交](/projects/python-async-concurrency/13-event-loop/#event-loop-lifecycle) | `asyncio.AbstractEventLoop`, `concurrent.futures.Future.result` | 1 |
| [事件循环停止、executor 排空与关闭](/projects/python-async-concurrency/13-event-loop/#loop-shutdown) | `asyncio.AbstractEventLoop.is_running`, `asyncio.AbstractEventLoop.shutdown_default_executor` | 1 |
| [Task 的状态、返回值与异常](/projects/python-async-concurrency/07-task-results/#task-results) | `asyncio.Task.done`, `asyncio.Task.result`, `asyncio.Task.exception` | 7 |
| [Task 身份、归属与完成读取](/projects/python-async-concurrency/13-event-loop/#task-inspection) | `asyncio.current_task`, `asyncio.all_tasks`, `asyncio.Task`, `asyncio.Task.cancelled`, `asyncio.Task.get_loop` | 4 |
| [手动 loop 的异步生成器兜底清理](/projects/python-async-concurrency/13-event-loop/#lifecycle-lab) | `asyncio.AbstractEventLoop.shutdown_asyncgens` | 0 |
| [创建本地监听与流式连接](/projects/python-async-concurrency/20-async-streams/#start-server) | `asyncio.start_server`, `asyncio.open_connection`, `asyncio.Server`, `asyncio.StreamReader`, `asyncio.StreamWriter` | 1 |
| [流式读取与协议分帧](/projects/python-async-concurrency/20-async-streams/#stream-reader) | `asyncio.LimitOverrunError`, `asyncio.StreamReader.read`, `asyncio.StreamReader.readline`, `asyncio.StreamReader.readuntil`, `asyncio.StreamReader.readexactly` | 0 |
| [提前 EOF 的部分数据与期待长度](/projects/python-async-concurrency/20-async-streams/#incomplete-read) | `asyncio.IncompleteReadError` | 1 |
| [写入流量控制与连接关闭](/projects/python-async-concurrency/20-async-streams/#stream-writer) | `asyncio.StreamWriter.write`, `asyncio.StreamWriter.drain`, `asyncio.StreamWriter.close`, `asyncio.StreamWriter.wait_closed` | 0 |
| [监听器与连接任务的独立收尾](/projects/python-async-concurrency/20-async-streams/#server-lifecycle) | `asyncio.Server.is_serving`, `asyncio.Server.serve_forever`, `asyncio.Server.close`, `asyncio.Server.wait_closed` | 0 |
| [调用后检查返回对象能否 await](/projects/python-async-concurrency/25-inspect-awaitable/#isawaitable) | `inspect.isawaitable` | 3 |
| [装饰时判断协程函数并选择 wrapper](/projects/python-async-concurrency/25-inspect-awaitable/#iscoroutinefunction) | `inspect.iscoroutinefunction` | 1 |
| [Awaitable 和 AsyncIterator 注解契约](/projects/python-async-concurrency/21-async-inspection/#async-type-annotations) | `collections.abc.Awaitable`, `collections.abc.AsyncIterator` | 7 |
| [上下文与迭代的异步协议入口](/projects/python-async-concurrency/21-async-inspection/#async-protocol-methods) | `builtins.StopAsyncIteration`, `contextlib.AbstractAsyncContextManager.__aenter__`, `contextlib.AbstractAsyncContextManager.__aexit__`, `collections.abc.AsyncIterable.__aiter__`, `collections.abc.AsyncIterator.__anext__`, `async_protocol_def` | 0 |
| [提前退出异步生成器时显式关闭](/projects/python-async-concurrency/21-async-inspection/#async-generator-cleanup) | `contextlib.aclosing`, `collections.abc.AsyncGenerator.aclose` | 0 |
| [同名方法与原生接收者证据边界](/projects/python-async-concurrency/21-async-inspection/#object-method-boundaries) | `dict.get`, `str.join`, `queue.Queue.get`, `queue.Queue.join`, `asyncio.Queue.get`, `asyncio.Queue.join`, `threading.Thread.join` | 670 |
| [从协程提交到指定线程池并等待结果](/projects/python-async-concurrency/33-run-in-executor/#executor-await) | `asyncio.AbstractEventLoop.run_in_executor` | 1 |
| [用事件循环时钟计算剩余预算](/projects/python-async-concurrency/33-loop-time/#loop-time-budget) | `asyncio.AbstractEventLoop.time` | 0 |
| [取得正在使用的事件循环](/projects/python-async-concurrency/33-current-loop/#running-loop) | `asyncio.get_running_loop` | 10 |
| [将已有执行器 Future 接入协程等待](/projects/python-async-concurrency/34-wrap-future/#wrap-future) | `asyncio.wrap_future` | 5 |
| [运行外部程序并等待退出结果](/projects/python-async-concurrency/37-subprocess-run/#subprocess-run) | `subprocess.run` | 15 |
| [启动子进程后收集输出并等待退出](/projects/python-async-concurrency/38-popen-communicate/#popen-communicate) | `subprocess.Popen`, `subprocess.Popen.communicate` | 15 |
| [读取 asyncio Future 的状态、结果与异常](/projects/python-async-concurrency/35-future-results/#asyncio-future-results) | `asyncio.Future.done`, `asyncio.Future.result`, `asyncio.Future.exception` | 0 |
| [创建 asyncio Future 并写入结果或异常](/projects/python-async-concurrency/35-future-completion/#future-completion) | `asyncio.AbstractEventLoop.create_future`, `asyncio.Future.set_result`, `asyncio.Future.set_exception` | 5 |
| [Task 完成后调用函数处理结果](/projects/python-async-concurrency/35-task-callbacks/#task-done-callback) | `asyncio.Task.add_done_callback` | 1 |
| [创建、关联、运行和关闭事件循环](/projects/python-async-concurrency/36-manual-event-loop/#manual-event-loop) | `asyncio.new_event_loop`, `asyncio.set_event_loop`, `asyncio.AbstractEventLoop.run_until_complete`, `asyncio.AbstractEventLoop.close`, `asyncio.AbstractEventLoop.run_forever`, `asyncio.AbstractEventLoop.stop` | 8 |
| [从另一线程向循环提交协程或回调](/projects/python-async-concurrency/36-threadsafe-submit/#threadsafe-submit) | `asyncio.run_coroutine_threadsafe`, `asyncio.AbstractEventLoop.call_soon_threadsafe` | 10 |

## 原始记录

[完整映射 JSON](/python-async-concurrency/teaching-coverage.json) 保留每条 ID、源文件、行号、原代码行、源码链接与教程锚点。

另外 29 段 Markdown 中的代码保留完整原文与讲解去向，区别于实际 `.py` 文件。
