# 01 · 阅读范围：多组生成任务怎样持续运行

[步骤入口](README.md) · [本步父函数卡](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md) · [前一步](../step-011-generate-and-rm-group/README.md)

## 1. 阅读目标

承接上一部“一组 Sample 分派给多个生成任务，再收齐结果”的模型，本步解释谁持续取下一组、什么时候允许启动，以及完成后怎样补充工作。岗位对应并发控制、背压与任务一致性；本轮先读正常运行路径。

**本步选择本地 AsyncRolloutWorker 分支。** _get_worker 在数据源没有 reader_config 时选择它；存在 reader_config 时选择 DistributedRollout。当前 Coding Agent 示例脚本默认 ROLLOUT_DATA_TRANSPORT=straw，默认走后一支；这里是已确认的本地调度实现阅读，不冒充该脚本默认运行轨迹。 分布式分支使用 Ray actor 及 actor 内部的 asyncio 生成池，见[本步边界核对](04-flow.md#ray-worker-boundary)。

## 2. 指挥官函数与最小前置

- 入口：[AsyncRolloutWorker._loop:178–243](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L178-L243)，负责后台持续调度；本轮重点 179–231。
- 前置：worker 已创建，data_buffer、output_queue、self.concurrency 与共享 GenerateState 已就绪；_thread_main 用 asyncio.run 运行本协程。
- 已读子调用：[generate_and_rm_group](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm_group.md)。这里的一个 Task 对应一整组，它内部才创建逐 Sample 的任务。
- 当前对象接口和 data_buffer 的最短来路见[类卡](02-short-term-memory/classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md)，本次调用前提与并发额度在[父卡输入](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md#worker-input)。线程启动、分布式实现与完整回调先只定位。

## 3. 完整骨架与阅读导航

### 3.1 整体位置

```text
generate_rollout_fully_async
    → _get_worker（选择或复用 worker）
        → 本地 AsyncRolloutWorker.start
            → 后台线程 _thread_main → asyncio.run(self._loop())【本步】
                → 创建组级 Task → generate_and_rm_group【前一步】
                → 完成回调 → output_queue【后续展开】
    → 本地 _generate_rollout_async → get_completed_groups【另一侧消费，后续展开】
```

后台生产与上层消费是配合运行的两条路径，_loop 不会为每个训练 rollout 返回一个结果列表。上游已有 worker 时复用它。分支依据见 [_get_worker:58–79](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L58-L79)，公开入口见 [381–389](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L381-L389)。

### 3.2 完整核心骨架：初始化 → 回收 → 补充 → 发布与等待

下面保留真实调用顺序和必要条件，四段在同一个连续代码块内。教学裁剪仅折叠 try/except 与日志、以及退出外层循环后的等待收尾；保留 t.result 的正常读取与 error 分支，参数保留组级交接所需部分。

```python
# ① 准备本次后台循环的局部状态
active_tasks: set[asyncio.Task] = set()
max_concurrent = self.concurrency
gid_counter = 0

while self.running:
    # ② 回收已完成的组任务
    if active_tasks:
        done = {t for t in active_tasks if t.done()}
        for t in done:
            t.result()
        active_tasks -= done
        if done:
            await asyncio.sleep(0)

    # ③ 检查容量并补充新组
    while (
        len(active_tasks) < max_concurrent
        and self.output_queue.qsize() < max_concurrent
        and self.running
        and not self.paused
    ):
        groups = self.data_buffer.get_samples(1)
        if not groups:
            break
        for group in groups:
            gid = gid_counter
            gid_counter += 1
            task = asyncio.create_task(
                generate_and_rm_group(
                    self.args, group,
                    sampling_params=self.state.sampling_params.copy(),
                    evaluation=False,
                )
            )
            task.add_done_callback(self._make_done_cb(gid, group))
            active_tasks.add(task)

    # ④ 发布状态并让出执行机会
    with self.condition:
        self.active = len(active_tasks)
        self.admission_paused = self.paused
        self.condition.notify_all()
    if self.error is not None:
        raise self.error
    await asyncio.sleep(self.poll_interval)
```

正常路径中，t.result 的值在这里没有赋给业务变量；成功结果交付由已注册的完成回调承担。折叠的异常处理会记录或传播错误，不能把教学省略理解成源码不处理异常。

### 3.3 怎么读、读到哪里

先快速看①，**从③的补充任务进入**，因为它直接调用前一步的组级函数；再回看②怎样回收名额，最后看④怎样让其他任务继续。下面编号仍对应源码执行位置，不表示改变执行顺序。

| 骨架位置 | 看清什么 | 回查与返回 |
| --- | --- | --- |
| [① 局部状态](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md#phase-1) | active_tasks 中存组级 Task，max_concurrent 按组计数，gid 在本次循环生命期内递增 | self.concurrency 来源只查构造器的公式，然后进入③ |
| [② 回收完成任务](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md#phase-2) | done 是哪些 Task；移除后集合大小怎样变化；t.result 与回调交付的职责不同 | 回调内部后读；回到③判断可否补任务 |
| [③ 接纳与创建](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md#phase-3) | 在途组数量与完成队列积压是两个条件；取得一组、创建并登记 Task | 组级生成按已有卡回顾，返回④发布状态 |
| [④ 发布与等待](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md#phase-4) | 给其他线程看的状态如何更新；sleep 让出执行机会后开始下一轮 | 状态发布先当黑箱；Condition、暂停协议与完整失败传播按需补 |

**本轮停止点**：能用一组开始、另一组完成的例子说明“回收 → 看容量与积压 → 取组并启动 → 等待下一轮”。_make_done_cb 的重试、get_completed_groups 的消费细节、关闭时的完整取消，以及分布式 worker 留到后续问题；已有评分表继续复用。

<details>
<summary>退出与错误分支：本轮保留边界，尚不展开</summary>

running=False 后退出外层循环；源代码随后对剩余 active_tasks 调用 asyncio.wait(timeout=30)，这不等于保证所有任务都已完成，也不是本轮的取消机制结论。错误处理及外层 _thread_main 的收尾见原函数 168–175、233–243。

</details>

源码固定提交：18868a79b0b083a093798a94ed0f8cb4f71b9c14；[证据记录](references/source-evidence.json)。本步只创建和接续本地阅读记录。
