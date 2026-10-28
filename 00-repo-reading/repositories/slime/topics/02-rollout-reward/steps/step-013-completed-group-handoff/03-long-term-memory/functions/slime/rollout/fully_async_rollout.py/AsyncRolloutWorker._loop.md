# AsyncRolloutWorker._loop

- 源码定位：[slime/rollout/fully_async_rollout.py:178–243](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L178-L243)。
- 首次接触：Step 011 作为调用者定位；2026-10-26 用户确认开启 Step 012，开始独立阅读。
- 最近认识更新：2026-10-26，用户表示①能看懂，能概括完成任务移出集合及继续取输入；组与样本的单位、Task 登记、状态发布和 poll_interval 仍需澄清。以下解释尚待进一步反馈。

后台线程 _thread_main → asyncio.run(**本方法**) → 组级 Task → [generate_and_rm_group](../sglang_rollout.py/generate_and_rm_group.md)；完成回调把正常结果交给 output_queue，上层另行消费。

## LLM 整理：使用场合、具体内容与心智模型

1. **使用场合**：本地 worker 已创建，需要持续从数据源启动一组组生成，服务多次上层 rollout 调用。本步选择 AsyncRolloutWorker；数据源带 reader_config 的分布式分支不是本方法。
2. **具体内容**：维护组级 Task 集合，回收完成项，在在途数量和完成结果积压允许时补充新组；发布状态并让出执行机会。回调承担结果入队，本协程长期运行，正常退出返回 None。
3. **建议构建的心智模型**：

   > 一个持续补充工作的循环：先移出完成任务，再看能否启动下一组，登记后让组任务继续运行。
   >
   > active_tasks 是本循环登记的组任务；output_queue 是已完成、等待消费的组结果。两者分别检查，任一达到接纳阈值都暂缓补新组；暂停接纳不等于取消已经启动的组。

4. **调用代码**（同文件 _thread_main:168–175，错误与收尾只定位）：

   ```python
   asyncio.run(self._loop())
   ```

## 本场景的输入与输出

<a id="worker-input"></a>

**输入**：显式参数只有 self。先用 [AsyncRolloutWorker 类卡](../../../../classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md)认出当前使用的对象接口；完整字段和内部实现按需回查。

| 已有字段 | 来路与当前用途 |
| --- | --- |
| self.data_buffer | 上层传入的输入源；本轮只使用 get_samples(1) 取得组列表，见[最短来路](../../../../classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md#data-buffer-origin) |
| self.concurrency | 构造器按组计算的接纳阈值，不直接等于逐 Sample 的 semaphore 容量 |
| self.output_queue | 构造器创建的标准库 queue.Queue；保存完成组，构造时未设硬容量 |
| self.state | 已有 [GenerateState](../../../../classes/slime/rollout/sglang_rollout.py/GenerateState.md)，本层取 sampling_params 副本 |
| self.running / self.paused | 外层继续运行、内层允许接纳的控制状态 |
| self.condition / self.active / self.admission_paused | 对外报告任务数量与暂停状态；线程配合暂作黑箱 |
| self.error / self.poll_interval | 错误传播标记与循环等待间隔；正常场景 error=None |

**教学场景**：worker 已构造，self.concurrency=2，未暂停，完成队列最初为空；数据源可提供组 A、B、C。这里的 2 是构造后的组阈值，不是项目默认配置。先只看正常完成，不运行真实生成器。

**输出与副作用**：本方法不会 return 一批 Sample。运行中创建组级 Task、注册回调、维护局部 active_tasks，并更新共享状态快照；完成回调另行写入 output_queue。running=False 后进入源码收尾，协程正常结束时返回 None。

<details>
<summary>并发数字从哪里来：只回查必要公式</summary>

[_get_worker:69–72](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L69-L72)创建本地 worker 时，传入 sglang_server_concurrency × 引擎数。构造器 88–89 将它除以 n_samples_per_prompt 并至少取 1，再乘 fully_async_group_prefetch_factor，得到 self.concurrency。逐 Sample 的 semaphore 仍由 GenerateState 独立控制，prefetch 放大组池不放大该 semaphore。

</details>

<a id="phase-1"></a>

### ① 准备局部状态（179–181）：本循环记住哪些组任务？

```python
active_tasks: set[asyncio.Task] = set()           # [1a]
max_concurrent = self.concurrency               # [1b]
gid_counter = 0                                # [1c]
```

- **[1a] 空集合起步**：登记的是 Task 对象，每个 Task 对应一次 generate_and_rm_group；完成项在②真正移除前仍属于此集合。
- **[1b] 取得组阈值**：后续用它分别检查集合大小和完成队列长度。组内 Sample 生成名额仍受已有 semaphore 控制。
- **[1c] 准备组标识**：每启动一个组就增加 gid，供完成回调关联结果；它是本循环的局部计数，不是 Sample.index。

**交接**：外层 while self.running 开始重复②③④；首次 active_tasks 为空，可先进入③理解核心动作。

<a id="phase-2"></a>

### ② 回收完成任务（185–197）：完成以后怎样允许再补一组？

以下正常路径折叠了 t.result 周围的异常记录；真实源码会记录异常，不把它当成没有错误分支。

```python
if active_tasks:
    done = {t for t in active_tasks if t.done()}  # [2a]
    for t in done:
        t.result()                              # [2b]
    active_tasks -= done                        # [2c]
    if done:
        await asyncio.sleep(0)                  # [2d]
```

- **[2a] 找到已经结束的 Task**：这里只检查完成状态，不等待尚未完成的组。
- **[2b] 读取结束状态**：正常返回值未赋给业务变量；结果交付已由回调负责，完整源码也在这里观察异常并记录。
- **[2c] 从登记集合移除**：比如原有 {TA, TB}，TA 完成并被移除后留下 {TB}，③看到的数量便从 2 变为 1。这里移除的是本循环的 Task 登记，不是把生成结果丢弃；结果交付由完成回调和队列承担。
- **[2d] 给已排队的回调执行机会**：本轮检查得到的 done 集合非空时，完成回收后才执行 sleep(0)。这会把控制权交还事件循环，让其他就绪任务/回调有机会运行；不是直接将控制权交给下面的 while。当前 _loop 恢复以后，才继续③。它是让出执行机会，不是为某个任务设置“可以睡眠”的状态；重试内容留给回调阅读。

**交接**：更新后的 active_tasks 进入③；是否还接新组，要同时看完成结果队列。

<a id="phase-3"></a>

### ③ 接纳与启动新组（198–223）：还有位置，为什么也可能不接任务？

```python
while (                                         # [3a]
    len(active_tasks) < max_concurrent
    and self.output_queue.qsize() < max_concurrent
    and self.running
    and not self.paused
):
    groups = self.data_buffer.get_samples(1)      # [3b]
    if not groups:
        break
    for group in groups:
        gid = gid_counter                       # [3c]
        gid_counter += 1
        task = asyncio.create_task(
            generate_and_rm_group(
                self.args, group,
                sampling_params=self.state.sampling_params.copy(),
                evaluation=False,
            )
        )
        task.add_done_callback(self._make_done_cb(gid, group))  # [3d]
        active_tasks.add(task)
```

- **[3a] 同时看两个数量和控制状态**：集合未满、完成队列未积压到阈值、仍运行且未暂停，才继续补充。active_tasks 统计已登记的组任务，output_queue 统计待消费结果；不是同一个计数。这里的 qsize 门槛是接纳控制，队列本身未设置硬容量。
- **[3b] 从数据源取组列表**：参数 1 表示请求一组，接口仍返回列表，因此下面还有 for group。取不到时只退出本次补充的内层循环，worker 仍在外层循环中运行。
- **[3c] 为该组创建 Task**：分配 gid，把 group 与参数副本交给前一步的 generate_and_rm_group。本层的一个 Task 内部可以有多个逐 Sample 的生成任务。
- **[3d] 登记完成处理与活跃任务**：_make_done_cb(gid, group) 先返回一个回调，add_done_callback 注册它；不是在这一行等待组结果。create_task 已安排任务执行，但不会自动修改 active_tasks。最后的 add 才把 Task 放入本循环的集合，供后续计数与回收。gid 是组标识，任务的创建发生在 create_task 调用处。

只观察 Task 登记：假设组阈值是 2，队列没有积压、未暂停，已经登记了 TA，现在准备创建 TB。

| 执行到哪里 | active_tasks 的内容 | len(active_tasks) |
| --- | --- | --- |
| 创建 TB 之前 | `{TA}` | 1 |
| `task = asyncio.create_task(...)`，TB 已被安排执行 | 仍是 `{TA}` | 仍是 1 |
| `active_tasks.add(task)`，把 TB 登记进去 | `{TA, TB}` | 2 |

add 之后再检查接纳条件，`2 < 2` 为 False，便停止补充。这张集合若没有登记新 Task，就不能真实反映已接纳的组数；后面也无法通过它找到该 Task 来回收。

除了组任务集合，还要看完成队列：即便 active_tasks 已是 0，只要 output_queue.qsize() 已到 2，本例仍暂缓接纳。get_samples(1) 请求的是一组，可能含多个 Sample。实际队列可能因已有任务继续完成而超过阈值，不能把它当成 maxsize=2 的硬容量；暂停也只阻止新接纳，不由这个 while 自动取消已有 Task。

**按需回查**：[组级函数卡](../sglang_rollout.py/generate_and_rm_group.md)接住 group 并返回结果；[_make_done_cb:246–275](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L246-L275)本轮只读“返回回调”的接口，内部后续展开。

**交接**：不再满足接纳条件或本次没有输入时，进入④更新状态和等待。

<a id="phase-4"></a>

### ④ 发布状态并等待（225–231）：其他任务什么时候获得执行机会？

```python
with self.condition:                            # [4a]
    self.active = len(active_tasks)
    self.admission_paused = self.paused
    self.condition.notify_all()
if self.error is not None:                       # [4b]
    raise self.error
await asyncio.sleep(self.poll_interval)          # [4c]
```

- **[4a] 对外报告状态**：报告当前登记的组任务数和暂停状态。当前先把它视为已提供的控制接口；pause 的等待条件与 Condition 协议留在[按需参考](../../../../../../step-012-async-rollout-worker-loop/references/worker-class-full-context-2026-10-26.md#pause-handshake)，不妨碍先跟随正常循环。
- **[4b] 检查已记录的错误**：正常例子跳过。若其他路径记录了 error，本层抛出并由外层处理；完整失败传播按后续问题展开。
- **[4c] 让出执行机会并等待下次检查**：构造器中 poll_interval=0.01，表示这轮处理后先异步等待约 10 毫秒，再有机会检查下一轮。await 会挂起当前 _loop 协程，让同一事件循环里的组任务和回调运行；不会把整个事件循环一起停住，也不是每个生成任务的超时。避免无事可做时不停空转，同时保留后续轮询的机会。

把③和④放回同一段执行时间中，可以这样观察（教学顺序，任务何时真正完成取决于运行）：

```text
_loop 创建 TB → 把 TB 加入 active_tasks → 发布当前数量
    → await sleep(0.01)：_loop 暂时挂起，组任务/回调有机会执行
    → _loop 被调度继续：回到②，检查并移除已完成项
    → 回到③：再检查是否能接下一组
```

等待结束时，组任务可以仍未完成；②只回收实际已完成的 Task。已有名额、结果队列与暂停条件共同决定是否接新组。

**本轮能追踪的变化**：已有组完成 → ②移除登记 → ③重新检查名额和结果积压 → 允许时接新组。回调如何入队、消费方如何取走，本轮先使用其接口效果。

**读完返回**：本方法持续循环，正常运行没有逐组返回；完成结果走回调与队列。关闭后的 asyncio.wait(timeout=30)、完整回调/消费逻辑及分布式对应关系仍是后续边界。

## 我的直接表述（原话）

用户确认开启本步：

> 好的那么请继续吧
> 开启下一个step吧

开始时尚无对本方法内部机制的直接复述；本轮后续反馈见下方。前一步对组到单任务分派的认识保留在[已调取的组级函数卡](../../../../../../step-012-async-rollout-worker-loop/02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md)，不转写成本方法已经掌握。

分支定位追问：

> 也就是说这个分布式其实可以在ray上实现吗？
> 是这个意思吗？

已核对分布式分支实际用 Ray actor，actor 内用 asyncio 组任务池并调用 generate_and_rm_group；它的循环是 _GenerationActor._produce，本卡仍记录本地 _loop。问题与证据见[本步分支说明](../../../../../../step-012-async-rollout-worker-loop/04-flow.md#ray-worker-boundary)。此处为助手核对，尚无用户对此实现关系的进一步复述。

本轮对四段的直接反馈：

> 好的那么我们现在还是应该看一下这里的这个asyncrolloutworker
> 好的那么请来一点点理清楚这里的的四个部分吧
> 首先是这里的task我差不多是理解的
> 然后是这里的并行
>
> 然后呢是什么？
>
> 回收这里的tasks？
> 我不是特别理解了
> 当前应该看看什么呢？
> 要不你带着我一点地iankanba
> 最开头的1我是能看懂的
> 第二各部分是
> 如果有任务已经完成了
> 那么就可以把这个active task剪掉了
>
> 然后之后是看一下这里的active的组如果小于的就从data buffer里面再拿一个sample是我的理解
> 然后再通过拿到group id的方式
> 再发送一个task
> 为什么最后有一个active tasks.add task？ 我有点没理解
>
> 以及最后一个状态状态部分我其实没有特别了解
> 这里的poll interval是做什么的呢？
> 我觉得需要看清楚？
>
> 请和我一步步过一下吧
>
> 主要针对我没有清楚叙述出来流程的部分

源码校准：用户已表达完成项可以从集合移除；取数单位是一组而非单个 Sample。Task 创建与登记、状态报告与异步等待的解释分别放在 [3d] 与 [4a]–[4c]，等待后续反馈。

本轮对控制权、输入来源与对象字段的追问：

> 这里的done我的理解是 如果有一个人物完成了
> 那么就会进入sleep的状态 同时这里变成可以或者需要sleep的情况
>
> 这里机会让到这里的下面一个while loop
> 是我的理解
>
> 这里进入的条件我也可以理解
> 但是这里的data buffer 我觉得我需要清楚是哪里来的
> 这个是我觉得需要了解的数据结构
>
> 下面的内容比较好理解
> 其实就是根据我们之前读得generate and rm group来生成这里的task
>
> 所以这个其实也好理解
>
> 但是最后一个部分在做什么 我其实就不是特别理解
> 这里的四我需要额外的理解
>
> 我觉得主要会变成
> 当前这个asyncrollout worker 是否需要单独开一个class 的short term memory？
> 这样子能够加深对于这个class的理解 主要是为什么需要某些字段

助手校准：sleep(0) 让出给事件循环，恢复后才继续下方 while；data_buffer 的对象来路和状态字段的读取方已补到类卡，尚待反馈。

本轮收束反馈：

> 好的 我觉得 我差不多理解了
> 那么读完了这个step的话 我应该需要读什么部分呢/

这是对当前主线的概括性反馈，保留已标出的黑箱和未知；下一入口建议见[完成结果的交接](../../../../../../step-012-async-rollout-worker-loop/04-flow.md#next-completed-result-handoff)。

## 尚不清楚

- 用户已将组级生成与 Task 创建联系起来；data_buffer 来源与两类队列的区分已补源码，尚待反馈。
- 已完成项从集合移除已有用户表述；sleep(0) 让出给事件循环与恢复后继续③的区别仍需确认。
- 第④段当前只保留“报告状态”的作用；暂停确认、数量发布与通知读取方的完整解释已移到参考，按用户要求暂作黑箱。
- 回调中的中止与重试、结果消费、关闭与取消、Condition 的完整跨线程协调，尚未展开。
- 已最小确认 DistributedRollout 使用 Ray actor、actor 内有独立 asyncio 生成池；其调度、数据协议与本地 _loop 的具体差异尚未展开，不将这次定位视为已读懂。

<details>
<summary>来源与验证边界</summary>

- 本轮逐步澄清：[Task 登记、状态与轮询](../../../../../../step-012-async-rollout-worker-loop/04-flow.md#task-registration-and-polling)。poll_interval 默认值依据构造器第 103 行；本次表格与时间线为静态教学推演，未运行 worker。
- 分布式边界：[Ray actor 创建](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_distributed.py#L532-L558)、[actor 内组任务池与生成交接](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_distributed.py#L330-L388)。只作范围定位。
- 源码提交 18868a79b0b083a093798a94ed0f8cb4f71b9c14，本地 HEAD 与本轮查询的 THUDM/slime 官方 main 一致，源码工作区干净。
- [构造器与字段](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L82-L110)、[线程入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L167-L175)、[方法主体](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L178-L243)、[完成回调边界](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L246-L275)。
- [_get_worker 的实现选择](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L58-L79)；[示例默认 straw](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/run_qwen38_27b_fully_async.sh#L130)。
- [本步形成过程](../../../../../../step-012-async-rollout-worker-loop/04-flow.md#step012-start)；[源码证据](../../../../../../step-012-async-rollout-worker-loop/references/source-evidence.json)。
- 主干与当前函数的正常路径 AST 对照；未运行真实 worker、模型、沙箱、队列服务或训练。教学场景不是实际运行报告。

</details>
