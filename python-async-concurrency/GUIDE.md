# 按 Slime 的任务主线阅读原生异步与并发

[返回总览](README.md) · [全部文件](FILES.md) · [逐条数据](inventory.tsv) · [版本与依据](SOURCE-CHECK.md)

本文是源码阅读导航。完整次数与每一个位置在 `usage-categories/` 和 `inventory.tsv` 中；这里挑选能够串起职责的入口。所有链接固定到本次本地 HEAD `2f2318653f6f794dddd321eff7c9d4b7b174643f`，不混用既有阅读章节的其他版本。代码块是原文件的连续片段，需要原上下文，未另造可执行示例。

## 1. 从同步入口进入事件循环

跟随调用方把一个异步任务交给后台线程，再拿回结果。先读 `slime/utils/async_utils.py` 的 `AsyncLoopThread`，然后返回调用它的 `run()`。

```python
    def run(self, coro):
        # Schedule a coroutine onto the loop and block until it's done
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()
```

构造器先建立事件循环和后台 `Thread`，线程内执行 `set_event_loop()`、`run_forever()`。上面的 `run_coroutine_threadsafe()` 把协程提交给那个循环；末尾 `.result()` 阻塞当前调用线程。这是同步桥接入口，不应照搬进同一个事件循环的运行线程。

<details>
<summary>源码入口与全部用法</summary>

- [AsyncLoopThread：async_utils.py:46–58](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/async_utils.py#L46-L58)
- [asyncio 全部用法](usage-categories/asyncio.md) · [线程全部用法](usage-categories/threading.md)

</details>

## 2. 创建协程、安排任务、汇合结果

进入 rollout 后，先分清 `async def`、`await` 和 `create_task()`。`async def` 定义异步函数；调用普通协程函数得到协程对象；`create_task()` 才把它安排为事件循环中的 Task。`await` 也可直接推进一个协程，并不等于创建新线程。

`sglang_rollout.py` 为一组样本创建任务，再用 `gather()` 汇合。它还使用 `wait(..., FIRST_COMPLETED)` 处理先完成的工作，评测路径使用 `as_completed()` 逐个收取结果。

| 用法 | 在这里解决的问题 | 源码入口 |
| --- | --- | --- |
| `create_task` + `gather` | 同时安排多份样本，等待这一组结果 | [sglang_rollout.py:411–414](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L411-L414) |
| `wait(..., FIRST_COMPLETED)` | 取出完成集合，同时保留 pending | [sglang_rollout.py:523](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L523) |
| `as_completed` | 按完成先后处理评测结果 | [sglang_rollout.py:725](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L725) |
| `async for` | 逐段消费模型流式响应 | [sglang_streaming_rollout.py:127](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_streaming_rollout.py#L127) |
| `@asynccontextmanager` + `yield` | 进入与退出异步资源作用域 | [generate.py:95](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L95) |

返回任务主线时，区分“任务已经安排”与“结果已经拿到”。全部语法位置见 [syntax](usage-categories/syntax.md)，异步上下文辅助见 [contextlib-async](usage-categories/contextlib-async.md)。

## 3. 工作量由谁限制

`GenerateState` 创建 `asyncio.Semaphore`；生成路径在许可范围内调用生成器。持续生产路径另外建立 `asyncio.Queue(maxsize=1)`，在已完成结果无法入队时等待消费者。

```python
            self.outputs = asyncio.Queue(maxsize=1)
            self.producer = asyncio.create_task(self._produce())
```

信号量限制的是持有许可的工作，队列容量限制的是已经入队的结果，两者不能互相代替。生产者还可能持有尚未入队的结果。`AsyncPacer` 则通过 Future 与 `call_soon/call_later` 分批唤醒等待者，其源码说明它控制启动节奏，不限制在途数量。

<details>
<summary>源码入口与全部用法</summary>

- [信号量创建：sglang_rollout.py:95](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sglang_rollout.py#L95)
- [有界结果队列：fully_async_distributed.py:291](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_distributed.py#L291)
- [分批唤醒：async_utils.py:8–42](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/utils/async_utils.py#L8-L42)
- [asyncio 全部用法](usage-categories/asyncio.md) · [同步队列全部用法](usage-categories/queue.md)

</details>

## 4. 结果等待、失败与取消一起读

消费者取结果时，还必须观察生产者是否异常退出，避免一直等待一个不会再产生的结果。读完 `_GenerationActor._next()` 再回到上层消费者。

```python
    async def _next(self):
        take = asyncio.create_task(self.outputs.get())
        try:
            await asyncio.wait((take, self.producer), return_when=asyncio.FIRST_COMPLETED)
            if take.done():
                return take.result()
            self.producer.result()  # Propagate custom generation errors.
            if not self.outputs.empty():
                return await take
            return None
        finally:
            take.cancel()
            await asyncio.gather(take, return_exceptions=True)
```

这里同时等待取数任务和生产者；通过 `.result()` 传播错误；退出时取消并等待取数任务结束。`return_exceptions=True` 用于收尾，不代表结果全部成功。`wait()` 的超时不会自动取消 pending；`wait_for()` 和 `asyncio.timeout()` 的行为需要分别理解。`asyncio.timeout()` 从 Python 3.11 才提供。

<details>
<summary>源码入口</summary>

- [取数与清理：fully_async_distributed.py:305–317](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_distributed.py#L305-L317)
- [任务组取消与等待：fully_async_distributed.py:338–342](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_distributed.py#L338-L342)
- [任务级 timeout：generate.py:202](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/examples/coding_agent_rl/generate.py#L202)
- [对象方法候选全集](usage-categories/candidates.md)：包括 `.cancel/.done/.result`，需结合接收者判断是 Task、Future 还是其他对象。

</details>

## 5. 阻塞工作交给线程，仍要追踪所有权

数据读取进入 `QueueReader.get_samples_async()` 后，把同步读操作交给专用单线程池：

```python
        return await asyncio.get_running_loop().run_in_executor(self._reader, self.get_samples, num_samples)
```

其构造器创建 `ThreadPoolExecutor(max_workers=1)`、`threading.RLock()`、`threading.Event()` 和后台心跳线程。分别负责同步读取、保护共享租约状态、停止通知和周期性续租。

`transport.run_rollout_io()` 则结合 Semaphore、`to_thread()` 和 `shield()`。它被取消后仍等待已经接受的文件写入结束：写入成功则继续传播取消，写入失败则传播写入异常。不能假设取消 await 就能停止工作线程。

<details>
<summary>源码入口与全部用法</summary>

- [线程与同步原语：queue_data_source.py:1034–1045](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L1034-L1045)
- [线程池桥接：queue_data_source.py:1113–1115](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L1113-L1115)
- [写入与取消：transport.py:370–389](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/transport.py#L370-L389)
- [执行器全部用法](usage-categories/executors.md) · [线程全部用法](usage-categories/threading.md)

</details>

## 6. 请求上下文不能被其他任务覆盖

`sample_hooks.py` 用 `ContextVar` 保存当前任务的 rollout ID，`rollout_context()` 在退出时用 token 恢复旧值；hook 返回值可能同步也可能异步，因此先执行，再用 `inspect.isawaitable()` 判断是否需要 await。

这里解决的是请求上下文隔离与接口适配。它不是互斥锁，也不替代共享对象的同步。

<details>
<summary>源码入口与全部用法</summary>

- [上下文与 hook：sample_hooks.py:12–41](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/sample_hooks.py#L12-L41)
- [ContextVar 用法](usage-categories/contextvars.md) · [异步反射用法](usage-categories/inspect-async.md)

</details>

## 7. 独立进程、系统信号与文件锁

| 机制 | Slime 中的职责 | 入口及完整清单 |
| --- | --- | --- |
| `multiprocessing.Process` | 启动单独的 SGLang 路由服务进程 | [deployment.py:53](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/backends/sglang_utils/deployment.py#L53) · [全部用法](usage-categories/multiprocessing.md) |
| `subprocess.Popen/run` | 启动外部命令，等待结果与退出 | [全部用法](usage-categories/subprocess.md) |
| `signal.signal/alarm` | 给同步评分代码设置闹钟超时 | [math_dapo_utils.py:64–79](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/rm_hub/math_dapo_utils.py#L64-L79) · [全部用法](usage-categories/signal.md) |
| `os.killpg` | CI 中向子进程组转发终止信号 | [gpu_lock_exec.py:55](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/ci/gpu_lock_exec.py#L55) · [全部用法](usage-categories/os-process.md) |
| `fcntl.flock` | 对持久化队列、CI 资源执行跨进程文件锁 | [队列文件锁：queue_data_source.py:73](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L73) · [全部用法](usage-categories/fcntl.md) |
| `time.sleep` | 同步轮询、重试或等待，单独统计以便检查阻塞边界 | [全部用法](usage-categories/time-sleep.md) |

`signal`、`fcntl`、`killpg` 涉及操作系统边界，不是 asyncio 任务取消的同义写法。这里只记录源码实际用途，不把这些平台相关实现改造成跨平台示例。

## 阅读时始终核对四件事

1. 谁创建任务、线程或进程，谁持有它的引用？
2. 哪一层等待结果，等待会阻塞哪个执行线程？
3. 什么限制在途工作、缓冲结果和共享状态访问？
4. 正常结束、异常、超时或取消之后，谁等待收尾并释放资源？

API 语义与书籍依据见 [SOURCE-CHECK.md](SOURCE-CHECK.md)。本次没有运行 Slime 的训练、模型服务或沙箱；静态命中次数不表示运行次数，也不表示这些路径已经验证通过。
