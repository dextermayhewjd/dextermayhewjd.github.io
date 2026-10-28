# AsyncRolloutWorker：完整字段与实现回查

这是 2026-10-26 收窄阅读范围前的完整类卡。保留字段、输入来源链、暂停确认协议与当时的原话及未知，供按需回查；不作为当前主线的必读内容。

[返回精简类卡](../02-short-term-memory/classes/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker.md)

---

# AsyncRolloutWorker

- 源码定位：[fully_async_rollout.py:82–275](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L82-L275)。
- 首次接触：Step 011 作为组级函数调用者定位；2026-10-26 在 Step 012 按用户问题建立类卡。
- 最近认识更新：用户提出需要知道字段为何存在、data_buffer 从哪里来；本卡先给源码对象图，尚无对全部字段和暂停协议的独立复述。

## 1. 对象职责

一个本地 worker 持有输入数据源、后台执行线程、共享控制状态和完成结果队列。[_loop](../02-short-term-memory/functions/slime/rollout/fully_async_rollout.py/AsyncRolloutWorker._loop.md)是它持续调度的方法；类卡解释对象中有什么、字段为什么需要，方法卡解释这些字段在一次循环里怎样变化。

**本轮关注**：data_buffer 的来路，以及 paused、admission_paused、active、condition 怎样让协调线程与后台循环配合。其余字段先保留完整浅层总览，按后续问题补用法。

## 2. 字段总览

### 2.1 13 个实例字段

| 字段 | 保存什么／为什么需要 | 当前核对的用法 |
| --- | --- | --- |
| args | 同一次 worker 使用的配置对象 | _loop 传给 generate_and_rm_group |
| **data_buffer** | 上层传入的输入数据源对象；提供待执行的组，也能接回重试组 | _loop.get_samples(1) 取组；完成回调必要时 add_samples，回调细节后续读 |
| concurrency | 以组为单位的接纳阈值；由传入预算、每组样本数和 prefetch 因子计算 | _loop 同时检查登记组数和完成队列长度 |
| running | worker 的外层运行开关 | close 置 False；_loop 和线程收尾使用，关闭协议后续读 |
| **paused** | 协调方提出的“停止接纳新组”请求 | pause 置 True，resume 置 False；_loop 的接纳条件检查 |
| **condition** | 协调状态读写与等待/通知所用的 threading.Condition | pause 等待状态；_loop 更新后 notify_all，见下面配合代码 |
| **active** | _loop 发布出来的组任务数量快照 | _loop 写入 len(active_tasks)；pause(drain=True) 等它归零 |
| **admission_paused** | _loop 发布出来的暂停状态，供协调方确认请求已被观察 | _loop 写入 paused；pause 等它为 True，避免仅发出请求就继续 |
| error | 最近捕获的异常；使等待方能获知失败，而非一直等待 | _loop、线程或回调写入；pause 等方法检查，完整错误路径后续读 |
| output_queue | 已完成、等待消费的 (gid, group) 队列；跨线程交接结果 | 完成回调 put；get_completed_groups 取走；_loop 只看 qsize；队列未设硬容量 |
| poll_interval | 本轮循环末尾的异步等待间隔，初始 0.01 秒 | _loop 在 sleep 后再检查任务与接纳条件 |
| worker_thread | 运行调度协程的后台线程对象，初始 None | start 创建线程，close 等待线程结束；完整生命周期后续读 |
| state | 当前进程的 GenerateState，持有采样参数等共享生成状态 | _loop 复制 sampling_params，见[已有类卡](../02-short-term-memory/classes/slime/rollout/sglang_rollout.py/GenerateState.md) |

`active_tasks`、`done`、`max_concurrent`、`gid_counter` 是 _loop 的局部变量，不是实例字段。其中 active_tasks 保存 Task 对象；active 只发布其数量，供别的方法读取。

<a id="data-buffer-origin"></a>

### 2.2 data_buffer 从哪里来，具体是什么？

**本节场景**：继续本步选定的非 straw 本地分支，且没有自定义 data_source_path。参数解析会选择 `slime.data.data_source.RolloutDataSourceWithBuffer`。其他配置可提供别的数据源，不能把字段名当成固定类型保证。

下面按实际交接拼接必要片段，省略其他分支；各片段来自不同函数，不是一个可直接运行的新函数：

```python
# RolloutManager.__init__：构造数据源，rollout.py:87、123
data_source_cls = load_function(self.args.data_source_path)
self.data_source = data_source_cls(args)

# RolloutManager._get_rollout_data：把同一对象传给生成入口，rollout.py:545
data = call_rollout_fn(self.generate_rollout, self.args, rollout_id, self.data_source, evaluation=False)

# _get_worker：生成入口的第三个参数在这里叫 data_buffer，fully_async_rollout.py:70
worker = AsyncRolloutWorker(args, data_buffer, concurrency=...)

# AsyncRolloutWorker.__init__：保存同一对象引用，fully_async_rollout.py:88
self.data_buffer = data_buffer
```

上方片段只作跨函数对照。`call_rollout_fn` 原样把参数传给选中的生成函数；本场景选中 generate_rollout_fully_async，之后由 _get_worker 取得或创建 worker。字段名变化不意味着重新创建了数据源。

```text
RolloutManager.self.data_source
    → 生成函数参数 data_buffer
        → _get_worker 的参数 data_buffer
            → worker.self.data_buffer
```

在此默认场景中，它的内部还有一个 buffer 列表，用于保存待优先执行的组。取组时先取 buffer，不够再从父类数据源取新组：

```python
# RolloutDataSourceWithBuffer.get_samples:205–211
samples = self._get_samples_from_buffer(num_samples)
num_samples -= len(samples)
if num_samples == 0:
    return samples
samples += super().get_samples(num_samples=num_samples)
return samples
```

因此本步只需要区分两端：**data_buffer 提供待执行的组；output_queue 接收已完成的组。** 请求一组时，返回值依然是“组的列表”。上层数据源还通过 consumers 缓存 worker，供后续调用复用。数据集初始化和完整重试缓冲策略暂不展开。

<a id="pause-handshake"></a>

### 2.3 第四段的字段为什么要发布？因为 pause 会读取它们

协调方在 pause 中提出请求并等待；后台 _loop 发布本轮状态。下面保留完成这次配合所需的真实语句。

```python
# AsyncRolloutWorker.pause:115–119
with self.condition:
    previous = self.paused
    self.paused = True
    while self.running and self.error is None and (not self.admission_paused or (drain and self.active)):
        self.condition.wait()
```

- `paused=True` 表示发出暂停接纳请求。后台循环需要执行到相关检查位置，才能观察它。
- `admission_paused=True` 让协调方知道循环已经发布了暂停状态。
- 默认 drain=True 时，还要等待 active 归零；已有组可继续完成，不会因这个请求自动被取消。

```python
# AsyncRolloutWorker._loop:225–228
with self.condition:
    self.active = len(active_tasks)
    self.admission_paused = self.paused
    self.condition.notify_all()
```

- 后台循环报告当前还登记着多少组，以及观察到的 paused 状态。
- notify_all 通知等待者重新检查条件；它不等于重新创建 Task，也不表示所有组此时都已完成。

下面是假设还有一组在执行时的状态示意，不是实际运行日志：

| 时刻 | paused | admission_paused | active |
| --- | --- | --- | --- |
| 刚发出暂停请求，循环尚未确认 | True | 仍可能是 False | 上次发布的数量 |
| 循环已发布暂停状态，仍有一组 | True | True | 1 |
| 最后一组完成，循环回收并再次发布 | True | True | 0 |

这说明 paused 与 admission_paused 分别承接“请求”和“循环确认”，而 active 让 pause 知道是否还要等待已有组。Condition 如何在等待时协调线程，是可继续展开的机制；本轮先看清谁写、谁读和等待条件。

## 3. 我的直接表述（原话）

2026-10-26，本轮节选：

> 这里的data buffer 我觉得我需要清楚是哪里来的
> 这个是我觉得需要了解的数据结构

> 但是最后一个部分在做什么 我其实就不是特别理解
> 这里的四我需要额外的理解

> 我觉得主要会变成
> 当前这个asyncrollout worker 是否需要单独开一个class 的short term memory？
> 这样子能够加深对于这个class的理解 主要是为什么需要某些字段

这些是字段来源、用途与记录方式的请求；不能写成已理解全部类字段。完整消息及 sleep(0) 的校准见[本步过程](../04-flow.md#worker-class-and-input-source)。

## 4. 尚不清楚

- 默认数据源对象与其内部 buffer、worker 完成队列是否已区分，等待反馈。
- paused 的请求与 admission_paused 的确认，以及 active 数量的作用，等待反馈。
- Condition 的线程等待机制、完整关闭/取消、缓存与恢复，尚未深入。
- 自定义数据源和 straw 分布式路径保持独立边界，本卡不概括为它们的全部实现。

## 5. 来源

<details>
<summary>固定版本、字段依据与阅读范围</summary>

- 固定源码提交：18868a79b0b083a093798a94ed0f8cb4f71b9c14。采用[已认可的 BaseAdapter 类卡结构](../../../../01-coding-agent-rl/steps/step-004-trajectory-to-samples/02-short-term-memory/classes/slime/agent/adapters/common.py/BaseAdapter.md)，完整字段浅层总览，按需补实际用法。
- [默认数据源选择](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/arguments.py#L2006-L2011)、[数据源构造](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L87-L125)、[传入 rollout 入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/ray/rollout.py#L545)、[参数转发](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/base_types.py#L28-L31)。
- [_get_worker](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L58-L79)、[13 个字段](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L86-L105)、[输入缓冲数据源](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/data_source.py#L191-L238)。
- [pause 的等待条件](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L114-L122)、[循环发布状态](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L225-L228)、[关闭与消费入口](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/fully_async_rollout.py#L140-L165)。
- 本轮静态核对字段定义与调用，未运行真实 worker、队列服务或训练；类卡不替代方法卡中的具体执行过程。

</details>
