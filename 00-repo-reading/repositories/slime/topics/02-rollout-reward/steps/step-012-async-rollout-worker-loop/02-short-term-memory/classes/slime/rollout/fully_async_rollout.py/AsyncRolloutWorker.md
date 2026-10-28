# AsyncRolloutWorker

- 源码定位：[fully_async_rollout.py:82–275](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L82-L275)。
- 首次接触：Step 011 定位调用者；2026-10-26 在 Step 012 建立类卡。
- 最近认识：用户要求保留部分黑箱、减少本步前置；这项范围选择不代表相关机制已掌握。

## 1. 对象职责

把它先理解为一个持续工作的本地生成 worker：**从输入源拿组，启动生成，把完成结果交出去。** [_loop 方法卡](../../../../functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md)记录这个过程；本卡只帮助认出它持有什么。

```text
data_buffer（输入源） → worker 内的组任务 → output_queue（完成结果）
```

Sample 在此只是组里的输入对象；其字段和轨迹结构沿用已有记录，当前不展开。

## 2. 当前需要的对象接口

| 字段 | 目前知道到什么程度 |
| --- | --- |
| data_buffer | 上层传入的输入源，get_samples(1) 返回一组输入；内部存储与取数算法先黑箱 |
| concurrency | 允许接纳的组数阈值；先用已给定的数值，计算公式按需回查 |
| output_queue | 保存已完成、待消费的组；本步先看队列长度如何影响接纳 |
| running / paused | 是否继续循环、是否允许接纳新组 |
| poll_interval | 每轮末尾等待的间隔，当前值 0.01 秒 |
| state | 已有 GenerateState，提供本次调用用到的采样参数；沿用已有模型 |

active_tasks 是 _loop 内维护的任务集合。active、admission_paused、condition 等字段属于对外报告与控制配合，本轮先把这部分看成“发布当前状态”的接口。

<a id="data-buffer-origin"></a>

### 2.1 输入源只接清来路与调用

上层 RolloutManager 创建数据源，再沿调用链传给 worker。本步默认本地分支使用 RolloutDataSourceWithBuffer；完整构造链保留在参考中。

```python
# 构造器保存上层传来的对象
self.data_buffer = data_buffer

# _loop 使用它提供的接口
groups = self.data_buffer.get_samples(1)
```

当前只跟踪 `groups → group → 生成 Task`。对象内部如何组织 dataset、buffer 和重试数据，见[按需回查](../../../../../references/worker-class-full-context-2026-10-26.md#data-buffer-origin)。

<a id="pause-handshake"></a>

### 2.2 第四段先作为“报告状态”使用

```python
with self.condition:
    self.active = len(active_tasks)
    self.admission_paused = self.paused
    self.condition.notify_all()
```

这几行向控制方报告本轮的任务数量和暂停状态。当前先知道这个作用；pause 怎样等待确认、Condition 怎样协调线程，放在[独立回查位置](../../../../../references/worker-class-full-context-2026-10-26.md#pause-handshake)。继续跟随循环时，回到 sleep 再进入下一轮即可。

完整 13 个字段、方法用途、输入来源链和暂停协议均保存在[完整参考](../../../../../references/worker-class-full-context-2026-10-26.md)。仅当某项细节妨碍当前问题时再进入，不增加本轮必须读完的清单。

## 3. 我的直接表述（原话）

<details>
<summary>原话与本轮范围反馈</summary>

2026-10-26，本轮节选：

> 这里的data buffer 我觉得我需要清楚是哪里来的
> 这个是我觉得需要了解的数据结构

> 但是最后一个部分在做什么 我其实就不是特别理解
> 这里的四我需要额外的理解

> 我觉得主要会变成
> 当前这个asyncrollout worker 是否需要单独开一个class 的short term memory？
> 这样子能够加深对于这个class的理解 主要是为什么需要某些字段

这些是字段来源、用途与记录方式的请求；不能写成已理解全部类字段。完整消息及 sleep(0) 的校准见[本步过程](../../../../../../step-012-async-rollout-worker-loop/04-flow.md#worker-class-and-input-source)。

本轮进一步要求：

> 我在想的问题是
> 这里asyncrolloutworker部分
> 这里吧sample什么放在这里2是合适的吗？
> 我只是感觉
> 在asyncrolloutworker部分这里的内容实在是太复杂或者晦涩难懂了
> 如果全部放在这里的话 我觉得会变成一个内容的灾难？
> 因为目前其实或许暂时不需要知道这么多
>
> 暂时把一部分留为黑箱 对于人来说比较好定位

</details>

## 4. 尚不清楚

- 输入源内部的数据集、缓冲和重试机制，暂作黑箱。
- 状态报告的作用已解释；暂停确认、Condition 线程协议与关闭/取消暂不展开。
- Sample 的详细字段与分布式实现使用已有记录按需回查，不作为当前 worker 主线的前置。

## 5. 来源

[完整字段与旧稿来源](../../../../../references/worker-class-full-context-2026-10-26.md)保留此前材料；[本轮范围调整](../../../../../../step-012-async-rollout-worker-loop/04-flow.md#worker-blackbox-boundary)说明哪些部分暂不展开。


<details>
<summary>固定版本、字段依据与阅读范围</summary>

- 固定源码提交：18868a79b0b083a093798a94ed0f8cb4f71b9c14。采用[已认可的 BaseAdapter 类卡结构](../../../../../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/02-short-term-memory/classes/slime/agent/adapters/common.py/BaseAdapter.md)，完整字段浅层总览，按需补实际用法。
- [默认数据源选择](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/arguments.py#L2006-L2011)、[数据源构造](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L87-L125)、[传入 rollout 入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L545)、[参数转发](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/base_types.py#L28-L31)。
- [_get_worker](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L58-L79)、[13 个字段](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L86-L105)、[输入缓冲数据源](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/data_source.py#L191-L238)。
- [pause 的等待条件](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L114-L122)、[循环发布状态](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L225-L228)、[关闭与消费入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L140-L165)。
- 本轮静态核对字段定义与调用，未运行真实 worker、队列服务或训练；类卡不替代方法卡中的具体执行过程。

</details>

