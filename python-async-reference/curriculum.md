# Python 原生异步与并发：完整课程设置

**8 个模块，41 个编号单元，覆盖 82/82 项调用与方法。**

这是课程规划，不是 41 篇都已编写完成的声明。各单元编写状态见下表。旧版 23 页目录保留历史编号，既有 URL 保留；现行单元号以本课程表为准。

输入范围：[82 项 API](current-api-plan.md)；唯一课程数据：[curriculum.json](curriculum.json)。课程按概念递进；每学完一个模块完成对应自查，不要求先记住整张清单。

## 阅读与完成规则

1. 01–20 已整理为独立阅读内容；21–41 是后续拆分与补写计划，不表示已写完。
2. 现行编号按确认后的概念依赖排序；10、11 各有两个独立子课。既有页面 URL 和旧版 23 页目录的历史编号保留，不能按 URL 数字前缀推断新课号。
3. 每个 API 有一个正式引入单元；后面的复用与回访不重复计数。
4. 完成整套课程时覆盖全部 82 项；按单元逐步学习，不要求一次学完，也不把清单内内容无限期留作选读。清单外内容仍按需。
5. 每单元先写前课结论，再给新增要求；机制实验只增加当前必要关系。纯语法前置的结构示意标明不能直接运行，再由下一单元的完整实验验证。
6. 模块结束能解释该模块的正常、失败或退出行为；全课结束再串联一个只含已学原生机制的综合例子。
7. API 正式讲解必须解释对象、调用时机、返回值以及必要的等待/异常/退出边界；仅在代码中出现不算完成讲解。

## 分阶段课程

| 模块 | 学习单元 | 每阶段先解决什么 | 首次正式讲解的 API 数 |
| --- | --- | --- | ---: |
| 1. 协程与任务基础 | 01–06 | 创建 → 内部等待 → 安排 → 进入与退出 → 分组 → 收集结果 | 6 |
| 2. 任务状态、失败与收尾 | 07–12 | 完成情况 → 状态 → 取消 → 整组失败 → 按完成顺序取结果 | 6 |
| 3. 超时与时间预算 | 13–16 | 单次时限 → 计时 → 共享预算 → 取消传播边界 | 6 |
| 4. 协程之间的协调 | 17–20 | 分别解决许可、数据交接、互斥与通知 | 13 |
| 5. 异步资源、迭代与上下文 | 21–25 | 先说明作用域与产出，再解释关闭、隔离和对象检查 | 8 |
| 6. 线程与执行器 | 26–32 | 从阻塞函数到线程，再到线程池和退出 | 24 |
| 7. 协程与线程的交接 | 33–36 | 区分 Future 类型以及跨线程提交方向 | 7 |
| 8. 进程与外部命令 | 37–41 | 先运行与取输出，再处理终止和回收 | 12 |

下面按模块展开。每个单元都列出唯一问题、正式引入的 API、前置和自查；同一 API 后续复用不重复计数。

<details id="curriculum-stage-coroutines">
<summary>模块 1 · 协程与任务基础（01–06）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 01 · async def：定义之后，什么时候执行？ | 调用 async def 定义的函数后，函数体已经运行了吗？ | `asyncio.run`、`async def` | 普通函数基础 |
| 02 · await：等待结果，不等于自动并发 | 已经在协程里，怎样等待另一份工作的结果？ | `asyncio.sleep`、`await` | 01 |
| 03 · create_task：先安排工作，再等待结果 | 怎样让两份独立工作在等待期间都能推进？ | `asyncio.create_task` | 02 |
| 04 · with / async with：进入、执行与退出 | 怎样把读文件后的关闭操作交给代码块的退出过程？ | `async with` | 03 |
| 05 · TaskGroup：离开代码块前，等任务结束 | 怎样给一组任务一个明确的结束位置？ | `asyncio.TaskGroup`、`asyncio.TaskGroup.create_task` | 03、04 |
| 06 · gather：等待一组任务，收集一组结果 | 怎样把这组任务的结果一次收齐？ | `asyncio.gather` | 03、05 |

<details>
<summary>本模块的原子结论与自查</summary>

### 01 · async def：定义之后，什么时候执行？

1. **带走：** 定义产生协程函数，调用产生协程对象，运行入口才驱动它执行。
2. **自查：** 预测创建协程与运行协程时分别会打印什么。

### 02 · await：等待结果，不等于自动并发

1. **带走：** await 等待对象完成；等待未完成的异步操作时，当前任务可以挂起。
2. **自查：** 沿两次直接 await 预测执行顺序。

### 03 · create_task：先安排工作，再等待结果

1. **带走：** create_task 安排协程；调用方在后续挂起时，事件循环可以运行已安排的任务。
2. **自查：** 分清安排顺序、完成顺序与 await 取值顺序。

现有计时展示使用 time.perf_counter；这里只说明用于显示经过时间，第 14 单元正式解释。

### 04 · with / async with：进入、执行与退出

1. **带走：** with 将进入和退出绑定到代码块；as 接收进入结果；async with 的进入和退出允许异步等待，但不会让块内自动并发。
2. **自查：** 运行文件读取例子，解释块内 closed 为 False、块外为 True，再说明 async with 的进入与退出可以等待。

先用 open/read/close 的具体文件例子建立正常进入与退出，再认识异步形式；不引入类、装饰器或协议实现。第 05 单元用 TaskGroup 验证异步退出，资源协议留到第 21 单元。

### 05 · TaskGroup：离开代码块前，等任务结束

1. **带走：** 正常退出 TaskGroup 的代码块前，会等完组内任务。
2. **自查：** 预测代码块之后的输出能否先于组内任务结束。

先读第 04 单元的 with / async with 结构，再用本单元实验观察正常退出时等待任务。

### 06 · gather：等待一组任务，收集一组结果

1. **带走：** 正常完成时，gather 按传入顺序给出结果列表。
2. **自查：** 任务反向完成时，预测结果列表的顺序。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 01：已有独立学习主线。材料：[01 · async def：定义之后，什么时候执行？](../content/projects/python-async-concurrency/01-async-def/index.md)。
- 02：已有独立学习主线。材料：[02 · await：等待结果，不等于自动并发](../content/projects/python-async-concurrency/02-await/index.md)。
- 03：已有独立学习主线。材料：[03 · create_task：先安排工作，再等待结果](../content/projects/python-async-concurrency/03-tasks/index.md)。
- 04：已有独立学习主线。材料：[04 · with / async with：进入、执行与退出](../content/projects/python-async-concurrency/04-with-async-with/index.md)。
- 05：已有独立学习主线。材料：[05 · TaskGroup：离开代码块前，等任务结束](../content/projects/python-async-concurrency/04-taskgroup/index.md)。
- 06：已有独立学习主线。材料：[06 · gather：等待一组任务，收集一组结果](../content/projects/python-async-concurrency/05-gather/index.md)。

</details>

</details>

<details id="curriculum-stage-results">
<summary>模块 2 · 任务状态、失败与收尾（07–12）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 07 · wait：先取得任务的完成情况 | 不等全部结束，怎样先知道哪些任务完成了？ | `asyncio.wait` | 06 |
| 08 · done、result、exception：读取 Task 的状态与结果 | Task 对象与它保存的返回值、异常有什么区别？ | `asyncio.Task.done`、`asyncio.Task.result`、`asyncio.Task.exception` | 07 |
| 09 · Task.cancel：请求取消并等待收尾 | 发出取消请求以后，怎样确认任务收尾了？ | `asyncio.Task.cancel`、`try/finally` | 08 |
| 10.1 · asyncio.gather：收集报错，任务仍可继续 | 一份任务报错，是否会让其他已创建的 Task 停止？ | 回访 `asyncio.gather` | 06、08、09 |
| 10.2 · return_exceptions=True：收齐结果与异常 | 有一份任务失败，也想一次收齐每份的成功或失败情况，怎么办？ | 回访 `asyncio.gather` | 10.1 |
| 11.1 · TaskGroup：一个任务失败，取消其余未完成任务并等待收尾 | 一份任务失败以后，谁取消并等完其他任务？ | 回访 `asyncio.TaskGroup`、`asyncio.TaskGroup.create_task` | 05、09、10 |
| 11.2 · ExceptionGroup / except*：读取任务组的错误 | TaskGroup 收尾后报告的整组错误，怎样读取和按类型处理？ | `except*`；回访 `asyncio.TaskGroup`、`asyncio.TaskGroup.create_task` | 11.1 |
| 12 · asyncio.as_completed：按完成顺序取结果 | 怎样依次处理先完成的工作？ | `asyncio.as_completed` | 07、08 |

<details>
<summary>本模块的原子结论与自查</summary>

### 07 · wait：先取得任务的完成情况

1. **带走：** wait 返回完成与未完成的任务集合，未完成的任务不会因此停止。
2. **自查：** 用已知 await 读取 done 中任务并等完 pending，暂不引入 as_completed。

### 08 · done、result、exception：读取 Task 的状态与结果

1. **带走：** done 判断是否结束；result 读取值或抛出保存的异常，exception 读取保存的异常。
2. **自查：** 分别预测未完成、成功和失败任务的读取结果。
3. **需要辨认的异常：** `asyncio.InvalidStateError`。

只观察任务状态与正常/异常结束；取消状态在第 09 单元再加入。

### 09 · Task.cancel：请求取消并等待收尾

1. **带走：** cancel 请求取消；继续等待任务，才能观察它处理取消并执行已进入的 finally。
2. **自查：** 让任务先进入等待，再取消，确认清理和取消传播的顺序。
3. **需要辨认的异常：** `asyncio.CancelledError`。

### 10.1 · asyncio.gather：收集报错，任务仍可继续

1. **带走：** 默认 gather 提前报告子任务的普通异常，但不因此取消其他 Task；调用方继续负责等待和读取。
2. **自查：** 解释为什么 gather error 后仍有 finished 10，最后的 await 是否会重启任务。

### 10.2 · return_exceptions=True：收齐结果与异常

1. **带走：** return_exceptions=True 把返回值和普通任务异常按传入顺序收进列表；调用方仍需检查失败。
2. **自查：** 指出列表中哪一项对应失败任务，并说明返回列表为什么不等于全部成功。

### 11.1 · TaskGroup：一个任务失败，取消其余未完成任务并等待收尾

1. **带走：** 普通子任务异常触发 TaskGroup 取消其余未完成任务，等待收尾后再向外报告整组错误。
2. **自查：** 解释为什么先看到任务 10 的 cleanup，再看到 group failed。

### 11.2 · ExceptionGroup / except*：读取任务组的错误

1. **带走：** ExceptionGroup 保存一组异常，except* 按内部异常类型匹配子组；子组的 exceptions 是异常对象组成的元组。
2. **自查：** 辨认 except* 捕获的子组与其中的 ValueError，并解释未匹配的错误如何传播。
3. **需要辨认的异常：** `builtins.ExceptionGroup`。

### 12 · asyncio.as_completed：按完成顺序取结果

1. **带走：** as_completed 提供按完成推进的等待入口，与 gather 的传入顺序结果不同。
2. **自查：** 说明为何先完成的任务可以先被处理。

主例子使用 Python 3.12 的普通 for 加 await 写法；新版本 async for 写法不作前置。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 07：已有独立学习主线。材料：[07 · wait：先取得任务的完成情况](../content/projects/python-async-concurrency/04-results/index.md)。
- 08：已有独立学习主线。材料：[08 · done、result、exception：读取 Task 的状态与结果](../content/projects/python-async-concurrency/07-task-results/index.md)。
- 09：已有独立学习主线。材料：[09 · Task.cancel：请求取消并等待收尾](../content/projects/python-async-concurrency/09-task-cancellation/index.md)。
- 10.1：已有独立学习主线。材料：[10.1 · asyncio.gather：收集报错，任务仍可继续](../content/projects/python-async-concurrency/15-gather-failures/index.md)。
- 10.2：已有独立学习主线。材料：[10.2 · return_exceptions=True：收齐结果与异常](../content/projects/python-async-concurrency/15-gather-exceptions/index.md)。
- 11.1：已有独立学习主线。材料：[11.1 · TaskGroup：一个任务失败，取消其余未完成任务并等待收尾](../content/projects/python-async-concurrency/11-taskgroup-failures/index.md)。
- 11.2：已有独立学习主线。材料：[11.2 · ExceptionGroup / except*：读取任务组的错误](../content/projects/python-async-concurrency/11-exception-groups/index.md)。
- 12：已有独立学习主线。材料：[12 · asyncio.as_completed：按完成顺序取结果](../content/projects/python-async-concurrency/08-as-completed/index.md)。

</details>

</details>

<details id="curriculum-stage-cancellation">
<summary>模块 3 · 超时与时间预算（13–16）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 13 · asyncio.wait_for：限制一次等待的时长 | 这次等待超过预算时，取消和异常怎样发生？ | `asyncio.wait_for`、`builtins.TimeoutError` | 09 |
| 14 · time.monotonic / time.perf_counter：计量经过时间与预算 | 怎样度量等待耗时，而不把时钟读数当成调度顺序？ | `time.monotonic`、`time.perf_counter` | 13 |
| 15 · asyncio.timeout：给一段异步代码共享时间预算 | 多个 await 怎样共用一个超时边界？ | `asyncio.timeout` | 05、13、14 |
| 16 · asyncio.shield：区分取消等待者与内部工作 | 调用方取消时，有没有需要继续负责等完的工作？ | `asyncio.shield` | 09、13、15 |

<details>
<summary>本模块的原子结论与自查</summary>

### 13 · asyncio.wait_for：限制一次等待的时长

1. **带走：** wait_for 通常取消等待对象并等它处理取消；TimeoutError 表达超时失败。
2. **自查：** 解释为什么清理会让总耗时超过指定 timeout，并给出自定义超时异常信息。

### 14 · time.monotonic / time.perf_counter：计量经过时间与预算

1. **带走：** 用单调时钟计算时间差与截止预算；计时本身不驱动任务。
2. **自查：** 分别标出开始、结束与剩余预算，不用墙钟误差推断并发先后。

正式解释第 3–6 单元展示时间戳时使用的 perf_counter；不引入通用性能分析课程。

### 15 · asyncio.timeout：给一段异步代码共享时间预算

1. **带走：** timeout 管理代码块的时间预算，超时异常在其作用域外处理。
2. **自查：** 比较每次 wait_for 单独计时与整个代码块共用预算。

### 16 · asyncio.shield：区分取消等待者与内部工作

1. **带走：** shield 阻断这一层取消传播，外层仍可取消，内部工作仍须有人持有并收尾。
2. **自查：** 指出外层取消后仍存活的任务由谁等待、谁读取错误。

主例子承接第 15 单元，用作用域预算观察外层取消；shield 本身也可用于其他已学等待方式。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 13：已有独立学习主线。材料：[13 · asyncio.wait_for：限制一次等待的时长](../content/projects/python-async-concurrency/10-wait-for/index.md)。
- 14：已有独立学习主线。材料：[14 · time.monotonic / time.perf_counter：计量经过时间与预算](../content/projects/python-async-concurrency/11-time-budget/index.md)。
- 15：已有独立学习主线。材料：[15 · asyncio.timeout：给一段异步代码共享时间预算](../content/projects/python-async-concurrency/12-timeout-scope/index.md)。
- 16：已有独立学习主线。材料：[16 · asyncio.shield：区分取消等待者与内部工作](../content/projects/python-async-concurrency/13-shield/index.md)。

</details>

</details>

<details id="curriculum-stage-coordination">
<summary>模块 4 · 协程之间的协调（17–20）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 17 · asyncio.Semaphore：限制同时进入的工作 | 任务都已安排后，怎样只允许少量工作进入？ | `asyncio.Semaphore`、`asyncio.Semaphore.acquire`、`asyncio.Semaphore.release` | 05、09 |
| 18 · asyncio.Queue：让生产者与消费者交接数据 | 生产快、消费慢时，数据怎样有界地等待？ | `asyncio.Queue`、`asyncio.Queue.put`、`asyncio.Queue.get` | 03、09、17 |
| 19 · asyncio.Lock：保护跨 await 的共享状态 | 多份任务会交错修改同一状态时怎么办？ | `asyncio.Lock`、`asyncio.Lock.acquire`、`asyncio.Lock.release` | 05、09、18 |
| 20 · asyncio.Event：让任务等待一个通知 | 没有数据要传，只需要通知其他任务继续，怎么办？ | `asyncio.Event`、`asyncio.Event.set`、`asyncio.Event.wait`、`asyncio.Event.clear` | 18、19 |

<details>
<summary>本模块的原子结论与自查</summary>

### 17 · asyncio.Semaphore：限制同时进入的工作

1. **带走：** 许可数限制进入受控区域的工作，退出时归还许可。
2. **自查：** 记录进入区域的最大数量，并验证异常后许可可重新取得。

### 18 · asyncio.Queue：让生产者与消费者交接数据

1. **带走：** 有界 Queue 在满时等待 put、空时等待 get，连接生产与消费。
2. **自查：** 区分排队容量与在途数量，并说明结束信号由应用约定。

### 19 · asyncio.Lock：保护跨 await 的共享状态

1. **带走：** 同一事件循环中的 Lock 保护约定的共享操作，获取等待可以挂起任务。
2. **自查：** 指出需要保护的读改写范围，以及退出时谁释放锁。

### 20 · asyncio.Event：让任务等待一个通知

1. **带走：** Event 保存一个可设置和清除的标志，wait 等待标志为真；它不是计数队列。
2. **自查：** 预测 set、wait、clear 对后续等待者的影响。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 17：已有独立学习主线。材料：[17 · asyncio.Semaphore：限制同时进入的工作](../content/projects/python-async-concurrency/06-semaphore/index.md)。
- 18：已有独立学习主线。材料：[18 · asyncio.Queue：让生产者与消费者交接数据](../content/projects/python-async-concurrency/07-queues/index.md)。
- 19：已有独立学习主线。材料：[19 · asyncio.Lock：保护跨 await 的共享状态](../content/projects/python-async-concurrency/19-async-lock/index.md)。
- 20：已有独立学习主线。材料：[20 · asyncio.Event：让任务等待一个通知](../content/projects/python-async-concurrency/20-async-event/index.md)。

</details>

</details>

<details id="curriculum-stage-protocols">
<summary>模块 5 · 异步资源、迭代与上下文（21–25）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 21 · async with / contextlib.asynccontextmanager：把异步资源绑定到作用域 | 资源使用结束或报错后，怎样统一关闭？ | `contextlib.asynccontextmanager` | 05、09 |
| 22 · async for / 异步生成器：逐项等待异步产出 | 结果是一项项到来的，怎样逐项消费？ | `async for`、`异步生成器中的 yield` | 02、21 |
| 23 · contextlib.aclosing：提前停止异步迭代 | 循环 break 之后，怎样让生成器及时清理？ | `contextlib.aclosing` | 09、21、22 |
| 24 · contextvars.ContextVar：保存每份任务自己的上下文 | 并发任务怎样各自读取并恢复临时值？ | `contextvars.ContextVar`、`contextvars.ContextVar.get`、`contextvars.ContextVar.set`、`contextvars.ContextVar.reset` | 03、09、21 |
| 25 · inspect.isawaitable / inspect.iscoroutinefunction：辨认函数与可等待对象 | 一个函数调用之后，究竟应不应该 await 返回值？ | `inspect.isawaitable`、`inspect.iscoroutinefunction` | 02、22 |

<details>
<summary>本模块的原子结论与自查</summary>

### 21 · async with / contextlib.asynccontextmanager：把异步资源绑定到作用域

1. **带走：** asynccontextmanager 将准备、yield 使用与 finally 清理组织成异步作用域。
2. **自查：** 沿正常、异常与取消路径指出已进入资源的清理位置。

若普通 with、生成器 yield 或装饰器尚不熟悉，先用最小前置例子解释，不混入主例子的新机制。

### 22 · async for / 异步生成器：逐项等待异步产出

1. **带走：** 含 yield 的 async def 产生异步生成器；async for 逐项等待，不自动并行循环体。
2. **自查：** 区分 await 一次结果与 async for 多次取项。

### 23 · contextlib.aclosing：提前停止异步迭代

1. **带走：** aclosing 将异步生成器的关闭绑定到使用它的作用域退出。
2. **自查：** 提前停止消费，确认生成器已进入的 finally 被执行。

### 24 · contextvars.ContextVar：保存每份任务自己的上下文

1. **带走：** ContextVar 保存上下文中的绑定，set 的 token 用于恢复先前状态。
2. **自查：** 验证两个任务与嵌套作用域的值，并区分绑定隔离与共享可变对象。

### 25 · inspect.isawaitable / inspect.iscoroutinefunction：辨认函数与可等待对象

1. **带走：** 函数形状与返回对象是不同证据；isawaitable 检查对象，不执行它。
2. **自查：** 对比 async def、普通值和普通函数返回协程三种情况。

Awaitable/AsyncIterator 注解仅按需说明，注解不会执行或验证对象。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 21：规划单元，待从旧课拆分或补写。材料：[12 · async with、async for 与异步生成器](../content/projects/python-async-concurrency/10-async-protocols/index.md)。
- 22：规划单元，待从旧课拆分或补写。材料：[12 · async with、async for 与异步生成器](../content/projects/python-async-concurrency/10-async-protocols/index.md)。
- 23：规划单元，待从旧课拆分或补写。材料：[23 · 异步能力检查与协议边界](../content/projects/python-async-concurrency/21-async-inspection/index.md)。
- 24：规划单元，待从旧课拆分或补写。材料：[13 · ContextVar：让并发任务保留各自的上下文](../content/projects/python-async-concurrency/11-contextvars/index.md)。
- 25：规划单元，待从旧课拆分或补写。材料：[23 · 异步能力检查与协议边界](../content/projects/python-async-concurrency/21-async-inspection/index.md)。

</details>

</details>

<details id="curriculum-stage-threads">
<summary>模块 6 · 线程与执行器（26–32）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 26 · asyncio.to_thread：把阻塞函数交给线程 | 同步等待会占住事件循环线程时怎么办？ | `asyncio.to_thread`、`time.sleep` | 03、09、24 |
| 27 · threading.Thread：创建、启动并等待线程 | 线程对象创建以后，何时开始，怎样等到退出？ | `threading.Thread`、`threading.Thread.start`、`threading.Thread.is_alive`、`threading.Thread.join` | 26 |
| 28 · threading.Lock：保护线程共享状态 | 多个线程同时修改共享数据时怎样互斥？ | `threading.Lock`、`threading.Lock.acquire`、`threading.Lock.release` | 19、27 |
| 29 · threading.Event：通知线程合作退出 | 线程需要收到停止请求时怎样安排？ | `threading.Event`、`threading.Event.set`、`threading.Event.wait`、`threading.Event.clear` | 20、27、28 |
| 30 · queue.Queue：在线程之间交接数据 | 同步队列怎样等待数据，或立即尝试取数？ | `queue.Queue`、`queue.Queue.put`、`queue.Queue.get`、`queue.Queue.get_nowait` | 18、27、29 |
| 31 · ThreadPoolExecutor / submit：把工作提交到线程池 | 不手动创建每个线程，怎样取得已提交工作的结果？ | `concurrent.futures.ThreadPoolExecutor`、`concurrent.futures.Executor.submit`、`concurrent.futures.Future.done`、`concurrent.futures.Future.result`、`concurrent.futures.Future.exception` | 08、27、28 |
| 32 · Future.cancel / Executor.shutdown：结束线程池并处理未执行工作 | 退出执行器时，排队工作和运行中工作分别怎么办？ | `concurrent.futures.Future.cancel`、`concurrent.futures.Executor.shutdown` | 09、29、31 |

<details>
<summary>本模块的原子结论与自查</summary>

### 26 · asyncio.to_thread：把阻塞函数交给线程

1. **带走：** to_thread 让同步函数在线程中执行；取消等待者不会强杀已开始的线程工作。
2. **自查：** 比较 time.sleep 与 asyncio.sleep，并观察 to_thread 的上下文传播。

### 27 · threading.Thread：创建、启动并等待线程

1. **带走：** start 启动线程，is_alive 观察存活状态，join 等待退出而不是请求停止。
2. **自查：** 辨认创建、启动、执行、join 返回四个阶段。

### 28 · threading.Lock：保护线程共享状态

1. **带走：** 线程 Lock 在获取失败时阻塞调用线程，配对释放保护共享操作。
2. **自查：** 与 asyncio.Lock 比较等待位置，并验证共享计数。

### 29 · threading.Event：通知线程合作退出

1. **带走：** Event 传递线程间标志；线程需要合作检查，join 才负责等待退出。
2. **自查：** 按设置标志、线程结束、join 返回的顺序核对。

### 30 · queue.Queue：在线程之间交接数据

1. **带走：** queue.Queue 为线程交接提供同步等待；get_nowait 为空时抛 Empty。
2. **自查：** 区分空队列等待、非阻塞取数，以及有界 put 的 Full。
3. **需要辨认的异常：** `queue.Empty`、`queue.Full`。

### 31 · ThreadPoolExecutor / submit：把工作提交到线程池

1. **带走：** submit 返回执行器 Future；result 可以阻塞调用线程，成功值与失败异常由 Future 保存。
2. **自查：** 说明它与 asyncio Task 的相似点，以及为何不能直接 await 它。
3. **需要辨认的异常：** `concurrent.futures.TimeoutError`。

### 32 · Future.cancel / Executor.shutdown：结束线程池并处理未执行工作

1. **带走：** Future.cancel 不能强停已运行的工作，shutdown 决定等待及未开始工作的处理。
2. **自查：** 分别检查排队取消、运行中取消失败与最终退出。
3. **需要辨认的异常：** `concurrent.futures.CancelledError`。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 26：规划单元，待从旧课拆分或补写。材料：[10 · 线程池：把阻塞工作移出事件循环](../content/projects/python-async-concurrency/08-executors/index.md)、[03 · create_task：先安排工作，再等待结果](../content/projects/python-async-concurrency/03-tasks/index.md)。
- 27：规划单元，待从旧课拆分或补写。材料：[11 · Lock、Event 与线程退出](../content/projects/python-async-concurrency/09-thread-synchronization/index.md)。
- 28：规划单元，待从旧课拆分或补写。材料：[11 · Lock、Event 与线程退出](../content/projects/python-async-concurrency/09-thread-synchronization/index.md)。
- 29：规划单元，待从旧课拆分或补写。材料：[11 · Lock、Event 与线程退出](../content/projects/python-async-concurrency/09-thread-synchronization/index.md)。
- 30：规划单元，待从旧课拆分或补写。材料：[18 · asyncio.Queue：让生产者与消费者交接数据](../content/projects/python-async-concurrency/07-queues/index.md)。
- 31：规划单元，待从旧课拆分或补写。材料：[10 · 线程池：把阻塞工作移出事件循环](../content/projects/python-async-concurrency/08-executors/index.md)、[19 · 线程池 Future 的结果与退出](../content/projects/python-async-concurrency/17-executor-results/index.md)。
- 32：规划单元，待从旧课拆分或补写。材料：[19 · 线程池 Future 的结果与退出](../content/projects/python-async-concurrency/17-executor-results/index.md)。

</details>

</details>

<details id="curriculum-stage-bridges">
<summary>模块 7 · 协程与线程的交接（33–36）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 33 · loop.run_in_executor：从协程使用指定执行器 | 已经选定线程池，怎样提交并用 await 等结果？ | `asyncio.get_running_loop`、`asyncio.AbstractEventLoop.run_in_executor` | 26、31 |
| 34 · asyncio.wrap_future：等待已有的执行器 Future | 已经拿到执行器 Future，怎样接入协程等待？ | `asyncio.wrap_future` | 31、33 |
| 35 · Future.done() / result() / exception()：读取 asyncio Future 的结果 | 协程接口给回一个 Future 时，怎样判断与读取？ | `asyncio.Future.done`、`asyncio.Future.result`、`asyncio.Future.exception` | 08、33、34 |
| 36 · asyncio.run_coroutine_threadsafe：从另一个线程提交协程 | 同步线程怎样把协程交给正在运行的事件循环？ | `asyncio.run_coroutine_threadsafe` | 27、29、31、33、35 |

<details>
<summary>本模块的原子结论与自查</summary>

### 33 · loop.run_in_executor：从协程使用指定执行器

1. **带走：** 从当前运行循环提交执行器工作，得到可 await 的 asyncio Future。
2. **自查：** 标出同步函数运行位置和等待者恢复位置。

### 34 · asyncio.wrap_future：等待已有的执行器 Future

1. **带走：** wrap_future 将执行器 Future 衔接为当前循环可等待的 Future，不重新提交工作。
2. **自查：** 证明被包装的工作只提交一次，并区分两类 Future。

### 35 · Future.done() / result() / exception()：读取 asyncio Future 的结果

1. **带走：** asyncio Future 的结果读取不阻塞等待，未完成时读取会失败。
2. **自查：** 对比 asyncio Future 与执行器 Future 的 result 行为。

### 36 · asyncio.run_coroutine_threadsafe：从另一个线程提交协程

1. **带走：** 跨线程提交返回执行器 Future；事件循环线程不能阻塞等待自己才能完成的工作。
2. **自查：** 画出提交线程、循环线程与结果返回的方向，排除循环等待。

主例子用 asyncio.run 持有循环并从工作线程提交；不强行把 new_event_loop/run_forever 等清单外 API 作为前置。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 33：规划单元，待从旧课拆分或补写。材料：[10 · 线程池：把阻塞工作移出事件循环](../content/projects/python-async-concurrency/08-executors/index.md)、[15 · Future、回调与跨线程事件循环](../content/projects/python-async-concurrency/13-event-loop/index.md)。
- 34：规划单元，待从旧课拆分或补写。材料：[15 · Future、回调与跨线程事件循环](../content/projects/python-async-concurrency/13-event-loop/index.md)。
- 35：规划单元，待从旧课拆分或补写。材料：[15 · Future、回调与跨线程事件循环](../content/projects/python-async-concurrency/13-event-loop/index.md)。
- 36：规划单元，待从旧课拆分或补写。材料：[15 · Future、回调与跨线程事件循环](../content/projects/python-async-concurrency/13-event-loop/index.md)。

</details>

</details>

<details id="curriculum-stage-processes">
<summary>模块 8 · 进程与外部命令（37–41）</summary>

| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |
| --- | --- | --- | --- |
| 37 · subprocess.run：运行并等待外部命令 | 一次性运行外部程序时，如何取得退出结果？ | `subprocess.run` | 27、32 |
| 38 · subprocess.Popen / communicate：启动命令并收集管道输出 | 想在启动后继续安排事情，再收集输出怎么办？ | `subprocess.Popen`、`subprocess.Popen.communicate` | 37 |
| 39 · Popen.wait / terminate / kill：命令超时后的回收 | 等待超时或发出终止请求，等不等于进程已经结束？ | `subprocess.Popen.wait`、`subprocess.Popen.terminate`、`subprocess.Popen.kill` | 09、13、38 |
| 40 · multiprocessing.Process：让 Python 工作在子进程执行 | 怎样启动另一份 Python 工作，并确认它退出？ | `multiprocessing.Process`、`multiprocessing.Process.start`、`multiprocessing.Process.is_alive`、`multiprocessing.Process.join` | 27、39 |
| 41 · Process.terminate / kill / join：结束 Python 子进程并完成回收 | 进程没有按约定结束时，怎样请求终止并等到退出？ | `multiprocessing.Process.terminate`、`multiprocessing.Process.kill` | 39、40 |

<details>
<summary>本模块的原子结论与自查</summary>

### 37 · subprocess.run：运行并等待外部命令

1. **带走：** run 等待外部程序结束；它是同步接口，需要注意调用线程。
2. **自查：** 指出外部进程与当前 Python 线程的不同，并读取退出结果。

### 38 · subprocess.Popen / communicate：启动命令并收集管道输出

1. **带走：** Popen 创建进程后返回句柄，communicate 处理管道通信并等待结束。
2. **自查：** 说明为什么带管道时不能只等退出而不消费输出。

### 39 · Popen.wait / terminate / kill：命令超时后的回收

1. **带走：** 超时与终止请求都不代替最终等待；带管道的工作还需完成通信收尾。
2. **自查：** 按超时、终止、必要时强制结束、等待回收检查句柄。
3. **需要辨认的异常：** `subprocess.TimeoutExpired`。

### 40 · multiprocessing.Process：让 Python 工作在子进程执行

1. **带走：** Process 对象负责 Python 子进程的启动和等待，线程对象与进程对象不能混为一谈。
2. **自查：** 用顶层 target 和入口保护启动，区分 join 超时与已退出。

说明运行平台和 Python 版本的默认启动方式；显式启动上下文与进程池保留为清单外按需补充。

### 41 · Process.terminate / kill / join：结束 Python 子进程并完成回收

1. **带走：** terminate/kill 发出终止动作，join 确认退出；强制终止不保证目标 finally 或共享资源完整。
2. **自查：** 区分合作退出与强制结束，并验证自己启动的进程不再存活。

</details>

<details>
<summary>可复用的旧课材料与编写状态</summary>

- 37：规划单元，待从旧课拆分或补写。材料：[14 · 进程池、子进程与系统边界](../content/projects/python-async-concurrency/12-processes/index.md)、[20 · 进程生命周期：从队列工作到超时回收](../content/projects/python-async-concurrency/18-process-lifecycle/index.md)。
- 38：规划单元，待从旧课拆分或补写。材料：[20 · 进程生命周期：从队列工作到超时回收](../content/projects/python-async-concurrency/18-process-lifecycle/index.md)。
- 39：规划单元，待从旧课拆分或补写。材料：[20 · 进程生命周期：从队列工作到超时回收](../content/projects/python-async-concurrency/18-process-lifecycle/index.md)。
- 40：规划单元，待从旧课拆分或补写。材料：[20 · 进程生命周期：从队列工作到超时回收](../content/projects/python-async-concurrency/18-process-lifecycle/index.md)。
- 41：规划单元，待从旧课拆分或补写。材料：[20 · 进程生命周期：从队列工作到超时回收](../content/projects/python-async-concurrency/18-process-lifecycle/index.md)。

</details>

</details>

## API 到正式讲解单元的检查表

| API | 正式讲解单元 |
| --- | --- |
| `asyncio.run` | 01 · async def：定义之后，什么时候执行？ |
| `asyncio.sleep` | 02 · await：等待结果，不等于自动并发 |
| `asyncio.create_task` | 03 · create_task：先安排工作，再等待结果 |
| `asyncio.TaskGroup` | 05 · TaskGroup：离开代码块前，等任务结束 |
| `asyncio.TaskGroup.create_task` | 05 · TaskGroup：离开代码块前，等任务结束 |
| `asyncio.gather` | 06 · gather：等待一组任务，收集一组结果 |
| `asyncio.wait` | 07 · wait：先取得任务的完成情况 |
| `asyncio.as_completed` | 12 · asyncio.as_completed：按完成顺序取结果 |
| `asyncio.Task.done` | 08 · done、result、exception：读取 Task 的状态与结果 |
| `asyncio.Task.result` | 08 · done、result、exception：读取 Task 的状态与结果 |
| `asyncio.Task.exception` | 08 · done、result、exception：读取 Task 的状态与结果 |
| `asyncio.Task.cancel` | 09 · Task.cancel：请求取消并等待收尾 |
| `asyncio.Future.done` | 35 · Future.done() / result() / exception()：读取 asyncio Future 的结果 |
| `asyncio.Future.result` | 35 · Future.done() / result() / exception()：读取 asyncio Future 的结果 |
| `asyncio.Future.exception` | 35 · Future.done() / result() / exception()：读取 asyncio Future 的结果 |
| `asyncio.wait_for` | 13 · asyncio.wait_for：限制一次等待的时长 |
| `asyncio.timeout` | 15 · asyncio.timeout：给一段异步代码共享时间预算 |
| `asyncio.shield` | 16 · asyncio.shield：区分取消等待者与内部工作 |
| `builtins.TimeoutError` | 13 · asyncio.wait_for：限制一次等待的时长 |
| `asyncio.Semaphore` | 17 · asyncio.Semaphore：限制同时进入的工作 |
| `asyncio.Semaphore.acquire` | 17 · asyncio.Semaphore：限制同时进入的工作 |
| `asyncio.Semaphore.release` | 17 · asyncio.Semaphore：限制同时进入的工作 |
| `asyncio.Queue` | 18 · asyncio.Queue：让生产者与消费者交接数据 |
| `asyncio.Queue.put` | 18 · asyncio.Queue：让生产者与消费者交接数据 |
| `asyncio.Queue.get` | 18 · asyncio.Queue：让生产者与消费者交接数据 |
| `asyncio.Lock` | 19 · asyncio.Lock：保护跨 await 的共享状态 |
| `asyncio.Lock.acquire` | 19 · asyncio.Lock：保护跨 await 的共享状态 |
| `asyncio.Lock.release` | 19 · asyncio.Lock：保护跨 await 的共享状态 |
| `asyncio.Event` | 20 · asyncio.Event：让任务等待一个通知 |
| `asyncio.Event.set` | 20 · asyncio.Event：让任务等待一个通知 |
| `asyncio.Event.wait` | 20 · asyncio.Event：让任务等待一个通知 |
| `asyncio.Event.clear` | 20 · asyncio.Event：让任务等待一个通知 |
| `asyncio.to_thread` | 26 · asyncio.to_thread：把阻塞函数交给线程 |
| `concurrent.futures.ThreadPoolExecutor` | 31 · ThreadPoolExecutor / submit：把工作提交到线程池 |
| `concurrent.futures.Executor.submit` | 31 · ThreadPoolExecutor / submit：把工作提交到线程池 |
| `concurrent.futures.Executor.shutdown` | 32 · Future.cancel / Executor.shutdown：结束线程池并处理未执行工作 |
| `concurrent.futures.Future.result` | 31 · ThreadPoolExecutor / submit：把工作提交到线程池 |
| `concurrent.futures.Future.done` | 31 · ThreadPoolExecutor / submit：把工作提交到线程池 |
| `concurrent.futures.Future.exception` | 31 · ThreadPoolExecutor / submit：把工作提交到线程池 |
| `concurrent.futures.Future.cancel` | 32 · Future.cancel / Executor.shutdown：结束线程池并处理未执行工作 |
| `threading.Thread` | 27 · threading.Thread：创建、启动并等待线程 |
| `threading.Thread.start` | 27 · threading.Thread：创建、启动并等待线程 |
| `threading.Thread.join` | 27 · threading.Thread：创建、启动并等待线程 |
| `threading.Thread.is_alive` | 27 · threading.Thread：创建、启动并等待线程 |
| `threading.Lock` | 28 · threading.Lock：保护线程共享状态 |
| `threading.Lock.acquire` | 28 · threading.Lock：保护线程共享状态 |
| `threading.Lock.release` | 28 · threading.Lock：保护线程共享状态 |
| `threading.Event` | 29 · threading.Event：通知线程合作退出 |
| `threading.Event.set` | 29 · threading.Event：通知线程合作退出 |
| `threading.Event.wait` | 29 · threading.Event：通知线程合作退出 |
| `threading.Event.clear` | 29 · threading.Event：通知线程合作退出 |
| `queue.Queue` | 30 · queue.Queue：在线程之间交接数据 |
| `queue.Queue.put` | 30 · queue.Queue：在线程之间交接数据 |
| `queue.Queue.get` | 30 · queue.Queue：在线程之间交接数据 |
| `queue.Queue.get_nowait` | 30 · queue.Queue：在线程之间交接数据 |
| `contextvars.ContextVar` | 24 · contextvars.ContextVar：保存每份任务自己的上下文 |
| `contextvars.ContextVar.get` | 24 · contextvars.ContextVar：保存每份任务自己的上下文 |
| `contextvars.ContextVar.set` | 24 · contextvars.ContextVar：保存每份任务自己的上下文 |
| `contextvars.ContextVar.reset` | 24 · contextvars.ContextVar：保存每份任务自己的上下文 |
| `contextlib.asynccontextmanager` | 21 · async with / contextlib.asynccontextmanager：把异步资源绑定到作用域 |
| `contextlib.aclosing` | 23 · contextlib.aclosing：提前停止异步迭代 |
| `inspect.isawaitable` | 25 · inspect.isawaitable / inspect.iscoroutinefunction：辨认函数与可等待对象 |
| `inspect.iscoroutinefunction` | 25 · inspect.isawaitable / inspect.iscoroutinefunction：辨认函数与可等待对象 |
| `asyncio.get_running_loop` | 33 · loop.run_in_executor：从协程使用指定执行器 |
| `asyncio.AbstractEventLoop.run_in_executor` | 33 · loop.run_in_executor：从协程使用指定执行器 |
| `asyncio.wrap_future` | 34 · asyncio.wrap_future：等待已有的执行器 Future |
| `asyncio.run_coroutine_threadsafe` | 36 · asyncio.run_coroutine_threadsafe：从另一个线程提交协程 |
| `multiprocessing.Process` | 40 · multiprocessing.Process：让 Python 工作在子进程执行 |
| `multiprocessing.Process.start` | 40 · multiprocessing.Process：让 Python 工作在子进程执行 |
| `multiprocessing.Process.is_alive` | 40 · multiprocessing.Process：让 Python 工作在子进程执行 |
| `multiprocessing.Process.join` | 40 · multiprocessing.Process：让 Python 工作在子进程执行 |
| `multiprocessing.Process.terminate` | 41 · Process.terminate / kill / join：结束 Python 子进程并完成回收 |
| `multiprocessing.Process.kill` | 41 · Process.terminate / kill / join：结束 Python 子进程并完成回收 |
| `subprocess.run` | 37 · subprocess.run：运行并等待外部命令 |
| `subprocess.Popen` | 38 · subprocess.Popen / communicate：启动命令并收集管道输出 |
| `subprocess.Popen.communicate` | 38 · subprocess.Popen / communicate：启动命令并收集管道输出 |
| `subprocess.Popen.wait` | 39 · Popen.wait / terminate / kill：命令超时后的回收 |
| `subprocess.Popen.terminate` | 39 · Popen.wait / terminate / kill：命令超时后的回收 |
| `subprocess.Popen.kill` | 39 · Popen.wait / terminate / kill：命令超时后的回收 |
| `time.sleep` | 26 · asyncio.to_thread：把阻塞函数交给线程 |
| `time.monotonic` | 14 · time.monotonic / time.perf_counter：计量经过时间与预算 |
| `time.perf_counter` | 14 · time.monotonic / time.perf_counter：计量经过时间与预算 |

## 语法与异常的检查表

| 类别 | 内容 | 单元 |
| --- | --- | --- |
| 语法 | `async def` | 01 |
| 语法 | `await` | 02 |
| 语法 | `async with` | 04 |
| 语法 | `async for` | 22 |
| 语法 | `异步生成器中的 yield` | 22 |
| 语法 | `try/finally` | 09 |
| 语法 | `except*` | 11.2 |
| 异常类型 | `asyncio.CancelledError` | 09 |
| 异常类型 | `asyncio.InvalidStateError` | 08 |
| 异常类型 | `concurrent.futures.CancelledError` | 32 |
| 异常类型 | `concurrent.futures.TimeoutError` | 31 |
| 异常类型 | `queue.Empty` | 30 |
| 异常类型 | `queue.Full` | 30 |
| 异常类型 | `subprocess.TimeoutExpired` | 39 |
| 异常类型 | `builtins.ExceptionGroup` | 11.2 |

检查保证所有输入 API 各有一个正式引入单元，语法与异常类型无遗漏，前置只指向更早单元。它不证明待编写课程的正文已经实现了这些讲解。

```bash
python3 python-async-reference/tools/build_curriculum.py
python3 python-async-reference/tools/build_curriculum.py --check
```
