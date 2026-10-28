# 01 · 阅读范围：完成结果的入队与领取

[步骤入口](README.md) · [函数索引](02-short-term-memory/overview.md) · [前一步](../step-012-async-rollout-worker-loop/README.md)

## 1. 阅读目标

接上 Step 012 的 Task 注册点，弄清三个时刻：**准备并注册回调 → 任务结束后回调入队 → 消费方调用方法取组**。本步先追踪一组正常完成的结果，保留组编号与结果的对应关系。

**本轮状态：2026-10-26 首轮范围已收束。** 四步的阅读入口和已讨论内容保留在下方；后台入队、上层领取及过滤收集的交接见[任务链路总结](05-task-flow.md)。具体机制的理解与未知按各函数卡原样保留。

继续沿用本地 AsyncRolloutWorker；生成成功、返回 list，结果中没有 ABORTED/PENDING。本轮不展开异常、取消、中止重试与输入快照复制的内部机制。get_completed_groups 的 queue.Empty 是正常的“已经没有可取结果”停止条件，必须保留。父卡已保留正常入队与交回重试的分支关系；prepare_retry_group 以输入输出为界，复制、分段会话和重试调度内部留白。

## 2. 入口与最小前置

- 从已读 [_loop 的注册行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L222) 进入本步；[_loop 背景卡](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md)保留完整旧骨架。
- 两个主读方法是 [_make_done_cb](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L246-L275) 和 [get_completed_groups](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L147-L161)。前者创建回调，返回的 _cb 组织完成处理；后者由消费方另行调用。它们不是彼此直接调用的上下级函数。
- **领取方法的直接调用方是 _generate_rollout_async**：它先取得同一个 worker，再于 [312 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L306-L321) 调用 worker.get_completed_groups(...)。本步已确认用[父函数卡](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md)保存整体骨架，重点展开 306–336 行的接收、过滤与收集；其他部分只认职责与接口。
- 最小已有数据：gid 是 _loop 的局部组编号；group 是创建该 Task 时的输入组；self.output_queue 是同一个 worker 的完成结果队列。Task 的正常返回值来自已读 generate_and_rm_group。
- [worker 类卡](02-short-term-memory/classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md)仅用于认出对象接口。输入源 data_buffer 与完成队列 output_queue 分开；Sample 字段、线程协调和队列内部继续留白。

## 3. 核心骨架与阅读导航

<a id="overall-position"></a>

### 3.1 整体位置：回调入队与上层领取

**本步 scope 框定的是“完成结果入队 → 上层领取并收集”这段交接。两个 worker 方法是 AsyncRolloutWorker._make_done_cb 和 AsyncRolloutWorker.get_completed_groups。** 后者的直接调用方 _generate_rollout_async 已建立父函数卡：整体保留准备、收集与交付骨架，本轮重点读接收、过滤与收集。

行号来自 `slime/rollout/fully_async_rollout.py`（固定版本 `18868a79`）。图内只标当前需要的“调用 → 定义 → 返回后接续”位置，其余来源放在下方折叠区。

```text
generate_rollout_fully_async（本地 worker 分支）
│
├─ _get_worker：取得 worker，首次创建时启动后台
│   └─ 后台 AsyncRolloutWorker._loop【Step 012 背景】
│       ├─ 创建 Task → generate_and_rm_group
│       ├─ _make_done_cb → 返回 _cb → 登记到 Task【已讨论】
│       └─ Task 结束后：事件循环调用 _cb(done_task)【已讨论，记在父卡】
│           └─ 将 (gid, result) 放入 worker.output_queue
│
└─ run(_generate_rollout_async(...))
    └─ _generate_rollout_async【本轮已展开收集阶段】
        ├─ _get_worker → 取得同一个 worker
        ├─ worker.get_completed_groups(limit=...)  # 调用 312 → 定义 147【已讨论】
        │   ├─ 从 worker.output_queue 取出组记录
        │   └─ 返回 completed 列表
        └─ 接住组记录 → 过滤 → 加入 collected      # 返回后接续：314【本轮展开】
```

本轮从 get_completed_groups **返回 _generate_rollout_async 的调用处**，沿组记录看接收与去向。_cb 负责入队，领取方法由上层主动调用；两侧使用同一个 worker 的 output_queue，运行可以交错进行。领取开始时队列为空，可以直接返回 []。

| 函数 | 本步阅读深度 |
| --- | --- |
| AsyncRolloutWorker._loop | 已读背景；只回看创建 Task 和登记回调的位置 |
| AsyncRolloutWorker._make_done_cb（含内部 _cb） | 已讨论创建并返回回调、完成后的结果处理；共用父卡，重试内部按已有黑箱边界 |
| **AsyncRolloutWorker.get_completed_groups** | **已讨论：完整方法 147–161 行；返回上层继续看组记录的去向** |
| [_generate_rollout_async 父卡](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md) | 本轮重点：306–336 行的接收、过滤、保留或丢弃及无结果时等待；准备与最终交付只保留骨架，子函数内部留白 |

外层 generate_rollout_fully_async 与 _get_worker 在图中用于定位入口及对象来路，不在这里展开完整实现。

<details>
<summary>图中关系的源码依据与旧版</summary>

- 入口和本地分支：fully_async_rollout.py:381–389；创建或复用 worker：58–79。
- 创建组级 Task 与登记回调：214–223；回调由 _make_done_cb:246–275 返回，正常入队位于 273。
- 调用方取得 worker：282；主动领取：312；队列取出并返回：155–161；过滤后的收集：314–321。
- [完整源码摘录](references/source-excerpts.md) · [本轮修改前的 scope](references/scope-before-consumer-call-context-2026-10-26.md) · [调用位置修正过程](04-flow.md#step013-consumer-call-context)。此前图示演变见[首次修正](04-flow.md#scope-position-diagram-revision)。

</details>

### 3.2 完整核心骨架

下面把同文件的定义与调用片段放在一个代码块中供定位，**不是可自顶向下执行的独立脚本**。先保留正常完成路径；回调工厂的输入备份、回调的失败分支暂省略，原文见[完整源码](references/source-excerpts.md)。保留 gid、group、result、limit，因为它们正是本步要追踪的交接。

```python
# 第一步的调用处：_loop:222，先得到回调函数，再登记它
task.add_done_callback(self._make_done_cb(gid, group))

# 第一步、第二步：_make_done_cb:246–275，创建回调与完成后的处理
def _make_done_cb(self, gid, input_group):
    # 省略 retry_group 的准备，只跟随正常完成路径
    def _cb(done_task):
        # 第二步：Task 结束后执行这段回调
        result = done_task.result()
        self.output_queue.put((gid, result))
    # 第一步：创建阶段返回回调函数
    return _cb

# 第三步：get_completed_groups:147–161，消费方调用时最多取 limit 组
def get_completed_groups(self, limit=None):
    completed = []
    while limit is None or len(completed) < limit:
        try:
            completed.append(self.output_queue.get_nowait())
        except queue.Empty:
            break
    return completed

# 第四步：回到 _generate_rollout_async，父卡进一步展开收集阶段
async def _generate_rollout_async(args, rollout_id, data_buffer):
    worker = _get_worker(args, data_buffer)
    target = args.rollout_batch_size
    collected = []
    # 省略 worker.resume、过滤器准备、日志与统计
    while len(collected) < target:
        for _gid, group in worker.get_completed_groups(limit=target - len(collected)):
            verdict = call_dynamic_filter(...)
            if verdict.keep:
                collected.append(group)
        # 省略本轮无结果时的等待与状态处理
    # 省略最终结果整理与返回
```

第四步展示调用方的局部上下文，选择本地非 straw 的正常接收路径。阅读第三步时先定位这里的调用，再进入 get_completed_groups，读完沿返回值回到调用处；[父函数卡](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md#collect-filter-retain)继续展开接收、判定、保留或丢弃及等待；不要求逐项深入全函数的依赖。过滤仍由消费方决定；“取走一组”不保证“最终保留一组”。骨架省略的等待、丢弃处理和最终整理不作为可运行实现。

### 3.3 每次读哪一段、读到什么程度

<a id="reading-order"></a>

先接回与本步直接相关的**阅读推进顺序**。下面的“第一步、第二步……”是 Step 013 内部的阅读顺序，与上方代码旁的标记对应；实际源码调用关系看 3.1。

```text
Step 010 · generate_and_rm                    单次生成与奖励
   ↓
Step 011 · generate_and_rm_group              组内并发与汇总
   ↓
Step 012 · AsyncRolloutWorker._loop           持续取组、创建与登记 Task
   ↓
Step 013 · 完成结果的交付
   ↓
第一步 · _make_done_cb：创建并返回回调        已讨论
   ↓
第二步 · 内部 _cb：任务结束后处理结果        已讨论；与第一步共用父卡
   ↓
第三步 · get_completed_groups：领取完成结果  已讨论
   ↓
第四步 · 回到 _generate_rollout_async        已讨论：父卡的接收、过滤与收集
   └─ 已回查 call_dynamic_filter             返回 verdict.keep 的分支
```

前序范围：[Step 010](../step-010-generate-and-rm/01-scope.md) · [Step 011](../step-011-generate-and-rm-group/01-scope.md) · [Step 012](../step-012-async-rollout-worker-loop/01-scope.md)。这条线用于接续阅读，不代表各步骤已全部掌握；实时接续仍见[唯一路线](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。

**本步局部导航：**

| 阅读顺序 | 卡片与段落 | 本段只看清什么 | 读完接回哪里 |
| --- | --- | --- | --- |
| 第一步 · 已讨论 | [_make_done_cb：创建并返回回调](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._make_done_cb.md#phase-1) | 返回的是 _cb 函数，登记时不读取该 Task 的结果 | 回到 _loop:222，把返回的函数登记到 Task |
| 第二步 · 已讨论 | [内部 _cb：父卡的第二阶段](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._make_done_cb.md#phase-2) | Task 结束后读取 result；正常入队与交回重试的分支，重试内部留白 | 正常结果留在 output_queue；下一处阅读上层怎样领取，两者不直接互相调用 |
| 第三步 · 已讨论 | [get_completed_groups](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.get_completed_groups.md) | 每次取走一个 (gid, group)，达到 limit 或遇空时返回 | 回到 _generate_rollout_async:312 的 for 循环，接住返回列表 |
| 第四步 · 父函数 | [_generate_rollout_async：收集阶段](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md#collect-filter-retain) | 解包组记录，依据 verdict.keep 决定去向；区分 drained 与 len(collected) | 收够 target 后交给最终整理；其内部先停在接口 |
| 第四步内回查 · 已讨论 | [call_dynamic_filter](02-short-term-memory/functions/slime/rollout/filter_hub/base_types.py/call_dynamic_filter.md) | 区分过滤前的已有奖励统计、调用 fn 与统一返回判定 | 回到父卡的 verdict，再看保留或丢弃分支；具体 fn 策略留白 |

第一步和第二步是**同一张函数卡的两个阅读观察点**；导航中的“已讨论”不表示卡片内的未知已全部解决。第三步已有用户理解反馈；用户已确认第四步采用父函数卡，重点记录收集阶段，其余阶段保留整体位置与接口。 随后确认将 call_dynamic_filter 独立建为子卡，作为第四步内部回查，不增加新的全局步骤。

本轮已按以下停止位置收束，详见[05 的收束与边界](05-task-flow.md#scope-closure)。

**停止位置**：能区分 _make_done_cb 返回的函数、_cb 的入队副作用、get_completed_groups 返回的组记录，以及父函数如何筛选并累计 collected；收够后认出最终整理的交付接口。_cb 留在父函数卡中；不为 put、append、result 或每个局部语句单独建卡。

<details>
<summary>版本、分支与保留的未知</summary>

- Slime 本地和本次查询的官方 main 都是 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，工作区干净。[核对证据](references/source-evidence.json)。
- 示例默认 straw 选择 DistributedRollout；本步继续已确认的本地 worker 读法，不声称覆盖该默认实现。
- 回调失败、取消、ABORTED/PENDING 重试、输入备份复制，以及消费方丢弃结果后的完整补充流程后续按问题展开。
- “返回的函数为什么仍能用 gid/self”有一份[最小 Python 参考](references/python-callback-notes.md)，不要求先学习完整闭包章节。
- 没有运行真实 worker、Agent、模型、队列服务或训练。

</details>
