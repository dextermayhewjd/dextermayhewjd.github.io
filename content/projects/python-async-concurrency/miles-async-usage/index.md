---
title: "Miles：原生异步与并发用法"
description: "从一份 rollout 的创建、等待、结果收集和清理，看 Miles 如何组合 Python 原生异步与并发机制。"
weight: 845
ShowToc: true
hideMeta: true
hideInOverview: true
---

这份记录对应本地 `/home/hongshi/projects/miles`，固定版本为 `cf91d625b3074f480b31ddcfd6604298407899f3`。扫描时工作区干净；完整清单覆盖已跟踪 Python 文件，课程对照表只取 `miles/` 核心包。`miles_plugins/`、入口脚本、测试和示例不混入核心包数字。

[查看完整课程统计表的 Miles 列](../api-frequency/)。调用次数、语法位置、装饰器引用分别计算，原有三库的固定统计继续保留。

## 1. create_task、Semaphore、wait：一份 rollout 如何得到结果

这里跟随当前类式 rollout 的正常训练路径，输入是一批提示词组，输出是收集并过滤后的样本组。先看组任务，再进入单个样本，最后回到收集循环。

1. **进入训练 rollout。** `InferenceRolloutFn.__call__` 把非评估请求交给 `_call_train`，再进入 `generate_rollout_async`。[入口源码](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/inference_rollout/inference_rollout_common.py#L220-L236)
2. **安排组任务。** `generate_rollout_async` 在有提交容量时取出提示词组；`submit_generate_tasks` 用 `asyncio.create_task` 安排各组的 `generate_and_rm_group`，把 Task 放进 `pendings`。[提交与收集循环](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/inference_rollout/inference_rollout_train.py#L79-L144)
3. **进入单组，安排样本任务。** `generate_and_rm_group` 为每个样本创建 Task，然后 `await asyncio.gather(*tasks)` 收齐这一组。[组内并发](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/inference_rollout/inference_rollout_common.py#L142-L180)
4. **限制实际生成的并发数量。** 每个样本进入 `async with state.generate_fn_semaphore` 后，才等待生成函数。Semaphore 限制的是这个区段，创建的 Task 可以更多。[受限区段](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/inference_rollout/inference_rollout_common.py#L85-L113)
5. **返回组外，先处理已完成的组。** 默认按组提交时，调度器使用 `asyncio.wait(..., FIRST_COMPLETED)`；调用方遍历 `done`，用 `task.result()` 读取结果，过滤后加入训练批次，继续补充工作。[默认等待策略](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/submission_scheduler.py#L16-L28)

对应课程：03 创建任务、06 收集结果、07 完成情况、08 读取结果、17 限制并发。

## 2. gather、cancel：组内失败之后谁负责收尾

同一份 `generate_and_rm_group` 在 `gather` 外包了 `try/except BaseException`。如果收集被异常或取消打断，它会逐个请求取消样本 Task，再用 `gather(..., return_exceptions=True)` 等它们结束，最后重新抛出原异常。[失败路径](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/inference_rollout/inference_rollout_common.py#L172-L180)

这里的取消与收尾是 **Miles 显式补上的责任**。不能从这段结果反推“普通 gather 一报错就自动取消其他任务”。对应课程 09、10.1、10.2，也适合与第 11 课的 TaskGroup 责任对照。

## 3. Event、Condition：完全异步时怎样持续生产并交接数据

`FullyAsyncRolloutFn` 第一次处理训练请求时，创建长期运行的 `_worker_loop`；调用方通过 `_drain` 取走已经完成的组。生成工作与训练方取数据不必逐轮一起开始、一起结束。[创建 worker](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/fully_async_rollout.py#L104-L118)

1. worker 先等待 `_producer_resumed` 这个 Event；需要暂停生产提交时清除标志，恢复时重新设置。[暂停与恢复](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/fully_async_rollout.py#L124-L144)
2. worker 按容量提交组任务，等待进展，把完成结果交给 `_output.put`；训练方在 `_output.get` 等待足够的可用数据。[生产循环](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/fully_async_rollout.py#L155-L185)、[消费入口](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/fully_async_rollout.py#L209-L219)
3. 默认 `_output` 是自定义 `DefaultDataBuffer`，内部用列表和 `asyncio.Condition`。缓冲区满时生产者等待；数据不足时消费者等待；修改缓冲区后调用 `notify_all` 通知重查条件。它还要处理样本过滤和权重版本，因此不能把这个对象直接当成 `asyncio.Queue`。[缓冲区与条件等待](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/rollout/fully_async_data_buffer.py#L153-L241)

对应课程 18 的数据交接、20 的条件通知。`asyncio.Condition` 是这次源码中发现的清单外接口，暂记为后续补充讨论，暂不纳入当前 97 项课程清单。

## 4. sleep(0)、gather：公共工具如何组织任务

`miles.utils.async_utils` 把已有机制组合成较短的调用入口：

- `eager_create_task` 创建 Task 后 `await asyncio.sleep(0)`，给新任务执行起始代码的机会，再返回 Task。调用处例如 `train_async.py` 的下一轮 rollout 准备工作。[工具实现](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/utils/async_utils.py#L134-L142)、[训练入口](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/train_async.py#L76-L105)
- `gather_and_raise_first` 先用 `return_exceptions=True` 收齐结果，再检查并抛出其中的第一个失败。[工具实现](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/utils/async_utils.py#L164-L175)
- `wait_cancelling_pending_on_first_completion` 等到首个任务完成后，显式取消 pending，再等待收尾并检查错误。[工具实现](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/utils/async_utils.py#L95-L118)

这些包装函数不计成新的 Python 原生 API；统计记录的是它们内部的原生调用位置。

## 5. Thread、run_coroutine_threadsafe、AsyncExitStack：入口与资源退出

`AsyncLoopThread` 在后台线程中启动事件循环，`submit` 用 `asyncio.run_coroutine_threadsafe` 提交协程并返回 `concurrent.futures.Future`；`run` 再调用这个 Future 的 `result()`，同步等待结果。这里的 `result()` 会等待，与课程 08 中未完成就报错的 `asyncio.Task.result()` 不同。[线程与循环入口](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/utils/async_utils.py#L31-L64)

`Disposer` 用 `AsyncExitStack` 登记同步或异步清理回调，在退出 `async with` 时执行；它接管的是资源清理。`AsyncExitStack` 已纳入第 23.2–23.3 子课规划，分别解释集中清理与清理责任转移。[清理责任](https://github.com/radixark/miles/blob/cf91d625b3074f480b31ddcfd6604298407899f3/miles/utils/async_utils.py#L182-L212)

## 6. 怎样理解表格里的 0

统计器保留直接调用、带接收者证据的方法推断，以及尚不能确认类型的候选。它不做完整的跨方法类型分析。例如 `_producer_resumed.clear()` 在源码中确实存在，但类型在 `__init__` 的另一次赋值中建立，因此这类类成员操作可能仍被列为候选，不能用已识别调用数 0 推断为不存在。

Ray 的远程调用、HTTP 客户端以及自定义缓冲区也不冒充 Python 原生 API 计数。表格回答“本次扫描识别到了多少原生源码位置”，源码主线回答“这些位置怎样组合”；二者需要一起看。
