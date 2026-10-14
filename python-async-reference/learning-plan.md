# Python 异步与并发学习范围和顺序

记录日期：2026-10-13。

本专题只学习 **Python 原生异步与并发**：相关语言语法、asyncio、线程、执行器、进程、同步机制，以及它们的等待、结果、异常和退出行为。Slime、AReaL、verl 的用法用于筛选内容与提供源码对照；岗位说明用于解释学习动机，不扩展本专题的范围。Python 官方文档用于确定语义。本文是学习范围与顺序的维护入口；网页调整见第 5 节。

## 1. 用户确定的筛选原则

1. 找出三个仓库都使用到的异步或并发内容。
2. 优先学习其中使用频率高的内容。
3. 为每项内容找到对应的 Python 官方网页和具体小节。
4. 用表格列出学习内容、官方网页和 API。
5. 根据表格中的知识依赖安排学习先后顺序。

当前确定的安排原则是：**先限定 Python 原生异步与并发，按概念依赖决定学习顺序，用三库调用次数辅助决定详略和例子。** 不把 API 总次数的降序直接当成课程顺序；低频接口也可能承担必要的概念衔接与清理责任。

范围限于与异步、并发直接相关的 Python 语法和标准库。通用测试、日志、监控、框架架构、训练流程、Kubernetes 和第三方调度 API 不作为本专题的独立学习模块。验证示例只服务于当前原生机制，不借机展开另一门工程化课程。

2026-10-13 的前一轮目标是把三个仓库各自的计划静态调用位置覆盖提高到约 **70%–80%**，第 4.2 节保留这次 53 项 API 清单的核算。用户随后明确以岗位要求中的“扎实的 Python、Asyncio、并发处理和工程化最佳实践”为目标：覆盖比例继续用来检查遗漏，**不再用达到比例代替能力验收，也不为保持比例而删掉必要内容**。

用户最新澄清：**这一块仍然只考虑 Python 原生并发与异步**。岗位背景不扩大范围；通用工程实践仅在验证某个原生行为必需时辅助使用。

### 1.1 岗位是动机，原生机制是学习边界

岗位原始需求与整仓阅读对应关系见 [目标需求对照](../slime_photo/code-reading/job-alignment.md)。本专题只承担“熟悉异步编程（Asyncio）、并发处理”这一部分，不承担整个岗位或一般软件工程训练。

1. **可解释**：分清协程、Task、Future、线程和进程；能预测执行、等待、结果与异常的传播。
2. **可使用**：能在最小例子中正确创建、等待、协调与结束协程、线程和进程。
3. **可判断**：能区分结果、异常、取消、超时和资源关闭，知道各原语改变了哪种行为。
4. **可验证**：通过运行例子与必要断言核对上述行为；验证工具本身不另设必学路线。

函数、对象、异常、生成器、上下文管理器、装饰器和类型注解仅在解释异步/并发机制时补充必要前置，不扩展为完整 Python 语法课程。

## 2. 本轮统计口径

1. 以三个仓库核心包为主，排除测试、示例、单纯导入和类型不明的方法候选。次数表示静态源码位置，不是运行频率。
2. API 次数为直接调用与有接收者类型线索的方法调用之和；后者仍是静态推断。语法次数按核心包中的 AST 节点统计，不与 API 调用相加。
3. 此前用“每个仓库至少 3 处”筛出共同高频接口，作为下面第 3 节索引的参考。这是可调整的工作口径，不是用户指定的固定阈值，也不能据此排除必要前置或低频衔接接口。
4. `asyncio.run` 作为运行练习的必要入口保留。线程池的 `submit`、`Future.result` 和事件循环的 `run_in_executor` 是较低频的衔接接口，表中单独列数。
5. 频次用于筛选范围；表格顺序按学习依赖排列。表格的一行是一组知识，不要求在一页中一次讲完。例如第 1 行仍应拆成“创建协程并运行”与“在协程内部 await”。

数据入口：[核心包 API 矩阵](CORE-API-USAGE.md)、[统计规则](METHOD.md)、[官方文档目录](OFFICIAL-DOCS.md)、[机器汇总](report.json)。语法的核心包计数从下表所列 `inventory.json` 中按 `scope=core` 筛选；[SYNTAX-USAGE.md](SYNTAX-USAGE.md) 则包含全部扫描文件，两者范围不同。

当前具体要学的调用与方法以 [82 项 API 清单与核算](current-api-plan.md) 为准，机器清单为 [current-api-plan.json](current-api-plan.json)。补齐了原 53 项中遗漏的队列操作、通知、执行器退出、异步协议辅助和子进程操作。静态调用覆盖为 Slime **182/229（79.5%）**、AReaL **632/756（83.6%）**、verl **295/377（78.2%）**。AReaL 略高于目标区间，保留必要操作，不为压低比例删去它们。第 4.2 节的 53 项清单保留为历史基线，不再当成完整的当前 API 表。

| 仓库 | 核心包 | 固定源码版本与逐条记录 |
| --- | --- | --- |
| Slime | `slime/` | [`22a89f96835969a47055a659c588f46151f8b07a`](repositories/slime/inventory.json) |
| AReaL | `areal/` | [`298412a40f5b84ae6b2042987e81777e6dd0f284`](repositories/areal/inventory.json) |
| verl | `verl/` | [`1d367a4f459a43768f76312c0d3430a99ec46b8c`](repositories/verl/inventory.json) |

## 3. 高频 API 与官方页面索引

次数依次为 **Slime / AReaL / verl**。这里保留此前筛选的高频接口及官网入口，索引号不代表章节顺序；当前按概念展开的路线见第 4 节。

| 索引 | 要学习的内容 | 具体语法或 API | 三库次数 | 对应 Python 官方网页 |
| --- | --- | --- | --- | --- |
| 1 | 协程的创建、运行与内部等待 | `async def`、`await`、`asyncio.run()` | `async def`：105 / 546 / 316；`await`：192 / 798 / 566；`run`：1 / 3 / 8 | [Coroutines 与 Awaitables](https://docs.python.org/3.16/library/asyncio-task.html#coroutines)、[运行异步程序](https://docs.python.org/3.16/library/asyncio-runner.html#running-an-asyncio-program) |
| 2 | 暂停协程与阻塞线程的区别 | `asyncio.sleep()`、`time.sleep()` | 13 / 22 / 33；10 / 69 / 13 | [Sleeping](https://docs.python.org/3.16/library/asyncio-task.html#sleeping)、[time.sleep](https://docs.python.org/3.16/library/time.html#time.sleep) |
| 3 | 把协程安排成任务 | `asyncio.create_task()` | 9 / 9 / 13 | [Creating tasks](https://docs.python.org/3.16/library/asyncio-task.html#creating-tasks) |
| 4 | 等待多个任务并收集结果 | `asyncio.gather()` | 13 / 100 / 57 | [Running tasks concurrently](https://docs.python.org/3.16/library/asyncio-task.html#running-tasks-concurrently) |
| 5 | 异步作用域的进入与退出 | `async with` | 13 / 188 / 37 | [The async with statement](https://docs.python.org/3.16/reference/compound_stmts.html#the-async-with-statement) |
| 6 | 把阻塞函数交给工作线程 | `asyncio.to_thread()` | 13 / 10 / 8 | [Running in threads](https://docs.python.org/3.16/library/asyncio-task.html#running-in-threads) |
| 7 | 使用明确的线程池 | `ThreadPoolExecutor`；随后接上 `submit()`、`Future.result()` | 线程池构造：3 / 13 / 10；`submit`：1 / 3 / 7；`result`：2 / 5 / 1 | [ThreadPoolExecutor](https://docs.python.org/3.16/library/concurrent.futures.html#threadpoolexecutor)、[Executor](https://docs.python.org/3.16/library/concurrent.futures.html#executor-objects)、[Future](https://docs.python.org/3.16/library/concurrent.futures.html#future-objects) |
| 8 | 保护线程共享状态 | `threading.Lock()` | 4 / 59 / 4 | [Lock objects](https://docs.python.org/3.16/library/threading.html#lock-objects) |
| 9 | 协程怎样取得事件循环、交给线程池执行 | `asyncio.get_running_loop()`、`loop.run_in_executor()` | 8 / 19 / 7；1 / 5 / 6 | [获取事件循环](https://docs.python.org/3.16/library/asyncio-eventloop.html#asyncio.get_running_loop)、[在线程池或进程池执行](https://docs.python.org/3.16/library/asyncio-eventloop.html#executing-code-in-thread-or-process-pools) |
| 10 | 保存各个任务自己的上下文 | `ContextVar`、`.get()`、`.set()` | 构造：3 / 5 / 4；`get`：5 / 3 / 4；`set`：3 / 3 / 3 | [Context Variables](https://docs.python.org/3.16/library/contextvars.html#context-variables) |
| 11 | 启动并等待外部程序 | `subprocess.run()` | 4 / 8 / 5 | [Using the subprocess module](https://docs.python.org/3.16/library/subprocess.html#using-the-subprocess-module) |

## 4. 按概念展开的路线与调用次数

前五课继续建立协程、await、Task、TaskGroup 和 gather 的理解。gather 之后，按下表的概念依赖继续展开，而不是按调用次数跳到另一个主题。每个概念组仍拆成最小学习单元，不要求一课讲完组内所有接口。

下表是核心包静态调用位置数，方法包含有接收者类型线索的推断；不含单纯导入、非调用引用和类型不明的候选。

| 概念阶段 | 新增的问题 | 相关 API | Slime | AReaL | verl |
| --- | --- | --- | ---: | ---: | ---: |
| 1. 等待部分任务完成 | gather 等整组结束；能否先取得完成情况？ | `asyncio.wait` | 5 | 1 | 5 |
| 同上 | 能否逐个处理完成的结果？ | `asyncio.as_completed` | 1 | 0 | 0 |
| 2. 取消与超时 | 不想继续等了，怎样请求停止？ | `Task.cancel` | 1 | 5 | 2 |
| 同上 | 最多等待一段时间，怎样处理？ | `asyncio.wait_for` | 2 | 9 | 3 |
| 同上 | 外层取消时，是否保留内部工作？ | `asyncio.shield` | 4 | 3 | 0 |
| 3. 协调异步任务 | 同时允许多少份工作进入？ | `asyncio.Semaphore` | 2 | 0 | 1 |
| 同上 | 多份任务怎样交接数据？ | `asyncio.Queue` | 1 | 1 | 3 |
| 同上 | 怎样保护跨 await 的共享状态？ | `asyncio.Lock` | 1 | 13 | 4 |
| 同上 | 怎样通知任务继续执行？ | `asyncio.Event` | 0 | 2 | 4 |
| 4. 接入阻塞工作 | 同步函数会阻塞事件循环，怎么办？ | `asyncio.to_thread` | 13 | 10 | 8 |
| 同上 | 怎样使用明确的线程池？ | `ThreadPoolExecutor` | 3 | 13 | 10 |
| 同上 | 怎样从协程提交到指定执行器？ | `loop.run_in_executor` | 1 | 5 | 6 |
| 5. 协调工作线程 | 多线程怎样保护共享状态？ | `threading.Lock` | 4 | 59 | 4 |
| 同上 | 怎样创建工作线程？ | `threading.Thread` | 8 | 19 | 2 |
| 同上 | 怎样通知线程？ | `threading.Event` | 5 | 18 | 2 |
| 6. 保存任务上下文 | 并发任务怎样各自保存请求信息？ | `ContextVar` | 3 | 5 | 4 |
| 7. 补齐底层交接 | 怎样取得当前循环？ | `get_running_loop` | 8 | 19 | 7 |
| 同上 | 怎样衔接执行器 Future？ | `asyncio.wrap_future` | 5 | 2 | 12 |
| 8. 外部进程 | 怎样运行并等待外部程序？ | `subprocess.run` | 4 | 8 | 5 |

`CancelledError` 主要作为异常类型被引用，核心包引用位置为 **8 / 10 / 1**，没有混入调用次数。表中的 0 表示本次扫描未命中，不能据此推断整个框架不存在相应机制。

### 4.1 用次数决定详略

1. **gather → wait → 取消与超时**：从等全部，到等部分，再到停止等待并收尾，概念连续。`wait`、取消、`wait_for` 的调用次数不算高，仍可用简短的独立单元完成衔接；`as_completed` 后置选读。
2. **异步任务协调**：限流、数据交接、共享状态、通知各自展开。`Queue`、`asyncio.Lock` 是共同用法；岗位目标明确后，`Semaphore` 与 `asyncio.Event` 也进入必学，理由是并发预算、积压和通知的工程责任，不能伪称它们都是三库共同高频接口。
3. **阻塞工作 → 线程池 → 线程同步**：三库共同用法更多，增加例子和练习；仍先建立前置概念，再进入高频的线程锁。
4. `async with`、`async for` 等语法位置与 API 调用分开统计。已有 TaskGroup 单元先提供最小作用域模型；资源管理、异步迭代在对应任务中继续展开。

`run_coroutine_threadsafe` 的共同调用位置为 **7 / 2 / 1**，在底层交接阶段按需补充；`time.monotonic` 为 **6 / 87 / 2**，随经过时间和截止时间的问题一起解释。

`TaskGroup`、`asyncio.Semaphore`、`asyncio.as_completed` 和 `asyncio.Event` 尚未满足本次核心包的三库共同使用条件。用户随后明确要求将 TaskGroup 作为独立的 04，用最小作用域模型衔接 create_task；岗位目标又要求补齐并发预算与通知。选题变化不改变上述共同高频统计，当前深度以第 4.3 节为准。`os.getpid` 虽有共同高频调用，但主要用于取得进程标识，随进程相关代码查阅即可，暂不单设学习单元。

### 4.2 阶段性核算：补齐到三库各约 70%–80%

本节核算的是前一轮明确列出的 53 项 API，保留作为可复算基线；第 4.3 节的岗位必学范围还包括验证、诊断等内容，不受这张白名单限制。

**Slime 的主要差距在于：原估算清单列了对象，却没有列全使用对象的操作。** 例如列了 `threading.Thread`，却未算入 `.start()`；列了 `ContextVar.get/set`，却遗漏 `.reset()`。此外，`subprocess.run()` 没有覆盖另起 Python 进程运行服务的 `multiprocessing.Process`。

原清单在 Slime 的 asyncio 子集已覆盖 **87/112（77.7%）**，但加入线程、进程等相关标准库调用后为 **141/229（61.6%）**。因此接下来主要补齐操作与生命周期，不继续堆叠任务调度 API。

按概念位置加入以下五组内容。次数表示相对原清单**新增覆盖的调用位置**，不是运行频率；一组可以拆成数个最小单元，不等于新增五个大章节。

| 放在什么位置 | 最小新增问题 | 明确补入的操作 | Slime | AReaL | verl |
| --- | --- | --- | ---: | ---: | ---: |
| 等待部分任务之后；Future 部分随后对应补齐 | 如何判断完成、取出结果或异常？ | `Task/Future.done()`、`.result()`、`.exception()` | 5 | 2 | 5 |
| 取消与超时 | 超时后怎样报告失败、交给调用方处理？ | `TimeoutError`，连同抛出、捕获和清理边界 | 7 | 30 | 7 |
| 线程创建与协调 | 创建线程后怎样启动、通知并等待退出？ | `Thread.start/join/is_alive`；`threading.Event.set/wait/clear` | 12 | 25 | 4 |
| 任务上下文 | 临时设置的上下文怎样恢复？ | `ContextVar.reset(token)`，配合 `try/finally` | 3 | 0 | 5 |
| 外部程序之后，另起 Python 子进程运行服务 | 怎样启动、检查存活、终止并回收？ | `multiprocessing.Process`；`.start/is_alive/join/terminate/kill` | 6 | 0 | 25 |

其中 `Task/Future` 指 `asyncio` 对象。`.result()` 和 `.exception()` 不负责等待完成；未完成时会报错，取消与失败也要分别说明。线程的 `Event` 与 `asyncio.Event` 分开讲。进程部分先比较一次性执行外部程序与管理长期运行的 Python 子进程，再拆开正常退出与失败回收。

| 仓库 | 原清单 | 补充后 | 新增位置 |
| --- | ---: | ---: | ---: |
| Slime | 141/229（61.6%） | **174/229（76.0%）** | 33 |
| AReaL | 538/756（71.2%） | **595/756（78.7%）** | 57 |
| verl | 233/377（61.8%） | **279/377（74.0%）** | 46 |

1. **保持概念顺序**：任务结果 → 超时 → 异步协调 → 阻塞工作与线程 → 上下文 → Future/循环交接 → 外部程序与子进程。不要为凑比例改变依赖顺序。
2. **先补现有主题，再决定拆课**：这五组主要补齐现有结果、超时、线程、上下文和进程主题。01–05 不因此增加内容；某个主题有多个新关系时再拆成最小单元。
3. **保留按需范围**：Slime 尚有手动事件循环、`RLock/Condition`、同步队列和信号；verl 的信号超时、AReaL 的执行器与进程配套也需在实际读到时回查。不为了数字单独讲 `os.getpid`。
4. **区分计划与效果**：以上只表示显式 API 清单能对应多少已识别标准库调用位置，不证明已完成学习，也不等于覆盖了 70%–80% 的实际训练场景。Ray、HTTP 客户端、分布式通信与业务协调不在这个分母中。

完整 API 白名单、官方小节、固定源码例子、剩余项及复算方法见 [覆盖与缺口核算](learning-coverage.md)；机器清单为 [learning-scope.json](learning-scope.json)。原来的 33 项估算清单也保存在其中，不把全部已有课程、候选 API 或方法自动当成已覆盖。后续新增内容若需重算，应明确另建范围版本，不能继续将这份历史清单的比例称为完整岗位路线覆盖率。

### 4.3 机制分组与旧材料索引

**必学**表示需要能解释并实现一个最小例子；**查阅**用于清单外内容。表中一行是机制分组，不是一课；按“旧方法能做什么 → 新增要求 → 新机制”继续拆分。82 项内的复杂接口可以后学，但在整套课程结束前都有正式单元覆盖。

用户进一步要求全课结束时包含全部 82 项 API。正式课程安排以 [8 模块、40 单元的课程设置](curriculum.md)及其 [curriculum.json](curriculum.json) 为准；下面的编号与链接保留为机制分组及旧材料索引，不能当作新单元编号。82 项内的内容全部安排正式单元，不再无限期放在选读中；只有清单外内容继续按需。

下表负责学习顺序与深度；[当前 API 表](current-api-plan.md)负责完整列出具体方法、官网页面和调用次数。当前范围足以服务至少 70%、约 80% 的静态调用覆盖目标，不继续把所有剩余低频 API 加进主线，也不据此声称覆盖了等比例的实际运行场景。

| 顺序与深度 | 要解决的具体问题 | Python 原生内容与官方小节 | 现有入口与处理 |
| --- | --- | --- | --- |
| 1. 执行基础 · 必学 | 一份工作何时执行？多份独立工作怎样在等待期间推进？ | `async def`、`await`、`asyncio.run`、`sleep`、`create_task`、TaskGroup 正常退出、`gather` 正常收集；[协程与任务](https://docs.python.org/3.16/library/asyncio-task.html)、[运行入口](https://docs.python.org/3.16/library/asyncio-runner.html) | 保留 01–05 的最小边界，不提前塞入失败、线程或完整事件循环实现。 |
| 2. 结果与失败 · 必学 | 一项先完成或失败后，剩余工作由谁继续等待或结束？ | `wait`、Task 的 `done/result/exception`；随后比较 `gather` 的异常传播与 TaskGroup 的失败收尾；最小 `ExceptionGroup`/`except*`；[等待](https://docs.python.org/3.16/library/asyncio-task.html#waiting-primitives)、[任务组](https://docs.python.org/3.16/library/asyncio-task.html#task-groups) | 06 先讲完成集合；07 讲清取消后，再回访 04/05 的异常分支。`as_completed` 保留短例或源码补学。 |
| 3. 取消与时间预算 · 必学 | 超时后到底停止了谁？清理执行完了吗？ | `Task.cancel`、`CancelledError`、`try/finally`、`wait_for`；再补 `asyncio.timeout` 的作用域预算；`shield` 连同任务引用和后续收尾作为源码补学；[取消](https://docs.python.org/3.16/library/asyncio-task.html#task-cancellation)、[超时](https://docs.python.org/3.16/library/asyncio-task.html#timeouts) | 07 当前同时包含多种机制，后续拆成取消请求、等待清理、单次超时、作用域预算。不在一页一次讲完。 |
| 4. 负载与共享状态 · 必学 | 慢服务和快生产者一起运行时，怎样控制在途工作与积压？ | `Semaphore`；有界 `asyncio.Queue` 的 `put/get`；`asyncio.Lock`；`Event.set/wait/clear`；[同步原语](https://docs.python.org/3.16/library/asyncio-sync.html)、[队列](https://docs.python.org/3.16/library/asyncio-queue.html) | 08 → 09 → 17。许可数、排队容量、共享状态、条件通知分别讲。Semaphore 与 Event 即使不是三库共用，也因工程责任进入必学。`task_done/join` 只在采用计数完成协议时补，不与结束标记强行混用。 |
| 5. 阻塞工作与线程 · 必学 | 同步工具会阻塞谁？取消等待后，线程是否仍在执行？ | `to_thread` → `ThreadPoolExecutor.submit` 与执行器 Future → `run_in_executor`；线程的 `start/join`、`Lock`、`Event`、`queue.Queue`；[线程执行](https://docs.python.org/3.16/library/asyncio-task.html#running-in-threads)、[执行器](https://docs.python.org/3.16/library/concurrent.futures.html)、[线程](https://docs.python.org/3.16/library/threading.html)、[同步队列](https://docs.python.org/3.16/library/queue.html) | 10 → 11 → 19 的相关部分。明确 asyncio Future 与执行器 Future 的区别；线程停止依靠合作协议，超时不强杀运行中的线程。 |
| 6. 资源与任务上下文 · 必学 | 退出时谁关闭资源？并发任务怎样保留自己的请求与 Trace 信息？ | `async with`、`asynccontextmanager`、`ContextVar.set/get/reset`；任务创建与 `to_thread` 的上下文传播；[异步资源](https://docs.python.org/3.16/library/contextlib.html#contextlib.asynccontextmanager)、[上下文](https://docs.python.org/3.16/library/contextvars.html) | 12 的资源部分 → 13。先理解普通 `with`/`yield` 前置，再学异步进入退出；分别测试成功、失败与取消时的恢复。可变对象的引用不会自动深拷贝。 |
| 7. 可等待对象与异步迭代 · 必学 | 怎样辨认可等待对象？怎样逐项等待并关闭异步生成器？ | `inspect.isawaitable`、`iscoroutinefunction` 的边界，`Awaitable`/`AsyncIterator` 注解，`async for`、异步生成器与提前关闭；[检查对象](https://docs.python.org/3.16/library/inspect.html)、[异步语法](https://docs.python.org/3.16/reference/compound_stmts.html#the-async-for-statement)、[aclosing](https://docs.python.org/3.16/library/contextlib.html#contextlib.aclosing) | 12 的迭代部分与 23 的对象检查部分拆开使用。返回值可 await 不代表调用该同步函数不会阻塞。 |
| 8. 进程与工具退出 · 基础必学，细节补学 | Python 子进程或外部命令超时以后，怎样确认已退出并收回资源？ | `subprocess.run/Popen/communicate/wait` 与 `TimeoutExpired`；`multiprocessing.Process.start/is_alive/join/terminate/kill`；[外部命令](https://docs.python.org/3.16/library/subprocess.html)、[Python 子进程](https://docs.python.org/3.16/library/multiprocessing.html#process-and-exceptions) | 14、20 中先选工具执行和生命周期部分；退出请求与等待退出分开验证。进程池、启动方式、序列化在 CPU 工作需求出现时补。 |

验证附属于各个原生机制：运行例子、必要断言、受控的事件顺序和 asyncio 自身的调试信息，用来确认结果、取消、阻塞与退出行为。`unittest`、`AsyncMock`、日志和性能分析工具只在例子确实需要时说明最小用法，不列为独立必学模块。

前五课之后，按新规划的 **06–08 完成与结果 → 09–15 取消、预算与失败 → 16–19 协程协调 → 20–24 资源、迭代与上下文 → 25–31 线程与执行器 → 32–35 协程和线程交接 → 36–40 进程与命令** 推进。旧页保留作材料入口，不能要求读者为了一个新问题先读完整个旧页。

`run_coroutine_threadsafe` 安排在新单元 35，完成全课必须覆盖；旧页 15 的手动 loop 生命周期、旧页 18 的 `Condition/RLock`、旧页 21 的信号/进程组/文件锁，以及进程池属于清单外按需内容。

按需查阅：22 的原始 Streams、低层 Transport/Protocol、选择器、任务调用图及新版本特有调度选项。`asyncio.create_subprocess_exec` 是异步管理外部命令的可选方案，在实现异步工具执行器时补；不因官方有整页就要求先学完。对线程、协程和进程的选型，应结合阻塞 I/O、CPU 运算、GIL 和扩展库实际行为，不许诺线程能让所有计算多核加速。

### 4.4 当前材料的实际缺口

已有页面或源码定位不等于已经理解原生机制。当前按以下顺序改进：

1. **最先补失败责任**：04/05 目前以正常完成为主；先学 07 的取消，再用同一组任务比较“其中一项失败”时的等待、异常与剩余任务清理。清楚区分默认 `gather`、`return_exceptions=True` 与 TaskGroup，不把不同责任简化成语法替换。
2. **拆开多主题旧课**：07 同时讲取消、三种超时和 shield，12 同时讲资源与异步迭代，15 同时讲 Future 与 loop，23 同时讲 hook、装饰器与协议。保留已有例子和锚点，先切成可独立复述的学习单元，不一次抛出整章。
3. **加强队列与退出合同**：分别验证满队列时生产者等待、消费者失败、外部取消及结束信号的责任。仅看到 `put/get` 次数，无法证明组件没有遗留等待者。重试、幂等和去重属于应用合同，原生队列不自动保证“结果恰好处理一次”。
4. **补原生行为的验证例子**：现有网站测试主要核对示例、源码和导航。面向学习者还缺取消、失败、资源关闭、上下文隔离等可观察实验；只补足当前机制的证据，不展开通用测试与诊断课程。
5. **最后串联原生机制**：在原子单元之后，用最小综合例子串联创建、等待、取消与清理。框架设计、模型接入和完整业务执行器不属于本专题的交付目标。

### 4.5 能力验收：六个可观察结果

以下是后续练习的完成标准，**当前未标记为已完成**。不以读完页数、输出看起来正确或覆盖百分比代替验收。

| 验收情景 | 必须观察到的结果 | 主要验证方式 |
| --- | --- | --- |
| 多任务正常与部分失败 | 成功结果能关联任务 ID；失败进入约定的异常或结果通道；所有已创建任务都有收尾责任 | 固定输入 + 显式失败注入，分别验证整组失败与独立收集的合同 |
| 慢任务、超时与外部取消 | 清理标记已经出现，取消继续传播；等待超时不会被误报为底层工作已停止 | 用 Event 建立“任务已进入”的条件，再取消；超时只作有限等待保护 |
| 快生产者、慢消费者 | 在途数与排队数满足各自限制；消费者失败或调用方取消后，双方都能退出 | 计数与状态断言；分别测正常完成、满队列及退出，不依靠日志顺序猜测 |
| 同步工具与线程退出 | 事件循环仍能响应；取消后运行中的线程仍有明确结束协议；退出后线程已 join | 线程 Event 与协程协调；检查受测组件拥有的线程，不断言其他库线程全部消失 |
| 任务上下文与可等待对象 | 每份任务保留自己的值，退出或异常后恢复；能区分函数与调用返回的 awaitable | ContextVar 最小例子，包含返回协程的普通函数、异常路径和可变状态边界 |
| 外部进程与退出 | 子进程退出状态已读取，管道按协议关闭；超时不被当成进程已经结束 | 有限时长的本地子进程；核对退出与关闭结果，不只检查超时异常 |

验证例子应通过事件和明确状态建立先后条件，不把很短的 `sleep` 当作可靠同步。只检查例子自己创建的任务、线程和进程；避免把环境中的其他工作误判为泄漏。不要求先学完整测试框架才继续异步课程。

## 5. 与现有教程的衔接

最新课程设置已保存为 [curriculum.md](curriculum.md)：8 模块、40 单元，每个单元都指定前置、新问题、正式引入 API、原子结论、自查和可复用旧材料。01–05 沿用现有课；06–40 是拆分与补写计划，不声称已完成。机器检查覆盖 82/82 项 API、7 项语法和 8 类异常，验证前置只能指向更早单元。运行 `python3 python-async-reference/tools/build_curriculum.py --check` 复核。网页 [学习路线与完成标准](../content/projects/python-async-concurrency/learning-route/index.md) 从同一课程数据生成模块表，避免两套安排分叉。

2026-10-13 落地：新增 [05 gather](../content/projects/python-async-concurrency/05-gather/index.md)，原第 05 课及之后显示编号顺延，页面地址保留。此前已新增 [04 TaskGroup](../content/projects/python-async-concurrency/04-taskgroup/index.md)，只讲正常退出作用域时等待组内任务；沿用 03 的生成函数和两份任务。已有章节显示编号顺延，旧网页地址保留。异常组和完整取消机制在后续展开。

1. 现有 01、02、03 的递进继续沿用。`gather` 已从 03 的折叠选读迁到独立的 [第 05 课](../content/projects/python-async-concurrency/05-gather/index.md)，随后第 06 课再讲 wait 与 as_completed；03 的旧锚点保留为跳转入口。
2. 新增的 04 TaskGroup 已在首次使用前交代 `async with` 的进入和退出。取消、Semaphore 等章节继续使用这个最小模型；自定义协议实现仍可后置。
3. 现有章节包含大量按需材料。章节已经存在不代表都属于当前必读范围；重排时以第 4.3 节的岗位能力与概念依赖为准，再用三库用法和次数辅助决定详略。
4. 每一学习单元开头先带上前文最小结论，每次只增加必要关系。源码应用和全部位置清单放在默认收起的入口，正文集中解释本节例子。

2026-10-13 岗位目标澄清后的落地：专题首页新增技术能力导向的[学习路线与完成标准](../content/projects/python-async-concurrency/learning-route/index.md)入口，完整课程目录默认收起。主线按第 4.3 节区分必学与按需内容；上述旧课拆分和第 4.5 节的故障实验是下一阶段待完成的教学工作，本轮不把规划写成已经完成的能力。

## 6. 官方文档与版本

1. 表格链接沿用用户指定的 Python 3.16 官方文档，本地快照标题为 3.16.0a1。先读表中指定小节；[High-level API Index](https://docs.python.org/3.16/library/asyncio-api-index.html) 用来定位功能。
2. 现有[教程版本说明](../content/projects/python-async-concurrency/references/index.md)按 Python 3.12 校验示例，统一最低要求为 Python 3.11。学习目录引用 3.16 不代表示例可以直接使用全部新接口。
3. 修改示例时核对具体版本变化。例如较新文档中的 `as_completed` 异步迭代写法、eager 执行选项，都应在引入时单独说明适用版本。
4. 更新数据或学习顺序时同步核对本文中的次数、筛选理由与官方小节。本文是独立维护的学习规划，不属于自动生成报告；刷新统计时保留此文件。
