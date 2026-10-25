# Rollout 接入与奖励：从 generate_and_rm 开始

单题主线已经把 Coding Agent 的职责接了起来：准备服务与沙箱，启动 CLI，处理模型请求，收集代码改动，评测并导出 Sample。现在回到框架的调用侧，看这份实现怎样被选中，以及返回后谁负责评分。

本篇先跟一个新的输入 Sample，使用 Coding Agent 自定义生成、正常训练模式 `evaluation=False`、非组评分 `group_rm=False`。组级并发与评分器内部留到对应问题再展开。

## 先定位：这次在已读函数的外面

```text
generate_and_rm_group
  └─ generate_and_rm                ← 当前入口
       ├─ 取得共享 state，在受控生成段内选择、调用并等待生成函数
       │    └─ Coding Agent generate → _generate
       │         └─ 单题运行、评测、导出 Samples
       ├─ 释放生成名额
       ├─ 继承任务上下文，执行样本后处理
       └─ 判断是否补奖励，返回生成结果
```

`generate_and_rm_group` 给单个待生成 Sample 创建任务。`generate_and_rm` 负责控制生成的准入与启动、选择生成实现、接住返回值，并衔接评分；具体怎样运行 Agent，仍由已有的 Coding Agent 实现负责。

需要回忆单题执行时，可回看[原来的完整导览](/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/task-walkthrough/)。这里先弄清两者之间的调用关系。

<a id="sample-and-state"></a>

## 进入实现前，先分清 sample 与 state

两者都是 Python 对象，但在本函数里承担不同职责：

| 变量与类型 | 从哪里来 | 在这里代表什么 |
| --- | --- | --- |
| `sample`，入口处为 `Sample` 实例 | `generate_and_rm_group` 将待生成的一项传入 | 本次任务的数据记录，包含输入、状态、生成结果与奖励等字段 |
| `state`，类型为 `GenerateState` | 本函数通过 `GenerateState(args)` 取得 | 当前进程内复用的生成运行状态，包含控制并发、启动节奏和中止的成员 |

可以按“单份样本”与“多份任务共用”区分两层。Sample 同时保存数据与状态，`status` 只是其中一个字段；GenerateState 的共享范围也不局限于某一个样本组，它可以被当前进程中的多个组及其生成任务复用。

前一主题已经见过生成后的 Sample；这里先看它进入生成前的形态。同一个类可以承载处理前和处理后的数据，字段会随阶段填写，并不意味着入口处已具有完整回答与奖励。

阅读顺序可先短回顾 `Sample`，再重点看 `GenerateState`：

1. **Sample 先抓用途。** `prompt` 与 `metadata` 提供任务输入，`status` 表示处理状态，`generate_function_path` 可以指定生成实现，`reward` 保存评分。token、logprob、mask 等字段可先接回此前的样本导出认识。
2. **GenerateState 先抓本函数使用的成员。** `semaphore`、`generation_pacer`、`aborted` 与 `dp_rank_context()` 怎样影响这次生成；其他模型依赖、默认参数与任务集合在实际用到时再展开。
3. **带着两个对象回到骨架。** 一份待处理的 `sample` 使用共享 `state` 进入生成段。生成后，变量 `sample` 可能被重新赋值为返回的 `list[Sample]`，不能一直把它当作入口处的同一个对象。

<details>
<summary>对象定义与传入位置</summary>

- [Sample 定义：types.py:106–170](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/types.py#L106-L170)。
- [调用者传入 sample：sglang_rollout.py:419–425](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L419-L425)。
- [取得 state：sglang_rollout.py:306](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L306)，[GenerateState 定义：84–140](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L84-L140)。

</details>

<a id="state-and-execution-skeleton"></a>

## 完整骨架还必须保留 state 与执行边界

若只保留“生成 → hook → 评分”，展示的是数据处理路径。这个函数还负责决定任务何时能开始、如何响应中止，以及何时归还生成名额。这些控制关系也是它的核心职责。

从源码提取骨架时，可以逐段判断：这段是否改变执行条件、是否改变结果的归属或去向、是否获取了必须归还的资源。符合其中一项，就先保留职责和控制结构，再决定哪些内部细节可以折叠。

`state = GenerateState(args)` 取得当前进程中按类缓存的共享实例。首次调用才执行初始化；后续调用通常复用它，因此多份生成任务操作的是同一套控制状态。

| 本函数用到的 state 成员 | 对执行产生的影响 |
| --- | --- |
| `semaphore` | 限制取得生成名额的任务数量；获得名额后，在 `finally` 中归还 |
| `generation_pacer` | 将等待者分批唤醒，平滑任务启动，减轻事件循环瞬时调度压力 |
| `aborted` | 任务等到可以继续后再次检查；已中止则交回 ABORTED 结果，跳过生成 |
| `dp_rank_context()` | 进入时增加选定 DP rank 的在途计数，退出时减少；这里先保留计数生命周期，不据此推定完整引擎路由 |

`generation_pacer` 的真实实现是 `AsyncPacer`：它分批释放等待者。它与限制在途数量的 semaphore 职责不同，也不是手动暂停开关；Trace 中的 `rollout_pause_wait` 标签不能代替实现依据。

下面是结构裁剪，跟随新输入任务、Coding Agent 自定义生成和列表返回；保留中止与组评分判断。省略日志、详细参数选择、部分续跑的 mask 处理、已完成输入的提前返回以及单个 Sample 的评分分支。它用于说明函数的执行范围，不是独立运行脚本。

```python
state = GenerateState(args)                       # 取得共享执行状态
queue_input = copy.copy(sample)                    # 保存输入任务的上下文

await state.semaphore.acquire()                   # 取得生成名额
try:
    await state.generation_pacer.wait()            # 分批启动
    if state.aborted:
        sample.status = Sample.Status.ABORTED
        return sample                             # 仍会经过 finally

    with state.dp_rank_context() as _:
        generate_func = load_function(...)        # 本例选中 Coding Agent
        generate_call = generate_func(...)
        sample = await _run_server_abort_generate(state, generate_call)
finally:
    state.semaphore.release()                     # 生成段结束，归还名额

sample = inherit_queue_context(queue_input, sample)
sample = await apply_rollout_sample_hooks(..., sample)
sample = inherit_queue_context(queue_input, sample)

if args.group_rm:
    return sample                                 # 组评分交给调用者

samples = sample                                  # 当前路径返回列表
if any(sample.status == Sample.Status.ABORTED for sample in samples):
    return samples
samples_need_reward = [sample for sample in samples if sample.reward is None]
rewards = await batched_async_rm(..., samples_need_reward)
for sample, reward in zip(samples_need_reward, rewards, strict=False):
    sample.reward = reward
return samples
```

**最重要的范围关系是：名额包住启动等待和生成，随后先归还名额，再做 hook 与评分。** 因而这里的 semaphore 不直接限制整个“生成加评分”流水线的在途数量。生成段里的提前返回、异常或取消经过 `finally` 时，也会归还已取得的名额。

两个 `inherit_queue_context` 也有明确的交接目的：生成器或 hook 可以新建 Sample，需要把输入任务的队列上下文接到输出上。第一遍可将三行合看为“保持任务归属的样本后处理”，具体字段稍后再查。

完整函数还有三类要保留位置的决策：已有 COMPLETED/TRUNCATED 输入直接返回；不同生成器按声明选择请求级取消包装或服务端中止计数包装；评分时按组配置、ABORTED 状态、返回形状与 `reward is None` 决定去向。正常路径可以分次读，退出点与资源范围应先标出来。

<details>
<summary>共享状态与执行结构的源码依据</summary>

- [GenerateState 与 DP 计数上下文：84–140](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L84-L140)、[SingletonMeta：62–76](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/misc.py#L62-L76)。实例是进程内缓存，不代表跨进程共享同一个 Python 对象。
- [AsyncPacer：8–42](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/async_utils.py#L8-L42)：每批最多释放 64 个等待者，有剩余时安排后续批次；这里不要求先展开调度 API。
- [本函数完整执行结构：289–380](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L289-L380)。
- [两类生成包装：258–285](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L258-L285)分别登记可取消任务、维护服务端生成计数；[abort：442–465](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L442-L465)使用这些共享状态。
- [输入任务上下文继承：207–230](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/data/transport.py#L207-L230)。本轮仅静态核对，未运行并发或中止实验。

</details>

<a id="generation-admission"></a>

## 生成前：名额、启动节奏、中止检查与 DP 计数

先沿这几行顺序走，当前 sample 已经由调用者传入：

```python
await state.semaphore.acquire()
try:
    await state.generation_pacer.wait()
    if state.aborted:
        sample.status = Sample.Status.ABORTED
        return sample
    with state.dp_rank_context() as _:
        ...  # 选择并执行本次生成
finally:
    state.semaphore.release()
```

**1. acquire：为当前任务取得生成名额。** 名额用完时，当前协程在这里等待；其他任务释放名额后，它才能继续。这一行不从队列取出下一个 Sample，也不表示生成下一个 token。Coding Agent 的一次生成任务内部可以发起多次模型请求，名额在这段任务结束后归还。

**2. pacer.wait：让拿到名额的任务分批继续。** 它每批最多释放 64 个等待者；仍有等待者时，用 `call_later(0.001, ...)` 安排后续批次。后续批次不需要等待上一批完成生成。semaphore 管进入生成段的数量，pacer 让大量任务的启动不要集中在一次事件循环调度中。

**3. aborted：检查是否已经要求中止。** 它是一个布尔值，重置时为 `False`，中止入口将其置为 `True`。此处为真，就把当前 `sample.status` 设为 ABORTED 并返回；外层 finally 仍然会归还名额。

`state.aborted` 不保存样本列表。`state.pendings` 是已提交组任务的集合，里面保存 Task；任务结束后才从结果中取得样本。两者承担不同职责。

**4. dp_rank_context：登记生成期间某个 rank 的占用。** DP 指数据并行，这里用 rank 编号索引各自的计数。方法在进入时从当前计数最少的 rank 中随机选一个，计数加一，随后运行 with 内的生成代码；退出时计数减一。

例如下面是没有其他任务同时修改计数时的教学推演：

| 时机 | `dp_counts` | 本次选择 |
| --- | --- | --- |
| 进入前 | `[2, 0, 1]` | rank 1 当前最少 |
| with 内执行生成 | `[2, 1, 1]` | 本次占用已登记 |
| 离开 with | `[2, 0, 1]` | 本次占用已归还 |

这个上下文交出的 rank 编号在调用处被 `_` 接住；本段没有直接把编号传给模型请求。当前先确认计数和生命周期，实际请求如何路由需要另外核对。

<a id="two-kinds-of-context"></a>

### 这里的 context 与 HarnessContext 有什么区别

`HarnessContext` 是保存运行参数的数据类：构造一个 `ctx`，把工作目录、会话编号、Adapter 地址等信息交给后续方法读取。

`dp_rank_context` 是 `GenerateState` 的方法。它用 `@contextmanager` 包装，调用后得到供 `with` 使用的上下文管理器，负责一段代码进入、执行和退出时的计数安排。

```python
# 参数对象：创建后交给其他方法读取
ctx = HarnessContext(workdir=workdir, session_id=session_id, adapter_url=adapter_url)

# 上下文管理器：围住一段执行范围
with state.dp_rank_context() as _:
    ...  # 在计数登记期间执行生成
```

这两个代码片段来自不同调用位置，只用于对照用途。第一个 `ctx` 保存数据；第二个 `_` 接住的是 `yield` 交出的 rank 编号。这里不能因为名称中都有 context，就把它们当作同一种对象或机制。

<details>
<summary>HarnessContext 对照的源码位置</summary>

- [数据类定义：harness/common.py:42–54](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L42-L54)。
- [构造与传递：98–104](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/harness/common.py#L98-L104)。

</details>

<details>
<summary>DP 上下文的真实实现与四处源码</summary>

```python
@contextmanager
def dp_rank_context(self):
    candidates = [i for i, count in enumerate(self.dp_counts) if count == min(self.dp_counts)]
    dp_rank = int(np.random.choice(candidates))
    self.dp_counts[dp_rank] += 1
    self.dp_rank = dp_rank
    try:
        yield dp_rank
    finally:
        self.dp_counts[dp_rank] -= 1
        assert self.dp_counts[dp_rank] >= 0
```

- [调用顺序与名额释放：sglang_rollout.py:329–351](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L329-L351)。
- [AsyncPacer.wait 与分批唤醒：async_utils.py:24–42](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/async_utils.py#L24-L42)。
- [aborted 初始值：reset:135–140](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L135-L140)，[置为 True：abort:442–448](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L442-L448)。
- [DP 上下文：123–133](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L123-L133)。

</details>

这四处接清后，回到 with 主体的 `338` 行，继续看生成函数怎样被选中。

## 下一处：路径怎样变成真正的生成函数

示例启动脚本包含：

```bash
--custom-generate-function-path examples.coding_agent_rl.generate.generate
```

它指定一个 Python 导入路径。在上面受控生成段中，选择生成实现时执行下面的真实代码：

```python
custom_func_path = sample.generate_function_path or args.custom_generate_function_path
generate_func = load_function(custom_func_path) if custom_func_path is not None else generate

if custom_func_path is not None and "evaluation" in inspect.signature(generate_func).parameters:
    generate_call = generate_func(args, sample, sampling_params, evaluation=evaluation)
else:
    generate_call = generate_func(args, sample, sampling_params)
```

- **选路径**：这个 Sample 自己指定的生成路径优先；未指定时采用全局配置。本场景沿全局配置找到 Coding Agent。
- **取函数**：`load_function` 导入模块并取出对应属性，得到此前读过的 `examples.coding_agent_rl.generate.generate` 函数对象。没有自定义路径时才选同文件的默认 `generate`。
- **准备调用**：Coding Agent 的 `generate` 接收 `evaluation`，因此走第一条调用分支。本例值为 `False`。

此时 `generate_call` 是本次调用创建的协程对象，尚未取得任务结果。随后才由 `_run_request_abortable_generate` 或 `_run_server_abort_generate` 接手等待。把“选哪个函数”和“等待它交回什么”分开，下一段的返回值就容易跟踪。

<details>
<summary>本段源码位置</summary>

- [示例启动配置：165–167](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/run_qwen38_27b_fully_async.sh#L165-L167)。
- [函数选择与调用：338–349](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L338-L349)。
- [load_function](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/utils/misc.py#L50-L59)。
- [被选中的 Coding Agent generate](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L225-L251)。

</details>

## 返回时先记住的边界

一次生成可以返回一个 `Sample`，也可以返回 `list[Sample]`。Coding Agent 的正常训练路径会先在内部得到 reward，再把带奖励的样本列表交回。

框架接住结果、完成样本 hook 之后，才判断是否补奖励。非组评分路径检查的是 `reward is None`；`0.0` 已经是有效分数。列表分支只把缺奖励的成员交给批量入口，不过待评分列表为空时，该入口仍会被调用。

沿同一个函数继续看 `346–380`：返回值怎样接住，hook 放在哪里，以及哪些结果需要评分。共享控制状态与名额范围已在前节定位；具体取消协议、队列字段和评分实现可按问题继续展开。

## 版本与证据边界

源码固定在 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`，上述判断来自静态调用与实现核对，没有运行真实 CLI、沙箱、SGLang 或训练。逐项来源见 [SOURCE-CHECK.md](SOURCE-CHECK.md)。
