# Python 原生异步与并发：完整课程设置

**8 个模块，40 个最小学习单元，覆盖 82/82 项调用与方法。**

这是课程规划，不是 40 篇都已编写完成的声明。01–05 沿用现有课程，其余按本表拆分或补写。现有 23 页的编号与 URL 保留，不能把新单元号误当成旧页面号。

输入范围：[82 项 API](current-api-plan.md)；唯一课程数据：[curriculum.json](curriculum.json)。课程按概念递进；每学完一个模块完成对应自查，不要求先记住整张清单。

## 阅读与完成规则

1. 01–05 沿用现有页面；06–40 是教学重组计划，不表示已写完。
2. 单元编号是新规划编号；复用的旧页面保留原编号和 URL。
3. 每个 API 有一个正式引入单元；后面的复用与回访不重复计数。
4. 完成整套课程时覆盖全部 82 项；按单元逐步学习，不要求一次学完，也不把清单内内容无限期留作选读。清单外内容仍按需。
5. 每单元先写前课结论，再给新增要求；一个完整可运行例子只增加当前必要关系。
6. 模块结束能解释该模块的正常、失败或退出行为；全课结束再串联一个只含已学原生机制的综合例子。
7. API 正式讲解必须解释对象、调用时机、返回值以及必要的等待/异常/退出边界；仅在代码中出现不算完成讲解。

## 分阶段课程

| 模块 | 学习单元 | 每阶段先解决什么 | 首次正式讲解的 API 数 |
| --- | --- | --- | ---: |
| 1. 协程与任务基础 | 01–05 | 创建 → 内部等待 → 安排 → 分组 → 收集结果 | 6 |
| 2. 完成情况与结果 | 06–08 | 先认任务对象，再按完成情况处理结果 | 5 |
| 3. 取消、预算与失败 | 09–15 | 先理解取消，再理解时间预算和整组失败 | 7 |
| 4. 协程之间的协调 | 16–19 | 分别解决许可、数据交接、互斥与通知 | 13 |
| 5. 异步资源、迭代与上下文 | 20–24 | 先说明作用域与产出，再解释关闭、隔离和对象检查 | 8 |
| 6. 线程与执行器 | 25–31 | 从阻塞函数到线程，再到线程池和退出 | 24 |
| 7. 协程与线程的交接 | 32–35 | 区分 Future 类型以及跨线程提交方向 | 7 |
| 8. 进程与外部命令 | 36–40 | 先运行与取输出，再处理终止和回收 | 12 |

下面按模块展开。每个单元都列出唯一问题、正式引入的 API、前置和自查；同一 API 后续复用不重复计数。

<details id="curriculum-stage-coroutines">
<summary>模块 1 · 协程与任务基础（01–05）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 01 · 定义、创建与运行协程 | 调用 async def 定义的函数后，函数体已经运行了吗？ | `asyncio.run`、`async def` | 普通函数基础 |
| 02 · 在协程内部等待 | 已经在协程里，怎样等待另一份工作的结果？ | `asyncio.sleep`、`await` | 01 |
| 03 · 先安排多份任务 | 怎样让两份独立工作在等待期间都能推进？ | `asyncio.create_task` | 02 |
| 04 · 让代码块负责等完任务 | 怎样给一组任务一个明确的结束位置？ | `asyncio.TaskGroup`、`asyncio.TaskGroup.create_task`、`async with` | 03 |
| 05 · 收集整组返回值 | 怎样把这组任务的结果一次收齐？ | `asyncio.gather` | 03、04 |

<details>
<summary>本模块的原子结论与自查</summary>

### 01 · 定义、创建与运行协程

1. **带走：** 定义产生协程函数，调用产生协程对象，运行入口才驱动它执行。
2. **自查：** 预测创建协程与运行协程时分别会打印什么。

### 02 · 在协程内部等待

1. **带走：** await 等待对象完成；等待未完成的异步操作时，当前任务可以挂起。
2. **自查：** 沿两次直接 await 预测执行顺序。

### 03 · 先安排多份任务

1. **带走：** create_task 安排协程；调用方在后续挂起时，事件循环可以运行已安排的任务。
2. **自查：** 分清安排顺序、完成顺序与 await 取值顺序。

现有计时展示使用 time.perf_counter；这里只说明用于显示经过时间，第 11 单元正式解释。

### 04 · 让代码块负责等完任务

1. **带走：** 正常退出 TaskGroup 的代码块前，会等完组内任务。
2. **自查：** 预测代码块之后的输出能否先于组内任务结束。

这里只建立 async with 进入与退出的最小关系；资源协议在第 20 单元展开。

### 05 · 收集整组返回值

1. **带走：** 正常完成时，gather 按传入顺序给出结果列表。
2. **自查：** 任务反向完成时，预测结果列表的顺序。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 01：沿用现有课。材料：[01 · async def：定义之后，什么时候执行？](../content/projects/python-async-concurrency/01-async-def/index.md)。
- 02：沿用现有课。材料：[02 · await：等待结果，不等于自动并发](../content/projects/python-async-concurrency/02-await/index.md)。
- 03：沿用现有课。材料：[03 · create_task：先安排工作，再等待结果](../content/projects/python-async-concurrency/03-tasks/index.md)。
- 04：沿用现有课。材料：[04 · TaskGroup：离开代码块前，等任务结束](../content/projects/python-async-concurrency/04-taskgroup/index.md)。
- 05：沿用现有课。材料：[05 · gather：等待一组任务，收集一组结果](../content/projects/python-async-concurrency/05-gather/index.md)。

</details>

</details>

<details id="curriculum-stage-results">
<summary>模块 2 · 完成情况与结果（06–08）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 06 · 先取得完成情况 | 不等全部结束，怎样先知道哪些任务完成了？ | `asyncio.wait` | 05 |
| 07 · 读取 Task 的状态与结果 | Task 对象与它保存的返回值、异常有什么区别？ | `asyncio.Task.done`、`asyncio.Task.result`、`asyncio.Task.exception` | 06 |
| 08 · 按完成顺序取结果 | 怎样依次处理先完成的工作？ | `asyncio.as_completed` | 06、07 |

<details>
<summary>本模块的原子结论与自查</summary>

### 06 · 先取得完成情况

1. **带走：** wait 返回完成与未完成的任务集合，未完成的任务不会因此停止。
2. **自查：** 用已知 await 读取 done 中任务并等完 pending，暂不引入 as_completed。

### 07 · 读取 Task 的状态与结果

1. **带走：** done 判断是否结束；result 读取值或抛出保存的异常，exception 读取保存的异常。
2. **自查：** 分别预测未完成、成功和失败任务的读取结果。
3. **需要辨认的异常：** `asyncio.InvalidStateError`。

只观察任务状态与正常/异常结束；取消状态在第 9 单元再加入。

### 08 · 按完成顺序取结果

1. **带走：** as_completed 提供按完成推进的等待入口，与 gather 的传入顺序结果不同。
2. **自查：** 说明为何先完成的任务可以先被处理。

主例子使用 Python 3.12 的普通 for 加 await 写法；新版本 async for 写法不作前置。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 06：规划单元，待从旧课拆分或补写。材料：[06 · wait 与 as_completed：先处理已经完成的工作](../content/projects/python-async-concurrency/04-results/index.md)。
- 07：规划单元，待从旧课拆分或补写。材料：[06 · wait 与 as_completed：先处理已经完成的工作](../content/projects/python-async-concurrency/04-results/index.md)、[15 · Future、回调与跨线程事件循环](../content/projects/python-async-concurrency/13-event-loop/index.md)。
- 08：规划单元，待从旧课拆分或补写。材料：[06 · wait 与 as_completed：先处理已经完成的工作](../content/projects/python-async-concurrency/04-results/index.md)。

</details>

</details>

<details id="curriculum-stage-cancellation">
<summary>模块 3 · 取消、预算与失败（09–15）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 09 · 请求取消并等到退出 | 发出取消请求以后，怎样确认任务收尾了？ | `asyncio.Task.cancel`、`try/finally` | 07 |
| 10 · 限制一次等待的时长 | 这次等待超过预算时，取消和异常怎样发生？ | `asyncio.wait_for`、`builtins.TimeoutError` | 09 |
| 11 · 计量经过时间与预算 | 怎样度量等待耗时，而不把时钟读数当成调度顺序？ | `time.monotonic`、`time.perf_counter` | 10 |
| 12 · 给一段异步代码共享时间预算 | 多个 await 怎样共用一个超时边界？ | `asyncio.timeout` | 04、10、11 |
| 13 · 区分取消等待者与内部工作 | 调用方取消时，有没有需要继续负责等完的工作？ | `asyncio.shield` | 09、10 |
| 14 · gather 中有任务失败 | 一份任务报错以后，整组结果与剩余任务怎样处理？ | 回访 `asyncio.gather` | 05、07、09 |
| 15 · TaskGroup 中有任务失败 | 相关任务需要共同失败时，代码块怎样收尾？ | `except*`；回访 `asyncio.TaskGroup`、`asyncio.TaskGroup.create_task` | 04、09、14 |

<details>
<summary>本模块的原子结论与自查</summary>

### 09 · 请求取消并等到退出

1. **带走：** cancel 请求取消；继续等待任务，才能观察它处理取消并执行已进入的 finally。
2. **自查：** 让任务先进入等待，再取消，确认清理和取消传播的顺序。
3. **需要辨认的异常：** `asyncio.CancelledError`。

### 10 · 限制一次等待的时长

1. **带走：** wait_for 通常取消等待对象并等它处理取消；TimeoutError 表达超时失败。
2. **自查：** 解释为什么清理会让总耗时超过指定 timeout，并给出自定义超时异常信息。

### 11 · 计量经过时间与预算

1. **带走：** 用单调时钟计算时间差与截止预算；计时本身不驱动任务。
2. **自查：** 分别标出开始、结束与剩余预算，不用墙钟误差推断并发先后。

正式解释第 3–5 单元展示时间戳时使用的 perf_counter；不引入通用性能分析课程。

### 12 · 给一段异步代码共享时间预算

1. **带走：** timeout 管理代码块的时间预算，超时异常在其作用域外处理。
2. **自查：** 比较每次 wait_for 单独计时与整个代码块共用预算。

### 13 · 区分取消等待者与内部工作

1. **带走：** shield 阻断这一层取消传播，外层仍可取消，内部工作仍须有人持有并收尾。
2. **自查：** 指出外层取消后仍存活的任务由谁等待、谁读取错误。

### 14 · gather 中有任务失败

1. **带走：** 默认 gather 传播首个异常但不会因此取消其他任务；return_exceptions 改变结果的收集方式。
2. **自查：** 分别追踪默认模式和 return_exceptions=True 的剩余工作。

### 15 · TaskGroup 中有任务失败

1. **带走：** TaskGroup 遇到一般子任务异常会取消并等完其余任务，再报告异常组。
2. **自查：** 用同一组失败任务比较第 14 单元，并读取 ExceptionGroup 的成员。
3. **需要辨认的异常：** `builtins.ExceptionGroup`。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 09：规划单元，待从旧课拆分或补写。材料：[07 · 取消与超时：请求停止以后，还要等待收尾](../content/projects/python-async-concurrency/05-cancellation/index.md)。
- 10：规划单元，待从旧课拆分或补写。材料：[07 · 取消与超时：请求停止以后，还要等待收尾](../content/projects/python-async-concurrency/05-cancellation/index.md)。
- 11：规划单元，待从旧课拆分或补写。材料：[03 · create_task：先安排工作，再等待结果](../content/projects/python-async-concurrency/03-tasks/index.md)、[07 · 取消与超时：请求停止以后，还要等待收尾](../content/projects/python-async-concurrency/05-cancellation/index.md)。
- 12：规划单元，待从旧课拆分或补写。材料：[07 · 取消与超时：请求停止以后，还要等待收尾](../content/projects/python-async-concurrency/05-cancellation/index.md)。
- 13：规划单元，待从旧课拆分或补写。材料：[07 · 取消与超时：请求停止以后，还要等待收尾](../content/projects/python-async-concurrency/05-cancellation/index.md)。
- 14：规划单元，待从旧课拆分或补写。材料：[05 · gather：等待一组任务，收集一组结果](../content/projects/python-async-concurrency/05-gather/index.md)、[07 · 取消与超时：请求停止以后，还要等待收尾](../content/projects/python-async-concurrency/05-cancellation/index.md)。
- 15：规划单元，待从旧课拆分或补写。材料：[04 · TaskGroup：离开代码块前，等任务结束](../content/projects/python-async-concurrency/04-taskgroup/index.md)、[07 · 取消与超时：请求停止以后，还要等待收尾](../content/projects/python-async-concurrency/05-cancellation/index.md)。

</details>

</details>

<details id="curriculum-stage-coordination">
<summary>模块 4 · 协程之间的协调（16–19）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 16 · 限制同时进入的工作 | 任务都已安排后，怎样只允许少量工作进入？ | `asyncio.Semaphore`、`asyncio.Semaphore.acquire`、`asyncio.Semaphore.release` | 04、09 |
| 17 · 让生产者与消费者交接数据 | 生产快、消费慢时，数据怎样有界地等待？ | `asyncio.Queue`、`asyncio.Queue.put`、`asyncio.Queue.get` | 03、09、16 |
| 18 · 保护跨 await 的共享状态 | 多份任务会交错修改同一状态时怎么办？ | `asyncio.Lock`、`asyncio.Lock.acquire`、`asyncio.Lock.release` | 04、09、17 |
| 19 · 让任务等待一个通知 | 没有数据要传，只需要通知其他任务继续，怎么办？ | `asyncio.Event`、`asyncio.Event.set`、`asyncio.Event.wait`、`asyncio.Event.clear` | 17、18 |

<details>
<summary>本模块的原子结论与自查</summary>

### 16 · 限制同时进入的工作

1. **带走：** 许可数限制进入受控区域的工作，退出时归还许可。
2. **自查：** 记录进入区域的最大数量，并验证异常后许可可重新取得。

### 17 · 让生产者与消费者交接数据

1. **带走：** 有界 Queue 在满时等待 put、空时等待 get，连接生产与消费。
2. **自查：** 区分排队容量与在途数量，并说明结束信号由应用约定。

### 18 · 保护跨 await 的共享状态

1. **带走：** 同一事件循环中的 Lock 保护约定的共享操作，获取等待可以挂起任务。
2. **自查：** 指出需要保护的读改写范围，以及退出时谁释放锁。

### 19 · 让任务等待一个通知

1. **带走：** Event 保存一个可设置和清除的标志，wait 等待标志为真；它不是计数队列。
2. **自查：** 预测 set、wait、clear 对后续等待者的影响。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 16：规划单元，待从旧课拆分或补写。材料：[08 · Semaphore：限制同时进入的工作数量](../content/projects/python-async-concurrency/06-semaphore/index.md)。
- 17：规划单元，待从旧课拆分或补写。材料：[09 · Queue：把生产速度和消费速度接起来](../content/projects/python-async-concurrency/07-queues/index.md)。
- 18：规划单元，待从旧课拆分或补写。材料：[17 · Event 通知与异步互斥](../content/projects/python-async-concurrency/15-async-notification/index.md)。
- 19：规划单元，待从旧课拆分或补写。材料：[17 · Event 通知与异步互斥](../content/projects/python-async-concurrency/15-async-notification/index.md)。

</details>

</details>

<details id="curriculum-stage-protocols">
<summary>模块 5 · 异步资源、迭代与上下文（20–24）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 20 · 把异步资源绑定到作用域 | 资源使用结束或报错后，怎样统一关闭？ | `contextlib.asynccontextmanager` | 04、09 |
| 21 · 逐项等待异步产出 | 结果是一项项到来的，怎样逐项消费？ | `async for`、`异步生成器中的 yield` | 02、20 |
| 22 · 提前停止异步迭代 | 循环 break 之后，怎样让生成器及时清理？ | `contextlib.aclosing` | 09、20、21 |
| 23 · 保存每份任务自己的上下文 | 并发任务怎样各自读取并恢复临时值？ | `contextvars.ContextVar`、`contextvars.ContextVar.get`、`contextvars.ContextVar.set`、`contextvars.ContextVar.reset` | 03、09、20 |
| 24 · 辨认函数与可等待对象 | 一个函数调用之后，究竟应不应该 await 返回值？ | `inspect.isawaitable`、`inspect.iscoroutinefunction` | 02、21 |

<details>
<summary>本模块的原子结论与自查</summary>

### 20 · 把异步资源绑定到作用域

1. **带走：** asynccontextmanager 将准备、yield 使用与 finally 清理组织成异步作用域。
2. **自查：** 沿正常、异常与取消路径指出已进入资源的清理位置。

若普通 with、生成器 yield 或装饰器尚不熟悉，先用最小前置例子解释，不混入主例子的新机制。

### 21 · 逐项等待异步产出

1. **带走：** 含 yield 的 async def 产生异步生成器；async for 逐项等待，不自动并行循环体。
2. **自查：** 区分 await 一次结果与 async for 多次取项。

### 22 · 提前停止异步迭代

1. **带走：** aclosing 将异步生成器的关闭绑定到使用它的作用域退出。
2. **自查：** 提前停止消费，确认生成器已进入的 finally 被执行。

### 23 · 保存每份任务自己的上下文

1. **带走：** ContextVar 保存上下文中的绑定，set 的 token 用于恢复先前状态。
2. **自查：** 验证两个任务与嵌套作用域的值，并区分绑定隔离与共享可变对象。

### 24 · 辨认函数与可等待对象

1. **带走：** 函数形状与返回对象是不同证据；isawaitable 检查对象，不执行它。
2. **自查：** 对比 async def、普通值和普通函数返回协程三种情况。

Awaitable/AsyncIterator 注解仅按需说明，注解不会执行或验证对象。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 20：规划单元，待从旧课拆分或补写。材料：[12 · async with、async for 与异步生成器](../content/projects/python-async-concurrency/10-async-protocols/index.md)。
- 21：规划单元，待从旧课拆分或补写。材料：[12 · async with、async for 与异步生成器](../content/projects/python-async-concurrency/10-async-protocols/index.md)。
- 22：规划单元，待从旧课拆分或补写。材料：[23 · 异步能力检查与协议边界](../content/projects/python-async-concurrency/21-async-inspection/index.md)。
- 23：规划单元，待从旧课拆分或补写。材料：[13 · ContextVar：让并发任务保留各自的上下文](../content/projects/python-async-concurrency/11-contextvars/index.md)。
- 24：规划单元，待从旧课拆分或补写。材料：[23 · 异步能力检查与协议边界](../content/projects/python-async-concurrency/21-async-inspection/index.md)。

</details>

</details>

<details id="curriculum-stage-threads">
<summary>模块 6 · 线程与执行器（25–31）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 25 · 把阻塞函数交给线程 | 同步等待会占住事件循环线程时怎么办？ | `asyncio.to_thread`、`time.sleep` | 03、09、23 |
| 26 · 创建、启动并等待线程 | 线程对象创建以后，何时开始，怎样等到退出？ | `threading.Thread`、`threading.Thread.start`、`threading.Thread.is_alive`、`threading.Thread.join` | 25 |
| 27 · 保护线程共享状态 | 多个线程同时修改共享数据时怎样互斥？ | `threading.Lock`、`threading.Lock.acquire`、`threading.Lock.release` | 18、26 |
| 28 · 通知线程合作退出 | 线程需要收到停止请求时怎样安排？ | `threading.Event`、`threading.Event.set`、`threading.Event.wait`、`threading.Event.clear` | 19、26、27 |
| 29 · 在线程之间交接数据 | 同步队列怎样等待数据，或立即尝试取数？ | `queue.Queue`、`queue.Queue.put`、`queue.Queue.get`、`queue.Queue.get_nowait` | 17、26、28 |
| 30 · 把工作提交到线程池 | 不手动创建每个线程，怎样取得已提交工作的结果？ | `concurrent.futures.ThreadPoolExecutor`、`concurrent.futures.Executor.submit`、`concurrent.futures.Future.done`、`concurrent.futures.Future.result`、`concurrent.futures.Future.exception` | 07、26、27 |
| 31 · 结束线程池并处理未执行工作 | 退出执行器时，排队工作和运行中工作分别怎么办？ | `concurrent.futures.Future.cancel`、`concurrent.futures.Executor.shutdown` | 09、28、30 |

<details>
<summary>本模块的原子结论与自查</summary>

### 25 · 把阻塞函数交给线程

1. **带走：** to_thread 让同步函数在线程中执行；取消等待者不会强杀已开始的线程工作。
2. **自查：** 比较 time.sleep 与 asyncio.sleep，并观察 to_thread 的上下文传播。

### 26 · 创建、启动并等待线程

1. **带走：** start 启动线程，is_alive 观察存活状态，join 等待退出而不是请求停止。
2. **自查：** 辨认创建、启动、执行、join 返回四个阶段。

### 27 · 保护线程共享状态

1. **带走：** 线程 Lock 在获取失败时阻塞调用线程，配对释放保护共享操作。
2. **自查：** 与 asyncio.Lock 比较等待位置，并验证共享计数。

### 28 · 通知线程合作退出

1. **带走：** Event 传递线程间标志；线程需要合作检查，join 才负责等待退出。
2. **自查：** 按设置标志、线程结束、join 返回的顺序核对。

### 29 · 在线程之间交接数据

1. **带走：** queue.Queue 为线程交接提供同步等待；get_nowait 为空时抛 Empty。
2. **自查：** 区分空队列等待、非阻塞取数，以及有界 put 的 Full。
3. **需要辨认的异常：** `queue.Empty`、`queue.Full`。

### 30 · 把工作提交到线程池

1. **带走：** submit 返回执行器 Future；result 可以阻塞调用线程，成功值与失败异常由 Future 保存。
2. **自查：** 说明它与 asyncio Task 的相似点，以及为何不能直接 await 它。
3. **需要辨认的异常：** `concurrent.futures.TimeoutError`。

### 31 · 结束线程池并处理未执行工作

1. **带走：** Future.cancel 不能强停已运行的工作，shutdown 决定等待及未开始工作的处理。
2. **自查：** 分别检查排队取消、运行中取消失败与最终退出。
3. **需要辨认的异常：** `concurrent.futures.CancelledError`。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 25：规划单元，待从旧课拆分或补写。材料：[10 · 线程池：把阻塞工作移出事件循环](../content/projects/python-async-concurrency/08-executors/index.md)、[03 · create_task：先安排工作，再等待结果](../content/projects/python-async-concurrency/03-tasks/index.md)。
- 26：规划单元，待从旧课拆分或补写。材料：[11 · Lock、Event 与线程退出](../content/projects/python-async-concurrency/09-thread-synchronization/index.md)。
- 27：规划单元，待从旧课拆分或补写。材料：[11 · Lock、Event 与线程退出](../content/projects/python-async-concurrency/09-thread-synchronization/index.md)。
- 28：规划单元，待从旧课拆分或补写。材料：[11 · Lock、Event 与线程退出](../content/projects/python-async-concurrency/09-thread-synchronization/index.md)。
- 29：规划单元，待从旧课拆分或补写。材料：[09 · Queue：把生产速度和消费速度接起来](../content/projects/python-async-concurrency/07-queues/index.md)。
- 30：规划单元，待从旧课拆分或补写。材料：[10 · 线程池：把阻塞工作移出事件循环](../content/projects/python-async-concurrency/08-executors/index.md)、[19 · 线程池 Future 的结果与退出](../content/projects/python-async-concurrency/17-executor-results/index.md)。
- 31：规划单元，待从旧课拆分或补写。材料：[19 · 线程池 Future 的结果与退出](../content/projects/python-async-concurrency/17-executor-results/index.md)。

</details>

</details>

<details id="curriculum-stage-bridges">
<summary>模块 7 · 协程与线程的交接（32–35）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 32 · 从协程使用指定执行器 | 已经选定线程池，怎样提交并用 await 等结果？ | `asyncio.get_running_loop`、`asyncio.AbstractEventLoop.run_in_executor` | 25、30 |
| 33 · 等待已有的执行器 Future | 已经拿到执行器 Future，怎样接入协程等待？ | `asyncio.wrap_future` | 30、32 |
| 34 · 读取 asyncio Future 的结果 | 协程接口给回一个 Future 时，怎样判断与读取？ | `asyncio.Future.done`、`asyncio.Future.result`、`asyncio.Future.exception` | 07、32、33 |
| 35 · 从另一个线程提交协程 | 同步线程怎样把协程交给正在运行的事件循环？ | `asyncio.run_coroutine_threadsafe` | 26、28、30、32、34 |

<details>
<summary>本模块的原子结论与自查</summary>

### 32 · 从协程使用指定执行器

1. **带走：** 从当前运行循环提交执行器工作，得到可 await 的 asyncio Future。
2. **自查：** 标出同步函数运行位置和等待者恢复位置。

### 33 · 等待已有的执行器 Future

1. **带走：** wrap_future 将执行器 Future 衔接为当前循环可等待的 Future，不重新提交工作。
2. **自查：** 证明被包装的工作只提交一次，并区分两类 Future。

### 34 · 读取 asyncio Future 的结果

1. **带走：** asyncio Future 的结果读取不阻塞等待，未完成时读取会失败。
2. **自查：** 对比 asyncio Future 与执行器 Future 的 result 行为。

### 35 · 从另一个线程提交协程

1. **带走：** 跨线程提交返回执行器 Future；事件循环线程不能阻塞等待自己才能完成的工作。
2. **自查：** 画出提交线程、循环线程与结果返回的方向，排除循环等待。

主例子用 asyncio.run 持有循环并从工作线程提交；不强行把 new_event_loop/run_forever 等清单外 API 作为前置。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 32：规划单元，待从旧课拆分或补写。材料：[10 · 线程池：把阻塞工作移出事件循环](../content/projects/python-async-concurrency/08-executors/index.md)、[15 · Future、回调与跨线程事件循环](../content/projects/python-async-concurrency/13-event-loop/index.md)。
- 33：规划单元，待从旧课拆分或补写。材料：[15 · Future、回调与跨线程事件循环](../content/projects/python-async-concurrency/13-event-loop/index.md)。
- 34：规划单元，待从旧课拆分或补写。材料：[15 · Future、回调与跨线程事件循环](../content/projects/python-async-concurrency/13-event-loop/index.md)。
- 35：规划单元，待从旧课拆分或补写。材料：[15 · Future、回调与跨线程事件循环](../content/projects/python-async-concurrency/13-event-loop/index.md)。

</details>

</details>

<details id="curriculum-stage-processes">
<summary>模块 8 · 进程与外部命令（36–40）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 36 · 运行并等待外部命令 | 一次性运行外部程序时，如何取得退出结果？ | `subprocess.run` | 26、31 |
| 37 · 启动命令并收集管道输出 | 想在启动后继续安排事情，再收集输出怎么办？ | `subprocess.Popen`、`subprocess.Popen.communicate` | 36 |
| 38 · 命令超时后的回收 | 等待超时或发出终止请求，等不等于进程已经结束？ | `subprocess.Popen.wait`、`subprocess.Popen.terminate`、`subprocess.Popen.kill` | 09、10、37 |
| 39 · 让 Python 工作在子进程执行 | 怎样启动另一份 Python 工作，并确认它退出？ | `multiprocessing.Process`、`multiprocessing.Process.start`、`multiprocessing.Process.is_alive`、`multiprocessing.Process.join` | 26、38 |
| 40 · 结束 Python 子进程并完成回收 | 进程没有按约定结束时，怎样请求终止并等到退出？ | `multiprocessing.Process.terminate`、`multiprocessing.Process.kill` | 38、39 |

<details>
<summary>本模块的原子结论与自查</summary>

### 36 · 运行并等待外部命令

1. **带走：** run 等待外部程序结束；它是同步接口，需要注意调用线程。
2. **自查：** 指出外部进程与当前 Python 线程的不同，并读取退出结果。

### 37 · 启动命令并收集管道输出

1. **带走：** Popen 创建进程后返回句柄，communicate 处理管道通信并等待结束。
2. **自查：** 说明为什么带管道时不能只等退出而不消费输出。

### 38 · 命令超时后的回收

1. **带走：** 超时与终止请求都不代替最终等待；带管道的工作还需完成通信收尾。
2. **自查：** 按超时、终止、必要时强制结束、等待回收检查句柄。
3. **需要辨认的异常：** `subprocess.TimeoutExpired`。

### 39 · 让 Python 工作在子进程执行

1. **带走：** Process 对象负责 Python 子进程的启动和等待，线程对象与进程对象不能混为一谈。
2. **自查：** 用顶层 target 和入口保护启动，区分 join 超时与已退出。

说明运行平台和 Python 版本的默认启动方式；显式启动上下文与进程池保留为清单外按需补充。

### 40 · 结束 Python 子进程并完成回收

1. **带走：** terminate/kill 发出终止动作，join 确认退出；强制终止不保证目标 finally 或共享资源完整。
2. **自查：** 区分合作退出与强制结束，并验证自己启动的进程不再存活。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 36：规划单元，待从旧课拆分或补写。材料：[14 · 进程池、子进程与系统边界](../content/projects/python-async-concurrency/12-processes/index.md)、[20 · 进程生命周期：从队列工作到超时回收](../content/projects/python-async-concurrency/18-process-lifecycle/index.md)。
- 37：规划单元，待从旧课拆分或补写。材料：[20 · 进程生命周期：从队列工作到超时回收](../content/projects/python-async-concurrency/18-process-lifecycle/index.md)。
- 38：规划单元，待从旧课拆分或补写。材料：[20 · 进程生命周期：从队列工作到超时回收](../content/projects/python-async-concurrency/18-process-lifecycle/index.md)。
- 39：规划单元，待从旧课拆分或补写。材料：[20 · 进程生命周期：从队列工作到超时回收](../content/projects/python-async-concurrency/18-process-lifecycle/index.md)。
- 40：规划单元，待从旧课拆分或补写。材料：[20 · 进程生命周期：从队列工作到超时回收](../content/projects/python-async-concurrency/18-process-lifecycle/index.md)。

</details>

</details>

## API 到正式讲解单元的检查表

| API | 正式讲解单元 |
| --- | --- |
| `asyncio.run` | 01 · 定义、创建与运行协程 |
| `asyncio.sleep` | 02 · 在协程内部等待 |
| `asyncio.create_task` | 03 · 先安排多份任务 |
| `asyncio.TaskGroup` | 04 · 让代码块负责等完任务 |
| `asyncio.TaskGroup.create_task` | 04 · 让代码块负责等完任务 |
| `asyncio.gather` | 05 · 收集整组返回值 |
| `asyncio.wait` | 06 · 先取得完成情况 |
| `asyncio.as_completed` | 08 · 按完成顺序取结果 |
| `asyncio.Task.done` | 07 · 读取 Task 的状态与结果 |
| `asyncio.Task.result` | 07 · 读取 Task 的状态与结果 |
| `asyncio.Task.exception` | 07 · 读取 Task 的状态与结果 |
| `asyncio.Task.cancel` | 09 · 请求取消并等到退出 |
| `asyncio.Future.done` | 34 · 读取 asyncio Future 的结果 |
| `asyncio.Future.result` | 34 · 读取 asyncio Future 的结果 |
| `asyncio.Future.exception` | 34 · 读取 asyncio Future 的结果 |
| `asyncio.wait_for` | 10 · 限制一次等待的时长 |
| `asyncio.timeout` | 12 · 给一段异步代码共享时间预算 |
| `asyncio.shield` | 13 · 区分取消等待者与内部工作 |
| `builtins.TimeoutError` | 10 · 限制一次等待的时长 |
| `asyncio.Semaphore` | 16 · 限制同时进入的工作 |
| `asyncio.Semaphore.acquire` | 16 · 限制同时进入的工作 |
| `asyncio.Semaphore.release` | 16 · 限制同时进入的工作 |
| `asyncio.Queue` | 17 · 让生产者与消费者交接数据 |
| `asyncio.Queue.put` | 17 · 让生产者与消费者交接数据 |
| `asyncio.Queue.get` | 17 · 让生产者与消费者交接数据 |
| `asyncio.Lock` | 18 · 保护跨 await 的共享状态 |
| `asyncio.Lock.acquire` | 18 · 保护跨 await 的共享状态 |
| `asyncio.Lock.release` | 18 · 保护跨 await 的共享状态 |
| `asyncio.Event` | 19 · 让任务等待一个通知 |
| `asyncio.Event.set` | 19 · 让任务等待一个通知 |
| `asyncio.Event.wait` | 19 · 让任务等待一个通知 |
| `asyncio.Event.clear` | 19 · 让任务等待一个通知 |
| `asyncio.to_thread` | 25 · 把阻塞函数交给线程 |
| `concurrent.futures.ThreadPoolExecutor` | 30 · 把工作提交到线程池 |
| `concurrent.futures.Executor.submit` | 30 · 把工作提交到线程池 |
| `concurrent.futures.Executor.shutdown` | 31 · 结束线程池并处理未执行工作 |
| `concurrent.futures.Future.result` | 30 · 把工作提交到线程池 |
| `concurrent.futures.Future.done` | 30 · 把工作提交到线程池 |
| `concurrent.futures.Future.exception` | 30 · 把工作提交到线程池 |
| `concurrent.futures.Future.cancel` | 31 · 结束线程池并处理未执行工作 |
| `threading.Thread` | 26 · 创建、启动并等待线程 |
| `threading.Thread.start` | 26 · 创建、启动并等待线程 |
| `threading.Thread.join` | 26 · 创建、启动并等待线程 |
| `threading.Thread.is_alive` | 26 · 创建、启动并等待线程 |
| `threading.Lock` | 27 · 保护线程共享状态 |
| `threading.Lock.acquire` | 27 · 保护线程共享状态 |
| `threading.Lock.release` | 27 · 保护线程共享状态 |
| `threading.Event` | 28 · 通知线程合作退出 |
| `threading.Event.set` | 28 · 通知线程合作退出 |
| `threading.Event.wait` | 28 · 通知线程合作退出 |
| `threading.Event.clear` | 28 · 通知线程合作退出 |
| `queue.Queue` | 29 · 在线程之间交接数据 |
| `queue.Queue.put` | 29 · 在线程之间交接数据 |
| `queue.Queue.get` | 29 · 在线程之间交接数据 |
| `queue.Queue.get_nowait` | 29 · 在线程之间交接数据 |
| `contextvars.ContextVar` | 23 · 保存每份任务自己的上下文 |
| `contextvars.ContextVar.get` | 23 · 保存每份任务自己的上下文 |
| `contextvars.ContextVar.set` | 23 · 保存每份任务自己的上下文 |
| `contextvars.ContextVar.reset` | 23 · 保存每份任务自己的上下文 |
| `contextlib.asynccontextmanager` | 20 · 把异步资源绑定到作用域 |
| `contextlib.aclosing` | 22 · 提前停止异步迭代 |
| `inspect.isawaitable` | 24 · 辨认函数与可等待对象 |
| `inspect.iscoroutinefunction` | 24 · 辨认函数与可等待对象 |
| `asyncio.get_running_loop` | 32 · 从协程使用指定执行器 |
| `asyncio.AbstractEventLoop.run_in_executor` | 32 · 从协程使用指定执行器 |
| `asyncio.wrap_future` | 33 · 等待已有的执行器 Future |
| `asyncio.run_coroutine_threadsafe` | 35 · 从另一个线程提交协程 |
| `multiprocessing.Process` | 39 · 让 Python 工作在子进程执行 |
| `multiprocessing.Process.start` | 39 · 让 Python 工作在子进程执行 |
| `multiprocessing.Process.is_alive` | 39 · 让 Python 工作在子进程执行 |
| `multiprocessing.Process.join` | 39 · 让 Python 工作在子进程执行 |
| `multiprocessing.Process.terminate` | 40 · 结束 Python 子进程并完成回收 |
| `multiprocessing.Process.kill` | 40 · 结束 Python 子进程并完成回收 |
| `subprocess.run` | 36 · 运行并等待外部命令 |
| `subprocess.Popen` | 37 · 启动命令并收集管道输出 |
| `subprocess.Popen.communicate` | 37 · 启动命令并收集管道输出 |
| `subprocess.Popen.wait` | 38 · 命令超时后的回收 |
| `subprocess.Popen.terminate` | 38 · 命令超时后的回收 |
| `subprocess.Popen.kill` | 38 · 命令超时后的回收 |
| `time.sleep` | 25 · 把阻塞函数交给线程 |
| `time.monotonic` | 11 · 计量经过时间与预算 |
| `time.perf_counter` | 11 · 计量经过时间与预算 |

## 语法与异常的检查表

| 类别 | 内容 | 单元 |
| --- | --- | --- |
| 语法 | `async def` | 01 |
| 语法 | `await` | 02 |
| 语法 | `async with` | 04 |
| 语法 | `async for` | 21 |
| 语法 | `异步生成器中的 yield` | 21 |
| 语法 | `try/finally` | 09 |
| 语法 | `except*` | 15 |
| 异常类型 | `asyncio.CancelledError` | 09 |
| 异常类型 | `asyncio.InvalidStateError` | 07 |
| 异常类型 | `concurrent.futures.CancelledError` | 31 |
| 异常类型 | `concurrent.futures.TimeoutError` | 30 |
| 异常类型 | `queue.Empty` | 29 |
| 异常类型 | `queue.Full` | 29 |
| 异常类型 | `subprocess.TimeoutExpired` | 38 |
| 异常类型 | `builtins.ExceptionGroup` | 15 |

检查保证所有输入 API 各有一个正式引入单元，语法与异常类型无遗漏，前置只指向更早单元。它不证明待编写课程的正文已经实现了这些讲解。

```bash
python3 python-async-reference/tools/build_curriculum.py
python3 python-async-reference/tools/build_curriculum.py --check
```
