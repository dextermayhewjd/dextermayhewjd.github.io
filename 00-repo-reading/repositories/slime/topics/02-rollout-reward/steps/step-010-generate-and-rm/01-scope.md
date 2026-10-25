# 01 · 阅读范围：生成接入与奖励归属

[步骤入口](README.md) · [本步函数记录](02-short-term-memory/overview.md) · [上一主题](../../../01-coding-agent-rl/README.md)

## 1. 阅读目标

- **整体目标**：理解自定义 Agent 怎样接入 Slime 的生成与评分流程。
- **本步问题**：框架怎样通过共享 `state` 控制一次生成，接住结果，并决定后续评分？
- **阅读范围**：先跟一个新 `Sample`，沿 Coding Agent 返回样本列表的路径读通，保留生成准入、中止检查、名额释放和评分责任的边界。

## 2. 指挥官函数

- **本步入口**：[sglang_rollout.py::generate_and_rm](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L289-L380)，组织受控生成、资源释放、样本后处理与评分。
- **调用者**：`generate_and_rm_group:425` 为每个待生成 Sample 创建本函数的任务；本步只定位这一交接。
- **已读下游**：`examples/coding_agent_rl/generate.py::generate → _generate`，负责一次 Coding Agent 任务；此次从框架调用侧接回它。

## 3. 给出真正干活的核心骨架

### 3.1 整体位置：回到 Coding Agent 的调用方

```text
generate_and_rm_group
  └─ 创建任务：generate_and_rm(...)              ← 本步指挥官
       └─ 选中并等待：Coding Agent generate(...)
            └─ _generate(...)                  ← 前一主题的单题主线
```

- **进入**：`generate_and_rm_group` 将一份待生成的 `Sample` 交给本函数。
- **返回**：Coding Agent 交回样本列表，本函数先释放生成名额，再完成后处理与奖励检查，把结果交回 `generate_and_rm_group`。

<a id="execution-skeleton"></a>

### 3.2 核心骨架：共享状态 → 受控生成 → 结果处理 → 评分交付

以下为教学裁剪：跟随一个新输入任务，使用 Coding Agent 自定义生成、`evaluation=False` 和列表返回；保留中止与组评分判断。详细配置选择、已完成输入的提前返回、部分续跑掩码、日志及单个 Sample 的评分分支暂时折叠，关键数据交接和资源范围保留。

```python
# 1. 取得共享控制状态，保留输入任务的上下文
state = GenerateState(args)
queue_input = copy.copy(sample)

# 2. 进入受控的生成阶段
await state.semaphore.acquire()
try:
    await state.generation_pacer.wait()

    if state.aborted:
        sample.status = Sample.Status.ABORTED
        return sample

    with state.dp_rank_context() as _:
        generate_func = load_function(...)
        generate_call = generate_func(...)
        sample = await _run_server_abort_generate(state, generate_call)
finally:
    state.semaphore.release()

# 3. 保持任务归属，处理生成结果
sample = inherit_queue_context(queue_input, sample)
sample = await apply_rollout_sample_hooks(..., sample)
sample = inherit_queue_context(queue_input, sample)

# 4. 判断评分责任
if args.group_rm:
    return sample

samples = sample
if any(sample.status == Sample.Status.ABORTED for sample in samples):
    return samples

samples_need_reward = [sample for sample in samples if sample.reward is None]
rewards = await batched_async_rm(..., samples_need_reward)
for sample, reward in zip(samples_need_reward, rewards, strict=False):
    sample.reward = reward
return samples
```

- **共享控制**：`state` 通常复用进程内缓存的同一对象；`semaphore` 管生成名额，`generation_pacer` 分批放行，`aborted` 决定此时是否继续生成。
- **资源边界**：名额覆盖启动等待和生成，由 `finally` 归还；hook 与评分在释放之后执行。
- **数据交接**：生成器或 hook 可以返回新的 Sample，`inherit_queue_context` 保持输入任务的上下文归属；后续按配置、状态与缺失奖励决定交付方式。

### 3.3 沿骨架阅读：先看控制范围，再看范围内的调用

进入下面的导航前，先短回顾 [Sample 类卡](02-short-term-memory/classes/slime/utils/types.py/Sample.md)，再看 [GenerateState 类卡](02-short-term-memory/classes/slime/rollout/sglang_rollout.py/GenerateState.md)：一份任务数据怎样使用共享运行状态。[两个对象的整体定位](../../../../../../../slime_photo/code-reading/chapters/03-strategy-evaluation/walkthrough.md#sample-and-state)继续作为讲解参考。

| 骨架位置 | 本轮看清什么 | 源码入口与返回位置 |
| --- | --- | --- |
| 1. 状态与输入上下文 | `GenerateState` 共享哪些执行控制；`queue_input` 保留什么 | [306–325 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L306-L325)；需要时回看[状态职责](../../../../../../../slime_photo/code-reading/chapters/03-strategy-evaluation/walkthrough.md#state-and-execution-skeleton)，再到 `329` 取得名额 |
| 2. 受控生成与释放 | 先辨认 acquire/try/finally 的范围，再看分批启动、中止检查、选函数与等待 | [329–351 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L329-L351)；当前展开 [dp_rank_context](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/GenerateState.dp_rank_context.md)，返回 `338` 选择生成函数；退出生成段后到 `353` |
| 3. 结果后处理 | 为什么 hook 前后都继承上下文，后续评分接收哪份结果 | [353–355 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L353-L355)；先按接口理解，再到 `358` 判断评分责任 |
| 4. 评分与交付 | 组评分交回调用者，ABORTED 提前返回，其余只补缺失奖励 | [358–380 行](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/rollout/sglang_rollout.py#L358-L380)；最终回到 `generate_and_rm_group:427–430` 接收结果 |

具体输入输出与逐段说明见 [generate_and_rm 函数卡片](02-short-term-memory/functions/slime/rollout/sglang_rollout.py/generate_and_rm.md)。**停止位置**：能说明任务怎样受控生成、何时释放名额，以及结果怎样完成后处理和评分交付；状态内部算法、队列协议与评分器实现按后续问题展开。

<details>
<summary>本轮剪掉了什么，以及其他路径何时再看</summary>

- **配置与执行实现**：路径优先级、参数签名检查、详细追踪与另一种生成包装暂不展开。当前 Coding Agent 使用 `_run_server_abort_generate`；共享状态、获取与释放关系已保留在骨架中。
- **输入处理**：部分续跑的旧响应掩码、已完成输入的直接返回、评估参数调整和队列生成请求历史省略；完整位置见源码 `296–325`。
- **其他返回形状**：单个 Sample 先检查 ABORTED，再仅在 `reward is None` 时调用 `async_rm`；当前骨架展示列表分支。
- **奖励边界**：`0.0` 是已有分数，只有 `None` 才待补。当前 Coding Agent 的正常训练结果已带奖励，所以待评分列表通常为空；源码仍会调用 `batched_async_rm(args, [])`，并非完全跳过该入口。

</details>

## 版本说明

- 源码固定为 `18868a79b0b083a093798a94ed0f8cb4f71b9c14`；本步卡片使用这一版本。
- 本轮按用户确认，采用包含共享状态与执行控制的骨架，见[采用记录](04-flow.md#execution-skeleton-adopted)。
- [本次替换前版本](references/scope-before-execution-structure-2026-10-25.md)与[最初重排前版本](references/scope-before-core-skeleton-review-2026-10-25.md)完整归档，保留当时说明和来源。
