# process_parallel

[返回 run_naive 的 executor 调用](../../../../../../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md#fleet-executor-handoff) · [本步 scope](../../../../../../../01-scope.md#reading-navigation) · [本轮讨论](../../../../../../../04-flow.md#return-to-executor)

- 源码定位：[strategies.py:34](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L34)。
- 首次接触：Step 000，2026-11-04，用户要求从 setup 返回 executor。
- 最近认识更新：用户已表述返回值不一定是奖励，当前进一步追问 process_fn 是否由外部传入，以及具体对应哪个函数；来源关系尚待反馈。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：run_naive 的 setup 正常返回后，以本函数作为 executor 执行任务；当前 recycle=False。
2. **具体内容**：为任务安排执行，汇集返回值或捕获的异常，按输入顺序交回结果列表。
3. **建议构建的心智模型**：

   > 外层安排一批任务；内层 _one 定义一条任务的处理动作。领取成功后，先运行处理函数，退出时释放环境。并发发生在 Python 调用程序中，具体环境操作通过 fleet 和 handle 完成。

4. **调用代码**：来自 run_naive:94；本场景 executor 在外层被设置为 process_parallel。

   ```python
   return executor(fleet, fleet.tasks, process_fn, concurrency)
   ```

## 本场景的输入与输出

### 1. 输入

沿用当前正常场景，环境准备已完成，任务为 t1、t2；下述结果名称为示意，没有执行真实集群任务。

| 参数 | 本场景含义 |
| --- | --- |
| fleet | run_naive 使用的同一个 SandboxFleet 管理对象 |
| tasks | 先前 fleet.load_tasks 已加载的 [t1, t2]，两条任务均使用 image-a；进入本函数时 Task 已经存在 |
| process_fn | 接入方的同步处理函数，接收 task 和 handle；需覆盖本次任务所需的执行、等待与结果收集，再返回结果记录 |
| concurrency | 2，本次进入线程池分支 |

executor 是调用方 run_naive 中的参数名，本场景指向 process_parallel；本函数内部的 ex 才是 ThreadPoolExecutor 实例，两者需要分清。

<a id="process-fn-origin"></a>

**process_fn 是一个接收函数值的参数。** 调用方决定传入哪个函数，执行器最终使用 process_fn(task, handle) 调用它。

当前 SWE-bench 示例的实际代码是 fleet.run(_record(swebench_probe), ...)。为看清实参，等价拆成下面两行；callback 是这段解释中临时命名的局部变量。

```python
callback = _record(swebench_probe)
results = fleet.run(callback, strategy=strategy,
                    concurrency=max_concurrent)
```

1. _record(swebench_probe) 先执行，返回它内部定义的 fn；这一步尚未执行探针。
2. fn 作为第一个实参传入 fleet.run，在该方法中由形参 process_fn 接住。
3. 同一个函数值经 run_naive 传给 process_parallel，最终在 process_fn(task, handle) 这一行被调用。

因此当前要看的实际回调是 [run_swebench_fleet.py 中的 _record.fn](../../examples/run_swebench_fleet.py/_record.fn.md)。它内部才调用 [swebench_probe](../adapters/swebench.py/swebench_probe.md)，再将返回文本包装成字典。调用方如何构造并传入它，见 [main](../../../../../../../02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md)。

### 2. 输出

```python
results = [result_for_t1, result_for_t2]
```

1. 正常路径中，每个元素保存 process_fn 返回的数据，可以是奖励、执行状态或其他结果对象；本层不规定它必须是 reward。
2. results[i] = fut.result() 把这份数据保存到原任务的位置，不随完成顺序改变。Future 完成表示 _one 调用已经结束，与返回数据里是否含有“完成”标记是两回事。
3. 下方 except Exception 捕获的失败放在对应位置，供调用方识别。
4. 结果返回 run_naive，随后由其 finally 决定整批清理。

### 3. 并发路径的核心骨架

当前先观察 [2] 的单任务动作，再接回 [3]–[5] 的整批安排。以下为 concurrency=2 的教学裁剪，省去日志、统计和 concurrency<=1 的串行分支；保留领取、释放、结果位置和异常交付。

```python
def process_parallel(fleet, tasks, process_fn, concurrency):
    # [1] reserve result slots
    results = [None] * len(tasks)

    # [2] define one task's work; this body runs when called
    def _one(task):
        handle = fleet.acquire(task)          # [2.1]
        try:
            return process_fn(task, handle)   # [2.2]
        finally:
            fleet.release(handle)            # [2.3]

    # [3] submit the tasks
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = {ex.submit(_one, t): i for i, t in enumerate(tasks)}

        # [4] collect completed work into the original slot
        for fut in as_completed(futs):
            i = futs[fut]
            try:
                results[i] = fut.result()
            except Exception as e:
                results[i] = e

    # [5] return the batch results
    return results
```

1. **[1] 留出结果位置**：两条任务先对应 [None, None]。
2. **[2] 定义单任务动作**：执行到 def 时只是定义 _one，尚未领取环境。每次真正调用 _one 才按下方三步处理任务。
3. **[3] 提交任务**：把整个 _one 和每条 task 交给线程池，保存外层 Future 到输入位置的对应关系。提交过程中，线程就可能开始执行任务。
4. **[4] 等待并收集结果**：as_completed 等待 _one 整体结束，包括 finally 中的环境释放，再交出该 Future。fut.result() 取回其结果或抛出异常，随后写入原位置；例如 t2 先完成，先填写 results[1]。
5. **[5] 返回整批结果**：离开线程池上下文后，向 run_naive 返回 results。

#### 3.1 当前先看 _one 的三步

1. **[2.1] 领取环境**：fleet.acquire(task) 接收已有 Task，并返回该任务所用环境的 handle；不在这里生成 Task 数据。当前预热命中路径领取已有环境，冷创建属于另一分支。
2. **[2.2] 执行任务处理**：process_fn(task, handle) 收到题目与环境。题目初始化、Agent 交互和评分由这个回调的具体实现承担。
3. **[2.3] 释放环境**：领取成功后，处理过程退出时由 finally 调用 fleet.release(handle)。

_one 的返回值是一条任务的结果；process_parallel 的返回值是整批任务的结果列表。

<a id="long-agent-lifetime"></a>

#### 3.2 长时间运行的 Agent 怎样结束这一轮调用

1. process_fn 可以长时间运行；它没返回时，对应线程和环境仍被该任务占用。
2. 当前外层 Future 只跟踪 _one 的完成。如果 process_fn 仅返回后台任务 ID 或另一个 Future，本层不会继续追踪远端任务，仍会进入释放流程。
3. 返回的数据含义由 process_fn 决定。本层保存返回值或异常，不自动判断 Agent 成功、失败或 reward。
4. 本函数未设置完整 Agent 的运行时限；长任务或卡住的任务可能阻塞整批返回。相关等待、超时和取消责任要沿回调及底层接口继续核对。

实际 OpenHands 回调、同步与异步边界以及本地受控验证见[长任务与结果交付说明](../../../../../../process-parallel-lifetime.md)。

<details>
<summary>当前省略的分支和后续源码入口</summary>

1. concurrency<=1 时，在调用线程中逐项调用同一个 _one，不创建线程池；仍写回原位置并返回列表。
2. 统计与日志包装已折叠，不改变本轮关注的领取、处理、释放和结果位置。
3. acquire、release 的内部实现继续作为后续入口；当前不为它们预建方法卡。位置分别为 fleet.py:1426、1663。
4. ThreadPoolExecutor、Future、as_completed 的内部机制按实际疑问回查，不要求先展开整个并发库。

</details>

## 我的直接表述（原话）

<details>
<summary>此前关于进入执行器与长任务的疑问</summary>

本轮切换入口的要求，节选：

> 这么看下来这里的sandboxfleet的内容还是特别的多了
>
> 那么我们返回去看一下这里的executor的部分吧

随后用户提出：

> 这里我的理解就是这里通过treadpoolexecutor来执行多个可能需要并行的任务?
> 但是从这里看的话
> 是不是没有考虑到如果一个agent的运行是一个比较长期的内容呢?
> 以及这里的结果或许不是那么明朗呢?
> 你确定这里的executor是这么简单的吗?
> 就是指吧这个prcess_fn 发出去了之后
> 直接通过这种方式运行之后直接拿到结果?

</details>

本轮用户归纳：

> 好的 我的简单理解是
> 这里的fn 返回的并一定是一个真实的奖励什么的
> 可能只是一个执行完成之后的信号
> 然后把这一部分的内容写进去
> 这是我的理解?

随后用户进一步确认函数的来路：

> 部队啊
> 我只是向看一下这里的这个process_fn
> 还是说这里的这个process fn是被传入进来的呢?
> 然后这个传入的process_fn?
> 我不是特别理解了?

## 尚不清楚

1. process_fn 作为形参接收外部函数值，及当前对应 _record 返回的 fn 的关系，尚待用户反馈。
2. 用户已表述返回值不限定为奖励；长回调、远端任务和外层 Future 的完成边界仍待确认。
3. 实际 Agent 回调如何定义结束、产生结果并处理超时或取消，尚未逐函数阅读。
4. Future 的完成顺序与结果位置、acquire 和 release 的内部机制仍保留为后续问题。

<details>
<summary>来源、验证与完整例子</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 主体：strategies.py:34–79；单任务核心：48–54；线程池分支：70–79。
- 默认执行器选择：fleet.py:2093；本次 recycle=False，未进入替换执行器的分支。
- 调用与返回：run_naive 在 strategies.py:94 调用，随后进入 95–97 的 finally。
- 示例仅说明结果形状与位置，经静态源码核对；没有运行真实任务或集群实验。
- 原始过程：[Step 000 · 返回 executor](../../../../../../../04-flow.md#return-to-executor)。
- 本轮验证：用原始 process_parallel 和替代的环境接口做了两次受控本地实验；记录见[长任务说明](../../../../../../process-parallel-lifetime.md#5-本次受控验证)，不涉及真实 Agent 或集群。

</details>
