# 05 · 任务链路：完成的组如何交给上层收集

> 后台 Task 完成后，回调把组编号与结果放入 worker 的完成队列；上层按需领取，经过过滤后累计保留的组，收够本批目标后交给最终整理。

[本步 scope](01-scope.md) · [函数记录](02-short-term-memory/overview.md) · [理解形成过程](04-flow.md) · [本次收束](04-flow.md#step013-first-pass-closure)

## 1. 本步接住什么，到哪里结束

Step 011 已读 generate_and_rm_group 组织组内生成与奖励；Step 012 已读本地 AsyncRolloutWorker._loop 持续取组、创建 Task 并登记回调。本步接着看 Task 的返回结果如何被交付给上层。

本轮选择本地 AsyncRolloutWorker 的正常完成路径。结果为组列表，没有 ABORTED/PENDING；这些状态的重试只保留去向。默认 straw 的 DistributedRollout 是另一条实现，本页不把本地流程当成默认分布式实现。

本步到 _generate_rollout_async 收集够目标组数、把 collected 交给最终整理的接口为止。最终整理和最外层返回形态只作定位，具体排序、批次 hook 与传输内部留白。

## 2. 后台交付与上层领取怎样接起来

两侧可以交错运行，通过同一个 worker.output_queue 交接。下面的“Task 结束”是事件循环触发回调，不能读成 _loop 随后直接调用 _cb 或 get_completed_groups。

```text
后台：AsyncRolloutWorker._loop
├─ 创建 Task → generate_and_rm_group
└─ _make_done_cb(gid, group) → 返回 _cb → 登记到 Task       222

Task 结束后：事件循环调用 _cb(done_task)
├─ done_task.result() → 本组结果                           254
└─ 正常结果 → output_queue.put((gid, result))              273
                         │
                         │ 同一个 worker 的完成队列
                         ▼
消费侧：_generate_rollout_async
├─ 取得并恢复 worker，设定 target 和 collected
├─ while len(collected) < target                          306
│  ├─ get_completed_groups(limit=还缺的组数)               312
│  │  └─ 从 output_queue 移出记录，返回 [(gid, group), ...]
│  ├─ for 逐项解包记录
│  │  ├─ call_dynamic_filter(...) → verdict               314
│  │  │  └─ 统计已有奖励 → 调用 fn → 统一返回判定
│  │  ├─ keep=True  → collected.append(group)             321
│  │  └─ keep=False → 交给丢弃处理，继续收集
│  └─ 本轮没取到组 → 短暂等待，再尝试领取                 335–336
└─ 收够目标 → finalize_rollout_groups → 按模式返回         364–378
```

图内行号属于 slime/rollout/fully_async_rollout.py，过滤子函数定义在 filter_hub/base_types.py:30–46。详细位置和阅读推进顺序继续看 scope；此图只总结执行与交接。

对应卡片：[回调工厂与内部 _cb](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._make_done_cb.md) · [限量领取](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.get_completed_groups.md) · [上层收集](02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/_generate_rollout_async.md#collect-filter-retain) · [过滤适配](02-short-term-memory/functions/slime/rollout/filter_hub/base_types.py/call_dynamic_filter.md)。

这段交接里需要保留四个区别：

- **返回函数与执行回调**：_make_done_cb 先返回 _cb；Task 结束后，事件循环再把已结束的 Task 传给它。
- **入队与消费**：_cb 负责写入完成队列；get_completed_groups 由上层主动调用，取出时移除记录。
- **已领取与已保留**：drained 统计本轮拿到的组，len(collected) 统计累计保留的组；被拒绝的组不会增加 collected。
- **奖励统计与筛选判定**：call_dynamic_filter 先记录已有 reward 的总和与数量，再调用规则得到判定；统计本身没有重新调用奖励模型。

## 3. 各层交出的结果是什么

| 位置 | 交出什么 | 由谁接住 |
| --- | --- | --- |
| _make_done_cb | 一个回调函数 _cb | _loop 将它登记到 Task |
| _cb 正常分支 | 副作用：写入 (gid, result)；没有把组作为返回值交给上层 | worker.output_queue 保存记录 |
| get_completed_groups | 本次领取的 (gid, group) 列表，可能为空或少于 limit | _generate_rollout_async 的 for 循环 |
| call_dynamic_filter | 带 keep、reason、raw_reward_stats 等字段的判定对象 | 父函数分支与统计器 |
| _generate_rollout_async | 本批整理后的输出；具体是对象还是 samples 取决于过滤与传输配置 | 外层 generate_rollout_fully_async，经 run 接收 |

沿用父卡的静态例子：目标是两组，G7、G8、G9 已依次入队，过滤结果分别为保留、丢弃、保留。

```text
第一次领取 G7、G8 → collected 只留下 G7
还差一组，再领取 G9 → collected 成为 [G7, G9]
达到 target=2 → 交给最终整理
```

limit 只限制单次领取量；队列当时为空就返回 []，外层仍可能继续等待。取走不会自动触发新 Task，后台是否继续接纳由 _loop 的条件决定。最终整理还可能排序或应用批次 hook，不能把循环结束时的列表无条件当成所有配置下的最终返回。

<a id="scope-closure"></a>

## 4. 本轮在这里收束

**按本步约定的首轮深度，结果交付主线已覆盖，可以停止继续下钻。** 本页由助手根据实际阅读与源码整理；用户已表达 Task 结果入队、队列归属、领取已完成组及整体筛选作用的理解，细分机制仍按各卡片中的原话与未知保留。

| 保留的边界或未知 | 何时回查 |
| --- | --- |
| 异常、取消、ABORTED/PENDING 与重试输入处理 | 需要解释任务失败、重复执行或中止恢复时 |
| 具体 fn 的过滤规则，分段轨迹统计与兼容字段 | 需要接入或排查某个筛选策略时 |
| 丢弃清理、最终排序、批次 hook 与传输凭证 | 需要追踪最终交付内容或资源处理时 |
| 线程协调、分布式队列与真实运行表现 | 需要排查并发、性能或运行稳定性时 |

这些边界不要求在本轮全部展开。父函数和过滤子卡中的具体分支、计数仍可复习，不因首轮收束而改写成全部掌握。下一步的问题和入口尚未确认，不据本页自动开启新步骤。

<details>
<summary>源码、形成依据与验证范围</summary>

- 固定源码版本：18868a79b0b083a093798a94ed0f8cb4f71b9c14。
- [创建 Task 与登记回调](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L214-L223)；[回调工厂](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L246-L275)；[领取方法](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L147-L161)。
- [上层收集与交付](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L278-L389)；[过滤适配](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/filter_hub/base_types.py#L30-L46)。
- 本页按 task-flow skill 的 Step 003 四段结构整理，并参考 Step 007 的调用层级表达；回调触发与跨线程共享队列另行标明。
- 形成过程：[队列与重试去向](04-flow.md#step013-queue-origin-and-retry)、[领取理解](04-flow.md#step013-getter-purpose-and-boundaries)、[父卡建立](04-flow.md#step013-collection-parent-card-created)、[过滤子卡](04-flow.md#step013-filter-card-created)、[筛选用途与性能边界](04-flow.md#step013-filter-purpose-versus-performance)。
- 各卡片源码摘录已做静态一致性检查，例子为构造与推导；未运行真实 worker、过滤插件、模型或训练，不据此判断运行性能。

</details>
