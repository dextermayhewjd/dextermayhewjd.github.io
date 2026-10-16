---
title: "Python 异步与并发"
description: "逐步理解 Python 原生异步、线程、进程与同步机制的运行、等待和退出。"
weight: 15
ShowToc: true
hideMeta: true
---

## 先学清楚一份任务怎么完成

[先看完整 01–41 课 API 与语法出现次数](api-frequency/)：按首次引入的课程逐项排列，列出全部 97 项接口及配套语法在 verl、AReaL、Slime、Miles 中的统计；同课只显示一次课号，待编写课程另作标注。

这份专题只讲 Python 原生异步与并发。目标是说明工作何时开始、谁在等待、多少份可以同时推进，以及失败或退出时怎样清理。Slime、AReaL、verl 的真实用法帮助选择学习重点，框架业务与通用工程化不在本专题展开。

**从第 1 节开始即可。** 只需知道 Python 函数、参数、返回值和变量赋值；不要求先理解强化学习、Ray 或模型服务。先用一句话认清本节概念，再沿小实验观察它的行为。Slime 对照与源码位置放在每页末尾，按需展开。

最初六个单元逐步增加知识点：**01 创建协程对象，用 run 执行 → 02 在协程内部用 await 等待 → 03 用 create_task 安排任务 → 04 读懂 with / async with 的进入和退出 → 05 用 TaskGroup 等待组内任务 → 06 用 gather 收集结果。** 前一节的最小结论，成为后一节的起点。

[开始：async def 定义之后，什么时候执行？](01-async-def/)

想先了解整体范围，可看[学习路线与完成标准](learning-route/)：按任务结果、退出、负载、线程、上下文和进程逐步展开，并区分必学与按需内容。

忘了前面学过什么，或不确定几个 API 的关系时，打开[知识地图与回忆练习](knowledge-map/)：从问题找概念，先回忆、再核对，用短代码检查理解，并留下自己的错因。

## 当前学习：线程基础与线程池

[26 · asyncio.to_thread](26-to-thread/) → [27 · Thread](27-thread-lifecycle/) → [28 · Lock](28-thread-lock/) → [29 · Event](29-thread-event/)。

**第 31 课 · ThreadPoolExecutor：提交并收集线程池工作**：先读 [31.1 · ThreadPoolExecutor / submit：提交工作并取结果](31-threadpool-submit/)，再读 [31.2 · ThreadPoolExecutor.map：批量提交并按输入顺序取结果](31-threadpool-map/)。两个小节归在同一目录组内。

**第 33 课 · 使用当前事件循环**的四个小节放在同一组：[33.1 · get_running_loop：取出正在使用的事件循环](33-current-loop/) → [33.2 · run_in_executor / await：提交到指定线程池并等待结果](33-run-in-executor/) → [33.3 · await / Event：等待线程时，让其他协程继续](33-await-handoff/) → [33.4 · loop.time：用事件循环时钟计算剩余预算](33-loop-time/)。

[34 · asyncio.wrap_future](34-wrap-future/)补上了“工作已经提交，怎样接入 await”的关系。[25 · inspect](25-inspect-awaitable/)已经分清检查函数与检查调用结果。[37 · subprocess.run](37-subprocess-run/)已经区分启动子进程、等待退出和读取输出。[38 · Popen / communicate](38-popen-communicate/)已写好。[35.1 · asyncio Future 的状态与结果](35-future-results/)已讨论，[35.2 · 创建 Future 并提供结果](35-future-completion/)也已讨论，[35.3 · Task 完成回调](35-task-callbacks/)也已讨论，[36.1 · 手动管理事件循环](36-manual-event-loop/)已讨论，现在继续 [36.2 · 跨线程提交协程](36-threadsafe-submit/)，为 Slime 样本生成里的 Future 与循环交接做准备。第 30、32 课继续暂缓；之后按[蓝黄重点续学表](learning-route/#priority-reading)推进。

## 已整理的学习主线

[07 · wait：先取得任务的完成情况](04-results/) → [08 · done、result、exception：读取 Task 的状态与结果](07-task-results/) → [09 · Task.cancel：请求取消并等待收尾](09-task-cancellation/) → [10.1 · asyncio.gather：收集报错，任务仍可继续](15-gather-failures/) → [10.2 · return_exceptions=True：收齐结果与异常](15-gather-exceptions/) → [11.1 · TaskGroup：一个任务失败，取消其余未完成任务并等待收尾](11-taskgroup-failures/) → [11.2 · ExceptionGroup / except*：读取任务组的错误](11-exception-groups/) → [12 · asyncio.as_completed：按完成顺序取结果](08-as-completed/) → [13 · asyncio.wait_for：限制一次等待的时长](10-wait-for/) → [14 · time.monotonic / time.perf_counter：计量经过时间与预算](11-time-budget/) → [15 · asyncio.timeout：给一段异步代码共享时间预算](12-timeout-scope/) → [16 · asyncio.shield：区分取消等待者与内部工作](13-shield/) → [17 · asyncio.Semaphore：限制同时进入的工作](06-semaphore/) → [18 · asyncio.Queue：让生产者与消费者交接数据](07-queues/) → [19 · asyncio.Lock：保护跨 await 的共享状态](19-async-lock/) → [20 · asyncio.Event：让任务等待一个通知](20-async-event/) → [21.1 · try/finally：分清准备、使用和关闭](21-resource-lifecycle/) → [21.2 · yield：交出一个值，并暂停在原处](21-yield-pause/) → [21.3 · @ 装饰器：把函数交给另一个函数处理](21-decorators/) → [21.4 · asynccontextmanager：把准备和关闭接到 async with](21-async-contextmanager/) → [21.5 · finally：使用区报错后怎样关闭](21-context-errors/) → [21.6 · Task.cancel：使用区被取消后怎样关闭](21-context-cancellation/) → [22 · async for / 异步生成器：逐项等待异步产出](22-async-iteration/)。先读取消与整组失败，再学习按完成顺序取结果，再进入超时和时间预算，随后学习协程间的协调。10、11 各分为两个子课；21 分为六个小节。

## 课程目录

下方旧目录保留历史编号，现行单元号以学习路线和页面标题为准；既有 URL 不因顺延而改动。多主题页面可以先读当前需要的一部分，不要求一开始通读全部课程。

<details id="legacy-course-catalog">
<summary>展开旧版 23 页与对应问题</summary>

## 01–16：先建立任务执行的主线

| 节 | 本节解决的问题 |
| --- | --- |
| [01 · async def：定义之后，什么时候执行？](01-async-def/) | 先分清异步函数、协程对象和真正执行的函数体。 |
| [02 · await：等待结果，不等于自动并发](02-await/) | 沿执行顺序理解挂起、恢复和 asyncio.sleep。 |
| [03 · create_task：先安排工作，再等待结果](03-tasks/) | 对比直接 await 与提前创建 Task，分清安排任务和等待结果。 |
| [04 · TaskGroup：离开代码块前，等任务结束](04-taskgroup/) | 沿用两份任务，只增加退出组时等待全部任务结束的关系。 |
| [05 · gather：等待一组任务，收集一组结果](05-gather/) | 等待已创建的 Task，按传入顺序收集返回值。 |
| [06 · wait：先取得任务的完成情况](04-results/) | 区分 done/pending，用已学的 await 取值并等完剩余任务。 |
| [07 · 取消与超时：请求停止以后，还要等待收尾](05-cancellation/) | 理解 cancel、CancelledError、finally 和任务级超时。 |
| [08 · Semaphore：限制同时进入的工作数量](06-semaphore/) | 把并发许可与任务总量区分开。 |
| [09 · Queue：把生产速度和消费速度接起来](07-queues/) | 用有界队列理解等待、背压与结束信号。 |
| [10 · 线程池：把阻塞工作移出事件循环](08-executors/) | 理解 to_thread、run_in_executor 与两类 Future 的边界。 |
| [11 · Lock、Event 与线程退出](09-thread-synchronization/) | 线程共享状态怎样保护，后台线程怎样收到停止信号。 |
| [12 · async with、async for 与异步生成器](10-async-protocols/) | 把异步资源的进入、迭代和退出连起来。 |
| [13 · ContextVar：让并发任务保留各自的上下文](11-contextvars/) | 区分任务上下文与共享全局变量，并恢复进入前的状态。 |
| [14 · 进程池、子进程与系统边界](12-processes/) | 从 spawn 和 Pool.starmap 出发，区分进程、线程与 asyncio。 |
| [15 · Future、回调与跨线程事件循环](13-event-loop/) | 理解谁保存尚未完成的结果，谁负责把等待者唤醒。 |
| [16 · 回到 Slime：串起创建、等待与清理](14-slime-walkthrough/) | 用一条完整任务主线检查前面学过的原生机制。 |

## 17–23：补齐通知、同步与系统边界

前 16 节先把一份任务的生命周期读通，下面逐项补齐 Slime 中出现的其他原生用法。已有页面地址保留；也可以从[源码用法与教程对照](coverage/)按遇到的接口直接进入。

| 节 | 本节解决的问题 |
| --- | --- |
| [17 · Event 通知与异步互斥](15-async-notification/) | 为什么任务已经开始，却还要等一次通知；set、wait、clear 和 Lock 分别做什么。 |
| [18 · Condition、RLock 与 Timer](16-thread-coordination/) | 等共享条件时怎样释放锁，醒来后为什么重查，计时线程怎样结束。 |
| [19 · 线程池 Future 的结果与退出](17-executor-results/) | submit、map、wait、as_completed、取消和 shutdown 的同步合同。 |
| [20 · 进程生命周期：从队列工作到超时回收](18-process-lifecycle/) | 多进程队列怎样传结果，完成消息与进程退出有何区别，命令超时后怎样回收。 |
| [21 · 信号、进程组与文件锁](19-signals-locks/) | 信号发给谁，怎样等待管道就绪，持锁进程退出后谁释放锁。 |
| [22 · asyncio Streams](20-async-streams/) | 按协议读字节、处理提前 EOF，区分写入缓冲、连接关闭和服务关闭。 |
| [23 · 异步能力检查与协议边界](21-async-inspection/) | 函数检查、返回值检查、类型注解和异步协议各能说明什么。 |

TaskGroup 是按本轮学习需要补充的独立单元，源码对照来自 AReaL；其余章节继续沿用固定 Slime 版本。

每节末尾可展开该知识点对应的**源码位置**，查看原代码行，并打开固定版本的原文或完整文件快照。重复出现的接口共用解释；每个业务调用的输入与清理仍需沿所在函数核对。

[源码用法与教程对照](coverage/)逐项连接扫描结果和讲解，也保留 Slime 文档里的 29 段 Python 示例。没有接收者类型证据的同名方法单独标为候选；它们有核对入口，但不冒称已经证明是原生并发 API。

</details>

## 怎样使用示例

每节的 `example.py` 都可以下载后用 Python 3.11 及以上版本运行。示例只使用标准库，不连接模型服务、不启动 Slime 训练。文中明确区分独立语言实验、教学裁剪和固定版本的原源码。

每次只做三件事：先猜输出，再运行，最后回答该节的复述问题。源码入口默认收起，等概念清楚后再展开；文件名、函数名、原行号与固定提交都保留。

## 需要回查时

- [源码用法与教程对照](coverage/)：从 API、方法或原代码定位对应讲解。
- [学习路线与完成标准](learning-route/)：确定先看哪部分，以及用什么结果验证理解。
- [全部用法索引](usage-index/)：分类统计、每一个源码位置以及可下载清单。
- [版本与参考](references/)：Slime 源码版本、Python 版本与书籍核对说明。

原始资料仍单独保存在项目根目录 `python-async-concurrency/`。本专题位于网站“项目”栏目。
